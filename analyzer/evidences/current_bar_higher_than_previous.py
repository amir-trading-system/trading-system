from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_higher_than_previous"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        previous_bar = milestones.previous_bar.bar_object
        current_bar_higher_than_previous = current_bar.high > previous_bar.high

        return objects.EvidenceResponse(
            result=current_bar_higher_than_previous,
            reason=""
            if current_bar_higher_than_previous
            else "Current bar lower than previous",
        )
