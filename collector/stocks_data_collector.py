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
        self.request_id_to_stock: dict[int,objects.Stock] = {}
        self.tws_client = tws_client.TWSClient(
            host=tws_host,
            port=tws_port,
            request_id_to_stock=self.request_id_to_stock,
        )
        self.tws_client.connect_tws()

    def collect(
        self,
        timeframe: int,
    ):
        threading.Thread(target=self.tws_client.run).start()
        time.sleep(1)

        stocks = ["AZI"]
        for stock in stocks:
            timeframes = [5, 15]
            contract = self.tws_client.client.Contract()
            contract.symbol = stock
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"

            ## For getting live data
            for timeframe in timeframes:
                request_id = self.tws_client.nextId()
                self.request_id_to_stock[request_id] = objects.Stock(
                    symbol_name=stock,
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
