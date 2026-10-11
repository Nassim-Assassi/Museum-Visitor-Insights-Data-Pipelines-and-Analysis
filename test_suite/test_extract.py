import json
from unittest.mock import Mock

import pandas as pd
import pytest

from data_seeding_pipeline import extract
from conftest import S3Downloader, S3ListEmpty, S3ListWithContents


class TestGetS3Client:
    def test_get_s3_client_passes_credentials(self, monkeypatch):
        # Arrange
        fake_client = Mock(return_value="s3-client")
        monkeypatch.setattr(extract, "client", fake_client)

        # Act
        result = extract.get_s3_client(
            {"ACCESS_KEY": "a", "SECRET_ACCESS_KEY": "b"})

        # Assert
        assert result == "s3-client"
        fake_client.assert_called_once_with(
            "s3", aws_access_key_id="a", aws_secret_access_key="b"
        )


class TestExtractS3BucketObjectNames:
    def test_filters_and_sorts(self):
        # Arrange
        s3_client = S3ListWithContents()

        # Act
        result = extract.extract_s3_bucket_object_names(
            "bucket", s3_client, prefix="lmnh", suffix=".csv"
        )

        # Assert
        assert result == ["lmnh/a.csv", "lmnh/c.csv"]

    def test_raises_when_no_contents(self):
        # Arrange
        s3_client = S3ListEmpty()

        # Act / Assert
        with pytest.raises(ValueError):
            extract.extract_s3_bucket_object_names(
                "bucket", s3_client, prefix="lmnh")


class TestExtractObjectFromS3Bucket:
    def test_downloads_file(self, tmp_path):
        # Arrange
        s3 = S3Downloader()

        # Act
        extract.extract_object_from_S3_bucket(
            "bucket", "file.csv", s3, save_dir=str(tmp_path))

        # Assert
        assert s3.calls == [("bucket", "file.csv", f"{tmp_path}/file.csv")]


class TestCombineCsvFiles:
    def test_combines_and_skips_headers(self, tmp_path):
        # Arrange
        f1 = tmp_path / "one.csv"
        f2 = tmp_path / "two.csv"
        out = tmp_path / "out.csv"
        f1.write_text("h1,h2\n1,2\n")
        f2.write_text("h1,h2\n3,4\n")

        # Act
        extract.combine_csv_files([str(f1), str(f2)], str(out))

        # Assert
        assert out.read_text() == "h1,h2\n1,2\n3,4\n"


class TestDeleteLocalFiles:
    def test_ignores_missing(self, tmp_path):
        # Arrange
        existing = tmp_path / "keep.csv"
        existing.write_text("x")

        # Act
        extract.delete_local_files(
            [str(existing), str(tmp_path / "missing.csv")])

        # Assert
        assert not existing.exists()


class TestJsonFilesToList:
    def test_reads_multiple_files(self, tmp_path):
        # Arrange
        f1 = tmp_path / "a.json"
        f2 = tmp_path / "b.json"
        f1.write_text(json.dumps({"x": 1}))
        f2.write_text(json.dumps({"y": 2}))

        # Act
        result = extract.json_files_to_list([str(f1), str(f2)])

        # Assert
        assert result == [{"x": 1}, {"y": 2}]


class TestConvertListOfDictsToCsv:
    def test_writes_file(self, tmp_path):
        # Arrange
        out = tmp_path / "data.csv"

        # Act
        extract.convert_list_of_dicts_to_csv([{"a": 1}, {"a": 2}], str(out))

        # Assert
        df = pd.read_csv(out)
        assert df["a"].tolist() == [1, 2]


class TestDownloadAndFormatDataFromS3Bucket:
    def test_calls_phases(self, monkeypatch):
        # Arrange
        s3_client = object()
        historical_phase = Mock()
        exhibition_phase = Mock()
        monkeypatch.setattr(
            extract, "extract_historical_phase", historical_phase)
        monkeypatch.setattr(
            extract, "extract_exhibition_phase", exhibition_phase)

        # Act
        extract.download_and_format_data_from_s3_bucket(s3_client, "bucket")

        # Assert
        historical_phase.assert_called_once_with(s3_client, "bucket")
        exhibition_phase.assert_called_once_with(s3_client, "bucket")


class TestCleanUpTempExtractFiles:
    def test_deletes_if_present(self, tmp_path, monkeypatch):
        # Arrange
        exhibition = tmp_path / "exhibition_data.csv"
        historical = tmp_path / "historical_data.csv"
        exhibition.write_text("x")
        historical.write_text("y")

        monkeypatch.setattr(extract, "EXHIBITION_DATA_FILE", exhibition)
        monkeypatch.setattr(extract, "HISTORICAL_DATA_FILE", historical)

        # Act
        extract.clean_up_temp_extract_files()

        # Assert
        assert not exhibition.exists()
        assert not historical.exists()
