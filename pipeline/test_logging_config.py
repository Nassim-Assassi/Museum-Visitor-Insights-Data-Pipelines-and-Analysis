import logging
from unittest.mock import Mock

import logging_config


class TestGetLogger:
    def test_returns_named_logger(self):
        # Arrange
        logger_name = "pipeline.test"

        # Act
        logger = logging_config.get_logger(logger_name)

        # Assert
        assert logger.name == logger_name


class TestConfigureLogging:
    def test_default_level(self, monkeypatch):
        # Arrange
        basic_config = Mock()
        monkeypatch.setattr(logging, "basicConfig", basic_config)

        # Act
        logging_config.configure_logging()

        # Assert
        assert basic_config.call_args.kwargs["level"] == logging.INFO

    def test_verbose_level(self, monkeypatch):
        # Arrange
        basic_config = Mock()
        monkeypatch.setattr(logging, "basicConfig", basic_config)

        # Act
        logging_config.configure_logging(verbose=True)

        # Assert
        assert basic_config.call_args.kwargs["level"] == logging.DEBUG
