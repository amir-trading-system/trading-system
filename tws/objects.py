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
