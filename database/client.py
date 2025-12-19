import sqlite3

from . import bars_table
from . import monitored_stocks_table

class Client:
    db_name = "day_trading"
    def __init__(
        self,
    ):
        self.connection = None
        self.bars_table = bars_table.BarsTable()
        self.monitored_stocks_table = monitored_stocks_table.MonitoredStocksTable()

    def connect(
        self,
    ):
        self.connection = sqlite3.connect(self.db_name)

    def __enter__(
        self,
    ):
        self.connect()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.connection.close()
