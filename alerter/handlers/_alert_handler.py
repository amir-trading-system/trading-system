import datetime
import logging

import config_manager

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
