import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_day_continues_without_touching_previous"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> bool:
        starting_bar = self.get_starting_bar(
            stock=stock,
        )

        if starting_bar is None:
            return False
        milestones.starting_bar = starting_bar

        top_bar = self.get_top_bar(
            starting_bar=starting_bar.bar_object,
            current_bar=current_bar,
        )
        if top_bar is not None:
            milestones.top_bar = top_bar

        current_day_continues_trend = (
            True
            and current_bar.high > starting_bar.bar_object.high
            and current_bar.close > current_bar.open_value
        )

        return current_day_continues_trend

    def confirm(
        self,
        relevant_stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        highest_high_one_minute: float,
        one_minute_bars: list[common.objects.BarData],
    ) -> bool:
        base_conditions = (
            True
            and potential_confirmation_bar.close > potential_confirmation_bar.open_value
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and potential_confirmation_bar.ema_9 > potential_confirmation_bar.ema_20
            and potential_confirmation_bar.ema_20 > potential_confirmation_bar.vwap
            and potential_confirmation_bar.macd > 0
            and potential_confirmation_bar.signal_line > 0
            and potential_confirmation_bar.histogram > 0
            and potential_confirmation_bar.low < highest_high_one_minute < potential_confirmation_bar.high
            and not any(
                r_l
                for r_l in relevant_stock.resistance_levels
                if r_l.high > potential_confirmation_bar.high
                and potential_confirmation_bar.high/r_l.high >= 0.95
            )
        )

        crossed_scenario_1 = (
            True
            and potential_confirmation_bar.low <= milestones.starting_bar.bar_object.high < potential_confirmation_bar.close
            and (potential_confirmation_bar.high - milestones.starting_bar.bar_object.high)/(potential_confirmation_bar.high - potential_confirmation_bar.low) >= 0.25
        )
        crossed_scenario_2 = (
            True
            and milestones.starting_bar.bar_object.high < potential_confirmation_bar.low
            and milestones.starting_bar.bar_object.high/potential_confirmation_bar.low >= 0.97
        )
        return (
            True
            and base_conditions
            and (
                crossed_scenario_1
                or crossed_scenario_2
            )
        )
