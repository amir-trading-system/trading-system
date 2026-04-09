import datetime
import logging

import common
import model

class Evidence:
    name: str = ""
    relevant_bars: list[common.objects.BarData] = []

    def __init__(
        self,
        logger: logging.Logger,
        stock: common.objects.Stock,
    ):
        self.logger = logger
        self.relevant_bars = stock.bars[1:]

    def is_potential_starting_bar(
        self,
        stock: common.objects.Stock,
        bar_object: common.objects.BarData,
    ) -> bool:
        base_condition = True
        previous_bar = stock.previous_bar(
            bar_object=bar_object,
        )
        if previous_bar is not None:
            base_condition = (
                True
                and base_condition
                and previous_bar is not None
                and bar_object.high > previous_bar.high
            )

        first_option = (
            True
            and bar_object.vwap is not None
            and bar_object.ema_9 is not None
            and bar_object.ema_20 is not None
            and bar_object.volume_average is not None
            and base_condition
            and bar_object.close > bar_object.ema_9
            and bar_object.close > bar_object.ema_20
            and bar_object.volume > bar_object.volume_average
            and bar_object.volume > 500000
            and bar_object.high > bar_object.vwap
            and bar_object.ema_9/bar_object.low >= 0.9
        )
        second_option = (
            True
            and bar_object.vwap is not None
            and bar_object.ema_9 is not None
            and bar_object.ema_20 is not None
            and bar_object.volume_average is not None
            and base_condition
            and bar_object.high > bar_object.vwap
            and bar_object.close > bar_object.ema_9
            and bar_object.histogram > 0
            and bar_object.volume/bar_object.volume_average > 7
            and max(
                stock.bars[bar_object.index:bar_object.index+20],
                key=lambda bar_obj: bar_obj.volume
            ) == bar_object
        )

        return first_option or second_option

    def get_starting_bar(
        self,
        stock: common.objects.Stock,
    ) -> common.objects.MilestoneBar | None:
        for bar_object in self.relevant_bars:
            previous_bar = stock.previous_bar(
                bar_object=bar_object,
            )
            is_potential_starting_bar = self.is_potential_starting_bar(
                stock=stock,
                bar_object=bar_object
            )
            potential_starting_bar = (
                True
                and is_potential_starting_bar
                and (
                    not self.is_potential_starting_bar(
                        stock=stock,
                        bar_object=previous_bar,
                    ) if previous_bar is not None else True
                )
            )
            if potential_starting_bar:
                if len(self.relevant_bars[:10]) > 0:
                    potential_starting_bar = max(
                        [
                            bar_obj.high
                            for bar_obj in self.relevant_bars[:10]
                        ]
                    ) == bar_object.high

                return common.objects.MilestoneBar(
                    index=bar_object.index,
                    bar_object=bar_object,
                    bar_type=common.objects.MilestoneType.STARTING_BAR,
                    bar_time=bar_object.bar_time,
                    timeframe=bar_object.timeframe,
                )

    def get_top_bar(
        self,
        starting_bar: common.objects.BarData,
        current_bar: common.objects.BarData,
    ) -> common.objects.MilestoneBar | None:
        top_bar_options = [
            bar_object
            for bar_object in self.relevant_bars[:starting_bar.index]
            if (
                True
                and bar_object.index > current_bar.index
                and bar_object.high > starting_bar.high
                and len(self.relevant_bars[1:starting_bar.index]) > 0
                and bar_object.high == max(
                    [
                        bar_obj.high
                        for bar_obj in self.relevant_bars[:starting_bar.index]
                        if bar_obj.index > current_bar.index
                    ]
                )
            )
        ]
        if len(top_bar_options) > 0:
            top_bar = top_bar_options[0]
            return common.objects.MilestoneBar(
                index=top_bar.index,
                bar_object=top_bar,
                bar_type=common.objects.MilestoneType.TOP_BAR,
                bar_time=top_bar.bar_time,
                timeframe=top_bar.timeframe,
            )

    def find_evidence(
        self,
        stock: common.objects.Stock,
        milestones: common.objects.Milestones,
        current_bar: common.objects.BarData,
        is_retro: bool,
    ) -> bool:
        raise NotImplementedError()

    def crossed_resistance_level_strongly(
        self,
        resistance_levels: list[common.objects.BarData],
        highest_high_one_minute_bar: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
    ) -> bool:
        crossed_resistance_level_strongly: bool = False

        for resistance_level in resistance_levels:
            if (
                potential_confirmation_bar.low < resistance_level.high < potential_confirmation_bar.close
                and abs(resistance_level.high - potential_confirmation_bar.open_value) > 0
                and (potential_confirmation_bar.close - resistance_level.high)/abs(resistance_level.high - potential_confirmation_bar.open_value) >= 0.25
                and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
                and potential_confirmation_bar.volume > 10000
            ) and not any(
                resistance_level
                for resistance_level in resistance_levels
                if resistance_level.high >= potential_confirmation_bar.high
                and potential_confirmation_bar.high/resistance_level.high >= 0.8
            ) and not any(
                r_l
                for r_l in resistance_levels
                if resistance_level.high < r_l.high
                and resistance_level.index > r_l.index
            ):
                crossed_resistance_level_strongly = True
                break

        higher_resistance_levels_count = len(
            [
                r_l
                for r_l in resistance_levels
                if r_l.high > potential_confirmation_bar.high
            ]
        )

        if (
            True
            and not crossed_resistance_level_strongly
            and higher_resistance_levels_count/len(resistance_levels) <= 1
            and len(resistance_levels) > 1
            and potential_confirmation_bar.bar_time - datetime.timedelta(minutes=5) > highest_high_one_minute_bar.bar_time
            and potential_confirmation_bar.high - potential_confirmation_bar.low > 0.0
            and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
            and (potential_confirmation_bar.close - potential_confirmation_bar.open_value)/(potential_confirmation_bar.high - potential_confirmation_bar.low) >= 0.6
            and potential_confirmation_bar.close > highest_high_one_minute_bar.high
            and (potential_confirmation_bar.close > highest_high_one_minute_bar.high)
            and not any(
                r_l
                for r_l in resistance_levels
                if potential_confirmation_bar.high/r_l.high >= 0.95
                and potential_confirmation_bar.high < r_l.high
            )
        ):
            crossed_resistance_level_strongly = True

        return crossed_resistance_level_strongly

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

    def bar_has_potential(
        self,
        stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
        highest_high_one_minute_bar: common.objects.BarData,
    ) -> bool:
        if potential_confirmation_bar.volume < 20000:
            return False

        if self.highest_high_occurred_more_than_once_in_the_last_bars(
            stock=stock,
            potential_confirmation_bar=potential_confirmation_bar,
            one_minute_bars=one_minute_bars,
        ):
            return False

        if sum(
            bar_object.volume
            for bar_object in one_minute_bars
            if bar_object.index > highest_high_one_minute_bar.index+1
        ) < 100000:
            return False

        if potential_confirmation_bar.buyers_are_indecision:
            return False

        return True

    def confirm(
        self,
        stock: common.objects.Stock,
        one_minute_timeframe_stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        highest_high_one_minute_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
        model_runner: model.runner.Runner,
    ) -> common.objects.Score:
        score = common.objects.Score(
            score=0.0,
            probability=0.0,
            threshold=0.0,
            should_take_trade=False,
        )

        if not self.bar_has_potential(
            stock=stock,
            potential_confirmation_bar=potential_confirmation_bar,
            one_minute_bars=one_minute_bars,
            highest_high_one_minute_bar=highest_high_one_minute_bar,
        ):
            return score

        if not self._confirm(
            stock=stock,
            original_bar_to_confirm=original_bar_to_confirm,
            potential_confirmation_bar=potential_confirmation_bar,
            milestones=milestones,
            highest_high_one_minute_bar=highest_high_one_minute_bar,
            one_minute_bars=one_minute_bars,
            volume_sum_since_market_open=stock.volume_sum_since_market_open,
        ):
            return score

        self.logger.info(
            msg="Potential confirmation bar has passed static confirmation, waiting for model confirmation",
            extra={
                "worker": "Confirmator",
                "symbol": stock.symbol_name,
                "timeframe": original_bar_to_confirm.timeframe,
                "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                "bar_time": original_bar_to_confirm.bar_time,
                "entry_position_bar_time": potential_confirmation_bar.bar_time,
                "evidence_name": self.name,
                "request_id": stock.request_id,
                "should_run_model": 1 if model_runner.should_run_model else 0,
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

        if model_runner.should_run_model:
            score: common.objects.Score = model_runner.score_potential_confirmation_bar(
                potential_confirmation_bar=potential_confirmation_bar,
            )

            msg = "Bar confirmed by model"
            if not score.should_take_trade:
                msg = "Bar confirmed by static confirmation, but got denied on model confirmation"

            self.logger.info(
                msg=msg,
                extra={
                    "worker": "Confirmator",
                    "symbol": stock.symbol_name,
                    "timeframe": original_bar_to_confirm.timeframe,
                    "timeframe_type": original_bar_to_confirm.timeframe_type.value,
                    "bar_time": original_bar_to_confirm.bar_time,
                    "entry_position_bar_time": potential_confirmation_bar.bar_time,
                    "evidence_name": self.name,
                    "request_id": stock.request_id,
                    "score": score.score,
                    "probability": score.probability,
                    "threshold": score.threshold,
                },
            )
            score.should_take_trade = (
                True
                and score.should_take_trade
                and potential_confirmation_bar.price_movement_statistics["feature_weak_bars_to_bars_since_highest_high_to_total_bars"] < 0.95
            )
        else:
            score.should_take_trade = True

        return score

    def _confirm(
        self,
        stock: common.objects.Stock,
        original_bar_to_confirm: common.objects.BarData,
        potential_confirmation_bar: common.objects.BarData,
        milestones: common.objects.Milestones,
        highest_high_one_minute_bar: common.objects.BarData,
        one_minute_bars: list[common.objects.BarData],
        volume_sum_since_market_open: float,
    ) -> bool:
        raise NotImplementedError()
