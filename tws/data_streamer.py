import datetime
import logging
import queue

import pandas as pd
import talib
from talib import MA_Type
from ibapi import common

import alerter
from . import objects


class DataStreamer():
    on_specific_bar_time: bool = False
    is_retro: bool = False

    def __init__(
        self,
        request_id_to_symbol: dict[int, objects.Stock],
        bars_ready_to_analyze_queue: queue.Queue,
        ibapi_requests: dict[int,objects.IbAPIRequest],
        logger: logging.Logger,
        alerter_object: alerter.alerter.Alerter,
    ):
        self.ibapi_requests = ibapi_requests
        self.request_id_to_symbol = request_id_to_symbol
        self.bars_ready_to_analyze_queue = bars_ready_to_analyze_queue
        self.logger = logger
        self.alerter_object = alerter_object

    def _filter_ignored_bars(
        self,
        bars: list[objects.BarData],
    ):
        relevant_bars: list[objects.BarData] = []
        for i, bar_object in enumerate(bars):
            if (
                bar_object.bar_time.hour == 8
                and bar_object.bar_time.minute == 0
                and i+1 < len(bars)-1
            ):
                bar_before = bars[i-1]
                bar_after = bars[i+1]
                if (
                    bar_object.volume > bar_before.volume * 10
                    and bar_object.volume > bar_after.volume * 10
                    and bar_object.high - bar_object.low > (bar_before.high - bar_before.low) * 10
                    and bar_object.high - bar_object.low > (bar_after.high - bar_after.low) * 10
                ):
                    continue

            relevant_bars.append(bar_object)

        return relevant_bars

    #pylint: disable=no-member
    def enrich_bars(
        self,
        bars: list[objects.BarData],
    ) -> list[objects.BarData]:
        fitered_bars = self._filter_ignored_bars(
            bars=bars,
        )
        bar_data_df = pd.DataFrame([vars(bar_candle) for bar_candle in fitered_bars])

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

        ## calculate vwap
        bar_data_df["bar_time"] = (
            pd.to_datetime(bar_data_df["bar_time"])
        )
        since_open_bar_df = bar_data_df.where(
            (bar_data_df["bar_time"].dt.time >= pd.to_datetime("09:30").time()) &
            (bar_data_df["bar_time"].dt.time <= pd.to_datetime("16:00").time())
        )
        since_open_bar_df["session"] = since_open_bar_df["bar_time"].dt.date

        since_open_bar_df["volume"] = since_open_bar_df["volume"].astype(float)
        since_open_bar_df["hlc3"] = (since_open_bar_df["high"] + since_open_bar_df["low"] + since_open_bar_df["close"]) / 3
        since_open_bar_df["pv"] = since_open_bar_df["hlc3"] * since_open_bar_df["volume"]

        bar_data_df["vwap"] = since_open_bar_df.groupby("session")["pv"].cumsum() / since_open_bar_df.groupby("session")["volume"].cumsum()

        [macd, signal_line, histogram] = talib.MACDEXT(
            real=bar_data_df["close"],
            fastperiod=12,
            fastmatype=MA_Type.EMA,
            slowperiod=26,
            slowmatype=MA_Type.EMA,
            signalperiod=9,
            signalmatype=MA_Type.EMA,
        )
        bar_data_df["macd"] = macd
        bar_data_df["signal_line"] = signal_line
        bar_data_df["histogram"] = histogram

        results_dict = bar_data_df.to_dict(orient="records")
        bars = sorted(
            [objects.BarData(**kwargs) for kwargs in results_dict],
            key=lambda bar: bar.bar_time,
        )
        for i, bar_object in enumerate(bars):
            bar_object.index = len(bars) - i-1

        return bars

    def get_historical_data(
        self,
        request_id: int,
        tws_bar: common.BarData,
    ):
        bar_time = datetime.datetime.fromtimestamp(float(tws_bar.date))
        now = datetime.datetime.now()
        if (
            (now.day != bar_time.day and bar_time.hour < 16 and not self.on_specific_bar_time and not self.is_retro)
            or tws_bar.volume == 0.0
        ):
            return

        ibapi_request = self.ibapi_requests.get(request_id, None)
        if ibapi_request is None:
            return

        self.request_id_to_symbol[request_id].bars.append(
            objects.BarData(
                symbol=ibapi_request.symbol,
                timeframe=ibapi_request.timeframe,
                open_value=tws_bar.open,
                close=tws_bar.close,
                high=tws_bar.high,
                low=tws_bar.low,
                volume=float(tws_bar.volume),
                bar_time=bar_time,
            )
        )

    def on_historical_data_end(
        self,
        request_id: int,
    ):
        relevant_symbol_bars = self.request_id_to_symbol[request_id].bars
        symbol = self.request_id_to_symbol[request_id].symbol_name
        bars_data = self.enrich_bars(
            bars=relevant_symbol_bars,
        )
        for bar_object in bars_data:
            bar_object.ready_to_analyze = True
        self.request_id_to_symbol[request_id].bars = bars_data
        self.request_id_to_symbol[request_id].ready_to_confirm = True
        if self.request_id_to_symbol[request_id].timeframe == 1:
            return

        self.bars_ready_to_analyze_queue.put(self.request_id_to_symbol[request_id])
        self.logger.info(
            msg="Finished to collect data for symbol",
            extra={
                "worker": f"{__name__}.{__class__.__name__}",
                "symbol": symbol,
            }
        )

    def on_historical_data_update(
        self,
        request_id: int,
        tws_bar: common.BarData,
    ):
        if tws_bar.volume == 0.0:
            return

        relevant_symbol_bars = self.request_id_to_symbol[request_id].bars
        current_bar_time = datetime.datetime.fromtimestamp(float(tws_bar.date))

        ibapi_request = self.ibapi_requests.get(request_id, None)
        if ibapi_request is None:
            return

        current_bar = objects.BarData(
            symbol=ibapi_request.symbol,
            timeframe=ibapi_request.timeframe,
            open_value=tws_bar.open,
            close=tws_bar.close,
            high=tws_bar.high,
            low=tws_bar.low,
            volume=tws_bar.volume,
            bar_time=current_bar_time,
        )

        if relevant_symbol_bars[-1].bar_time == current_bar_time:
            relevant_symbol_bars[-1].close = tws_bar.close
            relevant_symbol_bars[-1].open_value = tws_bar.open
            relevant_symbol_bars[-1].high = tws_bar.high
            relevant_symbol_bars[-1].low = tws_bar.low
            relevant_symbol_bars[-1].volume = float(tws_bar.volume)

            bars_data = self.enrich_bars(
                bars=relevant_symbol_bars,
            )

            if ibapi_request.timeframe == 1:
                bars_data[-1].ready_to_analyze = True
                self.request_id_to_symbol[request_id].bars = bars_data
                self.request_id_to_symbol[request_id].ready_to_confirm = True

            return

        relevant_symbol_bars[-1].ready_to_analyze = True
        relevant_symbol_bars.append(current_bar)
        bars_data = self.enrich_bars(
            bars=relevant_symbol_bars,
        )
        self.request_id_to_symbol[request_id].bars = bars_data
        self.request_id_to_symbol[request_id].ready_to_confirm = True

        if self.request_id_to_symbol[request_id].timeframe == 1:
            return

        self.bars_ready_to_analyze_queue.put(self.request_id_to_symbol[request_id])
        relevant_symbol = self.request_id_to_symbol[request_id]
        self.logger.info(
            msg="Bar is ready to analyze and confirm",
            extra={
                "worker": f"{__name__}.{__class__.__name__}",
                "symbol": relevant_symbol.symbol_name,
                "timeframe": relevant_symbol.timeframe,
            }
        )
