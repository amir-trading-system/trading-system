import datetime
import time
import queue

from analyzer import objects, helper
from analyzer.indications import __indications__, objects as indication_objects
from tws import objects as tws_objects




class Analyzer:
    def __init__(
        self,
        bars_ready_to_analyze_queue: queue.Queue
    ):
        self.bars_ready_to_analyze_queue = bars_ready_to_analyze_queue
        self.helper = helper.AnalyzerHelper()

    def _prepare_milestones(
        self,
        stock: tws_objects.Stock,
        current_bar: tws_objects.BarData,
    ) -> objects.Milestones:
        starting_bar: objects.MilestoneBar = self.helper.get_strating_bar(
            stock=stock,
            current_bar=current_bar,
        )

        top_bar: objects.MilestoneBar = self.helper.get_top_bar(
            stock=stock,
            starting_bar=starting_bar,
        )

        lowest_low_bar: objects.MilestoneBar = self.helper.get_lowest_bar_from_top_bar(
            stock=stock,
            top_bar=top_bar,
        )

        are_valid = False

        if (
            starting_bar.index > 0
            and top_bar.index > 0
            and lowest_low_bar.index > 0
        ):
            are_valid = True
            # print(
            #     f"""stock: {stock.symbol_name}.
            #     bar_time: {lowest_low_bar.bar_time}.
            #     timeframe: {lowest_low_bar.timeframe}.
            #     starting: index: {starting_bar.index}. time: {starting_bar.bar_time}\n
            #     top: index: {top_bar.index}. time: {top_bar.bar_time}\n
            #     lowest low: index: {lowest_low_bar.index}. time: {lowest_low_bar.bar_time}\n""",
            # )

        return objects.Milestones(
            starting_bar=starting_bar,
            top_bar=top_bar,
            lowest_low_bar=lowest_low_bar,
            are_valid=are_valid,
        )

    def _analyze(
        self,
        stock: tws_objects.Stock,
        current_bar: tws_objects.BarData,
        milestons: objects.Milestones,
    ) -> None:
        success_indicators_names: list[str] = []
        for indication in __indications__:
            indication_obj = indication()
            indication_response: indication_objects.IndicationResponse = indication_obj.indicate(
                stock=stock,
                milestones=milestons,
            )
            if indication_response.result:
                success_indicators_names.append(
                    str.format(f"{indication.name}: {indication_response.success_rate}")
                )

        if len(success_indicators_names) > 0:
            print(f"""
            Congrats!
            Timeframe: {stock.timeframe}.
            Time: {current_bar.bar_time}.
            Indications:{"\n".join(success_indicators_names)}.
            Symbol: {stock.symbol_name}.
            """)

    def analyze_data(
        self,
        specific_bar_time: datetime.datetime = None,
    ):
        while True:
            if not self.bars_ready_to_analyze_queue.empty():
                stock_object: tws_objects.Stock = self.bars_ready_to_analyze_queue.get()

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

                milestons: objects.Milestones = self._prepare_milestones(
                    stock=stock_object,
                    current_bar=current_bar,
                )

                if not milestons.are_valid:
                    continue

                self._analyze(
                    stock=stock_object,
                    current_bar=current_bar,
                    milestons=milestons,
                )
            else:
                time.sleep(2)
