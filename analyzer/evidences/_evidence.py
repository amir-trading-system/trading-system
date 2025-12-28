from tws import objects as tws_objects

from analyzer import objects

class Evidence:
    name: str = ""
    must_to_be_true: bool = False
    is_base_evidence: bool = False

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        raise NotImplementedError()
