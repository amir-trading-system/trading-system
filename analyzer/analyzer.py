import datetime
import queue

import copy
import logging


import alerter
import analyzer.indicators
import analyzer.evidences
import common
from tws import client

from . import helper


class Analyzer:
    def __init__(
        self,
        bars_ready_to_analyze_queue: queue.Queue[common.objects.Stock],
        waiting_for_confirmation_queue: queue.Queue[common.objects.BarData],
        alerter_object: alerter.alerter.Alerter,
        tws_client: client.Client,
        logger: logging.Logger,
    ):
        self.bars_ready_to_analyze_queue = bars_ready_to_analyze_queue
        self.waiting_for_confirmation_queue = waiting_for_confirmation_queue
        self.helper = helper.AnalyzerHelper(
            logger=logger,
        )
        self.tws_client = tws_client
        self.logger = logger
        self.alerter_object = alerter_object
        self.has_indications_bars: dict[str, common.objects.BarData] = {}

    def _prepare_milestones(
        self,
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
    ) -> common.objects.Milestones:
        are_valid = False
        starting_bar: common.objects.MilestoneBar = self.helper.get_strating_bar(
            stock=stock,
            current_bar=current_bar,
        )

        top_bar: common.objects.MilestoneBar = self.helper.get_top_bar(
            stock=stock,
            starting_bar=starting_bar,
        )

        if top_bar.index > 0:
            already_passed_top_bar = [
                bar_object.index
                for bar_object in stock.bars[current_bar.index+2:top_bar.index-1]
                if bar_object.high > top_bar.bar_object.high
                and bar_object.index < top_bar.index
                and bar_object.volume > top_bar.bar_object.volume
            ]
            if len(already_passed_top_bar) > 0:
                top_bar = common.objects.MilestoneBar(
                    index=0,
                    bar_type=common.objects.MilestoneType.TOP_BAR,
                    timeframe=stock.timeframe,
                )

        lowest_low_bar: common.objects.MilestoneBar = self.helper.get_lowest_bar_from_top_bar(
            stock=stock,
            top_bar=top_bar,
        )
        previous_bar = stock.previous_bar(
            bar_object=current_bar,
        )
        if not previous_bar:
            return common.objects.Milestones(
                starting_bar=starting_bar,
                top_bar=top_bar,
                lowest_low_bar=lowest_low_bar,
                previous_bar=previous_bar,
                are_valid=are_valid,
            )

        previous_bar = common.objects.MilestoneBar(
            index=previous_bar.index,
            bar_object=previous_bar,
            bar_type=common.objects.MilestoneType.PREVIOUS_BAR,
            bar_time=previous_bar.bar_time,
            timeframe=stock.timeframe,
        )

        if (
            True
            and starting_bar.index > 0
            and top_bar.index > 0
            and lowest_low_bar.index > 0
        ):
            are_valid = True

        milestones = common.objects.Milestones(
            starting_bar=starting_bar,
            top_bar=top_bar,
            lowest_low_bar=lowest_low_bar,
            previous_bar=previous_bar,
            are_valid=are_valid,
        )
        if not milestones.are_valid:
            return milestones

        fibonacci_retracement_evidence_object = analyzer.evidences.fibonacci_retracement.Evidence()
        retracements_evidence_object = analyzer.evidences.no_more_than_2_retracements_until_now.Evidence()
        fibonacci_retracement_result = fibonacci_retracement_evidence_object.find_evidence(
            stock=stock,
            current_bar=current_bar,
            milestones=milestones,
        )
        retracements_result = retracements_evidence_object.find_evidence(
            stock=stock,
            current_bar=current_bar,
            milestones=milestones,
        )
        milestones.fibonacci_retracement = float(fibonacci_retracement_result.value)
        milestones.retracement_indexes = retracements_result.value

        return milestones

    def _run_one_day_indicators(
        self,
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        is_retro: bool,
    ):
        for indicator in analyzer.indicators.__one_day_indicators__:
            indicator_obj: analyzer.indicators.indicator.Indicator = indicator(
                milestones=milestones,
                logger=self.logger,
            )
            indicator_response: common.objects.IndicatorResponse = indicator_obj.indicate(
                stock=stock,
                milestones=milestones,
                current_bar=current_bar,
            )
            if indicator_response.result and indicator_response.success_rate == 1:
                self.logger.info(
                    msg="Bar has Indication",
                    extra={
                        "worker": "Analyzer",
                        "symbol": stock.symbol_name,
                        "timeframe": stock.timeframe,
                        "timeframe_type": stock.timeframe_type.value,
                        "bar_time": current_bar.bar_time,
                        "current_index": current_bar.index,
                    }
                )

                self.alerter_object.send_alert(
                    sender="Analyzer",
                    stock=stock,
                    current_bar=current_bar,
                    emoji="✅",
                    milestones=milestones,
                    is_retro=is_retro,
                )
                bar_unique_identifier = current_bar.generate_unique_identifier()
                self.has_indications_bars[bar_unique_identifier] = current_bar
                stock.bars[current_bar.index].has_indication = True
                ## TODO: implelemnt confirmation logic by confirmator
                return

    def _run_indicators(
        self,
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
        is_retro: bool,
        milestones: common.objects.Milestones = None,
    ) -> None:
        self.logger.info(
            msg="Running analyzers",
            extra={
                "worker": "Analyzer",
                "symbol": stock.symbol_name,
                "timeframe": stock.timeframe,
                "timeframe_type": stock.timeframe_type.value,
                "bar_time": current_bar.bar_time,
                "current_index": current_bar.index,
                "starting_index": milestones.starting_bar.index,
                "starting_index_time": milestones.starting_bar.bar_time,
                "top_index": milestones.top_bar.index,
                "top_index_time": milestones.top_bar.bar_time,
                "lowest_low_index": milestones.lowest_low_bar.index,
                "lowest_low_time": milestones.lowest_low_bar.bar_time,
            },
        )
        success_indicators: dict[str,float] = {}
        stock.bars = stock.bars[:milestones.starting_bar.index+10]
        emoji = ""
        base_except_one = False

        for indicator in analyzer.indicators.__indicators__:
            indicator_obj: analyzer.indicators.indicator.Indicator = indicator(
                milestones=milestones,
                logger=self.logger,
            )
            indicator_response: common.objects.IndicatorResponse = indicator_obj.indicate(
                stock=stock,
                milestones=milestones,
                current_bar=current_bar,
            )
            if indicator_response.failed_base_evidences_count > 1:
                continue
            if indicator_response.result:
                success_indicators[indicator_obj.name] = round(indicator_response.success_rate, 3)
                if indicator_obj.can_be_confirm_by_itself:
                    self.waiting_for_confirmation_queue.put(current_bar)

                if indicator_response.failed_base_evidences_count == 1:
                    base_except_one = True

        self.logger.info(
            msg="Finished Running analyzers",
            extra={
                "worker": "Analyzer",
                "symbol": stock.symbol_name,
                "timeframe": stock.timeframe,
                "timeframe_type": stock.timeframe_type.value,
                "bar_time": current_bar.bar_time,
                "current_index": current_bar.index,
                "current_volume": current_bar.volume,
                "starting_index": milestones.starting_bar.index,
                "starting_index_time": milestones.starting_bar.bar_time,
                "top_index": milestones.top_bar.index,
                "top_index_time": milestones.top_bar.bar_time,
                "lowest_low_index": milestones.lowest_low_bar.index,
                "lowest_low_time": milestones.lowest_low_bar.bar_time,
                "success_indicators_count": len(success_indicators),
                "success_indicators": success_indicators,
            },
        )

        if len(success_indicators) > 0:
            sorted_indicators = dict(
                sorted(
                    success_indicators.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            )

            at_least_one_indication_result_is_certain = len(
                [
                    result
                    for result in sorted_indicators.values()
                    if result == 1.0
                ]
            ) >= 1
            certain_result = len(sorted_indicators) >= 2 or at_least_one_indication_result_is_certain

            if certain_result:
                if at_least_one_indication_result_is_certain:
                    emoji = "✅"
                else:
                    emoji = "👀"

                self.logger.info(
                    msg="Bar has Indication",
                    extra={
                        "worker": "Analyzer",
                        "symbol": stock.symbol_name,
                        "timeframe": stock.timeframe,
                        "timeframe_type": stock.timeframe_type.value,
                        "bar_time": current_bar.bar_time,
                        "current_index": current_bar.index,
                        "starting_index": milestones.starting_bar.index,
                        "starting_index_time": milestones.starting_bar.bar_time,
                        "top_index": milestones.top_bar.index,
                        "top_index_time": milestones.top_bar.bar_time,
                        "lowest_low_index": milestones.lowest_low_bar.index,
                        "lowest_low_time": milestones.lowest_low_bar.bar_time,
                    }
                )

                self.alerter_object.send_alert(
                    sender="Analyzer",
                    stock=stock,
                    current_bar=current_bar,
                    emoji=emoji,
                    base_except_one=base_except_one,
                    milestones=milestones,
                    sorted_indicators=sorted_indicators,
                    is_retro=is_retro,
                )
                bar_unique_identifier = current_bar.generate_unique_identifier()
                self.has_indications_bars[bar_unique_identifier] = current_bar
                stock.bars[current_bar.index].has_indication = True
                self.waiting_for_confirmation_queue.put(current_bar)

    def _analyze_day_bar(
        self,
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ):
        current_bar_is_valid = (
            True
            and current_bar.close > current_bar.open_value
            and current_bar.close > current_bar.ema_9
            and current_bar.close > current_bar.ema_20
            and current_bar.histogram > 0
        )
        if not current_bar_is_valid and stock.timeframe_type == 2:
            self.logger.info(
                msg="Bar is not valid, analyzer will wait for the next bar",
                extra={
                    "worker": "Analyzer",
                    "symbol": stock.symbol_name,
                    "timeframe": stock.timeframe,
                    "timeframe_type": stock.timeframe_type.value,
                    "bar_time": current_bar.bar_time,
                    "current_index": current_bar.index,
                }
            )
            return

        milestones = common.objects.Milestones(
            starting_bar=common.objects.MilestoneBar(
                index=0,
                bar_object=current_bar,
                bar_type=common.objects.MilestoneType.STARTING_BAR,
                bar_time=current_bar.bar_time,
            ),
            top_bar=common.objects.MilestoneBar(
                index=0,
                bar_object=current_bar,
                bar_type=common.objects.MilestoneType.TOP_BAR,
                bar_time=current_bar.bar_time,
            ),
            lowest_low_bar=common.objects.MilestoneBar(
                index=0,
                bar_object=current_bar,
                bar_type=common.objects.MilestoneType.LOWEST_BAR,
                bar_time=current_bar.bar_time,
            ),
            are_valid=True,
        )

        self._run_one_day_indicators(
            stock=stock,
            current_bar=current_bar,
            milestones=milestones,
            is_retro=is_retro,
        )

    def _analyze_bar(
        self,
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ):
        current_bar_is_valid = (
            True
            and current_bar.high - current_bar.low > 0.2
            and current_bar.close > current_bar.open_value
            and current_bar.high > current_bar.ema_9
            and current_bar.high > current_bar.vwap
        )
        if not current_bar_is_valid:
            self.logger.info(
                msg="Bar is not valid, analyzer will wait for the next bar",
                extra={
                    "worker": "Analyzer",
                    "symbol": stock.symbol_name,
                    "timeframe": stock.timeframe,
                    "timeframe_type": stock.timeframe_type.value,
                    "bar_time": current_bar.bar_time,
                    "current_index": current_bar.index,
                }
            )
            return

        milestones: common.objects.Milestones = self._prepare_milestones(
            stock=stock,
            current_bar=current_bar,
        )

        if not milestones.are_valid:
            self.logger.info(
                msg="One of the Milestones are not valid",
                extra={
                    "worker": "Analyzer",
                    "symbol": stock.symbol_name,
                    "timeframe": stock.timeframe,
                    "timeframe_type": stock.timeframe_type.value,
                    "bar_time": current_bar.bar_time,
                    "current_index": current_bar.index,
                    "starting_index": milestones.starting_bar.index,
                    "starting_index_time": milestones.starting_bar.bar_time,
                    "top_index": milestones.top_bar.index,
                    "top_index_time": milestones.top_bar.bar_time,
                    "lowest_low_index": milestones.lowest_low_bar.index,
                    "lowest_low_time": milestones.lowest_low_bar.bar_time,
                },
            )
            return

        self._run_indicators(
            stock=stock,
            current_bar=current_bar,
            milestones=milestones,
            is_retro=is_retro,
        )

    def analyze_retroactive_case(
        self,
        stock: common.objects.Stock,
        retroactive_from: datetime.datetime,
    ):
        all_bars = copy.deepcopy(stock.bars)
        for bar_object in stock.bars:
            if bar_object.bar_time.day != retroactive_from.day or not bar_object.ready_to_analyze:
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
                symbol_name=stock.symbol_name,
                bars=relevant_bars,
                timeframe=stock.timeframe,
                timeframe_type=stock.timeframe_type,
            )

            if new_stock_object.is_day_timeframe():
                self._analyze_day_bar(
                    stock=new_stock_object,
                    current_bar=current_bar,
                    is_retro=True,
                )
            else:
                self._analyze_bar(
                    stock=new_stock_object,
                    current_bar=current_bar,
                    is_retro=True,
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

        bar_unique_identifer = current_bar.generate_unique_identifier()
        if bar_unique_identifer in self.has_indications_bars:
            return

        if stock.is_day_timeframe():
            self._analyze_day_bar(
                stock=stock,
                current_bar=current_bar,
                is_retro=for_specific_date,
            )
        else:
            self._analyze_bar(
                stock=stock,
                current_bar=current_bar,
                is_retro=for_specific_date,
            )

    def analyze_data(
        self,
        specific_bar_time: datetime.datetime = None,
        retroactive_from: datetime.datetime = None,
    ):
        while True:
            if not self.bars_ready_to_analyze_queue.empty():
                stock_object: common.objects.Stock = self.bars_ready_to_analyze_queue.get()
                stock = common.objects.Stock(
                    symbol_name=stock_object.symbol_name,
                    timeframe=stock_object.timeframe,
                    timeframe_type=stock_object.timeframe_type,
                    bars=copy.deepcopy(stock_object.bars),
                    one_minute_bars_queue=stock_object.one_minute_bars_queue,
                )

                stock.bars = sorted(
                    stock.bars,
                    key=lambda bar: bar.bar_time,
                    reverse=True,
                )

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
                                "exception_message": str(e),
                                "symbol": stock.symbol_name,
                                "timeframe": stock.timeframe,
                                "timeframe_type": stock.timeframe_type.value,
                                "retroactive_from": retroactive_from,
                            }
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
                                "exception_message": str(e),
                                "symbol": stock.symbol_name,
                                "timeframe": stock.timeframe,
                                "timeframe_type": stock.timeframe_type.value,
                                "specific_bar_time": specific_bar_time,
                            }
                        )
