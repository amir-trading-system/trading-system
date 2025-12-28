from analyzer import objects
from tws import objects as tws_objects

from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_high_is_highest"

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

        current_high_is_highest = not any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.high > current_bar.high
        )

        return objects.EvidenceResponse(
            result=current_high_is_highest,
            reason=""
            if current_high_is_highest
            else "Current bar is not the highest",
        )
