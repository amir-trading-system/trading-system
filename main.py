import time
import threading

import collector

if __name__ == "__main__":
    app = collector.tws_client.TestApp()
    app.connect("localhost", 8081, 0)
    threading.Thread(target=app.run).start()
    time.sleep(1)

    contract = collector.tws_client.client.Contract()
    contract.symbol = "YCBD"
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"

    ## For getting live data
    app.reqHistoricalData(
        reqId=app.nextId(),
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
