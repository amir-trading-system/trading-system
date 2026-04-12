import common
from . import evidence


class Evidence(
    evidence.Evidence,
):
    name = "current_day_breaks_last_post_and_pre_market_high"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> bool:
        current_bar_is_strong = (
            True
            and (current_bar.close > current_bar.open_value or is_retro)
            and stock.last_post_pre_one_minute_highest_high > milestones.previous_bar.bar_object.high
            and not any(
                resistance_level
                for resistance_level in stock.resistance_levels
                if resistance_level.high > current_bar.low
                and resistance_level.index - 10 <= current_bar.index
                and resistance_level.volume > resistance_level.volume_average
            )
        )

        return current_bar_is_strong

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
        most_of_current_bar_body_above_high = (
            True
            and potential_confirmation_bar.close - potential_confirmation_bar.open_value > 0
            and (
                ((potential_confirmation_bar.close - stock.last_post_pre_one_minute_highest_high)/(potential_confirmation_bar.close - potential_confirmation_bar.open_value) >= 0.5)
                or potential_confirmation_bar.body_percentage >= 0.9
            )
        )

        confirmed_bar = (
            True
            and most_of_current_bar_body_above_high
            and potential_confirmation_bar.close > potential_confirmation_bar.open_value
            and potential_confirmation_bar.close > potential_confirmation_bar.ema_9
            and potential_confirmation_bar.close > potential_confirmation_bar.ema_20
            and potential_confirmation_bar.close > potential_confirmation_bar.vwap
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and potential_confirmation_bar.low < stock.last_post_pre_one_minute_highest_high < potential_confirmation_bar.close
            and stock.post_pre_market_volume_sum > 500000
        )

        return confirmed_bar
