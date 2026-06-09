from psycopg2 import connect

import pandas as pd

from dotenv import load_dotenv

from os import environ, _Environ

from sqlalchemy import create_engine


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


def import_exhibition_csv():
    """
    Import the exhibition data from a CSV file into a pandas DataFrame.
    """
    return pd.read_csv("exhibition_data.csv")


def convert_exhibition_id_to_int(exhibition_data: pd.DataFrame) -> None:
    """
    Convert the exhibition IDs to integers.
    Exhibition data is currently in the format EXH_01, EXH_02, etc.
    """
    exhibition_data["EXHIBITION_ID"] = exhibition_data["EXHIBITION_ID"].str.slice(
        -2).astype(int)


def convert_start_date_to_date(exhibition_data: pd.DataFrame) -> None:
    """
    Convert the start date field to a date format.
    The start date is currently in the format "dd/mm/yy".
    """
    exhibition_data["START_DATE"] = pd.to_datetime(
        exhibition_data["START_DATE"], format="%d/%m/%y").dt.date


def import_historical_csv():
    """
    Import the historical data from a CSV file into a pandas DataFrame.
    """
    return pd.read_csv("historical_data.csv")


# Functions to build tables and seed data into the database


def drop_tables(conn) -> None:
    """
    Drop all tables in the database.
    """
    query = """DROP TABLE IF EXISTS kiosk_output, exhibit, button, department, floor, button_type CASCADE;"""
    with conn.cursor() as cur:
        cur.execute(query)
    conn.commit()


def create_tables(conn) -> None:
    """
    Create the required tables in the database using the schema.sql file.
    """
    with conn.cursor() as cur:
        with open("schema.sql", "r") as f:
            cur.execute(f.read())
    conn.commit()


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
    return kiosk_output_data


def build_and_insert_tables(conn, engine, exhibition_data: pd.DataFrame, historical_data: pd.DataFrame) -> None:
    """
    Build all tables and insert the data into the database.
    """
    floor_data = build_floor_table(exhibition_data)
    floor_data.to_sql("floor", engine, if_exists="append", index=False)

    department_data = build_department_table(exhibition_data)
    department_data.to_sql("department", engine,
                           if_exists="append", index=False)

    department_id_dict = get_department_id_dict(conn)
    floor_id_dict = get_floor_id_dict(conn)

    exhibit_data = build_exhibit_table(
        department_id_dict, floor_id_dict, exhibition_data)
    exhibit_data.to_sql("exhibit", engine, if_exists="append", index=False)

    button_type_data = build_button_type_table()
    button_type_data.to_sql("button_type", engine,
                            if_exists="append", index=False)

    button_type_id_dict = get_button_type_id_dict(conn)

    button_data = build_button_table(button_type_id_dict)
    button_data.to_sql("button", engine, if_exists="append", index=False)

    description_button_id_dict = get_description_button_id_dict(conn)
    value_button_id_dict = get_value_button_id_dict(conn)

    kiosk_output_data = build_kiosk_output_table(description_button_id_dict,
                                                 value_button_id_dict, historical_data)
    kiosk_output_data.to_sql("kiosk_output", engine,
                             if_exists="append", index=False)


if __name__ == "__main__":

    load_dotenv()
    engine = get_db_engine(environ)
    conn = get_db_connection(environ)

    drop_tables(conn)
    create_tables(conn)

    exhibition_data = import_exhibition_csv()
    convert_exhibition_id_to_int(exhibition_data)
    convert_start_date_to_date(exhibition_data)

    historical_data = import_historical_csv()

    build_and_insert_tables(conn, engine, exhibition_data, historical_data)

    conn.close()
    engine.dispose()
