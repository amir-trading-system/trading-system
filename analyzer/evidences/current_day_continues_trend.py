import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_day_continues_trend"

    def is_potential_starting_bar(
        self,
        bar_object: common.objects.BarData,
    ) -> bool:
        return (
            True
            and bar_object.vwap is not None
            and bar_object.ema_9 is not None
            and bar_object.ema_20 is not None
            and bar_object.volume_average is not None
            and bar_object.close > bar_object.open_value
            and bar_object.close > bar_object.ema_9
            and bar_object.close > bar_object.ema_20
            and bar_object.volume > bar_object.volume_average
            and bar_object.high > bar_object.vwap
        )

    def get_starting_bar(
        self,
        stock: common.objects.Stock,
        relevant_bars: list[common.objects.BarData],
    ) -> common.objects.MilestoneBar | None:
        for bar_object in relevant_bars:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            if (
                True
                and self.is_potential_starting_bar(
                    bar_object=bar_object
                )
                and (
                    not self.is_potential_starting_bar(
                        bar_object=previous_bar,
                    ) if previous_bar is not None else True
                )
                and max(
                    [
                        bar_obj.high
                        for bar_obj in relevant_bars[:10]
                    ]
                ) == bar_object.high
            ):
                return common.objects.MilestoneBar(
                    index=bar_object.index,
                    bar_object=bar_object,
                    bar_type=common.objects.MilestoneType.STARTING_BAR,
                    bar_time=bar_object.bar_time,
                    timeframe=bar_object.timeframe,
                )

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
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
        previous_day = relevant_bars[0]
        previous_day_looks_good = (
            True
            and previous_day.close > previous_day.ema_9
            and previous_day.close > previous_day.ema_20
            and previous_day.high > previous_day.vwap
            and current_bar.low > previous_day.low
        )

        current_bar_is_strong = (
            True
            and current_bar.close > current_bar.open_value
            and current_bar.close > current_bar.ema_9
            and current_bar.close > current_bar.ema_20
            and current_bar.histogram > 0
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
