-- This file should contain all code required to create & seed postgres database tables.

CREATE TABLE floor(
    floor_id SMALLINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    number SMALLINT NOT NULL UNIQUE,
    name VARCHAR(255) NULL UNIQUE,
    PRIMARY KEY(floor_id)
);

CREATE TABLE department(
    department_id SMALLINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    name VARCHAR(255) NOT NULL UNIQUE,
    PRIMARY KEY(department_id)
);

CREATE TABLE button_type(
    button_type_id SMALLINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    name VARCHAR(255) NOT NULL UNIQUE,
    PRIMARY KEY(button_type_id)
);

CREATE TABLE button(
    button_id SMALLINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    button_type_id SMALLINT NOT NULL,
    description VARCHAR(255) NOT NULL UNIQUE,
    PRIMARY KEY(button_id),
    FOREIGN KEY(button_type_id) REFERENCES button_type(button_type_id)
);

CREATE TABLE exhibit(
    exhibit_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    name VARCHAR(255) NOT NULL UNIQUE,
    floor_id SMALLINT NOT NULL,
    department_id SMALLINT NOT NULL,
    start_date DATE NOT NULL,
    description VARCHAR(255) NOT NULL UNIQUE,
    PRIMARY KEY(exhibit_id),
    FOREIGN KEY(floor_id) REFERENCES floor(floor_id),
    FOREIGN KEY(department_id) REFERENCES department(department_id)
);

CREATE TABLE kiosk_output(
    kiosk_output_id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    recorded_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    exhibit_id BIGINT NOT NULL,
    button_id SMALLINT NOT NULL,
    PRIMARY KEY(kiosk_output_id),
    FOREIGN KEY(exhibit_id) REFERENCES exhibit(exhibit_id),
    FOREIGN KEY(button_id) REFERENCES button(button_id)
);

