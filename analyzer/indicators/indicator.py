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
        self.evidence: type[analyzer.evidences.evidence.Evidence]
        self.can_be_confirm_by_itself = False
        self.milestones = milestones

    def indicate(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> bool:
        evidence_object: analyzer.evidences.evidence.Evidence = self.evidence(
            logger=self.logger,
        )
        if not evidence_object.pre_process(
            stock=stock,
            current_bar=current_bar,
        ):
            return False

        result = evidence_object.find_evidence(
            stock=stock,
            milestones=milestones,
            current_bar=current_bar,
            is_retro=is_retro,
        )

        return result
