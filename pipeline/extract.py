import logging
import os
from os import environ, _Environ

import json
import sys
from botocore.exceptions import ClientError
from boto3 import client

from dotenv import load_dotenv

import pandas as pd

logger = logging.getLogger(__name__)


def get_s3_client(config: _Environ) -> client:
    """Returns an S3 client using the provided configuration."""
    s3_client = client(
        "s3",
        aws_access_key_id=config.get("ACCESS_KEY"),
        aws_secret_access_key=config.get("SECRET_ACCESS_KEY")
    )
    return s3_client


def extract_s3_bucket_object_names(bucket_name: str, s3_client: client, prefix: str = "", suffix: str = "") -> list[str]:
    """Extracts the names of all objects in an S3 bucket with a given prefix and suffix and returns them as a list."""
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name, Prefix=prefix)

        contents = response.get("Contents")
        if contents is None:
            raise ValueError(
                f"No objects found in bucket {bucket_name} with prefix {prefix}")

        object_names = sorted(
            [obj["Key"] for obj in contents if obj["Key"].endswith(suffix)]
        )
        logger.debug(
            f"Found {len(object_names)} objects in bucket {bucket_name} with suffix {suffix}"
        )
        return object_names
    except ClientError as e:
        raise Exception(
            f"Failed to list objects from S3 bucket {bucket_name}"
        )


def extract_object_from_S3_bucket(bucket_name: str, file_name: str, s3_client: client, save_dir: str = ".") -> None:
    """Extracts an object from an S3 bucket and saves it to a local file."""
    try:
        s3_client.download_file(bucket_name, file_name,
                                f"{save_dir}/{file_name}")
        logger.debug(
            f"Downloaded {file_name} from bucket {bucket_name} to {save_dir}"
        )
    except ClientError as e:
        raise Exception(
            f"Failed to download {file_name} from S3 bucket {bucket_name}")


def extract_objects_from_S3_bucket(bucket_name: str, file_names: list[str], s3_client: client, save_dir: str = ".") -> None:
    """Extracts objects from an S3 bucket and saves them to local files."""
    for file_name in file_names:
        extract_object_from_S3_bucket(
            bucket_name, file_name, s3_client, save_dir)


def download_exhibition_data(s3_client: client, bucket_name: str = "sigma-resources-museum") -> None:
    lmnh_exhibition_object_names = extract_s3_bucket_object_names(
        bucket_name, s3_client, prefix="lmnh", suffix=".json")

    extract_objects_from_S3_bucket(
        bucket_name, lmnh_exhibition_object_names, s3_client)


def download_historical_data(s3_client: client, bucket_name: str = "sigma-resources-museum") -> None:
    lmnh_historical_data_object_names = extract_s3_bucket_object_names(
        bucket_name, s3_client,  prefix="lmnh", suffix=".csv")

    extract_objects_from_S3_bucket(
        bucket_name, lmnh_historical_data_object_names, s3_client)


def combine_csv_files(file_names: list[str], output_file_name: str) -> None:
    """Combines multiple CSV files into a single CSV file."""
    try:
        with open(output_file_name, "w") as output_file:
            for i, file_name in enumerate(file_names):
                with open(file_name, "r") as input_file:
                    if i != 0:
                        # Skip the header row for all but the first file
                        next(input_file)
                    output_file.write(input_file.read())
        logger.info(
            f"Combined {len(file_names)} CSV files into {output_file_name}"
        )
    except IOError as e:
        logger.error(f"Error combining CSV files: {e}")
        raise


def delete_local_files(file_names: list[str]) -> None:
    """Deletes local files."""
    for file_name in file_names:
        try:
            os.remove(file_name)
            logger.debug(f"Deleted file {file_name}")
        except FileNotFoundError:
            logger.warning(f"File not found, skipping deletion: {file_name}")
        except OSError as e:
            logger.error(f"Error deleting file {file_name}: {e}")


def json_files_to_list(file_names: list[str]) -> list[dict]:
    """Reads JSON files and returns their contents as a list of dictionaries."""
    data = []
    for file_name in file_names:
        try:
            with open(file_name, "r") as f:
                data.append(json.load(f))
            logger.debug(f"Loaded JSON from {file_name}")
        except (IOError, json.JSONDecodeError) as e:
            raise Exception(f"Failed to load JSON file {file_name}")
    logger.info(f"Loaded {len(file_names)} JSON files")
    return data


def convert_list_of_dicts_to_csv(data: list[dict], output_file_name: str) -> None:
    """Converts a list of dictionaries to a CSV file."""
    try:
        df = pd.DataFrame(data)
        df.to_csv(output_file_name, index=False)
        logger.info(
            f"Converted {len(data)} JSON records to CSV file {output_file_name}"
        )
    except Exception as e:
        raise Exception(f"Failed to convert data to CSV: {output_file_name}")


def download_and_format_data_from_s3_bucket(s3_client: client, bucket_name) -> None:
    """
    Extracts all relevant data from an S3 bucket and saves it to local files.
    Combines the historical data into a single CSV file and converts the exhibition data from JSON to CSV format.
    """
    download_historical_data(s3_client, bucket_name)

    historical_file_names = extract_s3_bucket_object_names(
        bucket_name, s3_client, prefix="lmnh", suffix=".csv")

    combine_csv_files(historical_file_names,
                      "historical_data.csv")

    delete_local_files(historical_file_names)

    download_exhibition_data(s3_client, bucket_name)

    exhibition_file_names = extract_s3_bucket_object_names(
        bucket_name, s3_client, prefix="lmnh", suffix=".json")

    data = json_files_to_list(exhibition_file_names)
    convert_list_of_dicts_to_csv(data, "exhibition_data.csv")

    delete_local_files(exhibition_file_names)


def clean_up_temp_extract_files() -> None:
    """Deletes local temporary files."""
    for file_name in ["exhibition_data.csv", "historical_data.csv"]:
        try:
            os.remove(file_name)
        except FileNotFoundError:
            pass
        except OSError as e:
            raise Exception(f"Error deleting temporary file {file_name}: {e}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("Extract module started")

    load_dotenv()

    try:
        s3_client = get_s3_client(environ)
        logger.info("S3 client initialized")

        download_and_format_data_from_s3_bucket(
            s3_client, bucket_name="sigma-resources-museum")
        logger.info("Data download and formatting completed")

    except Exception as e:
        logger.error(e)
        sys.exit(1)
