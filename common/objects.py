import datetime
import enum
import inspect
import queue


class TimeframeType(enum.Enum):
    MINUTE = 1
    DAY = 2


class TimeframeInput:
    def __init__(
        self,
        timeframe: int,
        timeframe_type: TimeframeType,
    ):
        self.timeframe = timeframe
        self.timeframe_type = timeframe_type

class BarData:
    def __init__(
        self,
        symbol: str,
        timeframe: int,
        timeframe_type: TimeframeType,
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
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.timeframe_type = timeframe_type
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
        self.is_after_market_open = is_after_market_open if is_after_market_open is not None else bar_time > datetime.datetime(
            year=bar_time.year,
            month=bar_time.month,
            day=bar_time.day,
            hour=9,
            minute=30,
        ) or timeframe_type == TimeframeType.DAY
        self.ready_to_analyze = ready_to_analyze

    def has_strong_rejection(
        self,
    ) -> bool:
        return (
            True
            and self.close > self.open_value
            and self.volume > self.volume_average
            and self.high > self.ema_9
            and self.high > self.ema_20
            and self.volume > 2000000
            and (self.close - self.open_value)/(self.high - self.low) < 0.5
        )

    def generate_unique_key(
        self,
    ) -> str:
        return f"{self.symbol}-{self.bar_time}"

    @classmethod
    def field_names(
        cls,
    ):
        return list(inspect.signature(cls).parameters.keys())

class Stock:
    def __init__(
        self,
        request_id: int,
        symbol_name: str,
        bars: list[BarData],
        timeframe: int,
        timeframe_type: TimeframeType,
        specific_bar_time: datetime.datetime,
        one_minute_bars_queue: queue.Queue[BarData] = None,
        finished_collection: bool = False,
        finished_analyze: bool = False,
        resistance_levels: list[BarData] = [],
        last_post_pre_one_minute_highest_high: float = 0.0,
        post_pre_market_volume_sum: float = 0.0,
        should_monitor: bool = True,
    ):
        self.request_id = request_id
        self.symbol_name = symbol_name
        self.bars = bars
        self.timeframe = timeframe
        self.timeframe_type = timeframe_type
        self.one_minute_bars_queue = one_minute_bars_queue
        self.specific_bar_time = specific_bar_time
        self.finished_collection = finished_collection
        self.finished_analyze = finished_analyze
        self.resistance_levels = resistance_levels
        self.last_post_pre_one_minute_highest_high = last_post_pre_one_minute_highest_high
        self.post_pre_market_volume_sum = post_pre_market_volume_sum
        self.should_monitor = should_monitor

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

    def is_one_minute_timeframe(
        self,
    ) -> bool:
        return (
            True
            and self.timeframe_type == TimeframeType.MINUTE
            and self.timeframe == 1
        )

    def is_day_timeframe(
        self,
    ) -> bool:
        return self.timeframe_type == TimeframeType.DAY

    def is_same(
        self,
        symbol: str,
        timeframe: int,
        timeframe_type: TimeframeType,
        specific_bar_time: datetime.datetime = None,
    ) -> bool:
        res = (
            True
            and self.symbol_name == symbol
            and self.timeframe == timeframe
            and self.timeframe_type == timeframe_type
        )
        if self.specific_bar_time is not None:
            res = (
                True
                and res
                and self.specific_bar_time.year == specific_bar_time.year
                and self.specific_bar_time.month == specific_bar_time.month
                and self.specific_bar_time.day == specific_bar_time.day
            )

        return res

    def arrange_data_for_analysis(
        self,
    ):
        self.bars = sorted(
            self.bars,
            key=lambda bar: bar.bar_time,
            reverse=True,
        )

    def previous_bar_is_valid(
        self,
        bar_object: BarData,
    ) -> bool:
        previous_bar = self.previous_bar(
            bar_object=bar_object,
        )
        if not previous_bar:
            return True

        if (
            True
            and previous_bar.has_strong_rejection()
            and not self.bar_is_the_first_one_in_trend(
                bar_object=previous_bar,
                relevant_bars=self.bars,
            )
        ):
            return False

        return True

    def bar_is_the_first_one_in_trend(
        self,
        bar_object: BarData,
        relevant_bars: list[BarData],
    ):
        last_10_bars = relevant_bars[bar_object.index+1:bar_object.index+11]
        last_5_bars = relevant_bars[bar_object.index+1:bar_object.index+6]
        return (
            True
            and bar_object.volume_average/bar_object.volume < 0.2
            and bar_object.high > bar_object.ema_9
            and bar_object.high > bar_object.ema_20
            and bar_object.high > bar_object.vwap
            and max(
                bar_obj.high
                for bar_obj in last_10_bars
            ) < bar_object.high
            and max(
                bar_obj.volume
                for bar_obj in last_10_bars
            ) < bar_object.volume
            and not any(
                bar_obj.volume
                for bar_obj in last_5_bars
                if bar_obj.volume/bar_object.volume > 0.2
            )
        )

class IbAPIRequest:
    def __init__(
        self,
        request_id: int,
        symbol: str,
        timeframe: int,
        timeframe_type: TimeframeType,
    ):
        self.request_id = request_id
        self.symbol = symbol
        self.timeframe = timeframe
        self.timeframe_type = timeframe_type

    def is_one_minute_timeframe(
        self,
    ) -> bool:
        return (
            True
            and self.timeframe_type == TimeframeType.MINUTE
            and self.timeframe == 1
        )

    def is_day_timeframe(
        self,
    ) -> bool:
        return self.timeframe_type == TimeframeType.DAY

    def is_same(
        self,
        symbol: str,
        timeframe: int,
        timeframe_type: TimeframeType,
    ) -> bool:
        return (
            True
            and self.symbol == symbol
            and self.timeframe == timeframe
            and self.timeframe_type == timeframe_type
        )

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
