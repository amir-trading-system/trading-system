import logging
import queue

from ibapi import client, contract, tag_value

import alerter


class Scanner():
    def __init__(
        self,
        symbols_to_collect_queue: queue.Queue,
        logger: logging.Logger,
        alerter_object: alerter.alerter.Alerter,
    ):
        self.symbols_to_collect_queue = symbols_to_collect_queue
        self.relevant_symbols: list[str] = []
        self.logger = logger
        self.alerter_object = alerter_object
        self.next_id = 1

    def get_scanner_subscription(
        self,
    ) -> client.ScannerSubscription:
        scanner_subscription = client.ScannerSubscription()
        scanner_subscription.numberOfRows = 50
        scanner_subscription.instrument = "STK"
        scanner_subscription.locationCode = "STK.US.MAJOR"
        scanner_subscription.scanCode = "TOP_PERC_GAIN"


        return scanner_subscription

    def get_scanner_filters(
        self,
    ) -> list[tag_value.TagValue]:
        return [
            tag_value.TagValue("volumeAbove", "100000"),
            tag_value.TagValue("priceAbove", "1"),
            tag_value.TagValue("priceBelow", "100"),
            tag_value.TagValue("marketCapBelow1e6", "500000000"),
            tag_value.TagValue("changePercAbove", "20")
        ]

    def get_contract_details(
        self,
        contract_details: contract.ContractDetails,
    ):
        no_opening_trades = False
        symbol_name = contract_details.contract.symbol
        if symbol_name not in self.relevant_symbols:
            if contract_details.ineligibilityReasonList is not None:
                no_opening_trades = True
                self.relevant_symbols.append(contract_details.contract.symbol)
            if not no_opening_trades:
                if contract_details.contract.symbol not in self.relevant_symbols:
                    self.logger.info(
                        msg="New symbol founded by scanner",
                        extra={
                            "worker": "Scanner",
                            "symbol": contract_details.contract.symbol,
                            "symbol_type": contract_details.stockType,
                        },
                    )
                    print(symbol_name)
                    self.relevant_symbols.append(contract_details.contract.symbol)
                    self.symbols_to_collect_queue.put(contract_details.contract.symbol)
