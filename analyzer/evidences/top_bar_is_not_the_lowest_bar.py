from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "top_bar_is_not_the_lowest_bar"
    is_base_evidence = True

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        relevant_bars = stock.bars[1:milestones.top_bar.index]
        if len(relevant_bars) == 0:
            return objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        lowest_bar_since_top_index = min(
            relevant_bars,
            key=lambda bar_object: bar_object.low
        )

        top_bar_is_not_the_lowest_bar = (
            True
            and milestones.top_bar.bar_object.low > lowest_bar_since_top_index.low
            or milestones.top_bar.bar_object.close > milestones.top_bar.bar_object.open_value
        )

        return objects.EvidenceResponse(
            result=top_bar_is_not_the_lowest_bar,
            reason=""
            if top_bar_is_not_the_lowest_bar
            else "Lowest value is the lowest of top bar",
        )
