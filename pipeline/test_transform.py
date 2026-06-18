import pandas as pd
import pytest
from unittest.mock import Mock

import transform


class TestLoadExhibitionCsv:
    def test_reads_expected_file(self, monkeypatch):
        # Arrange
        read_csv = Mock(return_value="exhibition_data.csv")
        monkeypatch.setattr(transform.pd, "read_csv", read_csv)

        # Act
        result = transform.load_exhibition_csv()

        # Assert
        assert result == "exhibition_data.csv"


class TestValidateRawExhibitionData:
    def test_missing_columns_raises(self):
        # Arrange
        df = pd.DataFrame({"EXHIBITION_ID": ["EXH_01"]})

        # Act / Assert
        with pytest.raises(ValueError):
            transform.validate_raw_exhibition_data(df)

    def test_drops_null_rows(self):
        # Arrange
        df = pd.DataFrame(
            {
                "EXHIBITION_ID": ["EXH_01", "EXH_02"],
                "EXHIBITION_NAME": ["A", None],
                "FLOOR": ["1", "2"],
                "DEPARTMENT": ["D", "D2"],
                "START_DATE": ["01/01/24", "01/01/24"],
                "DESCRIPTION": ["desc", "desc2"],
            }
        )

        # Act
        result = transform.validate_raw_exhibition_data(df)

        # Assert
        assert len(result) == 1
        assert result.iloc[0]["EXHIBITION_ID"] == "EXH_01"


class TestValidateRawHistoricalData:
    def test_filters_invalid_values(self):
        # Arrange
        df = pd.DataFrame(
            {
                "at": ["2024-01-01T10:00:00", "bad-time"],
                "site": ["1", "2"],
                "val": [2, 99],
                "type": [None, 0],
            }
        )

        # Act
        result = transform.validate_raw_historical_data(df)

        # Assert
        assert len(result) == 1
        assert result.iloc[0]["val"] == 2


class TestConvertExhibitionIdToInt:
    def test_converts_values(self):
        # Arrange
        df = pd.DataFrame({"EXHIBITION_ID": ["EXH_01", "EXH_10"]})

        # Act
        transform.convert_exhibition_id_to_int(df)

        # Assert
        assert df["EXHIBITION_ID"].tolist() == [1, 10]


class TestConvertStartDateToDate:
    def test_drops_invalid_dates(self):
        # Arrange
        df = pd.DataFrame({"START_DATE": ["01/01/24", "not-a-date"]})

        # Act
        transform.convert_start_date_to_date(df)

        # Assert
        assert len(df) == 1


class TestCleanExhibitionData:
    def test_calls_both_steps(self, monkeypatch):
        # Arrange
        convert_ids = Mock()
        convert_dates = Mock()
        monkeypatch.setattr(
            transform, "convert_exhibition_id_to_int", convert_ids)
        monkeypatch.setattr(
            transform, "convert_start_date_to_date", convert_dates)

        frame = pd.DataFrame()

        # Act
        transform.clean_exhibition_data(frame)

        # Assert
        convert_ids.assert_called_once_with(frame)
        convert_dates.assert_called_once_with(frame)


class TestEnsureExtractedFilesExist:
    def test_raises_for_missing(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(
            transform,
            "EXHIBITION_DATA_FILE",
            transform.EXHIBITION_DATA_FILE.parent / "_missing_exhibition.csv",
        )
        monkeypatch.setattr(
            transform,
            "HISTORICAL_DATA_FILE",
            transform.HISTORICAL_DATA_FILE.parent / "_missing_historical.csv",
        )

        # Act / Assert
        with pytest.raises(FileNotFoundError):
            transform.ensure_extracted_files_exist()


class TestRunTransform:
    def test_writes_outputs(self, monkeypatch):
        # Arrange
        exhibition = pd.DataFrame(
            {
                "EXHIBITION_ID": ["EXH_01"],
                "EXHIBITION_NAME": ["A"],
                "FLOOR": ["1"],
                "DEPARTMENT": ["D"],
                "START_DATE": ["01/01/24"],
                "DESCRIPTION": ["desc"],
            }
        )
        historical = pd.DataFrame(
            {"at": ["2024-01-01T10:00:00"], "site": ["1"], "val": [1], "type": [None]})

        monkeypatch.setattr(transform, "ensure_extracted_files_exist", Mock())
        monkeypatch.setattr(transform, "load_exhibition_csv",
                            Mock(return_value=exhibition))
        monkeypatch.setattr(transform, "load_historical_csv",
                            Mock(return_value=historical))
        monkeypatch.setattr(transform, "clean_exhibition_data", Mock())
        monkeypatch.setattr(
            transform, "validate_raw_exhibition_data", Mock(return_value=exhibition))
        monkeypatch.setattr(
            transform, "validate_raw_historical_data", Mock(return_value=historical))

        to_csv = Mock()
        monkeypatch.setattr(pd.DataFrame, "to_csv", to_csv, raising=False)

        # Act
        transform.run_transform()

        # Assert
        assert to_csv.call_count == 2
        assert to_csv.call_args_list[0].args[0] == transform.CLEAN_EXHIBITION_FILE
        assert to_csv.call_args_list[1].args[0] == transform.CLEAN_HISTORICAL_FILE


class TestCleanUpTempTransformFiles:
    def test_ignores_missing(self, tmp_path, monkeypatch):
        # Arrange
        clean_exhibition = tmp_path / "clean_exhibition.csv"
        clean_historical = tmp_path / "clean_historical.csv"
        monkeypatch.setattr(
            transform, "CLEAN_EXHIBITION_FILE", clean_exhibition)
        monkeypatch.setattr(
            transform, "CLEAN_HISTORICAL_FILE", clean_historical)

        # Act
        transform.clean_up_temp_transform_files()

        # Assert
        assert not clean_exhibition.exists()
        assert not clean_historical.exists()
