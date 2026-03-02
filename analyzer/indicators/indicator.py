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
        self.can_be_confirm_by_itself = False
        self.milestones = milestones

    def handle_response(
        self,
        success_results: list[bool],
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
        success_results: list[bool] = []
        failed_base_evidences_count = 0

        evidence_object: analyzer.evidences._evidence.Evidence = self.evidence()
        if not evidence_object.pre_process(
            stock=stock,
            current_bar=current_bar,
        ):
            return common.objects.IndicatorResponse(
                success_count=0,
                success_rate=0.0,
                result=False,
                failed_base_evidences_count=0,
            )

        result = evidence_object.find_evidence(
            stock=stock,
            milestones=milestones,
            current_bar=current_bar,
            is_retro=is_retro,
        )
        if not result and evidence_object.is_base_evidence:
            failed_base_evidences_count += 1

        if not result and evidence_object.must_to_be_true:
            success_results = []
            return common.objects.IndicatorResponse(
                success_count=0,
                success_rate=0.0,
                result=False,
                failed_base_evidences_count=0,
            )

        if result:
            if not evidence_object.is_base_evidence or self.name == "already_has_indication":
                success_results.append(result)

        return self.handle_response(
            success_results=success_results,
            failed_base_evidences_count=failed_base_evidences_count,
        )
