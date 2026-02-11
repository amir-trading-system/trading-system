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

        top_bar: common.objects.BarData = None
        for bar_object in relevant_bars[:current_bar.index+40]:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            next_bar = stock.next_bar(
                bar_object=bar_object,
            )

            if (
                True
                and bar_object.high > bar_object.ema_9
                and bar_object.high > bar_object.ema_20
                and bar_object.high > bar_object.vwap
                and previous_bar is not None
                and next_bar is not None
                and previous_bar.high < bar_object.high > next_bar.high
                and previous_bar.high > previous_bar.ema_9
                and previous_bar.high > previous_bar.ema_20
                and next_bar.high > next_bar.ema_9
                and next_bar.high > next_bar.ema_20
            ):
                if top_bar is None:
                    top_bar = bar_object
                    continue

                rounded_top_bar_high = round(top_bar.high * 100) / 100
                rounded_bar_object_high = round(bar_object.high * 100) / 100
                if rounded_top_bar_high < rounded_bar_object_high:
                    top_bar = bar_object

        if top_bar is None:
            return common.objects.EvidenceResponse(
                result=False,
                reason="top bar does not exists",
            )

        breaking_high_attempts = 0
        for bar_object in relevant_bars[:current_bar.index+40]:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            next_bar = stock.next_bar(
                bar_object=bar_object,
            )
            if (
                True
                and bar_object.high/top_bar.high >= 0.95
                and bar_object.high > bar_object.ema_9
                and bar_object.high > bar_object.ema_20
                and previous_bar is not None
                and previous_bar.high < bar_object.high
                and previous_bar is not None
                and next_bar is not None
                and previous_bar.high > previous_bar.ema_9
                and previous_bar.high > previous_bar.ema_20
                and next_bar.high > next_bar.ema_9
                and next_bar.high > next_bar.ema_20
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
        current_bar = relevant_stock.bars[0]
        potential_confirmation_bar_is_highest = max(
            [
                round(highest_high_one_minute, 2),
                round(milestones.top_bar.bar_object.high, 2),
                round(current_bar.ema_9, 2),
                round(current_bar.ema_20, 2),
            ]
        ) < potential_confirmation_bar.close

        potential_bar_close_much_bigger_than_top_bar_high = potential_confirmation_bar.high - milestones.top_bar.bar_object.high > milestones.top_bar.bar_object.high - potential_confirmation_bar.low

        potential_confirmation_bar_is_strong = (
            True
            and potential_confirmation_bar.close > potential_confirmation_bar.open_value
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and potential_confirmation_bar.low < milestones.top_bar.bar_object.high
            and potential_bar_close_much_bigger_than_top_bar_high
        )

        return (
            True
            and potential_confirmation_bar_is_highest
            and potential_confirmation_bar_is_strong
        )
