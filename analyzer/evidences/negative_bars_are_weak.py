import common
from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "negative_bars_are_weak"

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.top_bar.index]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        negative_bars_are_weak = True
        for bar_object in relevant_bars:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            if not previous_bar:
                continue

            if (
                True
                and bar_object.close < bar_object.open_value
                and previous_bar.close > previous_bar.open_value
                and bar_object.volume > previous_bar.volume
                and bar_object.volume > bar_object.volume_average
            ):
                negative_bars_are_weak = False
                break

            if (
                True
                and bar_object.close < bar_object.open_value
                and bar_object.volume > bar_object.volume_average
                and bar_object.low/bar_object.close > 0.95
                and bar_object.high - bar_object.low > 0
                and (bar_object.high - bar_object.open_value)/(bar_object.high - bar_object.low) >= 0.4
            ):
                negative_bars_are_weak = False
                break

        return common.objects.EvidenceResponse(
            result=negative_bars_are_weak,
            reason=""
            if negative_bars_are_weak
            else "Negative bars are strong",
        )
