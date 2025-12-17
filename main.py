import time
import threading

from ibapi import client, wrapper
from ibapi.ticktype import TickTypeEnum


class TestApp(client.EClient, wrapper.EWrapper):
    def __init__(
        self,
        bar_size: int,
    ):
        client.EClient.__init__(
            self,
            self,
        )
        self.last_price = None
        self.bar_size = bar_size

    def nextValidId(
        self,
        orderId,
    ):
        self.orderId = orderId

    def nextId(
        self,
    ):
        self.orderId += 1
        return self.orderId

    def currentTime(
        self,
        time,
    ):
        print(time)

    def error(self, reqId, errorTime, errorCode, errorString, advancedOrderRejectJson=""):
        print(f"reqId: {reqId}, errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderRejectJson}")

    def tickPrice(self, reqId, tickType, price, attrib):
        if TickTypeEnum.toStr(tickType) == "LAST":
            self.last_price = price

    # def tickSize(self, reqId, tickType, size):
    #     print(f"reqId: {reqId}, tickType: {TickTypeEnum.toStr(tickType)}, size: {size}")

    def historicalData(self, reqId, bar):
        print(f"reqId: {reqId}, bar: {bar.__str__()}, price: {self.last_price}")

    def historicalDataUpdate(self, reqId, bar):
        bar.date
        print(f"reqId: {reqId}, bar: {bar.__str__()}. price: {self.last_price}")

if __name__ == "__main__":
    app = TestApp()
    app.connect("localhost", 8081, 0)
    threading.Thread(target=app.run).start()
    time.sleep(1)

    contract = client.Contract()
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
        formatDate=1,
        chartOptions=[],
        keepUpToDate=True,
    )

    ## For getting price.
    app.reqMktData(
        reqId=app.nextId(),
        contract=contract,
        genericTickList="",
        snapshot=False,
        regulatorySnapshot=False,
        mktDataOptions=[],
    )
