from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_is_highest_except_top_bar"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        current_bar_is_highest_except_top_bar = not any(
            bar_object
            for bar_object in stock.bars[1:milestones.top_bar.index-1]
            if bar_object.high > current_bar.high
        )

        return objects.EvidenceResponse(
            result=current_bar_is_highest_except_top_bar,
            reason=""
            if current_bar_is_highest_except_top_bar
            else "Current bar is not the highest since top bar",
        )
