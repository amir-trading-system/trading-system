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
        record_as_dict = record.__dict__
        document = {
            "@timestamp": datetime.datetime.now(datetime.timezone.utc),
            "worker": record_as_dict.get("worker", ""),
            "message": record.getMessage(),
            "level": record.levelname,
            "function_name": record.funcName,
            "logger_name": record.name,
            "symbol": record_as_dict.get("symbol", ""),
            "symbol_type": record_as_dict.get("symbol_type", ""),
            "timeframe": record_as_dict.get("timeframe", 0),
            "success_indicators": record_as_dict.get("success_indicators", {}),
            "success_indicators_count": record_as_dict.get("success_indicators_count", 0),
            "total_indicators": record_as_dict.get("total_indicators", 0),
            "failed_indicators": record_as_dict.get("failed_indicators", {}),
            "current_index": record_as_dict.get("current_index", 0),
            "starting_index": record_as_dict.get("starting_index", 0),
            "top_index": record_as_dict.get("top_index", 0),
            "lowest_low_index": record_as_dict.get("lowest_low_index", 0),
            "indicator_name": record_as_dict.get("indicator_name", ""),
        }

        if record_as_dict.get("starting_index_time"):
            document["starting_index_time"] = record_as_dict.get("starting_index_time") + datetime.timedelta(
                hours=5,
            )
        if record_as_dict.get("top_index_time"):
            document["top_index_time"] = record_as_dict.get("top_index_time") + datetime.timedelta(
                hours=5,
            )
        if record_as_dict.get("lowest_low_time"):
            document["lowest_low_time"] = record_as_dict.get("lowest_low_time") + datetime.timedelta(
                hours=5,
            )
        if record_as_dict.get("bar_time"):
            document["bar_time"] = record_as_dict.get("bar_time") + datetime.timedelta(
                hours=5,
            )

        self.elastic_client.index(
            index=self.index,
            document=document,
        )
