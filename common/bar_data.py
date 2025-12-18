class BarData:
    def __init__(
        self,
        open_value: float,
        close: float,
        high: float,
        low: float,
        volume: float,
        volume_average: float,
        vwap: float,
        ema_9: float,
        ema_20: float,
        histogram: float,
        macd: float,
        signal_line: float,
        timeframe: int,
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
