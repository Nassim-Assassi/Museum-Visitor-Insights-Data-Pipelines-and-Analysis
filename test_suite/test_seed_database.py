from unittest.mock import Mock

import pandas as pd
import pytest
from data_seeding_pipeline.temp_paths import TEMP_DIR

from data_seeding_pipeline import seed_database


class TestDownloadAndFormatExhibitionDataFromS3Bucket:
    def test_orchestrates(self, monkeypatch):
        # Arrange
        download = Mock()
        list_objects = Mock(return_value=["a.json"])
        read_json = Mock(return_value=[{"x": 1}])
        to_csv = Mock()
        cleanup = Mock()

        monkeypatch.setattr(seed_database.extract_phase,
                            "download_data_from_s3_with_suffix", download)
        monkeypatch.setattr(seed_database.extract_phase,
                            "extract_s3_bucket_object_names", list_objects)
        monkeypatch.setattr(seed_database.extract_phase,
                            "json_files_to_list", read_json)
        monkeypatch.setattr(seed_database.extract_phase,
                            "convert_list_of_dicts_to_csv", to_csv)
        monkeypatch.setattr(seed_database.extract_phase,
                            "delete_local_files", cleanup)

        # Act
        seed_database.download_and_format_exhibition_data_from_s3_bucket(
            object(), "bucket")

        # Assert
        assert download.call_count == 1
        assert read_json.call_args.args[0] == [
            str(TEMP_DIR / "a.json")
        ]
        assert to_csv.call_count == 1
        assert cleanup.call_args.args[0] == [
            str(TEMP_DIR / "a.json")
        ]
        assert cleanup.call_count == 1


class TestCleanupTempFiles:
    def test_cleanup_extract_temp_file_removes_file(self, tmp_path, monkeypatch):
        # Arrange
        f = tmp_path / "exhibition_data.csv"
        f.write_text("x")
        monkeypatch.setattr(seed_database, "EXHIBITION_DATA_FILE", f)

        # Act
        seed_database.clean_up_temp_extract_exhibition_data()

        # Assert
        assert not f.exists()

    def test_cleanup_transform_temp_file_removes_file(self, tmp_path, monkeypatch):
        # Arrange
        f = tmp_path / "clean_exhibition.csv"
        f.write_text("x")
        monkeypatch.setattr(seed_database, "CLEAN_EXHIBITION_FILE", f)

        # Act
        seed_database.clean_up_temp_transform_clean_exhibition_data()

        # Assert
        assert not f.exists()


class TestGenerateSeedData:
    def test_writes_clean_csv(self, monkeypatch):
        # Arrange
        df = pd.DataFrame({"a": [1]})
        monkeypatch.setattr(seed_database.transform_phase,
                            "load_exhibition_csv", Mock(return_value=df))
        monkeypatch.setattr(seed_database.transform_phase,
                            "clean_exhibition_data", Mock())
        monkeypatch.setattr(seed_database.transform_phase,
                            "validate_raw_exhibition_data", Mock(return_value=df))

        to_csv = Mock()
        monkeypatch.setattr(pd.DataFrame, "to_csv", to_csv, raising=False)

    # Act
        seed_database.generate_seed_data()

    # Assert
        assert to_csv.call_count == 1
        assert to_csv.call_args.args[0] == seed_database.CLEAN_EXHIBITION_FILE


class TestBuildAndInsertSeedTables:
    def test_calls_all_builders(self, monkeypatch):
        # Arrange
        exhibition = pd.DataFrame({"EXHIBITION_ID": [1], "EXHIBITION_NAME": ["x"], "DESCRIPTION": [
                                  "d"], "START_DATE": ["2024-01-01"], "DEPARTMENT": ["A"], "FLOOR": ["1"]})
        monkeypatch.setattr(seed_database.load_phase,
                            "load_clean_exhibition_csv", Mock(return_value=exhibition))
        monkeypatch.setattr(seed_database.load_phase, "build_floor_table", Mock(
            return_value=pd.DataFrame({"name": ["1"], "number": [1]})))
        monkeypatch.setattr(seed_database.load_phase, "build_department_table", Mock(
            return_value=pd.DataFrame({"name": ["A"]})))
        monkeypatch.setattr(seed_database.load_phase,
                            "get_department_id_dict", Mock(return_value={"A": 1}))
        monkeypatch.setattr(seed_database.load_phase,
                            "get_floor_id_dict", Mock(return_value={"1": 1}))
        monkeypatch.setattr(seed_database.load_phase, "build_exhibit_table", Mock(
            return_value=pd.DataFrame({"exhibit_id": [1]})))
        monkeypatch.setattr(seed_database.load_phase, "build_button_type_table", Mock(
            return_value=pd.DataFrame({"name": ["rating", "other"]})))
        monkeypatch.setattr(seed_database.load_phase, "get_button_type_id_dict", Mock(
            return_value={"rating": 1, "other": 2}))
        monkeypatch.setattr(seed_database.load_phase, "build_button_table", Mock(
            return_value=pd.DataFrame({"description": ["good"], "value": [3], "button_type_id": [1]})))

        to_sql = Mock()
        monkeypatch.setattr(pd.DataFrame, "to_sql", to_sql, raising=False)

        # Act
        seed_database.build_and_insert_seed_tables(object(), object())

        # Assert
        assert [c.args[0] for c in to_sql.call_args_list] == [
            "floor",
            "department",
            "exhibit",
            "button_type",
            "button",
        ]
