import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_is_strong_with_high_volume"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        current_bar_has_buyers = (
            True
            and current_bar.close > current_bar.open_value
            and current_bar.high > current_bar.low > 0
            and (current_bar.close > current_bar.open_value)/(current_bar.high > current_bar.low) >= 0.5
        )

        relevant_bars = stock.bars[:milestones.top_bar.index]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        any_bar_is_stronger = any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.volume > 0
            and current_bar.volume/bar_object.volume < 0.8
            and current_bar.volume < 500000
        )

        current_bar_is_strong_with_high_volume = (
            True
            and current_bar_has_buyers
            and not any_bar_is_stronger
        )

        return common.objects.EvidenceResponse(
            result=current_bar_is_strong_with_high_volume,
            reason=""
            if current_bar_is_strong_with_high_volume
            else "current bar is not strong enough",
        )
