import common
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "no_indecision_histogram_from_top"
    is_base_evidence = True

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.top_bar.index]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        indecision_histogram_bar_index = None
        no_indecision_histogram_from_top = True

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
                and bar_object.histogram > previous_bar.histogram
                and bar_object.histogram > next_bar.histogram
                and stock.bars[previous_bar.index+1].histogram > previous_bar.histogram
            ):
                indecision_histogram_bar_index = bar_object.index
                no_indecision_histogram_from_top = False
                break

        return common.objects.EvidenceResponse(
            result=no_indecision_histogram_from_top,
            reason=""
            if no_indecision_histogram_from_top
            else f"There has been indecision histogram since top bar. index: {indecision_histogram_bar_index}",
        )
