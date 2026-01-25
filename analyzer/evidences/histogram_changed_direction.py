import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "histogram_changed_direction"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:current_bar.index+3]
        if len(relevant_bars) < 3:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        histogram_changed_direction = (
            True
            and current_bar.histogram > milestones.previous_bar.bar_object.histogram
            and milestones.previous_bar.bar_object.histogram < relevant_bars[2].histogram
        )

        return common.objects.EvidenceResponse(
            result=histogram_changed_direction,
            reason=""
            if histogram_changed_direction
            else "histogram didnt change direction",
        )
