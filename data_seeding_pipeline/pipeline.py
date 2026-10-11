import argparse
import sys
from os import environ

from dotenv import load_dotenv

from .extract import clean_up_temp_extract_files, get_s3_client, download_and_format_data_from_s3_bucket
from .transform import run_transform, clean_up_temp_transform_files
from .load import run_load, verify_clean_files_exist, get_db_engine, get_db_connection
from .logging_config import configure_logging, get_logger


logger = get_logger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="ETL pipeline for museum kiosk data"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
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
    load_dotenv()
    config: dict[str, str] = dict(environ)

    args = parse_arguments()

    configure_logging(verbose=args.verbose)

    logger.info("Pipeline started with arguments: %s", args)

    # Determine which phases to run
    # Extract and load without transform is not a valid combination, since transform is needed to produce the cleaned files for load
    if args.extract and args.load and not args.transform:
        logger.error(
            "Invalid combination of flags: --extract and --load cannot be used without --transform. Exiting."
        )
        sys.exit(1)

    # If no flags specified, default to running all phases
    if not args.etl and not args.extract and not args.transform and not args.load:
        args.extract = True
        args.transform = True
        args.load = True
        logger.info(
            "No phase flags specified, running full ETL pipeline by default")

     # If etl flag specified, run all phases
    elif args.etl:
        args.extract = True
        args.transform = True
        args.load = True
        logger.info("Running full ETL pipeline (--etl flag)")

    conn = None
    engine = None

    try:
        # Extract phase
        if args.extract:
            logger.info(
                "Starting extraction phase from bucket: %s...", args.bucket)
            try:
                s3_client = get_s3_client(config)
                logger.info("S3 client initialized")

                download_and_format_data_from_s3_bucket(s3_client, args.bucket)
                logger.info("Data download and formatting completed")

            except Exception as e:
                logger.error("Error in extract module: %s", e)
                sys.exit(1)

        # Transform phase
        if args.transform:
            logger.info("Starting transformation phase...")
            try:
                run_transform()
                logger.info("Transformation phase completed")
            except Exception as e:
                logger.error("Error in transform module: %s", e)
                sys.exit(1)

        # Load phase
        if args.load:
            logger.info("Starting load phase...")
            try:
                # Create database connections once for load phase
                engine = get_db_engine(config)
                conn = get_db_connection(config)
                logger.info("Database connections established")

                verify_clean_files_exist()
                run_load(conn, engine, args.schema)
                logger.info("Load phase completed")

            except Exception as e:
                logger.error("Error in load module: %s", e)
                sys.exit(1)

        # Cleanup phase
        try:
            if args.extract and args.transform:
                clean_up_temp_extract_files()
                logger.info("Temporary extracted files cleaned up")
            if args.transform and args.load:
                clean_up_temp_transform_files()
                logger.info("Temporary transformed files cleaned up")
        except Exception as e:
            logger.error("Error cleaning up temporary files: %s", e)
            sys.exit(1)

        logger.info("Pipeline completed successfully")

    except Exception as e:
        logger.error("Pipeline failed: %s", e)
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
