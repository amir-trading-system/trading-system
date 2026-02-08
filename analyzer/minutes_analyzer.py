import logging
import queue

import alerter
import analyzer.evidences
import analyzer.indicators
import common

from . import helper as analyzer_helper

class Analyzer:
    def __init__(
        self,
        helper: analyzer_helper.AnalyzerHelper,
        waiting_for_confirmation_queue: queue.Queue[common.objects.BarData],
        logger: logging.Logger,
        alerter_object: alerter.alerter.Alerter = None,
    ):
        self.helper = helper
        self.alerter_object = alerter_object
        self.logger = logger
        self.waiting_for_confirmation_queue = waiting_for_confirmation_queue

        self.has_indications_bars: dict[str, common.objects.BarData] = {}

    def _prepare_milestones(
        self,
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
        is_retro: bool,
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
            is_retro=is_retro,
        )
        retracements_result = retracements_evidence_object.find_evidence(
            stock=stock,
            current_bar=current_bar,
            milestones=milestones,
            is_retro=is_retro,
        )
        milestones.fibonacci_retracement = float(fibonacci_retracement_result.value)
        milestones.retracement_indexes = retracements_result.value

        return milestones
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
                is_retro=is_retro,
            )
            if indicator_response.failed_base_evidences_count > 1:
                continue
            if indicator_response.result:
                success_indicators[indicator_obj.name] = round(indicator_response.success_rate, 3)
                if indicator_obj.can_be_confirm_by_itself:
                    self.waiting_for_confirmation_queue.put(
                        {
                            "bar_to_confirm": current_bar,
                            "milestones": milestones,
                        },
                    )

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

                if self.alerter_object:
                    self.alerter_object.send_alert(
                        sender="Analyzer",
                        stock=stock,
                        current_bar=current_bar,
                        emoji=emoji,
                        milestones=milestones,
                        is_retro=is_retro,
                    )

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

                if self.alerter_object:
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
                self.waiting_for_confirmation_queue.put(
                    {
                        "bar_to_confirm": current_bar,
                        "milestones": milestones,
                    },
                )

    def analyze_bar(
        self,
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ):
        bar_unique_identifer = current_bar.generate_unique_identifier()
        if bar_unique_identifer in self.has_indications_bars:
            return

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
            is_retro=is_retro,
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
