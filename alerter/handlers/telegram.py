import logging
import requests

import config_manager
import common

from . import _alert_handler


class Handler(
    _alert_handler.Handler,
):
    name = "Telegram"
    is_enabled = True

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
    ) -> str:
        return f"""
            <b>{emoji} Congrats! {emoji}</b>
            {"<b>BASE EXCEPT ONE!</b>" if base_except_one else ""}

            <b>Symbol:</b> <u>{stock.symbol_name}</u>
            <b>Timeframe:</b> <code>{stock.timeframe}</code>
            <b>Time:</b> <code>{current_bar.bar_time}</code>
            <b>Starting Time:</b> <code>{milestones.starting_bar.bar_time}</code>
            <b>Top Time:</b> <code>{milestones.top_bar.bar_time}</code>

            <b>{len(sorted_indicators)} Indications:</b>
            {chr(10).join(f"• <i>{indicator_name}: {rate}</i>" for indicator_name, rate in sorted_indicators.items())}
            """

    def design_confirmation_bar_message(
        self,
        original_bar,
        entry_position_bar,
    ) -> str:
        return f"""
            <b>Entry position confirmed for:</b>
            <b>Symbol:</b> <u>{entry_position_bar.symbol}</u>
            <b>Timeframe:</b> <code>{entry_position_bar.timeframe}</code>
            <b>Time:</b> <code>{entry_position_bar.bar_time}</code>
            <b>Original bar to confirm Time:</b> <code>{original_bar.bar_time}</code>
            <b>Original bar to confirm Timeframe:</b> <code>{original_bar.timeframe}</code>
        """

    def _send_message(
        self,
        message: str,
    ):
        payload = {
            "chat_id": self.configuration.telegram.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        url = f"https://api.telegram.org/bot{self.configuration.telegram.bot_token}/sendMessage"

        response = requests.post(
            url=url,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
