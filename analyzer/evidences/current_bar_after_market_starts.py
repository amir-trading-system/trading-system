import common
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_after_market_starts"
    must_to_be_true = True
    is_base_evidence = True

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        current_bar_after_market_starts = current_bar.is_after_market_open

        return common.objects.EvidenceResponse(
            result=current_bar_after_market_starts,
            reason=""
            if current_bar_after_market_starts
            else "Current bar is before market starts",
        )
