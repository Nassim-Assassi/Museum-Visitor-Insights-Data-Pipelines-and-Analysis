import sys

import pipeline as pipeline_script


class TestParseArguments:
    def test_defaults(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(sys, "argv", ["pipeline.py"])

        # Act
        args = pipeline_script.parse_arguments()

        # Assert
        assert args.bucket == "sigma-resources-museum"
        assert args.schema == "schema.sql"
        assert args.etl is False
        assert args.extract is False
        assert args.transform is False
        assert args.load is False

    def test_flags(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(
            sys, "argv", ["pipeline.py", "--etl", "--verbose", "--bucket", "demo-bucket"])

        # Act
        args = pipeline_script.parse_arguments()

        # Assert
        assert args.etl is True
        assert args.verbose is True
        assert args.bucket == "demo-bucket"
