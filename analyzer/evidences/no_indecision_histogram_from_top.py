from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "no_indecision_histogram_from_top"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        relevant_bars = stock.bars[1:milestones.top_bar.index-1]
        if len(relevant_bars) == 0:
            return objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        indecision_histogram_bar_index = None
        no_indecision_histogram_from_top = True

        for bar_object in relevant_bars:
            if not stock.has_previous_bar(
                bar_object=bar_object,
            ):
                continue

            previous_bar = stock.bars[bar_object.index+1]
            next_bar = stock.bars[bar_object.index-1]
            if (
                True
                and bar_object.histogram > previous_bar.histogram
                and bar_object.histogram > next_bar.histogram
                and stock.bars[previous_bar.index+1] > previous_bar.histogram
            ):
                indecision_histogram_bar_index = bar_object.index
                no_indecision_histogram_from_top = False
                break

        return objects.EvidenceResponse(
            result=no_indecision_histogram_from_top,
            reason=""
            if no_indecision_histogram_from_top
            else f"There has been indecision histogram since top bar. index: {indecision_histogram_bar_index}",
        )
