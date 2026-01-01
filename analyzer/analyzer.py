import datetime
import time
import queue

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

    def run_indicators(
        self,
        stock: tws_objects.Stock,
        current_bar: tws_objects.BarData,
        milestons: objects.Milestones,
    ) -> None:
        success_indicators_names: list[str] = []
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
            if indicator_response.failed_base_evidences_count > 1:
                continue
            if indicator_response.result:
                emoji = "✅"
                if indicator_response.success_rate < 1:
                    emoji = "👀"

                indicator_title = str.format(f"Indicator Name: {indicator_obj.name}.\nSuccess Rate:{indicator_response.success_rate}.\nThere was {indicator_response.success_count} success evidences.")
                if indicator_response.failed_base_evidences_count == 1:
                    base_except_one = True
                success_indicators_names.append(indicator_title)

        if len(success_indicators_names) > 0:
            message = f"""
<b>{emoji} Congrats! {emoji}</b>
{"<b>BASE EXCEPT ONE!</b>" if base_except_one else ""}

<b>Symbol:</b> <u>{stock.symbol_name}</u>
<b>Timeframe:</b> <code>{stock.timeframe}</code>
<b>Time:</b> <code>{current_bar.bar_time}</code>

<b>Indications:</b>
{chr(10).join(f"• <i>{name}</i>" for name in success_indicators_names)}


"""

            self.alert(
                message=message,
            )

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
