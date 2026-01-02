import datetime
import time
import queue

import copy
import requests

from analyzer import objects, helper
import analyzer.indicators
import analyzer.evidences
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

        if top_bar.index > 0:
            already_passed_top_bar = [
                bar_object.index
                for bar_object in stock.bars[current_bar.index+1:top_bar.index-1]
                if bar_object.high > top_bar.bar_object.high
                and bar_object.index < top_bar.index
                and bar_object.volume > top_bar.bar_object.volume
            ]
            if len(already_passed_top_bar) > 0:
                top_bar = objects.MilestoneBar(
                    index=0,
                    bar_type=objects.MilestoneType.TOP_BAR,
                    timeframe=stock.timeframe,
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

        if (
            True
            and starting_bar.index > 0
            and top_bar.index > 0
            and lowest_low_bar.index > 0
        ):
            are_valid = True

        milestones = objects.Milestones(
            starting_bar=starting_bar,
            top_bar=top_bar,
            lowest_low_bar=lowest_low_bar,
            previous_bar=previous_bar,
            are_valid=are_valid,
        )

        if milestones.are_valid:
            fibonacci_retracement_evidence_object = analyzer.evidences.fibonacci_retracement.Evidence()
            retracements_evidence_object = analyzer.evidences.no_more_than_2_retracements_until_now.Evidence()
            fibonacci_retracement_result = fibonacci_retracement_evidence_object.find_evidence(
                stock=stock,
                current_bar=current_bar,
                milestones=milestones,
            )
            retracements_result = retracements_evidence_object.find_evidence(
                stock=stock,
                current_bar=current_bar,
                milestones=milestones,
            )
            milestones.fibonacci_retracement = float(fibonacci_retracement_result.value)
            milestones.retracement_indexes = retracements_result.value

        return milestones

    def alert(
        self,
        symbol: str,
        timeframe: int,
        bar_date: datetime.datetime,
        message: str,
    ):
        bot_token = "8571936110:AAERqN-YhP_SZyj8_STi5nSwhqguwrUhcZc"
        chat_id = "-1003604401866"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(
            url=url,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        print(f"Alert has been sent successfully for {symbol} on {timeframe} minutes timeframe for {bar_date} bar")

    def run_indicators(
        self,
        stock: tws_objects.Stock,
        current_bar: tws_objects.BarData,
        milestons: objects.Milestones,
    ) -> None:
        print(f"ANALYZER: Symbol: {stock.symbol_name}. Timeframe: {stock.timeframe}. Bar Time: {current_bar.bar_time}. Message: Running analyzers")
        success_indicators: dict[str,float] = {}
        stock.bars = stock.bars[:milestons.starting_bar.index+10]
        emoji = ""
        base_except_one = False

        for indicator in analyzer.indicators.__indicators__:
            indicator_obj: analyzer.indicators.indicator.Indicator = indicator(
                milestons=milestons,
            )
            indicator_response: analyzer.indicators.objects.IndicatorResponse = indicator_obj.indicate(
                stock=stock,
                milestones=milestons,
                current_bar=current_bar,
            )
            ## remove those 2 lines when finish investigation.
            indicator_response.result = True
            indicator_response.failed_base_evidences_count = 0
            if indicator_response.failed_base_evidences_count > 1:
                continue
            if indicator_response.result:
                ## remove this line when finish investigation.
                success_indicators[indicator_obj.name] = 1.0
                # success_indicators[indicator_obj.name] = round(indicator_response.success_rate, 3)

                if indicator_response.failed_base_evidences_count == 1:
                    base_except_one = True

        if len(success_indicators) > 0:
            sorted_indicators = dict(
                sorted(
                    success_indicators.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            )

            at_least_one_indication_result_is_certain = len(
                [
                    result
                    for result in sorted_indicators.values()
                    if result == 1.0
                ]
            ) >= 1
            certain_result = len(sorted_indicators) >= 5

            if at_least_one_indication_result_is_certain:
                if certain_result:
                    emoji = "✅"
                else:
                    emoji = "👀"

                message = f"""
    <b>{emoji} Congrats! {emoji}</b>
    {"<b>BASE EXCEPT ONE!</b>" if base_except_one else ""}

    <b>Symbol:</b> <u>{stock.symbol_name}</u>
    <b>Timeframe:</b> <code>{stock.timeframe}</code>
    <b>Time:</b> <code>{current_bar.bar_time}</code>

    <b>{len(sorted_indicators)} Indications:</b>
    {chr(10).join(f"• <i>{indicator_name}: {rate}</i>" for indicator_name, rate in sorted_indicators.items())}
    """

                self.alert(
                    symbol=stock.symbol_name,
                    timeframe=stock.timeframe,
                    bar_date=current_bar.bar_time,
                    message=message,
                )

    def analyze_bar(
        self,
        stock: tws_objects.Stock,
        current_bar: tws_objects.BarData,
    ):
        current_bar_is_valid = (
            True
            and current_bar.close > current_bar.open_value
            and current_bar.high > current_bar.ema_9
            and current_bar.high > current_bar.vwap
        )
        if not current_bar_is_valid:
            print(f"ANALYZER: Symbol: {stock.symbol_name}. Timeframe: {stock.timeframe}. Bar Time: {current_bar.bar_time}. Message: Bar is not valid")
            return

        milestons: objects.Milestones = self._prepare_milestones(
            stock=stock,
            current_bar=current_bar,
        )

        if not milestons.are_valid:
            print(f"ANALYZER: Symbol: {stock.symbol_name}. Timeframe: {stock.timeframe}. Bar Time: {current_bar.bar_time}. Message: Milestones are not valid")
            return

        self.run_indicators(
            stock=stock,
            current_bar=current_bar,
            milestons=milestons,
        )

    def analyze_data(
        self,
        specific_bar_time: datetime.datetime = None,
        retroactive_from: datetime.datetime = False,
    ):
        while True:
            if not self.bars_ready_to_analyze_queue.empty():
                stock_object: tws_objects.Stock = self.bars_ready_to_analyze_queue.get()
                stock = tws_objects.Stock(
                    symbol_name=stock_object.symbol_name,
                    timeframe=stock_object.timeframe,
                    bars=copy.deepcopy(stock_object.bars),
                )
                print(f"ANALYZER: Symbol: {stock.symbol_name}. Timeframe: {stock.timeframe}. Message: Starting analyze bar")

                stock.bars = sorted(
                    stock.bars,
                    key=lambda bar: bar.bar_time,
                    reverse=True,
                )

                if retroactive_from:
                    all_bars = copy.deepcopy(stock.bars)
                    for bar_object in stock.bars:
                        if bar_object.bar_time.day != retroactive_from.day:
                            continue

                        relevant_bars = all_bars[bar_object.index:]
                        for i, bar_obj in enumerate(relevant_bars):
                            bar_obj.index = i

                        current_bar = [
                            bar_obj
                            for bar_obj in relevant_bars
                            if bar_obj.bar_time == bar_object.bar_time
                        ]
                        if len(current_bar) == 0:
                            continue

                        current_bar = current_bar[0]
                        new_stock_object = tws_objects.Stock(
                            symbol_name=stock_object.symbol_name,
                            bars=relevant_bars,
                            timeframe=stock_object.timeframe,
                        )

                        self.analyze_bar(
                            stock=new_stock_object,
                            current_bar=current_bar,
                        )
                else:
                    current_bar = stock.bars[0]
                    if specific_bar_time is not None:
                        current_bar = [
                            bar_data
                            for bar_data in stock.bars
                            if bar_data.bar_time == specific_bar_time
                        ]

                        if len(current_bar) == 1:
                            current_bar = current_bar[0]
                            stock.bars = stock.bars[current_bar.index:]
                            for i, bar_object in enumerate(stock.bars):
                                bar_object.index = i

                    self.analyze_bar(
                        stock=stock,
                        current_bar=current_bar,
                    )
            else:
                time.sleep(2)
