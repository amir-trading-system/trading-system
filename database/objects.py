import datetime

class BarData:
    def __init__(
        self,
        open_value: float,
        close: float,
        high: float,
        low: float,
        volume: float,
        volume_average: float = None,
        vwap: float = None,
        ema_9: float = None,
        ema_20: float = None,
        histogram: float = None,
        macd: float = None,
        signal_line: float = None,
        timeframe: int = None,
        time: str = None,
    ):
        self.open = open_value
        self.close = close
        self.high = high
        self.low = low
        self.volume = volume
        self.volume_average = volume_average
        self.vwap = vwap
        self.ema_9 = ema_9
        self.ema_20 = ema_20
        self.histogram = histogram
        self.macd = macd
        self.signal_line = signal_line
        self.timeframe = timeframe
        self.datetime = datetime.datetime.fromtimestamp(float(time))
