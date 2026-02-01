import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_high_is_highest"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[1:milestones.starting_bar.index+1]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        current_high_is_highest = not any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.high > current_bar.high
        )

        return common.objects.EvidenceResponse(
            result=current_high_is_highest,
            reason=""
            if current_high_is_highest
            else "Current bar is not the highest",
        )
