from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_close_similar_to_high"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        current_close_similar_to_high = current_bar.close/current_bar.high >= 0.7

        return objects.EvidenceResponse(
            result=current_close_similar_to_high,
            reason=""
            if current_close_similar_to_high
            else f"current close: {current_bar.close} is far from high: {current_bar.high}",
        )
