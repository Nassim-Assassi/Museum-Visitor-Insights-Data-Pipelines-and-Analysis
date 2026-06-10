import logging
from psycopg2 import connect

import pandas as pd

from dotenv import load_dotenv

from os import environ, _Environ

from sqlalchemy import create_engine

logger = logging.getLogger(__name__)


def get_db_engine(config: _Environ):
    """
    Establish a connection to the PostgreSQL database using SQLAlchemy.
    """
    return create_engine(
        f"postgresql://{config.get('DATABASE_USERNAME')}:{config.get('DATABASE_PASSWORD')}@{config.get('DATABASE_IP')}:{config.get('DATABASE_PORT')}/{config.get('DATABASE_NAME')}"
    )


def get_db_connection(config: _Environ):
    """
    Establish a connection to the PostgreSQL database.
    """
    return connect(
        dbname=config.get("DATABASE_NAME"),
        user=config.get("DATABASE_USERNAME"),
        password=config.get("DATABASE_PASSWORD"),
        host=config.get("DATABASE_IP"),
        port=config.get("DATABASE_PORT")
    )

# Functions to import and clean data


def load_exhibition_csv():
    """
    Import the exhibition data from a CSV file into a pandas DataFrame.
    """
    return pd.read_csv("exhibition_data.csv")


def load_historical_csv():
    """
    Import the historical data from a CSV file into a pandas DataFrame.
    """
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
            f"Dropped {dropped_count} exhibition rows with null values in required columns"
        )

    if len(exhibition_data) == 0:
        raise ValueError("Exhibition data is empty after validation")

    logger.info("Exhibition data validated: %d valid records",
                len(exhibition_data))
    return exhibition_data


def validate_raw_historical_data(historical_data: pd.DataFrame) -> pd.DataFrame:
    """
    Validate raw historical data by checking for required columns, valid value ranges, and parseable timestamps.

    Returns the cleaned DataFrame, or raises an exception if the result is empty.
    """
    required_columns = ["at", "site", "val", "type"]

    non_null_required_columns = ["at", "site", "val"]

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
    historical_data = historical_data.dropna(subset=required_columns)

    # Validate 'val' is in {-1, 0, 1, 2, 3, 4}
    valid_vals = {-1, 0, 1, 2, 3, 4}
    invalid_val_mask = ~historical_data["val"].isin(valid_vals)
    invalid_val_count = invalid_val_mask.sum()
    if invalid_val_count > 0:
        logger.warning(
            "Dropping %d historical records with invalid 'val' outside {-1, 0, 1, 2, 3, 4}",
            invalid_val_count,
        )
        historical_data = historical_data[~invalid_val_mask]

    # # Validate 'at' is parseable as a timestamp

    invalid_at_mask = pd.to_datetime(
        historical_data["at"], errors="coerce"
    ).isna()
    invalid_at_count = invalid_at_mask.sum()
    if invalid_at_count > 0:
        logger.warning(
            "Dropping %d historical records with unparseable timestamps",
            invalid_at_count,
        )
        historical_data = historical_data[~invalid_at_mask]

    # total_dropped = original_count - len(historical_data)
    # if total_dropped > 0:
    #     logger.warning(
    #         "Dropped %d historical records during validation",
    #         total_dropped,
    #     )

    # if len(historical_data) == 0:
    #     raise ValueError("Historical data is empty after validation")

    # logger.info("Historical data validated: %d valid records",
    #             len(historical_data))
    return historical_data


def convert_exhibition_id_to_int(exhibition_data: pd.DataFrame) -> None:
    """
    Convert the exhibition IDs to integers.
    Exhibition data is currently in the format EXH_01, EXH_02, etc.
    """
    try:
        original_count = len(exhibition_data)
        exhibition_data["EXHIBITION_ID"] = exhibition_data["EXHIBITION_ID"].str.slice(
            -2
        ).astype("Int64", errors="ignore")
        # Check for any NaN values that resulted from coercion
        nan_count = exhibition_data["EXHIBITION_ID"].isna().sum()
        if nan_count > 0:
            logger.warning(
                f"{nan_count} invalid exhibition IDs present in data, dropping those rows"
            )
            exhibition_data.dropna(subset=["EXHIBITION_ID"], inplace=True)
            logger.info(
                f"Retained {len(exhibition_data)} exhibition records after ID conversion"
            )
    except Exception as e:
        logger.error(f"Error converting exhibition IDs: {str(e)}")
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
                f"Failed to parse {nan_count} start dates, dropping those rows"
            )
            exhibition_data.dropna(subset=["START_DATE"], inplace=True)
            logger.info(
                f"Retained {len(exhibition_data)} exhibition records after date conversion"
            )
    except Exception as e:
        logger.error(f"Error converting start dates: {str(e)}")
        raise


def clean_exhibition_data(exhibition_data: pd.DataFrame) -> None:
    """
    Clean the exhibition data by converting the exhibition IDs to integers and converting the start date to a date format.
    """

    convert_exhibition_id_to_int(exhibition_data)
    convert_start_date_to_date(exhibition_data)


# Functions to build tables and seed data into the database


def drop_schema_tables(conn) -> None:
    """
    Drop all tables in the database.
    """
    try:
        query = """DROP TABLE IF EXISTS kiosk_output, exhibit, button, department, floor, button_type CASCADE;"""
        with conn.cursor() as cur:
            cur.execute(query)
        conn.commit()
        logger.info("Dropped all schema tables")
    except Exception as e:
        logger.error("Error dropping tables: %s", str(e))
        conn.rollback()
        raise


def create_schema_tables(conn, schema_path: str = "schema.sql") -> None:
    """
    Create the required tables in the database using the schema file.
    """
    try:
        with conn.cursor() as cur:
            with open(schema_path, "r") as f:
                cur.execute(f.read())
        conn.commit()
        logger.info("Created schema tables from %s", schema_path)
    except FileNotFoundError:
        logger.error("Schema file not found: %s", schema_path)
        raise
    except Exception as e:
        logger.error("Error creating tables: %s", str(e))
        conn.rollback()
        raise


def build_floor_table(exhibition_data: pd.DataFrame) -> pd.DataFrame:
    """
    Extract the floor numbers and names from the exhibition data.
    """
    floor_data = pd.DataFrame()
    floor_data["name"] = exhibition_data[["FLOOR"]
                                         ].drop_duplicates().reset_index(drop=True)
    floor_data["number"] = floor_data["name"].apply(
        lambda x: -1 if x == "Vault" else int(x))
    return floor_data


def build_department_table(exhibition_data: pd.DataFrame) -> pd.DataFrame:
    """
    Extract the department names from the exhibition data.
    """
    department_data = pd.DataFrame()
    department_data["name"] = exhibition_data[["DEPARTMENT"]
                                              ].drop_duplicates().reset_index(drop=True)
    return department_data


def get_department_id_dict(conn) -> int:
    """
    department_id is generated as identity in postgresql
    we need to get the department_id from the database for each department name
    """
    query = """SELECT department_id, name FROM department;"""
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return {row[1]: row[0] for row in result}


def get_floor_id_dict(conn) -> int:
    """
    floor_id is generated as identity in postgresql
    we need to get the floor_id from the database for each floor name
    """
    query = """SELECT floor_id, name FROM floor;"""
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return {row[1]: row[0] for row in result}


def build_exhibit_table(department_id_dict, floor_id_dict, exhibition_data: pd.DataFrame) -> pd.DataFrame:
    """
    Extract the exhibit names and their corresponding department and floor from the exhibition data.
    """
    exhibit_data = pd.DataFrame()
    exhibit_data["exhibit_id"] = exhibition_data[["EXHIBITION_ID"]]
    exhibit_data["name"] = exhibition_data[["EXHIBITION_NAME"]]
    exhibit_data["description"] = exhibition_data[["DESCRIPTION"]]
    exhibit_data["start_date"] = exhibition_data[["START_DATE"]]
    exhibit_data["department_id"] = exhibition_data["DEPARTMENT"].apply(
        lambda x: department_id_dict[x])
    exhibit_data["floor_id"] = exhibition_data["FLOOR"].apply(
        lambda x: floor_id_dict[x])

    return exhibit_data


def build_button_type_table() -> pd.DataFrame:
    """
    Build the button type table with the default button types.
    """
    button_type_data = pd.DataFrame({
        "name": ["rating", "other"]
    })
    return button_type_data


def get_button_type_id_dict(conn) -> int:
    """
    button_type_id is generated as identity in postgresql
    we need to get the button_type_id from the database for each button type name
    """
    query = """SELECT button_type_id, name FROM button_type;"""
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return {row[1]: row[0] for row in result}


def build_button_table(button_type_id_dict) -> pd.DataFrame:
    """
    Build the button table with the default buttons.
    """
    button_data = pd.DataFrame({
        "description": ["terrible", "bad", "neutral", "good", "amazing", "assistance", "emergency"],
        "value": [0, 1, 2, 3, 4, None, None]
    })
    button_data["button_type_id"] = button_data["value"].apply(
        lambda x: button_type_id_dict["rating"] if x in [0, 1, 2, 3, 4] else button_type_id_dict["other"])
    return button_data


def get_description_button_id_dict(conn) -> int:
    """
    button_id is generated as identity in postgresql
    we need to get the button_id from the database for each button description
    """
    query = """SELECT description, button_id FROM button;"""
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return {row[0]: row[1] for row in result}


def get_value_button_id_dict(conn) -> int:
    """
    button_id is generated as identity in postgresql
    we need to get the button_id from the database for each button value
    """
    query = """SELECT value, button_id FROM button;"""
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return {row[0]: row[1] for row in result if row[0] is not None}


def build_kiosk_output_table(description_button_id_dict: dict, value_button_id_dict: dict, historical_data: pd.DataFrame) -> pd.DataFrame:
    """
    Build the kiosk output table from historical interaction data.
    """
    kiosk_output_data = pd.DataFrame()
    kiosk_output_data["recorded_at"] = pd.to_datetime(
        historical_data["at"])
    kiosk_output_data["exhibit_id"] = historical_data["site"]
    # if val is 0 to 4 then it is a rating button, if it is -1 then it is another type of button
    # for others if type is 0 then it is assistance button, if type is 1 then it is emergency button
    kiosk_output_data["button_id"] = historical_data.apply(lambda row: value_button_id_dict[row["val"]] if row["val"] in [
                                                           0, 1, 2, 3, 4] else description_button_id_dict["assistance"] if row["type"] == 0 else description_button_id_dict["emergency"] if row["type"] == 1 else None, axis=1)

    # Drop rows with None button_id and log a warning
    original_count = len(kiosk_output_data)
    kiosk_output_data = kiosk_output_data.dropna(subset=["button_id"])
    dropped_count = original_count - len(kiosk_output_data)
    if dropped_count > 0:
        logger.warning(
            "Dropped %d kiosk output records with unmatched button types",
            dropped_count,
        )

    return kiosk_output_data


def build_and_insert_tables(conn, engine, exhibition_data: pd.DataFrame, historical_data: pd.DataFrame) -> None:
    """
    Build all tables and insert the data into the database.
    """
    try:
        floor_data = build_floor_table(exhibition_data)
        floor_data.to_sql("floor", engine, if_exists="append", index=False)
        logger.info("Inserted %d floor records", len(floor_data))

        department_data = build_department_table(exhibition_data)
        department_data.to_sql("department", engine,
                               if_exists="append", index=False)
        logger.info("Inserted %d department records", len(department_data))

        department_id_dict = get_department_id_dict(conn)
        floor_id_dict = get_floor_id_dict(conn)

        exhibit_data = build_exhibit_table(
            department_id_dict, floor_id_dict, exhibition_data)
        exhibit_data.to_sql("exhibit", engine, if_exists="append", index=False)
        logger.info("Inserted %d exhibit records", len(exhibit_data))

        button_type_data = build_button_type_table()
        button_type_data.to_sql("button_type", engine,
                                if_exists="append", index=False)
        logger.info("Inserted %d button type records", len(button_type_data))

        button_type_id_dict = get_button_type_id_dict(conn)

        button_data = build_button_table(button_type_id_dict)
        button_data.to_sql("button", engine, if_exists="append", index=False)
        logger.info("Inserted %d button records", len(button_data))

        description_button_id_dict = get_description_button_id_dict(conn)
        value_button_id_dict = get_value_button_id_dict(conn)

        kiosk_output_data = build_kiosk_output_table(description_button_id_dict,
                                                     value_button_id_dict, historical_data)
        kiosk_output_data.to_sql("kiosk_output", engine,
                                 if_exists="append", index=False)
        logger.info("Inserted %d kiosk output records", len(kiosk_output_data))
    except Exception as e:
        raise


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger.info("Seed database module started")

    try:
        load_dotenv()

        logger.info("Loading exhibition data...")
        exhibition_data = load_exhibition_csv()

        logger.info("Loading historical data...")
        historical_data = load_historical_csv()

        logger.info("Validating exhibition data...")
        exhibition_data = validate_raw_exhibition_data(exhibition_data)

        logger.info("Validating historical data...")
        historical_data = validate_raw_historical_data(historical_data)

        # logger.info("Cleaning exhibition data...")
        # clean_exhibition_data(exhibition_data)

        # engine = get_db_engine(environ)
        # conn = get_db_connection(environ)
        # logger.info("Database connections established")

        # drop_schema_tables(conn)
        # create_schema_tables(conn)

        # build_and_insert_tables(conn, engine, exhibition_data, historical_data)
        # logger.info("Database seeding completed successfully")

        # conn.close()
        # engine.dispose()
        # logger.info("Database connections closed")
    except Exception as e:
        logger.error(str(e))
        logger.error("Database seeding failed")
        sys.exit(1)
