import copy
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

    def confirm_entry_position(
        self,
        stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        milestones: common.objects.Milestones,
    ):
        one_minute_bars: list[common.objects.BarData] = []
        most_updated_datetime = datetime.datetime.fromtimestamp(0)
        already_sent_buy_order_for_stock: dict[str,bool] = {}
        stock.bars = sorted(
            stock.bars,
            key=lambda bar_object: bar_object.bar_time,
            reverse=True,
        )
        next_bar = None
        bar_has_confirmed = False
        confirmation_bar = None
        score: common.objects.Score = None
        previous_highest_high = 0.0
        one_minute_timeframe_stock = self.request_id_to_symbol[stock.one_minute_request_id]

        while True:
            next_bar = stock.one_minute_bars_queue.get()
            if next_bar.low < 1:
                continue

            stock.one_minute_bars_queue.task_done()
            date_now = datetime.datetime.now()

            if bar_has_confirmed:
                if self.confirm_bar_for_placing_order(
                    day_timeframe_stock=stock,
                    one_minute_timeframe_stock=one_minute_timeframe_stock,
                    original_bar_to_confirm=original_bar_to_confirm,
                    potential_confirmation_bar=confirmation_bar,
                    current_bar=next_bar,
                    previous_highest_high=previous_highest_high,
                    score=score,
                    already_sent_buy_order_for_stock=already_sent_buy_order_for_stock,
                ):
                    bar_has_confirmed = False
                    score = None

                continue

            if (
                True
                and self.is_retro
                and next_bar.bar_time > datetime.datetime(
                    year=next_bar.bar_time.year,
                    month=next_bar.bar_time.month,
                    day=next_bar.bar_time.day,
                    hour=16,
                )
            ):
                self.results_queue.put(
                    {
                        "symbol": stock.symbol_name,
                        "original_bar_time": original_bar_to_confirm.bar_time,
                        "confirmation_bar_time": None,
                        "bar_to_place_order_time": None,
                        "price_movement_statistics": {},
                        "score": 0,
                    },
                )
                return

            if (
                next_bar.bar_time < datetime.datetime(
                    year=original_bar_to_confirm.bar_time.year,
                    month=original_bar_to_confirm.bar_time.month,
                    day=original_bar_to_confirm.bar_time.day,
                    hour=4,
                )
                or next_bar.bar_time < most_updated_datetime
                or not next_bar.ready_to_analyze
                or not next_bar.histogram
                or (
                    not self.is_retro
                    and next_bar.bar_time < datetime.datetime(
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
                    "entry_position_bar_time": next_bar.bar_time,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "request_id": stock.request_id,
                    "high": next_bar.high,
                    "low": next_bar.low,
                    "open": next_bar.open_value,
                    "close": next_bar.close,
                    "collection_finished_time": next_bar.collection_finished_time,
                },
            )

            score, previous_highest_high = self._confirm(
                stock=stock,
                milestones=milestones,
                one_minute_bars=one_minute_bars,
                potential_confirmation_bar=next_bar,
                original_bar_to_confirm=original_bar_to_confirm,
            )

            if score.should_take_trade:
                bar_has_confirmed = True
                confirmation_bar = copy.deepcopy(next_bar)
                continue

            most_updated_datetime = next_bar.bar_time
            self.logger.info(
                msg="Entry point does not confirmed yet, waiting for next one",
                extra={
                    "worker": "Confirmator",
                    "symbol": original_bar_to_confirm.symbol,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "entry_position_bar_time": next_bar.bar_time,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "request_id": stock.request_id,
                },
            )

    def _confirm(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        one_minute_bars: list[common.objects.BarData],
        potential_confirmation_bar: common.objects.BarData,
        original_bar_to_confirm: common.objects.BarData,
    ) -> tuple[common.objects.Score, float]:
        entry_position_bar: common.objects.BarData = None
        one_minute_bars.append(potential_confirmation_bar)
        confirmed_evidence: str = ""
        score = common.objects.Score(
            score=0.0,
            probability=0.0,
            threshold=0.0,
            should_take_trade=False,
        )

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
            return (
                score,
                highest_high_one_minute_bar.high,
            )

        stock_is_valid_for_evidence = False

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
                    return (
                        score,
                        highest_high_one_minute_bar.high,
                    )

            if self.model_runner.should_run_model:
                score = self.model_runner.score_potential_confirmation_bar(
                    potential_confirmation_bar=potential_confirmation_bar,
                )

                msg = "Bar confirmed by model"

                if not score.should_take_trade:
                    msg = "Bar confirmed by static confirmation, but got denied on model confirmation"
                else:
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
            self.logger.info(
                "Bar has confirmed, waiting for volume confirmation for placing order",
                extra={
                    "worker": "Confirmator",
                    "symbol": original_bar_to_confirm.symbol,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "entry_position_bar_time": entry_position_bar.bar_time,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "evidence_name": confirmed_evidence,
                    "request_id": stock.request_id,
                    "score": score.score,
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
                )

        return (
            score,
            highest_high_one_minute_bar.high,
        )

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

    def confirm_bar_for_placing_order(
        self,
        day_timeframe_stock: common.objects.Stock,
        one_minute_timeframe_stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        current_bar: common.objects.BarData,
        previous_highest_high: float,
        score: common.objects.Score,
        already_sent_buy_order_for_stock: dict[str,bool] = {}
    ) -> bool:
        order_has_been_placed = False
        transmit = False

        if potential_confirmation_bar.bar_time + datetime.timedelta(minutes=15) < current_bar.bar_time:
            return True

        relevant_bars = [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if potential_confirmation_bar.bar_time < bar_object.bar_time <= current_bar.bar_time
        ]
        if not relevant_bars:
            return order_has_been_placed

        if any(
            bar_object
            for bar_object in relevant_bars
            if bar_object.close < previous_highest_high
        ):
            # meaning that this trend is not relevant anymore - not a real trend.
            return True

        had_pullback = False
        if any(
            bar_object
            for bar_object in relevant_bars
            if (
                True
                and (
                    bar_object.low <= bar_object.ema_9
                    or bar_object.low/bar_object.ema_9 > 0.95
                    or not bar_object.is_positive
                )
            )
        ):
            # meaning that this trend is healthy.
            had_pullback = True

        previous_bar = one_minute_timeframe_stock.previous_bar(
            bar_object=current_bar,
        )

        validation_for_placing_order = (
            True
            and current_bar.is_positive
            and current_bar.volume > current_bar.volume_average
            and current_bar.low > current_bar.ema_20
            and current_bar.ema_9 > current_bar.ema_20
            and current_bar.high - current_bar.low > current_bar.low - current_bar.ema_9
            and previous_bar is not None
            and current_bar.volume > previous_bar.volume
            and had_pullback
            and current_bar.macd > 0
            and current_bar.body_percentage > 0.5
            and any(
                bar_object
                for bar_object in relevant_bars
                if (
                    0.95 < bar_object.low/previous_highest_high < 1.05
                    or 0.95 < bar_object.low/potential_confirmation_bar.high < 1.05
                )
            )
            and any(
                bar_object
                for bar_object in relevant_bars
                if (
                    not bar_object.is_positive
                    or bar_object.body_percentage < 0.6
                )
            )
        )

        if validation_for_placing_order:
            unique_key_for_place_order = original_bar_to_confirm.symbol
            if self.is_retro:
                unique_key_for_place_order = f"{original_bar_to_confirm.symbol}-{day_timeframe_stock.specific_bar_time}"
            if (
                not already_sent_buy_order_for_stock.get(unique_key_for_place_order, False)
            ):
                already_sent_buy_order_for_stock[unique_key_for_place_order] = True

                if not self.is_retro:
                    self.tws_client.place_buy_order(
                        symbol=original_bar_to_confirm.symbol,
                        price=potential_confirmation_bar.close,
                        transmit=transmit,
                        score=score,
                    )
                order_has_been_placed = True

                self.results_queue.put(
                    {
                        "symbol": day_timeframe_stock.symbol_name,
                        "original_bar_time": original_bar_to_confirm.bar_time,
                        "confirmation_bar_time": potential_confirmation_bar.bar_time,
                        "bar_to_place_order_time": current_bar.bar_time,
                        "price_movement_statistics": potential_confirmation_bar.price_movement_statistics,
                        "score": score.score if score is not None else 0,
                    },
                )
                self.logger.info(
                    "Bar has confirmed by model and order has been placed",
                    extra={
                        "worker": "Confirmator",
                        "symbol": original_bar_to_confirm.symbol,
                        "timeframe": original_bar_to_confirm.timeframe,
                        "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                        "entry_position_bar_time": current_bar.bar_time,
                        "bar_time": original_bar_to_confirm.bar_time,
                        "request_id": one_minute_timeframe_stock.request_id,
                        "score": score.score,
                    },
                )

        return order_has_been_placed
