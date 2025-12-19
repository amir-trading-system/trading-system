import threading
import time

from .. import database
from . import tws_client

class Collector:
    def __init__(
        self,
        tws_host: str,
        tws_port: int,
    ):
        self.database_client = database.client.Client()
        self.tws_client = tws_client.TWSClient(
            host=tws_host,
            port=tws_port,
        )

    def collect(
        self,
    ):
        self.tws_client.connect_tws()

        threading.Thread(target=self.tws_client.run).start()
        time.sleep(1)

        contract = self.tws_client.client.Contract()
        contract.symbol = "YCBD"
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        ## For getting live data
        self.tws_client.reqHistoricalData(
            reqId=self.tws_client.nextId(),
            contract=contract,
            endDateTime="",
            durationStr="1 D",
            barSizeSetting="5 mins",
            whatToShow="TRADES",
            useRTH=0,
            formatDate=2,
            chartOptions=[],
            keepUpToDate=True,
        )
