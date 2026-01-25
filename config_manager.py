import os

import dotenv


class Whatsapp:
    def __init__(
        self,
        access_token: str,
        phone_number_id: str,
        recipient: str,
        enabled: bool,
    ):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.recipient = recipient
        self.enabled = enabled


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
        whatsapp: Whatsapp,
    ):
        self.telegram = telegram
        self.whatsapp = whatsapp


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
                whatsapp=Whatsapp(
                    access_token=os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
                    phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""),
                    recipient=os.getenv("WHATSAPP_RECIPIENT", ""),
                    enabled=True if os.getenv("WHATSAPP_ENABLED") == 'true' else False,
                ),
            ),
        )
