import logging
import requests

import config_manager
from tws import objects as tws_objects
from analyzer import objects as analyzer_objects

from . import _alert_handler


class Handler(
    _alert_handler.Handler,
):
    name = "Whatsapp"

    def __init__(
        self,
        configuration: config_manager.Alerts,
        logger: logging.Logger,
    ):
        super().__init__(
            configuration=configuration,
            logger=logger,
        )

    def design_indicated_bar_message(
        self,
        stock: tws_objects.Stock,
        current_bar: tws_objects.BarData,
        emoji: str,
        base_except_one: bool,
        milestones: analyzer_objects.Milestones,
        sorted_indicators: dict[str,float],
    ):
        return ""

    def design_confirmation_bar_message(
        self,
        original_bar: tws_objects.BarData,
        entry_position_bar: tws_objects.BarData,
    ) -> str:
        return ""

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
