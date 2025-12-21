import threading
import time
import queue

import analyzer
import collector
import tws

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

    collector_obj.tws_client.start_scanner()

    threading.Thread(
        target=collector_obj.collect_data,
    ).start()

    threading.Thread(
        target=analyzer_obj.analyze_data,
    ).start()
