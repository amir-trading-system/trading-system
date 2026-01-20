from . import _alert_handler

from . import telegram
from . import whatsapp

__handlers__: list[_alert_handler.Handler] = [
    telegram.Handler,
    whatsapp.Handler,
]
