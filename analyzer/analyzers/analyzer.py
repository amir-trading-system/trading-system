from tws import objects as tws_objects

from . import objects

class Analyzer:
    def analyze(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
    ) -> objects.AnalyzerResponse:
        raise NotImplementedError()
