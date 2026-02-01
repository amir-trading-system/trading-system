import logging

import analyzer.evidences
import common

class Indicator:
    name: str = ""

    def __init__(
        self,
        milestones: common.objects.Milestones,
        logger: logging.Logger,
    ):
        self.logger = logger
        self.unique_evidences: set[type[analyzer.evidences._evidence.Evidence]] = set()
        self.evidences: set[type[analyzer.evidences._evidence.Evidence]] = {
            analyzer.evidences.movement_is_after_market_starts.Evidence,
            analyzer.evidences.current_close_similar_to_high.Evidence,
            analyzer.evidences.current_high_close_to_top_bar_high.Evidence,
            analyzer.evidences.current_bar_is_highest_except_top_bar.Evidence,
            analyzer.evidences.current_bar_is_positive_and_volatile.Evidence,
            analyzer.evidences.current_bar_comes_after_healthy_retracement.Evidence,
            analyzer.evidences.most_volatile_bar_with_big_rejection_not_inside_current_bar_range.Evidence,
            analyzer.evidences.no_indecision_histogram_from_top.Evidence,
            analyzer.evidences.current_bar_higher_than_previous.Evidence,
            analyzer.evidences.current_bar_is_full.Evidence,
            analyzer.evidences.most_volatile_bar_from_top_strong.Evidence,
            analyzer.evidences.current_bar_is_not_the_volume_weakest_since_top_bar.Evidence,
            analyzer.evidences.retracement_occured_since_top_bar.Evidence,
            analyzer.evidences.current_bar_close_above_top_high_if_crossed_it.Evidence,
            analyzer.evidences.current_bar_after_market_starts.Evidence,
            analyzer.evidences.top_bar_is_not_the_lowest_bar.Evidence,
            analyzer.evidences.at_least_one_bar_was_closed_to_9_ema_since_start.Evidence,
            analyzer.evidences.most_of_move_signal_line_is_positive.Evidence,
        }
        self.must_to_have: list[bool] = []
        self.check_for_retracement_before: bool = True
        self.can_be_confirm_by_itself = False
        self.milestones = milestones

    def handle_response(
        self,
        success_results: list[common.objects.EvidenceResponse],
        failed_base_evidences_count: int,
    ) -> common.objects.IndicatorResponse:
        total = len(self.unique_evidences)
        success_rate = len(success_results)/total
        result = success_rate >= 0.9

        return common.objects.IndicatorResponse(
            success_count=len(success_results),
            success_rate=success_rate,
            result=result,
            failed_base_evidences_count=failed_base_evidences_count,
        )

    def indicate(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.IndicatorResponse:
        success_results: list[common.objects.EvidenceResponse] = []
        failed_base_evidences_count = 0

        if not all(
            boolean
            for boolean in self.must_to_have
            if boolean is True
        ):
            self.logger.error(
                msg="Not all must_to_have terms are true for indicator",
                extra={
                    "worker": "Indicator",
                    "indicator_name": self.name,
                    "symbol": stock.symbol_name,
                    "timeframe": stock.timeframe,
                    "timeframe_type": stock.timeframe_type.value,
                    "bar_time": current_bar.bar_time,
                    "bar_index": current_bar.index,
                    "current_bar": current_bar,
                    "starting_index": milestones.starting_bar.index,
                    "starting_index_time": milestones.starting_bar.bar_time,
                    "top_index": milestones.top_bar.index,
                    "top_index_time": milestones.top_bar.bar_time,
                    "lowest_low_index": milestones.lowest_low_bar.index,
                    "lowest_low_time": milestones.lowest_low_bar.bar_time,
                },
            )
            print(f"Not all must_to_have terms are true for {self.name} indicator")
            return common.objects.IndicatorResponse(
                success_count=0,
                success_rate=0.0,
                result=False,
                failed_base_evidences_count=0,
            )

        for evidence_class in self.evidences:
            if not self.check_for_retracement_before and evidence_class.name == analyzer.evidences.retracement_occured_since_top_bar:
                continue

            evidence_object: analyzer.evidences._evidence.Evidence = evidence_class()
            result = evidence_object.find_evidence(
                stock=stock,
                milestones=milestones,
                current_bar=current_bar,
                is_retro=is_retro,
            )
            if not result.result and evidence_object.is_base_evidence:
                failed_base_evidences_count += 1

            if not result.result and evidence_object.must_to_be_true:
                success_results = []
                break

            if result.result:
                if not evidence_object.is_base_evidence or self.name == "already_has_indication":
                    success_results.append(result)

        return self.handle_response(
            success_results=success_results,
            failed_base_evidences_count=failed_base_evidences_count,
        )
