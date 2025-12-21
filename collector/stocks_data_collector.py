import time
import queue

from . import tws_client
from . import objects

class Collector:
    def __init__(
        self,
        tws_host: str,
        tws_port: int,
        symbols_to_collect_queue: queue.Queue[str],
        bars_ready_to_analyze_queue: queue.Queue[objects.Stock],
    ):
        self.request_id_to_symbol: dict[int,objects.Stock] = {}
        self.tws_client = tws_client.TWSClient(
            host=tws_host,
            port=tws_port,
            request_id_to_symbol=self.request_id_to_symbol,
            symbols_to_collect_queue=symbols_to_collect_queue,
            bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
        )

    ## move it when ready to main.
    def collect_data(
        self,
    ):
        while True:
            if not self.tws_client.symbols_to_collect_queue.empty():
                symbol = self.tws_client.symbols_to_collect_queue.get()
                timeframes = [5, 15, 30]

                for timeframe in timeframes:
                    self.tws_client.request_historical_data(
                        symbol=symbol,
                        timeframe=timeframe,
                    )
            else:
                time.sleep(2)

    ## move it when ready to main.
    def analyze_data(
        self,
    ):
        while True:
            if not self.tws_client.bars_ready_to_analyze_queue.empty():
                stock_object: objects.Stock = self.tws_client.bars_ready_to_analyze_queue.get()
                print(f"got stock ready to analyze. stock: {stock_object.symbol_name}")
            else:
                time.sleep(2)
