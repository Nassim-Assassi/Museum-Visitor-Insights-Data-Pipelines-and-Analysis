import os

from boto3 import client

from dotenv import load_dotenv

from os import environ, _Environ

# import pandas as pd


def get_s3_client(config: _Environ) -> client:
    """Returns an S3 client using the provided configuration."""
    load_dotenv()

    s3_client = client(
        "s3",
        aws_access_key_id=config.get("ACCESS_KEY"),
        aws_secret_access_key=config.get("SECRET_ACCESS_KEY")
    )

    return s3_client


def extract_s3_bucket_names(s3_client: client) -> dict:
    """Extracts the names of all S3 buckets and returns them as a dictionary."""
    response = s3_client.list_buckets()

    bucket_names = [bucket["Name"] for bucket in response["Buckets"]]

    return bucket_names


def extract_s3_bucket_object_names(bucket_name: str, s3_client: client, prefix: str = "", suffix: str = "") -> list[str]:
    """Extracts the names of all objects in an S3 bucket with a given prefix and suffix and returns them as a list."""
    response = s3_client.list_objects_v2(
        Bucket=bucket_name, Prefix=prefix)

    object_names = sorted([obj["Key"] for obj in response.get(
        "Contents") if obj["Key"].endswith(suffix)])

    return object_names


def extract_object_from_S3_bucket(bucket_name: str, file_name: str, s3_client: client, save_dir: str = ".") -> None:
    """Extracts an object from an S3 bucket and saves it to a local file."""
    s3_client.download_file(bucket_name, file_name, f"{save_dir}/{file_name}")


def extract_objects_from_S3_bucket(bucket_name: str, file_names: str, s3_client: client, save_dir: str = ".") -> None:
    """Extracts objects from an S3 bucket and saves them to local files."""
    for file_name in file_names:
        extract_object_from_S3_bucket(
            bucket_name, file_name, s3_client, save_dir)


def download_exhibition_data(s3_client: client) -> None:
    lmnh_exhibition_object_names = extract_s3_bucket_object_names(
        "sigma-resources-museum", s3_client, prefix="lmnh", suffix=".json")

    lmnh_object_names = lmnh_exhibition_object_names + lmnh_exhibition_object_names

    extract_objects_from_S3_bucket(
        "sigma-resources-museum", lmnh_object_names, s3_client)


def download_historical_data(s3_client: client) -> None:
    historical_exhibition_object_names = extract_s3_bucket_object_names(
        "sigma-resources-museum", s3_client,  prefix="lmnh", suffix=".csv")

    historical_object_names = historical_exhibition_object_names + \
        historical_exhibition_object_names

    extract_objects_from_S3_bucket(
        "sigma-resources-museum", historical_object_names, s3_client)


# def combine_csv_files_pandas(file_names: list, output_file_name: str) -> None:
#     """Combines multiple CSV files into a single CSV file."""

#     combined_df = pd.concat([pd.read_csv(file_name)
#                             for file_name in file_names])
#     combined_df.to_csv(output_file_name, index=False)


def combine_csv_files(file_names: list, output_file_name: str) -> None:
    """Combines multiple CSV files into a single CSV file."""
    with open(output_file_name, "w") as output_file:
        for i, file_name in enumerate(file_names):
            with open(file_name, "r") as input_file:
                if i != 0:
                    # Skip the header row for all but the first file
                    next(input_file)
                output_file.write(input_file.read())


def delete_local_files(file_names: list) -> None:
    """Deletes local files."""
    for file_name in file_names:
        os.remove(file_name)


if __name__ == "__main__":
    s3_client = get_s3_client(environ)

    download_exhibition_data(s3_client)
    download_historical_data(s3_client)

    historical_file_names = extract_s3_bucket_object_names(
        "sigma-resources-museum", s3_client, prefix="lmnh", suffix=".csv")

    combine_csv_files(historical_file_names,
                      "combined_historical_data.csv")

    delete_local_files(historical_file_names)
