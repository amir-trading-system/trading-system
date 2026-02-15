import datetime
import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_day_continues_trend"

    def is_potential_starting_bar(
        self,
        stock: common.objects.Stock,
        bar_object: common.objects.BarData,
    ) -> bool:
        base_condition = True
        previous_bar = stock.previous_bar(
            bar_object=bar_object,
        )
        if previous_bar is not None:
            base_condition = (
                True
                and base_condition
                and bar_object.high > previous_bar.high
            )

        first_option = (
            True
            and bar_object.vwap is not None
            and bar_object.ema_9 is not None
            and bar_object.ema_20 is not None
            and bar_object.volume_average is not None
            and base_condition
            and bar_object.close > bar_object.ema_9
            and bar_object.close > bar_object.ema_20
            and bar_object.volume > bar_object.volume_average
            and bar_object.volume > 500000
            and bar_object.high > bar_object.vwap
            and bar_object.ema_9/bar_object.low >= 0.9
        )
        second_option = (
            True
            and bar_object.vwap is not None
            and bar_object.ema_9 is not None
            and bar_object.ema_20 is not None
            and bar_object.volume_average is not None
            and base_condition
            and bar_object.high > bar_object.vwap
            and bar_object.close > bar_object.ema_9
            and bar_object.histogram > 0
            and bar_object.volume/bar_object.volume_average > 7
            and max(
                stock.bars[bar_object.index:],
                key=lambda bar_obj: bar_obj.volume
            ) == bar_object
        )

        return first_option or second_option

    def get_starting_bar(
        self,
        stock: common.objects.Stock,
        relevant_bars: list[common.objects.BarData],
    ) -> common.objects.MilestoneBar | None:
        for bar_object in relevant_bars:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            potential_starting_bar = (
                True
                and self.is_potential_starting_bar(
                    stock=stock,
                    bar_object=bar_object
                )
                and (
                    not self.is_potential_starting_bar(
                        stock=stock,
                        bar_object=previous_bar,
                    ) if previous_bar is not None else True
                )
            )
            if potential_starting_bar:
                if len(relevant_bars[:10]) > 0:
                    potential_starting_bar = max(
                        [
                            bar_obj.high
                            for bar_obj in relevant_bars[:10]
                        ]
                    ) == bar_object.high

                return common.objects.MilestoneBar(
                    index=bar_object.index,
                    bar_object=bar_object,
                    bar_type=common.objects.MilestoneType.STARTING_BAR,
                    bar_time=bar_object.bar_time,
                    timeframe=bar_object.timeframe,
                )

    def get_top_bar(
        self,
        starting_bar: common.objects.BarData,
        relevant_bars: list[common.objects.BarData],
        current_bar: common.objects.BarData,
    ) -> common.objects.MilestoneBar | None:
        top_bar_options = [
            bar_object
            for bar_object in relevant_bars[:starting_bar.index]
            if (
                True
                and bar_object.index > current_bar.index
                and bar_object.high > starting_bar.high
                and len(relevant_bars[1:starting_bar.index]) > 0
                and bar_object.high == max(
                    [
                        bar_obj.high
                        for bar_obj in relevant_bars[:starting_bar.index]
                        if bar_obj.index > current_bar.index
                    ]
                )
            )
        ]
        if len(top_bar_options) > 0:
            top_bar = top_bar_options[0]
            return common.objects.MilestoneBar(
                index=top_bar.index,
                bar_object=top_bar,
                bar_type=common.objects.MilestoneType.TOP_BAR,
                bar_time=top_bar.bar_time,
                timeframe=top_bar.timeframe,
            )

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

        starting_bar = self.get_starting_bar(
            stock=stock,
            relevant_bars=relevant_bars,
        )

        if starting_bar is None:
            return common.objects.EvidenceResponse(
                result=False,
                reason="No strating bar for this day trend",
            )

        milestones.starting_bar = starting_bar

        top_bar = self.get_top_bar(
            starting_bar=starting_bar.bar_object,
            relevant_bars=relevant_bars,
            current_bar=current_bar,
        )
        if top_bar is not None:
            milestones.top_bar = top_bar

        if not any(
            bar_object
            for bar_object in relevant_bars[:starting_bar.index]
            if current_bar.low < bar_object.high
        ):
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        previous_day = relevant_bars[0]
        previous_day_looks_good = (
            True
            and previous_day.close > previous_day.ema_9
            and previous_day.close > previous_day.ema_20
            and previous_day.high > previous_day.vwap
            and current_bar.low > previous_day.low
        )

        boundries_bar = starting_bar.bar_object
        if top_bar is not None:
            boundries_bar = top_bar.bar_object

        between_bounderis = starting_bar.bar_object.low < current_bar.low < boundries_bar.high

        current_bar_is_strong = (
            True
            and current_bar.close > current_bar.open_value or is_retro
            and current_bar.close > current_bar.ema_9
            and current_bar.close > current_bar.ema_20
            and current_bar.ema_9 > current_bar.ema_20
            and current_bar.histogram > 0
            and between_bounderis
        )
        if len(relevant_bars[:starting_bar.index-1]) > 0:
            current_bar_is_strong = (
                True
                and current_bar_is_strong
                and max(
                    [
                        bar_obj.high
                        for bar_obj in relevant_bars[:starting_bar.index-1]
                    ]
                ) < current_bar.high
            )

        current_day_continues_trend = (
            True
            and previous_day_looks_good
            and current_bar_is_strong
        )

        return common.objects.EvidenceResponse(
            result=current_day_continues_trend,
            reason=""
            if current_day_continues_trend
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
        if milestones.top_bar.bar_object.index == 0:
            milestones.top_bar.bar_object.high = 0.0

        crossed_previous_day_only = (
            True
            and (potential_confirmation_bar.high <= milestones.starting_bar.bar_object.high or potential_confirmation_bar.high <= milestones.top_bar.bar_object.high)
            and potential_confirmation_bar.high > relevant_stock.bars[1].high
            and potential_confirmation_bar.low < relevant_stock.bars[1].high
            and potential_confirmation_bar.close > highest_high_one_minute
        )
        crossed_starting_point = (
            True
            and potential_confirmation_bar.high > milestones.starting_bar.bar_object.high
            and potential_confirmation_bar.low < milestones.starting_bar.bar_object.high
            and potential_confirmation_bar.close > highest_high_one_minute
        )
        crossed_top_point = (
            True
            and potential_confirmation_bar.high > milestones.top_bar.bar_object.high
            and potential_confirmation_bar.low < milestones.top_bar.bar_object.high
            and potential_confirmation_bar.close > highest_high_one_minute
        )

        crossed_highest_one_minute = False
        if (
            True
            and highest_high_one_minute > milestones.starting_bar.bar_object.high
            and highest_high_one_minute > milestones.top_bar.bar_object.high
            and potential_confirmation_bar.high > milestones.starting_bar.bar_object.high
            and potential_confirmation_bar.high > milestones.top_bar.bar_object.high
        ):
            crossed_highest_one_minute = (
                True
                and potential_confirmation_bar.low < highest_high_one_minute
                and potential_confirmation_bar.close > highest_high_one_minute
            )

        crossed_only_highest_high_today_and_after_noon = False
        previous_bar = relevant_stock.previous_bar(
            bar_object=original_bar_to_confirm,
        )
        highest_high_bar = [
            bar_obj
            for bar_obj in one_minute_bars
            if bar_obj.high == highest_high_one_minute
        ]
        if highest_high_bar:
            highest_high_bar = highest_high_bar[-1]

            crossed_only_highest_high_today_and_after_noon = (
                True
                and original_bar_to_confirm.low < previous_bar.high
                and potential_confirmation_bar.low < highest_high_one_minute
                and potential_confirmation_bar.high > highest_high_one_minute
                and potential_confirmation_bar.bar_time.hour >= 11
                and potential_confirmation_bar.bar_time - datetime.timedelta(minutes=20) < highest_high_bar.bar_time
            )

        if (
            True
            and potential_confirmation_bar.close > potential_confirmation_bar.open_value
            and (
                crossed_previous_day_only
                or crossed_starting_point
                or crossed_top_point
                or crossed_highest_one_minute
                or crossed_only_highest_high_today_and_after_noon
            )
            and potential_confirmation_bar.low < highest_high_one_minute < potential_confirmation_bar.close
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and potential_confirmation_bar.close > potential_confirmation_bar.ema_9
            and potential_confirmation_bar.close > potential_confirmation_bar.ema_20
            and potential_confirmation_bar.close > potential_confirmation_bar.vwap
            and potential_confirmation_bar.volume > 30000
        ):
            return True

        return False
