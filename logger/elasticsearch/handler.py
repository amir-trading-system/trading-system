import datetime
import json
import logging
import traceback


class Handler(
    logging.Handler
):
    file_path: str = "logs/app.log"

    def __init__(
        self,
    ):
        super().__init__()
        self.lines_to_save: list[str] = []

    def emit(
        self,
        record,
    ):
        record_as_dict = record.__dict__

        should_write_log = record_as_dict.get("should_write_log", True)
        if not should_write_log:
            return

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
            "evidences",
            "low",
            "open",
            "close",
            "high",
            "body_percentage",
            "request_id",
            "starting_index_time",
            "top_index_time",
            "lowest_low_time",
            "bar_time",
            "last_one_minute_bar_time",
            "entry_position_bar_time",
            "score",
            "potential_score",
            "probability",
            "threshold",
            "should_run_model",
            "collection_finished_time",
            "reason",
            "highest_high",
            "highest_high_bar_time",
            "current_day_ema_9",
            "current_day_ema_20",
            "current_day_vwap",
            "positive_tier",
            "positive_group_score",
            "positive_group_reasons",
            "positive_score",
            "strong_positive_group_score",
            "strong_positive_group_reasons",
            "soft_positive_group_score",
            "soft_positive_group_reasons",
            "valid_reason",
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

        self.lines_to_save.append(json.dumps(document, default=str) + "\n")

        if len(self.lines_to_save) >= 50:
            try:
                #pylint:disable=unspecified-encoding
                with open(self.file_path, "a", buffering=1) as f:
                    f.writelines(self.lines_to_save)
                    self.lines_to_save = []
            except Exception as e:
                exception_message = f"An exception has been thrown while trying to write log into file: {e}"
                print(exception_message)

    def flush_logs(
        self,
    ):
        if self.lines_to_save:
            #pylint:disable=unspecified-encoding
            with open(self.file_path, "a", buffering=1) as f:
                f.writelines(self.lines_to_save)
                self.lines_to_save = []
