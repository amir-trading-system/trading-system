import common
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_is_positive_and_volatile"
    is_base_evidence = True

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        current_bar_is_positive_and_volatile = (
            True
            and current_bar.volume > 100000
            and current_bar.close > current_bar.open_value
        )

        return common.objects.EvidenceResponse(
            result=current_bar_is_positive_and_volatile,
            reason=""
            if current_bar_is_positive_and_volatile
            else "Current bar is not volatile enough or nor positive",
        )
