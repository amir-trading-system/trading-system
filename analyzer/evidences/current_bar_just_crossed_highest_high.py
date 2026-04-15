import common
from . import evidence


class Evidence(
    evidence.Evidence,
):
    name = "current_bar_just_crossed_highest_high"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> bool:
        current_bar_is_strong = (
            True
            and current_bar.close > current_bar.open_value
            and (current_bar.body_percentage > 0.7 or is_retro)
            and current_bar.volume > milestones.previous_bar.bar_object.volume
        )

        return current_bar_is_strong

    def confirm(
        self,
        stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        highest_high_one_minute_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
    ) -> bool:
        confirmed_bar = (
            True
            and potential_confirmation_bar.above_9_ema
            and potential_confirmation_bar.above_volume_average
            and potential_confirmation_bar.above_vwap
            and potential_confirmation_bar.body_percentage > 0.5
            and potential_confirmation_bar.low < highest_high_one_minute_bar.high < potential_confirmation_bar.close
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and potential_confirmation_bar.volume_average/potential_confirmation_bar.volume <= 0.5
        )

        return confirmed_bar
