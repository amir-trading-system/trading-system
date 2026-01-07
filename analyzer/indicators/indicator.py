import logging

from colorama import Fore, Style

import analyzer.evidences
import analyzer.objects

from tws import objects as tws_objects

from . import objects

class Indicator:
    name: str = ""

    def __init__(
        self,
        milestones: analyzer.objects.Milestones,
        logger: logging.Logger,
    ):
        self.logger = logger
        self.unique_evidences: set[analyzer.evidences._evidence.Evidence] = {}
        self.evidences: set[analyzer.evidences._evidence.Evidence] = {
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
        }
        self.must_to_have: list[bool] = []
        self.check_for_retracement_before: bool = True
        self.milestones = milestones

    def handle_response(
        self,
        success_results: list[analyzer.objects.EvidenceResponse],
        printed_results: list[str],
        failed_base_evidences_count: int,
    ) -> objects.IndicatorResponse:
        total = len(self.unique_evidences)
        success_rate = len(success_results)/total
        result = success_rate >= 0.9

        if success_rate >= 0.9 and failed_base_evidences_count <= 1:
            print("\n".join(printed_results))

        return objects.IndicatorResponse(
            success_count=len(success_results),
            success_rate=success_rate,
            result=result,
            failed_base_evidences_count=failed_base_evidences_count,
        )

    def indicate(
        self,
        stock: tws_objects.Stock,
        milestones: analyzer.objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.IndicatorResponse:
        success_results: list[analyzer.objects.EvidenceResponse] = []
        printed_results: list[str] = []
        failed_base_evidences_count = 0

        if not all(
            boolean
            for boolean in self.must_to_have
            if boolean is True
        ):
            self.logger.error(
                msg="Not all must_to_have terms are true for indicator",
                extra={
                    "worker": f"{__name__}.{__class__.__name__}",
                    "indicator_name": self.name,
                    "symbol": stock.symbol_name,
                    "timeframe": stock.timeframe,
                    "bar_time": current_bar.bar_time,
                    "bar_index": current_bar.index,
                    "current_bar": current_bar,
                    "starting_index": milestones.starting_bar.index,
                    "starting_index_time": milestones.starting_bar.bar_time,
                    "top_index": milestones.top_bar.index,
                    "top_index_time": milestones.top_bar.bar_time,
                    "lowest_low_index": milestones.lowest_low_bar.index,
                    "lowest_low_time": milestones.lowest_low_bar.bar_time,
                }
            )
            print(f"Not all must_to_have terms are true for {self.name} indicator")
            return objects.IndicatorResponse(
                success_count=0,
                success_rate=0.0,
                result=False,
                failed_base_evidences_count=0,
            )

        for evidence_object in self.evidences:
            if not self.check_for_retracement_before and evidence_object.name == analyzer.evidences.retracement_occured_since_top_bar:
                continue

            evidence_object: analyzer.evidences._evidence.Evidence = evidence_object()
            result = evidence_object.find_evidence(
                stock=stock,
                milestones=milestones,
                current_bar=current_bar,
            )
            if not result.result and evidence_object.is_base_evidence:
                failed_base_evidences_count += 1

            if not result.result and evidence_object.must_to_be_true:
                success_results = []
                printed_results = []
                break

            if result.result:
                if not evidence_object.is_base_evidence or self.name == "already_has_indication":
                    success_results.append(result)
            else:
                printed_results.append(f"{stock.symbol_name}: {self.name} -  Evidence: {evidence_object.name}. Reason: {Fore.RED}{result.reason}.{Style.RESET_ALL}")

        return self.handle_response(
            success_results=success_results,
            printed_results=printed_results,
            failed_base_evidences_count=failed_base_evidences_count,
        )
