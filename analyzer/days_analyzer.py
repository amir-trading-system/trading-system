import datetime
import logging
import queue

import alerter
import analyzer.indicators
import analyzer.evidences
import common


class Analyzer:
    def __init__(
        self,
        logger: logging.Logger,
        waiting_for_confirmation_queue: queue.Queue[common.objects.BarData],
        request_id_to_symbol: dict[int,common.objects.Stock],
        alerter_object: alerter.alerter.Alerter = None,
    ):
        self.logger = logger
        self.waiting_for_confirmation_queue = waiting_for_confirmation_queue
        self.alerter_object = alerter_object

        self.request_id_to_symbol = request_id_to_symbol
        self.has_indications_bars: dict[str, common.objects.BarData] = {}
        self.symbol_to_last_log_time: dict[str, datetime.datetime] = {}

    def _run_indicators(
        self,
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        is_retro: bool,
        should_write_log: bool,
        confirmator_only: bool,
    ):
        if should_write_log:
            self.logger.info(
                msg="Running analyzers",
                extra={
                    "worker": "Analyzer",
                    "symbol": stock.symbol_name,
                    "timeframe": stock.timeframe,
                    "timeframe_type": stock.timeframe_type.value,
                    "bar_time": current_bar.bar_time,
                    "current_index": current_bar.index,
                },
            )

        evidences_to_confirm: list[analyzer.evidences._evidence.Evidence] = []
        for indicator in analyzer.indicators.__indicators__:
            indicator_obj: analyzer.indicators.indicator.Indicator = indicator(
                milestones=milestones,
                logger=self.logger,
            )
            indicator_response: common.objects.IndicatorResponse = indicator_obj.indicate(
                stock=stock,
                milestones=milestones,
                current_bar=current_bar,
                is_retro=is_retro,
            )
            if indicator_response.result and indicator_response.success_rate == 1:
                current_bar.indicator = indicator_obj.evidence.name
                self.logger.info(
                    msg="Bar has Indication",
                    extra={
                        "worker": "Analyzer",
                        "symbol": stock.symbol_name,
                        "timeframe": stock.timeframe,
                        "timeframe_type": stock.timeframe_type.value,
                        "bar_time": current_bar.bar_time,
                        "current_index": current_bar.index,
                        "evidence_name": indicator_obj.evidence.name,
                    },
                )

                if self.alerter_object:
                    self.alerter_object.send_alert(
                        sender="Analyzer",
                        stock=stock,
                        current_bar=current_bar,
                        emoji="✅",
                        milestones=milestones,
                        is_retro=is_retro,
                    )

                bar_unique_identifier = current_bar.generate_unique_identifier()
                self.has_indications_bars[bar_unique_identifier] = current_bar
                stock.bars[current_bar.index].has_indication = True
                stock.finished_analyze = True
                evidences_to_confirm.append(indicator_obj.evidence())
                self.request_id_to_symbol[stock.request_id] = stock
            elif confirmator_only:
                evidences_to_confirm.append(indicator_obj.evidence())
                break

        self.waiting_for_confirmation_queue.put(
            {
                "bar_to_confirm": current_bar,
                "milestones": milestones,
                "evidences": evidences_to_confirm,
            },
        )

        if should_write_log:
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
                },
            )

        should_write_log = False

    def analyze_day_bar(
        self,
        stock: common.objects.Stock,
        current_bar: common.objects.BarData,
        is_retro: bool,
        confirmator_only: bool,
    ):
        bar_unique_identifer = current_bar.generate_unique_identifier()
        if bar_unique_identifer in self.has_indications_bars:
            return

        current_bar_is_valid = (
            True
            and (current_bar.close > current_bar.open_value or is_retro)
            and current_bar.histogram > 0
        )
        should_write_log = False
        last_log_time = self.symbol_to_last_log_time.get(stock.symbol_name)
        if last_log_time is None:
            self.symbol_to_last_log_time[stock.symbol_name] = datetime.datetime.now()
            should_write_log = True
        else:
            if last_log_time <= datetime.datetime.now() - datetime.timedelta(minutes=5):
                should_write_log = True
                self.symbol_to_last_log_time[stock.symbol_name] = datetime.datetime.now()

        if not current_bar_is_valid and should_write_log:
            self.logger.info(
                msg="Bar is not valid, analyzer will wait for the next bar",
                extra={
                    "worker": "Analyzer",
                    "symbol": stock.symbol_name,
                    "timeframe": stock.timeframe,
                    "timeframe_type": stock.timeframe_type.value,
                    "bar_time": current_bar.bar_time,
                    "current_index": current_bar.index,
                }
            )
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
            are_valid=True,
        )

        self._run_indicators(
            stock=stock,
            current_bar=current_bar,
            milestones=milestones,
            is_retro=is_retro,
            should_write_log=should_write_log,
            confirmator_only=confirmator_only,
        )
