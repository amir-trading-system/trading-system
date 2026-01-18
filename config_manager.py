import yaml


class Elasticsearch:
    def __init__(
        self,
        username: str,
        password: str,
        certs_file_path: str,
    ):
        self.username = username
        self.password = password
        self.certs_file_path = certs_file_path


class Logger:
    def __init__(
        self,
        elasticsearch: Elasticsearch
    ):
        self.elasticsearch = elasticsearch


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
        logger: Logger,
    ):
        self.alerts = alerts
        self.logger = logger


class ConfigManager:
    def load_config(
        self,
    ) -> BotConfig:
        #pylint:disable=unspecified-encoding
        with open("config.yaml", "r") as f:
            settings: dict[str, any] = yaml.safe_load(f)

        alerts_config = settings.get("alerts", None).get("telegram", None)
        logger_config = settings.get("logger", None).get("elasticsearch", None)

        return BotConfig(
            alerts=Alerts(
                telegram_alerter=TelegramAlerter(
                    bot_token=alerts_config.get("bot_token"),
                    chat_id=alerts_config.get("chat_id"),
                ),
            ),
            logger=Logger(
                elasticsearch=Elasticsearch(
                    username=logger_config.get("username"),
                    password=logger_config.get("password"),
                    certs_file_path=logger_config.get("certs_file_path"),
                ),
            ),
        )
