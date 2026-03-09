import datetime
import os
import sys
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
from scripts import stock_finder
import tws

LOGS_PATH = "logs/app.log"
app_logger = logger.logger.Logger(
    enable_stdout=False,
)

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

def get_symbols() -> list[Symbol]:
    return [
        Symbol(
            name="EPSM",
            datetime_str="11.20.25T11:06:00",
        ),
        Symbol(
            name="CYCU",
            datetime_str="11.14.25T12:42:00",
        ),
        Symbol(
            name="TWG",
            datetime_str="12.08.25T13:10:00",
        ),
        Symbol(
            name="AFJK",
            datetime_str="12.09.25T10:35:00",
        ),
        Symbol(
            name="QCLS",
            datetime_str="12.04.25T09:43:00",
        ),
        Symbol(
            name="BBGI",
            datetime_str="12.10.25T09:45:00",
        ),
        Symbol(
            name="ASPC",
            datetime_str="12.26.25T12:25:00",
        ),
        Symbol(
            name="MBAI",
            datetime_str="01.26.26T10:22:00",
        ),
        Symbol(
            name="INBS",
            datetime_str="12.31.25T12:52:00",
        ),
        Symbol(
            name="INBS",
            datetime_str="01.05.26T12:22:00",
        ),
        Symbol(
            name="AUST",
            datetime_str="01.23.26T09:42:00",
        ),
        Symbol(
            name="MOVE",
            datetime_str="01.27.26T09:57:00",
        ),
        Symbol(
            name="GITS",
            datetime_str="01.21.26T09:42:00",
        ),
        Symbol(
            name="GITS",
            datetime_str="01.27.26T10:05:00",
        ),
        Symbol(
            name="NAMM",
            datetime_str="01.22.26T10:30:00",
        ),
        Symbol(
            name="NAMM",
            datetime_str="01.28.26T14:51:00",
        ),
        Symbol(
            name="DRMA",
            datetime_str="01.26.26T12:18:00",
        ),
        Symbol(
            name="RIME",
            datetime_str="02.13.26T14:11:00",
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
            datetime_str="01.23.26T09:37:00",
        ),
        Symbol(
            name="BNAI",
            datetime_str="01.28.26T09:39:00",
        ),
        Symbol(
            name="FEED",
            datetime_str="01.29.26T09:40:00",
        ),
        Symbol(
            name="FEED",
            datetime_str="01.30.26T09:57:00",
        ),
        Symbol(
            name="CATX",
            datetime_str="01.29.26T10:26:00",
        ),
        Symbol(
            name="CATX",
            datetime_str="02.02.26T10:48:00",
        ),
        Symbol(
            name="PLBY",
            datetime_str="02.10.26T09:49:00",
        ),
        Symbol(
            name="SUNE",
            datetime_str="02.10.26T09:48:00",
        ),
        Symbol(
            name="QVCGP",
            datetime_str="02.11.26T10:22:00",
        ),
        Symbol(
            name="NCI",
            datetime_str="02.11.26T11:00:00",
        ),
        Symbol(
            name="ATOM",
            datetime_str="02.17.26T09:31:00",
        ),
        Symbol(
            name="MLEC",
            datetime_str="01.15.26T11:28:00",
        ),
        Symbol(
            name="MLEC",
            datetime_str="02.18.26T09:47:00",
        ),
        Symbol(
            name="FJET",
            datetime_str="02.18.26T09:34:00",
        ),
        Symbol(
            name="FJET",
            datetime_str="02.19.26T10:18:00",
        ),
        Symbol(
            name="LRMR",
            datetime_str="02.25.26T09:32:00",
        ),
        Symbol(
            name="RXT",
            datetime_str="02.19.26T15:12:00",
        ),
        Symbol(
            name="RXT",
            datetime_str="02.26.26T10:55:00",
        ),
        Symbol(
            name="XWEL",
            datetime_str="02.27.26T09:32:00",
        ),
        Symbol(
            name="EDSA",
            datetime_str="03.03.26T09:31:00",
        ),
        Symbol(
            name="BATL",
            datetime_str="03.04.26T11:27:00",
        ),
        Symbol(
            name="BATL",
            datetime_str="03.05.26T09:31:00",
        ),
        Symbol(
            name="TPET",
            datetime_str="03.05.26T09:35:00",
        ),
        Symbol(
            name="TMDE",
            datetime_str="03.05.26T09:59:00",
        ),
    ]

def build_table(
    data: list[dict[str, str]],
) -> rich.table.Table:
    finished_collection = len(
        [
            symbol_data
            for symbol_data in data
            if symbol_data["collection_status"] == "done"
        ]
    )
    finished_analysis = len(
        [
            symbol_data
            for symbol_data in data
            if symbol_data["analysis_status"] == "done"
        ]
    )
    finished_confirmation = len(
        [
            symbol_data
            for symbol_data in data
            if symbol_data["actual_confirmation_bar_time"] != "in_progress"
        ]
    )
    table = rich.table.Table(
        "Symbol",
        "Original Bar Time",
        f"Collection Status: {finished_collection}/{len(data)}",
        f"Analysis Status: {finished_analysis}/{len(data)}",
        f"Actual Confirmation Bar Time {finished_confirmation}/{len(data)}",
        "Expected Confirmation Bar Time",
        "Evidence",
    )
    sorted_data_by_original_date = sorted(
        data,
        key=lambda symbol_data: symbol_data["symbol"],
    )

    for symbol_data in sorted_data_by_original_date:
        symbol = symbol_data["symbol"]
        original_bar_time = symbol_data["original_bar_time"]

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

        evidence_name = symbol_data["evidence_name"]
        if evidence_name == "in_progress":
            evidence_name = f"[red]{evidence_name}[/red]"
        elif symbol_data["is_new"]:
            evidence_name = f"[bold yellow]{evidence_name}[/bold yellow]"
        else:
            evidence_name = f"[green]{evidence_name}[/green]"

        actual_confirmation_bar_time = symbol_data["actual_confirmation_bar_time"]
        expected_confirmation_bar_time = symbol_data["expected_confirmation_bar_time"]

        if actual_confirmation_bar_time == expected_confirmation_bar_time:
            actual_confirmation_bar_time = f"[green]{actual_confirmation_bar_time}[/green]"
        else:
            actual_confirmation_bar_time = f"[red]{actual_confirmation_bar_time}[/red]"

        if symbol_data["is_new"]:
            row_style = "bold yellow"
            symbol = f"[{row_style}]{symbol}[/{row_style}]"

        table.add_row(
            symbol,
            str(original_bar_time),
            collection_status,
            analysis_status,
            str(actual_confirmation_bar_time),
            str(expected_confirmation_bar_time),
            evidence_name,
        )

    return table

def update_table_with_status_per_stage(
    symbols_data: list[dict[str,any]],
    request_id_to_symbol: dict[int,common.objects.Stock],
    live_table: rich.live.Live,
):
    while any(
        symbol_data
        for symbol_data in symbols_data
        if symbol_data["actual_confirmation_bar_time"] == "in_progress"
    ):
        for _, symbol in request_id_to_symbol.items():
            if symbol.is_one_minute_timeframe():
                continue

            relevant_symbol_data = [
                symbol_data
                for symbol_data in symbols_data
                if symbol_data["symbol"] == symbol.symbol_name
                and symbol_data["original_bar_time"] == symbol.specific_bar_time
            ][0]
            if symbol.finished_collection and symbol.is_day_timeframe() and relevant_symbol_data["collection_status"] != "done":
                relevant_symbol_data["collection_status"] = "done"
            if symbol.finished_analyze and symbol.is_day_timeframe() and relevant_symbol_data["analysis_status"] != "done":
                relevant_symbol_data["analysis_status"] = "done"

            live_table.update(build_table(symbols_data), refresh=True)

def update_table_with_results_queue(
    results_queue: queue.Queue[dict[str,any]],
    symbols_data: list[dict[str,any]],
    live_table: rich.live.Live,
    counter: list[int],
):
    while True:
        confirmation_result = results_queue.get()
        relevant_symbol_data = [
            symbol_data
            for symbol_data in symbols_data
            if symbol_data["symbol"] == confirmation_result["symbol"]
            and symbol_data["original_bar_time"] == confirmation_result["original_bar_time"]
            and symbol_data["evidence_name"] == "in_progress"
        ]
        should_update_first_default = True

        for evidence_name in confirmation_result["evidences"]:
            if should_update_first_default and relevant_symbol_data:
                relevant_symbol_data[0]["actual_confirmation_bar_time"] = confirmation_result["confirmation_bar_time"]
                relevant_symbol_data[0]["evidence_name"] = evidence_name
                relevant_symbol_data[0]["collection_status"] = "done"
                relevant_symbol_data[0]["analysis_status"] = "done"
                should_update_first_default = False
                continue

            symbols_data.append(
                {
                    "symbol": confirmation_result["symbol"],
                    "collection_status": "done",
                    "analysis_status": "done",
                    "original_bar_time": confirmation_result["original_bar_time"],
                    "actual_confirmation_bar_time": confirmation_result["confirmation_bar_time"],
                    "expected_confirmation_bar_time": confirmation_result["confirmation_bar_time"],
                    "evidence_name": evidence_name,
                    "is_new": True,
                },
            )

        live_table.update(build_table(symbols_data), refresh=True)
        counter[0] -= 1

def flush_logs():
    last_time_flushed = datetime.datetime.now()

    while True:
        now = datetime.datetime.now()
        if now - datetime.timedelta(
            minutes=1,
        ) > last_time_flushed:
            app_logger.elastic_handler.flush_logs()
            last_time_flushed = datetime.datetime.now()
        else:
            time.sleep(1)

def run_retroactive_check():
    symbols_data = []
    symbols = get_symbols()
    # symbols = [
    #     Symbol(
    #         name=symbol,
    #         datetime_str=date,
    #     )
    #     for symbol, date in stock_finder.get_dynamic_symbols_from_last_month().items()
    # ]
    # symbols = [
    #     Symbol(
    #         name="BATL",
    #         datetime_str="03.04.26T11:27:00",
    #     ),
    # ]

    symbols_to_collect_queue: queue.Queue[str] = queue.Queue()
    bars_ready_to_analyze_queue: queue.Queue[common.objects.Stock] = queue.Queue()
    waiting_for_confirmation_queue: queue.Queue[dict[str, common.objects.BarData|common.objects.Milestones]] = queue.Queue()
    results_queue: queue.Queue[dict[str,any]] = queue.Queue()
    request_id_to_symbol: dict[int,common.objects.Stock] = {}

    logger_object = app_logger.get_logger()
    tws_client = tws.client.Client(
        host="localhost",
        port=8081,
        symbols_to_collect_queue=symbols_to_collect_queue,
        bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
        request_id_to_symbol=request_id_to_symbol,
        monitored_symbols=[s.name for s in symbols],
        logger=logger_object,
    )

    threading.Thread(
        target=flush_logs,
    ).start()

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
        tws_client=tws_client,
        logger=logger_object,
    )
    # analyzer_object.confirmator_only = True

    confirmator_object = buying_confirmator.confirmator.Confirmator(
        tws_client=tws_client,
        waiting_for_confirmation_queue=waiting_for_confirmation_queue,
        results_queue=results_queue,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
        is_retro=True,
        # confirmation_only=True,
    )

    threading.Thread(
        target=analyzer_object.analyze_data,
        kwargs={
            "is_retro": True,
        },
    ).start()

    threading.Thread(
        target=confirmator_object.confirm_data,
    ).start()

    counter = [len(symbols)]

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
                "collection_status": "in_progress",
                "analysis_status": "in_progress",
                "original_bar_time": specific_bar_time,
                "actual_confirmation_bar_time": "in_progress",
                "expected_confirmation_bar_time": symbol.date_time,
                "evidence_name": "in_progress",
                "is_new": False,
            },
        )

    with rich.live.Live(build_table(symbols_data), refresh_per_second=4) as live_table:
        threading.Thread(
            target=update_table_with_status_per_stage,
            kwargs={
                "symbols_data": symbols_data,
                "request_id_to_symbol": request_id_to_symbol,
                "live_table": live_table,
            }
        ).start()

        threading.Thread(
            target=update_table_with_results_queue,
            kwargs={
                "results_queue": results_queue,
                "symbols_data": symbols_data,
                "counter": counter,
                "live_table": live_table,
            },
        ).start()

        while True:
            if counter[0] == 0:
                break

    sys.exit(0)

if __name__ == "__main__":
    if os.path.exists(LOGS_PATH):
        os.remove(LOGS_PATH)
    run_retroactive_check()
