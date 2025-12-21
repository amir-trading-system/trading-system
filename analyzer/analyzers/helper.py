import datetime
import enum

from tws import objects

class MilestoneType(enum.Enum):
    STARTING_BAR = 1
    TOP_BAR = 2
    LOWEST_BAR = 3

class MilestoneBar:
    def __init__(
        self,
        index: int,
        bar_object: objects.BarData = None,
        bar_type: MilestoneType = None,
        bar_time: datetime.datetime = None,
        timeframe: int = None,
    ):
        self.index = index
        self.bar_object = bar_object
        self.type = bar_type
        self.bar_time = bar_time
        self.timeframe = timeframe

class AnalyzerHelper:
    def __init__(
        self,
        stock: objects.Stock,
    ):
        self.stock = stock

    def get_strating_bar(
        self,
        current_bar: objects.BarData,
    ) -> MilestoneBar:
        starting_bar = MilestoneBar(
            index=0,
        )

        starting_datetime = datetime.datetime(
            year=current_bar.bar_time.year,
            month=current_bar.bar_time.month,
            day=current_bar.bar_time.day,
            hour=4,
        )

        bars_length = len(self.stock.bars)
        for i in range(bars_length-1, 0, -1):
            potential_starting_bar: objects.BarData = self.stock.bars[i-1]
            if potential_starting_bar.bar_time < starting_datetime:
                continue

            previous_bar = self.stock.bars[i-1]

            # pylint: disable=too-many-boolean-expressions
            if (potential_starting_bar.close > potential_starting_bar.open_value
            and potential_starting_bar.volume > previous_bar.volume * 1.5
            and potential_starting_bar.volume > potential_starting_bar.volume_average
            and potential_starting_bar.close > potential_starting_bar.ema_9
            and potential_starting_bar.high > potential_starting_bar.vwap
            and potential_starting_bar.high - potential_starting_bar.low > (previous_bar.high - previous_bar.low) * 2
            and potential_starting_bar.bar_time.day == current_bar.bar_time.day
            and potential_starting_bar.volume > 50000):
                for j in range(i-1, i-30, -1):
                    previous_bar: objects.BarData = self.stock.bars[j]
                    if (previous_bar.bar_time.date() < potential_starting_bar.bar_time.date()
                    and previous_bar.bar_time.time() < datetime.time(hour=16)):
                        continue

                    more_volatile_than_starting_bar = previous_bar.volume > potential_starting_bar.volume and previous_bar.high >= potential_starting_bar.high
                    previous_bar_close_to_starting_and_strong = previous_bar.volume/potential_starting_bar.volume >= 0.75 and i-j < 10 and previous_bar.volume > previous_bar.volume_average
                    previous_bar_body_identical_to_starting_bar = previous_bar.volume/potential_starting_bar.volume >= 0.6 and (previous_bar.high - previous_bar.low)/(potential_starting_bar.high - potential_starting_bar.low) > 0.9

                    bar_before_previous_bar = self.stock.bars[j-1]
                    potential_starting_bar_before_starting_bar = (previous_bar.high - previous_bar.low) >



        return starting_bar
