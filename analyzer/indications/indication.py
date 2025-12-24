from analyzer.analyzers.analyzer import Analyzer
from analyzer.analyzers import objects as analyzer_objects
from tws import objects as tws_objects

from . import objects

class Indication:
    analyzers: list[Analyzer] = []
    name: str = ""

    def handle_response(
        self,
        success_results: list[analyzer_objects.AnalyzerResponse],
        failure_results: list[analyzer_objects.AnalyzerResponse],
    ) -> objects.IndicationResponse:
        total = len(self.analyzers)
        success_rate = len(success_results)/total
        result = total == len(success_results) or success_rate >= 0.9

        if success_rate >= 0.9 and len(failure_results) > 0:
            for failure_result in failure_results:
                print(f"""
                    success_rate: {success_rate}%.\n
                    failed on {failure_result.reason}\n
                """)

        return objects.IndicationResponse(
            success_rate=success_rate,
            result=result,
        )

    def indicate(
        self,
        stock: tws_objects.Stock,
        milestones: analyzer_objects.Milestones,
    ) -> objects.IndicationResponse:
        failure_results: list[analyzer_objects.AnalyzerResponse] = []
        success_results: list[analyzer_objects.AnalyzerResponse] = []
        for analyzer_obj in self.analyzers:
            analyzer_obj = analyzer_obj()
            result = analyzer_obj.analyze(
                stock=stock,
                milestones=milestones,
            )

            if result.result:
                success_results.append(result)
            else:
                failure_results.append(result)

        return self.handle_response(
            success_results=success_results,
            failure_results=failure_results,
        )
