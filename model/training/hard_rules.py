#pylint:disable=too-many-lines
def should_be_rejected_by_hard_rules(
    features_data: dict[str, float],
) -> bool:
    current_day_volume_to_recent_days_volume = features_data["feature_current_day_volume_to_recent_days_volume"]
    current_day_high_to_previous_high = features_data["feature_current_day_high_to_previous_high"]
    gains_until_entry_bar = features_data["feature_gains_until_entry_bar"]
    controlled_volume_entry_quality = features_data["feature_controlled_volume_entry_quality"]
    entry_extension_pressure = features_data["feature_entry_extension_pressure"]
    entry_breakout_efficiency_from_ema_9 = features_data["feature_entry_breakout_efficiency_from_ema_9"]
    current_day_movement_to_recent_days_movement = features_data["feature_current_day_movement_to_recent_days_movement"]
    entry_bar_upper_wick = features_data["feature_entry_bar_upper_wick"]
    entry_histogram_to_highest_histogram = features_data["feature_entry_bar_histogram_to_highest_histogram"]
    entry_volume_to_highest_volume_in_pullback = features_data["feature_entry_bar_volume_to_highest_volume_in_pullback"]
    entry_volume_price_efficiency = features_data["feature_entry_volume_price_efficiency"]
    current_day_low_to_ema_9 = features_data["feature_current_day_low_to_ema_9"]
    entry_bar_close_to_highest_high = features_data["feature_entry_bar_close_to_highest_high"]
    price_movement_from_highest_high_to_lowest_low = features_data["feature_price_movement_from_highest_high_to_lowest_low"]
    entry_bar_body = features_data["feature_entry_bar_body"]
    entry_bar_low_to_ema_9 = features_data["feature_entry_bar_low_to_ema_9"]
    bars_since_highest_high_to_bars_before = features_data["feature_bars_since_highest_high_to_bars_before"]
    volume_since_highest_high_to_volume_before = features_data["feature_volume_since_highest_high_to_volume_before"]
    previous_bar_volume_to_its_previous_volume = features_data["feature_previous_bar_volume_to_its_previous_volume"]
    previous_bar_high_to_highest_high = features_data["feature_previous_bar_high_to_highest_high"]
    entry_bar_volume_to_highest_high_volume = features_data["feature_entry_bar_volume_to_highest_high_volume"]
    entry_bar_volume_to_recent_bars_average = features_data["feature_entry_bar_volume_to_recent_bars_average"]
    entry_upper_wick_to_recent_upper_wick_average = features_data["feature_entry_upper_wick_to_recent_upper_wick_average"]
    entry_body_to_highest_high_body = features_data["feature_entry_body_to_highest_high_body"]
    pullback_depth_vs_pre_high_move = features_data["feature_pullback_depth_vs_pre_high_move"]
    recent_bars_up_trend_pct = features_data["feature_recent_bars_up_trend_pct"]
    entry_body_to_recent_bars_body_average = features_data["feature_entry_body_to_recent_bars_body_average"]
    pre_market_volume = features_data["feature_pre_market_volume"]
    entry_close_to_vwap = features_data["feature_entry_close_to_vwap"]
    entry_bar_histogram_to_previous = features_data["feature_entry_bar_histogram_to_previous"]
    gains_since_lowest_low = features_data["feature_gains_since_lowest_low"]
    recent_bars_positive_bars_pct = features_data["feature_recent_bars_positive_bars_pct"]
    emas_distances_to_recent_bars_ema_distances = features_data["feature_emas_distances_to_recent_bars_ema_distances"]
    minutes_since_market_open = features_data["feature_minutes_since_market_open"]
    entry_close_to_previous_bar_close = features_data["feature_entry_close_to_previous_bar_close"]
    entry_body_to_previous_bar_body = features_data["feature_entry_body_to_previous_bar_body"]
    current_day_ema_9_to_ema_20_distance_to_recent_days = features_data["feature_current_day_ema_9_to_ema_20_distance_to_recent_days"]
    entry_bar_volume_to_previous_bar_volume = features_data["feature_entry_bar_volume_to_previous_bar_volume"]
    entry_bar_macd_to_previous = features_data["feature_entry_bar_macd_to_previous"]
    entry_close_position_vs_previous_close_position = features_data["feature_entry_close_position_vs_previous_close_position"]
    entry_bar_open_to_ema_9 = features_data["feature_entry_bar_open_to_ema_9"]
    profit_since_open_to_bars_count_since_open = features_data["feature_profit_since_open_to_bars_count_since_open"]
    entry_close_strength_to_highest_high_close_strength = features_data["feature_entry_close_strength_to_highest_high_close_strength"]
    reclaim_close_strength_since_highest_high = features_data["feature_reclaim_close_strength_since_highest_high"]
    entry_bar_lower_wick = features_data["feature_entry_bar_lower_wick"]
    entry_close_to_previous_bar_high = features_data["feature_entry_close_to_previous_bar_high"]
    volume_without_macd_confirmation = features_data["feature_volume_without_macd_confirmation"]
    bars_above_volume_average_vs_under_since_highest_high = features_data["feature_bars_above_volume_average_vs_under_since_highest_high"]
    entry_bar_vwap_to_ema_20 = features_data["feature_entry_bar_vwap_to_ema_20"]
    failed_pressure_to_followthrough = features_data["feature_failed_pressure_to_followthrough"]
    current_day_vwap_to_recent_days = features_data["feature_current_day_vwap_to_recent_days"]
    entry_bar_ema_9_to_vwap = features_data["feature_entry_bar_ema_9_to_vwap"]
    highest_high_to_entry_elapsed_minutes = features_data["feature_highest_high_to_entry_elapsed_minutes"]
    highest_high_quality = features_data["feature_highest_high_quality"]
    entry_followthrough_after_near_reclaim = features_data["feature_entry_followthrough_after_near_reclaim"]
    near_high_weak_followthrough = features_data["feature_near_high_weak_followthrough"]
    macd_recovery_followthrough_quality = features_data["feature_macd_recovery_followthrough_quality"]
    entry_bar_volume_to_volume_average = features_data["feature_entry_bar_volume_to_volume_average"]
    volume_since_lowest_low_to_entry_vs_since_highest_high = features_data["feature_volume_since_lowest_low_to_entry_vs_since_highest_high"]
    total_volume = features_data["total_volume"]
    current_day_ema_9_to_ema_20 = features_data["feature_current_day_ema_9_to_ema_20"]
    entry_close_to_lowest_low_recovery = features_data["feature_entry_close_to_lowest_low_recovery"]
    current_day_ema_20_to_recent_days_ema_20 = features_data["feature_current_day_ema_20_to_recent_days_ema_20"]
    entry_bar_volume = features_data["feature_entry_bar_volume"]
    current_day_ema_9_to_recent_days_ema_9 = features_data["feature_current_day_ema_9_to_recent_days_ema_9"]
    current_day_high_to_recent_days_highs = features_data["feature_current_day_high_to_recent_days_highs"]
    entry_bar_ema_9_to_ema_20 = features_data["feature_entry_bar_ema_9_to_ema_20"]
    pre_market_gains = features_data["feature_pre_market_gains"]
    entry_rejection_pressure = features_data["feature_entry_rejection_pressure"]
    entry_bar_volume_to_total_volume = features_data["feature_entry_bar_volume_to_total_volume"]
    pullback_health = features_data["feature_pullback_health"]
    histogram_changed_to_positive_direction_vs_negative_pct = features_data["feature_histogram_changed_to_positive_direction_vs_negative_pct"]
    macd_recovery_age_quality = features_data["feature_macd_recovery_age_quality"]
    previous_bar_close_to_highest_high = features_data["feature_previous_bar_close_to_highest_high"]
    failed_attempts_pressure = features_data["feature_failed_attempts_pressure"]
    uptrend_histogram_vs_downtrend_since_highest_high = features_data["feature_uptrend_histogram_vs_downtrend_since_highest_high"]
    entry_volume_spike_without_high_context = features_data["feature_entry_volume_spike_without_high_context"]
    inefficient_breakout_extension = features_data["feature_inefficient_breakout_extension"]
    fake_reclaim_pressure = features_data["feature_fake_reclaim_pressure"]
    positive_vs_negative_volume_during_pullback = features_data["feature_positive_vs_negative_volume_during_pullback"]
    volume_confirmation_quality = features_data["feature_volume_confirmation_quality"]
    clean_reentry_confirmation = features_data["feature_clean_reentry_confirmation"]
    entry_bar_movement_recent_bars_average = features_data["feature_entry_bar_movement_recent_bars_average"]
    distance_from_last_negative_macd_bar = features_data["feature_distance_from_last_negative_macd_bar"]
    breakout_attempts_during_pullback = features_data["feature_breakout_attempts_during_pullback"]
    entry_bar_histogram_to_lowest_histogram = features_data["feature_entry_bar_histogram_to_lowest_histogram"]
    clean_breakout_efficiency = features_data["feature_clean_breakout_efficiency"]

    # Major reject family: weak reclaim / weak breakout / weak extension.
    # These are setups where the candle may look like a reclaim,
    # but breakout efficiency, bounce quality, rejection pressure,
    # or extension quality is structurally weak.
    if (
        (
            entry_bar_low_to_ema_9 > 1.0070604682
            and gains_since_lowest_low <= 0.0916305929
            and entry_rejection_pressure > 0.023473856
            and entry_close_to_previous_bar_high > 1.0530339479
            and current_day_vwap_to_recent_days <= 7.642689643659104
            and entry_followthrough_after_near_reclaim > 1.073159808628476
            and bars_above_volume_average_vs_under_since_highest_high > 0
            and entry_bar_close_to_highest_high < 1.0188677346643054
        )
        or (
            entry_breakout_efficiency_from_ema_9 <= 0.4921557903
            and gains_until_entry_bar > 0.2806035727
            and current_day_volume_to_recent_days_volume <= 5.4054927826
            and pre_market_volume > 19492
            and current_day_low_to_ema_9 <= 1.1302526593
            and entry_close_strength_to_highest_high_close_strength <= 3.1998206377
            and inefficient_breakout_extension <= 0.0
            and current_day_vwap_to_recent_days <= 1.39595737727032
            and current_day_ema_9_to_ema_20_distance_to_recent_days >= 0.9692596835497636
        )
        or (
            entry_bar_low_to_ema_9 > 1.0070604682
            and gains_since_lowest_low <= 0.1303373128
            and entry_bar_upper_wick > 0.0226323679
            and entry_close_to_previous_bar_high > 1.0530339479
            and pre_market_gains <= 1.1489825845
            and current_day_low_to_ema_9 > 0.7408934236
            and macd_recovery_age_quality >= 14.07288225230256
            and near_high_weak_followthrough > 0.823546946
            and entry_bar_lower_wick <= 0.3502510786
            and entry_volume_spike_without_high_context < 2.743258749282846
        )
        or (
            entry_bar_low_to_ema_9 > 1.0070604682
            and gains_since_lowest_low >= 0.038548752834467
            and histogram_changed_to_positive_direction_vs_negative_pct > 1.030952394
            and current_day_ema_9_to_recent_days_ema_9 <= 2.0428084135
            and entry_bar_macd_to_previous <= 1.1608323455
            and pre_market_volume > 6389.9147949219
            and entry_volume_to_highest_volume_in_pullback > 1.0537672043
            and entry_extension_pressure <= 0.2560228407
        )
        or (
            reclaim_close_strength_since_highest_high >= 0.5555
            and entry_rejection_pressure >= 0.1428
            and entry_breakout_efficiency_from_ema_9 <= 0.6955
            and entry_bar_body >= 0.6666
            and current_day_vwap_to_recent_days <= 2.1286
            and entry_bar_volume_to_total_volume <= 0.227660134288
            and pre_market_gains <= 0.7774401823005571
            and entry_extension_pressure <= 0.84
        )
        or (
            entry_bar_low_to_ema_9 > 1.0070604682
            and gains_since_lowest_low <= 0.1303373128
            and entry_rejection_pressure > 0.023473856
            and entry_close_to_previous_bar_high > 1.0530339479
            and pre_market_gains <= 1.1489825845
            and current_day_low_to_ema_9 > 0.7408934236
            and macd_recovery_followthrough_quality <= 19.2633743286
            and total_volume <= 258551312.0
            and emas_distances_to_recent_bars_ema_distances > 0.1030314825
            and current_day_movement_to_recent_days_movement > 1.1011566698988786
            and current_day_vwap_to_recent_days <= 3.565152257209529
            and entry_bar_volume_to_volume_average <= 6.53772529741
            and entry_rejection_pressure >= 0.033
        )
        or (
            current_day_movement_to_recent_days_movement >= 6.5162
            and gains_since_lowest_low <= 0.228448275862
            and entry_body_to_previous_bar_body >= 2.8959
            and current_day_ema_9_to_recent_days_ema_9 <= 1.4831883273158324
            and entry_bar_close_to_highest_high >= 1.0178
            and bars_since_highest_high_to_bars_before <= 0.0141
            and recent_bars_up_trend_pct >= 0.4
            and entry_rejection_pressure <= 0.28
        )
        or (
            entry_breakout_efficiency_from_ema_9 <= 0.4368653595
            and entry_bar_macd_to_previous > 0.4929415584
            and entry_close_to_vwap > 1.1723103523
            and highest_high_quality > 1.6963175535
            and reclaim_close_strength_since_highest_high > 0.2052604109
            and entry_bar_low_to_ema_9 <= 1.0156897902
            and total_volume > 391419.5
            and failed_attempts_pressure <= 0.4304142594
            and recent_bars_up_trend_pct > 0.650000006
        )
    ):
        return True

    # Major reject family: pullback/body/volume failure.
    # These setups either have too shallow a reset,
    # or a deeper pullback where the entry body/volume does not confirm clean continuation.
    if (
        (
            pullback_depth_vs_pre_high_move > 0.5807133615016937
            and entry_bar_body <= 0.6001200675964355
            and entry_bar_volume_to_volume_average <= 2.208707094192505
            and entry_close_strength_to_highest_high_close_strength <= 1.479868233203888
            and macd_recovery_age_quality <= 24.621222496032715
            and current_day_ema_9_to_recent_days_ema_9 <= 4.0
        )
        or (
            pullback_depth_vs_pre_high_move <= 0.44685098528862
            and entry_close_to_vwap > 1.172208309173584
            and entry_bar_body <= 0.8797127604484558
            and entry_bar_volume_to_total_volume <= 0.4040
        )
        or (
            entry_body_to_recent_bars_body_average <= 3.138
            and pullback_depth_vs_pre_high_move >= 1.3531
            and entry_bar_volume_to_previous_bar_volume <= 2.0443
            and entry_bar_histogram_to_previous >= 0.5029
            and current_day_movement_to_recent_days_movement <= 6.104
            and pre_market_gains >= -0.0354838709677418
            and pre_market_gains <= 0.7774401823005571
        )
        or (
            gains_since_lowest_low <= 0.2115384615384616
            and previous_bar_volume_to_its_previous_volume <= 0.896686726772411
            and previous_bar_volume_to_its_previous_volume >= 0.5973
            and entry_upper_wick_to_recent_upper_wick_average >= 0.5068
            and current_day_high_to_recent_days_highs <= 1.8587
            and entry_bar_volume_to_highest_high_volume <= 2.2372
            and highest_high_quality >= 0.0858358066383931
        )
        or (
            price_movement_from_highest_high_to_lowest_low > 4.995
            and entry_bar_lower_wick > 0.132
            and entry_bar_volume_to_highest_high_volume <= 1.098
        )
        or (
            controlled_volume_entry_quality <= 1.418
            and pullback_depth_vs_pre_high_move >= 1.93
            and entry_bar_open_to_ema_9 <= 1.0014
            and entry_body_to_recent_bars_body_average <= 4.16585744804817
        )
        or (
            entry_volume_to_highest_volume_in_pullback >= 2.207124555748409
            and volume_without_macd_confirmation <= 1.3859621588
            and entry_close_to_vwap <= 1.192665838838092
            and bars_above_volume_average_vs_under_since_highest_high <= 1.0
            and volume_since_highest_high_to_volume_before >= 0.0035742178902402
        )
        or (
            bars_since_highest_high_to_bars_before <= 0.1951219512195122
            and gains_since_lowest_low <= 0.2146118721461188
            and pre_market_volume <= 0.0
            and pullback_depth_vs_pre_high_move <= 2.0677942074938342
            and entry_close_position_vs_previous_close_position <= 800
        )
    ):
        return True

    # Major reject family: low premarket / liquidity weakness.
    # These are weak-liquidity setups where the entry candle may look active,
    # but premarket support, efficiency, volume balance, or recent participation is not enough.
    if (
        (
            entry_volume_price_efficiency <= 0.02588854677
            and pre_market_volume <= 47862
            and recent_bars_positive_bars_pct >= 0.6
            and entry_close_to_previous_bar_high >= 1.0431372549019609
        )
        or (
            pre_market_volume <= 4972.5
            and current_day_high_to_previous_high <= 1.9557220936
            and entry_bar_volume <= 45106.3496
            and positive_vs_negative_volume_during_pullback <= 1.1987136006
            and entry_bar_low_to_ema_9 <= 1.04
        )
        or (
            pre_market_volume <= 4998.5
            and entry_bar_body <= 0.5862445831
            and volume_without_macd_confirmation <= 1.5416671634
            and minutes_since_market_open > 30
        )
        or (
            pre_market_volume <= 4998.5
            and entry_bar_body > 0.6565625072
            and current_day_ema_9_to_ema_20 > 1.0782429576
            and gains_since_lowest_low <= 0.2610012591
            and entry_bar_lower_wick <= 0.0270362683
        )
        or (
            pre_market_volume > 4972.5
            and minutes_since_market_open <= 12.5
            and recent_bars_up_trend_pct <= 0.650000006
        )
        or (
            pre_market_volume > 4998.5
            and current_day_ema_9_to_recent_days_ema_9 <= 1.1541311145
            and entry_bar_ema_9_to_ema_20 > 1.0535026193
            and current_day_movement_to_recent_days_movement <= 7.0314149857
            and entry_bar_volume_to_highest_high_volume <= 1.4427253604
        )
        or (
            total_volume <= 499196.6
            and entry_histogram_to_highest_histogram >= 2.1306
        )
        or (
            current_day_volume_to_recent_days_volume <= 5.698130559
            and entry_bar_low_to_ema_9 >= 1.0189563
            and entry_bar_ema_9_to_vwap >= 1.09945013
            and entry_volume_price_efficiency < 0.4123782583330475
        )
    ):
        return True

    # Major reject family: volume reclaim / pressure failure.
    # These setups show pressure, volume spikes, or close-position expansion,
    # but the followthrough/confirmation structure is still weak.
    if (
        (
            failed_pressure_to_followthrough >= 0.4017
            and entry_close_position_vs_previous_close_position >= 1.6041
            and bars_above_volume_average_vs_under_since_highest_high <= 0.8334
            and controlled_volume_entry_quality >= 2.2409
            and minutes_since_market_open >= 60
            and current_day_low_to_ema_9 >= 0.8095
            and entry_close_to_previous_bar_high < 1.1054054054054052
        )
        or (
            entry_bar_volume_to_recent_bars_average >= 4.6813
            and reclaim_close_strength_since_highest_high >= 0.5359
            and pullback_health <= 3.72281
            and entry_upper_wick_to_recent_upper_wick_average <= 0.58855
            and entry_close_to_lowest_low_recovery >= 1.34
            and pre_market_gains >= -0.01879
            and previous_bar_volume_to_its_previous_volume >= 0.3763
            and pre_market_volume >= 876.0
        )
        or (
            price_movement_from_highest_high_to_lowest_low >= 1.3499
            and entry_bar_upper_wick >= 0.1702
            and entry_close_position_vs_previous_close_position >= 1.7663
            and entry_bar_volume_to_total_volume >= 0.02298
        )
        or (
            entry_close_strength_to_highest_high_close_strength <= 0.947374
            and entry_bar_volume_to_recent_bars_average >= 9.089611
            and failed_pressure_to_followthrough < 1.8032795612091643
            and entry_volume_spike_without_high_context >= 0.0108463987712592
        )
        or (
            bars_above_volume_average_vs_under_since_highest_high > 0.2539
            and current_day_movement_to_recent_days_movement > 2.2284
            and entry_bar_low_to_ema_9 <= 1.00354
            and entry_breakout_efficiency_from_ema_9 > 0.4921
            and entry_close_to_previous_bar_close <= 1.1124
            and entry_histogram_to_highest_histogram <= 0.4558
            and entry_volume_to_highest_volume_in_pullback > 1.2703
            and entry_rejection_pressure > 0
        )
    ):
        return True

    # Major reject family: high-structure retest / rejection.
    # These are attempts near the highest-high where the previous bar is already near/over the high,
    # but the entry still shows weak body, weak wick context, or weak volume share.
    if (
        (
            previous_bar_high_to_highest_high <= 0.9955507815
            and previous_bar_high_to_highest_high > 0.9713259339
            and entry_bar_volume_to_recent_bars_average <= 1.89085114
            and entry_bar_ema_9_to_vwap > 1.1076951027
            and entry_bar_open_to_ema_9 > 1.0056756735
        )
        or (
            previous_bar_high_to_highest_high > 0.9955507815
            and entry_upper_wick_to_recent_upper_wick_average > 0.6726041138
            and entry_breakout_efficiency_from_ema_9 <= 0.7530556917
            and entry_close_strength_to_highest_high_close_strength <= 0.7273891568
            and entry_bar_volume_to_total_volume <= 0.2503615810967913
        )
        or (
            previous_bar_high_to_highest_high >= 1.0031150793650794
            and entry_bar_ema_9_to_ema_20 >= 1.053391820032275
            and entry_upper_wick_to_recent_upper_wick_average >= 0.6957268870518433
            and previous_bar_volume_to_its_previous_volume < 1.9726128342701927
        )
        or (
            entry_close_position_vs_previous_close_position <= 0.7012
            and volume_since_highest_high_to_volume_before <= 0.6092
        )
        or (
            bars_since_highest_high_to_bars_before <= 0.0018939393939393
            and entry_body_to_highest_high_body <= 1.271
            and entry_body_to_previous_bar_body <= 4.333333333333294
            and not clean_reentry_confirmation
        )
        or (
            highest_high_to_entry_elapsed_minutes <= 4
            and entry_bar_volume_to_total_volume <= 0.0186582446829219
            and entry_bar_close_to_highest_high <= 1.0121
            and entry_bar_open_to_ema_9 >= 1.003
            and current_day_ema_9_to_recent_days_ema_9 <= 4.0
        )
    ):
        return True

    # Major reject family: extended VWAP / daily-context failure.
    # These are daily-context expansion setups where the entry is chasing,
    # volume/high structure is weak, or pullback confirmation is poor.
    if (
        (
            entry_bar_low_to_ema_9 <= 1.0070604682
            and current_day_vwap_to_recent_days > 1.2754222155
            and current_day_high_to_recent_days_highs > 1.3807946444
            and entry_bar_volume_to_previous_bar_volume <= 5.0618071556
            and emas_distances_to_recent_bars_ema_distances > 0.0787730142
            and volume_since_highest_high_to_volume_before <= 0.5391068757
            and entry_bar_vwap_to_ema_20 <= 0.9406876862
            and volume_since_lowest_low_to_entry_vs_since_highest_high > 0.7631361485
            and current_day_low_to_ema_9 > 1.0629708767
            and entry_bar_movement_recent_bars_average >= 1.8572
            and entry_bar_volume_to_total_volume >= 0.00999352744067
            and current_day_ema_9_to_recent_days_ema_9 <= 4.0
        )
        or (
            current_day_vwap_to_recent_days <= 2.2341
            and current_day_high_to_recent_days_highs >= 2.3105
            and pullback_depth_vs_pre_high_move <= 0.5717007696228753
        )
        or (
            entry_bar_volume_to_highest_high_volume <= 1.4731575251
            and emas_distances_to_recent_bars_ema_distances <= 1.070509851
            and current_day_vwap_to_recent_days <= 2.1132727861
            and current_day_ema_9_to_ema_20_distance_to_recent_days > 2.4748704433
            and entry_close_to_vwap > 1.1157248616
            and entry_close_to_vwap <= 1.2302240729
            and minutes_since_market_open <= 267
            and profit_since_open_to_bars_count_since_open <= 0.0179995298
            and entry_body_to_highest_high_body <= 5.3399999142
            and entry_bar_close_to_highest_high > 1.0051801205
            and entry_bar_body <= 0.9892086330935264
            and entry_bar_close_to_highest_high <= 1.0118694362017804
        )
        or (
            entry_bar_ema_9_to_ema_20 > 1.0544950962
            and current_day_high_to_recent_days_highs <= 1.879216373
            and total_volume > 7206239
            and entry_followthrough_after_near_reclaim <= 1.4948156476
        )
        or (
            current_day_vwap_to_recent_days <= 1.404
            and positive_vs_negative_volume_during_pullback <= 0.31
            and entry_close_strength_to_highest_high_close_strength <= 1.052
            and macd_recovery_age_quality > 11.472846724011536
            and entry_close_to_previous_bar_high >= 1.0543184885290149
            and entry_extension_pressure >= 0.0943
        )
    ):
        return True

    # Reject: high-volume setup where the entry reclaims above previous close,
    # but extension pressure is weak, post-high volume rebuild is already heavy,
    # and the bounce from the low is still limited.
    if (
        total_volume > 8426614.5
        and entry_extension_pressure <= 0.392113
        and volume_since_highest_high_to_volume_before > 0.548121
        and gains_since_lowest_low <= 0.39163
        and entry_close_to_previous_bar_close > 1.077152
        and previous_bar_high_to_highest_high <= 1.014947
    ):
        return True

    if (
        previous_bar_high_to_highest_high > 0.9955507814884186
        and entry_upper_wick_to_recent_upper_wick_average > 0.672604113817215
        and entry_bar_volume > 19377.8037109375
        and gains_until_entry_bar > 0.15879975259304047
        and entry_bar_histogram_to_previous > 0.4862351715564728
        and entry_bar_body > 0.40687979757785797
        and entry_breakout_efficiency_from_ema_9 <= 0.7530556917190552
        and pre_market_volume <= 15563601.0
        and price_movement_from_highest_high_to_lowest_low <= 4.099999904632568
        and entry_body_to_previous_bar_body <= 4.946176528930664
        and positive_vs_negative_volume_during_pullback <= 3.7747384309768677
        and entry_body_to_highest_high_body <= 52.3
        and current_day_ema_9_to_recent_days_ema_9 <= 4.0
    ):
        return True

    if (
        previous_bar_high_to_highest_high > 0.9965063631534576
        and entry_upper_wick_to_recent_upper_wick_average > 0.672604113817215
        and entry_bar_ema_9_to_vwap > 1.0428656935691833
        and current_day_ema_9_to_recent_days_ema_9 > 0.7825587093830109
        and current_day_ema_9_to_recent_days_ema_9 <= 4.0
        and entry_breakout_efficiency_from_ema_9 <= 0.7530556917190552
        and pre_market_volume <= 15563601.0
        and entry_body_to_highest_high_body <= 2.502500057220459
        and entry_bar_lower_wick <= 0.5024212896823883
        and volume_confirmation_quality <= 1.667735755443573
        and entry_bar_body <= 0.9106597304344177
    ):
        return True

    if (
        entry_bar_volume_to_recent_bars_average > 1.8908511400222778
        and pullback_health > 0.9136257469654083
        and current_day_vwap_to_recent_days > 2.006888747215271
        and bars_since_highest_high_to_bars_before > 0.01178454514592886
        and previous_bar_high_to_highest_high <= 0.9955507814884186
        and current_day_low_to_ema_9 <= 1.1150060892105103
        and entry_bar_macd_to_previous <= 0.9387879967689514
        and pre_market_gains <= 1.547519028186798
        and entry_close_to_previous_bar_close <= 1.32196044921875
        and current_day_vwap_to_recent_days <= 3.9065240621566772
        and entry_volume_to_highest_volume_in_pullback <= 2.7033112049102783
        and entry_close_to_vwap >= 1.147
    ):
        return True

    if (
        pullback_depth_vs_pre_high_move <= 0.5807133615016937
        and entry_body_to_recent_bars_body_average <= 2.9088518619537354
        and current_day_ema_9_to_ema_20_distance_to_recent_days <= 2.0150817036628723
        and entry_bar_volume_to_volume_average <= 6.434927463531494
    ):
        return True

    if (
        previous_bar_high_to_highest_high > 0.9962527751922607
        and bars_since_highest_high_to_bars_before > 0.002998830983415246
        and near_high_weak_followthrough > 0.8628861904144287
        and entry_close_to_vwap > 1.0906840562820435
        and entry_bar_vwap_to_ema_20 > 0.7922076880931854
        and entry_upper_wick_to_recent_upper_wick_average <= 0.672604113817215
        and current_day_low_to_ema_9 <= 1.0580149292945862
        and reclaim_close_strength_since_highest_high <= 0.6921752095222473
        and pullback_health <= 9.686372756958008
        and total_volume <= 193450808.0
        and pre_market_gains <= 0.398
        and entry_extension_pressure >= 0.059
    ):
        return True

    if (
        entry_bar_volume_to_recent_bars_average > 1.8908511400222778
        and pullback_health > 0.9136257469654083
        and volume_without_macd_confirmation > 0.6141909956932068
        and pre_market_volume > 562394.0
        and previous_bar_high_to_highest_high <= 0.9955507814884186
        and current_day_low_to_ema_9 <= 1.1150060892105103
        and entry_bar_macd_to_previous <= 0.9387879967689514
        and current_day_vwap_to_recent_days <= 2.006888747215271
        and current_day_high_to_recent_days_highs <= 1.8599517345428467
        and entry_bar_ema_9_to_vwap <= 1.1866434812545776
        and entry_volume_price_efficiency <= 0.3189230039715767
        and current_day_ema_9_to_ema_20 <= 1.311029368268173
        and entry_volume_price_efficiency >= 0.014
        and previous_bar_close_to_highest_high >= 0.965
    ):
        return True

    if (
        previous_bar_high_to_highest_high > 0.9955507814884186
        and entry_upper_wick_to_recent_upper_wick_average <= 0.30692431330680847
        and bars_since_highest_high_to_bars_before <= 0.002998830983415246
        and entry_body_to_recent_bars_body_average <= 16.909310340881348
        and pre_market_gains <= 0.8412856012582779
        and entry_close_to_lowest_low_recovery <= 7.416666507720947
    ):
        return True

    if (
        entry_bar_volume_to_recent_bars_average >= 8.8
        and entry_bar_volume_to_total_volume <= 0.055
        and entry_bar_low_to_ema_9 <= 1.0
        and pre_market_gains <= 0
        and entry_close_strength_to_highest_high_close_strength <= 3.0
        and entry_bar_body <= 0.85
    ):
        return True

    if (
        current_day_ema_9_to_recent_days_ema_9 >= 1.35
        and entry_bar_volume_to_total_volume <= 0.012
        and entry_close_strength_to_highest_high_close_strength <= 1.2
        and entry_bar_low_to_ema_9 <= 1.005
        and pre_market_gains <= 0.04
        and entry_bar_body <= 0.86
    ):
        return True

    if (
        entry_bar_vwap_to_ema_20 <= 0.9903881602526934
        and gains_until_entry_bar <= 1.0722402930
        and entry_volume_to_highest_volume_in_pullback <= 1.8528105021
        and current_day_movement_to_recent_days_movement > 8.3926472664
        and entry_body_to_highest_high_body <= 13.3459329605
        and current_day_vwap_to_recent_days > 1.461265299777554
        and gains_since_lowest_low <= 0.56
        and entry_breakout_efficiency_from_ema_9 > 0.3267045912611484
    ):
        return True

    if (
        entry_bar_low_to_ema_9 <= 1.0070604682
        and entry_breakout_efficiency_from_ema_9 <= 0.9983366132
        and current_day_ema_9_to_recent_days_ema_9 <= 0.9913356900
        and entry_body_to_highest_high_body <= 4.6936500072
        and entry_rejection_pressure > 0.0012531328
        and entry_bar_vwap_to_ema_20 >= 0.7832668372258171
        and entry_body_to_previous_bar_body < 5.700066666666
        and volume_without_macd_confirmation <= 114.50953379574102
    ):
        return True

    if (
        entry_breakout_efficiency_from_ema_9 <= 0.4910371602
        and entry_bar_macd_to_previous <= 0.4929415584
        and previous_bar_close_to_highest_high <= 0.9681976736
        and entry_volume_to_highest_volume_in_pullback > 0.8198091388
        and current_day_movement_to_recent_days_movement > 1.9765470624
        and controlled_volume_entry_quality <= 620.9522094727
        and entry_bar_body <= 0.9365079105
        and pullback_health > 0.9441018105
        and emas_distances_to_recent_bars_ema_distances > 0.1493157074
        and entry_rejection_pressure >= 0.097087378642
    ):
        return True

    if (
        entry_breakout_efficiency_from_ema_9 <= 0.4572450357906625
        and entry_bar_macd_to_previous > 0.4929415584
        and entry_close_to_vwap > 1.1723103523
        and highest_high_quality > 1.6963175535
        and reclaim_close_strength_since_highest_high > 0.2052604109
        and entry_bar_low_to_ema_9 <= 1.0156897902
        and bars_since_highest_high_to_bars_before <= 0.9219741821
        and uptrend_histogram_vs_downtrend_since_highest_high <= 0.3951525092
        and volume_since_lowest_low_to_entry_vs_since_highest_high > 0.4856138527
        and pre_market_volume >= 7449
    ):
        return True

    if (
        pre_market_gains <= 0.0056163829285651445
        and price_movement_from_highest_high_to_lowest_low > 0.397149994969368
        and volume_since_highest_high_to_volume_before <= 0.8350349962711334
        and entry_bar_volume_to_previous_bar_volume > 1.1702489852905273
        and gains_since_lowest_low > 0.14865899831056595
        and entry_bar_volume_to_volume_average <= 2.095898747444153
    ):
        return True

    if (
        entry_close_strength_to_highest_high_close_strength <= 0.7199999999999989
        and entry_bar_volume_to_previous_bar_volume <= 2.23595627445762
        and entry_bar_body <= 0.8341666666666647
    ):
        return True

    if (
        entry_bar_open_to_ema_9 >= 1.02100165
        and entry_bar_close_to_highest_high <= 1.05555555556
        and current_day_ema_9_to_ema_20 >= 1.153187004
        and entry_bar_body <= 0.6721874999999996
        and pullback_health <= 2.6589815963267025
    ):
        return True

    if (
        current_day_ema_9_to_recent_days_ema_9 >= 1.27426832716
        and current_day_ema_20_to_recent_days_ema_20 <= 1.13188273075
        and entry_bar_ema_9_to_vwap <= 1.04418374495
        and volume_since_highest_high_to_volume_before >= 0.0040412767718574
        and entry_bar_volume_to_total_volume <= 0.225349232888
    ):
        return True

    if (
        entry_bar_volume >= 1130008.45
        and current_day_volume_to_recent_days_volume <= 8.40179578213
        and entry_body_to_recent_bars_body_average <= 3.07563963964
        and entry_rejection_pressure > 0
    ):
        return True

    if (
        pullback_depth_vs_pre_high_move <= 0.4368705484108274
        and profit_since_open_to_bars_count_since_open >= 0.00576
        and entry_bar_volume_to_volume_average <= 8.50
    ):
        return True

    if (
        entry_extension_pressure <= 0.11295875101172427
        and entry_bar_body <= 0.5507023034551829
    ):
        return True

    if (
        entry_bar_low_to_ema_9 <= 0.9834826278430685
        and entry_bar_ema_9_to_vwap <= 1.062694232648664
    ):
        return True

    if (
        entry_body_to_highest_high_body >= 21.0911
        and pullback_depth_vs_pre_high_move <= 0.8421832074
        and entry_close_to_vwap < 1.214043135738546
        and pre_market_gains <= 0.203125
        and volume_since_highest_high_to_volume_before >= 0.0083
    ):
        return True

    if (
        entry_bar_low_to_ema_9 >= 1.0372845392925112
        and entry_bar_histogram_to_lowest_histogram >= 1.266386431558122
        and distance_from_last_negative_macd_bar >= 12
    ):
        return True

    if (
        entry_bar_vwap_to_ema_20 <= 0.9514810741
        and current_day_vwap_to_recent_days <= 2.7823119164
        and profit_since_open_to_bars_count_since_open > 0.0132751414
        and bars_above_volume_average_vs_under_since_highest_high > 0.2250000015
        and entry_followthrough_after_near_reclaim > 1.0432881853785902
        and entry_upper_wick_to_recent_upper_wick_average > 0.3835864374007101
        and near_high_weak_followthrough <= 0.862386317520218
    ):
        return True

    if (
        current_day_movement_to_recent_days_movement > 2.2284
        and entry_bar_low_to_ema_9 <= 1.00354
        and entry_bar_lower_wick <= 0.0443
        and entry_breakout_efficiency_from_ema_9 > 0.4921
        and entry_histogram_to_highest_histogram <= 0.4558
        and entry_volume_to_highest_volume_in_pullback > 1.2703
        and near_high_weak_followthrough > 0.8687
    ):
        return True

    if (
        entry_extension_pressure > 0.7173990309
        and entry_bar_macd_to_previous <= 1.1105212569
    ):
        return True

    if (
        pullback_depth_vs_pre_high_move <= 0.88375
        and entry_body_to_previous_bar_body <= 0.98432
        and emas_distances_to_recent_bars_ema_distances <= 0.149473967112886
        and pullback_health <= 5.634074932605927
        and current_day_ema_9_to_recent_days_ema_9 <= 4.0
    ):
        return True

    if (
        gains_since_lowest_low <= 0.0491
        and entry_volume_to_highest_volume_in_pullback <= 0.893
        and entry_bar_volume_to_total_volume <= 0.0284
    ):
        return True

    if (
        current_day_movement_to_recent_days_movement >= 9.1927298390
        and entry_bar_lower_wick <= 0.0022260818
        and volume_since_lowest_low_to_entry_vs_since_highest_high >= 0.6822743076
        and current_day_low_to_ema_9 <= 1.0293851964429035
        and highest_high_quality >= 0.147032623908
    ):
        return True

    if (
        price_movement_from_highest_high_to_lowest_low <= 1.86
        and minutes_since_market_open <= 30.5
        and entry_bar_low_to_ema_9 <= 0.9938
        and entry_bar_volume > 335004
    ):
        return True

    if (
        price_movement_from_highest_high_to_lowest_low <= 4.995
        and minutes_since_market_open > 30.5
        and current_day_ema_9_to_ema_20_distance_to_recent_days <= 0.8482
        and clean_reentry_confirmation
        and total_volume >= 927001
    ):
        return True

    if (
        entry_bar_volume_to_total_volume >= 0.1046935351294476
        and entry_bar_vwap_to_ema_20 <= 0.9426331149875774
    ):
        return True

    if (
        failed_pressure_to_followthrough >= 0.4087759498495121
        and fake_reclaim_pressure <= 0.4155040928633324
    ):
        return True

    if (
        reclaim_close_strength_since_highest_high <= 0.0601
        and entry_upper_wick_to_recent_upper_wick_average <= 0.4476
    ):
        return True

    if (
        entry_body_to_highest_high_body <= 0.3977
        and entry_volume_to_highest_volume_in_pullback <= 0.7483
    ):
        return True

    if (
        recent_bars_positive_bars_pct <= 0.4
        and pre_market_gains <= -0.0682967959527823
    ):
        return True

    if (
        entry_bar_lower_wick >= 0.3599999999999994
        and entry_volume_to_highest_volume_in_pullback <= 0.7375094517384586
    ):
        return True

    if (
        controlled_volume_entry_quality <= 0.905
        and entry_body_to_previous_bar_body >= 21.15
        and entry_bar_volume_to_previous_bar_volume >= 4.345645918894326
    ):
        return True

    if (
        current_day_vwap_to_recent_days <= 1.5019456072
        and current_day_high_to_recent_days_highs >= 1.4439142795391444
        and entry_volume_price_efficiency <= 0.0256996691932799
    ):
        return True

    if (
        entry_volume_spike_without_high_context <= 1.927
        and volume_confirmation_quality <= 0.521
    ):
        return True

    if (
        previous_bar_volume_to_its_previous_volume >= 1.653460719663534
        and entry_bar_volume_to_highest_high_volume >= 6.98279758915118
        and entry_followthrough_after_near_reclaim <= 2.03305244211632
    ):
        return True

    if (
        macd_recovery_age_quality >= 16.58
        and entry_close_to_previous_bar_high >= 1.2408
        and total_volume <= 413805.0
        and minutes_since_market_open >= 58
    ):
        return True

    if (
        entry_volume_price_efficiency >= 0.8190
        and current_day_volume_to_recent_days_volume >= 131.07
        and distance_from_last_negative_macd_bar >= 12
    ):
        return True

    if (
        pullback_depth_vs_pre_high_move <= 0.7284
        and breakout_attempts_during_pullback >= 2
        and entry_body_to_previous_bar_body >= 15.9
    ):
        return True

    if (
        entry_close_position_vs_previous_close_position >= 3.4195
        and recent_bars_positive_bars_pct >= 0.72
        and entry_bar_volume_to_total_volume >= 0.1103
    ):
        return True

    if (
        total_volume <= 339183.0
        and entry_bar_ema_9_to_ema_20 >= 1.0394
        and entry_bar_volume_to_total_volume >= 0.1249
        and previous_bar_high_to_highest_high <= 1.0249
    ):
        return True

    if (
        highest_high_quality <= 0.2095
        and pre_market_gains >= 0.2355
        and total_volume >= 85786861.0
    ):
        return True

    if (
        current_day_high_to_previous_high <= 1.045
        and pre_market_volume <= 18560
    ):
        return True

    if (
        current_day_high_to_previous_high <= 0.85
        and entry_bar_volume_to_recent_bars_average >= 5
        and entry_body_to_previous_bar_body >= 5
        and entry_bar_volume_to_total_volume >= 0.05
    ):
        return True

    if (
        recent_bars_up_trend_pct >= 0.9
        and entry_volume_price_efficiency <= 0.1111710752349686
        and current_day_vwap_to_recent_days >= 1.8
        and entry_histogram_to_highest_histogram <= 1.2
    ):
        return True

    if (
        volume_confirmation_quality <= 0.2
        and current_day_vwap_to_recent_days >= 2.5
        and recent_bars_positive_bars_pct <= 0.4
        and entry_volume_spike_without_high_context >= 5
        and entry_bar_volume_to_total_volume >= 0.03
    ):
        return True

    if (
        previous_bar_close_to_highest_high <= 0.95
        and pre_market_volume <= 50000
        and recent_bars_positive_bars_pct <= 0.4
        and breakout_attempts_during_pullback >= 2
    ):
        return True

    if (
        current_day_vwap_to_recent_days <= 1.42
        and current_day_high_to_recent_days_highs >= 1.44
        and entry_bar_volume_to_total_volume >= 0.109
        and entry_bar_volume_to_recent_bars_average <= 2.145
        and pre_market_volume <= 500
    ):
        return True

    if (
        current_day_ema_9_to_recent_days_ema_9 >= 1.57698011498097
        and entry_bar_close_to_highest_high <= 1.0109454545454546
        and entry_extension_pressure >= 0.3105943493744694
        and entry_bar_volume >= 518983.0
        and entry_bar_ema_9_to_vwap >= 1.08
    ):
        return True

    if (
        gains_until_entry_bar > 0.4172315448522568
        and current_day_movement_to_recent_days_movement > 5.66583251953125
        and pre_market_gains > 3.3070324659347534
        and near_high_weak_followthrough <= 0.7769657671451569
    ):
        return True

    if (
        total_volume >= 8000000
        and current_day_low_to_ema_9 <= 0.91
        and gains_until_entry_bar >= 0.44
        and gains_until_entry_bar <= 0.53
        and entry_bar_volume_to_total_volume <= 0.031
        and pre_market_gains <= 0.083
        and current_day_movement_to_recent_days_movement >= 3.0
    ):
        return True

    if (
        gains_until_entry_bar >= 0.9
        and pre_market_gains >= 0.18
        and current_day_movement_to_recent_days_movement <= 5.2
        and entry_breakout_efficiency_from_ema_9 <= 0.72
        and entry_bar_volume_to_total_volume <= 0.041
        and total_volume <= 60000000
        and entry_close_strength_to_highest_high_close_strength <= 1.1
    ):
        return True

    if (
        entry_close_strength_to_highest_high_close_strength <= 0.0
        and current_day_movement_to_recent_days_movement <= 1.2851
    ):
        return True

    if (
        distance_from_last_negative_macd_bar >= 27
        and current_day_vwap_to_recent_days >= 2.7578
    ):
        return True

    if (
        current_day_ema_9_to_recent_days_ema_9 >= 3.3216
        and entry_bar_body <= 0.6921
        and recent_bars_up_trend_pct >= 0.70
    ):
        return True

    if (
        entry_volume_price_efficiency >= 0.2372
        and previous_bar_close_to_highest_high >= 0.9979
        and entry_bar_histogram_to_previous >= 2.6424
    ):
        return True

    if (
        entry_bar_volume_to_previous_bar_volume >= 15
        and entry_body_to_highest_high_body <= 1.30
        and current_day_vwap_to_recent_days >= 2.0
    ):
        return True

    if (
        clean_breakout_efficiency <= 0.32
        and highest_high_quality >= 65.56
        and entry_bar_body >= 0.867
    ):
        return True

    if (
        previous_bar_close_to_highest_high >= 0.9979
        and highest_high_to_entry_elapsed_minutes <= 2
        and entry_bar_vwap_to_ema_20 <= 0.8885
    ):
        return True

    return False

def success_patterns(
    features_data: dict[str, float]
) -> tuple[int, list[str]]:
    """
    Returns a buyer-arrival score and the matched positive behavior families.

    Important:
    - Do not use this as rescue logic.
    - Use it to protect positives when designing reject rules.
    - Use it to debug why a positive should maybe not be rejected.
    """

    score = 0
    reasons: list[str] = []

    entry_bar_close_to_highest_high = features_data["feature_entry_bar_close_to_highest_high"]
    entry_bar_histogram_to_previous = features_data["feature_entry_bar_histogram_to_previous"]
    current_day_ema_9_to_ema_20 = features_data["feature_current_day_ema_9_to_ema_20"]
    current_day_ema_9_to_recent_days_ema_9 = features_data["feature_current_day_ema_9_to_recent_days_ema_9"]
    total_volume = features_data["total_volume"]
    distance_from_last_negative_macd_bar = features_data["feature_distance_from_last_negative_macd_bar"]
    minutes_since_market_open = features_data["feature_minutes_since_market_open"]
    entry_close_position_vs_previous_close_position = features_data["feature_entry_close_position_vs_previous_close_position"]
    entry_close_strength_to_highest_high_close_strength = features_data["feature_entry_close_strength_to_highest_high_close_strength"]
    entry_extension_pressure = features_data["feature_entry_extension_pressure"]
    entry_body_to_highest_high_body = features_data["feature_entry_body_to_highest_high_body"]
    current_day_low_to_ema_9 = features_data["feature_current_day_low_to_ema_9"]
    entry_body_to_previous_bar_body = features_data["feature_entry_body_to_previous_bar_body"]
    entry_bar_histogram_to_lowest_histogram = features_data["feature_entry_bar_histogram_to_lowest_histogram"]
    entry_rejection_pressure = features_data["feature_entry_rejection_pressure"]
    entry_bar_body = features_data["feature_entry_bar_body"]
    entry_bar_volume_to_recent_bars_average = features_data["feature_entry_bar_volume_to_recent_bars_average"]
    pullback_depth_vs_pre_high_move = features_data["feature_pullback_depth_vs_pre_high_move"]
    controlled_volume_entry_quality = features_data["feature_controlled_volume_entry_quality"]
    entry_upper_wick_to_recent_upper_wick_average = features_data["feature_entry_upper_wick_to_recent_upper_wick_average"]
    entry_bar_volume_to_previous_bar_volume = features_data["feature_entry_bar_volume_to_previous_bar_volume"]
    volume_confirmation_quality = features_data["feature_volume_confirmation_quality"]
    entry_volume_price_efficiency = features_data["feature_entry_volume_price_efficiency"]
    volume_since_highest_high_to_volume_before = features_data["feature_volume_since_highest_high_to_volume_before"]
    previous_bar_close_to_highest_high = features_data["feature_previous_bar_close_to_highest_high"]
    entry_bar_volume_to_highest_volume_in_pullback = features_data["feature_entry_bar_volume_to_highest_volume_in_pullback"]
    entry_bar_ema_9_to_vwap = features_data["feature_entry_bar_ema_9_to_vwap"]
    current_day_high_to_previous_high = features_data["feature_current_day_high_to_previous_high"]
    entry_volume_spike_without_high_context = features_data["feature_entry_volume_spike_without_high_context"]
    pre_market_volume = features_data["feature_pre_market_volume"]
    reclaim_close_strength_since_highest_high = features_data["feature_reclaim_close_strength_since_highest_high"]
    entry_bar_volume_to_total_volume = features_data["feature_entry_bar_volume_to_total_volume"]
    previous_bar_high_to_highest_high = features_data["feature_previous_bar_high_to_highest_high"]
    entry_bar_low_to_ema_9 = features_data["feature_entry_bar_low_to_ema_9"]
    profit_since_open_to_bars_count_since_open = features_data["feature_profit_since_open_to_bars_count_since_open"]
    pre_market_gains = features_data["feature_pre_market_gains"]
    entry_bar_macd_to_previous = features_data["feature_entry_bar_macd_to_previous"]
    entry_close_to_previous_bar_high = features_data["feature_entry_close_to_previous_bar_high"]
    entry_bar_histogram_to_highest_histogram = features_data["feature_entry_bar_histogram_to_highest_histogram"]
    fake_reclaim_pressure = features_data["feature_fake_reclaim_pressure"]
    entry_bar_volume_to_highest_high_volume = features_data["feature_entry_bar_volume_to_highest_high_volume"]
    volume_since_lowest_low_to_entry_vs_since_highest_high = features_data["feature_volume_since_lowest_low_to_entry_vs_since_highest_high"]
    entry_bar_movement_recent_bars_average = features_data["feature_entry_bar_movement_recent_bars_average"]
    price_movement_from_highest_high_to_lowest_low = features_data["feature_price_movement_from_highest_high_to_lowest_low"]
    gains_since_lowest_low = features_data["feature_gains_since_lowest_low"]
    gains_until_entry_bar = features_data["feature_gains_until_entry_bar"]
    bars_since_highest_high_to_bars_before = features_data["feature_bars_since_highest_high_to_bars_before"]
    entry_bar_histogram_to_highest_high = features_data["feature_entry_bar_histogram_to_highest_high"]
    entry_bar_vwap_to_ema_20 = features_data["feature_entry_bar_vwap_to_ema_20"]
    volume_without_macd_confirmation = features_data["feature_volume_without_macd_confirmation"]
    histogram_changed_to_positive_direction_vs_negative_pct = features_data["feature_histogram_changed_to_positive_direction_vs_negative_pct"]
    macd_recovery_age_quality = features_data["feature_macd_recovery_age_quality"]
    entry_body_to_recent_bars_body_average = features_data["feature_entry_body_to_recent_bars_body_average"]
    reclaim_speed_from_lowest_low = features_data["feature_reclaim_speed_from_lowest_low"]
    pullback_health = features_data["feature_pullback_health"]
    highest_high_to_entry_elapsed_minutes = features_data["feature_highest_high_to_entry_elapsed_minutes"]
    previous_bar_volume_to_its_previous_volume = features_data["feature_previous_bar_volume_to_its_previous_volume"]
    current_day_high_to_recent_days_highs = features_data["feature_current_day_high_to_recent_days_highs"]
    positive_vs_negative_volume_during_pullback = features_data["feature_positive_vs_negative_volume_during_pullback"]
    highest_high_quality = features_data["feature_highest_high_quality"]
    current_day_ema_9_to_ema_20_distance_to_recent_days = features_data["feature_current_day_ema_9_to_ema_20_distance_to_recent_days"]
    emas_distances_to_recent_bars_ema_distances = features_data["feature_emas_distances_to_recent_bars_ema_distances"]
    entry_bar_volume = features_data["feature_entry_bar_volume"]
    recent_bars_positive_bars_pct = features_data["feature_recent_bars_positive_bars_pct"]
    entry_bar_open_to_ema_9 = features_data["feature_entry_bar_open_to_ema_9"]
    current_day_vwap_to_recent_days = features_data["feature_current_day_vwap_to_recent_days"]
    entry_breakout_efficiency_from_ema_9 = features_data["feature_entry_breakout_efficiency_from_ema_9"]
    recent_bars_up_trend_pct = features_data["feature_recent_bars_up_trend_pct"]
    current_day_movement_to_recent_days_movement = features_data["feature_current_day_movement_to_recent_days_movement"]
    distance_from_highest_high = features_data["feature_distance_from_highest_high"]
    entry_bar_volume_to_volume_average = features_data["feature_entry_bar_volume_to_volume_average"]
    near_high_weak_followthrough = features_data["feature_near_high_weak_followthrough"]
    uptrend_histogram_vs_downtrend_since_highest_high = features_data["feature_uptrend_histogram_vs_downtrend_since_highest_high"]
    entry_followthrough_after_near_reclaim = features_data["feature_entry_followthrough_after_near_reclaim"]
    entry_close_to_previous_bar_close = features_data["feature_entry_close_to_previous_bar_close"]
    bars_above_volume_average_vs_under_since_highest_high = features_data["feature_bars_above_volume_average_vs_under_since_highest_high"]
    clean_breakout_efficiency = features_data["feature_clean_breakout_efficiency"]
    current_day_ema_20_to_recent_days_ema_20 = features_data["feature_current_day_ema_20_to_recent_days_ema_20"]
    current_day_volume_to_recent_days_volume = features_data["feature_current_day_volume_to_recent_days_volume"]
    entry_bar_ema_9_to_ema_20 = features_data["feature_entry_bar_ema_9_to_ema_20"]
    entry_bar_lower_wick = features_data["feature_entry_bar_lower_wick"]
    entry_bar_upper_wick = features_data["feature_entry_bar_upper_wick"]
    entry_close_to_lowest_low_recovery = features_data["feature_entry_close_to_lowest_low_recovery"]
    entry_close_to_vwap = features_data["feature_entry_close_to_vwap"]
    failed_pressure_to_followthrough = features_data["feature_failed_pressure_to_followthrough"]
    lowest_low_to_entry_elapsed_minutes = features_data["feature_lowest_low_to_entry_elapsed_minutes"]
    macd_recovery_followthrough_quality = features_data["feature_macd_recovery_followthrough_quality"]

    # Success Pattern 1:
    # Clean high breakout continuation.
    if (
        entry_bar_close_to_highest_high >= 1.047401043
        and entry_bar_histogram_to_previous <= 0.9876351128
        and current_day_ema_9_to_ema_20 >= 1.047288046
        and total_volume >= 604175
    ):
        score += 1
        reasons.append("clean_high_breakout_continuation")

    # Success Pattern 2:
    # Real daily EMA expansion breakout.
    if (
        entry_bar_close_to_highest_high >= 1.047401043
        and entry_bar_histogram_to_previous <= 0.9876351128
        and current_day_ema_9_to_recent_days_ema_9 >= 1.169691864
        and total_volume >= 604175
    ):
        score += 1
        reasons.append("daily_ema_expansion_breakout")

    # Success Pattern 3:
    # Fresh early reclaim.
    if (
        distance_from_last_negative_macd_bar <= 0
        and minutes_since_market_open <= 44
        and total_volume <= 12725290.2
        and entry_close_position_vs_previous_close_position <= 2.482081959
    ):
        score += 1
        reasons.append("fresh_early_reclaim")

    # Success Pattern 4:
    # Snap close strength with low extension pressure.
    if (
        entry_close_strength_to_highest_high_close_strength >= 8.05010989
        and entry_extension_pressure <= 0.2199993956
        and entry_bar_histogram_to_previous <= 1.225417414
        and entry_body_to_highest_high_body <= 14.73302478
    ):
        score += 1
        reasons.append("snap_close_strength_low_extension")

    # Success Pattern 5:
    # Supported explosive body.
    if (
        current_day_low_to_ema_9 >= 1.119229591
        and entry_body_to_previous_bar_body >= 7.89129069
        and entry_bar_histogram_to_lowest_histogram <= 1
        and entry_rejection_pressure <= 0.2498751041
    ):
        score += 1
        reasons.append("supported_explosive_body")

    # Success Pattern 6:
    # Real reset with volume confirmation.
    if (
        entry_bar_volume_to_recent_bars_average > 1.8915035128593445
        and entry_bar_body > 0.6001200675964355
        and pullback_depth_vs_pre_high_move > 0.4464638829231262
        and controlled_volume_entry_quality > 88.66648483276367
        and entry_upper_wick_to_recent_upper_wick_average > 0.2643764615058899
        and entry_bar_volume_to_previous_bar_volume > 1.6711958050727844
        and volume_confirmation_quality > 0.3263349384069443
    ):
        score += 1
        reasons.append("real_reset_with_volume_confirmation")

    # Success Pattern 7:
    # Strong pullback-volume reclaim.
    if (
        entry_bar_volume_to_recent_bars_average > 2.4643672704696655
        and entry_volume_price_efficiency > 0.03994190879166126
        and volume_since_highest_high_to_volume_before <= 0.5249083638191223
        and previous_bar_close_to_highest_high <= 0.9887155294418335
        and entry_bar_volume_to_highest_volume_in_pullback > 1.013592779636383
        and minutes_since_market_open <= 125.0
        and entry_body_to_highest_high_body > 4.575719833374023
    ):
        score += 1
        reasons.append("strong_pullback_volume_reclaim")

    # Success Pattern 8:
    # Controlled non-chase close strength.
    if (
        entry_bar_volume_to_recent_bars_average <= 1.8915035128593445
        and entry_bar_ema_9_to_vwap <= 1.0798304677009583
        and current_day_high_to_previous_high <= 1.5273277759552002
        and entry_volume_spike_without_high_context > 0.9171657264232635
        and pre_market_volume <= 725162.5
        and entry_body_to_previous_bar_body > 0.8507025837898254
        and entry_close_strength_to_highest_high_close_strength > 1.1331384778022766
    ):
        score += 1
        reasons.append("controlled_non_chase_close_strength")

    # Success Pattern 9:
    # Supported low-float style volume ownership.
    if (
        entry_bar_volume_to_recent_bars_average <= 1.729531705379486
        and entry_bar_volume_to_total_volume > 0.0218327259644866
        and previous_bar_high_to_highest_high <= 1.0108754634857178
        and pre_market_volume > 175.0
        and total_volume <= 2451437.0
        and current_day_high_to_previous_high <= 2.3071115016937256
        and entry_close_position_vs_previous_close_position > 0.99399334192276
        and entry_bar_volume_to_recent_bars_average <= 1.6182057857513428
    ):
        score += 1
        reasons.append("supported_low_float_volume_ownership")

    # Success Pattern 10:
    # Supported body expansion from strong day structure.
    if (
        entry_bar_volume_to_recent_bars_average > 1.8915035128593445
        and entry_bar_body > 0.6001200675964355
        and pullback_depth_vs_pre_high_move > 0.4464638829231262
        and controlled_volume_entry_quality <= 88.66648483276367
        and current_day_low_to_ema_9 > 1.111901879310608
        and entry_upper_wick_to_recent_upper_wick_average <= 0.763389527797699
        and reclaim_close_strength_since_highest_high <= 0.6107226312160492
        and pre_market_volume <= 339666.0
    ):
        score += 1
        reasons.append("supported_body_expansion_from_day_structure")

    # Success Pattern 11:
    # Fresh MACD acceleration with controlled profit pace.
    # Buyers step in with volume and MACD acceleration,
    # but the move is not yet overextended from the open.
    if (
        entry_bar_volume_to_recent_bars_average > 1.729531705379486
        and entry_bar_low_to_ema_9 <= 1.0111923813819885
        and profit_since_open_to_bars_count_since_open <= 0.00812609912827611
        and pre_market_gains > 0.0056163829285651445
        and entry_bar_macd_to_previous > 1.1619797348976135
        and entry_close_position_vs_previous_close_position <= 1.4259920120239258
        and entry_upper_wick_to_recent_upper_wick_average > 0.18786534667015076
        and entry_bar_volume_to_total_volume > 0.025398355908691883
    ):
        score += 1
        reasons.append("fresh_macd_acceleration_controlled_pace")

    # Success Pattern 12:
    # Supported EMA histogram reclaim.
    # Entry is supported above EMA9, clears previous-bar high strongly,
    # histogram expansion is strong, and fake reclaim pressure is controlled.
    if (
        entry_bar_volume_to_recent_bars_average > 1.729531705379486
        and entry_bar_low_to_ema_9 > 1.0111923813819885
        and pullback_depth_vs_pre_high_move > 0.5860188007354736
        and current_day_ema_9_to_ema_20 <= 1.159429669380188
        and entry_upper_wick_to_recent_upper_wick_average <= 1.0669987797737122
        and entry_close_to_previous_bar_high > 1.0965244770050049
        and entry_bar_histogram_to_highest_histogram > 1.398955523967743
        and fake_reclaim_pressure <= 0.15265937894582748
    ):
        score += 1
        reasons.append("supported_ema_histogram_reclaim")

    # Success Pattern 13:
    # Mature reset efficiency reclaim.
    # The setup had time to reset, volume after the low rebuilt,
    # and price efficiency on the entry is strong.
    if (
        entry_bar_volume_to_recent_bars_average > 1.729531705379486
        and entry_bar_low_to_ema_9 <= 1.0111923813819885
        and profit_since_open_to_bars_count_since_open > 0.00812609912827611
        and entry_bar_volume_to_highest_high_volume <= 1.3092172741889954
        and volume_since_lowest_low_to_entry_vs_since_highest_high > 0.5118023157119751
        and minutes_since_market_open > 12.5
        and entry_volume_price_efficiency > 0.34550152719020844
    ):
        score += 1
        reasons.append("mature_reset_efficiency_reclaim")

    # Success Pattern 14:
    # Controlled weak-body reclaim.
    # The body is not large, but volume is above recent average,
    # movement from high to low was meaningful,
    # and the close-position structure stayed controlled.
    if (
        entry_bar_volume_to_recent_bars_average > 1.729531705379486
        and entry_bar_body <= 0.6001200675964355
        and previous_bar_high_to_highest_high <= 0.9952147305011749
        and controlled_volume_entry_quality <= 91.79913330078125
        and entry_close_position_vs_previous_close_position <= 2.037855386734009
        and entry_bar_movement_recent_bars_average <= 9.0991530418396
        and price_movement_from_highest_high_to_lowest_low > 0.24994999915361404
    ):
        score += 1
        reasons.append("controlled_weak_body_reclaim")

    # Success Pattern 15:
    # Premarket-supported controlled extension.
    # Premarket/gap context exists, but the entry extension remains controlled,
    # and histogram versus the highest-high remains constructive.
    if (
        entry_bar_volume_to_recent_bars_average <= 1.729531705379486
        and gains_since_lowest_low > 0.05263790301978588
        and gains_until_entry_bar <= 3.3947486877441406
        and bars_since_highest_high_to_bars_before > 0.007808145135641098
        and entry_bar_histogram_to_highest_high > 0.9913771152496338
        and entry_extension_pressure <= 0.4007411450147629
        and current_day_ema_9_to_ema_20 > 1.0398948788642883
        and pre_market_gains > 0.06045127287507057
    ):
        score += 1
        reasons.append("premarket_supported_controlled_extension")

    # Success Pattern 16:
    # Broad reset with buyer volume confirmation.
    # The setup had a real pullback/reset, the entry body is meaningful,
    # volume expands versus recent bars, and the entry volume beats the previous bar.
    if (
        entry_bar_volume_to_recent_bars_average > 1.8915035128593445
        and entry_bar_body > 0.6001200675964355
        and pullback_depth_vs_pre_high_move > 0.4464638829231262
        and controlled_volume_entry_quality > 88.66648483276367
        and entry_upper_wick_to_recent_upper_wick_average > 0.2643764615058899
        and entry_bar_volume_to_previous_bar_volume > 1.6711958050727844
    ):
        score += 1
        reasons.append("broad_reset_buyer_volume_confirmation")

    # Success Pattern 17:
    # Broad reset efficiency reclaim.
    # After a real reset, the entry shows body/volume participation
    # and beats the highest pullback volume enough to show buyer control.
    if (
        entry_bar_volume_to_recent_bars_average > 1.8915035128593445
        and entry_bar_body > 0.6001200675964355
        and pullback_depth_vs_pre_high_move > 0.48088546097278595
        and controlled_volume_entry_quality > 88.66648483276367
        and entry_bar_volume_to_highest_volume_in_pullback > 1.271771490573883
    ):
        score += 1
        reasons.append("broad_reset_efficiency_reclaim")

    # Success Pattern 18:
    # Fresh supported reclaim before MACD gets stale.
    # The entry happens early/fresh, MACD has not been positive for long,
    # and price is still structurally supported above EMA20/VWAP.
    if (
        distance_from_last_negative_macd_bar <= 0
        and minutes_since_market_open <= 39
        and entry_bar_vwap_to_ema_20 > 0.953998
    ):
        score += 1
        reasons.append("fresh_supported_reclaim_before_macd_stale")

    # Success Pattern 19:
    # Fresh supported volume reclaim without chase.
    # The setup is still fresh, not too extended over previous-bar high,
    # and volume/MACD confirmation is strong enough to show real demand.
    if (
        entry_bar_vwap_to_ema_20 > 0.969909
        and entry_close_to_previous_bar_high <= 1.064691
        and distance_from_last_negative_macd_bar <= 4
        and volume_without_macd_confirmation > 1.333612
    ):
        score += 1
        reasons.append("fresh_supported_volume_reclaim_no_chase")

    # Success Pattern 20:
    # Controlled snap reclaim.
    # Buyers step in with strong close strength,
    # but the entry is not an overextended chase.
    if (
        entry_close_strength_to_highest_high_close_strength >= 4.30
        and entry_bar_histogram_to_previous <= 0.56
        and entry_extension_pressure <= 0.262
        and entry_bar_macd_to_previous >= 0.30
        and entry_bar_volume_to_recent_bars_average >= 2.0
    ):
        score += 1
        reasons.append("controlled_snap_reclaim")

    # Success Pattern 21:
    # Supported day volume rotation.
    # The current day is well-supported above EMA9,
    # histogram direction is positive,
    # and buyers rotate volume into the entry bar.
    if (
        current_day_low_to_ema_9 >= 1.12186123895
        and histogram_changed_to_positive_direction_vs_negative_pct >= 1.2125
        and entry_bar_volume_to_previous_bar_volume >= 2.32971107929
        and entry_bar_volume_to_recent_bars_average >= 2.41328487682
        and entry_bar_volume_to_total_volume >= 0.015
    ):
        score += 1
        reasons.append("supported_day_volume_rotation")

    # Success Pattern 22:
    # Extreme daily expansion fresh body surge.
    # Current-day EMA9 is extremely expanded versus recent days,
    # MACD recovery is still fresh, and the entry body is much stronger than recent bars.
    if (
        current_day_ema_9_to_recent_days_ema_9 > 2.275308112629929
        and macd_recovery_age_quality <= 5.956758668893252
        and entry_body_to_recent_bars_body_average > 3.6966142941910953
    ):
        score += 1
        reasons.append("extreme_daily_expansion_fresh_body_surge")

    # Success Pattern 23:
    # Quiet open controlled body reclaim.
    # The move from the open is still quiet,
    # but the entry body is much stronger than the highest-high body,
    # and reclaim speed is controlled rather than a chase.
    if (
        profit_since_open_to_bars_count_since_open <= 0.0011123761300984101
        and entry_body_to_highest_high_body > 5.93333333333328
        and reclaim_speed_from_lowest_low <= 0.6875694444444458
    ):
        score += 1
        reasons.append("quiet_open_controlled_body_reclaim")

    # Success Pattern 24:
    # Delayed volume rebuild with controlled histogram.
    # The move from the open is still quiet,
    # enough volume has rebuilt after the highest-high,
    # and histogram is controlled rather than overextended.
    if (
        profit_since_open_to_bars_count_since_open <= 0.0011123761300984101
        and volume_since_highest_high_to_volume_before > 0.13026786204894306
        and entry_bar_histogram_to_highest_histogram <= 0.9568272235385898
    ):
        score += 1
        reasons.append("delayed_volume_rebuild_controlled_histogram")

    # Success Pattern 25:
    # Delayed pullback volume spike.
    # Enough time passed after the highest-high,
    # pullback health is strong,
    # and the entry shows a strong volume spike without being just a near-high chase.
    if (
        entry_volume_spike_without_high_context > 6.083272046377
        and pullback_health > 4.523913100916
        and highest_high_to_entry_elapsed_minutes > 21.0
    ):
        score += 1
        reasons.append("delayed_pullback_volume_spike")

    # Success Pattern 26:
    # Previous-volume spike body expansion, not VWAP chase.
    # The previous bar already showed volume ignition,
    # the entry body expands strongly versus recent bars,
    # and the entry is not overly stretched above VWAP.
    if (
        previous_bar_volume_to_its_previous_volume > 2.940825425613
        and entry_bar_ema_9_to_vwap <= 1.054934240024
        and entry_body_to_recent_bars_body_average > 4.905669490266
    ):
        score += 1
        reasons.append("previous_volume_spike_body_expansion_not_vwap_chase")

    # Success Pattern 27:
    # Pullback volume dominance with body expansion.
    # The entry volume dominates the pullback volume,
    # previous bar is still below the high,
    # and the entry body expands strongly versus recent bars.
    if (
        entry_bar_volume_to_highest_volume_in_pullback > 3.830134920395
        and previous_bar_high_to_highest_high <= 0.980774337661
        and entry_body_to_recent_bars_body_average > 4.050921052632
    ):
        score += 1
        reasons.append("pullback_volume_dominance_body_expansion")

    # Success Pattern 28:
    # Late body continuation in non-extreme daily context.
    # The setup is later after the highest-high,
    # but the day is not excessively stretched versus recent highs,
    # and the entry body is meaningful.
    if (
        highest_high_to_entry_elapsed_minutes > 131.0
        and current_day_high_to_recent_days_highs <= 1.430637402494
        and entry_bar_body > 0.80619589516
    ):
        score += 1
        reasons.append("late_body_continuation_non_extreme_daily_context")

    # Success Pattern 29:
    # Refined broad supported base reclaim.
    # Buyers are recovering from the pullback with positive-volume dominance,
    # controlled rejection pressure, non-extreme daily EMA expansion,
    # and a real entry body.
    if (
        positive_vs_negative_volume_during_pullback >= 0.767725
        and highest_high_quality <= 1.307631
        and entry_rejection_pressure <= 0.270846
        and current_day_ema_9_to_recent_days_ema_9 <= 1.266073
        and volume_since_lowest_low_to_entry_vs_since_highest_high <= 0.643274
        and entry_bar_body > 0.806196
    ):
        score += 1
        reasons.append("refined_broad_supported_base_reclaim")

    # Success Pattern 30:
    # Supported volume ownership above EMA9.
    # Buyers own a meaningful part of the day volume,
    # entry is supported above EMA9,
    # body is real, and wick/EMA-distance pressure is controlled.
    if (
        entry_bar_volume_to_recent_bars_average > 1.924173593521
        and entry_bar_body > 0.600120067596
        and entry_bar_low_to_ema_9 > 1.010593
        and entry_bar_volume_to_total_volume > 0.11214
        and current_day_ema_9_to_ema_20_distance_to_recent_days <= 1.410308
        and emas_distances_to_recent_bars_ema_distances <= 0.2497
        and entry_upper_wick_to_recent_upper_wick_average <= 1.0
    ):
        score += 1
        reasons.append("supported_volume_ownership_above_ema9")

    # Untagged Positive Pattern:
    # Near-high body/volume reclaim.
    # Covers: 31 positives / 0 FP
    # Includes: 26 currently untagged positives, 5 already-tagged positives
    if (
        near_high_weak_followthrough <= 0.960273236
        and current_day_ema_9_to_ema_20_distance_to_recent_days <= 1.348466456
        and controlled_volume_entry_quality > 0.8305397928
        and entry_close_to_previous_bar_high <= 1.044427335
        and entry_body_to_previous_bar_body > 0.7977560461
        and gains_since_lowest_low <= 0.1519492269
        and profit_since_open_to_bars_count_since_open > 0.002028054791
        and entry_bar_volume_to_highest_volume_in_pullback > 0.7476072311
    ):
        score += 1
        reasons.append("untagged_near_high_body_volume_reclaim")

    # Untagged Positive Pattern:
    # Delayed pullback base reclaim with quiet prior-volume behavior.
    # Covers: 14 positives / 0 FP
    # Includes: 14 currently untagged positives
    if (
        pullback_health <= 0.9453305304
        and minutes_since_market_open > 96.5
        and current_day_low_to_ema_9 <= 1.106336474
        and entry_bar_body > 0.8096311688
        and entry_bar_open_to_ema_9 <= 1.008332789
        and previous_bar_volume_to_its_previous_volume <= 0.5910618901
        and pullback_depth_vs_pre_high_move > 0.5377934277
        and gains_since_lowest_low <= 0.220812723
    ):
        score += 1
        reasons.append("untagged_delayed_pullback_base_reclaim")

    # Untagged Positive Pattern:
    # Controlled extension reclaim.
    # Covers: 14 positives / 0 FP
    # Includes: 14 currently untagged positives
    if (
        macd_recovery_age_quality > 1.028459311
        and entry_volume_spike_without_high_context <= 1.636733711
        and entry_bar_close_to_highest_high > 1.019910216
        and entry_bar_open_to_ema_9 > 1.008179486
        and entry_extension_pressure <= 0.2962066829
        and entry_extension_pressure > 0.2425897047
        and previous_bar_volume_to_its_previous_volume > 0.430446744
        and uptrend_histogram_vs_downtrend_since_highest_high <= 0.3390804678
    ):
        score += 1
        reasons.append("untagged_controlled_extension_reclaim")

    # Untagged Positive Pattern:
    # Compact volume-followthrough reclaim.
    # Covers: 14 positives / 0 FP
    # Includes: 14 currently untagged positives
    if (
        volume_without_macd_confirmation > 1.497488439
        and entry_followthrough_after_near_reclaim > 1.023718357
        and gains_until_entry_bar > 0.4142454565
        and entry_bar_open_to_ema_9 <= 1.008332789
        and price_movement_from_highest_high_to_lowest_low <= 0.1289499998
        and entry_upper_wick_to_recent_upper_wick_average > 0.1980083734
        and volume_since_highest_high_to_volume_before > 0.001002329387
        and entry_bar_histogram_to_lowest_histogram <= 1.53204447
    ):
        score += 1
        reasons.append("untagged_compact_volume_followthrough_reclaim")

    # Untagged Positive Pattern:
    # Low-positive-bars volume reclaim.
    # Covers: 12 positives / 0 FP
    # Includes: 12 currently untagged positives
    if (
        current_day_low_to_ema_9 <= 1.106336474
        and entry_bar_open_to_ema_9 <= 1.008179486
        and entry_close_to_previous_bar_close <= 1.115805089
        and recent_bars_positive_bars_pct <= 0.450000003
        and entry_bar_volume_to_recent_bars_average > 1.807909131
        and entry_bar_volume_to_previous_bar_volume <= 2.797281384
        and entry_bar_volume_to_previous_bar_volume > 1.816251576
    ):
        score += 1
        reasons.append("untagged_low_positive_bars_volume_reclaim")

    # Untagged Positive Pattern:
    # VWAP body-compression reclaim.
    # Covers: 12 positives / 0 FP
    # Includes: 12 currently untagged positives
    if (
        current_day_vwap_to_recent_days <= 1.545367122
        and entry_bar_low_to_ema_9 > 0.9870319068
        and entry_bar_open_to_ema_9 <= 1.006395698
        and entry_body_to_recent_bars_body_average > 3.406441331
        and entry_body_to_previous_bar_body <= 3.957191467
        and entry_close_position_vs_previous_close_position > 0.9390972555
        and entry_bar_volume_to_previous_bar_volume <= 3.406533241
        and entry_bar_volume_to_previous_bar_volume > 1.836494625
    ):
        score += 1
        reasons.append("untagged_vwap_body_compression_reclaim")

    # Untagged Positive Pattern:
    # Clean rejection-pressure volume reclaim.
    # Covers: 17 positives / 0 FP
    # Includes: 14 currently untagged positives, 3 already-tagged positives
    if (
        entry_rejection_pressure <= 0.01129987789
        and near_high_weak_followthrough > 0.8779112101
        and current_day_low_to_ema_9 <= 1.106336474
        and entry_bar_low_to_ema_9 > 0.9958772957
        and entry_bar_open_to_ema_9 <= 1.008179486
        and entry_close_position_vs_previous_close_position <= 3.152427435
        and entry_bar_volume_to_recent_bars_average > 1.799983323
        and entry_bar_volume_to_previous_bar_volume <= 3.564065337
    ):
        score += 1
        reasons.append("untagged_clean_rejection_volume_reclaim")

    # Safe Positive Variant 1:
    # Broad reset-volume confirmation where low-to-entry volume stays controlled
    # versus the post-high volume, and entry volume is meaningful.
    # Covers: 65 positives / 0 FP
    if (
        "reset_volume_confirmation" in reasons
        and volume_since_lowest_low_to_entry_vs_since_highest_high <= 0.770058
        and entry_bar_volume > 84684.6
    ):
        score += 1
        reasons.append("safe_reset_volume_confirmation_volume_balance")

    # Safe Positive Variant 2:
    # Close-strength non-chase where recent bars are not too one-sided
    # and entry opens above EMA9 support.
    # Covers: 49 positives / 0 FP
    if (
        "close_strength_non_chase" in reasons
        and recent_bars_positive_bars_pct <= 0.7
        and entry_bar_open_to_ema_9 > 1.000809
    ):
        score += 1
        reasons.append("safe_close_strength_non_chase_base")

    # Safe Positive Variant 3:
    # Broad reset buyer-volume case with controlled daily VWAP expansion,
    # no excessive entry-volume spike, and enough wick/participation.
    # Covers: 38 positives / 0 FP
    if (
        "broad_reset_buyer_volume" in reasons
        and current_day_vwap_to_recent_days <= 1.979262
        and entry_volume_spike_without_high_context <= 2.574231
        and entry_upper_wick_to_recent_upper_wick_average > 0.240062
    ):
        score += 1
        reasons.append("safe_broad_reset_clean_volume")

    # Safe Positive Variant 4:
    # Breakout expansion that is not histogram-overextended
    # and still occurs inside a reasonable market-open window.
    # Covers: 32 positives / 0 FP
    if (
        "breakout_expansion" in reasons
        and entry_bar_histogram_to_lowest_histogram <= 2.438529
        and minutes_since_market_open <= 314.0
    ):
        score += 1
        reasons.append("safe_breakout_expansion_histogram_time")

    # Safe Positive Variant 5:
    # Fresh supported volume reclaim with real body expansion,
    # previous bar still near the highest high, and no oversized entry-volume chase.
    # Covers: 30 positives / 0 FP
    if (
        "fresh_supported_volume_reclaim" in reasons
        and entry_bar_body > 0.507875
        and previous_bar_high_to_highest_high > 0.961338
        and entry_bar_volume <= 879005.6
    ):
        score += 1
        reasons.append("safe_fresh_supported_volume_reclaim_body")

    # Safe Positive Variant 6:
    # Refined supported base reclaim with controlled breakout efficiency,
    # some profit-per-bar expansion, and healthy pullback structure.
    # Covers: 29 positives / 0 FP
    if (
        "refined_broad_supported_base_reclaim" in reasons
        and entry_breakout_efficiency_from_ema_9 <= 0.891129
        and profit_since_open_to_bars_count_since_open > 0.000791
        and pullback_health > 0.659266
    ):
        score += 1
        reasons.append("safe_refined_supported_base_reclaim")

    # Safe Positive Variant 7:
    # Fresh timing case with controlled entry movement,
    # enough recent upward participation, and strong close-position followthrough.
    # Covers: 28 positives / 0 FP
    if (
        "fresh_timing" in reasons
        and entry_bar_movement_recent_bars_average <= 5.811589
        and recent_bars_up_trend_pct > 0.35
        and entry_close_position_vs_previous_close_position > 0.936711
    ):
        score += 1
        reasons.append("safe_fresh_timing_close_followthrough")

    # Safe Positive Variant 8:
    # Explosive body support where reclaim close-strength is not too stretched,
    # MACD recovery is still fresh, and EMA9 breakout efficiency stays controlled.
    # Covers: 28 positives / 0 FP
    if (
        "explosive_body_support" in reasons
        and reclaim_close_strength_since_highest_high <= 0.729485
        and macd_recovery_age_quality <= 12.539876
        and entry_breakout_efficiency_from_ema_9 <= 0.834276
    ):
        score += 1
        reasons.append("safe_explosive_body_controlled_macd")

    # Safe Positive Variant:
    # Real reset with volume confirmation, but without extreme total-liquidity expansion.
    # Covers: 41 positives / 0 FP
    if (
        "real_reset_with_volume_confirmation" in reasons
        and total_volume <= 62889928.8
    ):
        score += 1
        reasons.append("safe_real_reset_volume_confirmation_liquidity_control")

    # Safe Positive Variant:
    # Broad reset buyer-volume confirmation with clean expansion.
    # Keeps the buyer-volume reset but removes the overextended daily-movement cases.
    # Covers: 38 positives / 0 FP
    if (
        "broad_reset_buyer_volume_confirmation" in reasons
        and entry_volume_spike_without_high_context <= 3.08358017
        and current_day_movement_to_recent_days_movement <= 18.6383137
    ):
        score += 1
        reasons.append("safe_broad_reset_buyer_volume_confirmation_clean_expansion")

    # Safe Positive Variant:
    # Fresh MACD acceleration where entry volume is a meaningful part of total volume.
    # Covers: 33 positives / 0 FP
    if (
        "fresh_macd_acceleration_controlled_pace" in reasons
        and entry_bar_volume_to_total_volume > 0.0127641446
    ):
        score += 1
        reasons.append("safe_fresh_macd_acceleration_volume_participation")

    # Safe Positive Variant:
    # Strong pullback volume reclaim, but only after real distance from the high
    # and without a previous-volume blowoff.
    # Covers: 33 positives / 0 FP
    if (
        "strong_pullback_volume_reclaim" in reasons
        and previous_bar_volume_to_its_previous_volume <= 1.77033687
        and distance_from_highest_high > 2
    ):
        score += 1
        reasons.append("safe_strong_pullback_volume_reclaim_after_distance")

    # Safe Positive Variant:
    # Clean high breakout continuation with controlled histogram extension.
    # Covers: 31 positives / 0 FP
    if (
        "clean_high_breakout_continuation" in reasons
        and entry_volume_price_efficiency <= 1.60443805
        and entry_bar_histogram_to_lowest_histogram <= 2.43852923
    ):
        score += 1
        reasons.append("safe_clean_high_breakout_histogram_control")

    # Safe Positive Variant:
    # Supported base reclaim where highest-high quality is low enough
    # to avoid the more dangerous extension/chase cases.
    # Covers: 29 positives / 0 FP
    if (
        "safe_refined_supported_base_reclaim" in reasons
        and highest_high_quality <= 1.33356595
    ):
        score += 1
        reasons.append("safe_supported_base_reclaim_low_high_quality")

    # Safe Positive Variant:
    # Controlled non-chase close-strength with clean pullback movement
    # and no extreme premarket stretch.
    # Covers: 26 positives / 0 FP
    if (
        "controlled_non_chase_close_strength" in reasons
        and price_movement_from_highest_high_to_lowest_low <= 0.92
        and pre_market_gains <= 0.0875621891
    ):
        score += 1
        reasons.append("safe_controlled_non_chase_close_strength_clean_pullback")

    # Safe Positive Variant:
    # Real reset with controlled rejection pressure and acceptable EMA9 daily context.
    # Covers: 45 positives / 0 FP
    if (
        "real_reset_with_volume_confirmation" in reasons
        and entry_rejection_pressure <= 0.4971486222
        and current_day_ema_9_to_recent_days_ema_9 <= 1.527511594
    ):
        score += 1
        reasons.append("safe_real_reset_rejection_ema_context")

    # Safe Positive Variant:
    # Broad reset buyer-volume confirmation with controlled entry spike and liquidity.
    # Covers: 41 positives / 0 FP
    if (
        "broad_reset_buyer_volume_confirmation" in reasons
        and entry_volume_spike_without_high_context <= 2.814302399
        and total_volume <= 74729905.95
    ):
        score += 1
        reasons.append("safe_broad_reset_buyer_clean_liquidity")

    # Safe Positive Variant:
    # Strong pullback reclaim without previous-bar blowoff and without extreme body expansion.
    # Covers: 37 positives / 0 FP
    if (
        "strong_pullback_volume_reclaim" in reasons
        and previous_bar_volume_to_its_previous_volume <= 2.126178413
        and entry_body_to_recent_bars_body_average <= 13.59989672
    ):
        score += 1
        reasons.append("safe_strong_pullback_no_prior_blowoff")

    # Safe Positive Variant:
    # Clean high breakout where close-strength is real and recent bars still show participation.
    # Covers: 35 positives / 0 FP
    if (
        "clean_high_breakout_continuation" in reasons
        and entry_close_strength_to_highest_high_close_strength > 0.5433462246
        and recent_bars_positive_bars_pct > 0.4
    ):
        score += 1
        reasons.append("safe_clean_high_close_strength_continuation")

    # Safe Positive Variant:
    # Daily EMA expansion breakout with efficient volume/price behavior and participation.
    # Covers: 32 positives / 0 FP
    if (
        "daily_ema_expansion_breakout" in reasons
        and entry_volume_price_efficiency <= 1.495320283
        and recent_bars_positive_bars_pct > 0.4
    ):
        score += 1
        reasons.append("safe_daily_ema_expansion_efficient_participation")

    # Safe Positive Variant:
    # Broad reset efficiency reclaim with low-to-entry volume balance and some premarket strength.
    # Covers: 32 positives / 0 FP
    if (
        "broad_reset_efficiency_reclaim" in reasons
        and volume_since_lowest_low_to_entry_vs_since_highest_high <= 0.801966641
        and pre_market_gains > 0.01146131805
    ):
        score += 1
        reasons.append("safe_broad_reset_efficiency_premarket_volume_balance")

    # Safe Positive Variant:
    # Controlled non-chase close-strength with VWAP/day context under control.
    # Covers: 29 positives / 0 FP
    if (
        "controlled_non_chase_close_strength" in reasons
        and current_day_vwap_to_recent_days <= 2.016561739
        and entry_bar_open_to_ema_9 > 0.9984208946
    ):
        score += 1
        reasons.append("safe_controlled_non_chase_vwap_base")

    # Safe Positive Variant:
    # Fresh supported volume reclaim where previous bar remains near high context.
    # Covers: 29 positives / 0 FP
    if (
        "fresh_supported_volume_reclaim_no_chase" in reasons
        and previous_bar_high_to_highest_high > 0.9569656773
        and current_day_low_to_ema_9 > 0.836463179
    ):
        score += 1
        reasons.append("safe_fresh_supported_near_high_base")

    # Safe Positive Variant:
    # Snap close-strength with meaningful entry volume versus highest-high volume.
    # Covers: 28 positives / 0 FP
    if (
        "snap_close_strength_low_extension" in reasons
        and recent_bars_positive_bars_pct <= 0.7
        and entry_bar_volume_to_highest_high_volume > 0.7509705684
    ):
        score += 1
        reasons.append("safe_snap_close_strength_volume_confirmation")

    # Safe Positive Variant:
    # Supported body expansion from day structure with clean participation.
    # Covers: 28 positives / 0 FP
    if (
        "supported_body_expansion_from_day_structure" in reasons
        and entry_volume_spike_without_high_context <= 4.070191289
        and recent_bars_positive_bars_pct <= 0.7
    ):
        score += 1
        reasons.append("safe_supported_body_day_structure_clean_participation")

    # Safe Positive Variant:
    # Fresh reclaim before MACD stale with controlled body expansion and close followthrough.
    # Covers: 27 positives / 0 FP
    if (
        "fresh_supported_reclaim_before_macd_stale" in reasons
        and entry_body_to_recent_bars_body_average <= 5.953984864
        and entry_close_position_vs_previous_close_position > 0.858351
    ):
        score += 1
        reasons.append("safe_fresh_reclaim_macd_close_followthrough")

    # Safe Positive Variant:
    # Refined base reclaim with controlled EMA9 breakout efficiency and volume-average behavior.
    # Covers: 26 positives / 0 FP
    if (
        "refined_broad_supported_base_reclaim" in reasons
        and entry_breakout_efficiency_from_ema_9 <= 0.8129578009
        and entry_bar_volume_to_volume_average <= 7.39324826
    ):
        score += 1
        reasons.append("safe_refined_base_reclaim_efficiency_volume_control")

    # Mined Feature-Only Positive Pattern:
    # mined_broad_distance_body_macd_reclaim
    # Covers: 32 positives / 0 FP
    # Includes: 12 currently untagged positives, 20 already-tagged positives
    # Conditions: 16
    if (
        current_day_volume_to_recent_days_volume <= 1103.55899
        and distance_from_highest_high > 4.5
        and emas_distances_to_recent_bars_ema_distances > 0.1017406285
        and entry_bar_body > 0.5407562554
        and entry_bar_body <= 0.9875641167
        and entry_bar_histogram_to_lowest_histogram <= 2.350764155
        and entry_bar_lower_wick <= 0.1653926373
        and entry_bar_macd_to_previous > 0.5137349814
        and entry_bar_movement_recent_bars_average > 4.379752636
        and entry_close_strength_to_highest_high_close_strength <= 5.48837018
        and entry_close_to_previous_bar_close > 1.069625795
        and entry_close_to_previous_bar_high <= 1.20044136
        and macd_recovery_followthrough_quality <= 36.72091484
        and minutes_since_market_open > 12.5
        and price_movement_from_highest_high_to_lowest_low > 0.3549499959
        and reclaim_speed_from_lowest_low > 0.09627187625
    ):
        score += 1
        reasons.append("mined_broad_distance_body_macd_reclaim")

    # Mined Feature-Only Positive Pattern:
    # mined_broad_daily_ema_distance_clean_reclaim
    # Covers: 33 positives / 0 FP
    # Includes: 4 currently untagged positives, 29 already-tagged positives
    # Conditions: 17
    if (
        current_day_ema_9_to_ema_20_distance_to_recent_days > 3.230713725
        and current_day_movement_to_recent_days_movement > 1.175007463
        and emas_distances_to_recent_bars_ema_distances > 0.0807254687
        and entry_bar_ema_9_to_vwap <= 1.296068549
        and entry_bar_low_to_ema_9 > 0.98511976
        and entry_bar_lower_wick <= 0.2738636434
        and entry_bar_upper_wick <= 0.2641544789
        and entry_bar_volume_to_previous_bar_volume > 1.154551983
        and entry_bar_volume_to_recent_bars_average > 1.799685419
        and entry_bar_vwap_to_ema_20 <= 1.021435022
        and entry_body_to_previous_bar_body <= 58
        and entry_close_strength_to_highest_high_close_strength <= 3.271921515
        and entry_extension_pressure <= 0.650565505
        and entry_rejection_pressure <= 0.2157036513
        and entry_volume_price_efficiency > 0.0350418631
        and pre_market_gains <= 0.06031775661
        and price_movement_from_highest_high_to_lowest_low > 0.05749999918
    ):
        score += 1
        reasons.append("mined_broad_daily_ema_distance_clean_reclaim")

    # Mined Feature-Only Positive Pattern:
    # mined_broad_volume_controlled_histogram_reclaim
    # Covers: 24 positives / 0 FP
    # Includes: 7 currently untagged positives, 17 already-tagged positives
    # Conditions: 16
    if (
        current_day_high_to_previous_high <= 2.46967268
        and entry_bar_histogram_to_previous <= 1.709322274
        and entry_bar_low_to_ema_9 > 0.9854449034
        and entry_bar_volume <= 972500
        and entry_body_to_highest_high_body > 0.6324675381
        and entry_body_to_previous_bar_body > 0.9956383705
        and entry_body_to_recent_bars_body_average > 1.353095055
        and entry_rejection_pressure <= 0.7701000273
        and entry_volume_spike_without_high_context > 1.034627497
        and macd_recovery_age_quality <= 33.87496567
        and macd_recovery_followthrough_quality > 17.47827625
        and minutes_since_market_open > 16
        and near_high_weak_followthrough > 0.6956980228
        and price_movement_from_highest_high_to_lowest_low <= 0.6523499787
        and profit_since_open_to_bars_count_since_open <= 0.04048698023
        and volume_since_highest_high_to_volume_before > 0.04197785445
    ):
        score += 1
        reasons.append("mined_broad_volume_controlled_histogram_reclaim")

    # Mined Feature-Only Positive Pattern:
    # mined_broad_volume_pullback_followthrough_reclaim
    # Covers: 25 positives / 0 FP
    # Includes: 6 currently untagged positives, 19 already-tagged positives
    # Conditions: 16
    if (
        bars_above_volume_average_vs_under_since_highest_high <= 0.9204545617
        and bars_since_highest_high_to_bars_before > 0.03110119049
        and bars_since_highest_high_to_bars_before <= 1.154176414
        and entry_bar_ema_9_to_ema_20 <= 1.050940275
        and entry_bar_macd_to_previous <= 0.8789401948
        and entry_bar_movement_recent_bars_average <= 7.791760683
        and entry_bar_open_to_ema_9 <= 1.016707778
        and entry_body_to_recent_bars_body_average > 1.353095055
        and entry_followthrough_after_near_reclaim > 1.049783051
        and gains_since_lowest_low > 0.07910162956
        and histogram_changed_to_positive_direction_vs_negative_pct <= 1.083916128
        and macd_recovery_age_quality <= 18.64052391
        and previous_bar_close_to_highest_high <= 1.002683759
        and reclaim_speed_from_lowest_low <= 2.580357194
        and uptrend_histogram_vs_downtrend_since_highest_high > 0.169507578
        and volume_confirmation_quality > 0.1467424929
    ):
        score += 1
        reasons.append("mined_broad_volume_pullback_followthrough_reclaim")

    # Mined Feature-Only Positive Pattern:
    # mined_broad_vwap_near_high_reclaim
    # Covers: 29 positives / 0 FP
    # Includes: 5 currently untagged positives, 24 already-tagged positives
    # Conditions: 17
    if (
        current_day_ema_20_to_recent_days_ema_20 > 0.957154423
        and current_day_vwap_to_recent_days <= 2.003365695
        and entry_bar_low_to_ema_9 <= 1.003329992
        and entry_bar_lower_wick <= 0.3341038525
        and entry_bar_volume_to_previous_bar_volume > 0.9832480252
        and entry_body_to_previous_bar_body <= 44.33333397
        and entry_close_position_vs_previous_close_position <= 5.702798128
        and entry_close_strength_to_highest_high_close_strength <= 4.174242496
        and entry_close_to_vwap <= 1.175489843
        and entry_followthrough_after_near_reclaim > 1.064789534
        and entry_rejection_pressure <= 0.503287673
        and gains_since_lowest_low <= 0.1097233295
        and gains_until_entry_bar > 0.08884497359
        and highest_high_to_entry_elapsed_minutes <= 6.5
        and minutes_since_market_open <= 236.5
        and pre_market_gains <= 0.1151857935
        and previous_bar_high_to_highest_high > 0.9713801146
    ):
        score += 1
        reasons.append("mined_broad_vwap_near_high_reclaim")

    # Mined Feature-Only Positive Pattern:
    # mined_broad_clean_breakout_low_extension_reclaim
    # Covers: 25 positives / 0 FP
    # Includes: 5 currently untagged positives, 20 already-tagged positives
    # Conditions: 16
    if (
        clean_breakout_efficiency > 0.9007738363
        and current_day_volume_to_recent_days_volume <= 249.5097034
        and entry_bar_body > 0.2449956579
        and entry_bar_low_to_ema_9 > 0.9860114588
        and entry_bar_open_to_ema_9 <= 1.002428166
        and entry_close_to_previous_bar_high <= 1.199881299
        and entry_extension_pressure <= 0.3690450781
        and failed_pressure_to_followthrough <= 0.4338370434
        and lowest_low_to_entry_elapsed_minutes <= 327.132818
        and macd_recovery_age_quality <= 60.99647227
        and near_high_weak_followthrough > 0.5921348188
        and previous_bar_high_to_highest_high > 0.8516965427
        and previous_bar_high_to_highest_high <= 0.9876069991
        and pullback_health <= 21.28503248
        and reclaim_speed_from_lowest_low <= 0.5354329004
        and uptrend_histogram_vs_downtrend_since_highest_high <= 1.180022583
    ):
        score += 1
        reasons.append("mined_broad_clean_breakout_low_extension_reclaim")

    # Mined Feature-Only Positive Pattern:
    # mined_broad_daily_ema20_pullback_volume_reclaim
    # Covers: 24 positives / 0 FP
    # Includes: 3 currently untagged positives, 21 already-tagged positives
    # Conditions: 12
    if (
        current_day_ema_20_to_recent_days_ema_20 > 1.20306015
        and current_day_movement_to_recent_days_movement <= 2.683113694
        and distance_from_highest_high > 3.5
        and entry_bar_lower_wick <= 0.2582051307
        and entry_bar_volume > 50127.69922
        and entry_bar_volume_to_volume_average > 1.68495214
        and entry_followthrough_after_near_reclaim <= 1.245562553
        and entry_rejection_pressure <= 0.9439071715
        and minutes_since_market_open <= 224.5
        and price_movement_from_highest_high_to_lowest_low > 0.3450000137
        and pullback_depth_vs_pre_high_move <= 1.832362473
        and pullback_health > 0.5647868365
    ):
        score += 1
        reasons.append("mined_broad_daily_ema20_pullback_volume_reclaim")

    # Mined Feature-Only Positive Pattern:
    # mined_broad_macd_body_followthrough_reclaim
    # Covers: 22 positives / 0 FP
    # Includes: 4 currently untagged positives, 18 already-tagged positives
    # Conditions: 12
    if (
        entry_bar_macd_to_previous > 0.1987970918
        and entry_bar_movement_recent_bars_average > 4.328333378
        and entry_body_to_highest_high_body > 0.8069075644
        and entry_close_position_vs_previous_close_position > 0.9121666551
        and entry_close_position_vs_previous_close_position <= 3.385722995
        and entry_close_to_previous_bar_close <= 1.069153547
        and entry_close_to_previous_bar_high <= 1.06344974
        and entry_extension_pressure > 0.1087492928
        and entry_extension_pressure <= 0.2566989362
        and highest_high_quality <= 5.118121624
        and positive_vs_negative_volume_during_pullback > 0.9160264134
        and pullback_depth_vs_pre_high_move > 0.4379407912
    ):
        score += 1
        reasons.append("mined_broad_macd_body_followthrough_reclaim")

    # Mined Feature-Only Positive Pattern:
    # mined_broad_high_volume_pullback_depth_reclaim
    # Covers: 20 positives / 0 FP
    # Includes: 5 currently untagged positives, 15 already-tagged positives
    # Conditions: 10
    if (
        current_day_low_to_ema_9 > 0.4760414362
        and entry_bar_close_to_highest_high > 1.023502707
        and entry_bar_volume > 180632.0781
        and entry_bar_volume_to_recent_bars_average > 1.105450094
        and macd_recovery_followthrough_quality <= 33.15610123
        and minutes_since_market_open > 43.5
        and near_high_weak_followthrough <= 0.7820093036
        and previous_bar_close_to_highest_high <= 0.9897916019
        and profit_since_open_to_bars_count_since_open > 0.008917489089
        and pullback_depth_vs_pre_high_move > 0.4489547014
    ):
        score += 1
        reasons.append("mined_broad_high_volume_pullback_depth_reclaim")

    # Mined Feature-Only Positive Pattern:
    # mined_broad_ema_distance_low_reclaim
    # Covers: 20 positives / 0 FP
    # Includes: 4 currently untagged positives, 16 already-tagged positives
    # Conditions: 12
    if (
        current_day_ema_9_to_ema_20_distance_to_recent_days > 4.735637903
        and current_day_low_to_ema_9 > 1.052269518
        and entry_bar_lower_wick > 0.005828819005
        and entry_bar_volume_to_previous_bar_volume > 1.36056
        and entry_close_position_vs_previous_close_position > 0.7339743674
        and entry_close_to_previous_bar_high <= 1.086722314
        and entry_rejection_pressure <= 0.9581117034
        and entry_volume_price_efficiency <= 0.4431177378
        and gains_since_lowest_low <= 0.0954590328
        and macd_recovery_followthrough_quality <= 37.9438839
        and positive_vs_negative_volume_during_pullback <= 2.102654755
        and profit_since_open_to_bars_count_since_open <= 0.008038461208
    ):
        score += 1
        reasons.append("mined_broad_ema_distance_low_reclaim")

    # Mined Feature-Only Positive Pattern:
    # mined_broad_fast_low_recovery_reclaim
    # Covers: 18 positives / 0 FP
    # Includes: 4 currently untagged positives, 14 already-tagged positives
    # Conditions: 6
    if (
        distance_from_highest_high <= 4.5
        and entry_close_to_lowest_low_recovery > 1.337715328
        and entry_extension_pressure <= 0.2844875157
        and minutes_since_market_open > 20
        and pre_market_gains <= 0.1601275057
        and previous_bar_high_to_highest_high <= 0.9842794836
    ):
        score += 1
        reasons.append("mined_broad_fast_low_recovery_reclaim")

    # Mined Feature-Only Positive Pattern:
    # mined_broad_controlled_volume_recovery_reclaim
    # Covers: 18 positives / 0 FP
    # Includes: 4 currently untagged positives, 14 already-tagged positives
    # Conditions: 10
    if (
        current_day_high_to_previous_high <= 1.734777689
        and entry_bar_low_to_ema_9 <= 1.024830222
        and entry_bar_upper_wick > 0.0571895428
        and entry_bar_volume_to_recent_bars_average <= 2.46436727
        and entry_bar_volume_to_total_volume > 0.01952039357
        and entry_close_to_lowest_low_recovery <= 1.456912279
        and entry_extension_pressure > 0.3120003194
        and gains_since_lowest_low > 0.0726512745
        and pre_market_volume <= 3405334.875
        and previous_bar_high_to_highest_high <= 0.9976538718
    ):
        score += 1
        reasons.append("mined_broad_controlled_volume_recovery_reclaim")

    # Mined Feature-Only Positive Pattern:
    # mined_broad_volume_compression_entry_reclaim
    # Covers: 23 positives / 0 FP
    # Includes: 0 currently untagged positives, 23 already-tagged positives
    # Conditions: 12
    if (
        current_day_ema_9_to_ema_20 <= 1.139072895
        and entry_bar_open_to_ema_9 > 0.9915205538
        and entry_bar_open_to_ema_9 <= 1.011562109
        and entry_bar_volume_to_highest_high_volume > 1.264354348
        and entry_bar_volume_to_highest_volume_in_pullback <= 3.908864975
        and entry_bar_volume_to_recent_bars_average > 1.729531705
        and entry_close_position_vs_previous_close_position > 0.7275024951
        and entry_followthrough_after_near_reclaim <= 1.267271578
        and entry_volume_price_efficiency > 0.02633171901
        and minutes_since_market_open > 29.5
        and previous_bar_close_to_highest_high <= 1.004442811
        and reclaim_speed_from_lowest_low > 0.6453338563
    ):
        score += 1
        reasons.append("mined_broad_volume_compression_entry_reclaim")

    # Mined Feature-Only Positive Pattern:
    # mined_broad_simple_low_ema_volume_efficiency
    # Covers: 15 positives / 0 FP
    # Includes: 1 currently untagged positives, 14 already-tagged positives
    # Conditions: 5
    if (
        bars_above_volume_average_vs_under_since_highest_high <= 0.7239304781
        and current_day_ema_9_to_recent_days_ema_9 > 0.9933525026
        and current_day_high_to_recent_days_highs <= 1.664610028
        and entry_bar_low_to_ema_9 <= 1.002914965
        and entry_volume_price_efficiency <= 0.01573944604
    ):
        score += 1
        reasons.append("mined_broad_simple_low_ema_volume_efficiency")

    # Mined Feature-Only Positive Pattern:
    # mined_untagged_body_volume_balance_reclaim
    # Covers: 22 positives / 0 FP
    # Includes: 9 currently untagged positives, 13 already-tagged positives
    # Conditions: 19
    if (
        bars_since_highest_high_to_bars_before <= 1.029506207
        and current_day_movement_to_recent_days_movement <= 5.163761616
        and entry_bar_ema_9_to_vwap > 1.028492451
        and entry_bar_histogram_to_highest_high > -0.3267802149
        and entry_bar_volume_to_recent_bars_average > 1.629383028
        and entry_body_to_previous_bar_body > 1.588558018
        and entry_body_to_recent_bars_body_average > 0.9495838881
        and entry_body_to_recent_bars_body_average <= 7.812668562
        and gains_since_lowest_low > 0.08101280406
        and gains_since_lowest_low <= 0.3771048337
        and macd_recovery_age_quality > 9.024832726
        and macd_recovery_followthrough_quality <= 54.54345131
        and previous_bar_close_to_highest_high <= 1.004442811
        and previous_bar_high_to_highest_high <= 1.021455824
        and pullback_health > 0.8466237783
        and recent_bars_up_trend_pct > 0.3500000089
        and reclaim_close_strength_since_highest_high <= 0.6553650796
        and reclaim_speed_from_lowest_low <= 0.6381656229
        and volume_since_lowest_low_to_entry_vs_since_highest_high > 0.5224396288
    ):
        score += 1
        reasons.append("mined_untagged_body_volume_balance_reclaim")

    # Mined Feature-Only Positive Pattern:
    # mined_untagged_daily_extension_histogram_reclaim
    # Covers: 11 positives / 0 FP
    # Includes: 7 currently untagged positives, 4 already-tagged positives
    # Conditions: 7
    if (
        current_day_ema_9_to_ema_20 > 1.071515799
        and current_day_movement_to_recent_days_movement > 2.089119077
        and entry_bar_histogram_to_lowest_histogram > 1.000385642
        and entry_body_to_previous_bar_body <= 0.9876294434
        and entry_close_to_vwap <= 1.368021071
        and entry_volume_spike_without_high_context > 1.215853035
        and minutes_since_market_open > 63
    ):
        score += 1
        reasons.append("mined_untagged_daily_extension_histogram_reclaim")

    return score, reasons

def positive_reason_groups(
    positive_reasons: list[str],
) -> dict[str, object]:
    reason_set = set(positive_reasons)

    strong_groups = {
        "breakout_expansion": {
            "clean_high_breakout_continuation",
            "daily_ema_expansion_breakout",
        },
        "reset_volume_confirmation": {
            "real_reset_with_volume_confirmation",
            "strong_pullback_volume_reclaim",
            "supported_body_expansion_from_day_structure",
        },
        "fresh_timing": {
            "fresh_early_reclaim",
            "fresh_supported_reclaim_before_macd_stale",
        },
        "fresh_supported_volume_reclaim": {
            "fresh_supported_volume_reclaim_no_chase",
        },
        "close_strength_non_chase": {
            "snap_close_strength_low_extension",
            "controlled_non_chase_close_strength",
        },
        "explosive_body_support": {
            "supported_explosive_body",
        },
        "supported_ema_reclaim": {
            "supported_ema_histogram_reclaim",
        },
        "controlled_snap_reclaim": {
            "controlled_snap_reclaim",
        },
        "supported_day_volume_rotation": {
            "supported_day_volume_rotation",
        },
        "extreme_daily_expansion_fresh_body": {
            "extreme_daily_expansion_fresh_body_surge",
        },
        "quiet_open_controlled_reclaim": {
            "quiet_open_controlled_body_reclaim",
        },
        "delayed_volume_rebuild_controlled_histogram": {
            "delayed_volume_rebuild_controlled_histogram",
        },
        "delayed_pullback_volume_spike": {
            "delayed_pullback_volume_spike",
        },
        "previous_volume_spike_body_expansion": {
            "previous_volume_spike_body_expansion_not_vwap_chase",
        },
        "pullback_volume_dominance": {
            "pullback_volume_dominance_body_expansion",
        },
        "supported_volume_ownership": {
            "supported_volume_ownership_above_ema9",
        },
        "safe_reset_volume_confirmation": {
            "safe_reset_volume_confirmation_volume_balance",
        },
        "safe_close_strength_non_chase": {
            "safe_close_strength_non_chase_base",
        },
        "safe_broad_reset_clean_volume": {
            "safe_broad_reset_clean_volume",
        },
        "safe_breakout_expansion": {
            "safe_breakout_expansion_histogram_time",
        },
        "safe_fresh_supported_volume_reclaim": {
            "safe_fresh_supported_volume_reclaim_body",
        },
        "safe_refined_supported_base_reclaim": {
            "safe_refined_supported_base_reclaim",
        },
        "safe_fresh_timing": {
            "safe_fresh_timing_close_followthrough",
        },
        "safe_explosive_body_support": {
            "safe_explosive_body_controlled_macd",
        },
        "safe_real_reset_volume_confirmation": {
            "safe_real_reset_volume_confirmation_liquidity_control",
        },
        "safe_broad_reset_buyer_volume_confirmation": {
            "safe_broad_reset_buyer_volume_confirmation_clean_expansion",
        },
        "safe_fresh_macd_acceleration": {
            "safe_fresh_macd_acceleration_volume_participation",
        },
        "safe_strong_pullback_volume_reclaim": {
            "safe_strong_pullback_volume_reclaim_after_distance",
        },
        "safe_clean_high_breakout": {
            "safe_clean_high_breakout_histogram_control",
        },
        "safe_supported_base_reclaim": {
            "safe_supported_base_reclaim_low_high_quality",
        },
        "safe_controlled_non_chase_close_strength": {
            "safe_controlled_non_chase_close_strength_clean_pullback",
        },
        "safe_real_reset_rejection_ema_context": {
            "safe_real_reset_rejection_ema_context",
        },
        "safe_broad_reset_buyer_clean_liquidity": {
            "safe_broad_reset_buyer_clean_liquidity",
        },
        "safe_strong_pullback_no_prior_blowoff": {
            "safe_strong_pullback_no_prior_blowoff",
        },
        "safe_clean_high_close_strength_continuation": {
            "safe_clean_high_close_strength_continuation",
        },
        "safe_daily_ema_expansion_efficient_participation": {
            "safe_daily_ema_expansion_efficient_participation",
        },
        "safe_broad_reset_efficiency_premarket_volume_balance": {
            "safe_broad_reset_efficiency_premarket_volume_balance",
        },
        "safe_controlled_non_chase_vwap_base": {
            "safe_controlled_non_chase_vwap_base",
        },
        "safe_fresh_supported_near_high_base": {
            "safe_fresh_supported_near_high_base",
        },
        "safe_snap_close_strength_volume_confirmation": {
            "safe_snap_close_strength_volume_confirmation",
        },
        "safe_supported_body_day_structure_clean_participation": {
            "safe_supported_body_day_structure_clean_participation",
        },
        "safe_fresh_reclaim_macd_close_followthrough": {
            "safe_fresh_reclaim_macd_close_followthrough",
        },
        "safe_refined_base_reclaim_efficiency_volume_control": {
            "safe_refined_base_reclaim_efficiency_volume_control",
        },
    }

    soft_groups = {
        "broad_reset_buyer_volume": {
            "broad_reset_buyer_volume_confirmation",
            "broad_reset_efficiency_reclaim",
        },
        "low_float_volume_ownership": {
            "supported_low_float_volume_ownership",
        },
        "mature_reset_efficiency": {
            "mature_reset_efficiency_reclaim",
        },
        "controlled_weak_body_reclaim": {
            "controlled_weak_body_reclaim",
        },
        "premarket_supported_extension": {
            "premarket_supported_controlled_extension",
        },
        "late_body_continuation": {
            "late_body_continuation_non_extreme_daily_context",
        },
        "refined_broad_supported_base_reclaim": {
            "refined_broad_supported_base_reclaim",
        },
        "untagged_near_high_body_volume_reclaim": {
            "untagged_near_high_body_volume_reclaim",
        },
        "untagged_delayed_pullback_base_reclaim": {
            "untagged_delayed_pullback_base_reclaim",
        },
        "untagged_controlled_extension_reclaim": {
            "untagged_controlled_extension_reclaim",
        },
        "untagged_compact_volume_followthrough_reclaim": {
            "untagged_compact_volume_followthrough_reclaim",
        },
        "untagged_low_positive_bars_volume_reclaim": {
            "untagged_low_positive_bars_volume_reclaim",
        },
        "untagged_vwap_body_compression_reclaim": {
            "untagged_vwap_body_compression_reclaim",
        },
        "untagged_clean_rejection_volume_reclaim": {
            "untagged_clean_rejection_volume_reclaim",
        },
        "mined_feature_only_broad_rescue": {
            "mined_broad_distance_body_macd_reclaim",
            "mined_broad_daily_ema_distance_clean_reclaim",
            "mined_broad_volume_controlled_histogram_reclaim",
            "mined_broad_volume_pullback_followthrough_reclaim",
            "mined_broad_vwap_near_high_reclaim",
            "mined_broad_clean_breakout_low_extension_reclaim",
            "mined_broad_daily_ema20_pullback_volume_reclaim",
            "mined_broad_macd_body_followthrough_reclaim",
            "mined_broad_high_volume_pullback_depth_reclaim",
            "mined_broad_ema_distance_low_reclaim",
            "mined_broad_fast_low_recovery_reclaim",
            "mined_broad_controlled_volume_recovery_reclaim",
            "mined_broad_volume_compression_entry_reclaim",
            "mined_broad_simple_low_ema_volume_efficiency",
            "mined_untagged_body_volume_balance_reclaim",
            "mined_untagged_daily_extension_histogram_reclaim",
        },
    }

    matched_strong_groups: list[str] = []
    matched_soft_groups: list[str] = []

    for group_name, group_reasons in strong_groups.items():
        if reason_set.intersection(group_reasons):
            matched_strong_groups.append(group_name)

    for group_name, group_reasons in soft_groups.items():
        if reason_set.intersection(group_reasons):
            matched_soft_groups.append(group_name)

    matched_groups = matched_strong_groups + matched_soft_groups

    return {
        "positive_group_score": len(matched_groups),
        "positive_group_reasons": matched_groups,
        "strong_positive_group_score": len(matched_strong_groups),
        "strong_positive_group_reasons": matched_strong_groups,
        "soft_positive_group_score": len(matched_soft_groups),
        "soft_positive_group_reasons": matched_soft_groups,
    }

def positive_tier(
    strong_positive_group_score: int,
    soft_positive_group_score: int,
    positive_score: int,
) -> str:
    if strong_positive_group_score >= 3:
        return "elite_tag_trade"

    if strong_positive_group_score >= 2:
        return "strong_tag_trade"

    if strong_positive_group_score >= 1 and soft_positive_group_score >= 1:
        return "mixed_tag_trade"

    if strong_positive_group_score == 1:
        return "moderate_tag_trade"

    if soft_positive_group_score >= 1:
        return "soft_tag_trade"

    if positive_score >= 1:
        return "soft_tag_trade"

    return "no_known_tag_trade"
