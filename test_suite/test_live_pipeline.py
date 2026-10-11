import json
from unittest.mock import MagicMock, Mock

import pandas as pd
import pytest

from live_data_pipeline import live_pipeline
from conftest import FakeConsumerForConfig, FakeMessage, FakePollingConsumer


class TestDecodeMessage:
    def test_none_returns_none(self):
        # Arrange
        message = None

        # Act
        result = live_pipeline.decode_message(message)

        # Assert
        assert result is None

    def test_invalid_json_raises(self):
        # Arrange
        message = "not-json"

        # Act / Assert
        with pytest.raises(json.JSONDecodeError):
            live_pipeline.decode_message(message)


class TestValidateEventHelpers:
    def test_validate_event_structure_returns_true_for_required_fields(self):
        # Arrange
        event = {"at": "x", "site": "1", "val": 1}

        # Act
        result = live_pipeline.validate_event_structure(event)

        # Assert
        assert result is True

    def test_validate_event_structure_returns_false_when_field_missing(self):
        # Arrange
        event = {"at": "x", "site": "1"}

        # Act
        result = live_pipeline.validate_event_structure(event)

        # Assert
        assert result is False

    def test_validate_event_type_relationship_returns_true_for_valid_type(self):
        # Arrange
        event = {"val": -1, "type": 0}

        # Act
        result = live_pipeline.validate_event_type_relationship(event)

        # Assert
        assert result is True

    def test_validate_event_type_relationship_returns_false_without_type(self):
        # Arrange
        event = {"val": -1}

        # Act
        result = live_pipeline.validate_event_type_relationship(event)

        # Assert
        assert result is False

    def test_validate_event_at_ranges_returns_true_for_lower_bound(self):
        # Arrange
        event = {"at": "2024-01-01T08:45:00"}

        # Act
        result = live_pipeline.validate_event_at_ranges(event)

        # Assert
        assert result is True

    def test_validate_event_at_ranges_returns_true_for_upper_bound(self):
        # Arrange
        event = {"at": "2024-01-01T18:15:00"}

        # Act
        result = live_pipeline.validate_event_at_ranges(event)

        # Assert
        assert result is True

    def test_validate_event_at_ranges_returns_false_below_bound(self):
        # Arrange
        event = {"at": "2024-01-01T08:44:59"}

        # Act
        result = live_pipeline.validate_event_at_ranges(event)

        # Assert
        assert result is False


class TestValidateEvent:
    def test_valid_payload_returns_true(self):
        # Arrange
        event = {"at": "2024-01-01T10:00:00", "site": "1", "val": 2}

        # Act
        result = live_pipeline.validate_event(event, exhibit_ids={1, 2})

        # Assert
        assert result is True

    def test_invalid_payload_returns_false(self):
        # Arrange
        event = {"at": "2024-01-01T10:00:00", "site": "not-digit", "val": 2}

        # Act
        result = live_pipeline.validate_event(event, exhibit_ids={1, 2})

        # Assert
        assert result is False


class TestCreateKafkaConsumer:
    def test_requires_topic(self):
        # Arrange
        config = {"KAFKA_BOOTSTRAP_SERVERS": "server"}

        # Act / Assert
        with pytest.raises(ValueError):
            live_pipeline.create_kafka_consumer(config, "gid", "earliest")

    def test_subscribes(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(live_pipeline, "Consumer", FakeConsumerForConfig)

        config = {
            "KAFKA_BOOTSTRAP_SERVERS": "server",
            "KAFKA_TOPIC": "topic",
            "KAFKA_SECURITY_PROTOCOL": "p",
            "KAFKA_SASL_MECHANISM": "m",
            "KAFKA_SASL_USERNAME": "u",
            "KAFKA_SASL_PASSWORD": "pw",
        }

        # Act
        consumer = live_pipeline.create_kafka_consumer(
            config, "gid", "earliest")

        # Assert
        assert isinstance(consumer, FakeConsumerForConfig)
        assert consumer.topics == ["topic"]
        assert consumer.config["enable.auto.commit"] is False


class TestConsumeBatch:
    def test_raises_on_non_positive_batch_size(self):
        # Arrange
        batch_size = 0

        # Act / Assert
        with pytest.raises(ValueError):
            live_pipeline.consume_batch(object(), batch_size, {1})

    def test_skips_invalid_and_keeps_valid(self):
        # Arrange
        messages = [
            FakeMessage(b"not-json"),
            FakeMessage(None),
            FakeMessage(json.dumps(
                {"at": "2024-01-01T10:00:00", "site": "1", "val": 2}).encode()),
        ]

        consumer = FakePollingConsumer(messages)

        # Act
        df = live_pipeline.consume_batch(
            consumer, batch_size=1, exhibit_ids={1})

        # Assert
        assert len(df) == 1
        assert df.iloc[0]["site"] == "1"


class TestRunAndInsertBatch:
    def test_calls_to_sql(self, monkeypatch):
        # Arrange
        events = pd.DataFrame(
            {"at": ["2024-01-01T10:00:00"], "site": ["1"], "val": [2]})
        output = pd.DataFrame(
            {"recorded_at": ["2024-01-01T10:00:00"], "exhibit_id": ["1"], "button_id": [1]})

        consume_batch = Mock(return_value=events)
        build_table = Mock(return_value=output)
        to_sql = Mock()
        consumer = Mock()

        monkeypatch.setattr(live_pipeline, "consume_batch", consume_batch)
        monkeypatch.setattr(
            live_pipeline, "build_kiosk_output_table", build_table)
        monkeypatch.setattr(pd.DataFrame, "to_sql", to_sql, raising=False)

        # Act
        live_pipeline.run_and_insert_batch(
            consumer, 1, {1}, {"assistance": 1}, {0: 1}, object())

        # Assert
        assert to_sql.call_count == 1
        assert to_sql.call_args.args[0] == "kiosk_output"
        consumer.commit.assert_called_once_with(asynchronous=False)


class TestGroupIdPersistence:
    def test_load_saved_group_id_returns_existing_value(self, tmp_path, monkeypatch):
        # Arrange
        group_id_file = tmp_path / "group_id.txt"
        group_id_file.write_text("persisted-group", encoding="utf-8")
        monkeypatch.setattr(live_pipeline, "GROUP_ID_FILE", str(group_id_file))

        # Act
        result = live_pipeline.load_saved_group_id()

        # Assert
        assert result == "persisted-group"

    def test_load_saved_group_id_returns_none_when_missing(self, tmp_path, monkeypatch):
        # Arrange
        group_id_file = tmp_path / "group_id.txt"
        monkeypatch.setattr(live_pipeline, "GROUP_ID_FILE", str(group_id_file))

        # Act
        result = live_pipeline.load_saved_group_id()

        # Assert
        assert result is None

    def test_create_and_save_group_id_rotates_and_persists(self, tmp_path, monkeypatch):
        # Arrange
        group_id_file = tmp_path / "group_id.txt"
        group_id_file.write_text("old-group", encoding="utf-8")
        monkeypatch.setattr(live_pipeline, "GROUP_ID_FILE", str(group_id_file))

        # Act
        live_pipeline.create_and_save_group_id(prefix="museum-live-consumer")
        result = group_id_file.read_text(encoding="utf-8")

        # Assert
        assert result != "old-group"
        assert result


class TestResetKioskOutput:
    def test_reset_kiosk_output_runs_truncate_and_commit(self):
        # Arrange
        conn = MagicMock()
        cursor_context = conn.cursor.return_value
        cursor = cursor_context.__enter__.return_value

        # Act
        live_pipeline.reset_kiosk_output_table(conn)

        # Assert
        cursor.execute.assert_called_once_with("TRUNCATE TABLE kiosk_output")
        conn.commit.assert_called_once()
