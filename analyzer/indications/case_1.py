from analyzer.analyzers._analyzer import Analyzer
from analyzer.analyzers import fibonacci_retracement

from . import indication

class Indicator(
    indication.Indication,
):
    analyzers: list[Analyzer] = [
        fibonacci_retracement.Analyzer,
    ]
    name = "case_1"
