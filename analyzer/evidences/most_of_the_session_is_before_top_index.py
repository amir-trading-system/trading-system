import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "most_of_the_session_is_before_top_index"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        most_of_the_session_is_before_top_index = milestones.top_bar.index/milestones.starting_bar.index <= 0.7

        return common.objects.EvidenceResponse(
            result=most_of_the_session_is_before_top_index,
            reason=""
            if most_of_the_session_is_before_top_index
            else "Most of session is after top index",
        )
