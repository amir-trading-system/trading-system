import common
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_is_not_the_volume_weakest_since_top_bar"
    is_base_evidence = True

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[1:milestones.top_bar.index+1]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        lowest_volume_bar_since_top = min(
            relevant_bars,
            key=lambda bar_object: bar_object.volume
        )

        current_bar_is_not_the_volume_weakest_since_top_bar = current_bar.volume > lowest_volume_bar_since_top.volume
        if not current_bar_is_not_the_volume_weakest_since_top_bar:
            current_bar_is_not_the_volume_weakest_since_top_bar = current_bar.volume/milestones.top_bar.bar_object.volume > 0.6

        return common.objects.EvidenceResponse(
            result=current_bar_is_not_the_volume_weakest_since_top_bar,
            reason=""
            if current_bar_is_not_the_volume_weakest_since_top_bar
            else f"Current bar has the smallest amount of volume since top. Volume: {current_bar.volume}",
        )
