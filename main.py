import threading
import time
import queue

import collector

if __name__ == "__main__":
    symbols_to_collect_queue: queue.Queue[str] = queue.Queue()
    bars_ready_to_analyze_queue: queue.Queue[collector.objects.Stock] = queue.Queue()
    collector_obj = collector.stocks_data_collector.Collector(
        tws_host="localhost",
        tws_port=8081,
        symbols_to_collect_queue=symbols_to_collect_queue,
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
        target=collector_obj.analyze_data,
    ).start()
