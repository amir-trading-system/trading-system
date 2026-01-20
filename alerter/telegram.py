import logging
import requests

import config_manager

from . import _alerter


class Telegram(
    _alerter.BaseAlerter,
):
    def __init__(
        self,
        configuration: config_manager.Telegram,
        logger: logging.Logger,
    ):
        super().__init__(
            configuration=configuration,
            logger=logger,
        )

    def _send_message(
        self,
        message: str,
    ):
        payload = {
            "chat_id": self.configuration.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        url = f"https://api.telegram.org/bot{self.configuration.bot_token}/sendMessage"

        response = requests.post(
            url=url,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
