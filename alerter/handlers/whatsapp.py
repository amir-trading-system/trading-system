import logging
import requests

import config_manager
import common

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
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
        emoji: str,
        base_except_one: bool,
        milestones: common.objects.Milestones,
        sorted_indicators: dict[str,float],
    ):
        return ""

    def design_confirmation_bar_message(
        self,
        original_bar: common.objects.BarData,
        entry_position_bar: common.objects.BarData,
        evidence_name: str,
    ) -> str:
        return ""

    def _send_message(
        self,
        message: str,
    ):
        url = f"https://graph.facebook.com/v19.0/{self.configuration.whatsapp.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.configuration.whatsapp.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": self.configuration.whatsapp.recipient,
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
