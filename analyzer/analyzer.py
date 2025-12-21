import datetime
import time
import queue

from tws import objects
from . import analyzers


class Analyzer:
    def __init__(
        self,
        bars_ready_to_analyze_queue: queue.Queue
    ):
        self.bars_ready_to_analyze_queue = bars_ready_to_analyze_queue
        self.helper = analyzers.helper.AnalyzerHelper()

    def _prepare_milestones(
        self,
        stock: objects.Stock,
        current_bar: objects.BarData,
    ):
        starting_bar: analyzers.helper.MilestoneBar = self.helper.get_strating_bar(
            stock=stock,
            current_bar=current_bar,
        )
        if starting_bar.index > 0:
            print(f"starting index: {starting_bar.index}. bar_time: {starting_bar.bar_time}. timeframe: {starting_bar.timeframe}")
        # pass

    def _analyze(
        self,
    ) -> bool:
        pass

    def analyze_data(
        self,
        specific_bar_time: datetime.datetime = None,
    ):
        while True:
            if not self.bars_ready_to_analyze_queue.empty():
                stock_object: objects.Stock = self.bars_ready_to_analyze_queue.get()

                current_bar = stock_object.bars[-1]
                if specific_bar_time is not None:
                    current_bar = [
                        bar_data
                        for bar_data in stock_object.bars
                        if bar_data.bar_time == specific_bar_time
                    ]
                    if len(current_bar) == 1:
                        current_bar = current_bar[0]

                self._prepare_milestones(
                    stock=stock_object,
                    current_bar=current_bar,
                )
                print(f"got stock ready to analyze. stock: {stock_object.symbol_name}")
            else:
                time.sleep(2)
