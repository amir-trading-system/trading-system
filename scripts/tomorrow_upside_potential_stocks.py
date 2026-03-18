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
        client_id=1,
        is_retro=True,
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
    tws_client.data_streamer.on_specific_bar_time = True

    threading.Thread(
        target=collector_obj.collect_data,
    ).start()
    relevant_symbols: list[str] = []

    while True:
        try:
            stock: common.objects.Stock = bars_ready_to_analyze_queue.get(
                timeout=10,
            )
        except queue.Empty as e:
            print("No more data from scanner")
            if relevant_symbols:
                #pylint:disable=unspecified-encoding
                with open("potential_upside_for_tomorrow.txt", "w") as f:
                    f.writelines(relevant_symbols)
            break

        stock.arrange_data_for_analysis()

        for bar_object in stock.bars[:5]:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            if (
                True
                and previous_bar is not None
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
                and bar_object.volume > previous_bar.volume
                and bar_object.low/bar_object.close >= 0.9
            ):
                SYMBOL = f"{bar_object.symbol}--{bar_object.bar_time}"
                relevant_symbols.append(f"{SYMBOL}\n")
                print(SYMBOL)
