import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "most_of_volume_does_not_stuck_between_top_index_to_current"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        relevant_bars_from_start = stock.bars[:milestones.starting_bar.index+1]
        if len(relevant_bars_from_start) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        all_volume_since_start_bar = sum(
            [
                bar_object.volume
                for bar_object in relevant_bars_from_start
            ]
        )

        all_volume_since_top_bar = sum(
            [
                bar_object.volume
                for bar_object in stock.bars[:milestones.top_bar.index+1]
            ]
        )

        volume_percentage_from_top = all_volume_since_top_bar/all_volume_since_start_bar
        bars_percentage_from_top = milestones.top_bar.index/milestones.starting_bar.index

        most_of_volume_does_not_stuck_between_top_index_to_current = not bars_percentage_from_top/volume_percentage_from_top <= 0.9

        return common.objects.EvidenceResponse(
            result=most_of_volume_does_not_stuck_between_top_index_to_current,
            reason=""
            if most_of_volume_does_not_stuck_between_top_index_to_current
            else "Most of volume stuck between top to current",
        )
