import datetime
import logging
import requests


class Alerter:
    def __init__(
        self,
        logger: logging.Logger,
    ):
        self.logger = logger

    def alert(
        self,
        symbol: str,
        timeframe: int,
        bar_date: datetime.datetime,
        bar_index: int,
        message: str,
    ):
        bot_token = "8571936110:AAERqN-YhP_SZyj8_STi5nSwhqguwrUhcZc"
        chat_id = "-1003604401866"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(
            url=url,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        self.logger.info(
            msg="Alert has been sent successfully",
            extra={
                "worker": f"{__name__}.{__class__.__name__}",
                "symbol": symbol,
                "timeframe": timeframe,
                "bar_time": bar_date,
                "current_index": bar_index,
            },
        )
