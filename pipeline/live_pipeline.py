"""Live Kafka consumer for lmnh topic with cleaning, validation, and logging."""
import argparse
import json
import time
from datetime import datetime, timezone
from os import environ
from pathlib import Path
from typing import Any
from uuid import uuid4

from confluent_kafka import Consumer, KafkaError
from dotenv import load_dotenv
import pandas as pd

from load import build_kiosk_output_table, get_db_engine, get_db_connection, get_description_button_id_dict, get_value_button_id_dict
from logging_config import configure_logging, get_logger
from seed_database import run_seed_database


logger = get_logger(__name__)
DB_RETRY_SECONDS = 5
MODULE_DIR = Path(__file__).resolve().parent
GROUP_ID_FILE = str(MODULE_DIR / ".kafka_group_id")
DEFAULT_INFRASTRUCTURE_NAME = "museum"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI flags for live pipeline runtime behavior."""
    parser = argparse.ArgumentParser(
        description="Run the live kiosk pipeline consumer")
    parser.add_argument(
        "--reset_kiosk_output",
        action="store_true",
        help="Reset kiosk_output table and rotate Kafka consumer group id",
    )
    parser.add_argument(
        "--reset_db",
        action="store_true",
        help="Rebuild entire database and rotate Kafka consumer group id",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args(argv)


def generate_group_id(prefix: str) -> str:
    """Generate a random Kafka consumer group id."""
    return f"{prefix}-{uuid4().hex[:8]}"


def get_group_id_prefix(config: dict[str, str]) -> str:
    """Build group id prefix from runtime config with a safe fallback."""
    infrastructure_name = config.get(
        "INFRASTRUCTURE_NAME", DEFAULT_INFRASTRUCTURE_NAME)
    return f"{infrastructure_name}-live-consumer"


def save_group_id(group_id: str) -> None:
    """Persist group id for future runs."""
    with open(GROUP_ID_FILE, "w", encoding="utf-8") as file:
        file.write(group_id)


def load_saved_group_id() -> str | None:
    """Load saved group id if present and non-empty."""
    try:
        with open(GROUP_ID_FILE, "r", encoding="utf-8") as file:
            saved_group_id = file.read().strip()
    except FileNotFoundError:
        return None
    return saved_group_id or None


def create_and_save_group_id(prefix: str) -> None:
    """Generate and persist a new group id."""
    new_group_id = generate_group_id(prefix=prefix)
    save_group_id(new_group_id)


def reset_entire_database(config: dict[str, str], conn: Any, engine: Any) -> None:
    """Drop and recreate all tables by running seed database flow."""
    logger.info("--reset_db enabled: rebuilding database")
    run_seed_database(config, conn=conn, engine=engine)
    logger.info("Database rebuild complete")


def reset_kiosk_output_table(conn: Any) -> None:
    """Clear kiosk_output records and commit the reset transaction."""
    query = "TRUNCATE TABLE kiosk_output"
    with conn.cursor() as cur:
        cur.execute(query)
    conn.commit()
    logger.info("kiosk_output table reset complete")


def decode_message(message: str | bytes | None) -> dict[str, Any] | None:
    """Decode message value as JSON; returns None for empty payloads."""
    if message is None:
        return None
    return json.loads(message)


def validate_event_structure(event: dict) -> bool:
    """Validate the structure of the event payload."""
    required_fields = ["at", "site", "val"]
    return all(field in event for field in required_fields)


def validate_event_types(event: dict) -> bool:
    """Validate the types of the event fields."""
    if not isinstance(event.get("at"), str):
        return False
    if not isinstance(event.get("site"), str):
        return False
    if not isinstance(event.get("val"), int):
        return False
    if "type" in event:
        if not isinstance(event.get("type"), int):
            return False
    return True


def validate_event_site_isdigit(event: dict) -> bool:
    """Validate that the 'site' field is a string of digits."""
    site = event.get("site")
    if not isinstance(site, str) or not site.isdigit():
        return False
    return True


def get_exhibit_ids(conn) -> set:
    """Retrieve all exhibit IDs from the database."""
    query = "SELECT exhibit_id FROM exhibit"
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return {row[0] for row in result}


def validate_event_exhibit_in_db(event: dict, exhibit_ids: set) -> bool:
    """Validate that the event's exhibit ID is in the set of known exhibit IDs."""
    if int(event.get("site")) not in exhibit_ids:
        return False
    return True


def validate_event_at_timestamp(event: dict) -> bool:
    """Validate the 'at' timestamp field of the event is a timestamp."""
    try:
        datetime.fromisoformat(event["at"])
    except ValueError:
        return False
    return True


def validate_event_type_relationship(event: dict) -> bool:
    """Validate the relationship between 'type' and 'val' fields."""
    if event.get("val") == -1 and "type" not in event:
        return False
    if event.get("val") == -1 and event.get("type") not in {0, 1}:
        return False
    return True


def validate_event_val_ranges(event: dict) -> bool:
    """Validate the values of the event fields."""
    if event["val"] not in {-1, 0, 1, 2, 3, 4}:
        return False
    return True


def validate_event_typ_ranges(event: dict) -> bool:
    """Validate the values of the event fields."""
    if event.get("type") not in {0, 1, None}:
        return False
    return True


def validate_event_at_ranges(event: dict) -> bool:
    """Validate the timestamp in the at field is between 8.45am and 6.15pm."""
    try:
        at_time = datetime.fromisoformat(event["at"]).time()
        if not (at_time >= datetime.strptime("08:45", "%H:%M").time() and at_time <= datetime.strptime("18:15", "%H:%M").time()):
            return False
    except ValueError:
        return False
    return True


def validate_event(event: Any, exhibit_ids: set) -> bool:
    """Validate lmnh event payload. Invalid payloads return False."""
    if not isinstance(event, dict):
        logger.warning("Skipping message: value is not a JSON object")
        return False

    if not validate_event_structure(event):
        logger.warning(
            "Skipping message: missing required fields (present fields: %s)",
            ", ".join(list(event.keys())),
        )
        return False

    if not validate_event_types(event):
        logger.warning(
            "Skipping message: invalid field types (%s)",
            ", ".join(f"{k}: {type(v).__name__}" for k, v in event.items()),
        )
        return False

    if not validate_event_site_isdigit(event):
        logger.warning(
            "Skipping message: 'site' field is not a string of digits (site: %s)",
            event.get("site"),
        )
        return False

    if not validate_event_type_relationship(event):
        logger.warning(
            "Skipping message: 'type' field is missing or invalid when 'val' is -1 (val: %s, type: %s)",
            event.get("val"),
            event.get("type"),
        )
        return False

    if not validate_event_exhibit_in_db(event, exhibit_ids):
        logger.warning(
            "Skipping message: 'site' field not found in database (site: %s)",
            event.get("site"),
        )
        return False

    if not validate_event_at_timestamp(event):
        logger.warning(
            "Skipping message: 'at' field is not a valid timestamp (at: %s)",
            event.get("at"),
        )
        return False

    if not validate_event_at_ranges(event):
        logger.warning(
            "Skipping message: 'at' field out of range (at: %s)",
            event.get("at"),
        )
        return False

    if not validate_event_val_ranges(event):
        logger.warning(
            "Skipping message: 'val' field out of range (val: %s)",
            event.get("val"),
        )
        return False

    if not validate_event_typ_ranges(event):
        logger.warning(
            "Skipping message: 'type' field out of range (type: %s)",
            event.get("type"),
        )
        return False

    return True


def create_kafka_consumer(config: dict[str, str], group_id: str, offset_reset: str) -> Consumer:
    """Create and subscribe a Kafka consumer to topic from environment."""
    bootstrap_servers = config.get("KAFKA_BOOTSTRAP_SERVERS")
    topic = config.get("KAFKA_TOPIC")
    security_protocol = config.get("KAFKA_SECURITY_PROTOCOL")
    sasl_mechanism = config.get("KAFKA_SASL_MECHANISM")
    sasl_username = config.get("KAFKA_SASL_USERNAME")
    sasl_password = config.get("KAFKA_SASL_PASSWORD")

    if not bootstrap_servers:
        raise ValueError("Missing KAFKA_BOOTSTRAP_SERVERS in environment")
    if not topic:
        raise ValueError("Missing KAFKA_TOPIC in environment")

    consumer_config = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": offset_reset,
        "enable.auto.commit": False,
        "security.protocol": security_protocol,
        "sasl.mechanism": sasl_mechanism,
        "sasl.username": sasl_username,
        "sasl.password": sasl_password,
    }

    logger.info("Creating Kafka consumer for topic '%s'", topic)
    consumer = Consumer(consumer_config)
    consumer.subscribe([topic])
    logger.info("Kafka consumer subscribed to topic '%s'", topic)
    return consumer


def consume_batch(
    consumer: Consumer,
    batch_size: int,
    exhibit_ids: set,
) -> pd.DataFrame:
    """Consume, clean, and validate messages from lmnh topic."""
    if batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")

    processed_events: list[dict] = []
    polled_count = 0
    invalid = 0
    valid_count = 0

    try:
        while valid_count < batch_size:
            message = consumer.poll(1)
            if message:
                polled_count += 1

                readable_timestamp = datetime.now(timezone.utc)

                logger.debug(
                    "Received message topic: %s, partition: %s, offset: %s, timestamp: %s",
                    message.topic(),
                    message.partition(),
                    message.offset(),
                    readable_timestamp
                )
                logger.debug("Polled message: %s", message)
                try:
                    decoded_message = decode_message(message.value())
                except json.JSONDecodeError:
                    invalid += 1
                    logger.warning("Skipping. Message is not valid JSON")
                    continue

                if decoded_message is None:
                    invalid += 1
                    logger.warning("Skipping. Message is empty")
                    continue

                if not validate_event(decoded_message, exhibit_ids):

                    invalid += 1
                    continue

                valid_count += 1
                processed_events.append(decoded_message)
                logger.debug("Valid event accepted: %s", decoded_message)

            else:
                logger.debug("No message available in current poll interval")
                continue

    finally:
        logger.info("Batch complete. polled=%s valid=%s invalid=%s",
                    polled_count,
                    len(processed_events),
                    invalid,
                    )

    return pd.DataFrame(processed_events)


def run_and_insert_batch(
    consumer,
    batch_size,
    exhibit_ids,
    description_button_id_dict,
    value_button_id_dict,
    engine,
) -> None:
    """Consume a batch of messages and insert them into the database."""
    logger.info("Starting lmnh Kafka consumer batch. batch_size=%s", batch_size)

    events = consume_batch(
        consumer,
        batch_size=batch_size,
        exhibit_ids=exhibit_ids,
    )

    kiosk_output_data = build_kiosk_output_table(description_button_id_dict,
                                                 value_button_id_dict, events)

    while True:
        try:
            kiosk_output_data.to_sql(
                "kiosk_output",
                engine,
                if_exists="append",
                index=False,
            )
            break
        except Exception:
            logger.error(
                "DB insert failed; retrying in %s seconds",
                DB_RETRY_SECONDS,
            )
            time.sleep(DB_RETRY_SECONDS)

    # Commit offsets only after DB write succeeds to avoid losing messages.
    consumer.commit(asynchronous=False)
    logger.info("Inserted %s kiosk output records", len(kiosk_output_data))


if __name__ == "__main__":
    args = parse_args()
    load_dotenv()
    config: dict[str, str] = dict(environ)
    configure_logging(verbose=args.verbose)

    conn = None
    engine = None
    kafka_consumer = None
    startup_ok = False

    try:
        logger.info("Establishing database connection")
        conn = get_db_connection(config)
        engine = get_db_engine(config)

        if args.reset_db:
            reset_entire_database(config, conn, engine)

        if args.reset_kiosk_output:
            logger.info(
                "--reset_kiosk_output enabled: resetting kiosk_output table")
            reset_kiosk_output_table(conn)

        group_id = load_saved_group_id()
        if args.reset_kiosk_output or args.reset_db or group_id is None:
            create_and_save_group_id(prefix=get_group_id_prefix(config))
            group_id = load_saved_group_id()

        kafka_consumer = create_kafka_consumer(
            config, group_id=group_id, offset_reset="earliest")

        # Get button ID mappings
        description_button_id_dict = get_description_button_id_dict(conn)
        value_button_id_dict = get_value_button_id_dict(conn)
        exhibit_ids = get_exhibit_ids(conn)
        startup_ok = True

        # Batch process messages from Kafka topic and insert into database
        while True:
            run_and_insert_batch(
                consumer=kafka_consumer,
                batch_size=1,
                exhibit_ids=exhibit_ids,
                description_button_id_dict=description_button_id_dict,
                value_button_id_dict=value_button_id_dict,
                engine=engine,
            )
    except Exception:
        if startup_ok:
            logger.error("Batch processing failed. Exiting.")
        else:
            logger.error(
                "Failed to establish startup resources. Check configuration and connectivity. Exiting.")
    finally:
        try:
            if conn:
                conn.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error("Error closing database connection: %s", e)

        try:
            if engine:
                engine.dispose()
                logger.info("Database engine disposed")
        except Exception as e:
            logger.error("Error disposing database engine: %s", e)

        try:
            if kafka_consumer:
                kafka_consumer.close()
                logger.info("Kafka consumer closed")
        except Exception as e:
            logger.error("Error closing Kafka consumer: %s", e)
