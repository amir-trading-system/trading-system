import common
from . import evidence


class Evidence(
    evidence.Evidence,
):
    name = "current_day_comes_after_strong_day"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> bool:
        previous_bar = milestones.previous_bar.bar_object
        previous_day_closed_strong = (
            True
            and previous_bar.close > previous_bar.open_value
            and previous_bar.open_value > previous_bar.ema_9
            and previous_bar.volume > previous_bar.volume_average
            and (previous_bar.close - previous_bar.open_value)/(previous_bar.high - previous_bar.low) >= 0.7
            and previous_bar.close/previous_bar.high >= 0.9
            and previous_bar.histogram > 0
        )

        current_day_does_not_touch_previous_day = current_bar.low >= previous_bar.high

        previous_day_is_strong = (
            True
            and previous_day_closed_strong
            and not any(
                bar_object
                for bar_object in stock.bars[2:32]
                if bar_object.volume/previous_bar.volume >= 0.5
            )
        )

        current_day_comes_after_strong_day = (
            True
            and current_bar.volume > current_bar.volume_average
            and current_day_does_not_touch_previous_day
            and previous_day_is_strong
        )

        return current_day_comes_after_strong_day

    def confirm(
        self,
        stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        highest_high_one_minute_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
    ) -> bool:
        current_bar_highest_from_post_pre_market = stock.last_post_pre_one_minute_highest_high < potential_confirmation_bar.close

        current_bar_is_highest_since_open = max(
            bar_object.high
            for bar_object in one_minute_bars
        ) == potential_confirmation_bar.high

        current_bar_closed_strong = (
            True
            and potential_confirmation_bar.close > potential_confirmation_bar.open_value
            and potential_confirmation_bar.body_percentage >= 0.75
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and len(one_minute_bars) >= 30
            and potential_confirmation_bar.volume == max(
                bar_object.volume
                for bar_object in one_minute_bars[:30]
            )
        )

        potential_bar_crossed_just_now_highest_high = (
            True
            and highest_high_one_minute_bar.index < potential_confirmation_bar.index+10
            and potential_confirmation_bar.open_value < highest_high_one_minute_bar.high < potential_confirmation_bar.close
        )

        confirmed_bar = (
            True
            and potential_bar_crossed_just_now_highest_high
            and current_bar_highest_from_post_pre_market
            and current_bar_is_highest_since_open
            and current_bar_closed_strong
        )

        return confirmed_bar
