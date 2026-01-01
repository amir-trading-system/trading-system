from  argparse import ArgumentParser
import datetime
import threading
import time
import queue

import analyzer
import collector
import tws

def run_bot(
    c_obj: collector.collector.Collector,
    a_obj: analyzer.analyzer.Analyzer,
    on_specific_bar_time: bool = False,
):
    manual_results_for_test = []
    collector_kwargs = {}
    analyzer_kwargs = {}
    c_obj.tws_client.on_specific_bar_time = on_specific_bar_time

    if on_specific_bar_time:
        manual_results_for_test = ["EKSO"]
        specific_bar_time = datetime.datetime(
            year=2025,
            month=12,
            day=30,
            hour=11,
            minute=5,
        )
        collector_kwargs = {
            "manual_timeframe_for_tests": 5,
            "specific_bar_time": specific_bar_time,
        }
        analyzer_kwargs = {
            "specific_bar_time": specific_bar_time,
        }

    c_obj.tws_client.start_scanner(
        manual_results_for_test=manual_results_for_test,
    )

    threading.Thread(
        target=c_obj.collect_data,
        kwargs=collector_kwargs,
    ).start()

    threading.Thread(
        target=a_obj.analyze_data,
        kwargs=analyzer_kwargs,
    ).start()

if __name__ == "__main__":
    symbols_to_collect_queue: queue.Queue[str] = queue.Queue()
    bars_ready_to_analyze_queue: queue.Queue[tws.objects.Stock] = queue.Queue()
    collector_obj = collector.collector.Collector(
        tws_host="localhost",
        tws_port=8081,
        symbols_to_collect_queue=symbols_to_collect_queue,
        bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
    )
    analyzer_obj = analyzer.analyzer.Analyzer(
        bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
    )

    argument_parser = ArgumentParser()
    argument_parser.add_argument(
        "--on_specific_bar_time",
        type=bool,
        default=False,
    )

    args = argument_parser.parse_args()

    threading.Thread(
        target=collector_obj.tws_client.run
    ).start()
    time.sleep(1)

    run_bot(
        on_specific_bar_time=args.on_specific_bar_time,
        c_obj=collector_obj,
        a_obj=analyzer_obj,
    )
