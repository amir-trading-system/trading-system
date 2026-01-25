import common

from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_has_histogram_wave"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[1:milestones.top_bar.index+1]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        highest_histogram_change = 0.0
        downtrend_histogram_count = 0

        for bar_object in relevant_bars:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            if not previous_bar:
                continue

            histogram_distance = abs(bar_object.histogram - previous_bar.histogram)
            if (
                True
                and histogram_distance > highest_histogram_change
                and bar_object.index+1 < milestones.starting_bar.index
            ):
                highest_histogram_change = histogram_distance

            if bar_object.histogram < previous_bar.histogram:
                downtrend_histogram_count += 1

        previous_histogram = milestones.previous_bar.bar_object.histogram
        current_histogram_has_big_change_regarding_before = (
            True
            and current_bar.histogram > previous_histogram
            and previous_histogram > 0
            and current_bar.histogram - previous_histogram > highest_histogram_change
        )

        current_bar_has_histogram_wave = (
            True
            and current_histogram_has_big_change_regarding_before
            and downtrend_histogram_count >= 2
        )

        return common.objects.EvidenceResponse(
            result=current_bar_has_histogram_wave,
            reason=""
            if current_bar_has_histogram_wave
            else "Current bar does not have histogram wave",
        )
