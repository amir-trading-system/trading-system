import datetime
import enum

from tws import objects as tws_objects

class MilestoneType(enum.Enum):
    STARTING_BAR = 1
    TOP_BAR = 2
    LOWEST_BAR = 3

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
        are_valid: bool,
    ):
        self.starting_bar = starting_bar
        self.top_bar = top_bar
        self.lowest_low_bar = lowest_low_bar
        self.are_valid = are_valid

class AnalyzerResponse:
    def __init__(
        self,
        result: bool,
        reason: str = None,
    ):
        self.result = result
        self.reason = reason
