-- This file should contain all code required to create & seed postgres database tables.

CREATE TABLE floor(
    floor_id SMALLINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    number SMALLINT NOT NULL UNIQUE,
    name TEXT NULL UNIQUE,
    PRIMARY KEY(floor_id)
    
);

CREATE TABLE department(
    department_id SMALLINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    name TEXT NOT NULL UNIQUE,
    PRIMARY KEY(department_id)
);

CREATE TABLE button_type(
    button_type_id SMALLINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    name TEXT NOT NULL UNIQUE,
    PRIMARY KEY(button_type_id),
    CONSTRAINT button_type_valid CHECK (name IN ('rating', 'other'))
);

CREATE TABLE button(
    button_id SMALLINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    button_type_id SMALLINT NOT NULL,
    description TEXT NOT NULL UNIQUE,
    value SMALLINT,
    PRIMARY KEY(button_id),
    FOREIGN KEY(button_type_id) REFERENCES button_type(button_type_id) ON DELETE RESTRICT,
    CONSTRAINT value_valid CHECK (value IN (0, 1, 2, 3, 4) OR value IS NULL)
);

CREATE TABLE exhibit(
    exhibit_id INTEGER NOT NULL,
    name TEXT NOT NULL UNIQUE,
    floor_id SMALLINT NOT NULL,
    department_id SMALLINT NOT NULL,
    start_date DATE NOT NULL,
    description TEXT NOT NULL UNIQUE,
    PRIMARY KEY(exhibit_id),
    FOREIGN KEY(floor_id) REFERENCES floor(floor_id) ON DELETE RESTRICT,
    FOREIGN KEY(department_id) REFERENCES department(department_id) ON DELETE RESTRICT
);

CREATE TABLE kiosk_output(
    kiosk_output_id INTEGER GENERATED ALWAYS AS IDENTITY NOT NULL,
    recorded_at TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    exhibit_id INTEGER NOT NULL,
    button_id SMALLINT NOT NULL,
    PRIMARY KEY(kiosk_output_id),
    FOREIGN KEY(exhibit_id) REFERENCES exhibit(exhibit_id) ON DELETE RESTRICT,
    FOREIGN KEY(button_id) REFERENCES button(button_id) ON DELETE RESTRICT
);

CREATE INDEX ON kiosk_output(recorded_at);
CREATE INDEX ON kiosk_output(exhibit_id);
CREATE INDEX ON kiosk_output(button_id);