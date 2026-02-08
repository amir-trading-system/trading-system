import datetime
import threading
import time
import queue

import rich
import rich.live
import rich.table

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

def build_table(
    data: list[dict[str, str]],
) -> rich.table.Table:
    table = rich.table.Table(
        "Symbol", "Original Bar Time", "Collection Status", "Analysis Status", "Confirmation Status", "Actual Confirmation Bar Time", "Expected Confirmation Bar Time"
    )

    for symbol_data in data:
        collection_status = symbol_data["collection_status"]
        if collection_status != "done":
            collection_status = f"[red]{collection_status}[/red]"
        else:
            collection_status = f"[green]{collection_status}[/green]"

        analysis_status = symbol_data["analysis_status"]
        if analysis_status != "done":
            analysis_status = f"[red]{analysis_status}[/red]"
        else:
            analysis_status = f"[green]{analysis_status}[/green]"

        confirmation_status = symbol_data["confirmation_status"]
        if confirmation_status != "done":
            confirmation_status = f"[red]{confirmation_status}[/red]"
        else:
            confirmation_status = f"[green]{confirmation_status}[/green]"

        actual_confirmation_bar_time = symbol_data["actual_confirmation_bar_time"]
        expected_confirmation_bar_time = symbol_data["expected_confirmation_bar_time"]

        if actual_confirmation_bar_time == expected_confirmation_bar_time:
            actual_confirmation_bar_time = f"[green]{actual_confirmation_bar_time}[/green]"
        else:
            actual_confirmation_bar_time = f"[red]{actual_confirmation_bar_time}[/red]"

        table.add_row(
            symbol_data["symbol"],
            symbol_data["original_bar_time"],
            collection_status,
            analysis_status,
            confirmation_status,
            actual_confirmation_bar_time,
            expected_confirmation_bar_time,
        )

    return table

def run_retroactive_check():
    symbols_to_collect_queue: queue.Queue[str] = queue.Queue()
    bars_ready_to_analyze_queue: queue.Queue[common.objects.Stock] = queue.Queue()
    waiting_for_confirmation_queue: queue.Queue[dict[str, common.objects.BarData|common.objects.Milestones]] = queue.Queue()
    results_queue: queue.Queue[dict[str,any]] = queue.Queue()
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
        results_queue=results_queue,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
        is_retro=True,
    )

    analyze_stop_event = threading.Event()
    threading.Thread(
        target=analyzer_object.analyze_data_retroactively,
        kwargs={
            "stop_event": analyze_stop_event,
        }
    ).start()

    confirmator_stop_event = threading.Event()
    threading.Thread(
        target=confirmator_object.confirm_data,
        kwargs={
            "stop_event": confirmator_stop_event,
        }
    ).start()

    symbols_data = []
    symbols = get_symbols()
    for symbol in symbols:
        specific_bar_time = symbol.date_time.replace(hour=0, minute=0)
        collector_object.collect_data_retroactively(
            symbol=symbol.name,
            manual_timeframe_for_tests=common.objects.TimeframeInput(
                timeframe=1,
                timeframe_type=common.objects.TimeframeType(2),
            ),
            specific_bar_time=specific_bar_time,
        )
        symbols_data.append(
            {
                "symbol": symbol.name,
                "collection_status": "unknown",
                "analysis_status": "unknown",
                "confirmation_status": "unknown",
                "original_bar_time": str(specific_bar_time),
                "actual_confirmation_bar_time": "unknown",
                "expected_confirmation_bar_time": str(symbol.date_time),
            },
        )

    with rich.live.Live(build_table(symbols_data), refresh_per_second=2) as live:
        while any(
            symbol_data
            for symbol_data in symbols_data
            if symbol_data["confirmation_status"] != "done"
        ):
            for _, symbol in request_id_to_symbol.items():
                if symbol.is_one_minute_timeframe():
                    continue

                relevant_symbol_data = [
                    symbol_data
                    for symbol_data in symbols_data
                    if symbol_data["symbol"] == symbol.symbol_name
                    and symbol_data["original_bar_time"] == str(symbol.specific_bar_time)
                ][0]
                if symbol.finished_collection and symbol.is_day_timeframe():
                    relevant_symbol_data["collection_status"] = "done"
                if symbol.finished_analyze and symbol.is_day_timeframe():
                    relevant_symbol_data["analysis_status"] = "done"
                if symbol.finished_confirmation and symbol.is_day_timeframe():
                    relevant_symbol_data["confirmation_status"] = "done"

                live.update(build_table(symbols_data))
                time.sleep(1)

        while not results_queue.empty():
            confirmation_result = results_queue.get()
            relevant_symbol_data = [
                symbol_data
                for symbol_data in symbols_data
                if symbol_data["symbol"] == confirmation_result["symbol"]
                and symbol_data["original_bar_time"] == str(confirmation_result["original_bar_time"])
            ][0]
            relevant_symbol_data["actual_confirmation_bar_time"] = str(confirmation_result["confirmation_bar_time"])
            live.update(build_table(symbols_data))

        time.sleep(1)

    analyze_stop_event.set()
    confirmator_stop_event.set()


if __name__ == "__main__":
    run_retroactive_check()
