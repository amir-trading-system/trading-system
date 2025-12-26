from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_close_above_top_high_if_crossed_it"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        current_bar_close_above_top_high_if_crossed_it = True
        if (
            True
            and current_bar.high > milestones.top_bar.bar_object.high
            and current_bar.close < milestones.top_bar.bar_object.high
            and current_bar.close/milestones.top_bar.bar_object.high < 0.95
        ):
            current_bar_close_above_top_high_if_crossed_it = False

        return objects.EvidenceResponse(
            result=current_bar_close_above_top_high_if_crossed_it,
            reason=""
            if current_bar_close_above_top_high_if_crossed_it
            else "Current bar close didnt crossed top high but high crossed top high",
        )
