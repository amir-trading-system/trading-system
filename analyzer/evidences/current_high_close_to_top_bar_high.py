from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_high_close_to_top_bar_high"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        base_condition = current_bar.high/milestones.top_bar.bar_object.high >= 0.99
        any_other_bar_has_similar_condition = any(
            bar_object
            for bar_object in stock.bars[1:milestones.starting_bar.index]
            if bar_object.close > current_bar.close
        )

        current_high_close_to_top_bar_high = (
            True
            and base_condition
            and not any_other_bar_has_similar_condition
        )

        return objects.EvidenceResponse(
            result=current_high_close_to_top_bar_high,
            reason=""
            if current_high_close_to_top_bar_high
            else f"Current high: {current_bar.high} is not close or not the only one who close to top bar high: {milestones.top_bar.bar_object.high}",
        )
