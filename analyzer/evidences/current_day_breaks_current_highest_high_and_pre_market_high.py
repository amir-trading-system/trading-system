import common
from . import evidence


class Evidence(
    evidence.Evidence,
):
    name = "current_day_pre_market_had_move"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> bool:
        current_bar_is_strong = (
            True
            and stock.last_post_pre_one_minute_highest_high > 0
            and (current_bar.close > current_bar.open_value or is_retro)
            and (stock.last_post_pre_one_minute_highest_high - milestones.previous_bar.bar_object.high)/stock.last_post_pre_one_minute_highest_high >= 0.2
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
        above_post_pre_market_highest_high = (
            True
            and potential_confirmation_bar.high > stock.pre_market_one_minute_highest_high_bar.high
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and potential_confirmation_bar.volume > stock.pre_market_one_minute_highest_high_bar.volume
        )
        highest_volume_until_now = max(
            bar_object.volume
            for bar_object in one_minute_bars
        ) == potential_confirmation_bar.volume

        highest_high_until_now = max(b.high for b in one_minute_bars[1:])

        crossed_highest_high = potential_confirmation_bar.low < highest_high_until_now < potential_confirmation_bar.close

        confirmed_bar = (
            True
            and crossed_highest_high
            and potential_confirmation_bar.close > potential_confirmation_bar.open_value
            and above_post_pre_market_highest_high
            and highest_volume_until_now
        )

        return confirmed_bar
