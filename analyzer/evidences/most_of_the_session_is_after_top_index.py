from analyzer import objects
from tws import objects as tws_objects

from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "most_of_the_session_is_after_top_index"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        most_of_the_session_is_after_top_index = milestones.top_bar.index/milestones.starting_bar.index > 0.7

        return objects.EvidenceResponse(
            result=most_of_the_session_is_after_top_index,
            reason=""
            if most_of_the_session_is_after_top_index
            else "Most of session is before top index",
        )
