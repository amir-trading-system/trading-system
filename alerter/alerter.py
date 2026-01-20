import datetime
import logging
import threading

import config_manager

from . import telegram
from . import whatsapp
from . import _alerter

class Alerter:
    def __init__(
        self,
        logger: logging.Logger,
        configuration: config_manager.Alerts,
    ):
        self.alerters: list[_alerter.BaseAlerter] = [
            telegram.Telegram(
                configuration=configuration.telegram,
                logger=logger,
            ),
            whatsapp.Whatsapp(
                configuration=configuration.whatsapp,
                logger=logger,
            ),
        ]

    def send_alert(
        self,
        sender: str,
        symbol: str,
        timeframe: int,
        bar_date: datetime.datetime,
        bar_index: int,
        message: str,
    ):
        for alerter in self.alerters:
            threading.Thread(
                target=alerter.alert,
                kwargs={
                    "sender": sender,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "bar_date": bar_date,
                    "bar_index": bar_index,
                    "message": message,
                },
            ).start()
