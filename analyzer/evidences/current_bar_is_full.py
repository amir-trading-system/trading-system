import common
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_is_full"
    is_base_evidence = True

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        current_bar_is_full = (
            True
            and current_bar.high - current_bar.low > 0
            and (current_bar.close - current_bar.open_value)/(current_bar.high - current_bar.low) >= 0.4
        )

        return common.objects.EvidenceResponse(
            result=current_bar_is_full,
            reason=""
            if current_bar_is_full
            else "Current bar is not strong and full",
        )
