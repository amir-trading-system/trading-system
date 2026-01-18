import datetime
import logging
import requests


class Alerter:
    def __init__(
        self,
        logger: logging.Logger,
        bot_token: str,
        chat_id: str,
    ):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        self.logger = logger

    def _send_message(
        self,
        message: str,
    ):
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(
            url=self.url,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()

    def alert(
        self,
        sender: str,
        symbol: str,
        timeframe: int,
        bar_date: datetime.datetime,
        bar_index: int,
        message: str,
    ):
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

    def alert_on_error(
        self,
        message: str,
    ):
        error_message = f"<b>Error: {message}</b>"
        self._send_message(
            message=error_message,
        )
        self.logger.info(
            msg="Error has occurred - sending message by bot",
            extra={
                "error_message": error_message,
            },
        )
