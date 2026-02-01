import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "has_classic_bars_wave"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.starting_bar.index+1]
        if len(relevant_bars) < 5:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        forth_bar_is_positive = (
            True
            and relevant_bars[3].close > relevant_bars[3].open_value
            and relevant_bars[3].high > relevant_bars[4].high
            and relevant_bars[3].volume > relevant_bars[3].volume_average
            and relevant_bars[3].volume > relevant_bars[4].volume
        )

        both_middle_bars_are_negative_but_weak = (
            True
            and relevant_bars[2].close < relevant_bars[2].open_value
            and relevant_bars[1].close < relevant_bars[1].open_value
            and relevant_bars[2].volume > relevant_bars[1].volume
            and relevant_bars[2].volume < relevant_bars[3].volume
            and relevant_bars[2].close > relevant_bars[2].ema_9
            and relevant_bars[1].close > relevant_bars[1].ema_9
            and relevant_bars[2].high > relevant_bars[1].high
            and relevant_bars[2].high - relevant_bars[2].low > relevant_bars[1].high - relevant_bars[1].low
        )

        current_bar_is_strong = (
            True
            and current_bar.close > current_bar.open_value
            and current_bar.volume > current_bar.volume_average
            and current_bar.volume > milestones.previous_bar.bar_object.volume
            and current_bar.close > milestones.previous_bar.bar_object.high
        )

        has_classic_bars_wave = (
            True
            and forth_bar_is_positive
            and both_middle_bars_are_negative_but_weak
            and current_bar_is_strong
        )

        return common.objects.EvidenceResponse(
            result=has_classic_bars_wave,
            reason=""
            if has_classic_bars_wave
            else "Does not have classic bars wave",
        )
