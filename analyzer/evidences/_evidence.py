import common

class Evidence:
    name: str = ""
    must_to_be_true: bool = False
    is_base_evidence: bool = False

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
    ) -> common.objects.EvidenceResponse:
        raise NotImplementedError()
