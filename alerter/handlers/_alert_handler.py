import datetime
import logging

import config_manager
import common

class Handler:
    name = ""
    is_enabled = False

    def __init__(
        self,
        configuration: config_manager.Alerts,
        logger: logging.Logger,
    ):
        self.configuration = configuration
        self.logger = logger

    def _send_message(
        self,
        message: str,
    ):
        raise NotImplementedError()

    def design_confirmation_bar_message(
        self,
        original_bar: common.objects.BarData,
        entry_position_bar: common.objects.BarData,
    ) -> str:
        raise NotImplementedError()

    def design_indicated_bar_message(
        self,
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
        emoji: str,
        base_except_one: bool,
        milestones: common.objects.Milestones,
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
        if not self.is_enabled:
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
