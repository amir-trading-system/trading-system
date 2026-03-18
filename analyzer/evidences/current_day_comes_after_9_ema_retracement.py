import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_day_comes_after_9_ema_retracement"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> bool:
        previous_day = milestones.previous_bar.bar_object
        two_days_ago_bar = stock.bars[2]
        three_days_ago_bar = stock.bars[3]

        day_before_previous_day_is_strong_day = (
            True
            and three_days_ago_bar.high < two_days_ago_bar.high > previous_day.high
            and two_days_ago_bar.close > two_days_ago_bar.open_value
            and two_days_ago_bar.volume > two_days_ago_bar.volume_average
            and two_days_ago_bar.volume > previous_day.volume
            and (two_days_ago_bar.low-two_days_ago_bar.ema_9)/(previous_day.high-previous_day.low) >= 0.5
        )

        previous_day_is_after_9_ema_retracement = previous_day.ema_9/previous_day.low >= 0.8

        current_day_comes_after_9_ema_retracement = (
            True
            and day_before_previous_day_is_strong_day
            and previous_day_is_after_9_ema_retracement
        )

        return current_day_comes_after_9_ema_retracement

    def _confirm(
        self,
        stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        highest_high_one_minute_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
        volume_sum_since_market_open: float,
    ) -> bool:
        current_day_is_strong = (
            True
            and original_bar_to_confirm.low > original_bar_to_confirm.ema_9
            and original_bar_to_confirm.ema_9 > original_bar_to_confirm.ema_20
            and stock.last_post_pre_one_minute_highest_high < potential_confirmation_bar.close
        )
        if len(one_minute_bars) == 1:
            return False

        previous_one_minute_bar = one_minute_bars[1]

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
            and potential_confirmation_bar.low/potential_confirmation_bar.vwap > 0.95
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
