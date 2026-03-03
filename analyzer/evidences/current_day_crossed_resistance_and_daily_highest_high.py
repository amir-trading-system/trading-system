import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_day_crossed_resistance_and_daily_highest_high"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> bool:
        previous_bar = stock.previous_bar(
            bar_object=current_bar,
        )

        current_bar_crossed_any_resistance = (
            True
            and previous_bar is not None
            and (current_bar.close > current_bar.open_value or is_retro)
            and any(
                resistance_level
                for resistance_level in stock.resistance_levels
                if current_bar.low < resistance_level.high < current_bar.high
                and not resistance_level.has_strong_rejection()
            )
            and current_bar.low < previous_bar.high
        )

        return current_bar_crossed_any_resistance

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
        current_bar = relevant_stock.bars[0]
        previous_bar = relevant_stock.previous_bar(
            bar_object=current_bar,
        )

        highest_high_bar = [
            bar_object
            for bar_object in one_minute_bars
            if bar_object.high == highest_high_one_minute
        ]
        if not highest_high_bar:
            return False

        highest_high_bar = highest_high_bar[0]

        if (
            True
            and highest_high_bar.close < highest_high_bar.open_value
            and potential_confirmation_bar.index+1 < highest_high_bar.index
            and (highest_high_bar.high - highest_high_bar.close)/(highest_high_bar.high - highest_high_bar.low) > 0.5
            and highest_high_bar.volume > highest_high_bar.volume_average
        ):
            return False

        crossed_highest_high = (
            True
            and previous_bar is not None
            and previous_bar.high < highest_high_one_minute
            and potential_confirmation_bar.low < highest_high_one_minute <= potential_confirmation_bar.close
            and (
                potential_confirmation_bar.index+1 < highest_high_bar.index
                or highest_high_bar.close < highest_high_bar.open_value
            )
            and potential_confirmation_bar.bar_time.hour >= 11
        )

        highest_than_any_resistance_level = any(
            resistance_level
            for resistance_level in relevant_stock.resistance_levels
            if resistance_level.high < potential_confirmation_bar.close
            and not resistance_level.has_strong_rejection()
        ) and not any(
            resistance_level
            for resistance_level in relevant_stock.resistance_levels
            if resistance_level.high > potential_confirmation_bar.high
            and potential_confirmation_bar.high/resistance_level.high >= 0.9
        )

        return (
            True
            and potential_confirmation_bar.close > potential_confirmation_bar.open_value
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and crossed_highest_high
            and highest_than_any_resistance_level
        )
