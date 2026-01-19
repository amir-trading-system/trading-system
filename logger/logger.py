import logging

from . import elasticsearch


class Logger:
    def __init__(
        self,
    ):
        name = "day_trading"
        elastic_handler = elasticsearch.handler.Handler(
            index=name,
        )

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                elastic_handler,
            ],
        )
        self.logger = logging.getLogger(
            name=name,
        )

        for logger_name, logger_object in logging.root.manager.loggerDict.items():
            if not logger_name.startswith(name):
                logger_object.disabled = True

    def get_logger(
        self,
    ) -> logging.Logger:
        return self.logger
