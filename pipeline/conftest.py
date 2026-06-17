import sys
import types


def _noop():
    return None


def _boto3_client(*args, **kwargs):
    return object()


def _psycopg2_connect(**kwargs):
    return object()


def _sqlalchemy_engine(*args, **kwargs):
    return object()


def _ensure_module(name: str, attrs: dict) -> None:
    if name in sys.modules:
        return
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module


_ensure_module("dotenv", {"load_dotenv": _noop})
_ensure_module("confluent_kafka", {
               "Consumer": object, "KafkaError": Exception})
_ensure_module("boto3", {"client": _boto3_client})

if "botocore" not in sys.modules:
    sys.modules["botocore"] = types.ModuleType("botocore")
_ensure_module("botocore.exceptions", {"ClientError": Exception})
_ensure_module("psycopg2", {"connect": _psycopg2_connect})
_ensure_module("sqlalchemy", {"create_engine": _sqlalchemy_engine})


class S3ListWithContents:
    def list_objects_v2(self, Bucket, Prefix):
        return {
            "Contents": [
                {"Key": "lmnh/b.json"},
                {"Key": "lmnh/a.csv"},
                {"Key": "lmnh/c.csv"},
            ]
        }


class S3ListEmpty:
    def list_objects_v2(self, Bucket, Prefix):
        return {}


class S3Downloader:
    def __init__(self):
        self.calls = []

    def download_file(self, bucket, file_name, save_path):
        self.calls.append((bucket, file_name, save_path))


class DummyCursor:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.executed = []

    def execute(self, query):
        self.executed.append(query)

    def fetchall(self):
        return self.rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class DummyConn:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return DummyCursor(self.rows)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class FakeConsumerForConfig:
    def __init__(self, config):
        self.config = config
        self.topics = []

    def subscribe(self, topics):
        self.topics = topics


class FakeMessage:
    def __init__(self, value):
        self._value = value

    def value(self):
        return self._value

    def topic(self):
        return "lmnh"

    def partition(self):
        return 0

    def offset(self):
        return 1


class FakePollingConsumer:
    def __init__(self, messages):
        self.messages = messages

    def poll(self, _timeout):
        if self.messages:
            return self.messages.pop(0)
        return None
