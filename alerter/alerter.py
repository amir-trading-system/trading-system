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
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
        emoji: str,
        milestones: common.objects.Milestones,
        is_retro: bool,
        sorted_indicators: dict[str, float] = {},
        base_except_one: bool = None,
    ):
        for handler in handlers.__handlers__:
            handler_object: handlers._alert_handler.Handler = handler(
                configuration=self.configuration,
                logger=self.logger,
            )
            designed_message = handler_object.design_indicated_bar_message(
                stock=stock,
                current_bar=current_bar,
                emoji=emoji,
                base_except_one=base_except_one,
                milestones=milestones,
                sorted_indicators=sorted_indicators,
            )

            threading.Thread(
                target=handler_object.alert,
                kwargs={
                    "sender": sender,
                    "symbol": current_bar.symbol,
                    "timeframe": current_bar.timeframe,
                    "bar_date": current_bar.bar_time,
                    "bar_index": current_bar.index,
                    "message": designed_message,
                    "is_retro": is_retro,
                },
            ).start()

    def send_confirmation_alert(
        self,
        sender: str,
        original_bar: common.objects.BarData,
        entry_position_bar: common.objects.BarData,
        evidence_name: str,
        is_retro: bool,
    ):
        for handler in handlers.__handlers__:
            handler_object: handlers._alert_handler.Handler = handler(
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
                },
            ).start()
