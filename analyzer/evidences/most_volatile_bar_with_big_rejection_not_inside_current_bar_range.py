import common
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "most_volatile_bar_with_big_rejection_not_inside_current_bar_range"
    is_base_evidence = True

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

        most_volatile_bar = max(
            relevant_bars,
            key=lambda bar_object: bar_object.volume
        )

        most_volatile_bar_with_big_rejection_not_inside_current_bar_range = not (
            True
            and most_volatile_bar.index != milestones.top_bar.index
            and most_volatile_bar.volume > current_bar.volume
            and most_volatile_bar.high < current_bar.high
            and most_volatile_bar.high > current_bar.open_value
            and most_volatile_bar.high - most_volatile_bar.open_value > 0
            and (most_volatile_bar.high - most_volatile_bar.close)/(most_volatile_bar.high - most_volatile_bar.open_value) > 0.5
            and milestones.starting_bar.index - most_volatile_bar.index > most_volatile_bar.index
        )

        return common.objects.EvidenceResponse(
            result=most_volatile_bar_with_big_rejection_not_inside_current_bar_range,
            reason=""
            if most_volatile_bar_with_big_rejection_not_inside_current_bar_range
            else "Most volatile bar with big rejection inside current bar range",
        )
