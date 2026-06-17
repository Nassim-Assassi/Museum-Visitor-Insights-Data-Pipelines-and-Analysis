import os

import json
from botocore.exceptions import ClientError
from boto3 import client

import pandas as pd
from logging_config import get_logger

logger = get_logger(__name__)


def get_s3_client(config: dict[str, str]) -> client:
    """Returns an S3 client using the provided configuration."""
    s3_client = client(
        "s3",
        aws_access_key_id=config.get("ACCESS_KEY"),
        aws_secret_access_key=config.get("SECRET_ACCESS_KEY")
    )
    return s3_client


def extract_s3_bucket_object_names(bucket_name: str, s3_client: client, prefix: str = "", suffix: str = "") -> list[str]:
    """Extracts the names of all objects in an S3 bucket with a given prefix and suffix and returns them as a list."""
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
        "Found %s objects in bucket %s with suffix %s",
        len(object_names),
        bucket_name,
        suffix,
    )
    return object_names


def extract_object_from_S3_bucket(bucket_name: str, file_name: str, s3_client: client, save_dir: str = ".") -> None:
    """Extracts an object from an S3 bucket and saves it to a local file."""
    s3_client.download_file(bucket_name, file_name,
                            f"{save_dir}/{file_name}")
    logger.debug(
        "Downloaded %s from bucket %s to %s",
        file_name,
        bucket_name,
        save_dir,
    )


def extract_objects_from_S3_bucket(s3_client: client, bucket_name: str, file_names: list[str],  save_dir: str = ".") -> None:
    """Extracts objects from an S3 bucket and saves them to local files."""
    for file_name in file_names:
        extract_object_from_S3_bucket(
            bucket_name, file_name, s3_client, save_dir)


def download_data_from_s3_with_suffix(s3_client: client, bucket_name: str = "sigma-resources-museum", suffix: str = "") -> None:
    """Downloads data from an S3 bucket with a specific suffix and saves it to local files."""
    object_names = extract_s3_bucket_object_names(
        bucket_name, s3_client, prefix="lmnh", suffix=suffix)
    extract_objects_from_S3_bucket(s3_client, bucket_name, object_names)


def combine_csv_files(file_names: list[str], output_file_name: str) -> None:
    """Combines multiple CSV files into a single CSV file."""
    with open(output_file_name, "w", encoding="utf-8") as output_file:
        for i, file_name in enumerate(file_names):
            with open(file_name, "r", encoding="utf-8") as input_file:
                if i != 0:
                    # Skip the header row for all but the first file
                    next(input_file)
                output_file.write(input_file.read())
    logger.info(
        "Combined %s CSV files into %s",
        len(file_names),
        output_file_name,
    )


def delete_local_files(file_names: list[str]) -> None:
    """Deletes local files."""
    for file_name in file_names:
        try:
            os.remove(file_name)
            logger.debug("Deleted file %s", file_name)
        except FileNotFoundError:
            logger.warning("File not found, skipping deletion: %s", file_name)
        except OSError as e:
            logger.error("Error deleting file %s: %s", file_name, e)


def json_files_to_list(file_names: list[str]) -> list[dict]:
    """Reads JSON files and returns their contents as a list of dictionaries."""
    data = []
    for file_name in file_names:
        with open(file_name, "r", encoding="utf-8") as f:
            data.append(json.load(f))
        logger.debug("Loaded JSON from %s", file_name)
    logger.info("Loaded %s JSON files", len(file_names))
    return data


def convert_list_of_dicts_to_csv(data: list[dict], output_file_name: str) -> None:
    """Converts a list of dictionaries to a CSV file."""
    df = pd.DataFrame(data)
    df.to_csv(output_file_name, index=False)
    logger.info(
        "Converted %s JSON records to CSV file %s",
        len(data),
        output_file_name,
    )


def extract_historical_phase(s3_client: client, bucket_name: str) -> None:
    """Download, combine, and clean up historical CSV files."""
    download_data_from_s3_with_suffix(s3_client, bucket_name, suffix=".csv")

    historical_file_names = extract_s3_bucket_object_names(
        bucket_name, s3_client, prefix="lmnh", suffix=".csv")

    combine_csv_files(historical_file_names,
                      "historical_data.csv")

    delete_local_files(historical_file_names)


def extract_exhibition_phase(s3_client: client, bucket_name: str) -> None:
    """Download, convert, and clean up exhibition JSON files."""
    download_data_from_s3_with_suffix(s3_client, bucket_name, suffix=".json")

    exhibition_file_names = extract_s3_bucket_object_names(
        bucket_name, s3_client, prefix="lmnh", suffix=".json")

    data = json_files_to_list(exhibition_file_names)
    convert_list_of_dicts_to_csv(data, "exhibition_data.csv")

    delete_local_files(exhibition_file_names)


def download_and_format_data_from_s3_bucket(s3_client: client, bucket_name) -> None:
    """
    Extracts all relevant data from an S3 bucket and saves it to local files.
    Combines the historical data into a single CSV file and converts the exhibition data from JSON to CSV format.
    """
    extract_historical_phase(s3_client, bucket_name)
    extract_exhibition_phase(s3_client, bucket_name)


def clean_up_temp_extract_files() -> None:
    """Deletes local temporary files."""
    for file_name in ["exhibition_data.csv", "historical_data.csv"]:
        try:
            os.remove(file_name)
        except FileNotFoundError:
            pass
