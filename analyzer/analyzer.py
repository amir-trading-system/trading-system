import datetime
import pickle
import time
import queue

import copy
import logging
import threading


import alerter
from tws import client
import common
import model

from . import days_analyzer


class Analyzer:
    def __init__(
        self,
        bars_ready_to_analyze_queue: queue.Queue[common.objects.Stock],
        waiting_for_confirmation_queue: queue.Queue[common.objects.BarData],
        request_id_to_symbol: dict[int,common.objects.Stock],
        logger: logging.Logger,
        tws_client: client.Client,
        alerter_object: alerter.alerter.Alerter = None,
        get_only_statistics: bool = False,
    ):
        self.bars_ready_to_analyze_queue = bars_ready_to_analyze_queue
        self.logger = logger
        self.request_id_to_symbol = request_id_to_symbol
        self.get_only_statistics = get_only_statistics

        self.days_analyzer = days_analyzer.Analyzer(
            alerter_object=alerter_object,
            waiting_for_confirmation_queue=waiting_for_confirmation_queue,
            request_id_to_symbol=request_id_to_symbol,
            tws_client=tws_client,
            logger=logger,
        )

    def analyze(
        self,
        stock: common.objects.Stock,
    ):
        while not self.request_id_to_symbol[stock.one_minute_request_id].finished_collection:
            self.logger.info(
                msg="waiting for one minute request data to be sent from broker",
                extra={
                    "worker": "Analyzer",
                    "symbol": stock.symbol_name,
                    "timeframe": stock.timeframe,
                    "timeframe_type": stock.timeframe_type.value,
                    "bar_time": stock.specific_bar_time,
                    "request_id": stock.request_id,
                },
            )
            time.sleep(10)

        stock.resistance_levels = self.get_resistance_levels(
            stock=stock,
            relevant_bars=stock.bars[1:],
            current_bar=stock.bars[0],
        )
        if self.get_only_statistics:
            one_minute_timeframe_stock = self.request_id_to_symbol[stock.one_minute_request_id]
            self.save_data_for_model_training(
                request_id=stock.one_minute_request_id,
                current_bar=[
                    bar_object
                    for bar_object in one_minute_timeframe_stock.bars
                    if bar_object.bar_time == stock.expected_bar_time
                ][0],
            )
            self.request_id_to_symbol[stock.request_id].finished_analyze = True
            self.request_id_to_symbol[stock.one_minute_request_id].finished_analyze = True

            return

        current_bar = stock.bars[0]
        if not stock.bars[0].ready_to_analyze and stock.bars[1].ready_to_analyze:
            current_bar = stock.bars[1]
            stock.bars = stock.bars[1:]

        for_specific_date = stock.specific_bar_time is not None

        if for_specific_date:
            relevant_bars = [
                bar_data
                for bar_data in stock.bars
                if bar_data.bar_time == stock.specific_bar_time
            ]

            if len(relevant_bars) == 1:
                current_bar = relevant_bars[0]
                stock.bars = stock.bars[current_bar.index:]
                for i, bar_object in enumerate(stock.bars):
                    bar_object.index = i
                current_bar.index = 0
        else:
            current_bar.index = 0
            stock.bars = stock.bars[current_bar.index:]
            for i, bar_object in enumerate(stock.bars):
                bar_object.index = i

        if not current_bar.is_after_market_open:
            return

        if stock.is_day_timeframe():
            self.days_analyzer.analyze_bar(
                stock=stock,
                current_bar=current_bar,
                is_retro=for_specific_date,
            )

    def analyze_data(
        self,
        is_retro: bool = False,
    ):
        while True:
            stock_object: common.objects.Stock = self.bars_ready_to_analyze_queue.get()
            stock = common.objects.Stock(
                request_id=stock_object.request_id,
                symbol_name=stock_object.symbol_name,
                timeframe=stock_object.timeframe,
                timeframe_type=stock_object.timeframe_type,
                bars=copy.deepcopy(stock_object.bars),
                one_minute_bars_queue=stock_object.one_minute_bars_queue,
                specific_bar_time=stock_object.specific_bar_time,
                expected_bar_time=stock_object.expected_bar_time,
                last_post_pre_one_minute_highest_high=stock_object.last_post_pre_one_minute_highest_high,
                pre_market_one_minute_highest_high_bar=stock_object.pre_market_one_minute_highest_high_bar,
                post_pre_market_volume_sum=stock_object.post_pre_market_volume_sum,
                finished_collection=stock_object.finished_collection,
                finished_analyze=stock_object.finished_analyze,
                one_minute_request_id=stock_object.one_minute_request_id,
                day_request_id=stock_object.day_request_id,
                total_volume=stock_object.total_volume,
                total_price_volume=stock_object.total_price_volume,
                volume_sum_since_4_am_today=stock_object.volume_sum_since_4_am_today,
                volume_sum_since_market_open=stock_object.volume_sum_since_market_open,
                is_positive=stock_object.is_positive,
            )
            stock.arrange_data_for_analysis()

            most_recent_bar = stock.bars[0]
            today = datetime.datetime.now().day
            if (
                True
                and not is_retro
                and today != most_recent_bar.bar_time.day
            ):
                continue

            threading.Thread(
                target=self.analyze,
                kwargs={
                    "stock": stock,
                },
            ).start()

    def save_data_for_model_training(
        self,
        request_id: int,
        current_bar: common.objects.BarData,
    ):
        one_minute_timeframe_stock = self.request_id_to_symbol[request_id]
        day_timeframe_stock = self.request_id_to_symbol[one_minute_timeframe_stock.day_request_id]

        highest_high_one_minute_bar: common.objects.BarData = one_minute_timeframe_stock.get_highest_high_one_minute_bar(
            current_one_minute_bar=current_bar,
        )
        one_minute_bars: list[common.objects.BarData] = one_minute_timeframe_stock.get_one_minutes_bars_since_market_open(
            current_one_minute_bar=current_bar,
        )
        volume_sum_since_market_open = one_minute_timeframe_stock.get_volume_sum_since_market_open(
            current_one_minute_bar=current_bar,
        )

        current_bar.price_movement_statistics = model.data_extractor.DataExtractor.extract_features_from_symbol_data(
            day_timeframe_stock=day_timeframe_stock,
            one_minute_timeframe_stock=one_minute_timeframe_stock,
            potential_confirmation_bar=current_bar,
            highest_high_one_minute_bar=highest_high_one_minute_bar,
            volume_sum_since_market_open=volume_sum_since_market_open,
            one_minute_bars=one_minute_bars,
        )
        day_timeframe_stock.resistance_levels = self.get_resistance_levels(
            stock=day_timeframe_stock,
            relevant_bars=day_timeframe_stock.bars[1:],
            current_bar=day_timeframe_stock.bars[0],
        )
        with open(f"model/training/data/next_training/{day_timeframe_stock.symbol_name}-{day_timeframe_stock.expected_bar_time}.json", "wb") as f:
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

        model.graph_creator.GraphCreator.create_interactive_chart(
            symbol=day_timeframe_stock.symbol_name,
            potential_confirmation_bar=current_bar,
            one_minute_timeframe_stock=one_minute_timeframe_stock,
        )

    def get_resistance_levels(
        self,
        stock: common.objects.Stock,
        relevant_bars: list[common.objects.BarData],
        current_bar: common.objects.BarData,
    ) -> list[common.objects.BarData]:
        resistance_levels: list[common.objects.BarData] = []
        for bar_object in relevant_bars[:current_bar.index+40]:
            if (
                bar_object.vwap is None
                or bar_object.ema_9 is None
                or bar_object.ema_20 is None
            ):
                continue

            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            next_bar = stock.next_bar(
                bar_object=bar_object,
            )

            high_pattern_one = (
                True
                and bar_object.high > bar_object.close
                and bar_object.high > bar_object.open_value
                and (bar_object.high - bar_object.close)/(bar_object.high - bar_object.low) >= 0.1
                and bar_object.high > bar_object.ema_9
                and bar_object.high > bar_object.ema_20
                and bar_object.high > bar_object.vwap
                and previous_bar is not None
                and previous_bar.high < bar_object.high
            )
            high_pattern_two = (
                True
                and previous_bar is not None
                and next_bar is not None
                and previous_bar.high < bar_object.high > next_bar.high
            )

            if (
                True
                and (high_pattern_one or high_pattern_two)
            ):
                resistance_level = [
                    r_l
                    for r_l in resistance_levels
                    if bar_object.high == r_l.high
                ]
                if not resistance_level:
                    resistance_levels.append(bar_object)

        resistance_levels = sorted(
            resistance_levels,
            key=lambda r_l: r_l.high,
        )
        temp_resistance_levels = [temp_r_l for temp_r_l in resistance_levels]
        for i, resistance_level in enumerate(temp_resistance_levels):
            if i+1 > len(resistance_levels) - 1:
                continue

            if resistance_level.high/resistance_levels[i+1].high >= 0.95:
                resistance_levels = [
                    r_l
                    for r_l in resistance_levels
                    if r_l.bar_time != resistance_level.bar_time
                ]

        return resistance_levels
