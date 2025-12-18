import datetime

from ibapi import client, wrapper


class TestApp(client.EClient, wrapper.EWrapper):
    def __init__(
        self,
    ):
        self.order_id = None
        client.EClient.__init__(
            self,
            self,
        )

    def nextValidId(
        self,
        orderId,
    ):
        self.order_id = orderId

    def nextId(
        self,
    ):
        self.order_id += 1
        return self.order_id

    def error(self, reqId, errorTime, errorCode, errorString, advancedOrderRejectJson=""):
        print(f"reqId: {reqId}, errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderRejectJson}")

    def historicalData(self, reqId, bar):
        bar_date = datetime.datetime.fromtimestamp(float(bar.date))
        print(f"reqId: {reqId}, price: {bar.close} date: {bar_date}")

    def historicalDataUpdate(self, reqId, bar):
        print(f"reqId: {reqId}, bar: {str(bar)}. price: {bar.close}")
