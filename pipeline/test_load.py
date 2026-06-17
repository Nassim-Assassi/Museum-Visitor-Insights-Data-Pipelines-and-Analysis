import pandas as pd
import pytest
from unittest.mock import Mock, call

import load
from conftest import DummyConn


class TestLoadCleanCsvFunctions:
    def test_use_expected_paths(self, monkeypatch):
        # Arrange
        read_csv = Mock(
            side_effect=[load.CLEAN_EXHIBITION_FILE,
                         load.CLEAN_HISTORICAL_FILE]
        )
        monkeypatch.setattr(load.pd, "read_csv", read_csv)

        # Act
        exhibition_path = load.load_clean_exhibition_csv()
        historical_path = load.load_clean_historical_csv()

        # Assert
        assert exhibition_path == load.CLEAN_EXHIBITION_FILE
        assert historical_path == load.CLEAN_HISTORICAL_FILE


class TestGetDbEngine:
    def test_builds_connection_string(self, monkeypatch):
        # Arrange
        create_engine = Mock(return_value="engine")
        monkeypatch.setattr(load, "create_engine", create_engine)
        config = {
            "DATABASE_USER": "u",
            "DATABASE_PASSWORD": "p",
            "DATABASE_HOST": "h",
            "DATABASE_PORT": "5432",
            "DATABASE_DB": "db",
        }

        # Act
        result = load.get_db_engine(config)

        # Assert
        assert result == "engine"
        assert create_engine.call_args.args[0] == "postgresql://u:p@h:5432/db"


class TestGetDbConnection:
    def test_passes_expected_kwargs(self, monkeypatch):
        # Arrange
        connect = Mock(return_value="conn")
        monkeypatch.setattr(load, "connect", connect)
        config = {
            "DATABASE_USER": "u",
            "DATABASE_PASSWORD": "p",
            "DATABASE_HOST": "h",
            "DATABASE_PORT": "5432",
            "DATABASE_DB": "db",
        }

        # Act
        result = load.get_db_connection(config)

        # Assert
        assert result == "conn"
        assert connect.call_args.kwargs["host"] == "h"
        assert connect.call_args.kwargs["sslmode"] == "require"


class TestGetIdDictHelpers:
    def test_get_department_id_dict_maps_rows(self):
        # Arrange
        department_conn = DummyConn(rows=[(1, "Art")])

        # Act
        department_ids = load.get_department_id_dict(department_conn)

        # Assert
        assert department_ids == {"Art": 1}

    def test_get_floor_id_dict_maps_rows(self):
        # Arrange
        floor_conn = DummyConn(rows=[(2, "Vault")])

        # Act
        floor_ids = load.get_floor_id_dict(floor_conn)

        # Assert
        assert floor_ids == {"Vault": 2}

    def test_get_button_type_id_dict_maps_rows(self):
        # Arrange
        button_type_conn = DummyConn(rows=[(3, "rating")])

        # Act
        button_type_ids = load.get_button_type_id_dict(button_type_conn)

        # Assert
        assert button_type_ids == {"rating": 3}

    def test_get_description_button_id_dict_maps_rows(self):
        # Arrange
        description_conn = DummyConn(rows=[("help", 4)])

        # Act
        description_ids = load.get_description_button_id_dict(description_conn)

        # Assert
        assert description_ids == {"help": 4}

    def test_get_value_button_id_dict_filters_none_values(self):
        # Arrange
        value_conn = DummyConn(rows=[(0, 10), (None, 11)])

        # Act
        value_ids = load.get_value_button_id_dict(value_conn)

        # Assert
        assert value_ids == {0: 10}


class TestBuildFloorTable:
    def test_handles_vault_and_numeric(self):
        # Arrange
        exhibition = pd.DataFrame({"FLOOR": ["1", "Vault", "1"]})

        # Act
        result = load.build_floor_table(exhibition)

        # Assert
        assert sorted(result["name"].tolist()) == ["1", "Vault"]
        assert set(result["number"].tolist()) == {1, -1}


class TestBuildDepartmentTable:
    def test_deduplicates(self):
        # Arrange
        exhibition = pd.DataFrame({"DEPARTMENT": ["A", "A", "B"]})

        # Act
        result = load.build_department_table(exhibition)

        # Assert
        assert set(result["name"].tolist()) == {"A", "B"}


class TestBuildButtonTypeTable:
    def test_defaults(self):
        # Act
        result = load.build_button_type_table()

        # Assert
        assert result["name"].tolist() == ["rating", "other"]


class TestBuildExhibitTable:
    def test_maps_foreign_keys(self):
        # Arrange
        exhibition = pd.DataFrame(
            {
                "EXHIBITION_ID": [1],
                "EXHIBITION_NAME": ["Show"],
                "DESCRIPTION": ["desc"],
                "START_DATE": ["2024-01-01"],
                "DEPARTMENT": ["Art"],
                "FLOOR": ["1"],
            }
        )

        # Act
        result = load.build_exhibit_table({"Art": 10}, {"1": 20}, exhibition)

        # Assert
        assert result.iloc[0]["department_id"] == 10
        assert result.iloc[0]["floor_id"] == 20


class TestMapRowToButtonId:
    def test_returns_rating_button_for_standard_value(self):
        # Arrange
        desc = {"assistance": 100, "emergency": 200}
        val = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}

        # Act
        button_id = load.map_row_to_button_id(
            {"val": 3, "type": None}, val, desc)

        # Assert
        assert button_id == 4

    def test_returns_assistance_button_for_type_zero(self):
        # Arrange
        desc = {"assistance": 100, "emergency": 200}
        val = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}

        # Act
        button_id = load.map_row_to_button_id(
            {"val": -1, "type": 0}, val, desc)

        # Assert
        assert button_id == 100

    def test_returns_emergency_button_for_type_one(self):
        # Arrange
        desc = {"assistance": 100, "emergency": 200}
        val = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}

        # Act
        button_id = load.map_row_to_button_id(
            {"val": -1, "type": 1}, val, desc)

        # Assert
        assert button_id == 200

    def test_returns_none_for_unknown_type(self):
        # Arrange
        desc = {"assistance": 100, "emergency": 200}
        val = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}

        # Act
        button_id = load.map_row_to_button_id(
            {"val": -1, "type": 99}, val, desc)

        # Assert
        assert button_id is None


class TestBuildKioskOutputTable:
    def test_drops_unmapped_rows(self):
        # Arrange
        historical = pd.DataFrame(
            {
                "at": ["2024-01-01T10:00:00", "2024-01-01T11:00:00"],
                "site": ["1", "1"],
                "val": [0, -1],
                "type": [None, 99],
            }
        )

        # Act
        result = load.build_kiosk_output_table(
            {"assistance": 10, "emergency": 11}, {0: 1}, historical)

        # Assert
        assert len(result) == 1
        assert result.iloc[0]["button_id"] == 1


class TestVerifyCleanFilesExist:
    def test_raises_when_missing(self, monkeypatch):
        # Arrange
        exists = Mock(return_value=False)
        monkeypatch.setattr(load.os.path, "exists", exists)

        # Act / Assert
        with pytest.raises(FileNotFoundError):
            load.verify_clean_files_exist()


class TestRunLoad:
    def test_calls_reset_then_build(self, monkeypatch):
        # Arrange
        tracker = Mock()
        reset_schema = Mock()
        build_tables = Mock()
        tracker.attach_mock(reset_schema, "reset")
        tracker.attach_mock(build_tables, "build")
        monkeypatch.setattr(load, "reset_schema", reset_schema)
        monkeypatch.setattr(load, "build_and_insert_tables", build_tables)

        conn = object()
        engine = object()

        # Act
        load.run_load(conn, engine, "schema.sql")

        # Assert
        assert tracker.mock_calls == [
            call.reset(conn, "schema.sql"),
            call.build(conn, engine),
        ]
