import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "volume_sum_is_positive"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.starting_bar.index+1]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
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

        return common.objects.EvidenceResponse(
            result=volume_sum_is_positive,
            reason=""
            if volume_sum_is_positive
            else "Volume is not positive in total",
        )
