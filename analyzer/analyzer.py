import time
import queue

from tws import objects

class Analyzer:
    def __init__(
        self,
        bars_ready_to_analyze_queue: queue.Queue
    ):
        self.bars_ready_to_analyze_queue = bars_ready_to_analyze_queue

    ## move it when ready to main.
    def analyze_data(
        self,
    ):
        while True:
            if not self.bars_ready_to_analyze_queue.empty():
                stock_object: objects.Stock = self.bars_ready_to_analyze_queue.get()
                print(f"got stock ready to analyze. stock: {stock_object.symbol_name}")
            else:
                time.sleep(2)
