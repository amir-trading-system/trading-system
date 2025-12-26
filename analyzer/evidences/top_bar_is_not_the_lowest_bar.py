from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "top_bar_is_not_the_lowest_bar"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        lowest_bar_since_top_index = min(
            stock.bars[1:milestones.top_bar.index-1],
            key=lambda bar_object: bar_object.low
        )
        top_bar_is_not_the_lowest_bar = milestones.top_bar.bar_object.low > lowest_bar_since_top_index.low

        return objects.EvidenceResponse(
            result=top_bar_is_not_the_lowest_bar,
            reason=""
            if top_bar_is_not_the_lowest_bar
            else "Lowest value is the lowest of top bar",
        )
