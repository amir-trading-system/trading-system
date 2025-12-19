import threading
import time

from . import tws_client

class Collector:
    def __init__(
        self,
        database_client,
        tws_host: str,
        tws_port: int,
    ):
        self.database_client = database_client
        self.tws_client = tws_client.TWSClient(
            host=tws_host,
            port=tws_port,
            database_client=database_client,
        )
        self.tws_client.connect_tws()

    def collect(
        self,
        timeframe: int,
    ):
        threading.Thread(target=self.tws_client.run).start()
        time.sleep(1)

        stocks = ["AFJK", "ISSC"]
        for stock in stocks:
            contract = self.tws_client.client.Contract()
            contract.symbol = stock
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"

            ## For getting live data
            self.tws_client.reqHistoricalData(
                reqId=self.tws_client.nextId(),
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
