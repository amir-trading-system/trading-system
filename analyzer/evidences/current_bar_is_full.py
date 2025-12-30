from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_is_full"
    is_base_evidence = True

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        current_bar_is_full = (
            True
            and current_bar.high - current_bar.low > 0
            and (current_bar.close - current_bar.open_value)/(current_bar.high - current_bar.low) >= 0.4
        )

        return objects.EvidenceResponse(
            result=current_bar_is_full,
            reason=""
            if current_bar_is_full
            else "Current bar is not strong and full",
        )
