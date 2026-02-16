import datetime
import logging
import queue

import pandas as pd
import talib
from talib import MA_Type # type: ignore
from ibapi import common as ibapi_common

import common


class DataStreamer():
    on_specific_bar_time: bool = False
    is_retro: bool = False

    def __init__(
        self,
        request_id_to_symbol: dict[int, common.objects.Stock],
        bars_ready_to_analyze_queue: queue.Queue,
        ibapi_requests: dict[int,common.objects.IbAPIRequest],
        logger: logging.Logger,
    ):
        self.ibapi_requests = ibapi_requests
        self.request_id_to_symbol = request_id_to_symbol
        self.bars_ready_to_analyze_queue = bars_ready_to_analyze_queue
        self.logger = logger

    def _filter_ignored_bars(
        self,
        bars: list[common.objects.BarData],
    ):
        relevant_bars: list[common.objects.BarData] = []
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

    def enrich_bars(
        self,
        bars: list[common.objects.BarData],
    ) -> list[common.objects.BarData]:
        if not bars:
            return []

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
            (bar_data_df["bar_time"].dt.time >= pd.to_datetime("09:30").time()) & # type: ignore
            (bar_data_df["bar_time"].dt.time <= pd.to_datetime("16:00").time()) # type: ignore
        )
        is_one_day_bars = fitered_bars[0].timeframe_type == common.objects.TimeframeType.DAY
        if is_one_day_bars:
            since_open_bar_df = bar_data_df.copy()

        since_open_bar_df["session"] = since_open_bar_df["bar_time"].dt.date # type: ignore

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
            [common.objects.BarData(**kwargs) for kwargs in results_dict], # pyright: ignore[reportCallIssue]
            key=lambda bar: bar.bar_time,
        )
        for i, bar_object in enumerate(bars):
            bar_object.index = len(bars) - i-1

        return bars

    def get_historical_data(
        self,
        request_id: int,
        tws_bar: ibapi_common.BarData,
    ):
        is_timestamp = len(tws_bar.date) == 10
        is_date = len(tws_bar.date) == 8
        bar_time = None
        if is_timestamp:
            bar_time = datetime.datetime.fromtimestamp(float(tws_bar.date))
        if is_date:
            bar_time = datetime.datetime.strptime(tws_bar.date, '%Y%m%d')

        now = datetime.datetime.now()
        if (
            is_timestamp
            and (
                (now.day != bar_time.day and bar_time.hour < 16 and not self.on_specific_bar_time and not self.is_retro)
                or tws_bar.volume == 0.0
            )
        ):
            return

        ibapi_request = self.ibapi_requests.get(request_id, None)
        if ibapi_request is None:
            return

        self.request_id_to_symbol[request_id].bars.append(
            common.objects.BarData(
                symbol=ibapi_request.symbol,
                timeframe=ibapi_request.timeframe,
                timeframe_type=ibapi_request.timeframe_type,
                open_value=tws_bar.open,
                close=tws_bar.close,
                high=tws_bar.high,
                low=tws_bar.low,
                volume=float(tws_bar.volume),
                bar_time=bar_time,
            )
        )

    def insert_one_minute_bars_into_confirmation_queues(
        self,
        one_minute_request_id: int,
        symbol: str,
        specific_bar_time: datetime.datetime = None,
    ):
        current_session_date = datetime.datetime.fromtimestamp(0)
        previous_session_date = datetime.datetime.fromtimestamp(0)
        if specific_bar_time is not None:
            current_session_date = specific_bar_time
            previous_session_date = specific_bar_time - datetime.timedelta(days=1)
        else:
            date_now = datetime.datetime.now()
            current_session_date = datetime.datetime(
                year=date_now.year,
                month=date_now.month,
                day=date_now.day,
            )
            previous_session_date = current_session_date - datetime.timedelta(days=1)

        temp_request_id_to_symbol = {
            key: value
            for key, value in self.request_id_to_symbol.items()
            if value.symbol_name == symbol
        }
        one_minute_bars = temp_request_id_to_symbol[one_minute_request_id].bars

        for _, stock in temp_request_id_to_symbol.items():
            if stock.timeframe_type == common.objects.TimeframeType.DAY:
                if specific_bar_time is not None and stock.specific_bar_time != specific_bar_time:
                    continue
                for one_minute_bar in one_minute_bars:
                    if (
                        True
                        and one_minute_bar.bar_time >= datetime.datetime(
                            year=previous_session_date.year,
                            month=previous_session_date.month,
                            day=previous_session_date.day,
                            hour=16,
                            minute=0,
                        )
                        and one_minute_bar.bar_time < datetime.datetime(
                            year=current_session_date.year,
                            month=current_session_date.month,
                            day=current_session_date.day,
                            hour=9,
                            minute=30,
                        )
                    ):
                        stock.last_post_pre_one_minute_highest_high = max(
                            stock.last_post_pre_one_minute_highest_high,
                            one_minute_bar.high,
                        )

                    stock.one_minute_bars_queue.put(one_minute_bar)

    def on_historical_data_end(
        self,
        request_id: int,
    ):
        relevant_symbol_bars = self.request_id_to_symbol[request_id].bars
        symbol = self.request_id_to_symbol[request_id].symbol_name
        specific_bar_time = self.request_id_to_symbol[request_id].specific_bar_time
        bars_data = self.enrich_bars(
            bars=relevant_symbol_bars,
        )
        for bar_object in bars_data:
            bar_object.ready_to_analyze = True
        self.request_id_to_symbol[request_id].bars = bars_data
        if self.request_id_to_symbol[request_id].is_one_minute_timeframe():
            self.insert_one_minute_bars_into_confirmation_queues(
                one_minute_request_id=request_id,
                symbol=symbol,
                specific_bar_time=specific_bar_time,
            )
            return

        self.bars_ready_to_analyze_queue.put(self.request_id_to_symbol[request_id])
        self.request_id_to_symbol[request_id].finished_collection = True
        self.logger.info(
            msg="Finished to collect data for symbol",
            extra={
                "worker": "DataStreamer",
                "symbol": symbol,
                "timeframe": self.request_id_to_symbol[request_id].timeframe,
                "timeframe_type": self.request_id_to_symbol[request_id].timeframe_type.value,
            }
        )

    def on_historical_data_update(
        self,
        request_id: int,
        tws_bar: ibapi_common.BarData,
    ):
        if tws_bar.volume == 0.0:
            return

        relevant_symbol_bars = self.request_id_to_symbol[request_id].bars
        current_bar_time = datetime.datetime.fromtimestamp(float(tws_bar.date))

        ibapi_request = self.ibapi_requests.get(request_id, None)
        if ibapi_request is None:
            return

        current_bar = common.objects.BarData(
            symbol=ibapi_request.symbol,
            timeframe=ibapi_request.timeframe,
            timeframe_type=ibapi_request.timeframe_type,
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

            if ibapi_request.is_one_minute_timeframe():
                bars_data[-1].ready_to_analyze = True
                self.request_id_to_symbol[request_id].bars = bars_data
                self.insert_one_minute_bars_into_confirmation_queues(
                    one_minute_request_id=request_id,
                    symbol=self.request_id_to_symbol[request_id].symbol_name,
                    specific_bar_time=self.request_id_to_symbol[request_id].specific_bar_time,
                )

            if not ibapi_request.is_day_timeframe():
                return

        relevant_symbol_bars[-1].ready_to_analyze = True
        relevant_symbol_bars.append(current_bar)
        bars_data = self.enrich_bars(
            bars=relevant_symbol_bars,
        )
        self.request_id_to_symbol[request_id].bars = bars_data

        if self.request_id_to_symbol[request_id].is_one_minute_timeframe():
            self.insert_one_minute_bars_into_confirmation_queues(
                one_minute_request_id=request_id,
                symbol=self.request_id_to_symbol[request_id].symbol_name,
                specific_bar_time=self.request_id_to_symbol[request_id].specific_bar_time,
            )
            return

        self.bars_ready_to_analyze_queue.put(self.request_id_to_symbol[request_id])
