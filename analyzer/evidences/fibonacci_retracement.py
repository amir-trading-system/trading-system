from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "fibonacci_retracement"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        top_high = milestones.top_bar.bar_object.high
        lowest_low_after = milestones.lowest_low_bar.bar_object.low
        starting_open = milestones.starting_bar.bar_object.open_value

        retracement = 0
        if top_high - starting_open > 0:
            retracement = (top_high - lowest_low_after)/(top_high - starting_open)

        move_is_still_strong_due_to_fibonacci_retracement = 0.27 <= retracement <= 0.62

        if (
            True
            and not move_is_still_strong_due_to_fibonacci_retracement
            and milestones.top_bar.index - 1 > 0
        ):
            move_is_still_strong_due_to_fibonacci_retracement = (
                True
                and current_bar.close > stock.bars[milestones.top_bar.index-1].high
                and 0.22 <= retracement <= 0.8
            )

        return objects.EvidenceResponse(
            result=move_is_still_strong_due_to_fibonacci_retracement,
            reason=""
            if move_is_still_strong_due_to_fibonacci_retracement
            else f"Retracement is: {retracement}, too high and risky",
            value=retracement,
        )
