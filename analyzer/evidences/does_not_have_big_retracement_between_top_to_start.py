from analyzer import objects
from tws import objects as tws_objects

from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "does_not_have_big_retracement_between_top_to_start"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        relevant_bars = stock.bars[milestones.top_bar.index:milestones.starting_bar.index]
        if len(relevant_bars) == 0:
            return objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        does_not_have_big_retracement_between_top_to_start = not any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.low < milestones.starting_bar.bar_object.low
            or milestones.starting_bar.bar_object.low/bar_object.low >= 0.99
        )

        return objects.EvidenceResponse(
            result=does_not_have_big_retracement_between_top_to_start,
            reason=""
            if does_not_have_big_retracement_between_top_to_start
            else "Has big retracement between top to start",
        )
