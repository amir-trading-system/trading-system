from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_after_market_starts"
    must_to_be_true = True

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        current_bar_after_market_starts = current_bar.is_after_market_open

        return objects.EvidenceResponse(
            result=current_bar_after_market_starts,
            reason=""
            if current_bar_after_market_starts
            else "Current bar is before market starts",
        )
