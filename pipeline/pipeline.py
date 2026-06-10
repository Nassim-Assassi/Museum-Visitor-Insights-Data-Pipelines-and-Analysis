import argparse
import logging
import sys
from os import environ, _Environ

from dotenv import load_dotenv

from extract import get_s3_client, download_and_format_data_from_s3_bucket, clean_up_temp_files
from seed_database import (
    get_db_engine,
    get_db_connection,
    load_exhibition_csv,
    load_historical_csv,
    clean_exhibition_data,
    validate_exhibition_data,
    validate_historical_data,
    drop_schema_tables,
    create_schema_tables,
    build_and_insert_tables,
)


def setup_logging(level=logging.INFO):
    """Configure logging for the pipeline."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="ETL pipeline for museum kiosk data"
    )
    parser.add_argument(
        "--bucket",
        default="sigma-resources-museum",
        help="S3 bucket name for data extraction (default: sigma-resources-museum)",
    )
    parser.add_argument(
        "--schema",
        default="schema.sql",
        help="Path to a custom schema.sql file (default: schema.sql)",
    )
    parser.add_argument(
        "--etl",
        action="store_true",
        help="Run full ETL pipeline (extract, transform, load)",
    )
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Run extraction phase",
    )
    parser.add_argument(
        "--transform",
        action="store_true",
        help="Run transformation phase",
    )
    parser.add_argument(
        "--load",
        action="store_true",
        help="Run load phase",
    )
    return parser.parse_args()


if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)

    args = parse_arguments()
    logger.info("Pipeline started with arguments: %s", args)

    # If --etl is specified, or no phase flags are specified, run all phases
    if args.etl or (not args.extract and not args.transform and not args.load):
        args.extract = True
        args.transform = True
        args.load = True
        if args.etl:
            logger.info("Running full ETL pipeline (--etl flag)")
        else:
            logger.info(
                "No phase flags specified, running full ETL pipeline by default")

    # Load environment variables
    load_dotenv()
    logger.info("Environment variables loaded")

    # Initialize variables
    engine = None
    conn = None
    exhibition_data = None
    historical_data = None

    try:
        # Extract phase
        if args.extract:
            logger.info(
                "Starting extraction phase from bucket: %s...", args.bucket)
            s3_client = get_s3_client(environ)
            download_and_format_data_from_s3_bucket(s3_client, args.bucket)
            logger.info("Extraction phase completed")
        else:
            logger.info("Skipping extraction phase")

        # Transform phase
        if args.transform:
            logger.info("Starting transformation phase...")

            logger.info("Loading exhibition data...")
            exhibition_data = load_exhibition_csv()
            logger.info("Loaded %d exhibition records", len(exhibition_data))

            logger.info("Loading historical data...")
            historical_data = load_historical_csv()
            logger.info("Loaded %d historical records", len(historical_data))

            logger.info("Cleaning exhibition data...")
            clean_exhibition_data(exhibition_data)

            # Validate data
            logger.info("Validating exhibition data...")
            exhibition_data = validate_exhibition_data(exhibition_data)
            logger.info("Exhibition data validated: %d records",
                        len(exhibition_data))

            logger.info("Validating historical data...")
            historical_data = validate_historical_data(historical_data)
            logger.info("Historical data validated: %d records",
                        len(historical_data))

            logger.info("Transformation phase completed")
        else:
            logger.info("Skipping transformation phase")

        # Load phase
        if args.load:
            logger.info("Starting load phase...")

            # Database operations
            logger.info("Connecting to database...")
            engine = get_db_engine(environ)
            conn = get_db_connection(environ)
            logger.info("Database connection established")

            logger.info("Dropping existing tables...")
            drop_schema_tables(conn)
            logger.info("Creating schema tables from %s...", args.schema)
            create_schema_tables(conn, args.schema)
            logger.info("Schema tables created")

            logger.info("Inserting data into database...")
            build_and_insert_tables(
                conn, engine, exhibition_data, historical_data)
            logger.info("Data insertion completed successfully")

            logger.info("Load phase completed")
        else:
            logger.info("Skipping load phase")

        logger.info("Pipeline completed successfully")

    except Exception as e:
        logger.exception("Pipeline failed with error: %s", str(e))
        sys.exit(1)

    finally:
        try:
            if conn is not None:
                conn.close()
            if engine is not None:
                engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.warning("Error closing database connections: %s", str(e))
