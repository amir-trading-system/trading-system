import datetime

import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_day_starting_trend"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[1:]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        resistance_level_to_breaking_attempts: dict[float,int] = self.get_resistance_levels(
            stock=stock,
            relevant_bars=relevant_bars,
            current_bar=current_bar,
        )
        stock.resistance_levels = list(resistance_level_to_breaking_attempts.keys())

        current_day_is_the_start_of_a_trend = not any(
            bar_object
            for bar_object in relevant_bars[:10]
            if bar_object.high > current_bar.low
        ) or not any(
            bar_object
            for bar_object in relevant_bars[:20]
            if bar_object.volume > current_bar.volume
        )

        current_day_starting_trend = (
            True
            and current_day_is_the_start_of_a_trend
            and current_bar.close > current_bar.open_value
            and current_bar.close > current_bar.ema_9
            and current_bar.close > current_bar.ema_20
        )

        return common.objects.EvidenceResponse(
            result=current_day_starting_trend,
            reason=""
            if current_day_starting_trend
            else "Current day does not starting any trend",
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
        bar_has_been_confirmed = False

        highest_high_bar: common.objects.BarData = None
        highest_high_bars = [
            bar_object
            for bar_object in one_minute_bars
            if bar_object.high == highest_high_one_minute
        ]
        if highest_high_bars:
            highest_high_bar = highest_high_bars[-1]
            since_highest_high_retracement_occurred = any(
                bar_object
                for bar_object in one_minute_bars
                if (
                    potential_confirmation_bar.index < bar_object.index < highest_high_bar.index
                    and bar_object.high < potential_confirmation_bar.low
                ) or (bar_object.close < bar_object.open_value and bar_object.close >= bar_object.ema_9)
            )

            crossed_resistance_level_strongly = self.crossed_resistance_level_strongly(
                resistance_levels=relevant_stock.resistance_levels,
                potential_confirmation_bar=potential_confirmation_bar,
            )

            bar_has_been_confirmed = (
                True
                and crossed_resistance_level_strongly
                and highest_high_bar is not None
                and potential_confirmation_bar.volume > highest_high_bar.volume
                and potential_confirmation_bar.bar_time - datetime.timedelta(
                    minutes=20,
                ) < highest_high_bar.bar_time
                and since_highest_high_retracement_occurred
                and potential_confirmation_bar.volume > 50000
            )

        return bar_has_been_confirmed
