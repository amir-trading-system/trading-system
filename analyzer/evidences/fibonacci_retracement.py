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

        retracement = (top_high - lowest_low_after)/(top_high - starting_open)

        move_is_still_strong_due_to_fibonacci_retracement = 0.27 <= retracement <= 0.62

        return objects.EvidenceResponse(
            result=move_is_still_strong_due_to_fibonacci_retracement,
            reason=""
            if move_is_still_strong_due_to_fibonacci_retracement
            else f"retracement is: {retracement}, too high and risky",
        )
