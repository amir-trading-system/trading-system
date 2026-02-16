import common
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

        resistance_level_to_breaking_attempts: dict[float,int] = self.get_resistance_levels(
            stock=stock,
            relevant_bars=relevant_bars,
            current_bar=current_bar,
        )
        top_bar = [
            bar_object
            for bar_object in stock.bars
            if bar_object.high == max(resistance_level_to_breaking_attempts)
        ][0]

        if top_bar is None:
            return common.objects.EvidenceResponse(
                result=False,
                reason="top bar does not exists",
            )

        stock.resistance_levels = list(resistance_level_to_breaking_attempts.keys())
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
            and any(
                r_l
                for r_l in stock.resistance_levels
                if r_l > current_bar.low
            )
        )

        return common.objects.EvidenceResponse(
            result=current_day_breaks_highest_high_since_fall,
            reason=""
            if current_day_breaks_highest_high_since_fall
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
        potential_confirmation_bar_is_strong = False
        current_bar = relevant_stock.bars[0]
        potential_confirmation_bar_is_highest = max(
            [
                round(highest_high_one_minute, 2),
                round(current_bar.ema_9, 2),
                round(current_bar.ema_20, 2),
            ]
        ) < potential_confirmation_bar.close

        crossed_resistance_level_strongly = self.crossed_resistance_level_strongly(
            resistance_levels=relevant_stock.resistance_levels,
            potential_confirmation_bar=potential_confirmation_bar,
        )

        potential_confirmation_bar_is_strong = (
            True
            and potential_confirmation_bar.close > potential_confirmation_bar.open_value
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and crossed_resistance_level_strongly
        )


        return (
            True
            and potential_confirmation_bar_is_highest
            and potential_confirmation_bar_is_strong
        )
