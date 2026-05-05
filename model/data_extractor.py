import datetime

import common


class DataExtractor:
    def recent_days_structure(
        self,
    ):
        pass

    def breakout_structure(
        self,
    ):
        pass

    def volume_structure(
        self,
    ):
        pass

    def macd_structure(
        self,
    ):
        pass

    def pre_market_structure(
        self,
    ):
        pass

    #pylint:disable=W0613
    def extract_features_from_symbol_data(
        self,
        day_timeframe_stock: common.objects.Stock,
        one_minute_timeframe_stock: common.objects.Stock,
        potential_confirmation_bar: common.objects.BarData,
        highest_high_one_minute_bar: common.objects.BarData,
        volume_sum_since_market_open: float,
        one_minute_bars: list[common.objects.BarData],
        for_training: bool = False,
    ) -> dict[str, any]:
        minutes_since_market_open = ((potential_confirmation_bar.bar_time.hour - 9) * 60) + potential_confirmation_bar.bar_time.minute - 30
        total_bars = len(one_minute_bars)
        highest_high_one_minute_bar_time = day_timeframe_stock.get_highest_high_one_minute_bar(
            current_one_minute_bar=potential_confirmation_bar,
        )

        total_volume = 0
        bars_size_sum = 0
        highest_volume_average = 0

        for bar_object in one_minute_bars:
            if bar_object.bar_time < potential_confirmation_bar.bar_time:
                bars_size_sum += abs(bar_object.close - bar_object.open_value)
            total_volume += bar_object.volume
            if bar_object.volume_average > highest_volume_average:
                highest_volume_average = bar_object.volume_average

            previous_bar = one_minute_timeframe_stock.previous_bar(
                bar_object=bar_object,
            )
            next_bar = one_minute_timeframe_stock.next_bar(
                bar_object=bar_object,
            )

        features = {
            "highest_high_one_minute_bar_time": highest_high_one_minute_bar.bar_time if highest_high_one_minute_bar is not None else datetime.datetime.fromtimestamp(0),
        }

        return features
