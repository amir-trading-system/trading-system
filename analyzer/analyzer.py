import datetime
import queue

import copy
import logging


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

    def analyze_retroactive_case(
        self,
        stock: common.objects.Stock,
        retroactive_from: datetime.datetime,
    ):
        all_bars = copy.deepcopy(stock.bars)
        for bar_object in stock.bars:
            if bar_object.bar_time.date() != retroactive_from or not bar_object.ready_to_analyze:
                continue

            relevant_bars = all_bars[bar_object.index:]
            for i, bar_obj in enumerate(relevant_bars):
                bar_obj.index = i

            current_bar = [
                bar_obj
                for bar_obj in relevant_bars
                if bar_obj.bar_time == bar_object.bar_time
            ]
            if len(current_bar) == 0:
                continue

            current_bar = current_bar[0]
            new_stock_object = common.objects.Stock(
                request_id=stock.request_id,
                symbol_name=stock.symbol_name,
                bars=relevant_bars,
                timeframe=stock.timeframe,
                timeframe_type=stock.timeframe_type,
                specific_bar_time=current_bar.bar_time,
                finished_collection=stock.finished_collection,
                finished_analyze=stock.finished_analyze,
                last_post_pre_one_minute_highest_high=stock.last_post_pre_one_minute_highest_high,
                post_pre_market_volume_sum=stock.post_pre_market_volume_sum,
            )

            self.days_analyzer.analyze_day_bar(
                stock=new_stock_object,
                current_bar=current_bar,
                is_retro=True,
                confirmator_only=self.confirmator_only,
            )

    def analyze_live_case(
        self,
        stock: common.objects.Stock,
        specific_bar_time: datetime.datetime,
    ):
        current_bar = stock.bars[0]
        if not stock.bars[0].ready_to_analyze and stock.bars[1].ready_to_analyze:
            current_bar = stock.bars[1]
            stock.bars = stock.bars[1:]

        for_specific_date = specific_bar_time is not None

        if for_specific_date:
            relevant_bars = [
                bar_data
                for bar_data in stock.bars
                if bar_data.bar_time == specific_bar_time
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
            self.days_analyzer.analyze_day_bar(
                stock=stock,
                current_bar=current_bar,
                is_retro=for_specific_date,
                confirmator_only=self.confirmator_only,
            )

    def analyze_data(
        self,
        specific_bar_time: datetime.datetime = None,
        retroactive_from: datetime.datetime = None,
    ):
        while True:
            stock_object: common.objects.Stock = self.bars_ready_to_analyze_queue.get()
            most_recent_bar = stock_object.bars[-1]
            today = datetime.datetime.now().day
            if (
                True
                and not specific_bar_time
                and not retroactive_from
                and today != most_recent_bar.bar_time.day
            ):
                continue

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
                finished_collection=stock_object.finished_collection,
                finished_analyze=stock_object.finished_analyze,
            )
            stock.arrange_data_for_analysis()

            if retroactive_from:
                try:
                    self.analyze_retroactive_case(
                        stock=stock,
                        retroactive_from=retroactive_from,
                    )
                except Exception as e:
                    self.logger.error(
                        msg="Exception occured while analyzing stock retroactively",
                        extra={
                            "exception": e,
                            "symbol": stock.symbol_name,
                            "timeframe": stock.timeframe,
                            "timeframe_type": stock.timeframe_type.value,
                            "retroactive_from": retroactive_from,
                            "request_id": stock.request_id,
                        },
                    )
            else:
                try:
                    self.analyze_live_case(
                        stock=stock,
                        specific_bar_time=specific_bar_time,
                    )
                except Exception as e:
                    self.logger.error(
                        msg="Exception occured while analyzing stock on live or on specific bar time",
                        extra={
                            "exception": e,
                            "symbol": stock.symbol_name,
                            "timeframe": stock.timeframe,
                            "timeframe_type": stock.timeframe_type.value,
                            "specific_bar_time": specific_bar_time,
                            "request_id": stock.request_id,
                        },
                    )

    def analyze_data_retroactively(
        self,
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
                finished_collection=stock_object.finished_collection,
                finished_analyze=stock_object.finished_analyze,
            )
            stock.arrange_data_for_analysis()

            try:
                self.analyze_live_case(
                    stock=stock,
                    specific_bar_time=stock_object.specific_bar_time,
                )
            except Exception as e:
                self.logger.error(
                    msg="Exception occured while analyzing stock on live or on specific bar time",
                    extra={
                        "exception": e,
                        "symbol": stock.symbol_name,
                        "timeframe": stock.timeframe,
                        "timeframe_type": stock.timeframe_type.value,
                        "specific_bar_time": stock_object.specific_bar_time,
                        "request_id": stock_object.request_id,
                    },
                )
