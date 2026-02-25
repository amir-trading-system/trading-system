import logging
import queue

from ibapi import client, contract, tag_value


class Scanner():
    def __init__(
        self,
        symbols_to_collect_queue: queue.Queue,
        logger: logging.Logger,
    ):
        self.symbols_to_collect_queue = symbols_to_collect_queue
        self.relevant_symbols: list[str] = []
        self.logger = logger
        self.next_id = 1

    def get_scanner_subscription(
        self,
        for_upside_potential: bool = False
    ) -> client.ScannerSubscription:
        scanner_subscription = client.ScannerSubscription()
        scanner_subscription.numberOfRows = 50
        scanner_subscription.instrument = "STK"
        scanner_subscription.locationCode = "STK.US.MAJOR"
        scanner_subscription.scanCode = "TOP_PERC_GAIN"
        if for_upside_potential:
            scanner_subscription.scanCode = "HOT_BY_VOLUME"

        return scanner_subscription

    def get_scanner_filters(
        self,
        for_upside_potential: bool = False,
    ) -> list[tag_value.TagValue]:
        if for_upside_potential:
            return [
                tag_value.TagValue("volumeAbove", "1000000"),
                tag_value.TagValue("priceAbove", "0.5"),
                tag_value.TagValue("priceBelow", "30"),
                tag_value.TagValue("marketCapBelow1e6", "500000000"),
            ]

        return [
            tag_value.TagValue("volumeAbove", "200000"),
            tag_value.TagValue("priceAbove", "1"),
            tag_value.TagValue("priceBelow", "100"),
            tag_value.TagValue("marketCapBelow1e6", "500000000"),
            tag_value.TagValue("changePercAbove", "20")
        ]

    def get_contract_details(
        self,
        request_id: int,
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
                            "request_id": request_id,
                        },
                    )
                    self.relevant_symbols.append(contract_details.contract.symbol)
                    self.symbols_to_collect_queue.put(contract_details.contract.symbol)
