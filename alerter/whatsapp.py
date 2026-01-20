import datetime
import logging
import requests

import config_manager

from . import _alerter


class Whatsapp(
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
        url = f"https://graph.facebook.com/v19.0/{self.configuration.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.configuration.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": self.configuration.recipient,
            "type": "text",
            "text": {
                "body": message,
            },
        }

        response = requests.post(
            url=url,
            headers=headers,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
