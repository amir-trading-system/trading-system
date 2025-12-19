import datetime
import pandas as pd
import talib

from ibapi import client, wrapper, common
from . import objects


class TWSClient(client.EClient, wrapper.EWrapper):
    def __init__(
        self,
        host: str,
        port: int,
        request_id_to_stock: dict[int, objects.Stock],
    ):
        self.order_id = None
        client.EClient.__init__(
            self,
            self,
        )
        self.client = client
        self.host = host
        self.port = port

        self.request_id_to_stock = request_id_to_stock

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
        bars: list[objects.BarData],
    ) -> list[objects.BarData]:
        bar_data_df = pd.DataFrame([vars(bar) for bar in bars])

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

        results_dict = bar_data_df.to_dict(orient="records")
        bars = [objects.BarData(**kwargs) for kwargs in results_dict]
        return bars


    def historicalData(
        self,
        reqId: int,
        bar: common.BarData,
    ):
        bar_time = datetime.datetime.fromtimestamp(float(bar.date))
        self.request_id_to_stock[reqId].bars.append(
            objects.BarData(
                open_value=bar.open,
                close=bar.close,
                high=bar.high,
                low=bar.low,
                volume=bar.volume,
                vwap=bar.wap,
                bar_time=bar_time,
            )
        )

    def historicalDataEnd(
        self,
        reqId: int,
        start: str,
        end: str,
    ):
        relevant_stock_bars = self.request_id_to_stock[reqId].bars
        bars_data = self.enrich_bars(
            bars=relevant_stock_bars,
        )
        self.request_id_to_stock[reqId].bars = bars_data

    def historicalDataUpdate(
        self,
        reqId: int,
        bar: common.BarData,
    ):
        relevant_stock_bars = self.request_id_to_stock[reqId].bars
        current_bar_time = datetime.datetime.fromtimestamp(float(bar.date))
        current_bar = objects.BarData(
            open_value=bar.open,
            close=bar.close,
            high=bar.high,
            low=bar.low,
            volume=bar.volume,
            vwap=bar.wap,
            bar_time=current_bar_time,
        )

        if relevant_stock_bars[-1].bar_time == current_bar_time:
            relevant_stock_bars[-1] = current_bar
        else:
            relevant_stock_bars.append(current_bar)

        bars_data = self.enrich_bars(
            bars=relevant_stock_bars,
        )
        self.request_id_to_stock[reqId].bars = bars_data
