import datetime
import logging
import time
import queue

from tws import objects, client

class Collector:
    def __init__(
        self,
        tws_host: str,
        tws_port: int,
        symbols_to_collect_queue: queue.Queue[str],
        bars_ready_to_analyze_queue: queue.Queue[objects.Stock],
        logger: logging.Logger,
    ):
        self.logger = logger
        self.request_id_to_symbol: dict[int,objects.Stock] = {}
        self.tws_client = client.Client(
            host=tws_host,
            port=tws_port,
            request_id_to_symbol=self.request_id_to_symbol,
            symbols_to_collect_queue=symbols_to_collect_queue,
            bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
            logger=logger,
        )

    def collect_data(
        self,
        manual_timeframe_for_tests: int = None,
        specific_bar_time: datetime.datetime = None,
    ):
        while True:
            if not self.tws_client.symbols_to_collect_queue.empty():
                symbol = self.tws_client.symbols_to_collect_queue.get()
                timeframes = [5, 15, 30]
                if manual_timeframe_for_tests:
                    timeframes = [manual_timeframe_for_tests]

                for timeframe in timeframes:
                    self.tws_client.request_historical_data(
                        symbol=symbol,
                        timeframe=timeframe,
                        specific_bar_time=specific_bar_time,
                    )
            else:
                time.sleep(2)
