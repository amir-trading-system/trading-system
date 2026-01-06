import datetime
import logging

from . import client


class Handler(
    logging.Handler
):
    def __init__(
        self,
        index: str,
    ):
        super().__init__()
        elastic_client_object = client.Client()
        self.index = index
        self.elastic_client = elastic_client_object.connect()

    def emit(
        self,
        record,
    ):
        document = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "@timestamp": datetime.datetime.now(datetime.timezone.utc),
        }

        for key, value in record.__dict__.items():
            if key not in logging.LogRecord.__dict__:
                document[key] = value

        self.elastic_client.index(
            index=self.index,
            document=record.__dict__,
        )
