from analyzer import objects
from tws import objects as tws_objects

from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_is_top_and_after_own_retracement"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        current_bar_is_highest = current_bar.high >= milestones.top_bar.bar_object.high
        current_bar_after_own_retracement = (
            True
            and (current_bar.open_value - current_bar.low)/(current_bar.high - current_bar.low) >= 0.18
            and (current_bar.high - current_bar.close)/(current_bar.high - current_bar.low) <= 0.2
            and current_bar.close - current_bar.open_value > current_bar.high - current_bar.close
        )
        current_bar_volume_is_higher_than_before = (
            True
            and current_bar.volume > milestones.previous_bar.bar_object.volume
            and current_bar.volume > current_bar.volume_average
        )
        ema_9_close_to_low = current_bar.ema_9/current_bar.low >= 0.98

        current_bar_is_top_and_after_own_retracement = (
            True
            and current_bar_is_highest
            and current_bar_after_own_retracement
            and current_bar_volume_is_higher_than_before
            and ema_9_close_to_low
        )


        return objects.EvidenceResponse(
            result=current_bar_is_top_and_after_own_retracement,
            reason=""
            if current_bar_is_top_and_after_own_retracement
            else "current bar dont have its own retracement",
        )
