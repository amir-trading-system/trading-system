import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "most_of_current_bar_is_above_9_ema"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        most_of_current_bar_is_above_9_ema = (
            True
            and (
                current_bar.index > current_bar.ema_9
                or (
                    current_bar.high - current_bar.open_value > 0
                    and (current_bar.ema_9 - current_bar.open_value)/(current_bar.high - current_bar.open_value) <= 0.2
                )
            )
        )

        previous_bar = milestones.previous_bar.bar_object
        low_close_to_9_ema = (
            True
            and (
                (
                   current_bar.ema_9/current_bar.low >= 0.88
                   and current_bar.low - current_bar.ema_9 < previous_bar.low - previous_bar.ema_9
                )
                or current_bar.ema_9/current_bar.low >= 0.95
            )
        )

        result = (
            True
            and most_of_current_bar_is_above_9_ema
            and low_close_to_9_ema
        )

        return common.objects.EvidenceResponse(
            result=result,
            reason=""
            if result
            else "Most of current body is not above 9 ema or low is not close to 9 ema",
        )
