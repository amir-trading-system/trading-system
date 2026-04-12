# import datetime

# import common


# class DataExtractor:
#     @staticmethod
#     def extract_features_from_symbol_data(
#         day_timeframe_stock: common.objects.Stock,
#         one_minute_timeframe_stock: common.objects.Stock,
#         potential_confirmation_bar: common.objects.BarData,
#         highest_high_one_minute_bar: common.objects.BarData,
#         volume_sum_since_market_open: float,
#         one_minute_bars: list[common.objects.BarData],
#     ) -> dict[str, float]:
#         total_bars = len(one_minute_bars)
#         minutes_since_market_open = ((potential_confirmation_bar.bar_time.hour - 9) * 60) + potential_confirmation_bar.bar_time.minute - 30

#         total_volume = 0
#         positive_volume_sum = 0
#         negative_volume_sum = 0
#         positive_movement = 0
#         negative_movement = 0
#         positive_histograms_sum = 0
#         negative_histograms_sum = 0
#         positive_bars_counter = 0
#         negative_bars_counter = 0
#         last_bars_positive_bars = 0
#         last_bars_negative_bars = 0
#         bars_with_at_least_50_pct_wick_counter = 0
#         strong_positive_bars_with_full_body_counter = 0
#         bars_with_negative_momentum_histogram_counter = 0
#         bars_with_lower_volume_average_counter = 0
#         macd_under_signal_line_counter = 0
#         ema_9_keeps_going_up_counter = 0
#         bars_above_volume_average_counter = 0
#         strong_bars_counter = 0
#         bars_after_strong_bars_that_continues_trend_counter = 0
#         high_volume_bars_with_rejection_counter = 0
#         bars_with_rejection_inside_entry_bar_range: list[common.objects.BarData] = []
#         bars_with_highest_volume: list[common.objects.BarData] = []
#         bars_without_movement_counter = 0
#         bars_above_vwap_counter = 0
#         bars_ema_above_vwap_counter = 0
#         positive_bars_close_strong_counter = 0
#         volume_average_goes_up_counter = 0
#         volume_average_goes_down_counter = 0
#         volume_avergae_above_10000_counter = 0
#         bars_with_rejection_since_market_open = 0
#         bars_size_sum = 0
#         bars_size_average = 0
#         histogram_changed_directions_counter = 0
#         strong_negative_bars_counter = 0
#         pick_points_counter = 0
#         rejected_pick_points_counter = 0
#         price_action_is_stuck_counter = 0
#         bars_closed_above_half_of_bar_counter = 0
#         stronger_than_previous_bars_counter = 0
#         bars_with_ordered_indicators_counter = 0
#         indecision_bars_counter = 0
#         negative_bars_with_positive_histogram = 0
#         highest_volume_average = 0
#         bars_with_rejection_counter = 0
#         overlapped_bars_counter = 0
#         volume_sum_from_market_start_to_middle_point = 0
#         volume_sum_from_middle_point_to_entry_point = 0
#         bars_since_highest_high: list[common.objects.BarData] = []
#         volume_to_volume_average_ratio_since_highest_high = 0
#         last_10_bars_range_sum = 0
#         weak_bars_since_highest_high = 0

#         for bar_object in one_minute_bars:
#             if bar_object.bar_time < potential_confirmation_bar.bar_time:
#                 bars_size_sum += abs(bar_object.close - bar_object.open_value)
#             total_volume += bar_object.volume
#             is_positive = bar_object.close > bar_object.open_value
#             above_volume_average = bar_object.volume > bar_object.volume_average
#             above_vwap = bar_object.close > bar_object.vwap
#             above_9_ema = bar_object.close > bar_object.ema_9
#             if bar_object.volume_average > highest_volume_average:
#                 highest_volume_average = bar_object.volume_average

#             previous_bar = one_minute_timeframe_stock.previous_bar(
#                 bar_object=bar_object,
#             )
#             next_bar = one_minute_timeframe_stock.next_bar(
#                 bar_object=bar_object,
#             )
#             if bar_object.buyers_are_indecision:
#                 indecision_bars_counter += 1

#             if (
#                 True
#                 and bar_object.vwap < bar_object.ema_9
#                 and bar_object.vwap < bar_object.ema_20
#                 and bar_object.ema_9 > bar_object.ema_20
#                 and bar_object.low >= bar_object.ema_9
#             ):
#                 bars_with_ordered_indicators_counter += 1

#             if (
#                 True
#                 and bar_object.high - bar_object.low > 0
#                 and (bar_object.high - bar_object.close)/(bar_object.high - bar_object.low) < 0.5
#             ):
#                 bars_closed_above_half_of_bar_counter += 1

#             if (
#                 True
#                 and previous_bar is not None
#                 and next_bar is not None
#                 and previous_bar.is_after_market_open
#                 and bar_object.index - potential_confirmation_bar.index < 10
#                 and bar_object.high > previous_bar.high
#                 and bar_object.high > next_bar.high
#                 and bar_object.volume > bar_object.volume_average
#                 and bar_object.volume > next_bar.volume
#                 and bar_object.volume > previous_bar.volume
#                 and bar_object.bar_wick_percentage > 0.1
#             ):
#                 bars_with_rejection_counter += 1

#             if (
#                 True
#                 and previous_bar is not None
#                 and previous_bar.low <= bar_object.open_value <= previous_bar.high
#                 and previous_bar.low <= bar_object.close <= previous_bar.high
#             ):
#                 overlapped_bars_counter += 1

#             if bar_object.index <= potential_confirmation_bar.index + round(minutes_since_market_open/2):
#                 volume_sum_from_middle_point_to_entry_point += bar_object.volume
#             else:
#                 volume_sum_from_market_start_to_middle_point += bar_object.volume

#             if (
#                 True
#                 and next_bar is not None
#                 and bar_object.index - potential_confirmation_bar.index < 10
#                 and not next_bar.is_positive
#                 and bar_object.is_positive
#                 and above_volume_average
#                 and above_9_ema
#                 and above_vwap
#                 and next_bar.volume > next_bar.volume_average
#                 and next_bar.close < bar_object.low
#             ):
#                 bars_with_rejection_counter += 1

#             if (
#                 True
#                 and is_positive
#                 and above_9_ema
#                 and above_vwap
#                 and bar_object.bar_is_solid
#                 and previous_bar is not None
#                 and next_bar is not None
#                 and bar_object.high > previous_bar.high
#                 and bar_object.close - bar_object.open_value > previous_bar.close - previous_bar.open_value
#                 and bar_object.low/next_bar.low < 0.8
#             ):
#                 stronger_than_previous_bars_counter += 1

#             if (
#                 True
#                 and previous_bar is not None
#                 and next_bar is not None
#                 and bar_object.high > previous_bar.high
#                 and bar_object.high > next_bar.high
#                 and bar_object.volume > bar_object.volume_average
#             ):
#                 pick_points_counter += 1
#                 if (
#                     True
#                     and next_bar.close < next_bar.open_value
#                     and next_bar.volume > next_bar.volume_average
#                     and next_bar.body_percentage > 0.3
#                     and (
#                         next_bar.low <= bar_object.low
#                         or bar_object.low/next_bar.low >= 0.9
#                     )
#                 ):
#                     rejected_pick_points_counter += 1

#             if (
#                 previous_bar is not None
#                 and next_bar is not None
#                 and bar_object.histogram < previous_bar.histogram
#                 and bar_object.histogram < next_bar.histogram
#             ):
#                 histogram_changed_directions_counter += 1

#             if highest_high_one_minute_bar.bar_time < bar_object.bar_time < potential_confirmation_bar.bar_time:
#                 bars_since_highest_high.append(bar_object)
#                 volume_to_volume_average_ratio_since_highest_high += bar_object.volume/bar_object.volume_average
#                 if (
#                     True
#                     and bar_object.ema_9 < bar_object.vwap
#                     and bar_object.close < bar_object.vwap
#                     and bar_object.volume/bar_object.volume_average <= 1.1
#                 ):
#                     weak_bars_since_highest_high += 1

#             if (
#                 True
#                 and previous_bar is not None
#                 and bar_object.volume > bar_object.volume_average
#             ):
#                 if (
#                     previous_bar.high > bar_object.high
#                     and bar_object.high/previous_bar.high >= 0.98
#                 ):
#                     price_action_is_stuck_counter += 1
#                 if (
#                     previous_bar.high < bar_object.high
#                     and (
#                         previous_bar.high/bar_object.high >= 0.98
#                         or previous_bar.high/bar_object.close >= 0.98
#                     )
#                 ):
#                     price_action_is_stuck_counter += 1

#             has_rejection = bar_object.bar_wick_percentage >= 0.5
#             if bar_object.macd < bar_object.signal_line:
#                 macd_under_signal_line_counter += 1

#             if (
#                 True
#                 and previous_bar is not None
#                 and bar_object.bar_wick_percentage >= 0.1
#                 and bar_object.volume > bar_object.volume_average
#                 and previous_bar.high < bar_object.high
#             ):
#                 bars_with_rejection_since_market_open += 1

#             if bar_object.bar_wick_percentage >= 0.5:
#                 bars_with_at_least_50_pct_wick_counter += 1

#             if bar_object.volume_average > 10000:
#                 volume_avergae_above_10000_counter += 1

#             if bar_object.histogram > 0:
#                 positive_histograms_sum += bar_object.histogram
#             else:
#                 negative_histograms_sum += abs(bar_object.histogram)

#             if is_positive:
#                 positive_volume_sum += bar_object.volume
#                 positive_movement += bar_object.close - bar_object.open_value
#                 if bar_object.index - 5 < potential_confirmation_bar.index:
#                     last_bars_positive_bars += 1
#                 if bar_object.body_percentage >= 0.75:
#                     strong_positive_bars_with_full_body_counter += 1
#                 if bar_object.bar_wick_percentage <= 0.1:
#                     positive_bars_close_strong_counter += 1
#                 if bar_object.close > bar_object.vwap:
#                     positive_bars_counter += 1
#             else:
#                 negative_volume_sum += bar_object.volume
#                 negative_movement += bar_object.open_value - bar_object.close
#                 if bar_object.index - 5 < potential_confirmation_bar.index:
#                     last_bars_negative_bars += 1
#                 if bar_object.close > bar_object.vwap:
#                     negative_bars_counter += 1
#                 if (
#                     True
#                     and bar_object.high > bar_object.vwap
#                     and above_volume_average
#                     and bar_object.body_percentage > 0.3
#                 ):
#                     strong_negative_bars_counter += 1

#                 if bar_object.histogram > 0 and bar_object.macd > 0 and bar_object.signal_line > 0:
#                     negative_bars_with_positive_histogram += 1

#             if previous_bar is not None:
#                 if previous_bar.volume_average < bar_object.volume_average:
#                     volume_average_goes_up_counter += 1
#                 else:
#                     volume_average_goes_down_counter += 1

#                 if bar_object.histogram < previous_bar.histogram or bar_object.histogram < 0:
#                     bars_with_negative_momentum_histogram_counter += 1
#                 if previous_bar.ema_9 < bar_object.ema_9:
#                     ema_9_keeps_going_up_counter += 1

#             if (
#                 True
#                 and previous_bar is not None
#                 and previous_bar.volume_average > bar_object.volume_average
#             ):
#                 bars_with_lower_volume_average_counter += 1

#             if (
#                 True
#                 and above_volume_average
#                 and bar_object.close > bar_object.vwap
#             ):
#                 bars_with_highest_volume.append(bar_object)

#             if above_volume_average:
#                 bars_above_volume_average_counter += 1
#                 if has_rejection:
#                     high_volume_bars_with_rejection_counter += 1

#             if (
#                 True
#                 and is_positive
#                 and above_volume_average
#                 and bar_object.body_percentage > 0.4
#                 and bar_object.bar_wick_percentage <= 0.4
#             ):
#                 strong_bars_counter += 1
#                 if (
#                     True
#                     and next_bar is not None
#                     and next_bar.high >= bar_object.high * 0.995
#                 ):
#                     bars_after_strong_bars_that_continues_trend_counter += 1

#             if (
#                 True
#                 and bar_object.bar_time + datetime.timedelta(hours=1) >= potential_confirmation_bar.bar_time
#                 and bar_object.index - 1 > potential_confirmation_bar.index
#                 and potential_confirmation_bar.open_value < bar_object.high < potential_confirmation_bar.close
#                 and bar_object.close < potential_confirmation_bar.open_value
#                 and bar_object.volume > bar_object.volume_average
#                 and bar_object.close < bar_object.high
#                 and above_vwap
#                 and above_9_ema
#                 and bar_object.close > bar_object.ema_20
#                 and previous_bar is not None
#                 and next_bar is not None
#                 and previous_bar.high < bar_object.high
#                 and next_bar.high < bar_object.high
#             ):
#                 bars_with_rejection_inside_entry_bar_range.append(bar_object)

#             if round(bar_object.high, 2) == round(bar_object.low, 2):
#                 bars_without_movement_counter += 1

#             if bar_object.close > bar_object.vwap:
#                 bars_above_vwap_counter += 1

#             if (
#                 True
#                 and bar_object.ema_9 > bar_object.vwap
#                 and bar_object.ema_20 > bar_object.vwap
#                 and bar_object.ema_9 >= bar_object.ema_20
#             ):
#                 bars_ema_above_vwap_counter += 1

#             if bar_object.bar_time + datetime.timedelta(minutes=10) >= potential_confirmation_bar.bar_time:
#                 last_10_bars_range_sum += bar_object.high - bar_object.low

#         feature_bars_with_rejection_inside_entry_bar_range_pct = 0
#         max_bars_since_first_breakout_attempt = 0
#         if bars_with_rejection_inside_entry_bar_range:
#             breakout_attempts_total_bars = len(bars_with_rejection_inside_entry_bar_range)
#             max_bars_since_first_breakout_attempt = max(
#                 bar_object.index
#                 for bar_object in bars_with_rejection_inside_entry_bar_range
#             ) - potential_confirmation_bar.index

#             feature_bars_with_rejection_inside_entry_bar_range_pct = breakout_attempts_total_bars/max_bars_since_first_breakout_attempt

#         feature_volume_before_middle_point_vs_after_middle_point_pct = volume_sum_from_market_start_to_middle_point/volume_sum_from_middle_point_to_entry_point
#         feature_histogram_negative_momentum_pct = bars_with_negative_momentum_histogram_counter/total_bars
#         feature_bars_with_at_least_50_pct_wick_pct = bars_with_at_least_50_pct_wick_counter/total_bars
#         feature_bars_with_lower_volume_average_pct = bars_with_lower_volume_average_counter/total_bars
#         feature_high_volume_bars_with_rejection_pct = high_volume_bars_with_rejection_counter/bars_above_volume_average_counter
#         volume_per_minute = volume_sum_since_market_open/minutes_since_market_open if minutes_since_market_open > 0 else 1

#         previous_bar_to_entry_bar = one_minute_timeframe_stock.previous_bar(
#             bar_object=potential_confirmation_bar,
#         )

#         crossed_any_resistance = any(
#             r_l
#             for r_l in day_timeframe_stock.resistance_levels
#             if potential_confirmation_bar.low < r_l.high < potential_confirmation_bar.high
#         )
#         last_10_bars_range_average = last_10_bars_range_sum/10

#         feature_volume_average_goes_up_pct = volume_average_goes_up_counter/total_bars
#         feature_overlapped_bars_since_market_open_pct = overlapped_bars_counter/len(one_minute_bars)
#         feature_weak_bars_since_highest_high_to_total_pct = weak_bars_since_highest_high/len(bars_since_highest_high) if bars_since_highest_high else 0
#         feature_bars_since_highest_high_to_total_bars_pct = len(bars_since_highest_high)/total_bars
#         feature_weak_bars_to_bars_since_highest_high_to_total_bars = feature_weak_bars_since_highest_high_to_total_pct/feature_bars_since_highest_high_to_total_bars_pct if feature_bars_since_highest_high_to_total_bars_pct > 0 else 0

#         feature_crossed_highest_high = (
#             True
#             and potential_confirmation_bar.low < highest_high_one_minute_bar.high < potential_confirmation_bar.high
#             and (potential_confirmation_bar.high - highest_high_one_minute_bar.high)/(potential_confirmation_bar.high - potential_confirmation_bar.low) > 0.3
#             and potential_confirmation_bar.low/potential_confirmation_bar.open_value >= 0.95
#             and potential_confirmation_bar.body_percentage > 0.5
#             and volume_sum_since_market_open > 500000
#             and not any(
#                 bar_object
#                 for bar_object in one_minute_bars[1:10]
#                 if abs(bar_object.close - bar_object.open_value) > potential_confirmation_bar.close - potential_confirmation_bar.open_value
#                 and bar_object.volume/potential_confirmation_bar.volume > 0.95
#             )
#         )

#         highest_high_bar_since_market_open = None
#         for bar_object in one_minute_bars[1:]:
#             previous_bar = one_minute_timeframe_stock.previous_bar(
#                 bar_object=bar_object,
#             )
#             next_bar = one_minute_timeframe_stock.next_bar(
#                 bar_object=bar_object,
#             )
#             if (
#                 previous_bar is not None
#                 and next_bar is not None
#                 and bar_object.high >= previous_bar.high
#                 and bar_object.high > next_bar.high
#                 and bar_object.volume > bar_object.volume_average
#             ):
#                 if (
#                     highest_high_bar_since_market_open is None
#                     or (
#                         highest_high_bar_since_market_open is not None
#                         and bar_object.high > highest_high_bar_since_market_open.high
#                     )
#                 ):
#                     highest_high_bar_since_market_open = bar_object

#         last_bars_positive_movement = 0
#         last_bars_negative_movement = 0
#         for bar_object in one_minute_bars[1:15]:
#             if not bar_object.above_9_ema or not bar_object.above_vwap:
#                 continue

#             if not bar_object.is_positive:
#                 last_bars_negative_movement += bar_object.high - bar_object.low
#             else:
#                 last_bars_negative_movement += (bar_object.high - bar_object.close) + (bar_object.open_value - bar_object.low)
#                 last_bars_positive_movement += bar_object.close - bar_object.open_value

#         feature_last_bars_positive_movement_pct = last_bars_positive_movement/last_bars_negative_movement if last_bars_negative_movement > 0 else 1
#         feature_is_there_highest_high_after_market_open = highest_high_bar_since_market_open is not None
#         feature_distance_from_highest_high_since_market_open = highest_high_bar_since_market_open.index if highest_high_bar_since_market_open is not None else 0

#         bars_size_average = bars_size_sum/(total_bars-1) if total_bars > 1 else 1
#         feature_entry_bar_has_highest_volume = max(bar_object.volume for bar_object in one_minute_bars) == potential_confirmation_bar.volume
#         feature_entry_bar_is_biggest_bar = max(bar_object.high - bar_object.low for bar_object in one_minute_bars) == potential_confirmation_bar.high - potential_confirmation_bar.low
#         feature_entry_bar_is_highest = max(bar_object.high for bar_object in one_minute_bars) == potential_confirmation_bar.high

#         feature_bar_getting_high_while_9_ema_getting_down = any(
#             bar_object
#             for bar_object in one_minute_bars[1:20]
#             if bar_object.is_positive
#             and bar_object.above_9_ema
#             and bar_object.above_vwap
#             and bar_object.high < potential_confirmation_bar.high
#             and bar_object.ema_9 - bar_object.ema_20 > potential_confirmation_bar.ema_9 - potential_confirmation_bar.ema_20
#         )
#         feature_crossed_bar_with_big_resistance = any(
#             bar_object
#             for bar_object in one_minute_bars[1:]
#             if potential_confirmation_bar.low < bar_object.high < potential_confirmation_bar.close
#             and bar_object.volume > bar_object.volume_average
#             and potential_confirmation_bar.bar_wick_percentage <= 0.3
#         )

#         crossed_any_near_resistance = any(
#             r_l
#             for r_l in day_timeframe_stock.resistance_levels
#             if potential_confirmation_bar.low < r_l.high < potential_confirmation_bar.close
#             and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
#             and r_l.index < 10
#         )

#         feature_entry_bar_closed_strong = (
#             True
#             and previous_bar_to_entry_bar is not None
#             and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
#             and potential_confirmation_bar.volume > previous_bar_to_entry_bar.volume
#             and potential_confirmation_bar.body_percentage > 0.7
#             and potential_confirmation_bar.bar_wick_percentage < 0.3
#         )
#         feature_current_macd_to_previous = 0
#         if previous_bar_to_entry_bar is not None:
#             feature_current_macd_to_previous = potential_confirmation_bar.macd/previous_bar_to_entry_bar.macd

#         ema_9_crossed_down_ema_20_since_pullback = any(
#             bar_object
#             for bar_object in bars_since_highest_high
#             if bar_object.ema_9 < bar_object.ema_20
#         )
#         bar_closed_under_vwap_during_pullback = any(
#             bar_object
#             for bar_object in bars_since_highest_high
#             if bar_object.close < bar_object.vwap
#         )

#         two_bars_back_bar = None
#         if previous_bar_to_entry_bar is not None:
#             two_bars_back_bar = one_minute_timeframe_stock.previous_bar(
#                 bar_object=previous_bar_to_entry_bar,
#             )
#         feature_bar_histogram_changed_direction = (
#             True
#             and previous_bar_to_entry_bar is not None
#             and two_bars_back_bar is not None
#             and previous_bar_to_entry_bar.histogram < two_bars_back_bar.histogram
#             and previous_bar_to_entry_bar.histogram < potential_confirmation_bar.histogram
#         ) or (
#             True
#             and previous_bar_to_entry_bar is not None
#             and previous_bar_to_entry_bar.histogram > 0
#             and previous_bar_to_entry_bar.macd > 0
#             and previous_bar_to_entry_bar.histogram/potential_confirmation_bar.histogram < 0.5
#             and potential_confirmation_bar.ema_9 > potential_confirmation_bar.ema_20
#             and potential_confirmation_bar.ema_20 > potential_confirmation_bar.vwap
#             and potential_confirmation_bar.close > potential_confirmation_bar.ema_9
#             and 0.95 < potential_confirmation_bar.ema_9/potential_confirmation_bar.open_value < 1.05
#         )
#         previous_bar_is_highest = False
#         if previous_bar_to_entry_bar is not None and previous_bar_to_entry_bar.is_after_market_open:
#             relevant_bars = [b for b in one_minute_bars if b.bar_time < previous_bar_to_entry_bar.bar_time]
#             if relevant_bars:
#                 previous_bar_is_highest = max(
#                     b.high
#                     for b in relevant_bars
#                 ) < previous_bar_to_entry_bar.high

#         feature_entry_bar_shape_is_good = (
#             True
#             and previous_bar_to_entry_bar.is_after_market_open
#             and not previous_bar_is_highest
#             and potential_confirmation_bar.volume > potential_confirmation_bar.volume_average
#             and potential_confirmation_bar.ema_9 > potential_confirmation_bar.ema_20
#             and potential_confirmation_bar.ema_20 > potential_confirmation_bar.vwap
#             and 0.95 < potential_confirmation_bar.ema_9/potential_confirmation_bar.open_value < 1.05
#             and potential_confirmation_bar.body_percentage > 0.5
#             and (potential_confirmation_bar.open_value - potential_confirmation_bar.low)/(potential_confirmation_bar.close - potential_confirmation_bar.open_value) < 0.4
#             and bars_with_rejection_counter < 3
#         )

#         volume_bigger_than_last_bars_count = 0
#         bars_been_crossed_count = 0
#         for bar_object in one_minute_bars[1:11]:
#             if bar_object.volume < potential_confirmation_bar.volume:
#                 volume_bigger_than_last_bars_count += 1
#             if potential_confirmation_bar.open_value < bar_object.high < potential_confirmation_bar.high:
#                 bars_been_crossed_count += 1

#         features = {
#             "feature_price_minus_vwap_at_entry": potential_confirmation_bar.close - potential_confirmation_bar.vwap,
#             "feature_histogram_negative_momentum_pct": feature_histogram_negative_momentum_pct,
#             "feature_bars_with_at_least_50_pct_wick_pct": feature_bars_with_at_least_50_pct_wick_pct,
#             "feature_bars_with_lower_volume_average_pct": feature_bars_with_lower_volume_average_pct,
#             "feature_high_volume_bars_with_rejection_pct": feature_high_volume_bars_with_rejection_pct,
#             "feature_volume_per_minute_to_bar_volume": round(volume_per_minute, 2)/potential_confirmation_bar.volume,
#             "feature_bars_with_rejection_inside_entry_bar_range_pct": feature_bars_with_rejection_inside_entry_bar_range_pct,
#             "feature_positive_vs_negative_volume": positive_volume_sum/negative_volume_sum if negative_volume_sum > 0 else 1,
#             "feature_positive_vs_negative_movement": positive_movement/negative_movement if negative_movement > 0 else 1,
#             "feature_volume_before_middle_point_vs_after_middle_point_pct_above_threshold": feature_volume_before_middle_point_vs_after_middle_point_pct > 0.2,
#             "feature_bars_without_movement_pct_above_threshold": bars_without_movement_counter/total_bars > 0.02,
#             "feature_entry_strength_vs_avg": (potential_confirmation_bar.high - potential_confirmation_bar.low)/last_10_bars_range_average,
#             "feature_volume_average_goes_up_pct": feature_volume_average_goes_up_pct,
#             "feature_overlapped_bars_since_market_open_pct": feature_overlapped_bars_since_market_open_pct,
#             "feature_weak_bars_to_bars_since_highest_high_to_total_bars": feature_weak_bars_to_bars_since_highest_high_to_total_bars,
#             "feature_crossed_highest_high": feature_crossed_highest_high,
#             "feature_entry_bar_volume_average_above_threshold": potential_confirmation_bar.volume_average > 50000,
#             "feature_volume_avergae_above_10000_pct_above_threshold": volume_avergae_above_10000_counter/total_bars >= 0.8,
#             "feature_is_there_highest_high_after_market_open": feature_is_there_highest_high_after_market_open,
#             "feature_distance_from_highest_high_since_market_open": feature_distance_from_highest_high_since_market_open,
#             "feature_entry_bar_lowest_wick_to_bar_body_pct": (potential_confirmation_bar.open_value - potential_confirmation_bar.low)/(potential_confirmation_bar.close - potential_confirmation_bar.open_value) if potential_confirmation_bar.close - potential_confirmation_bar.open_value > 0 else 0,
#             "feature_entry_bar_volume": potential_confirmation_bar.volume,
#             "feature_entry_volume_vs_total_volume": potential_confirmation_bar.volume/(total_volume - potential_confirmation_bar.volume) if (total_volume - potential_confirmation_bar.volume) > 0 else 1,
#             "feature_distance_from_highest_high": highest_high_bar_since_market_open.index if highest_high_bar_since_market_open is not None else 0,
#             "feature_bars_with_rejection_since_market_open": bars_with_rejection_since_market_open/total_bars,
#             "feature_entry_point_size_to_bars_size_average": (potential_confirmation_bar.close - potential_confirmation_bar.open_value)/bars_size_average if bars_size_average else 0,
#             "feature_volume_average_to_volume": potential_confirmation_bar.volume_average/potential_confirmation_bar.volume,
#             "feature_entry_bar_has_highest_volume": feature_entry_bar_has_highest_volume,
#             "feature_entry_bar_is_biggest_bar": feature_entry_bar_is_biggest_bar,
#             "feature_entry_bar_is_highest": feature_entry_bar_is_highest,
#             "feature_histogram_changed_directions_pct": histogram_changed_directions_counter/total_bars,
#             "feature_volume_average_goes_down_pct": volume_average_goes_down_counter/total_bars,
#             "feature_strong_negative_bars_pct": strong_negative_bars_counter/negative_bars_counter if negative_bars_counter > 0 else 0,
#             "feature_rejected_pick_points_pct": rejected_pick_points_counter/pick_points_counter if pick_points_counter > 0 else 0,
#             "feature_price_action_is_stuck_pct": price_action_is_stuck_counter/total_bars,
#             "feature_bars_closed_above_half_of_bar_pct": bars_closed_above_half_of_bar_counter/total_bars,
#             "feature_stronger_than_previous_bars_pct": stronger_than_previous_bars_counter/total_bars,
#             "feature_bars_with_ordered_indicators_pct": bars_with_ordered_indicators_counter/total_bars,
#             "feature_last_bars_positive_movement_pct": feature_last_bars_positive_movement_pct,
#             "feature_indecision_bars_pct": indecision_bars_counter/total_bars,
#             "feature_negative_bars_with_positive_histogram_pct": negative_bars_with_positive_histogram/negative_bars_counter if negative_bars_counter > 0 else 1,
#             "feature_entry_bar_close_to_crossed_highest_high_pct": potential_confirmation_bar.close/highest_high_one_minute_bar.high,
#             "feature_bar_getting_high_while_9_ema_getting_down": feature_bar_getting_high_while_9_ema_getting_down,
#             "feature_crossed_bar_with_big_resistance": feature_crossed_bar_with_big_resistance,
#             "feature_total_volume": total_volume,
#             "feature_crossed_any_resistance": crossed_any_resistance,
#             "feature_crossed_any_near_resistance": crossed_any_near_resistance,
#             "feature_entry_bar_closed_strong": feature_entry_bar_closed_strong,
#             "feature_current_macd_to_previous": feature_current_macd_to_previous,
#             "feature_highest_volume_average_greater_than_entry_bar": highest_volume_average > potential_confirmation_bar.volume_average,
#             "feature_highest_high_was_recently": highest_high_one_minute_bar.index < potential_confirmation_bar.index+30,
#             "feature_ema_9_crossed_down_ema_20_since_pullback": ema_9_crossed_down_ema_20_since_pullback,
#             "feature_bar_closed_under_vwap_during_pullback": bar_closed_under_vwap_during_pullback,
#             "feature_bar_histogram_changed_direction": feature_bar_histogram_changed_direction,
#             "feature_entry_bar_shape_is_good": feature_entry_bar_shape_is_good,
#             "feature_volume_bigger_than_last_10_bars_pct": volume_bigger_than_last_bars_count/10,
#             "feature_bars_been_crossed_in_the_last_10_bars_pct": bars_been_crossed_count/10,
#         }

#         return features
