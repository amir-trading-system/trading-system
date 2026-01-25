import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "all_bars_are_positive_with_own_retracement"

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

        all_bars_are_positive_and_strong = all(
            bar_object
            for bar_object in relevant_bars
            if bar_object.close > bar_object.open_value
            or bar_object.volume > bar_object.volume_average
        )

        previous_bar = milestones.previous_bar.bar_object
        previous_bar_is_positive_with_own_retracement = (
            True
            and previous_bar.high - previous_bar.low > 0
            and (previous_bar.open_value - previous_bar.low)/(previous_bar.high - previous_bar.low) > 0.5
        )
        current_bar_volume_is_higher_than_before = current_bar.volume > previous_bar.volume
        ema_9_close_to_low = current_bar.ema_9/current_bar.low >= 0.99

        all_bars_are_positive_with_own_retracement = (
            True
            and all_bars_are_positive_and_strong
            and previous_bar_is_positive_with_own_retracement
            and current_bar_volume_is_higher_than_before
            and ema_9_close_to_low
        )

        return common.objects.EvidenceResponse(
            result=all_bars_are_positive_with_own_retracement,
            reason=""
            if all_bars_are_positive_with_own_retracement
            else "Bars doesnt have own retracements",
        )
