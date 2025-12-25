from tws import objects as tws_objects

from analyzer import objects

class Evidence:
    name: str = ""

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        raise NotImplementedError()
