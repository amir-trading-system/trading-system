import common
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "most_volatile_bar_from_top_is_strong"
    is_base_evidence = True

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        relevant_bars = stock.bars[1:milestones.top_bar.index]
        if len(relevant_bars) == 0:
            return common.objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        most_volatile_bar = max(
            relevant_bars,
            key=lambda bar_object: bar_object.volume
        )

        most_volatile_bar_from_top_is_strong = (
            True
            and most_volatile_bar.close > most_volatile_bar.open_value
            or (
                True
                and most_volatile_bar.high - most_volatile_bar.low > 0
                and most_volatile_bar.close < most_volatile_bar.open_value
                and most_volatile_bar.low < most_volatile_bar.close
                and most_volatile_bar.high > most_volatile_bar.open_value
                and (most_volatile_bar.open_value - most_volatile_bar.close)/(most_volatile_bar.high - most_volatile_bar.low) < 0.7
            )
        )

        if (
            True
            and not most_volatile_bar_from_top_is_strong
            and most_volatile_bar.close < most_volatile_bar.open_value
            and milestones.top_bar.bar_object.high - milestones.top_bar.bar_object.low > 0
            and (most_volatile_bar.high - most_volatile_bar.low)/(milestones.top_bar.bar_object.high - milestones.top_bar.bar_object.low) < 0.7
        ):
            most_volatile_bar_from_top_is_strong = True

        if not most_volatile_bar_from_top_is_strong and milestones.top_bar.index == 2:
            most_volatile_bar_from_top_is_strong = True

        if (
            True
            and not most_volatile_bar_from_top_is_strong
            and milestones.top_bar.bar_object.volume > most_volatile_bar.volume * 1.2
            and current_bar.volume > most_volatile_bar.volume
            and current_bar.high > most_volatile_bar.high
        ):
            most_volatile_bar_from_top_is_strong = True

        return common.objects.EvidenceResponse(
            result=most_volatile_bar_from_top_is_strong,
            reason=""
            if most_volatile_bar_from_top_is_strong
            else f"Most volatile bar from top is weak. Index: {most_volatile_bar.index}",
        )
