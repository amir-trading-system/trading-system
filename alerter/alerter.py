import datetime
import logging
import threading

import config_manager

from . import handlers

class Alerter:
    def __init__(
        self,
        logger: logging.Logger,
        configuration: config_manager.Alerts,
    ):
        self.logger = logger
        self.configuration = configuration

    def send_alert(
        self,
        sender: str,
        symbol: str,
        timeframe: int,
        bar_date: datetime.datetime,
        bar_index: int,
        message: str,
    ):
        for handler in handlers.__handlers__:
            handler_object: handlers._alert_handler.Handler = handler(
                configuration=self.configuration,
                logger=self.logger,
            )
            threading.Thread(
                target=handler_object.alert,
                kwargs={
                    "sender": sender,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "bar_date": bar_date,
                    "bar_index": bar_index,
                    "message": message,
                },
            ).start()
