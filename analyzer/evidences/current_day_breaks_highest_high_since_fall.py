import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_day_breaks_highest_high_since_fall"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> bool:
        top_bar_is_valid = len(stock.resistance_levels) > 0

        current_day_breaks_highest_high_since_fall = (
            True
            and (current_bar.close > current_bar.open_value or is_retro)
            and top_bar_is_valid
            and any(
                r_l
                for r_l in stock.resistance_levels
                if r_l.high > current_bar.low
            )
        )

        return current_day_breaks_highest_high_since_fall

    def confirm(
        self,
        stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        highest_high_one_minute_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
        volume_sum_since_market_open: float,
    ) -> bool:
        potential_confirmation_bar_is_strong = False
        current_bar = stock.bars[0]
        ema_for_check = current_bar.ema_9 if current_bar.ema_9 < current_bar.ema_20 else current_bar.ema_20
        potential_confirmation_bar_is_highest = max(
            [
                round(highest_high_one_minute_bar.high, 2),
                round(ema_for_check, 2),
            ]
        ) < potential_confirmation_bar.close

        crossed_resistance_level_strongly = self.crossed_resistance_level_strongly(
            resistance_levels=stock.resistance_levels,
            highest_high_one_minute_bar=highest_high_one_minute_bar,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        potential_confirmation_bar_is_strong = (
            True
            and potential_confirmation_bar.close > potential_confirmation_bar.open_value
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and crossed_resistance_level_strongly
        )

        return (
            True
            and potential_confirmation_bar_is_highest
            and potential_confirmation_bar_is_strong
        )
