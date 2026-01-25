import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "starting_bar_is_not_the_biggest_in_terms_of_price"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.starting_bar.index]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        starting_bar = milestones.starting_bar.bar_object
        starting_bar_is_not_the_biggest_in_terms_of_price = any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.high - bar_object.low > starting_bar.high - starting_bar.low
        )

        return common.objects.EvidenceResponse(
            result=starting_bar_is_not_the_biggest_in_terms_of_price,
            reason=""
            if starting_bar_is_not_the_biggest_in_terms_of_price
            else "Starting bar has the biggest price movement",
        )
