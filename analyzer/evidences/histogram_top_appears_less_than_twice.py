from analyzer import objects
from tws import objects as tws_objects

from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "histogram_top_appears_less_than_twice"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        relevant_bars = stock.bars[1:milestones.starting_bar.index+1]
        if len(relevant_bars) == 0:
            return objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        top_histogram_index = 0
        top_histogram_value = 0.0
        for bar_object in relevant_bars:
            if bar_object.histogram > top_histogram_value:
                top_histogram_index = bar_object.index
                top_histogram_value = bar_object.histogram

        histogram_top_appears_count = 0
        relevant_bars = stock.bars[1:top_histogram_index+1]
        for bar_object in relevant_bars:
            next_bar = stock.next_bar(
                bar_object=bar_object,
            )
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            if not next_bar or not previous_bar:
                continue

            if (
                True
                and bar_object.histogram > next_bar.histogram
                and bar_object.histogram > previous_bar.histogram
                and bar_object.index > current_bar.index
                and bar_object.index < milestones.top_bar.index
            ):
                histogram_top_appears_count += 1

        histogram_top_appears_less_than_twice = histogram_top_appears_count < 2

        return objects.EvidenceResponse(
            result=histogram_top_appears_less_than_twice,
            reason=""
            if histogram_top_appears_less_than_twice
            else "Histogram top appears more than twice",
        )
