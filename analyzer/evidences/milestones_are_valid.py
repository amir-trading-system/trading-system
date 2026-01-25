import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "milestones_are_valid"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        milestones_are_valid = (
            True
            and milestones.starting_bar.index != milestones.top_bar.index
            and milestones.starting_bar.index > current_bar.index
            and milestones.top_bar.index > current_bar.index
            and milestones.starting_bar.index > 0
            and milestones.top_bar.index > 0
        )

        starting_index = milestones.starting_bar.index
        top_index = milestones.top_bar.index

        return common.objects.EvidenceResponse(
            result=milestones_are_valid,
            reason=""
            if milestones_are_valid
            else f"Milestones are not valid. starting_index: {starting_index}. top_index: {top_index}",
        )
