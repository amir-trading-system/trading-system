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

        resistance_level_to_breaking_attempts: dict[float, int] = {}
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
            ):
                if not resistance_level_to_breaking_attempts.get(bar_object.high):
                    resistance_level_to_breaking_attempts[bar_object.high] = 0

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

        resistance_levels: list[float] = resistance_level_to_breaking_attempts.keys()
        for bar_object in relevant_bars[:current_bar.index+40]:
            for resistance_level in resistance_levels:
                previous_bar = stock.previous_bar(
                    bar_object=bar_object,
                )
                next_bar = stock.next_bar(
                    bar_object=bar_object,
                )
                if (
                    True
                    and bar_object.high/resistance_level >= 0.95
                    and bar_object.high > bar_object.ema_9
                    and bar_object.high > bar_object.ema_20
                    and previous_bar is not None
                    and previous_bar.high < bar_object.high
                    and previous_bar is not None
                    and next_bar is not None
                    and previous_bar.high > previous_bar.ema_9
                    and previous_bar.high > previous_bar.ema_20
                ):
                    resistance_level_to_breaking_attempts[resistance_level] += 1

        stock.resistance_levels = [
            resistance_level
            for resistance_level, attempts in resistance_level_to_breaking_attempts.items()
            if attempts >= 2
        ]

        top_bar_is_valid = len(stock.resistance_levels) > 0

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
        potential_confirmation_bar_is_strong = False
        current_bar = relevant_stock.bars[0]
        potential_confirmation_bar_is_highest = max(
            [
                round(highest_high_one_minute, 2),
                round(current_bar.ema_9, 2),
                round(current_bar.ema_20, 2),
            ]
        ) < potential_confirmation_bar.close

        resistances_crossed = [
            level
            for level in relevant_stock.resistance_levels
            if level < potential_confirmation_bar.close
        ]
        potential_confirmation_bar_breaks_any_resistance_level = len(resistances_crossed) > 0
        if potential_confirmation_bar_breaks_any_resistance_level:
            highest_resistance_crossed = max(resistances_crossed)

            potential_bar_close_much_bigger_than_top_bar_high = (
                True
                and potential_confirmation_bar_breaks_any_resistance_level
                and (
                    potential_confirmation_bar.high - highest_resistance_crossed > highest_resistance_crossed - potential_confirmation_bar.low
                    or (
                        potential_confirmation_bar.close > highest_resistance_crossed
                        and (potential_confirmation_bar.close - potential_confirmation_bar.open_value)/(potential_confirmation_bar.high - potential_confirmation_bar.low) >= 0.7
                    )
                )
            )

            potential_confirmation_bar_is_strong = (
                True
                and potential_confirmation_bar.close > potential_confirmation_bar.open_value
                and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
                and potential_confirmation_bar.low < highest_resistance_crossed
                and potential_bar_close_much_bigger_than_top_bar_high
            )

        return (
            True
            and potential_confirmation_bar_is_highest
            and potential_confirmation_bar_is_strong
        )
