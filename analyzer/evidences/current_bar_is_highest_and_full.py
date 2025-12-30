from analyzer import objects
from tws import objects as tws_objects

from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_is_highest_and_full"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        relevant_bars = stock.bars[1:milestones.starting_bar.index+1]
        if len(relevant_bars) == 0:
            return objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        current_bar_is_highest = not any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.high >= current_bar.high
        )
        current_bar_is_full = (
            True
            and current_bar.high - current_bar.low > 0
            and (current_bar.close - current_bar.open_value)/(current_bar.high - current_bar.low) >= 0.7
            and current_bar.low/current_bar.open_value >= 0.95
        )

        current_bar_is_highest_and_full = (
            True
            and current_bar_is_highest
            and current_bar_is_full
        )

        return objects.EvidenceResponse(
            result=current_bar_is_highest_and_full,
            reason=""
            if current_bar_is_highest_and_full
            else "Current bar is not full or highest",
        )
