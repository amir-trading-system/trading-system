import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "has_three_positive_two_negative_pattern"

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

        has_three_positive_two_negative_pattern = any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.index+4 <= milestones.starting_bar.index
            and bar_object.close < bar_object.open_value
            and stock.bars[bar_object.index+1].close < stock.bars[bar_object.index+1].open_value
            and stock.bars[bar_object.index+2].close > stock.bars[bar_object.index+2].open_value
            and stock.bars[bar_object.index+3].close > stock.bars[bar_object.index+3].open_value
            and stock.bars[bar_object.index+4].close > stock.bars[bar_object.index+4].open_value
            and bar_object.volume < stock.bars[bar_object.index+1].volume
        )

        return common.objects.EvidenceResponse(
            result=has_three_positive_two_negative_pattern,
            reason=""
            if has_three_positive_two_negative_pattern
            else "Doesnt have 3-2 pattern",
        )
