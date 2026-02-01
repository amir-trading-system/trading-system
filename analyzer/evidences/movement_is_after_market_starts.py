import common
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "movement_is_after_market_starts"
    is_base_evidence = True

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        movement_is_after_market_starts = 9 <= current_bar.bar_time.hour <= 20

        return common.objects.EvidenceResponse(
            result=movement_is_after_market_starts,
            reason=""
            if movement_is_after_market_starts
            else f"Current bar is outside of market hours. bar time: {current_bar.bar_time}",
        )
