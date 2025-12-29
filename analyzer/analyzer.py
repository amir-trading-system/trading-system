import datetime
import time
import queue

from colorama import Fore, Style

from analyzer import objects, helper
import analyzer.indicators
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
        are_valid = False
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
        previous_bar = stock.previous_bar(
            bar_object=current_bar,
        )
        if not previous_bar:
            return objects.Milestones(
                starting_bar=starting_bar,
                top_bar=top_bar,
                lowest_low_bar=lowest_low_bar,
                previous_bar=previous_bar,
                are_valid=are_valid,
            )

        previous_bar = objects.MilestoneBar(
            index=previous_bar.index,
            bar_object=previous_bar,
            bar_type=objects.MilestoneType.PREVIOUS_BAR,
            bar_time=previous_bar.bar_time,
            timeframe=stock.timeframe,
        )

        current_bar_is_valid = (
            True
            and current_bar.close > current_bar.open_value
            and current_bar.high > current_bar.ema_9
            and current_bar.high > current_bar.vwap
        )

        if (
            current_bar_is_valid
            and starting_bar.index > 0
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
            previous_bar=previous_bar,
            are_valid=are_valid,
        )

    def run_indicators(
        self,
        stock: tws_objects.Stock,
        current_bar: tws_objects.BarData,
        milestons: objects.Milestones,
    ) -> None:
        success_indicators_names: list[str] = []
        stock.bars = stock.bars[:milestons.starting_bar.index+1]

        for indicator in analyzer.indicators.__indicators__:
            indicator_obj: analyzer.indicators.indicator.Indicator = indicator()
            indicator_response: analyzer.indicators.objects.IndicatorResponse = indicator_obj.indicate(
                stock=stock,
                milestones=milestons,
                current_bar=current_bar,
            )
            if indicator_response.result:
                font_color = Fore.GREEN
                if indicator_response.success_rate < 1:
                    font_color = Fore.YELLOW

                indicator_title = str.format(f"{indicator.name}: {font_color}{indicator_response.success_rate} - {indicator_response.success_count} success evidences{Style.RESET_ALL}")
                success_indicators_names.append(indicator_title)

        if len(success_indicators_names) > 0:
            print(f"""
            {Fore.GREEN}Congrats!{Style.RESET_ALL}
            Timeframe: {stock.timeframe}.
            Time: {current_bar.bar_time}.
            Indications:
            {"\n".join(success_indicators_names)}.
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

                self.run_indicators(
                    stock=stock_object,
                    current_bar=current_bar,
                    milestons=milestons,
                )
            else:
                time.sleep(2)
