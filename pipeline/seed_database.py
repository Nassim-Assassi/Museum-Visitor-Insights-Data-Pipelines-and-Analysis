import os
from os import environ
from pathlib import Path
import sys
from typing import Any
from dotenv import load_dotenv

import extract as extract_phase
import load as load_phase
import transform as transform_phase
from logging_config import configure_logging, get_logger
from temp_paths import CLEAN_EXHIBITION_FILE, EXHIBITION_DATA_FILE, TEMP_DIR


logger = get_logger(__name__)


def run_seed_database(
    config: dict[str, str],
    conn: Any,
    engine: Any,
) -> None:
    """Run full seed pipeline using caller-provided DB connection resources."""
    logger.info(
        "Starting extraction phase from S3 bucket: %s...",
        config.get("BUCKET_NAME"),
    )
    s3_client = extract_phase.get_s3_client(config)
    logger.info("S3 client initialized")
    download_and_format_exhibition_data_from_s3_bucket(
        s3_client, config.get("BUCKET_NAME")
    )
    logger.info("Data download and formatting completed")

    logger.info("Starting transformation phase...")
    generate_seed_data()
    logger.info("Transformation phase completed")

    logger.info("Starting load phase...")
    logger.info("Using caller-provided database connections")

    load_phase.drop_schema_tables(conn)
    load_phase.create_schema_tables(conn)
    build_and_insert_seed_tables(conn, engine)
    logger.info("Load phase completed")

    clean_up_temp_extract_exhibition_data()
    logger.info("Temporary extracted files cleaned up")
    clean_up_temp_transform_clean_exhibition_data()
    logger.info("Temporary transformed files cleaned up")

    logger.info("Pipeline completed successfully")


def download_and_format_exhibition_data_from_s3_bucket(s3_client: Any, bucket_name) -> None:
    """
    Extracts exhibition data from an S3 bucket and saves it to local files.
    Converts the exhibition data from JSON to CSV format.
    """
    extract_phase.download_data_from_s3_with_suffix(
        s3_client, bucket_name, suffix=".json")

    exhibition_file_names = extract_phase.extract_s3_bucket_object_names(
        bucket_name, s3_client, prefix="lmnh", suffix=".json")
    local_exhibition_files = [
        str(TEMP_DIR / Path(file_name).name) for file_name in exhibition_file_names
    ]

    data = extract_phase.json_files_to_list(local_exhibition_files)
    extract_phase.convert_list_of_dicts_to_csv(data, str(EXHIBITION_DATA_FILE))

    extract_phase.delete_local_files(local_exhibition_files)


def clean_up_temp_extract_exhibition_data() -> None:
    """Deletes local temporary files."""
    try:
        EXHIBITION_DATA_FILE.unlink()
    except FileNotFoundError:
        pass
    except OSError as e:
        raise Exception(
            f"Error deleting temporary file exhibition_data.csv: {e}")


def clean_up_temp_transform_clean_exhibition_data() -> None:
    """Delete temporary transform output files."""
    try:
        CLEAN_EXHIBITION_FILE.unlink()
    except FileNotFoundError:
        pass
    except OSError as e:
        raise Exception(
            f"Error deleting temporary file clean_exhibition.csv: {e}")


def generate_seed_data():
    exhibition_data = transform_phase.load_exhibition_csv()

    transform_phase.clean_exhibition_data(exhibition_data)

    exhibition_data = transform_phase.validate_raw_exhibition_data(
        exhibition_data)

    exhibition_data.to_csv(CLEAN_EXHIBITION_FILE, index=False)
    logger.info("Saved clean_exhibition.csv")


def build_and_insert_seed_tables(conn, engine) -> None:
    """Build all tables from cleaned data and insert into database with ID linking."""
    # Load cleaned data from transform phase
    exhibition_data = load_phase.load_clean_exhibition_csv()

    # Build floor table and insert
    floor_data = load_phase.build_floor_table(exhibition_data)
    floor_data.to_sql("floor", engine, if_exists="append", index=False)
    logger.info("Inserted %s floor records", len(floor_data))

    # Build department table and insert
    department_data = load_phase.build_department_table(exhibition_data)
    department_data.to_sql("department", engine,
                           if_exists="append", index=False)
    logger.info("Inserted %s department records", len(department_data))

    # Get ID mappings from database
    department_id_dict = load_phase.get_department_id_dict(conn)
    floor_id_dict = load_phase.get_floor_id_dict(conn)

    # Build and insert exhibit with FK linking
    exhibit_data = load_phase.build_exhibit_table(
        department_id_dict, floor_id_dict, exhibition_data)
    exhibit_data.to_sql("exhibit", engine, if_exists="append", index=False)
    logger.info("Inserted %s exhibit records", len(exhibit_data))

    # Build button types and insert
    button_type_data = load_phase.build_button_type_table()
    button_type_data.to_sql("button_type", engine,
                            if_exists="append", index=False)
    logger.info("Inserted %s button type records", len(button_type_data))

    # Get button type ID mapping
    button_type_id_dict = load_phase.get_button_type_id_dict(conn)

    # Build and insert button with FK linking
    button_data = load_phase.build_button_table(button_type_id_dict)
    button_data.to_sql("button", engine, if_exists="append", index=False)
    logger.info("Inserted %s button records", len(button_data))


if __name__ == "__main__":
    load_dotenv()
    config: dict[str, str] = dict(environ)

    configure_logging()
    conn = None
    engine = None
    try:
        engine = load_phase.get_db_engine(config)
        conn = load_phase.get_db_connection(config)
        run_seed_database(config, conn, engine)
    except Exception as e:
        logger.error("Database seeding failed: %s", e)
        sys.exit(1)
    finally:
        try:
            if conn is not None:
                conn.close()
                logger.info("Database connection closed")
            if engine is not None:
                engine.dispose()
                logger.info("Database engine disposed")
        except Exception as e:
            logger.error("Error closing database connections: %s", e)
