import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_day_is_after_healty_retracement"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> bool:
        previous_day = milestones.previous_bar.bar_object
        previous_day_is_strong = (
            True
            and previous_day.close > previous_day.open_value
            and previous_day.volume > previous_day.volume_average
            and (previous_day.close-previous_day.open_value)/(previous_day.high-previous_day.low) > 0.3
            and previous_day.high > current_bar.high
        )

        current_day_is_potential = (
            True
            and (current_bar.open_value-current_bar.low)/(current_bar.high-current_bar.low) >= 0.2
            and current_bar.open_value-current_bar.low > abs(current_bar.close-current_bar.open_value)
        )

        current_day_is_after_healty_retracement = (
            True
            and previous_day_is_strong
            and current_day_is_potential
        )
        return current_day_is_after_healty_retracement

    def confirm(
        self,
        relevant_stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        highest_high_one_minute: float,
        one_minute_bars: list[common.objects.BarData],
        volume_sum_since_market_open: float,
    ) -> bool:
        current_day_is_strong = (
            True
            and original_bar_to_confirm.low > original_bar_to_confirm.ema_9
            and original_bar_to_confirm.ema_9 > original_bar_to_confirm.ema_20
        )
        previous_one_minute_bar = [
            bar_object
            for bar_object in one_minute_bars
            if bar_object.index-1 == potential_confirmation_bar.index
        ][0]

        potential_bar_is_most_volatile = max(
            bar_object.volume
            for bar_object in one_minute_bars
            if bar_object.index <= potential_confirmation_bar.index+20
        ) == potential_confirmation_bar.volume

        potential_bar_is_highest = not any(
            bar_object.high
            for bar_object in one_minute_bars
            if potential_confirmation_bar.index+1 < bar_object.index <= potential_confirmation_bar.index+20
            and bar_object.high >= potential_confirmation_bar.high
        )

        potential_bar_break_parallel_channel = (
            True
            and potential_confirmation_bar.close > potential_confirmation_bar.open_value
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and potential_confirmation_bar.low > potential_confirmation_bar.vwap
            and potential_confirmation_bar.ema_9 > potential_confirmation_bar.vwap
            and potential_confirmation_bar.ema_9 > potential_confirmation_bar.ema_20
            and potential_confirmation_bar.close > potential_confirmation_bar.ema_9
            and potential_confirmation_bar.close > potential_confirmation_bar.ema_20
            and potential_confirmation_bar.close > potential_confirmation_bar.vwap
            and potential_confirmation_bar.signal_line > 0
            and potential_confirmation_bar.high > previous_one_minute_bar.high
            and potential_confirmation_bar.volume > previous_one_minute_bar.volume
            and (potential_confirmation_bar.high - potential_confirmation_bar.low) > (previous_one_minute_bar.high - previous_one_minute_bar.low)
        )

        bar_has_been_confirmed = (
            True
            and current_day_is_strong
            and potential_bar_break_parallel_channel
            and potential_bar_is_most_volatile
            and potential_bar_is_highest
        )

        return bar_has_been_confirmed
