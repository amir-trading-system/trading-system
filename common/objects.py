import datetime
import enum
import queue


class BarData:
    def __init__(
        self,
        symbol: str,
        timeframe: int,
        open_value: float,
        close: float,
        high: float,
        low: float,
        volume: float,
        bar_time: datetime.datetime,
        vwap: float = 0.0,
        volume_average: float = 0.0,
        ema_9: float = 0.0,
        ema_20: float = 0.0,
        histogram: float = 0.0,
        macd: float = 0.0,
        signal_line: float = 0.0,
        index: int = 0,
        is_after_market_open: bool = None,
        ready_to_analyze: bool = False,
        has_indication: bool = False,
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.open_value = open_value
        self.close = close
        self.high = high
        self.low = low
        self.volume = float(volume)
        self.volume_average = volume_average
        self.vwap = vwap
        self.ema_9 = ema_9
        self.ema_20 = ema_20
        self.histogram = histogram
        self.macd = macd
        self.signal_line = signal_line
        self.bar_time = bar_time
        self.index = index
        self.is_after_market_open = is_after_market_open if is_after_market_open is not None else bar_time >= datetime.datetime(
            year=bar_time.year,
            month=bar_time.month,
            day=bar_time.day,
            hour=9,
            minute=30,
        )
        self.ready_to_analyze = ready_to_analyze
        self.has_indication = has_indication

class Stock:
    def __init__(
        self,
        symbol_name: str,
        bars: list[BarData],
        timeframe: int,
        ready_to_confirm: bool = False,
        one_minute_bars_queue: queue.Queue[BarData] = None,
    ):
        self.symbol_name = symbol_name
        self.bars = bars
        self.timeframe = timeframe
        self.ready_to_confirm = ready_to_confirm
        self.one_minute_bars_queue = one_minute_bars_queue

    def previous_bar(
        self,
        bar_object: BarData,
    ) -> BarData | None:
        previous_bar_index = bar_object.index + 1
        if previous_bar_index < len(self.bars):
            return self.bars[previous_bar_index]

        return None

    def next_bar(
        self,
        bar_object: BarData,
    ) -> BarData | None:
        next_bar_index = bar_object.index - 1
        if next_bar_index > 0:
            return self.bars[next_bar_index]

        return None

class IbAPIRequest:
    def __init__(
        self,
        request_id: int,
        symbol: str,
        timeframe: int,
    ):
        self.request_id = request_id
        self.symbol = symbol
        self.timeframe = timeframe

class Order:
    def __init__(
        self,
        symbol: str,
        action: str,
        status: str,
    ):
        self.symbol = symbol
        self.action = action
        self.status = status

class MilestoneType(enum.Enum):
    STARTING_BAR = 1
    TOP_BAR = 2
    LOWEST_BAR = 3
    PREVIOUS_BAR = 4

class MilestoneBar:
    def __init__(
        self,
        index: int,
        bar_object: BarData = None,
        bar_type: MilestoneType = None,
        bar_time: datetime.datetime = None,
        timeframe: int = 0,
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
        previous_bar: MilestoneBar = None,
        fibonacci_retracement: float = 0.0,
        retracement_indexes: list[int] = [],
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
        reason: str | None = None,
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
