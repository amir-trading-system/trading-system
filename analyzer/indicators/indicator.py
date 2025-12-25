from colorama import Fore, Style

import analyzer.evidences
import analyzer.objects

from tws import objects as tws_objects

from . import objects

class Indicator:
    evidences: set[analyzer.evidences._evidence.Evidence] = {
        analyzer.evidences.movement_is_after_market_starts.Evidence,
        analyzer.evidences.current_close_similar_to_high.Evidence,
    }
    name: str = ""

    def handle_response(
        self,
        success_results: list[analyzer.objects.EvidenceResponse],
        failure_results: list[analyzer.objects.EvidenceResponse],
    ) -> objects.IndicatorResponse:
        total = len(self.evidences)
        success_rate = len(success_results)/total
        result = total == len(success_results) or success_rate >= 0.9

        if success_rate >= 0.9 and len(failure_results) > 0:
            for failure_result in failure_results:
                print(f"""
                    success_rate: {success_rate}%.\n
                    failed on {failure_result.reason}\n
                """)

        return objects.IndicatorResponse(
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

        for evidence_object in self.evidences:
            evidence_object: analyzer.evidences._evidence.Evidence = evidence_object()
            result = evidence_object.find_evidence(
                stock=stock,
                milestones=milestones,
                current_bar=current_bar,
            )

            if result.result:
                print(f"{self.name}: Evidence {Fore.GREEN}{evidence_object.name}{Style.RESET_ALL} is positive")
                success_results.append(result)
            else:
                print(f"{self.name}: Evidence {Fore.RED}{evidence_object.name}{Style.RESET_ALL} is negative")
                failure_results.append(result)

        return self.handle_response(
            success_results=success_results,
            failure_results=failure_results,
        )
