import common
from . import _evidence
from . import histogram_changed_direction


class Evidence(
    _evidence.Evidence,
):
    name = "histogram_did_not_changed_direction"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        evidence_object = histogram_changed_direction.Evidence()
        evidence_result = evidence_object.find_evidence(
            stock=stock,
            milestones=milestones,
            current_bar=current_bar,
            is_retro=is_retro,
        )

        return common.objects.EvidenceResponse(
            result=not evidence_result.result,
            reason=""
            if evidence_result.result
            else "histogram changed direction while it should not",
        )
