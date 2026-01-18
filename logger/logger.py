import logging

from . import elasticsearch


class Logger:
    def __init__(
        self,
        username: str,
        password: str,
        certs_file_path: str,
    ):
        name = "day_trading"
        elastic_handler = elasticsearch.handler.Handler(
            index=name,
            username=username,
            password=password,
            certs_file_path=certs_file_path,
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
