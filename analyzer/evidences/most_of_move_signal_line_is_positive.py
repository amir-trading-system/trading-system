from analyzer import objects
from tws import objects as tws_objects

from . import _evidence


class Evidence(
    _evidence.Evidence,
):
    name = "most_of_move_signal_line_is_positive"
    must_to_be_true = True
    is_base_evidence = True

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

        bars_with_positive_signal_line = 0
        bars_with_negative_signal_line = 0
        for bar_object in relevant_bars:
            if bar_object.signal_line > 0:
                bars_with_positive_signal_line += 1
            else:
                bars_with_negative_signal_line += 1

        most_of_move_signal_line_is_positive = bars_with_positive_signal_line > bars_with_negative_signal_line

        return objects.EvidenceResponse(
            result=most_of_move_signal_line_is_positive,
            reason=""
            if most_of_move_signal_line_is_positive
            else "Most of bars has negative signal line",
        )
