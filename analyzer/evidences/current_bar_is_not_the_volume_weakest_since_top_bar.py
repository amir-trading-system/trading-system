from tws import objects as tws_objects

from analyzer import objects
from . import _evidence

class Evidence(
    _evidence.Evidence,
):
    name = "current_bar_is_not_the_volume_weakest_since_top_bar"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        lowest_volume_bar_since_top = min(
            stock.bars[1:milestones.top_bar.index],
            key=lambda bar_object: bar_object.volume
        )

        current_bar_is_not_the_volume_weakest_since_top_bar = current_bar.volume > lowest_volume_bar_since_top.volume
        if not current_bar_is_not_the_volume_weakest_since_top_bar:
            current_bar_is_not_the_volume_weakest_since_top_bar = current_bar.volume/milestones.top_bar.bar_object.volume > 0.6

        return objects.EvidenceResponse(
            result=current_bar_is_not_the_volume_weakest_since_top_bar,
            reason=""
            if current_bar_is_not_the_volume_weakest_since_top_bar
            else f"Current bar has the smallest amount of volume since top. Volume: {current_bar.volume}",
        )
