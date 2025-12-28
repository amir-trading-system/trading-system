from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "movement_is_after_market_starts"
    is_base_evidence = True

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        movement_is_after_market_starts = 9 <= current_bar.bar_time.hour <= 20

        return objects.EvidenceResponse(
            result=movement_is_after_market_starts,
            reason=""
            if movement_is_after_market_starts
            else f"Current bar is outside of market hours. bar time: {current_bar.bar_time}",
        )
