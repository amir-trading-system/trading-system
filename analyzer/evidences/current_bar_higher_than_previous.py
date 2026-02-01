import common
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_higher_than_previous"
    is_base_evidence = True

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        previous_bar = milestones.previous_bar.bar_object
        current_bar_higher_than_previous = current_bar.high > previous_bar.high

        return common.objects.EvidenceResponse(
            result=current_bar_higher_than_previous,
            reason=""
            if current_bar_higher_than_previous
            else "Current bar lower than previous",
        )
