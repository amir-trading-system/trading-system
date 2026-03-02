import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_day_upside_after_lowest_low"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> bool:
        current_day_upside_after_lowest_low = False
        previous_bar = stock.previous_bar(
            bar_object=current_bar,
        )
        if (
            True
            and previous_bar is not None
            and previous_bar.close > previous_bar.open_value
            and previous_bar.volume > previous_bar.volume_average * 3
        ):
            return False

        for bar_object in stock.bars[current_bar.index+1:current_bar.index+10]:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            if (
                True
                and previous_bar is not None
                and bar_object.close < bar_object.open_value
                and bar_object.volume > bar_object.volume_average
                and bar_object.close < bar_object.ema_9
                and bar_object.close < bar_object.ema_20
                and bar_object.close < bar_object.vwap
                and min(
                    bar_obj.close
                    for bar_obj in stock.bars[bar_object.index:bar_object.index+50]
                ) == bar_object.close
                and min(
                    bar_obj.low
                    for bar_obj in stock.bars[bar_object.index+1:bar_object.index+50]
                ) > bar_object.close
                and bar_object.volume > previous_bar.volume
                and bar_object.low/bar_object.close >= 0.9
                and bar_object.volume > 200000
            ):
                stock.last_lowest_low_bar = bar_object
                current_day_upside_after_lowest_low = True
                break

        return current_day_upside_after_lowest_low

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
        highest_resistance = max(
            resistance_level.high
            for resistance_level in relevant_stock.resistance_levels
        )
        base_condition = (
            True
            and relevant_stock.last_lowest_low_bar is not None
            and volume_sum_since_market_open > 1000000
            and potential_confirmation_bar.close > potential_confirmation_bar.open_value
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and potential_confirmation_bar.volume > 20000
            and not any(
                resistance_level
                for resistance_level in relevant_stock.resistance_levels
                if resistance_level.high > potential_confirmation_bar.high
                and potential_confirmation_bar.high/resistance_level.high >= 0.92
            )
            and potential_confirmation_bar.high > relevant_stock.last_lowest_low_bar.high
        )
        potential_bar_just_crossed_highest_resistance = (
            True
            and base_condition
            and potential_confirmation_bar.low < highest_resistance < potential_confirmation_bar.close
        )
        potential_bar_just_crossed_last_pre_post_session = (
            True
            and base_condition
            and potential_confirmation_bar.low < relevant_stock.last_post_pre_one_minute_highest_high < potential_confirmation_bar.close
        )
        potential_bar_just_crossed_highest_high_one_minute = (
            True
            and base_condition
            and potential_confirmation_bar.low/highest_high_one_minute < 0.95
            and potential_confirmation_bar.low < highest_high_one_minute < potential_confirmation_bar.close
        )

        bar_has_been_confirmed = (
            True
            and (
                potential_bar_just_crossed_highest_resistance
                or potential_bar_just_crossed_last_pre_post_session
                or potential_bar_just_crossed_highest_high_one_minute
            )
        )

        return bar_has_been_confirmed
