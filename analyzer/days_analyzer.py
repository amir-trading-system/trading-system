import datetime
import logging
import queue

import analyzer.indicators
import common
from tws import client


class Analyzer:
    def __init__(
        self,
        logger: logging.Logger,
        waiting_for_confirmation_queue: queue.Queue[common.objects.BarData],
        request_id_to_symbol: dict[int,common.objects.Stock],
        tws_client: client.Client,
    ):
        self.logger = logger
        self.waiting_for_confirmation_queue = waiting_for_confirmation_queue
        self.tws_client = tws_client

        self.request_id_to_symbol = request_id_to_symbol
        self.has_indication: list[str] = []
        self.symbol_to_last_log_time: dict[str, datetime.datetime] = {}
        self.should_write_log: bool = False

    def _should_write_log(
        self,
        symbol: str,
    ):
        last_log_time = self.symbol_to_last_log_time.get(symbol)
        if last_log_time is None:
            self.symbol_to_last_log_time[symbol] = datetime.datetime.now()
            self.should_write_log = True
        else:
            if last_log_time <= datetime.datetime.now() - datetime.timedelta(minutes=5):
                self.should_write_log = True
                self.symbol_to_last_log_time[symbol] = datetime.datetime.now()

    def _run_indicators(
        self,
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        is_retro: bool,
    ):
        if self.should_write_log:
            self.logger.info(
                msg="Running analyzers",
                extra={
                    "worker": "Analyzer",
                    "symbol": stock.symbol_name,
                    "timeframe": stock.timeframe,
                    "timeframe_type": stock.timeframe_type.value,
                    "bar_time": current_bar.bar_time,
                    "current_index": current_bar.index,
                    "request_id": stock.request_id,
                },
            )

        for indicator in analyzer.indicators.__indicators__:
            unique_key = current_bar.generate_unique_key()
            if unique_key in self.has_indication:
                break

            indicator_obj: analyzer.indicators.indicator.Indicator = indicator(
                milestones=milestones,
                logger=self.logger,
            )
            indication_result: bool = indicator_obj.indicate(
                stock=stock,
                milestones=milestones,
                current_bar=current_bar,
                is_retro=is_retro,
            )
            if indication_result:
                self.request_id_to_symbol[stock.request_id] = stock
                self.logger.info(
                    msg="Bar has Indication, waiting for confirmation",
                    extra={
                        "worker": "Analyzer",
                        "symbol": stock.symbol_name,
                        "timeframe": stock.timeframe,
                        "timeframe_type": stock.timeframe_type.value,
                        "bar_time": current_bar.bar_time,
                        "current_index": current_bar.index,
                        "request_id": stock.request_id,
                    },
                )
                self.waiting_for_confirmation_queue.put(
                    {
                        "bar_to_confirm": current_bar,
                    },
                )
                self.has_indication.append(unique_key)
                break

        self.request_id_to_symbol[stock.request_id].finished_analyze = True
        if self.should_write_log:
            self.logger.info(
                msg="Finished Running analyzers",
                extra={
                    "worker": "Analyzer",
                    "symbol": stock.symbol_name,
                    "timeframe": stock.timeframe,
                    "timeframe_type": stock.timeframe_type.value,
                    "bar_time": current_bar.bar_time,
                    "current_index": current_bar.index,
                    "current_volume": current_bar.volume,
                    "request_id": stock.request_id,
                },
            )

        self.should_write_log = False

    def analyze_bar(
        self,
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ):
        unique_key = current_bar.generate_unique_key()
        if unique_key in self.has_indication:
            return

        self._should_write_log(
            symbol=stock.symbol_name,
        )

        previous_bar = stock.previous_bar(
            bar_object=current_bar,
        )
        if not previous_bar:
            return

        milestones = common.objects.Milestones(
            starting_bar=common.objects.MilestoneBar(
                index=0,
                bar_object=current_bar,
                bar_type=common.objects.MilestoneType.STARTING_BAR,
                bar_time=current_bar.bar_time,
            ),
            top_bar=common.objects.MilestoneBar(
                index=0,
                bar_object=current_bar,
                bar_type=common.objects.MilestoneType.TOP_BAR,
                bar_time=current_bar.bar_time,
            ),
            lowest_low_bar=common.objects.MilestoneBar(
                index=0,
                bar_object=current_bar,
                bar_type=common.objects.MilestoneType.LOWEST_BAR,
                bar_time=current_bar.bar_time,
            ),
            previous_bar=common.objects.MilestoneBar(
                index=previous_bar.index,
                bar_object=previous_bar,
                bar_type=common.objects.MilestoneType.PREVIOUS_BAR,
                bar_time=previous_bar.bar_time,
            ),
            are_valid=True,
        )

        self._run_indicators(
            stock=stock,
            current_bar=current_bar,
            milestones=milestones,
            is_retro=is_retro,
        )
