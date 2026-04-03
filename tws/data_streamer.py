import datetime
import logging
import pickle

from ibapi import common as ibapi_common

import common
import model


class DataStreamer():
    on_specific_bar_time: bool = False

    def __init__(
        self,
        request_id_to_symbol: dict[int, common.objects.Stock],
        ibapi_requests: dict[int,common.objects.IbAPIRequest],
        logger: logging.Logger,
        get_only_statistics: bool,
    ):
        self.ibapi_requests = ibapi_requests
        self.request_id_to_symbol = request_id_to_symbol
        self.logger = logger
        self.get_only_statistics = get_only_statistics

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
                hour=4,
            ):
                if (
                    day_timeframe_stock.pre_market_one_minute_highest_high_bar is None
                    or (
                        day_timeframe_stock.pre_market_one_minute_highest_high_bar is not None
                        and day_timeframe_stock.pre_market_one_minute_highest_high_bar.high < enriched_bar.high
                    )
                ):
                    day_timeframe_stock.pre_market_one_minute_highest_high_bar = enriched_bar

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

        self.update_current_symbol_data_state(
            request_id=request_id,
            current_bar=current_bar,
        )

        if ibapi_request.is_one_minute_timeframe():
            self.save_data_for_model_training(
                request_id=request_id,
                current_bar=current_bar,
            )

    def update_current_symbol_data_state(
        self,
        request_id: int,
        current_bar: common.objects.BarData,
    ) -> None:
        stock = self.request_id_to_symbol[request_id]
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

    def save_data_for_model_training(
        self,
        request_id: int,
        current_bar: common.objects.BarData,
    ):
        current_bar_09_30 = datetime.datetime(
            year=current_bar.bar_time.year,
            month=current_bar.bar_time.month,
            day=current_bar.bar_time.day,
            hour=9,
            minute=30,
        )
        one_minute_timeframe_stock = self.request_id_to_symbol[request_id]
        day_timeframe_stock = self.request_id_to_symbol[one_minute_timeframe_stock.day_request_id]

        if (
            True
            and self.get_only_statistics
            and current_bar.bar_time == day_timeframe_stock.expected_bar_time
        ):
            one_minute_bars: list[common.objects.BarData] = []
            highest_high_one_minute_bar: common.objects.BarData = None
            for bar_object in one_minute_timeframe_stock.bars:
                if bar_object.bar_time >= datetime.datetime(
                    year=current_bar.bar_time.year,
                    month=current_bar.bar_time.month,
                    day=current_bar.bar_time.day,
                    hour=4,
                ) and bar_object.bar_time < current_bar.bar_time:
                    if highest_high_one_minute_bar is None:
                        highest_high_one_minute_bar = bar_object
                    elif bar_object.high > highest_high_one_minute_bar.high:
                        highest_high_one_minute_bar = bar_object

                if bar_object.bar_time >= current_bar_09_30:
                    one_minute_bars.append(bar_object)

            volume_sum_since_market_open = sum(
                bar_object.volume
                for bar_object in one_minute_timeframe_stock.bars
                if current_bar_09_30 <= bar_object.bar_time <= current_bar.bar_time
            )

            current_bar.price_movement_statistics = model.data_extractor.DataExtractor.extract_features_from_symbol_data(
                day_timeframe_stock=day_timeframe_stock,
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                potential_confirmation_bar=current_bar,
                highest_high_one_minute_bar=highest_high_one_minute_bar,
                volume_sum_since_market_open=volume_sum_since_market_open,
                one_minute_bars=one_minute_bars,
            )
            with open(f"model/training/data/{day_timeframe_stock.symbol_name}-{day_timeframe_stock.expected_bar_time}.json", "wb") as f:
                pickle.dump(
                    {
                        "day_timeframe_stock": day_timeframe_stock,
                        "one_minute_timeframe_stock": one_minute_timeframe_stock,
                        "potential_confirmation_bar": current_bar,
                        "highest_high_one_minute_bar": highest_high_one_minute_bar,
                        "volume_sum_since_market_open": volume_sum_since_market_open,
                        "one_minute_bars": one_minute_bars,
                    },
                    f,
                )
