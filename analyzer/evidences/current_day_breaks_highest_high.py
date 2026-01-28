import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_day_breaks_highest_high"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:4]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        third_day_bar = relevant_bars[2]
        second_day_bar = relevant_bars[1]
        forth_day_bar = stock.previous_bar(
            bar_object=third_day_bar,
        )
        if not forth_day_bar:
            return common.objects.EvidenceResponse(
                result=False,
                reason="No previous bar for indication",
            )

        third_day_starts_positive_trend = (
            True
            and third_day_bar.low > forth_day_bar.high
            and third_day_bar.high > third_day_bar.ema_9
            and third_day_bar.high > third_day_bar.ema_20
            and third_day_bar.volume > third_day_bar.volume_average
            and forth_day_bar.high < third_day_bar.high > second_day_bar.high
        )

        second_day_has_small_retracement = (
            True
            and second_day_bar.high < third_day_bar.high
            and second_day_bar.low >= third_day_bar.low
        )

        current_day_is_highgest = (
            True
            and current_bar.high > third_day_bar.high
            and current_bar.close > current_bar.open_value
        )

        current_day_breaks_highest_high = (
            True
            and third_day_starts_positive_trend
            and second_day_has_small_retracement
            and current_day_is_highgest
        )

        return common.objects.EvidenceResponse(
            result=current_day_breaks_highest_high,
            reason=""
            if current_day_breaks_highest_high
            else "Current day does not break highest high",
        )
