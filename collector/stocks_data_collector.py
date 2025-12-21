import threading
import time

from . import tws_client
from . import objects

class Collector:
    def __init__(
        self,
        tws_host: str,
        tws_port: int,
    ):
        self.request_id_to_symbol: dict[int,objects.Stock] = {}
        self.tws_client = tws_client.TWSClient(
            host=tws_host,
            port=tws_port,
            request_id_to_symbol=self.request_id_to_symbol,
        )
        self.tws_client.connect_tws()

    def collect(
        self,
        timeframe: int,
    ):
        threading.Thread(target=self.tws_client.run).start()
        time.sleep(1)

        request_id = self.tws_client.nextId()
        self.tws_client.start_scanner(
            request_id=request_id,
        )

        while True:
            if not self.tws_client.symbols_to_collect_queue.empty():
                symbol = self.tws_client.symbols_to_collect_queue.get()
                timeframes = [5, 15, 30]
                contract = self.tws_client.client.Contract()
                contract.symbol = symbol
                contract.secType = "STK"
                contract.exchange = "SMART"
                contract.currency = "USD"

                ## For getting live data
                for timeframe in timeframes:
                    request_id = self.tws_client.nextId()
                    self.request_id_to_symbol[request_id] = objects.Stock(
                        symbol_name=symbol,
                        bars=[],
                        timeframe=timeframe,
                    )
                    self.tws_client.reqHistoricalData(
                        reqId=request_id,
                        contract=contract,
                        endDateTime="",
                        durationStr="1 D",
                        barSizeSetting=f"{timeframe} mins",
                        whatToShow="TRADES",
                        useRTH=0,
                        formatDate=2,
                        chartOptions=[],
                        keepUpToDate=True,
                    )
