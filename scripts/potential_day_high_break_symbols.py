import time
import queue

import collector
import common
import logger
import tws

from . import get_relevant_stocks

def run_script():
    print("h")

if __name__ == '__main__':
    symbols_to_collect_queue: queue.Queue[str] = queue.Queue()
    bars_ready_to_analyze_queue: queue.Queue[common.objects.Stock] = queue.Queue()
    request_id_to_symbol: dict[int,common.objects.Stock] = {}
    logger_object = logger.logger.Logger().get_logger()

    tws_client = tws.client.Client(
        host="localhost",
        port=8081,
        symbols_to_collect_queue=symbols_to_collect_queue,
        bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
    )
    collector_obj = collector.collector.Collector(
        tws_client=tws_client,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
    )
    # relevant_stocks: list[str] = get_relevant_stocks.get_stocks_by_price_change_and_volume()
    relevant_stocks = ["BNAI"]

    for stock in relevant_stocks:
        collector_obj.collect_by_symbol(
            symbol=stock,
            timeframes=[
                common.objects.TimeframeInput(
                    timeframe=1,
                    timeframe_type=common.objects.TimeframeType.MINUTE,
                ),
                # common.objects.TimeframeInput(
                #     timeframe=1,
                #     timeframe_type=common.objects.TimeframeType.DAY,
                # ),
            ],
        )

    final_stocks: list[common.objects.Stock] = []
    while True:
        if not tws_client.bars_ready_to_analyze_queue.empty():
            stock = tws_client.bars_ready_to_analyze_queue.get()
            print(f"{stock.symbol_name}")
            final_stocks.append(stock)

        time.sleep(1)
