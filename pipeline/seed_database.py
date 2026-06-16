import os
import logging
from os import environ
import sys
from typing import Any
from dotenv import load_dotenv

from extract import convert_list_of_dicts_to_csv, delete_local_files, download_data_from_s3_with_suffix, get_s3_client, extract_s3_bucket_object_names, json_files_to_list
from load import build_button_table, build_button_type_table, build_department_table, build_exhibit_table, build_floor_table, create_schema_tables, drop_schema_tables, get_button_type_id_dict, get_db_connection, get_db_engine, get_department_id_dict, get_floor_id_dict, load_clean_exhibition_csv
from transform import clean_exhibition_data, load_exhibition_csv, validate_raw_exhibition_data


def download_and_format_exhibition_data_from_s3_bucket(s3_client: Any, bucket_name) -> None:
    """
    Extracts exhibition data from an S3 bucket and saves it to local files.
    Converts the exhibition data from JSON to CSV format.
    """
    download_data_from_s3_with_suffix(s3_client, bucket_name, suffix=".json")

    exhibition_file_names = extract_s3_bucket_object_names(
        bucket_name, s3_client, prefix="lmnh", suffix=".json")

    data = json_files_to_list(exhibition_file_names)
    convert_list_of_dicts_to_csv(data, "exhibition_data.csv")

    delete_local_files(exhibition_file_names)


def clean_up_temp_extract_exhibition_data() -> None:
    """Deletes local temporary files."""
    try:
        os.remove("exhibition_data.csv")
    except FileNotFoundError:
        pass
    except OSError as e:
        raise Exception(
            f"Error deleting temporary file exhibition_data.csv: {e}")


def clean_up_temp_transform_clean_exhibition_data() -> None:
    """Delete temporary transform output files."""
    try:
        os.remove("clean_exhibition.csv")
    except FileNotFoundError:
        pass
    except OSError as e:
        raise Exception(
            f"Error deleting temporary file clean_exhibition.csv: {e}")


def generate_seed_data():
    exhibition_data = load_exhibition_csv()

    clean_exhibition_data(exhibition_data)

    exhibition_data = validate_raw_exhibition_data(exhibition_data)

    exhibition_data.to_csv("clean_exhibition.csv", index=False)
    logger.info("Saved clean_exhibition.csv")


def build_and_insert_seed_tables(conn, engine) -> None:
    """Build all tables from cleaned data and insert into database with ID linking."""
    # Load cleaned data from transform phase
    exhibition_data = load_clean_exhibition_csv()

    # Build floor table and insert
    floor_data = build_floor_table(exhibition_data)
    floor_data.to_sql("floor", engine, if_exists="append", index=False)
    logger.info(f"Inserted {len(floor_data)} floor records")

    # Build department table and insert
    department_data = build_department_table(exhibition_data)
    department_data.to_sql("department", engine,
                           if_exists="append", index=False)
    logger.info(f"Inserted {len(department_data)} department records")

    # Get ID mappings from database
    department_id_dict = get_department_id_dict(conn)
    floor_id_dict = get_floor_id_dict(conn)

    # Build and insert exhibit with FK linking
    exhibit_data = build_exhibit_table(
        department_id_dict, floor_id_dict, exhibition_data)
    exhibit_data.to_sql("exhibit", engine, if_exists="append", index=False)
    logger.info(f"Inserted {len(exhibit_data)} exhibit records")

    # Build button types and insert
    button_type_data = build_button_type_table()
    button_type_data.to_sql("button_type", engine,
                            if_exists="append", index=False)
    logger.info(f"Inserted {len(button_type_data)} button type records")

    # Get button type ID mapping
    button_type_id_dict = get_button_type_id_dict(conn)

    # Build and insert button with FK linking
    button_data = build_button_table(button_type_id_dict)
    button_data.to_sql("button", engine, if_exists="append", index=False)
    logger.info(f"Inserted {len(button_data)} button records")


if __name__ == "__main__":
    load_dotenv()
    config: dict[str, str] = dict(environ)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger = logging.getLogger(__name__)

    conn = None
    engine = None
    try:
        # Extract phase

        logger.info(
            f"Starting extraction phase from S3 bucket: {config.get('BUCKET_NAME')}...")
        try:
            s3_client = get_s3_client(config)
            logger.info("S3 client initialized")

            download_and_format_exhibition_data_from_s3_bucket(
                s3_client, config.get('BUCKET_NAME'))
            logger.info("Data download and formatting completed")

        except Exception as e:
            logger.error(f"Error in extract module: {e}")
            sys.exit(1)

        # Transform phase

        logger.info("Starting transformation phase...")
        try:
            generate_seed_data()
            logger.info("Transformation phase completed")

        except Exception as e:
            logger.error(f"Error in transform module: {e}")
            sys.exit(1)

        # Load phase
        logger.info("Starting load phase...")
        try:
            # Create database connections once for load phase
            engine = get_db_engine(config)
            conn = get_db_connection(config)
            logger.info("Database connections established")

            drop_schema_tables(conn)

            create_schema_tables(conn)

            build_and_insert_seed_tables(conn, engine)
            logger.info("Load phase completed")

        except Exception as e:
            logger.error(f"Error in load module: {e}")
            sys.exit(1)

        # Cleanup phase
        try:

            clean_up_temp_extract_exhibition_data()
            logger.info("Temporary extracted files cleaned up")
            clean_up_temp_transform_clean_exhibition_data()
            logger.info("Temporary transformed files cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")
            sys.exit(1)

        logger.info("Pipeline completed successfully")

    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
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
            logger.error(f"Error closing database connections: {e}")
