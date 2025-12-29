import datetime

class BarData:
    def __init__(
        self,
        open_value: float,
        close: float,
        high: float,
        low: float,
        volume: float,
        vwap: float,
        bar_time: datetime.datetime,
        volume_average: float = None,
        ema_9: float = None,
        ema_20: float = None,
        histogram: float = None,
        macd: float = None,
        signal_line: float = None,
        index: int = None,
        is_after_market_open: bool = None,
    ):
        self.open_value = open_value
        self.close = close
        self.high = high
        self.low = low
        self.volume = float(volume)
        self.volume_average = volume_average
        self.vwap = float(vwap)
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

class Stock:
    def __init__(
        self,
        symbol_name: str,
        bars: list[BarData],
        timeframe: int
    ):
        self.symbol_name = symbol_name
        self.bars = bars
        self.timeframe = timeframe

    def previous_bar(
        self,
        bar_object: BarData,
    ) -> BarData:
        previous_bar_index = bar_object.index + 1
        if previous_bar_index < len(self.bars):
            return self.bars[previous_bar_index]

        return None

    def next_bar(
        self,
        bar_object: BarData,
    ) -> BarData:
        next_bar_index = bar_object.index - 1
        if next_bar_index > 0:
            return self.bars[next_bar_index]

        return None
