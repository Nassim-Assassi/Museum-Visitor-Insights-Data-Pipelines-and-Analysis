"""Transform phase for the museum ETL pipeline."""

import os

import pandas as pd
from logging_config import get_logger

logger = get_logger(__name__)


def load_exhibition_csv():
    """Import the exhibition data from a CSV file into a pandas DataFrame."""
    return pd.read_csv("exhibition_data.csv")


def load_historical_csv():
    """Import the historical data from a CSV file into a pandas DataFrame."""
    return pd.read_csv("historical_data.csv")


def validate_raw_exhibition_data(exhibition_data: pd.DataFrame) -> pd.DataFrame:
    """
    Validate raw exhibition data by checking for required columns and dropping rows with nulls.

    Returns the cleaned DataFrame, or raises an exception if the result is empty.
    """
    required_columns = [
        "EXHIBITION_ID",
        "EXHIBITION_NAME",
        "FLOOR",
        "DEPARTMENT",
        "START_DATE",
        "DESCRIPTION",
    ]

    # Check for required columns
    missing_columns = [
        col for col in required_columns if col not in exhibition_data.columns]
    if missing_columns:
        raise ValueError(
            f"Exhibition data is missing required columns: {missing_columns}"
        )

    original_count = len(exhibition_data)

    # Drop rows with any null values in required columns
    exhibition_data = exhibition_data.dropna(subset=required_columns)

    dropped_count = original_count - len(exhibition_data)
    if dropped_count > 0:
        logger.warning(
            "Dropped %s exhibition rows with null values in required columns",
            dropped_count,
        )

    if len(exhibition_data) == 0:
        raise ValueError("Exhibition data is empty after validation")

    logger.info(
        "Exhibition data validated: %s valid records", len(exhibition_data))
    return exhibition_data


def validate_raw_historical_data(historical_data: pd.DataFrame) -> pd.DataFrame:
    """
    Validate raw historical data by checking for required columns, valid value ranges, and parseable timestamps.

    Returns the cleaned DataFrame, or raises an exception if the result is empty.
    """
    required_columns = ["at", "site", "val", "type"]

    non_null_constrained_columns = ["at", "site", "val"]

    # Check for required columns
    missing_columns = [
        col for col in required_columns if col not in historical_data.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Historical data is missing required columns: {missing_columns}"
        )

    original_count = len(historical_data)

    # Drop rows with any null values in required columns
    historical_data = historical_data.dropna(
        subset=non_null_constrained_columns)

    # Validate values in 'val' column are in {-1, 0, 1, 2, 3, 4}
    valid_vals = {-1, 0, 1, 2, 3, 4}
    invalid_val_mask = ~historical_data["val"].isin(valid_vals)
    invalid_val_count = invalid_val_mask.sum()
    if invalid_val_count > 0:
        logger.warning(
            "Dropping %s historical records with invalid 'val' outside %s",
            invalid_val_count,
            valid_vals,
        )
        historical_data = historical_data[~invalid_val_mask]

    # Validate values in 'at' column are parseable as timestamps
    invalid_at_mask = pd.to_datetime(
        historical_data["at"], errors="coerce"
    ).isna()
    invalid_at_count = invalid_at_mask.sum()
    if invalid_at_count > 0:
        logger.warning(
            "Dropping %s historical records with unparseable timestamps",
            invalid_at_count,
        )
        historical_data = historical_data[~invalid_at_mask]

    total_dropped = original_count - len(historical_data)
    if total_dropped > 0:
        logger.warning(
            "Dropped %s historical records during validation",
            total_dropped,
        )

    if len(historical_data) == 0:
        raise ValueError("Historical data is empty after validation")

    logger.info(
        "Historical data validated: %s valid records", len(historical_data))
    return historical_data


def convert_exhibition_id_to_int(exhibition_data: pd.DataFrame) -> None:
    """
    Convert the exhibition IDs to integers.
    Exhibition data is currently in the format EXH_01, EXH_02, etc.
    """
    try:
        exhibition_data["EXHIBITION_ID"] = exhibition_data["EXHIBITION_ID"].str.split(
            "_"
        ).str[-1].astype("Int64", errors="ignore")
        # Check for any NaN values that resulted from coercion
        nan_count = exhibition_data["EXHIBITION_ID"].isna().sum()
        if nan_count > 0:
            logger.warning(
                "%s invalid exhibition IDs present in data, dropping those rows",
                nan_count,
            )
            exhibition_data.dropna(subset=["EXHIBITION_ID"], inplace=True)
            logger.info(
                "Retained %s exhibition records after ID conversion",
                len(exhibition_data),
            )
    except Exception as e:
        logger.error("Error converting exhibition IDs: %s", e)
        raise


def convert_start_date_to_date(exhibition_data: pd.DataFrame) -> None:
    """
    Convert the start date field to a date format.
    The start date is currently in the format "dd/mm/yy".
    """
    try:
        original_count = len(exhibition_data)
        exhibition_data["START_DATE"] = pd.to_datetime(
            exhibition_data["START_DATE"], format="%d/%m/%y", errors="coerce"
        ).dt.date
        # Check for any NaT values that resulted from coercion
        nan_count = exhibition_data["START_DATE"].isna().sum()
        if nan_count > 0:
            logger.warning(
                "Failed to parse %s start dates, dropping those rows",
                nan_count,
            )
            exhibition_data.dropna(subset=["START_DATE"], inplace=True)
            logger.info(
                "Retained %s exhibition records after date conversion",
                len(exhibition_data),
            )
    except Exception as e:
        logger.error("Error converting start dates: %s", e)
        raise


def clean_exhibition_data(exhibition_data: pd.DataFrame) -> None:
    """
    Clean the exhibition data by converting the exhibition IDs to integers and converting the start date to a date format.
    """
    convert_exhibition_id_to_int(exhibition_data)
    convert_start_date_to_date(exhibition_data)


def ensure_extracted_files_exist() -> None:
    """Ensure extracted CSV files are available before running transform."""
    missing = []
    for file_name in ["exhibition_data.csv", "historical_data.csv"]:
        if not os.path.exists(file_name):
            missing.append(file_name)

    if missing:
        raise FileNotFoundError(
            "Missing extracted input file(s): "
            f"{', '.join(missing)}. "
            "Run extract first or place these files in the pipeline directory."
        )


def run_transform() -> None:
    """
    Load, clean, and validate extracted CSVs, then save cleaned data.

    Outputs:
        - clean_exhibition.csv: cleaned and validated exhibition data
        - clean_historical.csv: cleaned and validated historical data
    """
    logger.info("Transform module started")

    ensure_extracted_files_exist()

    exhibition_data = load_exhibition_csv()
    historical_data = load_historical_csv()

    clean_exhibition_data(exhibition_data)

    exhibition_data = validate_raw_exhibition_data(exhibition_data)
    historical_data = validate_raw_historical_data(historical_data)

    # Save cleaned data for load phase
    exhibition_data.to_csv("clean_exhibition.csv", index=False)
    logger.info("Saved clean_exhibition.csv")

    historical_data.to_csv("clean_historical.csv", index=False)
    logger.info("Saved clean_historical.csv")

    logger.info("Transform phase completed successfully")


def clean_up_temp_transform_files() -> None:
    """Delete temporary transform output files."""
    for file_name in ["clean_exhibition.csv", "clean_historical.csv"]:
        try:
            os.remove(file_name)
            logger.debug("Deleted temporary file %s", file_name)
        except FileNotFoundError:
            logger.debug(
                "Temporary file %s not found, skipping deletion", file_name)
        except Exception as e:
            logger.error("Error deleting temporary file %s: %s", file_name, e)
