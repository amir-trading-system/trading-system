import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_day_continues_last_success_day"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:3]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        current_day = current_bar
        second_day = relevant_bars[1]
        third_day = relevant_bars[2]

        second_day_price_movememnt = second_day.high - second_day.low
        third_day_price_movememnt = third_day.high - third_day.low

        second_day_starts_positive_movement = (
            True
            and second_day.close > second_day.open_value
            and second_day.volume > second_day.volume_average
            and (second_day.close - second_day.open_value)/(second_day.high - second_day.low) > 0.5
            and second_day.close > second_day.ema_9
            and second_day.close > second_day.ema_20
            and second_day.close > second_day.vwap
            and second_day.close > third_day.high
        )

        third_day_does_not_moving_much = (
            True
            and third_day.volume/second_day.volume < 0.2
            and third_day.histogram < second_day.histogram
            and third_day_price_movememnt/second_day_price_movememnt < 0.1
        )

        current_day_breaks_highest_high = (
            True
            and current_day.close > current_day.open_value
            and (current_day.close - current_day.open_value)/(current_day.high - current_day.low) > 0.5
            and current_day.volume > current_day.volume_average
            and current_day.close > current_day.ema_9
            and current_day.close > current_day.ema_20
            and current_day.close > current_day.vwap
            and current_day.close > second_day.high
        )

        current_day_continues_last_success_day = (
            True
            and second_day_starts_positive_movement
            and third_day_does_not_moving_much
            and current_day_breaks_highest_high
        )

        return common.objects.EvidenceResponse(
            result=current_day_continues_last_success_day,
            reason=""
            if current_day_continues_last_success_day
            else "Current day does not continues last success day",
        )
