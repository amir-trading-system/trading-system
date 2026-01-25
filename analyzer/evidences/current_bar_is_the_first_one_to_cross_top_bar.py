import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_is_the_first_one_to_cross_top_bar"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[1:milestones.top_bar.index+1]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        current_bar_is_the_first_one_to_cross_top_bar = not any(
            bar_object
            for bar_object in relevant_bars
            if (
                True
                and bar_object.high > milestones.top_bar.bar_object.high
                and bar_object.low < milestones.top_bar.bar_object.high
            )
        )

        return common.objects.EvidenceResponse(
            result=current_bar_is_the_first_one_to_cross_top_bar,
            reason=""
            if current_bar_is_the_first_one_to_cross_top_bar
            else "Current bar is not the first one to cross top bar",
        )
