from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "most_volatile_bar_from_top_is_strong"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        relevant_bars = stock.bars[1:milestones.top_bar.index-1]
        if len(relevant_bars) == 0:
            return objects.EvidenceResponse(
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

        return objects.EvidenceResponse(
            result=most_volatile_bar_from_top_is_strong,
            reason=""
            if most_volatile_bar_from_top_is_strong
            else f"Most volatile bar from top is weak. Index: {most_volatile_bar.index}",
        )
