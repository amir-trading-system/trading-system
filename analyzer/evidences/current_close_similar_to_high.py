import common
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_close_similar_to_high"
    is_base_evidence = True

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        current_close_similar_to_high = current_bar.close/current_bar.high >= 0.7

        return common.objects.EvidenceResponse(
            result=current_close_similar_to_high,
            reason=""
            if current_close_similar_to_high
            else f"Current close: {current_bar.close} is far from high: {current_bar.high}",
        )
