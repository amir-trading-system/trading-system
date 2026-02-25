import datetime
import threading
import queue
import time

import logger

import collector
import common
import tws

if __name__ == '__main__':
    symbols_to_collect_queue: queue.Queue[str] = queue.Queue()
    bars_ready_to_analyze_queue: queue.Queue[common.objects.Stock] = queue.Queue()
    request_id_to_symbol: dict[int,common.objects.Stock] = {}

    logger_object = logger.logger.Logger(
        enable_stdout=False,
    ).get_logger()
    tws_client = tws.client.Client(
        host="localhost",
        port=8081,
        symbols_to_collect_queue=symbols_to_collect_queue,
        bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
        request_id_to_symbol=request_id_to_symbol,
        monitored_symbols=[],
        logger=logger_object,
    )

    collector_obj = collector.collector.Collector(
        tws_client=tws_client,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
    )

    threading.Thread(
        target=tws_client.run
    ).start()
    time.sleep(1)

    tws_client.start_scanner(
        for_upside_potential=True,
    )
    tws_client.data_streamer.is_retro = True

    threading.Thread(
        target=collector_obj.collect_data,
    ).start()

    while True:
        if not bars_ready_to_analyze_queue.empty():
            stock: common.objects.Stock = bars_ready_to_analyze_queue.get()
            stock.arrange_data_for_analysis()

            for bar_object in stock.bars[:5]:
                if (
                    True
                    and bar_object.close < bar_object.open_value
                    and bar_object.volume > bar_object.volume_average
                    and bar_object.close < bar_object.ema_9
                    and bar_object.close < bar_object.ema_20
                    and bar_object.close < bar_object.vwap
                    and min(
                        bar_obj.close
                        for bar_obj in stock.bars[:50]
                    ) == bar_object.close
                    and min(
                        bar_obj.low
                        for bar_obj in stock.bars[1:50]
                    ) > bar_object.close
                    and max(
                        bar_obj.volume
                        for bar_obj in stock.bars[:10]
                    ) == bar_object.volume
                ):
                    print(f"{bar_object.symbol}--{bar_object.bar_time}")
        else:
            time.sleep(1)
