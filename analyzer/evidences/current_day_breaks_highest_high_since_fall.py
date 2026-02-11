import common
from common.objects import BarData, Milestones, Stock
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
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[1:]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        top_bar = max(
            relevant_bars[:current_bar.index+40],
            key=lambda bar_obj: bar_obj.high
        )
        breaking_high_attempts = 0
        for bar_object in relevant_bars[:current_bar.index+40]:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            if (
                True
                and bar_object.high/top_bar.high >= 0.95
                and bar_object.high > bar_object.ema_9
                and bar_object.high > bar_object.ema_20
                and previous_bar is not None
                and previous_bar.high < bar_object.high
            ):
                breaking_high_attempts += 1

        top_bar_is_valid = breaking_high_attempts >= 2
        if top_bar_is_valid:
            milestones.top_bar = common.objects.MilestoneBar(
                index=top_bar.index,
                bar_object=top_bar,
                bar_type=common.objects.MilestoneType.TOP_BAR,
                bar_time=top_bar.bar_time,
                timeframe=top_bar.timeframe,
            )

        previous_day = relevant_bars[0]
        current_day_breaks_highest_high_since_fall = (
            True
            and current_bar.close > current_bar.open_value
            and current_bar.close > current_bar.ema_20
            and current_bar.high > previous_day.high
            and current_bar.histogram > 0
            and top_bar_is_valid
        )

        return common.objects.EvidenceResponse(
            result=current_day_breaks_highest_high_since_fall,
            reason=""
            if current_day_breaks_highest_high_since_fall
            else "Current day does not continues any trend",
        )

    def confirm(
        self,
        relevant_stock: Stock,
        potential_confirmation_bar: BarData,
        milestones: Milestones,
        highest_high_one_minute: float,
    ) -> bool:
        return False
