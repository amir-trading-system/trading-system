import datetime
import logging
import queue
import time

import pandas as pd
import talib
from talib import MA_Type # type: ignore
from ibapi import common as ibapi_common

import common


class DataStreamer():
    on_specific_bar_time: bool = False

    def __init__(
        self,
        request_id_to_symbol: dict[int, common.objects.Stock],
        bars_ready_to_analyze_queue: queue.Queue,
        ibapi_requests: dict[int,common.objects.IbAPIRequest],
        logger: logging.Logger,
        monitored_symbols: list[str],
        potential_symbols_file_path: str = None,
    ):
        self.ibapi_requests = ibapi_requests
        self.request_id_to_symbol = request_id_to_symbol
        self.bars_ready_to_analyze_queue = bars_ready_to_analyze_queue
        self.logger = logger
        self.potential_symbols_file_path = potential_symbols_file_path
        self.monitored_symbols = monitored_symbols
        self.today_monitored_symbols: list[str] = []

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

        bar_data_df["session"] = bar_data_df["bar_time"].dt.date # type: ignore

        bar_data_df["volume"] = bar_data_df["volume"].astype(float)
        bar_data_df["hlc3"] = (bar_data_df["high"] + bar_data_df["low"] + bar_data_df["close"]) / 3
        bar_data_df["pv"] = bar_data_df["hlc3"] * bar_data_df["volume"]

        bar_data_df["vwap"] = bar_data_df.groupby("session")["pv"].cumsum() / bar_data_df.groupby("session")["volume"].cumsum()

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

        bar_data_df = bar_data_df.sort_values("bar_time")
        columns = common.objects.BarData.field_names()
        formatted_bars = [
            common.objects.BarData(*row)
            for row in bar_data_df[columns].itertuples(index=False, name=None)
        ]

        for i, bar_object in enumerate(formatted_bars):
            bar_object.index = len(formatted_bars) - i-1

        return formatted_bars

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
                (now.day != bar_time.day and bar_time.hour < 16 and not self.on_specific_bar_time)
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
            previous_session_date = current_session_date - datetime.timedelta(
                days=1,
            )
        else:
            date_now = datetime.datetime.now()
            current_session_date = datetime.datetime(
                year=date_now.year,
                month=date_now.month,
                day=date_now.day,
            )
            previous_session_date = current_session_date - datetime.timedelta(
                days=1,
            )

        while previous_session_date.weekday() > 4:
            previous_session_date -= datetime.timedelta(
                days=1,
            )

        day_timeframe_stock = [
            stock
            for stock in self.request_id_to_symbol.values()
            if stock.symbol_name == symbol
            and stock.is_day_timeframe()
            and (
                not self.on_specific_bar_time
                or (
                    stock.specific_bar_time is not None
                    and stock.specific_bar_time == specific_bar_time
                )
            )
        ][0]
        one_minute_bars = self.request_id_to_symbol[one_minute_request_id].bars
        if specific_bar_time is not None and day_timeframe_stock.specific_bar_time != specific_bar_time:
            return

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
                day_timeframe_stock.post_pre_market_volume_sum += one_minute_bar.volume
                day_timeframe_stock.last_post_pre_one_minute_highest_high = max(
                    day_timeframe_stock.last_post_pre_one_minute_highest_high,
                    one_minute_bar.high,
                )

            day_timeframe_stock.one_minute_bars_queue.put(one_minute_bar)

    def on_historical_data_end(
        self,
        request_id: int,
    ):
        stock = self.request_id_to_symbol[request_id]

        if stock.is_day_timeframe() and self.on_specific_bar_time:
            one_minute_timeframe_stock = self.request_id_to_symbol[stock.one_minute_request_id]
            while not one_minute_timeframe_stock.finished_collection:
                time.sleep(2)

        relevant_symbol_bars = stock.bars
        symbol = stock.symbol_name
        specific_bar_time = stock.specific_bar_time
        bars_data = self.enrich_bars(
            bars=relevant_symbol_bars,
        )
        for bar_object in bars_data:
            bar_object.ready_to_analyze = True
        stock.bars = bars_data
        if stock.is_one_minute_timeframe():
            self.insert_one_minute_bars_into_confirmation_queues(
                one_minute_request_id=request_id,
                symbol=symbol,
                specific_bar_time=specific_bar_time,
            )
            stock.finished_collection = True
            return

        stock.finished_collection = True

        if (
            True
            and (
                (
                    stock.is_worth_to_monitor()
                    and stock.symbol_name in self.monitored_symbols
                ) or self.on_specific_bar_time
            )
        ):
            self.bars_ready_to_analyze_queue.put(stock)
        self.logger.info(
            msg="Finished to collect data for symbol",
            extra={
                "worker": "DataStreamer",
                "symbol": symbol,
                "timeframe": stock.timeframe,
                "timeframe_type": stock.timeframe_type.value,
                "request_id": request_id,
            }
        )

    def on_historical_data_update(
        self,
        request_id: int,
        tws_bar: ibapi_common.BarData,
    ):
        if tws_bar.volume == 0.0:
            return

        stock = self.request_id_to_symbol[request_id]
        now = datetime.datetime.now()

        if (
            True
            and not self.on_specific_bar_time
            and stock.symbol_name not in self.monitored_symbols
            and now < datetime.datetime(
                year=now.year,
                month=now.month,
                day=now.day,
                hour=16,
                minute=1,
            )
        ):
            return

        if stock.symbol_name not in self.today_monitored_symbols:
            self.insert_symbol_to_future_list(
                symbol=stock.symbol_name,
            )

        relevant_symbol_bars = stock.bars
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
                stock.bars = bars_data
                self.insert_one_minute_bars_into_confirmation_queues(
                    one_minute_request_id=request_id,
                    symbol=stock.symbol_name,
                    specific_bar_time=stock.specific_bar_time,
                )
                return

        relevant_symbol_bars[-1].ready_to_analyze = True
        relevant_symbol_bars.append(current_bar)
        bars_data = self.enrich_bars(
            bars=relevant_symbol_bars,
        )
        stock.bars = bars_data

        if stock.is_one_minute_timeframe():
            self.insert_one_minute_bars_into_confirmation_queues(
                one_minute_request_id=request_id,
                symbol=stock.symbol_name,
                specific_bar_time=stock.specific_bar_time,
            )
            return

        if stock.is_worth_to_monitor():
            self.bars_ready_to_analyze_queue.put(stock)

    #pylint:disable=unspecified-encoding
    def insert_symbol_to_future_list(
        self,
        symbol: str,
    ):
        current_bar: common.objects.BarData = None
        relevant_bars: list[common.objects.BarData] = []

        day_timeframe_stock = [
            stock_obj
            for stock_obj in self.request_id_to_symbol.values()
            if stock_obj.symbol_name == symbol
            and stock_obj.timeframe_type == common.objects.TimeframeType.DAY
        ][0]

        if day_timeframe_stock.bars:
            relevant_bars = sorted(
                day_timeframe_stock.bars,
                key=lambda bar_obj: bar_obj.bar_time,
                reverse=True,
            )
            current_bar = relevant_bars[0]
        else:
            return

        now = datetime.datetime.now()
        if (
            True
            and not self.on_specific_bar_time
            and self.potential_symbols_file_path is not None
            and now >= datetime.datetime(
                year=now.year,
                month=now.month,
                day=now.day,
                hour=16,
                minute=1,
            )
        ):
            if day_timeframe_stock.bar_is_the_first_one_in_trend(
                bar_object=current_bar,
                relevant_bars=relevant_bars,
            ):
                with open(self.potential_symbols_file_path, "a") as f:
                    f.write(f"{current_bar.symbol}--{datetime.datetime(
                        year=now.year,
                        month=now.month,
                        day=now.day,
                    )}\n")

                self.monitored_symbols.append(current_bar.symbol)
                self.today_monitored_symbols.append(current_bar.symbol)
