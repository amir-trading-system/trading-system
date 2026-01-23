import datetime
import logging

import config_manager
from tws import objects as tws_objects
from analyzer import objects as analyzer_objects

class Handler:
    name = ""

    def __init__(
        self,
        configuration: config_manager.Alerts,
        logger: logging.Logger,
    ):
        match self.name:
            case "Telegram":
                self.configuration = configuration.telegram
            case "Whatsapp":
                self.configuration = configuration.whatsapp

        self.logger = logger

    def _send_message(
        self,
        message: str,
    ):
        raise NotImplementedError()

    def design_confirmation_bar_message(
        self,
        original_bar: tws_objects.BarData,
        entry_position_bar: tws_objects.BarData,
    ) -> str:
        raise NotImplementedError()

    def design_indicated_bar_message(
        self,
        stock: tws_objects.Stock,
        current_bar: tws_objects.BarData,
        emoji: str,
        base_except_one: bool,
        milestones: analyzer_objects.Milestones,
        sorted_indicators: dict[str,float],
    ) -> str:
        raise NotImplementedError()

    def alert(
        self,
        sender: str,
        symbol: str,
        timeframe: int,
        bar_date: datetime.datetime,
        bar_index: int,
        message: str,
    ):
        if not self.configuration.enabled:
            self.logger.warning(
                msg=f"{self.name} alerter is not enabled by configuration",
                extra={
                    "worker": sender,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "bar_time": bar_date,
                    "current_index": bar_index,
                },
            )
            return

        self._send_message(
            message=message,
        )
        self.logger.info(
            msg=f"Alert has been sent successfully to {self.name}",
            extra={
                "worker": sender,
                "symbol": symbol,
                "timeframe": timeframe,
                "bar_time": bar_date,
                "current_index": bar_index,
            },
        )
