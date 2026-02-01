import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "most_of_bars_are_volatile"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.starting_bar.index+1]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        volatile_bars_count = len(
            [
                bar_object
                for bar_object in relevant_bars
                if bar_object.volume >= 40000
            ]
        )

        most_of_bars_are_volatile = volatile_bars_count/milestones.starting_bar.index >= 0.6

        return common.objects.EvidenceResponse(
            result=most_of_bars_are_volatile,
            reason=""
            if most_of_bars_are_volatile
            else "Most of bars are not volatile",
        )
