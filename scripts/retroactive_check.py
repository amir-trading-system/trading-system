import datetime
import threading
import time
import queue

import analyzer
import buying_confirmator
import common
import collector
import logger
import tws

class Symbol:
    def __init__(
        self,
        name: str,
        datetime_str: str,
        finished: bool = False,
    ):
        self.name = name
        self.date_time = datetime.datetime.strptime(datetime_str, "%m.%d.%yT%H:%M:%S")
        self.finished = finished

def analyze_finished(
    request_id_to_symbol: dict[int,common.objects.Stock],
) -> bool:
    return all(
        (
            True
            and symbol.finished_collection
            and symbol.finished_analyze
        )
        for _, symbol in request_id_to_symbol.items()
        if symbol.is_day_timeframe()
    )

def confirmation_finished(
    request_id_to_symbol: dict[int,common.objects.Stock],
) -> bool:
    return all(
        symbol.finished_confirmation
        for _, symbol in request_id_to_symbol.items()
        if symbol.is_day_timeframe()
    )

def get_symbols() -> list[Symbol]:
    return [
        Symbol(
            name="NAMM",
            datetime_str="01.22.26T10:30:00",
        ),
        Symbol(
            name="NAMM",
            datetime_str="01.28.26T14:51:00",
        ),
        Symbol(
            name="BNAI",
            datetime_str="01.02.26T09:38:00",
        ),
        Symbol(
            name="BNAI",
            datetime_str="01.14.26T09:35:00",
        ),
        Symbol(
            name="BNAI",
            datetime_str="01.23.26T10:32:00",
        ),
        Symbol(
            name="BNAI",
            datetime_str="01.28.26T09:45:00",
        ),
        Symbol(
            name="FEED",
            datetime_str="01.29.26T09:40:00",
        ),
        Symbol(
            name="FEED",
            datetime_str="01.30.26T10:14:00",
        ),
        Symbol(
            name="CATX",
            datetime_str="02.02.26T10:48:00",
        ),
    ]

def run_retroactive_check():
    symbols_to_collect_queue: queue.Queue[str] = queue.Queue()
    bars_ready_to_analyze_queue: queue.Queue[common.objects.Stock] = queue.Queue()
    waiting_for_confirmation_queue: queue.Queue[dict[str, common.objects.BarData|common.objects.Milestones]] = queue.Queue()
    request_id_to_symbol: dict[int,common.objects.Stock] = {}

    logger_object = logger.logger.Logger().get_logger()
    tws_client = tws.client.Client(
        host="localhost",
        port=8081,
        symbols_to_collect_queue=symbols_to_collect_queue,
        bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
    )
    threading.Thread(
        target=tws_client.run
    ).start()
    time.sleep(1)

    tws_client.data_streamer.on_specific_bar_time = True
    collector_object = collector.collector.Collector(
        tws_client=tws_client,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
    )
    analyzer_object = analyzer.analyzer.Analyzer(
        bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
        waiting_for_confirmation_queue=waiting_for_confirmation_queue,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
    )
    confirmator_object = buying_confirmator.confirmator.Confirmator(
        tws_client=tws_client,
        waiting_for_confirmation_queue=waiting_for_confirmation_queue,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
    )
    confirmator_object.is_retro = True

    symbols = get_symbols()
    for symbol in symbols:
        collector_object.collect_data_retroactively(
            symbol=symbol.name,
            manual_timeframe_for_tests=common.objects.TimeframeInput(
                timeframe=1,
                timeframe_type=common.objects.TimeframeType(2),
            ),
            specific_bar_time=symbol.date_time.replace(hour=0, minute=0)
        )


    stop_event = threading.Event()
    threading.Thread(
        target=analyzer_object.analyze_data_retroactively,
        kwargs={
            "stop_event": stop_event,
        }
    ).start()

    while not analyze_finished(
        request_id_to_symbol=request_id_to_symbol,
    ):
        collection_not_finished_count = len(
            [
                symbol
                for _, symbol in request_id_to_symbol.items()
                if symbol.is_day_timeframe()
                and not symbol.finished_collection
            ]
        )

        analyze_not_finished_count = len(
            [
                symbol
                for _, symbol in request_id_to_symbol.items()
                if symbol.is_day_timeframe()
                and not symbol.finished_analyze
            ]
        )
        print(f"collection_left: {collection_not_finished_count}. analyze_left: {analyze_not_finished_count}")
        time.sleep(5)

    stop_event.set()

    ## TODO: need to complete confirmation logic.

    while not confirmation_finished(
        request_id_to_symbol=request_id_to_symbol,
    ):
        print("waiting for confirmation to finish")
        time.sleep(5)

if __name__ == "__main__":
    run_retroactive_check()
