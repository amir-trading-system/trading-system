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
    is_manual: bool = False,
):
    manual_results_for_test = []
    collector_kwargs = {}
    analyzer_kwargs = {}

    if is_manual:
        manual_results_for_test = ["FJET"]
        collector_kwargs = {
            "manual_timeframe_for_tests": 15,
        }
        analyzer_kwargs = {
            "specific_bar_time": datetime.datetime(
                year=2025,
                month=12,
                day=22,
                hour=13,
                minute=45,
            ),
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

    threading.Thread(
        target=collector_obj.tws_client.run
    ).start()
    time.sleep(1)

    run_bot(
        # is_manual=True,
        c_obj=collector_obj,
        a_obj=analyzer_obj,
    )
