import logging


class Handler(
    logging.StreamHandler,
):
    def emit(
        self,
        record: logging.LogRecord,
    ) -> None:
        record_as_dict = record.__dict__
        final_message = ""
        symbol = record_as_dict.get("symbol")
        if symbol:
            final_message += f"Symbol: {symbol}. "

        worker = record_as_dict.get("worker")
        if worker:
            final_message += f"Worker: {worker}. "

        bar_time = record_as_dict.get("bar_time")
        if bar_time:
            final_message += f"Bar Time: {bar_time}. "

        entry_position_bar_time = record_as_dict.get("entry_position_bar_time")
        if entry_position_bar_time:
            final_message += f"Entry position bar time: {entry_position_bar_time}. "

        record.msg = f"{final_message}{record.getMessage()}"

        return super().emit(record)
