import datetime
import logging

import config_manager

class BaseAlerter:
    def __init__(
        self,
        configuration: config_manager.Whatsapp | config_manager.Telegram,
        logger: logging.Logger,
    ):
        self.configuration = configuration
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
                msg="Whatsapp alerter is not enabled by configuration",
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
            msg="Alert has been sent successfully",
            extra={
                "worker": sender,
                "symbol": symbol,
                "timeframe": timeframe,
                "bar_time": bar_date,
                "current_index": bar_index,
            },
        )
