from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_comes_after_healthy_retracement"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        current_bar_comes_after_healthy_retracement = True
        negative_volume_goes_down = True
        has_fake_top_since_top_index = False

        for bar_object in stock.bars[1:milestones.top_bar.index-1]:
            previous_bar = stock.bars[bar_object.index+1]
            if bar_object.ema_9 < previous_bar.ema_9:
                current_bar_comes_after_healthy_retracement = False

            if (
                True
                and bar_object.close < bar_object.open_value
                and previous_bar.volume/bar_object.volume < 0.9
                and bar_object.is_after_market_open
            ):
                negative_volume_goes_down = False
                break

            next_bar_index = bar_object.index-1
            if next_bar_index <= 0:
                break

            next_bar = stock.bars[next_bar_index]
            if (
                True
                and bar_object.high > previous_bar.high
                and bar_object.high > next_bar.high
                and bar_object.volume > previous_bar.volume
                and bar_object.volume > next_bar.volume
            ):
                has_fake_top_since_top_index = any(
                    b_object
                    for b_object in stock.bars[current_bar.index:next_bar_index]
                    if b_object.histogram < stock.bars[b_object.index+1].histogram
                    and b_object.index+1 < bar_object.index
                )
                if has_fake_top_since_top_index:
                    break

        result = (
            True
            and current_bar_comes_after_healthy_retracement
            and negative_volume_goes_down
            and not has_fake_top_since_top_index
        )

        return objects.EvidenceResponse(
            result=result,
            reason=""
            if result
            else "Current bar comes after unhealthy retracement",
        )
