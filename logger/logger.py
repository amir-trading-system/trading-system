import logging

from . import elasticsearch
from . import stdout_handler


class Logger:
    def __init__(
        self,
        enable_stdout: bool,
    ):
        name = "day_trading"
        elastic_handler = elasticsearch.handler.Handler(
            index=name,
        )

        handlers = [
            elastic_handler,
        ]
        if enable_stdout:
            handlers.append(stdout_handler.Handler())

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=handlers,
        )
        self.logger = logging.getLogger(
            name=name,
        )

        for logger_name, logger_object in logging.root.manager.loggerDict.items():
            if not logger_name.startswith(name):
                logger_object.disabled = True # type: ignore

    def get_logger(
        self,
    ) -> logging.Logger:
        return self.logger
