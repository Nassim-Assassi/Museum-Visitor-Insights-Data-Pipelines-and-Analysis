"""Load phase for the museum ETL pipeline."""

import logging
import os
import sys
from os import environ, _Environ

import pandas as pd
from psycopg2 import connect
from sqlalchemy import create_engine
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Temporary CSV files created by transform phase
CLEAN_EXHIBITION_FILE = "clean_exhibition.csv"
CLEAN_HISTORICAL_FILE = "clean_historical.csv"


def verify_clean_files_exist() -> None:
    """Verify that the clean CSV files exist."""
    if not os.path.exists(CLEAN_EXHIBITION_FILE):
        raise FileNotFoundError(
            f"Clean exhibition file not found: {CLEAN_EXHIBITION_FILE}")
    if not os.path.exists(CLEAN_HISTORICAL_FILE):
        raise FileNotFoundError(
            f"Clean historical file not found: {CLEAN_HISTORICAL_FILE}")


def load_clean_exhibition_csv() -> pd.DataFrame:
    """Load clean exhibition data from transform phase."""
    return pd.read_csv(CLEAN_EXHIBITION_FILE)


def load_clean_historical_csv() -> pd.DataFrame:
    """Load clean historical data from transform phase."""
    return pd.read_csv(CLEAN_HISTORICAL_FILE)


def get_db_engine(config: _Environ):
    """Establish a connection to the PostgreSQL database using SQLAlchemy."""
    return create_engine(
        f"postgresql://{config.get('DATABASE_USER')}:{config.get('DATABASE_PASSWORD')}@{config.get('DATABASE_HOST')}:{config.get('DATABASE_PORT')}/{config.get('DATABASE_DB')}"
    )


def get_db_connection(config: _Environ):
    """Establish a connection to the PostgreSQL database."""
    return connect(
        host=config.get("DATABASE_HOST"),
        port=config.get("DATABASE_PORT"),
        user=config.get("DATABASE_USER"),
        password=config.get("DATABASE_PASSWORD"),
        dbname=config.get("DATABASE_DB"),
        sslmode='require',
    )


def drop_schema_tables(conn) -> None:
    """Drop all tables in the database."""
    try:
        query = """DROP TABLE IF EXISTS kiosk_output, exhibit, button, department, floor, button_type CASCADE;"""
        with conn.cursor() as cur:
            cur.execute(query)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise


def create_schema_tables(conn, schema_path: str = "schema.sql") -> None:
    """Create the required tables in the database using the schema file."""
    try:
        with conn.cursor() as cur:
            with open(schema_path, "r") as f:
                cur.execute(f.read())
        conn.commit()
    except FileNotFoundError:
        raise
    except Exception as e:
        conn.rollback()
        raise


def get_department_id_dict(conn) -> dict:
    """
    Get department_id from database for each department name.
    department_id is generated as identity in postgresql.
    """
    query = """SELECT department_id, name FROM department;"""
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return {row[1]: row[0] for row in result}


def get_floor_id_dict(conn) -> dict:
    """
    Get floor_id from database for each floor name.
    floor_id is generated as identity in postgresql.
    """
    query = """SELECT floor_id, name FROM floor;"""
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return {row[1]: row[0] for row in result}


def get_button_type_id_dict(conn) -> dict:
    """
    Get button_type_id from database for each button type name.
    button_type_id is generated as identity in postgresql.
    """
    query = """SELECT button_type_id, name FROM button_type;"""
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return {row[1]: row[0] for row in result}


def get_description_button_id_dict(conn) -> dict:
    """
    Get button_id from database for each button description.
    button_id is generated as identity in postgresql.
    """
    query = """SELECT description, button_id FROM button;"""
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return {row[0]: row[1] for row in result}


def get_value_button_id_dict(conn) -> dict:
    """
    Get button_id from database for each button value.
    button_id is generated as identity in postgresql.
    """
    query = """SELECT value, button_id FROM button;"""
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return {row[0]: row[1] for row in result if row[0] is not None}


def build_floor_table(exhibition_data: pd.DataFrame) -> pd.DataFrame:
    """Extract the floor numbers and names from the exhibition data."""
    floor_data = pd.DataFrame()
    floor_data["name"] = exhibition_data[["FLOOR"]
                                         ].drop_duplicates().reset_index(drop=True)
    floor_data["number"] = floor_data["name"].apply(
        lambda x: -1 if x == "Vault" else int(x))
    return floor_data


def build_department_table(exhibition_data: pd.DataFrame) -> pd.DataFrame:
    """Extract the department names from the exhibition data."""
    department_data = pd.DataFrame()
    department_data["name"] = exhibition_data[["DEPARTMENT"]
                                              ].drop_duplicates().reset_index(drop=True)
    return department_data


def build_button_type_table() -> pd.DataFrame:
    """Build the button type table with the default button types."""
    button_type_data = pd.DataFrame({
        "name": ["rating", "other"]
    })
    return button_type_data


def build_exhibit_table(department_id_dict, floor_id_dict, exhibition_data: pd.DataFrame) -> pd.DataFrame:
    """
    Extract the exhibit names and their corresponding department and floor from the exhibition data.
    Links natural keys to surrogate IDs from database.
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


def build_button_table(button_type_id_dict) -> pd.DataFrame:
    """Build the button table with the default buttons and link to button types."""
    button_data = pd.DataFrame({
        "description": ["terrible", "bad", "neutral", "good", "amazing", "assistance", "emergency"],
        "value": [0, 1, 2, 3, 4, None, None]
    })
    button_data["button_type_id"] = button_data["value"].apply(
        lambda x: button_type_id_dict["rating"] if x in [0, 1, 2, 3, 4] else button_type_id_dict["other"])
    return button_data


def build_kiosk_output_table(description_button_id_dict: dict, value_button_id_dict: dict, historical_data: pd.DataFrame) -> pd.DataFrame:
    """
    Build the kiosk output table from historical interaction data.
    Links natural keys to surrogate IDs from database.
    """
    kiosk_output_data = pd.DataFrame()
    kiosk_output_data["recorded_at"] = pd.to_datetime(historical_data["at"])
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
            f"Dropped {dropped_count} kiosk output records with unmatched button types"
        )

    return kiosk_output_data


def ensure_clean_files_exist() -> None:
    """Ensure cleaned CSVs from transform phase exist before loading."""
    required_files = [
        CLEAN_EXHIBITION_FILE,
        CLEAN_HISTORICAL_FILE,
    ]
    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        raise FileNotFoundError(
            f"Missing cleaned data file(s): {', '.join(missing)}. "
            "Run --transform first or use --etl to run all phases."
        )


def build_and_insert_tables(conn, engine) -> None:
    """Build all tables from cleaned data and insert into database with ID linking."""
    ensure_clean_files_exist()

    # Load cleaned data from transform phase
    exhibition_data = load_clean_exhibition_csv()
    historical_data = load_clean_historical_csv()

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

    # Get button ID mappings
    description_button_id_dict = get_description_button_id_dict(conn)
    value_button_id_dict = get_value_button_id_dict(conn)

    # Build and insert kiosk output with FK linking
    kiosk_output_data = build_kiosk_output_table(description_button_id_dict,
                                                 value_button_id_dict, historical_data)
    kiosk_output_data.to_sql("kiosk_output", engine,
                             if_exists="append", index=False)
    logger.info(f"Inserted {len(kiosk_output_data)} kiosk output records")


def run_load(conn, engine, schema_path: str) -> None:
    """
    Orchestrate the load phase: drop, create schema, build and insert all tables with ID linking.
    Reads cleaned CSV files created by transform phase.

    Args:
        schema_path: Path to schema.sql file
        engine: SQLAlchemy engine
        conn: PostgreSQL connection
    """

    logger.info("Dropping existing tables if they exist...")
    drop_schema_tables(conn)
    logger.info("Existing tables dropped")

    logger.info("Creating schema tables...")
    create_schema_tables(conn, schema_path)
    logger.info("Schema tables created")

    logger.info(
        "Building tables from cleaned data and inserting into database...")
    build_and_insert_tables(conn, engine)
    logger.info("Data inserted into database")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger = logging.getLogger(__name__)
    load_dotenv()

    logger.info("Load module started")

    engine = None
    conn = None

    try:
        engine = get_db_engine(environ)
        conn = get_db_connection(environ)
        ensure_clean_files_exist()
        run_load(engine=engine, conn=conn, schema_path="schema.sql")
        logger.info("Load phase completed successfully")
    except Exception as e:
        logger.error(e)
        sys.exit(1)
    finally:
        try:
            if conn is not None:
                conn.close()
            if engine is not None:
                engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {str(e)}")
