import datetime
import logging
import queue

import alerter
import analyzer.evidences
import common
import model
from tws import client


class Confirmator:
    def __init__(
        self,
        is_retro: bool,
        should_run_model: bool,
        tws_client: client.Client,
        logger: logging.Logger,
        request_id_to_symbol: dict[int,common.objects.Stock],
        results_queue: queue.Queue[dict[str,any]],
        alerter_object: alerter.alerter.Alerter = None,
    ):
        self.tws_client = tws_client
        self.is_retro = is_retro
        self.logger = logger
        self.alerter_object = alerter_object
        self.results_queue = results_queue
        self.request_id_to_symbol = request_id_to_symbol
        self.model_runner = model.runner.Runner(
            should_run_model=should_run_model,
        )

    def _confirm(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        one_minute_bars: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
        original_bar_to_confirm: common.objects.BarData,
        highest_high_one_minute_bar: common.objects.BarData,
        already_sent_buy_order_for_stock: dict[str,bool],
    ) -> bool:
        bar_has_confirmed: bool = False
        entry_position_bar: common.objects.BarData = None
        one_minute_bars.append(potential_confirmation_bar)
        confirmed_evidence: str = ""

        if (
            True
            and self.is_retro
            and potential_confirmation_bar.bar_time > datetime.datetime(
                year=potential_confirmation_bar.bar_time.year,
                month=potential_confirmation_bar.bar_time.month,
                day=potential_confirmation_bar.bar_time.day,
                hour=16,
            )
        ):
            self.results_queue.put(
                {
                    "symbol": stock.symbol_name,
                    "original_bar_time": original_bar_to_confirm.bar_time,
                    "confirmation_bar_time": None,
                    "evidences": "",
                    "price_movement_statistics": {},
                    "score": 0,
                },
            )
            return True

        one_minute_timeframe_stock = self.request_id_to_symbol[stock.one_minute_request_id]
        highest_high_one_minute_bar = one_minute_timeframe_stock.get_highest_high_one_minute_bar(
            current_one_minute_bar=potential_confirmation_bar,
        )

        stock.volume_sum_since_4_am_today = one_minute_timeframe_stock.get_volume_sum_since_04_am_today(
            current_one_minute_bar=potential_confirmation_bar,
        )
        stock.volume_sum_since_market_open = one_minute_timeframe_stock.get_volume_sum_since_market_open(
            current_one_minute_bar=potential_confirmation_bar,
        )

        temp_one_minute_bars = sorted(
            [
                one_minute_bar
                for one_minute_bar in one_minute_bars
                if one_minute_bar.bar_time <= potential_confirmation_bar.bar_time
            ],
            key=lambda bar_object: bar_object.bar_time,
            reverse=True
        )

        highest_high: float = max(
            highest_high_one_minute_bar.high if highest_high_one_minute_bar is not None else 0,
            stock.last_post_pre_one_minute_highest_high,
        )

        if not self.bar_has_potential(
            stock=stock,
            original_bar_to_confirm=original_bar_to_confirm,
            potential_confirmation_bar=potential_confirmation_bar,
            one_minute_bars=temp_one_minute_bars,
            highest_high=highest_high,
        ):
            return bar_has_confirmed

        stock_is_valid_for_evidence = False
        transmit_order = False
        score = common.objects.Score(
            score=0.0,
            probability=0.0,
            threshold=0.0,
            should_take_trade=False,
        )

        for evidence in analyzer.evidences.__evidences__:
            evidence_obj = evidence(
                logger=self.logger,
                stock=stock,
            )
            if (
                not stock_is_valid_for_evidence
                and not evidence_obj.relevant_bars
            ):
                break

            stock_is_valid_for_evidence = True
            if not evidence_obj.find_evidence(
                stock=stock,
                milestones=milestones,
                current_bar=original_bar_to_confirm,
                is_retro=self.is_retro,
            ):
                continue

            one_minute_timeframe_stock = self.request_id_to_symbol[stock.one_minute_request_id]

            if not evidence_obj.confirm(
                stock=stock,
                original_bar_to_confirm=original_bar_to_confirm,
                potential_confirmation_bar=potential_confirmation_bar,
                milestones=milestones,
                highest_high_one_minute_bar=highest_high_one_minute_bar,
                one_minute_bars=temp_one_minute_bars,
            ):
                continue

            self.logger.info(
                msg="Potential confirmation bar has passed static confirmation, waiting for model confirmation",
                extra={
                    "worker": "Confirmator",
                    "symbol": stock.symbol_name,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "entry_position_bar_time": potential_confirmation_bar.bar_time,
                    "evidence_name": evidence_obj.name,
                    "request_id": stock.request_id,
                },
            )

            potential_confirmation_bar.price_movement_statistics = model.data_extractor.DataExtractor.extract_features_from_symbol_data(
                day_timeframe_stock=stock,
                one_minute_timeframe_stock=one_minute_timeframe_stock,
                potential_confirmation_bar=potential_confirmation_bar,
                highest_high_one_minute_bar=highest_high_one_minute_bar,
                volume_sum_since_market_open=stock.volume_sum_since_market_open,
                one_minute_bars=one_minute_bars,
            )

            total_volume = potential_confirmation_bar.price_movement_statistics.get("feature_total_volume")
            if (
                True
                and total_volume is not None
            ):
                if (
                    total_volume < 300000
                    or (
                        potential_confirmation_bar.volume/total_volume < 0.02
                        and potential_confirmation_bar.volume < 50000
                    )
                ):
                    return bar_has_confirmed

            if self.model_runner.should_run_model:
                score: common.objects.Score = self.model_runner.score_potential_confirmation_bar(
                    potential_confirmation_bar=potential_confirmation_bar,
                )

                msg = "Bar confirmed by model"

                if not score.should_take_trade:
                    msg = "Bar confirmed by static confirmation, but got denied on model confirmation"
                    bar_has_confirmed = False
                else:
                    bar_has_confirmed = True
                    entry_position_bar = potential_confirmation_bar
                    confirmed_evidence = evidence_obj.name

                self.logger.info(
                    msg=msg,
                    extra={
                        "worker": "Confirmator",
                        "symbol": stock.symbol_name,
                        "timeframe": original_bar_to_confirm.timeframe,
                        "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                        "bar_time": original_bar_to_confirm.bar_time,
                        "entry_position_bar_time": potential_confirmation_bar.bar_time,
                        "evidence_name": evidence_obj.name,
                        "request_id": stock.request_id,
                        "score": score.score,
                        "probability": score.probability,
                        "threshold": score.threshold,
                    },
                )

                break

            else:
                score.should_take_trade = True

        if entry_position_bar is not None:
            self.results_queue.put(
                {
                    "symbol": stock.symbol_name,
                    "original_bar_time": original_bar_to_confirm.bar_time,
                    "confirmation_bar_time": entry_position_bar.bar_time,
                    "evidences": confirmed_evidence,
                    "price_movement_statistics": entry_position_bar.price_movement_statistics,
                    "score": score.score if score is not None else 0,
                },
            )

            self.logger.info(
                "Bar has confirmed",
                extra={
                    "worker": "Confirmator",
                    "symbol": original_bar_to_confirm.symbol,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "entry_position_bar_time": entry_position_bar.bar_time,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "evidence_name": confirmed_evidence,
                    "request_id": stock.request_id,
                },
            )

            if self.alerter_object:
                self.alerter_object.send_confirmation_alert(
                    sender="Confirmator",
                    stock=stock,
                    original_bar=original_bar_to_confirm,
                    entry_position_bar=entry_position_bar,
                    evidence_name=confirmed_evidence,
                    is_retro=self.is_retro,
                    request_id=stock.request_id,
                    transmit=transmit_order,
                )

            unique_key_for_place_order = original_bar_to_confirm.symbol
            if self.is_retro:
                unique_key_for_place_order = f"{original_bar_to_confirm.symbol}-{stock.specific_bar_time}"
            if (
                not already_sent_buy_order_for_stock.get(unique_key_for_place_order, False)
            ):
                already_sent_buy_order_for_stock[unique_key_for_place_order] = True
                bar_has_confirmed = True

                if self.is_retro or not self.model_runner.should_run_model:
                    return bar_has_confirmed

                if score.should_take_trade and score.score > 0:
                    # transmit_order = potential_confirmation_bar.bar_time >= datetime.datetime(
                    #     year=potential_confirmation_bar.bar_time.year,
                    #     month=potential_confirmation_bar.bar_time.month,
                    #     day=potential_confirmation_bar.bar_time.day,
                    #     hour=9,
                    #     minute=40,
                    # )
                    # need to remove it
                    transmit_order = False

                self.tws_client.place_buy_order(
                    symbol=original_bar_to_confirm.symbol,
                    current_price=entry_position_bar.close,
                    transmit=transmit_order,
                    score=score,
                )

        return bar_has_confirmed

    def should_write_log(
        self,
        most_updated_datetime: datetime.datetime,
        potential_confirmation_bar: common.objects.BarData,
        original_bar_to_confirm: common.objects.BarData,
    ) -> bool:
        return (
            True
            and most_updated_datetime < potential_confirmation_bar.bar_time
            and potential_confirmation_bar.close > potential_confirmation_bar.open_value
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and potential_confirmation_bar.high > potential_confirmation_bar.ema_9
            and potential_confirmation_bar.high > potential_confirmation_bar.ema_20
            and potential_confirmation_bar.high > potential_confirmation_bar.vwap
            and potential_confirmation_bar.bar_time >= datetime.datetime(
                year=original_bar_to_confirm.bar_time.year,
                month=original_bar_to_confirm.bar_time.month,
                day=original_bar_to_confirm.bar_time.day,
                hour=9,
                minute=30,
            )
        )

    def confirm_entry_position(
        self,
        stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        milestones: common.objects.Milestones,
    ):
        one_minute_bars: list[common.objects.BarData] = []
        highest_high_one_minute_bar: common.objects.BarData = None
        lowest_low_one_minute_bar: common.objects.BarData = None
        most_updated_datetime = datetime.datetime.fromtimestamp(0)
        already_sent_buy_order_for_stock: dict[str,bool] = {}
        stock.bars = sorted(
            stock.bars,
            key=lambda bar_object: bar_object.bar_time,
            reverse=True,
        )
        potential_confirmation_bar = None

        while True:
            if (
                True
                and potential_confirmation_bar is not None
                and highest_high_one_minute_bar is not None
                and potential_confirmation_bar.high > highest_high_one_minute_bar.high
                and potential_confirmation_bar.bar_time >= datetime.datetime(
                    year=original_bar_to_confirm.bar_time.year,
                    month=original_bar_to_confirm.bar_time.month,
                    day=original_bar_to_confirm.bar_time.day,
                    hour=4,
                )
                and highest_high_one_minute_bar.index - 1 > potential_confirmation_bar.index
            ):
                highest_high_one_minute_bar = potential_confirmation_bar

            if (
                True
                and potential_confirmation_bar is not None
                and lowest_low_one_minute_bar is not None
                and potential_confirmation_bar.low < lowest_low_one_minute_bar.low
                and potential_confirmation_bar.bar_time >= datetime.datetime(
                    year=original_bar_to_confirm.bar_time.year,
                    month=original_bar_to_confirm.bar_time.month,
                    day=original_bar_to_confirm.bar_time.day,
                    hour=4,
                )
            ):
                lowest_low_one_minute_bar = potential_confirmation_bar

            potential_confirmation_bar = stock.one_minute_bars_queue.get()

            if highest_high_one_minute_bar is None:
                highest_high_one_minute_bar = potential_confirmation_bar
            if lowest_low_one_minute_bar is None:
                lowest_low_one_minute_bar = potential_confirmation_bar

            stock.one_minute_bars_queue.task_done()
            date_now = datetime.datetime.now()

            if (
                potential_confirmation_bar.bar_time < datetime.datetime(
                    year=original_bar_to_confirm.bar_time.year,
                    month=original_bar_to_confirm.bar_time.month,
                    day=original_bar_to_confirm.bar_time.day,
                    hour=4,
                )
                or potential_confirmation_bar.bar_time < most_updated_datetime
                or not potential_confirmation_bar.ready_to_analyze
                or not potential_confirmation_bar.histogram
                or (
                    not self.is_retro
                    and potential_confirmation_bar.bar_time < datetime.datetime(
                        year=date_now.year,
                        month=date_now.month,
                        day=date_now.day,
                        hour=date_now.hour,
                        minute=date_now.minute-1 if date_now.minute > 0 else 59,
                    )
                )
            ):
                continue

            self.logger.info(
                msg="Starting to confirm one minute bar for entry point",
                extra={
                    "worker": "Confirmator",
                    "symbol": original_bar_to_confirm.symbol,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "entry_position_bar_time": potential_confirmation_bar.bar_time,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "request_id": stock.request_id,
                    "high": potential_confirmation_bar.high,
                    "low": potential_confirmation_bar.low,
                    "open": potential_confirmation_bar.open_value,
                    "close": potential_confirmation_bar.close,
                    "collection_finished_time": potential_confirmation_bar.collection_finished_time,
                },
            )

            if potential_confirmation_bar.bar_time == datetime.datetime(
                year=original_bar_to_confirm.bar_time.year,
                month=original_bar_to_confirm.bar_time.month,
                day=original_bar_to_confirm.bar_time.day,
                hour=9,
                minute=30,
            ):
                highest_high_one_minute_bar = potential_confirmation_bar
                lowest_low_one_minute_bar = potential_confirmation_bar

            if self._confirm(
                stock=stock,
                milestones=milestones,
                one_minute_bars=one_minute_bars,
                potential_confirmation_bar=potential_confirmation_bar,
                original_bar_to_confirm=original_bar_to_confirm,
                highest_high_one_minute_bar=highest_high_one_minute_bar,
                already_sent_buy_order_for_stock=already_sent_buy_order_for_stock,
            ):
                continue

            most_updated_datetime = potential_confirmation_bar.bar_time
            self.logger.info(
                msg="Entry point does not confirmed yet, waiting for next one",
                extra={
                    "worker": "Confirmator",
                    "symbol": original_bar_to_confirm.symbol,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "entry_position_bar_time": potential_confirmation_bar.bar_time,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "request_id": stock.request_id,
                },
            )

        return

    def bar_has_potential(
        self,
        stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
        highest_high: float,
    ) -> bool:
        today_09_30 = datetime.datetime(
            year=original_bar_to_confirm.bar_time.year,
            month=original_bar_to_confirm.bar_time.month,
            day=original_bar_to_confirm.bar_time.day,
            hour=9,
            minute=30,
        )
        today_10_00 = datetime.datetime(
            year=original_bar_to_confirm.bar_time.year,
            month=original_bar_to_confirm.bar_time.month,
            day=original_bar_to_confirm.bar_time.day,
            hour=10,
            minute=00,
        )
        today_12_00 = datetime.datetime(
            year=original_bar_to_confirm.bar_time.year,
            month=original_bar_to_confirm.bar_time.month,
            day=original_bar_to_confirm.bar_time.day,
            hour=12,
            minute=00,
        )

        highest_high = round(highest_high, 2)
        if potential_confirmation_bar.close < 1.0:
            return False

        crossed_any_resistance = any(
            r_l
            for r_l in stock.resistance_levels
            if potential_confirmation_bar.low < r_l.high < potential_confirmation_bar.close
        )
        crossed_highest_high = round(potential_confirmation_bar.low, 2) < highest_high < round(potential_confirmation_bar.close, 2)

        if potential_confirmation_bar.bar_time < datetime.datetime(
            year=potential_confirmation_bar.bar_time.year,
            month=potential_confirmation_bar.bar_time.month,
            day=potential_confirmation_bar.bar_time.day,
            hour=9,
            minute=40,
        ):
            return False

        if not crossed_highest_high:
            return False

        should_wait_for_next_bar = (
            potential_confirmation_bar.bar_time < today_09_30
            or potential_confirmation_bar.volume < 20000
            or stock.volume_sum_since_market_open < 100000
            or (
                today_10_00 <= potential_confirmation_bar.bar_time <= today_12_00
                and stock.volume_sum_since_market_open < 500000
            )
            or (
                potential_confirmation_bar.bar_time > today_12_00
                and stock.volume_sum_since_market_open < 1000000
            )
        )

        bar_is_strong_than_before = (
            True
            and potential_confirmation_bar.bar_up_percentage >= 0.03
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
        )

        if should_wait_for_next_bar and not bar_is_strong_than_before:
            return False

        if (
            True
            and potential_confirmation_bar.low - potential_confirmation_bar.ema_9 > potential_confirmation_bar.close - potential_confirmation_bar.low
            and not crossed_any_resistance
            and not crossed_highest_high
        ):
            return False

        if highest_high >= potential_confirmation_bar.close:
            return False

        if self.highest_high_occurred_more_than_once_in_the_last_bars(
            stock=stock,
            potential_confirmation_bar=potential_confirmation_bar,
            one_minute_bars=one_minute_bars,
        ):
            return False

        if potential_confirmation_bar.buyers_are_indecision:
            return False

        if any(
            r_l
            for r_l in stock.resistance_levels
            if r_l.high > potential_confirmation_bar.high
            and potential_confirmation_bar.high/r_l.high > 0.9
            and potential_confirmation_bar.bar_wick_percentage > 0.4
        ):
            return False

        if (
            True
            and len(stock.bars) > 1
            and (
                stock.bars[1].close > potential_confirmation_bar.high
                or 0.9 < potential_confirmation_bar.high/stock.bars[1].high <= 1
            )
        ):
            return False

        # need to check it carefully
        # if 0.95 <= potential_confirmation_bar.high/original_bar_to_confirm.ema_20 <= 1.05:
        #     return False

        return True

    def highest_high_occurred_more_than_once_in_the_last_bars(
        self,
        stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
    ) -> bool:
        if len(one_minute_bars) < 3:
            return False

        current_bar_is_highest_high = max(
            bar_object.high
            for bar_object in one_minute_bars
        ) == potential_confirmation_bar.high

        previous_bar_was_highest_high = max(
            bar_object.high
            for bar_object in one_minute_bars[2:]
        )/one_minute_bars[1].high < 0.95

        current_bar_crossed_stock_highest_high = potential_confirmation_bar.low < stock.last_post_pre_one_minute_highest_high < potential_confirmation_bar.close

        return current_bar_is_highest_high and previous_bar_was_highest_high and not current_bar_crossed_stock_highest_high
