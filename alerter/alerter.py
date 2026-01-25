import datetime
import logging
import threading

import config_manager
import common

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

    def send_confirmation_alert(
        self,
        sender: str,
        original_bar: common.objects.BarData,
        entry_position_bar: common.objects.BarData,
    ):
        for handler in handlers.__handlers__:
            handler_object: handlers._alert_handler.Handler = handler(
                configuration=self.configuration,
                logger=self.logger,
            )
            designed_message = handler_object.design_confirmation_bar_message(
                original_bar=original_bar,
                entry_position_bar=entry_position_bar,
            )

            threading.Thread(
                target=handler_object.alert,
                kwargs={
                    "sender": sender,
                    "symbol": original_bar.symbol,
                    "timeframe": original_bar.timeframe,
                    "bar_date": original_bar.bar_time,
                    "bar_index": original_bar.index,
                    "message": designed_message,
                },
            ).start()
