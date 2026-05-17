import datetime
import logging
import requests

import config_manager
import common


class Handler:
    name = "Telegram"
    is_enabled = True

    def __init__(
        self,
        configuration: config_manager.Alerts,
        logger: logging.Logger,
    ):
        self.configuration = configuration
        self.logger = logger

    def design_indicated_bar_message(
        self,
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
        emoji: str,
        evidences: list[str],
        milestones: common.objects.Milestones,
    ) -> str:
        return f"""
            <b>{emoji} Congrats! {emoji}</b>

            <b>Symbol:</b> <u>{stock.symbol_name}</u>
            <b>Timeframe:</b> <code>{stock.timeframe}</code>
            <b>Time:</b> <code>{current_bar.bar_time}</code>
            <b>Starting Time:</b> <code>{milestones.starting_bar.bar_time}</code>
            <b>Top Time:</b> <code>{milestones.top_bar.bar_time}</code>
            <b>{len(evidences)} Indications:</b>
            {chr(10).join(f"• <i>{evidence}</i>" for evidence in evidences)}
            """

    def design_confirmation_bar_message(
        self,
        stock: common.objects.Stock,
        original_bar: common.objects.BarData,
        entry_position_bar: common.objects.BarData,
        highest_high_one_minute_bar: common.objects.BarData,
        evidence_name: str,
    ) -> str:
        crossed_resistance_bar_time = None
        for resistance_level in stock.resistance_levels:
            if entry_position_bar.low < resistance_level.high < entry_position_bar.high:
                crossed_resistance_bar_time = resistance_level.bar_time

        return f"""
            <b>Entry position confirmed for:</b>
            <b>Symbol:</b> <u>{entry_position_bar.symbol}</u>
            <b>Evidence:</b> <code>{evidence_name}</code>
            <b>Timeframe:</b> <code>{entry_position_bar.timeframe}</code>
            <b>Crossed highest high:</b> <code>{highest_high_one_minute_bar.high if highest_high_one_minute_bar is not None else 0}</code>
            <b>Highest high Bar Time:</b> <code>{highest_high_one_minute_bar.bar_time if highest_high_one_minute_bar is not None else 0}</code>
            <b>Time:</b> <code>{entry_position_bar.bar_time}</code>
            <b>Original bar to confirm Time:</b> <code>{original_bar.bar_time}</code>
            <b>Original bar to confirm Timeframe:</b> <code>{original_bar.timeframe}</code>
            <b>Resistance Crossed bar time:</b> <code>{crossed_resistance_bar_time if crossed_resistance_bar_time is not None else ""}</code>
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

    def alert(
        self,
        sender: str,
        symbol: str,
        timeframe: int,
        bar_date: datetime.datetime,
        bar_index: int,
        message: str,
        is_retro: bool,
        request_id: int,
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
                    "request_id": request_id,
                },
            )
            return

        if is_retro:
            message = ""
            if sender == "Confirmator":
                message = f"Congrats! {symbol} has been confirmed on {bar_date}"
            else:
                message = f"Congrats! {symbol} has indication on {bar_date}"

            self.logger.info(
                msg=message,
                extra={
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "bar_time": bar_date,
                    "request_id": request_id,
                },
            )
            return

        try:
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
                    "request_id": request_id,
                },
            )
        except Exception as e:
            self.logger.error(
                msg="An error occurred while sending message via alerter",
                extra={
                    "exception": e,
                    "worker": sender,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "bar_time": bar_date,
                    "current_index": bar_index,
                    "request_id": request_id,
                },
            )
