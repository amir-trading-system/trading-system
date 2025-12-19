import pandas as pd
import talib

from ibapi import client, wrapper

import database


class TWSClient(client.EClient, wrapper.EWrapper):
    def __init__(
        self,
        host: str,
        port: int,
        database_client: database.client.Client,
    ):
        self.order_id = None
        client.EClient.__init__(
            self,
            self,
        )
        self.database_client = database_client
        self.client = client
        self.host = host
        self.port = port

        self.bars: list[dict] = []

    def connect_tws(
        self,
    ):
        self.connect(
            host=self.host,
            port=self.port,
            clientId=0,
        )

    def nextValidId(
        self,
        orderId,
    ):
        self.order_id = orderId

    def nextId(
        self,
    ):
        self.order_id += 1
        return self.order_id

    def error(self, reqId, errorTime, errorCode, errorString, advancedOrderRejectJson=""):
        print(f"reqId: {reqId}, errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderRejectJson}")

    def enrich_bars(
        self,
    ) -> pd.DataFrame:
        bar_data_df = pd.DataFrame(self.bars)

        bar_data_df["ema_9"] = talib.EMA(
            real=bar_data_df["close"],
            timeperiod=9,
        )
        bar_data_df["ema_20"] = talib.EMA(
            real=bar_data_df["close"],
            timeperiod=20,
        )
        bar_data_df["volume_average"] = talib.SMA(
            real=bar_data_df["volume"],
            timeperiod=20,
        )
        [macd, signal_line, histogram] = talib.MACD(
            real=bar_data_df["close"],
        )
        bar_data_df["macd"] = macd
        bar_data_df["signal_line"] = signal_line
        bar_data_df["histogram"] = histogram
        return bar_data_df

    def historicalData(self, reqId, bar):
        bar_data = {
            "open_value": bar.open,
            "close": bar.close,
            "high": bar.high,
            "low": bar.low,
            "volume": bar.volume,
            "vwap": bar.wap,
            "time": bar.date,
        }
        self.bars.append(bar_data)

    def historicalDataEnd(self, reqId, start, end):
        bar_data = self.enrich_bars()
        bars = bar_data.to_dict()
        res = talib.get_functions()
        print("h")

    def historicalDataUpdate(self, reqId, bar):
        print(f"reqId: {reqId}, bar: {str(bar)}. price: {bar.close}")
