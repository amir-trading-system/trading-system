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
        self.evidence: type[analyzer.evidences._evidence.Evidence]
        self.must_to_have: list[bool] = []
        self.can_be_confirm_by_itself = False
        self.milestones = milestones

    def handle_response(
        self,
        success_results: list[common.objects.EvidenceResponse],
        failed_base_evidences_count: int,
    ) -> common.objects.IndicatorResponse:
        success_rate = len(success_results)/1
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

        evidence_object: analyzer.evidences._evidence.Evidence = self.evidence()
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
            return common.objects.IndicatorResponse(
                success_count=0,
                success_rate=0.0,
                result=False,
                failed_base_evidences_count=0,
            )

        if result.result:
            if not evidence_object.is_base_evidence or self.name == "already_has_indication":
                success_results.append(result)

        return self.handle_response(
            success_results=success_results,
            failed_base_evidences_count=failed_base_evidences_count,
        )
