from . import _alert_handler

from . import telegram
from . import whatsapp

__handlers__: list[type[_alert_handler.Handler]] = [
    telegram.Handler,
    whatsapp.Handler,
]
