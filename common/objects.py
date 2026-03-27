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
        volume_average_last_3: float = 0.0,
        volume_average_last_10: float = 0.0,
        ema_9: float = 0.0,
        ema_20: float = 0.0,
        ema_12: float = 0.0,
        ema_26: float = 0.0,
        histogram: float = 0.0,
        macd: float = 0.0,
        signal_line: float = 0.0,
        index: int = 0,
        is_after_market_open: bool = None,
        ready_to_analyze: bool = False,
        price_movement_statistics: dict[str, float] = {},
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
        self.volume_average_last_3 = volume_average_last_3
        self.volume_average_last_10 = volume_average_last_10
        self.vwap = vwap
        self.ema_9 = ema_9
        self.ema_20 = ema_20
        self.ema_12 = ema_12
        self.ema_26 = ema_26
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
        self.price_movement_statistics = price_movement_statistics
        self.is_opening_bar = bar_time == datetime.datetime(
            year=bar_time.year,
            month=bar_time.month,
            day=bar_time.day,
            hour=9,
            minute=30,
        )

    @property
    def body_percentage(
        self,
    ) -> float:
        if self.high - self.low <= 0.0:
            return 0.0

        return abs(self.close - self.open_value)/(self.high - self.low)

    @property
    def bar_up_percentage(
        self,
    ) -> float:
        return (self.close - self.open_value)/self.open_value

    @property
    def bar_wick_percentage(
        self,
    ) -> float:
        if self.high - self.low <= 0.0:
            return 0.0

        return (self.high - self.close)/(self.high - self.low)

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
        pre_market_one_minute_highest_high_bar: BarData = None,
        post_pre_market_volume_sum: float = 0.0,
        last_lowest_low_bar: BarData = None,
        one_minute_request_id: int = None,
        day_request_id: int = None,
        total_volume: float = 0.0,
        total_price_volume: float = 0.0,
        volume_sum_since_4_am_today: float = 0.0,
        volume_sum_since_market_open: float = 0.0,
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
        self.pre_market_one_minute_highest_high_bar = pre_market_one_minute_highest_high_bar
        self.post_pre_market_volume_sum = post_pre_market_volume_sum
        self.volume_sum_since_4_am_today = volume_sum_since_4_am_today
        self.volume_sum_since_market_open = volume_sum_since_market_open
        self.last_lowest_low_bar = last_lowest_low_bar
        self.one_minute_request_id = one_minute_request_id
        self.day_request_id = day_request_id
        self.total_volume = total_volume
        self.total_price_volume = total_price_volume

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
        for i, bar_object in enumerate(self.bars):
            bar_object.index = i

    def bar_is_the_first_one_in_trend(
        self,
        bar_object: BarData,
        relevant_bars: list[BarData],
    ):
        last_10_bars = relevant_bars[bar_object.index+1:bar_object.index+11]
        last_5_bars = relevant_bars[bar_object.index+1:bar_object.index+6]
        return (
            True
            and bar_object.volume > 0.0
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

    def is_worth_to_monitor(
        self,
    ):
        self.arrange_data_for_analysis()
        return (
            True
            and len(self.bars) > 0
            and self.is_day_timeframe()
            and self.bars[0].volume >= 500000
        )

    def _filter_ignored_bars(
        self,
        bars: list[BarData],
    ):
        relevant_bars: list[BarData] = []
        for i, bar_object in enumerate(bars):
            if (
                bar_object.bar_time.hour == 8
                and bar_object.bar_time.minute == 0
                and i+1 < len(bars)-1
            ):
                bar_before = bars[i-1]
                bar_after = bars[i+1]
                if (
                    bar_object.volume > bar_before.volume * 10
                    and bar_object.volume > bar_after.volume * 10
                    and bar_object.high - bar_object.low > (bar_before.high - bar_before.low) * 10
                    and bar_object.high - bar_object.low > (bar_after.high - bar_after.low) * 10
                ):
                    continue

            relevant_bars.append(bar_object)

        return relevant_bars

    def enrich_bar(
        self,
        current_bar: BarData,
    ) -> BarData:
        self.bars = self._filter_ignored_bars(
            bars=self.bars if len(self.bars) > 0 else [],
        )
        current_bar.index = 0

        if len(self.bars) == 0:
            previous_ema_9 = 0.0
            previous_ema_12 = 0.0
            previous_ema_20 = 0.0
            previous_ema_26 = 0.0
        else:
            previous_bar = None
            if self.bars[0].bar_time < current_bar.bar_time or len(self.bars) == 1:
                previous_bar = self.bars[0]
            else:
                previous_bar = self.bars[1]

            previous_ema_9 = previous_bar.ema_9
            previous_ema_20 = previous_bar.ema_20
            previous_ema_12 = previous_bar.ema_12
            previous_ema_26 = previous_bar.ema_26

        current_length = len(self.bars)
        current_bar.ema_9 = self.calculate_ema(
            period=9,
            close=current_bar.close,
            previous_ema=previous_ema_9,
            current_length=current_length,
        )
        current_bar.ema_20 = self.calculate_ema(
            period=20,
            close=current_bar.close,
            previous_ema=previous_ema_20,
            current_length=current_length,
        )
        current_bar.ema_12 = self.calculate_ema(
            period=12,
            close=current_bar.close,
            previous_ema=previous_ema_12,
            current_length=current_length,
        )
        current_bar.ema_26 = self.calculate_ema(
            period=26,
            close=current_bar.close,
            previous_ema=previous_ema_26,
            current_length=current_length,
        )
        current_bar.volume_average = self.calculate_volume_average(
            current_bar=current_bar,
            period=20,
        )
        current_bar.volume_average_last_3 = self.calculate_volume_average(
            current_bar=current_bar,
            period=3,
        )
        current_bar.volume_average_last_10 = self.calculate_volume_average(
            current_bar=current_bar,
            period=10,
        )
        self.calculate_vwap(
            current_bar=current_bar,
        )
        self.calculate_macd(
            current_bar=current_bar,
            previous_ema_12=previous_ema_12,
            previous_ema_26=previous_ema_26,
            current_length=current_length,
        )

        return current_bar

    def calculate_ema(
        self,
        period: int,
        close: float,
        previous_ema: float,
        current_length: int,
    ):
        ema_result = 0.0
        if current_length+1 < period:
            return ema_result
        if current_length+1 == period:
            sum_close = sum(
                bar_object.close
                for bar_object in self.bars
                if bar_object.index <= period
            ) + close

            return sum_close / period

        alpha = 2/(period+1)
        ema_result = alpha * close + (1-alpha) * previous_ema

        return ema_result

    def calculate_volume_average(
        self,
        current_bar: BarData,
        period: int = 20,
    ) -> float:
        sorted_bars = sorted(
            self.bars,
            key=lambda bar_object: bar_object.bar_time,
            reverse=True,
        )
        volume_sum = current_bar.volume
        for bar_object in sorted_bars[:period-1]:
            volume_sum += bar_object.volume

        return volume_sum/period

    def calculate_vwap(
        self,
        current_bar: BarData,
    ):
        hlc3 = (current_bar.high + current_bar.low + current_bar.close) / 3
        if current_bar.timeframe_type == TimeframeType.DAY:
            self.total_volume = current_bar.volume
            self.total_price_volume = hlc3 * current_bar.volume
        else:
            self.total_volume += current_bar.volume
            self.total_price_volume += hlc3 * current_bar.volume

        if self.total_volume > 0:
            current_bar.vwap = self.total_price_volume / self.total_volume

    def calculate_macd(
        self,
        current_bar: BarData,
        previous_ema_12: float,
        previous_ema_26: float,
        current_length: int,
    ):
        ema_12 = self.calculate_ema(
            period=12,
            close=current_bar.close,
            previous_ema=previous_ema_12,
            current_length=current_length,
        )
        ema_26 = self.calculate_ema(
            period=26,
            close=current_bar.close,
            previous_ema=previous_ema_26,
            current_length=current_length,
        )

        current_bar.macd = ema_12 - ema_26
        current_bar.signal_line = self.calculate_ema(
            period=9,
            close=current_bar.macd,
            previous_ema=previous_ema_12-previous_ema_26,
            current_length=current_length,
        )
        current_bar.histogram = current_bar.macd - current_bar.signal_line

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

class Score:
    def __init__(
        self,
        score: float,
        probability: float,
        threshold: float,
        should_take_trade: bool,
    ):
        self.score = score
        self.probability = probability
        self.threshold = threshold
        self.should_take_trade = should_take_trade

class SymbolTest:
    def __init__(
        self,
        name: str,
        datetime_str: str,
        is_positive: bool = False,
    ):
        self.name = name
        self.date_time = datetime.datetime.strptime(datetime_str, "%m.%d.%yT%H:%M:%S")
        self.is_positive = is_positive
