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

    def send_confirmation_alert(
        self,
        sender: str,
        original_bar: common.objects.BarData,
        entry_position_bar: common.objects.BarData,
        evidence_name: str,
        is_retro: bool,
        request_id: int,
    ):
        handler_object: handlers.telegram.Handler = handlers.telegram.Handler(
            configuration=self.configuration,
            logger=self.logger,
        )
        designed_message = handler_object.design_confirmation_bar_message(
            original_bar=original_bar,
            entry_position_bar=entry_position_bar,
            evidence_name=evidence_name,
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
                "is_retro": is_retro,
                "request_id": request_id,
            },
        ).start()
