from tws import objects as tws_objects

from analyzer import objects

class Analyzer:
    name: str = ""

    def analyze(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
    ) -> objects.AnalyzerResponse:
        raise NotImplementedError()
