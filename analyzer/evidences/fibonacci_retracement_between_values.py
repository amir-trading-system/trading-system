from tws import objects as tws_objects

from analyzer import objects
from . import _evidence
from . import fibonacci_retracement

class Evidence(
    _evidence.Evidence,
):
    name = "fibonacci_retracement_between_values"

    def find_evidence(
        self,
        stock: tws_objects.Stock,
        milestones: objects.Milestones,
        current_bar: tws_objects.BarData,
    ) -> objects.EvidenceResponse:
        fibonacci_retracement_evidence = fibonacci_retracement.Evidence()
        fibonacci_retracement_result = fibonacci_retracement_evidence.find_evidence(
            stock=stock,
            milestones=milestones,
            current_bar=current_bar,
        )

        retracement = float(fibonacci_retracement_result.value)

        retracement_between_values = 0.3 <= retracement <= 0.72

        return objects.EvidenceResponse(
            result=retracement_between_values,
            reason=""
            if retracement_between_values
            else f"Retracement is: {retracement}, not between expected values",
        )
