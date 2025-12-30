from analyzer import objects
from tws import objects as tws_objects

from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "volume_sum_is_positive"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.starting_bar.index+1]
        if len(relevant_bars) == 0:
            return objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        positive_volume_sum = 0.0
        negative_volume_sum = 0.0
        for bar_object in relevant_bars:
            if bar_object.close > bar_object.open_value:
                positive_volume_sum += bar_object.volume
            else:
                negative_volume_sum += bar_object.volume

        volume_sum_is_positive = positive_volume_sum > negative_volume_sum

        return objects.EvidenceResponse(
            result=volume_sum_is_positive,
            reason=""
            if volume_sum_is_positive
            else "Volume is not positive in total",
        )
