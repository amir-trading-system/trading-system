from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "retracement_occured_since_top_bar"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        has_at_least_one_retracement_bar = any(
            bar_object
            for bar_object in stock.bars[:milestones.top_bar.index-1]
            if bar_object.low < stock.bars[bar_object.index+1].low
        )
        retracement_occured_since_top_bar = has_at_least_one_retracement_bar or milestones.top_bar.index <= 2

        return objects.EvidenceResponse(
            result=retracement_occured_since_top_bar,
            reason=""
            if retracement_occured_since_top_bar
            else "No real retracement occured since top bar",
        )
