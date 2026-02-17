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
    ) -> common.objects.EvidenceResponse:
        previous_bar = stock.previous_bar(
            bar_object=current_bar,
        )

        current_bar_crossed_any_resistance = (
            True
            and current_bar.close > current_bar.open_value
            and current_bar.close > current_bar.ema_9
            and current_bar.close > current_bar.ema_20
            and current_bar.close > current_bar.vwap
            and any(
                resistance_level
                for resistance_level in stock.resistance_levels
                if current_bar.low < resistance_level < current_bar.high
            )
            and current_bar.low < previous_bar.high < current_bar.high
        )

        return common.objects.EvidenceResponse(
            result=current_bar_crossed_any_resistance,
            reason=""
            if current_bar_crossed_any_resistance
            else "Current day does not continues any trend",
        )

    def confirm(
        self,
        relevant_stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        highest_high_one_minute: float,
        one_minute_bars: list[common.objects.BarData],
    ) -> bool:
        current_bar = relevant_stock.bars[0]
        potential_confirmation_bar_is_today_highest = max(
            [
                round(highest_high_one_minute, 2),
                round(current_bar.ema_9, 2),
                round(current_bar.ema_20, 2),
            ]
        ) < potential_confirmation_bar.close

        previous_bar = relevant_stock.previous_bar(
            bar_object=current_bar,
        )

        crossed_highest_high = (
            True
            and previous_bar.high < highest_high_one_minute
            and potential_confirmation_bar.low < highest_high_one_minute < potential_confirmation_bar.close
        )

        highest_than_any_resistance_level = any(
            resistance_level
            for resistance_level in relevant_stock.resistance_levels
            if resistance_level < potential_confirmation_bar.close
        )

        return (
            True
            and potential_confirmation_bar.close > potential_confirmation_bar.open_value
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and potential_confirmation_bar_is_today_highest
            and crossed_highest_high
            and highest_than_any_resistance_level
        )
