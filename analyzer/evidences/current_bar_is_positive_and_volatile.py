from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_is_positive_and_volatile"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        current_bar_is_positive_and_volatile = (
            True
            and current_bar.volume > 100000
            and current_bar.close > current_bar.open_value
        )

        return objects.EvidenceResponse(
            result=current_bar_is_positive_and_volatile,
            reason=""
            if current_bar_is_positive_and_volatile
            else "Current bar is not volatile enough or nor positive",
        )
