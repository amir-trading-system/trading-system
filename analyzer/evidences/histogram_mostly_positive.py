import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "histogram_mostly_positive"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.starting_bar.index+1]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        lowest_histogram = 1000.0
        lowest_histogram_index = 0

        for bar_object in relevant_bars:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            next_bar = stock.next_bar(
                bar_object=bar_object,
            )
            if not previous_bar or not next_bar:
                continue

            if (
                True
                and bar_object.histogram < 0
                and bar_object.histogram < previous_bar.histogram
                and bar_object.histogram < next_bar.histogram
                and bar_object.histogram < lowest_histogram
            ):
                lowest_histogram_index = bar_object.index
                lowest_histogram = bar_object.histogram

        highest_histogram = 1000.0
        for bar_object in stock.bars[lowest_histogram_index:milestones.starting_bar.index+1]:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            next_bar = stock.next_bar(
                bar_object=bar_object,
            )
            if not previous_bar or not next_bar:
                continue

            if (
                True
                and bar_object.histogram > 0
                and bar_object.histogram > previous_bar.histogram
                and bar_object.histogram > next_bar.histogram
                and bar_object.histogram > highest_histogram
            ):
                highest_histogram = bar_object.histogram


        histogram_mostly_positive = (
            True
            and abs(lowest_histogram)/highest_histogram < 0.3
            and abs(lowest_histogram) < current_bar.histogram
        )

        return common.objects.EvidenceResponse(
            result=histogram_mostly_positive,
            reason=""
            if histogram_mostly_positive
            else "Histogram was not mostly positive or histogram was fully positive",
        )
