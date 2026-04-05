import datetime
import logging
import os
import threading
import time
import queue

import alerter
import analyzer
import buying_confirmator
import config_manager
import common
import collector
import logger
import tws

LOGS_PATH = "logs/app.log"
app_logger = logger.logger.Logger(
    enable_stdout=True,
)

def flush_logs():
    last_time_flushed = datetime.datetime.now()

    while True:
        now = datetime.datetime.now()
        if now - datetime.timedelta(
            minutes=1,
        ) > last_time_flushed:
            app_logger.elastic_handler.flush_logs()
        else:
            time.sleep(10)

#pylint:disable=unspecified-encoding
def initiate_potential_symbols(
    file_path: str,
    logger_obj: logging.Logger,
    symbols_queue: queue.Queue[str],
):
    symbol_to_date: dict[str, datetime.datetime] = {}
    lines_to_save: list[str] = []
    unique_symbols: set[str] = set()

    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            return []

    with open(file_path, "r") as f:
        try:
            lines = f.readlines()
            for line in lines:
                [symbol, date] = line.split("--")
                formatted_date = datetime.datetime.fromisoformat(date.replace("\n", ""))
                if (formatted_date + datetime.timedelta(
                    days=15,
                )) >= datetime.datetime.now():
                    symbol_to_date[symbol] = formatted_date
        except FileNotFoundError as e:
            logger_obj.error(
                msg="potential stocks file does not exists",
                extra={
                    "exception": e,
                },
            )

    symbols = sorted(
        symbol_to_date.items(),
        key=lambda item: item[1]
    )
    for symbol_object in symbols:
        symbol, formatted_date = symbol_object
        lines_to_save.append(f"{symbol}--{str(formatted_date)}\n")
        if symbol not in unique_symbols:
            symbols_queue.put(symbol)
            unique_symbols.add(symbol)

    with open(file_path, "w") as f:
        f.writelines(lines_to_save)

def run_bot(
    tws_client_obj: tws.client.Client,
    c_obj: collector.collector.Collector,
    a_obj: analyzer.analyzer.Analyzer,
    co_obj: buying_confirmator.confirmator.Confirmator,
):
    tws_client_obj.start_scanner(
        for_upside_potential=False,
    )

    threading.Thread(
        target=c_obj.collect_data,
    ).start()

    threading.Thread(
        target=a_obj.analyze_data,
        kwargs={
            "is_retro": False,
        },
    ).start()

    threading.Thread(
        target=co_obj.confirm_data,
    ).start()

if __name__ == "__main__":
    if os.path.exists(LOGS_PATH):
        os.remove(LOGS_PATH)

    configuration: config_manager.BotConfig = config_manager.ConfigManager().load_config()
    symbols_to_collect_queue: queue.Queue[str] = queue.Queue()
    bars_ready_to_analyze_queue: queue.Queue[common.objects.Stock] = queue.Queue()
    waiting_for_confirmation_queue: queue.Queue[dict[str, common.objects.BarData|common.objects.Milestones]] = queue.Queue()
    results_queue: queue.Queue[dict[str, any]] = queue.Queue()
    request_id_to_symbol: dict[int,common.objects.Stock] = {}
    logger_object = app_logger.get_logger()

    initiate_potential_symbols(
        file_path=configuration.potential_symbols_file_path,
        logger_obj=logger_object,
        symbols_queue=symbols_to_collect_queue,
    )
    alerter_object = alerter.alerter.Alerter(
        logger=logger_object,
        configuration=configuration.alerts,
    )
    tws_client = tws.client.Client(
        host="localhost",
        port=8081,
        symbols_to_collect_queue=symbols_to_collect_queue,
        bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
        client_id=0,
        is_retro=False,
        get_only_statistics=False,
    )
    collector_obj = collector.collector.Collector(
        tws_client=tws_client,
        request_id_to_symbol=request_id_to_symbol,
        logger=logger_object,
    )
    analyzer_obj = analyzer.analyzer.Analyzer(
        bars_ready_to_analyze_queue=bars_ready_to_analyze_queue,
        waiting_for_confirmation_queue=waiting_for_confirmation_queue,
        request_id_to_symbol=request_id_to_symbol,
        alerter_object=alerter_object,
        tws_client=tws_client,
        logger=logger_object,
    )
    confirmator_obj = buying_confirmator.confirmator.Confirmator(
        tws_client=tws_client,
        waiting_for_confirmation_queue=waiting_for_confirmation_queue,
        results_queue=results_queue,
        request_id_to_symbol=request_id_to_symbol,
        alerter_object=alerter_object,
        logger=logger_object,
        should_run_model=True,
        is_retro=False,
    )

    threading.Thread(
        target=flush_logs,
    ).start()

    threading.Thread(
        target=tws_client.run
    ).start()
    time.sleep(1)

    run_bot(
        tws_client_obj=tws_client,
        c_obj=collector_obj,
        a_obj=analyzer_obj,
        co_obj=confirmator_obj,
    )
