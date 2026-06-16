"""Live Kafka consumer for lmnh topic with cleaning, validation, and logging."""
import json
import logging
from datetime import datetime, timezone
from os import environ
from typing import Any

from confluent_kafka import Consumer, KafkaError
from dotenv import load_dotenv
import pandas as pd

from load import build_kiosk_output_table, get_db_engine, get_db_connection, get_description_button_id_dict, get_value_button_id_dict


logger = logging.getLogger(__name__)


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
            f"Skipping message: missing required fields (present fields: {', '.join(list(event.keys()))})")
        return False

    if not validate_event_types(event):
        logger.warning(
            f"Skipping message: invalid field types ({', '.join(f'{k}: {type(v).__name__}' for k, v in event.items())})")
        return False

    if not validate_event_site_isdigit(event):
        logger.warning(
            f"Skipping message: 'site' field is not a string of digits (site: {event.get('site')})")
        return False

    if not validate_event_type_relationship(event):
        logger.warning(
            f"Skipping message: 'type' field is missing or invalid when 'val' is -1 (val: {event.get('val')}, type: {event.get('type')})")
        return False

    if not validate_event_exhibit_in_db(event, exhibit_ids):
        logger.warning(
            f"Skipping message: 'site' field not found in database (site: {event.get('site')})")
        return False

    if not validate_event_at_timestamp(event):
        logger.warning(
            f"Skipping message: 'at' field is not a valid timestamp (at: {event.get('at')})")
        return False

    if not validate_event_at_ranges(event):
        logger.warning(
            f"Skipping message: 'at' field out of range (at: {event.get('at')})")
        return False

    if not validate_event_val_ranges(event):
        logger.warning(
            f"Skipping message: 'val' field out of range (val: {event.get('val')})")
        return False

    if not validate_event_typ_ranges(event):
        logger.warning(
            f"Skipping message: 'type' field out of range (type: {event.get('type')})")
        return False

    return True


def create_kafka_consumer(config: dict[str, str], group_id: str) -> Consumer:
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
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
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


def consume_batch(consumer: Consumer, batch_size: int, exhibit_ids: set) -> pd.DataFrame:
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


def run_and_insert_batch(consumer, batch_size, exhibit_ids, description_button_id_dict, value_button_id_dict, engine) -> None:
    """Consume a batch of messages and insert them into the database."""
    logger.info("Starting lmnh Kafka consumer batch. batch_size=%s", batch_size)

    events = consume_batch(
        consumer, batch_size=batch_size, exhibit_ids=exhibit_ids)

    kiosk_output_data = build_kiosk_output_table(description_button_id_dict,
                                                 value_button_id_dict, events)
    kiosk_output_data.to_sql("kiosk_output", engine,
                             if_exists="append", index=False)
    logger.info(f"Inserted {len(kiosk_output_data)} kiosk output records")


if __name__ == "__main__":
    load_dotenv()
    config: dict[str, str] = dict(environ)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    conn = None
    engine = None
    kafka_consumer = None

    try:
        logger.info("Establishing database connection")
        conn = get_db_connection(config)
        engine = get_db_engine(config)
        kafka_consumer = create_kafka_consumer(
            config, group_id="nassim-lmnh-live-consumer-new1")

        # Get button ID mappings
        description_button_id_dict = get_description_button_id_dict(conn)
        value_button_id_dict = get_value_button_id_dict(conn)
        exhibit_ids = get_exhibit_ids(conn)

        # Batch process messages from Kafka topic and insert into database
        while True:
            run_and_insert_batch(
                consumer=kafka_consumer,
                batch_size=1,
                exhibit_ids=exhibit_ids,
                description_button_id_dict=description_button_id_dict,
                value_button_id_dict=value_button_id_dict,
                engine=engine
            )
    finally:
        try:
            if conn is not None:
                conn.close()
                logger.info("Database connection closed")
            if engine is not None:
                engine.dispose()
                logger.info("Database engine disposed")
            if kafka_consumer is not None:
                kafka_consumer.close()
                logger.info("Kafka consumer closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
