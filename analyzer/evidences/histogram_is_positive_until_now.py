from analyzer import objects
from tws import objects as tws_objects

from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "histogram_is_positive_until_now"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.starting_bar.index]
        if len(relevant_bars) == 0:
            return objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        histogram_is_positive_until_now = not any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.histogram < 0
        )

        return objects.EvidenceResponse(
            result=histogram_is_positive_until_now,
            reason=""
            if histogram_is_positive_until_now
            else "Histogram was not fully positive",
        )
