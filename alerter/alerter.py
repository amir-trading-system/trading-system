import logging
import threading

import config_manager
import common

from . import telegram


class Alerter:
    def __init__(
        self,
        logger: logging.Logger,
        configuration: config_manager.Alerts,
    ):
        self.logger = logger
        self.configuration = configuration

    def send_confirmation_alert(
        self,
        stock: common.objects.Stock,
        sender: str,
        original_bar: common.objects.BarData,
        entry_position_bar: common.objects.BarData,
        highest_high_one_minute_bar: common.objects.BarData,
        evidence_name: str,
        is_retro: bool,
        request_id: int,
    ):
        telegram_handler: telegram.Handler = telegram.Handler(
            configuration=self.configuration,
            logger=self.logger,
        )
        designed_message = telegram_handler.design_confirmation_bar_message(
            stock=stock,
            original_bar=original_bar,
            entry_position_bar=entry_position_bar,
            highest_high_one_minute_bar=highest_high_one_minute_bar,
            evidence_name=evidence_name,
        )

        threading.Thread(
            target=telegram_handler.alert,
            kwargs={
                "sender": sender,
                "symbol": original_bar.symbol,
                "timeframe": original_bar.timeframe,
                "bar_date": original_bar.bar_time,
                "bar_index": original_bar.index,
                "message": designed_message,
                "is_retro": is_retro,
                "request_id": request_id,
            },
        ).start()
