import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "has_bull_pattern"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.starting_bar.index+1]
        if len(relevant_bars) < 4:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        third_bar_is_very_strong = (
            True
            and relevant_bars[2].close > relevant_bars[2].open_value
            and relevant_bars[2].volume > relevant_bars[2].volume_average
            and relevant_bars[2].volume > relevant_bars[3].volume * 2
            and relevant_bars[2].close/relevant_bars[2].high >= 0.9
            and relevant_bars[2].high > relevant_bars[1].high
        )

        second_bar_is_negative_with_good_retacement = (
            True
            and relevant_bars[1].close < relevant_bars[1].open_value
            and relevant_bars[1].high - relevant_bars[1].low > 0
            and (relevant_bars[1].close - relevant_bars[1].low)/(relevant_bars[1].high - relevant_bars[1].low) >= 0.5
            and (relevant_bars[1].open_value - relevant_bars[1].close)/(relevant_bars[1].high - relevant_bars[1].low) <= 0.3
            and relevant_bars[1].volume > relevant_bars[1].volume_average
            and relevant_bars[1].volume < relevant_bars[2].volume
            and relevant_bars[1].volume/relevant_bars[2].volume >= 0.5
        )

        third_bar_middle_point = relevant_bars[2].high - ((relevant_bars[2].high - relevant_bars[2].low)/2)

        second_bar_low_close_to_middle_point = third_bar_middle_point/relevant_bars[1].low >= 0.9

        highest_high = max(
            relevant_bars,
            key=lambda bar_object: bar_object.high
        )

        has_bull_pattern = (
            True
            and third_bar_is_very_strong
            and second_bar_is_negative_with_good_retacement
            and second_bar_low_close_to_middle_point
            and highest_high == current_bar.high
        )

        return common.objects.EvidenceResponse(
            result=has_bull_pattern,
            reason=""
            if has_bull_pattern
            else "Does not have bull pattern",
        )
