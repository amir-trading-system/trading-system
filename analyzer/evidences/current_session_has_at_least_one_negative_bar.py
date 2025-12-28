from analyzer import objects
from tws import objects as tws_objects

from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_session_has_at_least_one_negative_bar"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.starting_bar.index+1]
        if len(relevant_bars) == 0:
            return objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        current_session_has_at_least_one_negative_bar = any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.close < bar_object.open_value
        )

        return objects.EvidenceResponse(
            result=current_session_has_at_least_one_negative_bar,
            reason=""
            if current_session_has_at_least_one_negative_bar
            else "No bar was negative since starting bar",
        )
