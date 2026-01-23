import datetime
import enum

from tws import objects as tws_objects

class MilestoneType(enum.Enum):
    STARTING_BAR = 1
    TOP_BAR = 2
    LOWEST_BAR = 3
    PREVIOUS_BAR = 4

class MilestoneBar:
    def __init__(
        self,
        index: int,
        bar_object: tws_objects.BarData = None,
        bar_type: MilestoneType = None,
        bar_time: datetime.datetime = None,
        timeframe: int = None,
    ):
        self.index = index
        self.bar_object = bar_object
        self.type = bar_type
        self.bar_time = bar_time
        self.timeframe = timeframe

class Milestones:
    def __init__(
        self,
        starting_bar: MilestoneBar,
        top_bar: MilestoneBar,
        lowest_low_bar: MilestoneBar,
        previous_bar: MilestoneBar,
        are_valid: bool,
        fibonacci_retracement: float = None,
        retracement_indexes: list[int] = None,
    ):
        self.starting_bar = starting_bar
        self.top_bar = top_bar
        self.lowest_low_bar = lowest_low_bar
        self.previous_bar = previous_bar
        self.are_valid = are_valid
        self.fibonacci_retracement = fibonacci_retracement
        self.retracement_indexes = retracement_indexes

class EvidenceResponse:
    def __init__(
        self,
        result: bool,
        reason: str = None,
        value: any = None,
    ):
        self.result = result
        self.reason = reason
        self.value = value

class IndicatorResponse:
    def __init__(
        self,
        success_count: int,
        success_rate: float,
        result: bool,
        failed_base_evidences_count: int,
    ):
        self.success_rate = success_rate
        self.success_count = success_count
        self.result = result
        self.failed_base_evidences_count = failed_base_evidences_count
