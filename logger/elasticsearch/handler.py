import datetime
import logging
import traceback

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
            "message": record.getMessage(),
            "level": record.levelname,
            "logger_name": record.name,
        }

        fields = [
            "worker",
            "symbol",
            "symbol_type",
            "indicator_name",
            "error_message",
            "order_action",
            "timeframe",
            "timeframe_type",
            "success_indicators",
            "success_indicators_count",
            "total_indicators",
            "failed_indicators",
            "current_index",
            "starting_index",
            "top_index",
            "lowest_low_index",
            "quantity",
            "evidence_name",
        ]

        for field in fields:
            if record_as_dict.get(field):
                document[field] = record_as_dict[field]

        if record_as_dict.get("exception"):
            exception: Exception = record_as_dict["exception"]
            document["message"] = str(exception),
            document["error"] = {
                "type": type(exception).__name__,
                "stack_trace": traceback.format_exc(),
            }

        date_fields = [
            "starting_index_time",
            "top_index_time",
            "lowest_low_time",
            "bar_time",
            "last_one_minute_bar_time",
            "entry_position_bar_time",
            "retroactive_from",
        ]

        for field in date_fields:
            datetime_value = record_as_dict.get(field)
            if datetime_value:
                document[field] = datetime_value + datetime.timedelta(
                    hours=5,
                )

        try:
            self.elastic_client.index(
                index=self.index,
                document=document,
            )
        except Exception as e:
            exception_message = f"An exception has been thrown from elasticsearch: {e}"
            print(exception_message)
