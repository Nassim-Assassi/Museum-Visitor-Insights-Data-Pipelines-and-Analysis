from os import environ
import sys
from dotenv import load_dotenv
from datetime import datetime, timezone

from live_pipeline import create_kafka_consumer, consume_batch, get_exhibit_ids
from email_sender import send_email, verify_smtp_vars
from logging_config import get_logger, configure_logging
from load import get_db_connection

logger = get_logger(__name__)


def to_int_or_none(value):
    """Convert value to int when possible; return None on invalid input."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def within_recent_window(timestamp_str: str, minutes: int) -> bool:
    """Check if a timestamp string is within a recent time window (default 5 minutes)."""
    try:
        event_time = datetime.fromisoformat(timestamp_str)
        now = datetime.now(timezone.utc)
        # Ensure event_time is timezone-aware
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
        time_diff = abs((now - event_time).total_seconds())
        return time_diff <= (minutes * 60)
    except (ValueError, TypeError):
        return False


def get_email_body(event: dict, exhibit_name_dict: dict) -> str:
    """Generate the email body for the emergency event."""
    site = event.get("site")
    try:
        site_id = int(site)
    except (TypeError, ValueError):
        site_id = site

    exhibit_name = exhibit_name_dict.get(site_id)
    return f"Emergency event detected:\n\nTimestamp: {event.get('at')}\nExhibit Name: {exhibit_name}\nPlease take immediate action."


def get_exhibit_name_dict(conn) -> dict[str, str]:
    """Fetch exhibit names from the database and return a mapping of exhibit ID to exhibit name."""
    exhibit_name_dict = {}
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT exhibit_id, name FROM exhibit")
            for row in cursor.fetchall():
                exhibit_id, name = row
                exhibit_name_dict[exhibit_id] = name
    except Exception as e:
        logger.error("Error fetching exhibit names: %s", e)
    return exhibit_name_dict


if __name__ == "__main__":
    load_dotenv()
    config: dict[str, str] = dict(environ)
    configure_logging()

    if not verify_smtp_vars(config):
        logger.error("Missing required SMTP environment variables.")
        sys.exit(1)

    if not config.get("KAFKA_BOOTSTRAP_SERVERS") or not config.get("KAFKA_TOPIC"):
        logger.error("Missing required Kafka environment variables.")
        sys.exit(1)

    if not config.get("INFRASTRUCTURE_NAME"):
        logger.error(
            "Missing required INFRASTRUCTURE_NAME environment variable.")
        sys.exit(1)

    conn = None
    kafka_consumer = None
    startup_ok = False

    try:
        conn = get_db_connection(config)
        exhibit_ids = get_exhibit_ids(conn)
        exhibit_name_dict = get_exhibit_name_dict(conn)

        group_id = f"{config.get('INFRASTRUCTURE_NAME')}_emergency_notifier_group"
        kafka_consumer = create_kafka_consumer(
            config, group_id, offset_reset="latest")

        startup_ok = True

        while True:

            events = consume_batch(kafka_consumer, 1, exhibit_ids)
            event = events.iloc[0]

            event_val = to_int_or_none(event.get("val"))
            event_type = to_int_or_none(event.get("type"))

            # Emergency is indicated by val == -1 and type == 1
            is_emergency = event_val == -1 and event_type == 1
            is_recent = within_recent_window(event.get("at", ""), minutes=60)
            logger.info(
                "Received event: %s | is_emergency=%s, is_recent=%s",
                event,
                is_emergency,
                is_recent,
            )
            if is_emergency and is_recent:
                logger.info(f"Emergency event received: {event}")
                logger.info("Notifying museum staff about the emergency.")
                send_email(
                    config=config,
                    subject="Museum Emergency Alert",
                    body=get_email_body(event, exhibit_name_dict),
                )
            elif is_emergency:
                logger.info(
                    "Skipping stale emergency event older than 60 minutes: %s", event)

            # Commit every processed event (emergency or not) to avoid replay loops.
            kafka_consumer.commit(asynchronous=False)

    except Exception as e:
        if startup_ok:
            logger.error(f"Error during Kafka polling: {e}")
        else:
            logger.error(
                f"Failed to establish startup resources. Check configuration and connectivity. Error: {e}")
            sys.exit(1)
    finally:
        try:
            if conn:
                conn.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error("Error closing database connection: %s", e)

        try:
            if kafka_consumer:
                kafka_consumer.close()
                logger.info("Kafka consumer closed")
        except Exception as e:
            logger.error("Error closing Kafka consumer: %s", e)
