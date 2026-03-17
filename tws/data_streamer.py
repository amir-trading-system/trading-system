import datetime
import logging

from ibapi import common as ibapi_common

import common


class DataStreamer():
    on_specific_bar_time: bool = False

    def __init__(
        self,
        request_id_to_symbol: dict[int, common.objects.Stock],
        ibapi_requests: dict[int,common.objects.IbAPIRequest],
        logger: logging.Logger,
        monitored_symbols: list[str],
        potential_symbols_file_path: str = None,
    ):
        self.ibapi_requests = ibapi_requests
        self.request_id_to_symbol = request_id_to_symbol
        self.logger = logger
        self.potential_symbols_file_path = potential_symbols_file_path
        self.monitored_symbols = monitored_symbols
        self.today_monitored_symbols: list[str] = []

    def insert_one_minute_bars_into_confirmation_queues(
        self,
        one_minute_stock: common.objects.Stock,
        enriched_bar: common.objects.BarData,
    ):
        specific_bar_time = one_minute_stock.specific_bar_time

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

        day_timeframe_stock = self.request_id_to_symbol[one_minute_stock.day_request_id]

        if specific_bar_time is not None and day_timeframe_stock.specific_bar_time != specific_bar_time:
            return

        if (
            True
            and enriched_bar.bar_time >= datetime.datetime(
                year=previous_session_date.year,
                month=previous_session_date.month,
                day=previous_session_date.day,
                hour=16,
                minute=0,
            )
            and enriched_bar.bar_time < datetime.datetime(
                year=current_session_date.year,
                month=current_session_date.month,
                day=current_session_date.day,
                hour=9,
                minute=30,
            )
        ):
            day_timeframe_stock.post_pre_market_volume_sum += enriched_bar.volume
            day_timeframe_stock.last_post_pre_one_minute_highest_high = max(
                day_timeframe_stock.last_post_pre_one_minute_highest_high,
                enriched_bar.high,
            )

        if enriched_bar.bar_time >= datetime.datetime(
            year=current_session_date.year,
            month=current_session_date.month,
            day=current_session_date.day,
            hour=9,
            minute=30,
        ):
            day_timeframe_stock.one_minute_bars_queue.put(enriched_bar)

    def on_historical_data(
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

        current_bar = common.objects.BarData(
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

        stock = self.request_id_to_symbol[request_id]
        if (
            current_bar.symbol not in self.today_monitored_symbols
            and stock.finished_collection
            and stock.is_day_timeframe()
        ):
            self.insert_symbol_to_future_list(
                symbol=current_bar.symbol,
            )

        self.update_current_symbol_data_state(
            request_id=request_id,
            current_bar=current_bar,
        )

    def update_current_symbol_data_state(
        self,
        request_id: int,
        current_bar: common.objects.BarData,
    ) -> None:
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

        stock.arrange_data_for_analysis()

        relevant_symbol_bars = stock.bars

        ibapi_request = self.ibapi_requests.get(request_id, None)
        if ibapi_request is None:
            return

        if (
            len(relevant_symbol_bars) > 0
            and relevant_symbol_bars[0].bar_time == current_bar.bar_time
        ):
            relevant_symbol_bars[0].close = current_bar.close
            relevant_symbol_bars[0].open_value = current_bar.open_value
            relevant_symbol_bars[0].high = current_bar.high
            relevant_symbol_bars[0].low = current_bar.low
            relevant_symbol_bars[0].volume = float(current_bar.volume)
            enriched_bar = stock.enrich_bar(
                current_bar=relevant_symbol_bars[0],
            )

            if ibapi_request.is_one_minute_timeframe() and enriched_bar:
                relevant_symbol_bars[0].ready_to_analyze = True
                self.insert_one_minute_bars_into_confirmation_queues(
                    one_minute_stock=stock,
                    enriched_bar=relevant_symbol_bars[0],
                )
                return
        else:
            enriched_bar = stock.enrich_bar(
                current_bar=current_bar,
            )
            if enriched_bar:
                enriched_bar.ready_to_analyze = True
                stock.bars.append(enriched_bar)
                stock.arrange_data_for_analysis()

        if stock.is_one_minute_timeframe() and enriched_bar is not None:
            self.insert_one_minute_bars_into_confirmation_queues(
                one_minute_stock=stock,
                enriched_bar=enriched_bar,
            )
            return

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
