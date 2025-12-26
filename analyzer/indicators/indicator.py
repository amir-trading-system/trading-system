from colorama import Fore, Style

import analyzer.evidences
import analyzer.objects

from tws import objects as tws_objects

from . import objects

class Indicator:
    evidences: set[analyzer.evidences._evidence.Evidence] = {
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
    }
    name: str = ""

    def handle_response(
        self,
        symbol_name: str,
        success_results: list[analyzer.objects.EvidenceResponse],
        failure_results: list[analyzer.objects.EvidenceResponse],
        printed_results: list[str]
    ) -> objects.IndicatorResponse:
        total = len(self.evidences)
        success_rate = len(success_results)/total
        result = total == len(success_results) or success_rate >= 0.9 or total - len(success_results) == 1

        if success_rate >= 0.9:
            print(f"SYMBOL: {symbol_name}")
            print("\n".join(printed_results))
        if success_rate >= 0.9 and len(failure_results) > 0:
            for failure_result in failure_results:
                print(f"""
                    success_rate: {success_rate}%.\n
                    {failure_result.reason}\n
                """)

        return objects.IndicatorResponse(
            success_count=len(success_results),
            success_rate=success_rate,
            result=result,
        )

    def indicate(
        self,
        stock: tws_objects.Stock,
        milestones: analyzer.objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.IndicatorResponse:
        failure_results: list[analyzer.objects.EvidenceResponse] = []
        success_results: list[analyzer.objects.EvidenceResponse] = []
        printed_results: list[str] = []

        for evidence_object in self.evidences:
            evidence_object: analyzer.evidences._evidence.Evidence = evidence_object()
            result = evidence_object.find_evidence(
                stock=stock,
                milestones=milestones,
                current_bar=current_bar,
            )

            if not result.result and evidence_object.must_to_be_true:
                success_results = []
                printed_results = []
                break

            if result.result:
                success_results.append(result)
                printed_results.append(f"{self.name}: Evidence {Fore.GREEN}{evidence_object.name}{Style.RESET_ALL} is positive")
            else:
                failure_results.append(result)
                printed_results.append(f"{self.name}: Evidence {Fore.RED}{evidence_object.name}{Style.RESET_ALL} is negative")

        return self.handle_response(
            symbol_name=stock.symbol_name,
            success_results=success_results,
            failure_results=failure_results,
            printed_results=printed_results,
        )
