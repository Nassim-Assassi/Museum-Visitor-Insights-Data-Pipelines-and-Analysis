from psycopg2 import connect

import pandas as pd

from dotenv import load_dotenv

from os import environ, _Environ

from sqlalchemy import create_engine


def get_db_engine(environ: _Environ):
    # Function to establish a connection to the PostgreSQL database using SQLAlchemy
    return create_engine(
        f"postgresql://{environ.get('DATABASE_USERNAME')}:{environ.get('DATABASE_PASSWORD')}@{environ.get('DATABASE_IP')}:{environ.get('DATABASE_PORT')}/{environ.get('DATABASE_NAME')}"
    )


def get_db_connection(environ: _Environ):
    # Function to establish a connection to the PostgreSQL database
    return connect(
        dbname=environ.get("DATABASE_NAME"),
        user=environ.get("DATABASE_USERNAME"),
        password=environ.get("DATABASE_PASSWORD"),
        host=environ.get("DATABASE_IP"),
        port=environ.get("DATABASE_PORT")
    )

# functions to import and clean data


def import_exhibition_csv():
    # Function to import the exhibition data from a CSV file into a pandas DataFrame
    return pd.read_csv("exhibition_data.csv")


def convert_exhibition_id_to_int(exhibition_data: pd.DataFrame) -> None:
    # Function to convert the exhibition IDs to integers
    # exhibition data is currently in the format EXH_01, EXH_02, etc.
    exhibition_data["EXHIBITION_ID"] = exhibition_data["EXHIBITION_ID"].str.slice(
        -2).astype(int)


def convert_floor_to_int(exhibition_data: pd.DataFrame) -> None:
    # Function to convert the floor value Vault to "-1"
    # and then convert the field to int
    exhibition_data["FLOOR"] = exhibition_data["FLOOR"].replace(
        "Vault", -1).astype(int)


def convert_start_date_to_date(exhibition_data: pd.DataFrame) -> None:
    # Function to convert the start date field to a date format
    # The start date is currently in the format "dd/mm/yy"
    exhibition_data["START_DATE"] = pd.to_datetime(
        exhibition_data["START_DATE"], format="%d/%m/%y").dt.date


def import_historical_csv():
    # Function to import the historical data from a CSV file into a pandas DataFrame
    return pd.read_csv("historical_data.csv")


# add functions to clean historical data if necessary


# functions to build and insert default tables


def drop_tables(conn) -> None:
    # Function to drop all tables in the database
    query = """DROP TABLE IF EXISTS kiosk_output, exhibit, button, department, floor, button_type CASCADE;"""
    with conn.cursor() as cur:
        cur.execute(query)
    conn.commit()


def create_tables(conn) -> None:
    # Function to create the tables in the database using the schema.sql file
    with conn.cursor() as cur:
        with open("schema.sql", "r") as f:
            cur.execute(f.read())
    conn.commit()


def build_floor_table(exhibition_data: pd.DataFrame) -> pd.DataFrame:
    # Function to extract the floor numbers and names from the exhibition data
    # name is vault if number is -1, otherwise it is the integer value,

    floor_data = exhibition_data[["FLOOR"]
                                 ].drop_duplicates().reset_index(drop=True)
    floor_data["FLOOR_NAME"] = floor_data["FLOOR"].apply(
        lambda x: "Vault" if x == -1 else str(x))
    return floor_data


def insert_floor_data(conn, floor_data: pd.DataFrame) -> None:
    # Function to insert the floor data into the floor table in the database
    with conn.cursor() as cur:
        for _, row in floor_data.iterrows():
            cur.execute(
                "INSERT INTO floor (number, name) VALUES (%s, %s)",
                (row["FLOOR"], row["FLOOR_NAME"])
            )
    conn.commit()


def build_and_insert_floor_table(conn, exhibition_data: pd.DataFrame) -> None:
    # Function to build the floor table and insert the data into the database
    floor_data = build_floor_table(exhibition_data)
    insert_floor_data(conn, floor_data)


def build_department_table(exhibition_data: pd.DataFrame) -> pd.DataFrame:
    # Function to extract the department names from the exhibition data
    department_data = exhibition_data[[
        "DEPARTMENT"]].drop_duplicates().reset_index(drop=True)
    return department_data


if __name__ == "__main__":

    load_dotenv()
    engine = get_db_engine(environ)
    conn = get_db_connection(environ)

    drop_tables(conn)
    create_tables(conn)

    exhibition_data = import_exhibition_csv()
    convert_exhibition_id_to_int(exhibition_data)
    convert_floor_to_int(exhibition_data)
    convert_start_date_to_date(exhibition_data)

    floor_numbers = build_floor_table(exhibition_data)
    insert_floor_data(conn, floor_numbers)

    department_data = build_department_table(exhibition_data)
    print(department_data)
    # insert_department_data(conn, department_data)
    conn.close()
