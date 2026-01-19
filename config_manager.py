import yaml


class TelegramAlerter:
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
    ):
        self.bot_token = bot_token
        self.chat_id = chat_id


class Alerts:
    def __init__(
        self,
        telegram_alerter: TelegramAlerter,
    ):
        self.telegram_alerter = telegram_alerter


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
        #pylint:disable=unspecified-encoding
        with open("config.yaml", "r") as f:
            settings: dict[str, any] = yaml.safe_load(f)

        alerts_config = settings.get("alerts", None).get("telegram", None)

        return BotConfig(
            alerts=Alerts(
                telegram_alerter=TelegramAlerter(
                    bot_token=alerts_config.get("bot_token"),
                    chat_id=alerts_config.get("chat_id"),
                ),
            ),
        )
