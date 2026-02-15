import os

import dotenv

class Telegram:
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        enabled: bool,
    ):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled


class Alerts:
    def __init__(
        self,
        telegram: Telegram,
    ):
        self.telegram = telegram


class BotConfig:
    def __init__(
        self,
        alerts: Alerts,
    ):
        self.alerts = alerts


class ConfigManager:
    def load_config(
        self,
    ) -> BotConfig:
        dotenv.load_dotenv()

        return BotConfig(
            alerts=Alerts(
                telegram=Telegram(
                    bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
                    chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
                    enabled=True if os.getenv("TELEGRAM_ENABLED") == 'true' else False,
                ),
            ),
        )
