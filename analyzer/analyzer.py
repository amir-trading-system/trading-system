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
    ) -> dict[str,objects.BarData]:
        starting_bar: analyzers.helper.MilestoneBar = self.helper.get_strating_bar(
            stock=stock,
            current_bar=current_bar,
        )
        if starting_bar.index > 0:
            print(f"stock: {stock.symbol_name}. bar_time: {starting_bar.bar_time}. timeframe: {starting_bar.timeframe}. starting index: {starting_bar.index}.")

        top_bar: analyzers.helper.MilestoneBar = self.helper.get_top_bar(
            stock=stock,
            starting_bar=starting_bar,
        )
        if top_bar.index > 0:
            print(f"stock: {stock.symbol_name}. bar_time: {top_bar.bar_time}. timeframe: {top_bar.timeframe}. starting index: {top_bar.index}.")

        lowest_low_bar: analyzers.helper.MilestoneBar = self.helper.get_lowest_bar_from_top_bar(
            stock=stock,
            top_bar=top_bar,
        )

        if lowest_low_bar.index > 0:
            print(f"stock: {stock.symbol_name}. bar_time: {lowest_low_bar.bar_time}. timeframe: {lowest_low_bar.timeframe}. starting index: {lowest_low_bar.index}.")


        return {
            "starting_bar": starting_bar,
            "top_bar": top_bar,
            "lowest_low_bar": lowest_low_bar,
        }

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

                current_bar = stock_object.bars[0]
                if specific_bar_time is not None:
                    current_bar = [
                        bar_data
                        for bar_data in stock_object.bars
                        if bar_data.bar_time == specific_bar_time
                    ]

                    if len(current_bar) == 1:
                        current_bar = current_bar[0]
                        stock_object.bars = stock_object.bars[current_bar.index:]
                        for i, bar_object in enumerate(stock_object.bars):
                            bar_object.index = i

                self._prepare_milestones(
                    stock=stock_object,
                    current_bar=current_bar,
                )
                # print(f"got stock ready to analyze. stock: {stock_object.symbol_name}")
            else:
                time.sleep(2)
