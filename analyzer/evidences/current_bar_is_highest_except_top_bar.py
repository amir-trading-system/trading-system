import common
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_is_highest_except_top_bar"
    is_base_evidence = True

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.top_bar.index+1]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        current_bar_is_highest_except_top_bar = not any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.high > current_bar.high
            and bar_object.high - bar_object.low > 0
            and abs(bar_object.close - bar_object.open_value)/(bar_object.high - bar_object.low) >= 0.5
        )

        return common.objects.EvidenceResponse(
            result=current_bar_is_highest_except_top_bar,
            reason=""
            if current_bar_is_highest_except_top_bar
            else "Current bar is not the highest since top bar",
        )
