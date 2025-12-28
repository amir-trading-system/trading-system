from analyzer import objects
from tws import objects as tws_objects

from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "at_least_one_bar_was_closed_to_9_ema_since_start"
    must_to_be_true = True
    is_base_evidence = True

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        relevant_bars = stock.bars[:milestones.starting_bar.index]
        if len(relevant_bars) == 0:
            return objects.EvidenceResponse(
                result=False,
                reason="no bars to indicate",
            )

        at_least_one_bar_was_closed_to_9_ema_since_start = any(
            bar_object
            for bar_object in relevant_bars
            if (
                (
                    bar_object.low < bar_object.open_value
                    and bar_object.low < bar_object.ema_9
                    and bar_object.open_value > bar_object.ema_9
                )
                or (
                    bar_object.low < bar_object.open_value
                    and bar_object.low >= bar_object.ema_9
                    and bar_object.open_value > bar_object.ema_9
                    and bar_object.low - bar_object.ema_9 <= 0.1
                )
            )
        )

        return objects.EvidenceResponse(
            result=at_least_one_bar_was_closed_to_9_ema_since_start,
            reason=""
            if at_least_one_bar_was_closed_to_9_ema_since_start
            else "No bar was closed to 9 ema since start",
        )
