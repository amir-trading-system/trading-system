import datetime
import queue

import copy
import logging
import threading


import alerter
from tws import client
import common

from . import days_analyzer


class Analyzer:
    confirmator_only = False

    def __init__(
        self,
        bars_ready_to_analyze_queue: queue.Queue[common.objects.Stock],
        waiting_for_confirmation_queue: queue.Queue[common.objects.BarData],
        request_id_to_symbol: dict[int,common.objects.Stock],
        logger: logging.Logger,
        tws_client: client.Client,
        alerter_object: alerter.alerter.Alerter = None,
    ):
        self.bars_ready_to_analyze_queue = bars_ready_to_analyze_queue
        self.logger = logger
        self.request_id_to_symbol = request_id_to_symbol

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
                confirmator_only=self.confirmator_only,
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
                last_post_pre_one_minute_highest_high=stock_object.last_post_pre_one_minute_highest_high,
                post_pre_market_volume_sum=stock_object.post_pre_market_volume_sum,
                last_lowest_low_bar=stock_object.last_lowest_low_bar,
                finished_collection=stock_object.finished_collection,
                finished_analyze=stock_object.finished_analyze,
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
