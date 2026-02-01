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
        is_retro: bool,
    ) -> common.objects.EvidenceResponse:
        raise NotImplementedError()
