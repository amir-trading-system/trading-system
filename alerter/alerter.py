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
        evidence_name: str,
    ):
        telegram_object: handlers.telegram.Handler = handlers.telegram.Handler(
            configuration=self.configuration,
            logger=self.logger,
        )
        designed_message = telegram_object.design_indicated_bar_message(
            stock=stock,
            current_bar=current_bar,
            emoji=emoji,
            milestones=milestones,
            evidence_name=evidence_name,
        )

        threading.Thread(
            target=telegram_object.alert,
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
            },
        ).start()
