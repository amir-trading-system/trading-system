import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "negative_bars_volume_is_going_down"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.starting_bar.index]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        negative_bars_volume_is_going_down = True
        for bar_object in relevant_bars:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            if not previous_bar:
                continue

            if (
                True
                and bar_object.close < bar_object.open_value
                and previous_bar.close < previous_bar.open_value
                and bar_object.volume >= previous_bar.volume
            ):
                negative_bars_volume_is_going_down = False
                break

        return common.objects.EvidenceResponse(
            result=negative_bars_volume_is_going_down,
            reason=""
            if negative_bars_volume_is_going_down
            else "Negative bars is going up",
        )
