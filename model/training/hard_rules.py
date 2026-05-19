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

    if (
        entry_bar_low_to_ema_9 > 1.0070604682
        and gains_since_lowest_low <= 0.0916305929
        and entry_rejection_pressure > 0.0234738560
        and entry_close_to_previous_bar_high > 1.0530339479
        and current_day_vwap_to_recent_days <= 7.642689643659104
        and entry_followthrough_after_near_reclaim > 1.073159808628476
        and bars_above_volume_average_vs_under_since_highest_high > 0
        and entry_bar_close_to_highest_high < 1.0188677346643054
    ):
        return True

    if (
        entry_breakout_efficiency_from_ema_9 <= 0.4921557903
        and gains_until_entry_bar > 0.2806035727
        and current_day_volume_to_recent_days_volume <= 5.4054927826
        and pre_market_volume > 19492
        and current_day_low_to_ema_9 <= 1.1302526593
        and entry_close_strength_to_highest_high_close_strength <= 3.1998206377
        and inefficient_breakout_extension <= 0.0
        and current_day_vwap_to_recent_days <= 1.39595737727032
        and current_day_ema_9_to_ema_20_distance_to_recent_days >= 0.9692596835497636
    ):
        return True

    if (
        previous_bar_high_to_highest_high <= 0.9955507815
        and previous_bar_high_to_highest_high > 0.9713259339
        and entry_bar_volume_to_recent_bars_average <= 1.8908511400
        and entry_bar_ema_9_to_vwap > 1.1076951027
        and entry_bar_open_to_ema_9 > 1.0056756735
    ):
        return True

    if (
        previous_bar_high_to_highest_high > 0.9955507815
        and entry_upper_wick_to_recent_upper_wick_average <= 0.3657742143
        and bars_since_highest_high_to_bars_before <= 0.0029988310
        and entry_body_to_recent_bars_body_average <= 3.5869444609
    ):
        return True

    if (
        previous_bar_high_to_highest_high > 0.9955507815
        and entry_upper_wick_to_recent_upper_wick_average > 0.6726041138
        and entry_breakout_efficiency_from_ema_9 <= 0.7530556917
        and entry_close_strength_to_highest_high_close_strength <= 0.7273891568
    ):
        return True

    if (
        previous_bar_high_to_highest_high > 0.9955507815
        and entry_upper_wick_to_recent_upper_wick_average > 0.6726041138
        and entry_breakout_efficiency_from_ema_9 <= 0.7530556917
        and entry_close_strength_to_highest_high_close_strength > 0.7273891568
        and entry_body_to_previous_bar_body > 1.8191176057
        and current_day_ema_9_to_ema_20 > 1.1524280906
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
        entry_bar_low_to_ema_9 > 1.0070604682
        and gains_since_lowest_low <= 0.1303373128
        and entry_bar_upper_wick > 0.0226323679
        and entry_close_to_previous_bar_high > 1.0530339479
        and pre_market_gains <= 1.1489825845
        and current_day_low_to_ema_9 > 0.7408934236
        and macd_recovery_age_quality >= 14.07288225230256
        and near_high_weak_followthrough > 0.8235469460
        and entry_bar_lower_wick <= 0.3502510786
        and entry_volume_spike_without_high_context < 2.743258749282846
    ):
        return True

    if (
        entry_bar_low_to_ema_9 > 1.0070604682
        and gains_since_lowest_low >= 0.038548752834467
        and histogram_changed_to_positive_direction_vs_negative_pct > 1.0309523940
        and current_day_ema_9_to_recent_days_ema_9 <= 2.0428084135
        and entry_bar_macd_to_previous <= 1.1608323455
        and pre_market_volume > 6389.9147949219
        and entry_volume_to_highest_volume_in_pullback > 1.0537672043
        and entry_extension_pressure <= 0.2560228407
    ):
        return True

    if (
        reclaim_close_strength_since_highest_high >= 0.5555
        and entry_rejection_pressure >= 0.1428
        and entry_breakout_efficiency_from_ema_9 <= 0.6955
        and entry_bar_body >= 0.6666
        and current_day_vwap_to_recent_days <= 2.1286
        and entry_bar_volume_to_total_volume <= 0.227660134288
    ):
        return True

    if (
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
    ):
        return True

    if (
        previous_bar_high_to_highest_high >= 1.0031150793650794
        and entry_bar_ema_9_to_ema_20 >= 1.053391820032275
        and entry_upper_wick_to_recent_upper_wick_average >= 0.6957268870518433
        and previous_bar_volume_to_its_previous_volume < 1.9726128342701927
    ):
        return True

    if (
        current_day_vwap_to_recent_days <= 2.2341
        and current_day_high_to_recent_days_highs >= 2.3105
        and pullback_depth_vs_pre_high_move <= 0.5717007696228753
    ):
        return True

    if (
        entry_bar_low_to_ema_9 > 1.0070604682
        and gains_since_lowest_low <= 0.1303373128
        and entry_rejection_pressure > 0.0234738560
        and entry_close_to_previous_bar_high > 1.0530339479
        and pre_market_gains <= 1.1489825845
        and current_day_low_to_ema_9 > 0.7408934236
        and macd_recovery_followthrough_quality <= 19.2633743286
        and total_volume <= 258551312.0
        and emas_distances_to_recent_bars_ema_distances > 0.1030314825
        and current_day_movement_to_recent_days_movement > 1.1011566698988786
        and current_day_vwap_to_recent_days <= 3.565152257209529
        and entry_bar_volume_to_volume_average <= 6.53772529741
    ):
        return True

    if (
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
    ):
        return True

    if (
        current_day_ema_20_to_recent_days_ema_20 <= 1.0401
        and entry_body_to_highest_high_body <= 1.03731343284
        and volume_since_highest_high_to_volume_before <= 0.8409639544696886
        and entry_bar_ema_9_to_vwap > 1.0852916008150164
        and entry_close_to_previous_bar_close >= 1.028846153846154
    ):
        return True

    if (
        entry_close_position_vs_previous_close_position <= 0.7012
        and volume_since_highest_high_to_volume_before <= 0.4316
    ):
        return True

    if (
        entry_body_to_recent_bars_body_average <= 3.138
        and pullback_depth_vs_pre_high_move >= 1.3531
        and entry_bar_volume_to_previous_bar_volume <= 2.0443
        and entry_bar_histogram_to_previous >= 0.5029
        and current_day_movement_to_recent_days_movement <= 6.104
        and pre_market_gains >= -0.0354838709677418
    ):
        return True

    if (
        volume_since_highest_high_to_volume_before >= 0.0035
        and volume_since_highest_high_to_volume_before <= 0.0141
        and entry_bar_volume_to_previous_bar_volume <= 1.42493594611
    ):
        return True

    if (
        gains_since_lowest_low <= 0.2115384615384616
        and previous_bar_volume_to_its_previous_volume <= 0.896686726772411
        and previous_bar_volume_to_its_previous_volume >= 0.5973
        and entry_upper_wick_to_recent_upper_wick_average >= 0.5068
        and current_day_high_to_recent_days_highs <= 1.8587
        and entry_bar_volume_to_highest_high_volume <= 2.2372
        and highest_high_quality >= 0.0858358066383931
    ):
        return True

    if (
        entry_volume_price_efficiency <= 0.02588854677
        and pre_market_volume <= 47862
        and recent_bars_positive_bars_pct >= 0.6
        and entry_close_to_previous_bar_high >= 1.0431372549019609
    ):
        return True

    if (
        failed_pressure_to_followthrough >= 0.4017
        and entry_close_position_vs_previous_close_position >= 1.6041
        and bars_above_volume_average_vs_under_since_highest_high <= 0.8334
        and controlled_volume_entry_quality >= 2.2409
        and minutes_since_market_open >= 60
        and current_day_low_to_ema_9 >= 0.8095
        and entry_close_to_previous_bar_high < 1.1054054054054052
    ):
        return True

    if (
        current_day_movement_to_recent_days_movement >= 6.5162
        and gains_since_lowest_low <= 0.228448275862
        and entry_body_to_previous_bar_body >= 2.8959
        and current_day_ema_9_to_recent_days_ema_9 <= 1.4831883273158324
        and entry_bar_close_to_highest_high >= 1.0178
        and bars_since_highest_high_to_bars_before <= 0.0141
        and recent_bars_up_trend_pct >= 0.4
        and entry_rejection_pressure <= 0.28
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
        price_movement_from_highest_high_to_lowest_low > 4.995
        and entry_bar_lower_wick > 0.132
        and entry_bar_volume_to_highest_high_volume <= 1.098
    ):
        return True

    if (
        entry_bar_ema_9_to_ema_20 > 1.0544950962
        and current_day_high_to_recent_days_highs <= 1.879216373
        and total_volume > 7206239
        and entry_followthrough_after_near_reclaim <= 1.4948156476
    ):
        return True

    if (
        entry_bar_volume_to_recent_bars_average >= 4.6813
        and reclaim_close_strength_since_highest_high >= 0.5359
        and pullback_health <= 3.72281
        and entry_upper_wick_to_recent_upper_wick_average <= 0.58855
        and entry_close_to_lowest_low_recovery >= 1.3400
        and pre_market_gains >= -0.01879
        and previous_bar_volume_to_its_previous_volume >= 0.3763
        and pre_market_volume >= 876.0
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
        entry_breakout_efficiency_from_ema_9 > 0.1634351015
        and entry_breakout_efficiency_from_ema_9 <= 0.4910371602
        and entry_bar_macd_to_previous <= 0.4929415584
        and previous_bar_close_to_highest_high > 0.8984606564
        and previous_bar_close_to_highest_high <= 0.9681976736
        and entry_volume_to_highest_volume_in_pullback > 0.8198091388
        and entry_bar_vwap_to_ema_20 <= 0.9952417314
        and entry_bar_volume_to_volume_average > 3.1015892029
        and gains_since_lowest_low <= 0.3168023080
    ):
        return True

    if (
        entry_breakout_efficiency_from_ema_9 <= 0.4368653595
        and entry_bar_macd_to_previous > 0.4929415584
        and entry_close_to_vwap > 1.1723103523
        and highest_high_quality > 1.6963175535
        and reclaim_close_strength_since_highest_high > 0.2052604109
        and entry_bar_low_to_ema_9 <= 1.0156897902
        and total_volume > 391419.5
        and failed_attempts_pressure <= 0.4304142594
        and recent_bars_up_trend_pct > 0.6500000060
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
        entry_breakout_efficiency_from_ema_9 > 0.4245388588392034
        and bars_since_highest_high_to_bars_before <= 0.0018091702
        and entry_body_to_highest_high_body <= 1.6986946464
        and current_day_movement_to_recent_days_movement > 0.6746948957
        and macd_recovery_followthrough_quality >= 1.296867882512253
        and minutes_since_market_open > 11
    ):
        return True

    if (
        price_movement_from_highest_high_to_lowest_low >= 1.3499
        and entry_bar_upper_wick >= 0.1702
        and entry_close_position_vs_previous_close_position >= 1.7663
        and entry_bar_volume_to_total_volume >= 0.02298
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
        recent_bars_up_trend_pct >= 0.9
        and entry_bar_volume_to_volume_average <= 1.8993538884
        and near_high_weak_followthrough <= 0.9333999609603748
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
        controlled_volume_entry_quality <= 1.418
        and pullback_depth_vs_pre_high_move >= 1.93
        and entry_bar_open_to_ema_9 <= 1.0014
        and entry_body_to_recent_bars_body_average <= 4.16585744804817
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
        volume_since_lowest_low_to_entry_vs_since_highest_high <= 0.291147893564
        and profit_since_open_to_bars_count_since_open <= 0.00369869518854
        and pre_market_gains <= 0.00634941981096
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
        current_day_ema_20_to_recent_days_ema_20 <= 1.008479159307657
        and entry_close_strength_to_highest_high_close_strength <= 1.070
        and uptrend_histogram_vs_downtrend_since_highest_high >= 0.405
    ):
        return True

    if (
        total_volume <= 499196.6
        and entry_histogram_to_highest_histogram >= 2.1306
    ):
        return True

    if (
        current_day_volume_to_recent_days_volume <= 5.698130559
        and entry_bar_low_to_ema_9 >= 1.0189563
        and entry_bar_ema_9_to_vwap >= 1.09945013
        and entry_volume_price_efficiency < 0.4123782583330475
    ):
        return True

    if (
        pullback_depth_vs_pre_high_move <= 0.4368705484108274
        and profit_since_open_to_bars_count_since_open >= 0.00576
    ):
        return True

    if (
        entry_bar_open_to_ema_9 >= 1.018775
        and entry_bar_macd_to_previous <= 0.371873
    ):
        return True

    if (
        current_day_vwap_to_recent_days <= 1.404
        and positive_vs_negative_volume_during_pullback <= 0.310
        and entry_close_strength_to_highest_high_close_strength <= 1.052
        and macd_recovery_age_quality > 11.472846724011536
        and entry_close_to_previous_bar_high >= 1.0543184885290149
    ):
        return True

    if (
        entry_close_strength_to_highest_high_close_strength <= 0.947374
        and entry_bar_volume_to_recent_bars_average >= 9.089611
        and failed_pressure_to_followthrough < 1.8032795612091643
        and entry_volume_spike_without_high_context >= 0.0108463987712592
    ):
        return True

    if (
        entry_bar_upper_wick >= 0.278571428571
        and entry_extension_pressure >= 0.2814410998
        and current_day_ema_9_to_ema_20 >= 1.2140274946512368
    ):
        return True

    if (
        highest_high_to_entry_elapsed_minutes <= 2.0
        and entry_bar_volume_to_total_volume <= 0.013987671038471768
        and entry_volume_spike_without_high_context <= 2.1745357952992115
        and entry_bar_open_to_ema_9 >= 1.003
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
        pre_market_volume <= 41894.4
        and entry_bar_histogram_to_previous >= 7.814066193177794
        and entry_close_to_previous_bar_high >= 1.086
    ):
        return True

    if (
        entry_volume_to_highest_volume_in_pullback >= 2.207124555748409
        and volume_without_macd_confirmation <= 1.3859621588
        and entry_close_to_vwap <= 1.192665838838092
        and bars_above_volume_average_vs_under_since_highest_high <= 1.0
        and volume_since_highest_high_to_volume_before >= 0.0035742178902402
    ):
        return True

    if (
        entry_body_to_highest_high_body >= 21.0911
        and pullback_depth_vs_pre_high_move <= 0.8421832074
        and entry_close_to_vwap < 1.214043135738546
        and pre_market_gains <= 0.203125
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
        bars_above_volume_average_vs_under_since_highest_high > 0.2539
        and current_day_movement_to_recent_days_movement > 2.2284
        and entry_bar_low_to_ema_9 <= 1.00354
        and entry_breakout_efficiency_from_ema_9 > 0.4921
        and entry_close_to_previous_bar_close <= 1.1124
        and entry_histogram_to_highest_histogram <= 0.4558
        and entry_volume_to_highest_volume_in_pullback > 1.2703
        and entry_rejection_pressure > 0
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
        bars_since_highest_high_to_bars_before <= 0.0018939393939393
        and entry_body_to_highest_high_body <= 1.271
        and entry_body_to_previous_bar_body <= 4.333333333333294
        and not clean_reentry_confirmation
    ):
        return True

    if (
        bars_since_highest_high_to_bars_before <= 0.1951219512195122
        and gains_since_lowest_low <= 0.2146118721461188
        and pre_market_volume <= 0.0
        and pullback_depth_vs_pre_high_move <= 2.0677942074938342
    ):
        return True

    if (
        recent_bars_up_trend_pct <= 0.40
        and current_day_high_to_previous_high <= 1.0216
        and controlled_volume_entry_quality <= 5.631135876710102
        and entry_volume_price_efficiency <= 0.073140707851
    ):
        return True

    if (
        pullback_depth_vs_pre_high_move <= 0.88375
        and entry_body_to_previous_bar_body <= 0.98432
        and emas_distances_to_recent_bars_ema_distances <= 0.149473967112886
        and pullback_health <= 5.634074932605927
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
        price_movement_from_highest_high_to_lowest_low <= 4.995
        and minutes_since_market_open <= 30.5
        and entry_bar_low_to_ema_9 > 0.9937
        and entry_bar_body > 0.9507
        and pre_market_volume >= 56104
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
        highest_high_to_entry_elapsed_minutes <= 4
        and entry_bar_volume_to_total_volume <= 0.0186582446829219
        and entry_bar_close_to_highest_high <= 1.0121
        and entry_bar_open_to_ema_9 >= 1.003
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
        volume_without_macd_confirmation <= 0.4212260308300548
        and entry_close_strength_to_highest_high_close_strength <= 1.3536733454766223
        and volume_confirmation_quality >= 0.0957090445047056
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
        entry_bar_close_to_highest_high <= 1.008
        and pre_market_volume <= 1347
    ):
        return True

    if (
        entry_bar_volume <= 29886.5
        and entry_volume_price_efficiency <= 0.0279956333
        and volume_without_macd_confirmation >= 0.2977939445781497
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
    ):
        return True

    if (
        entry_close_strength_to_highest_high_close_strength <= 0.9146477178873554
        and entry_body_to_previous_bar_body >= 31.999999999998817
    ):
        return True

    if (
        entry_bar_open_to_ema_9 <= 0.9913
        and entry_extension_pressure >= 0.3907
    ):
        return True

    if (
        macd_recovery_age_quality >= 16.58
        and entry_close_to_previous_bar_high >= 1.2408
        and total_volume <= 413805.0
    ):
        return True

    if (
        entry_bar_low_to_ema_9 >= 1.0325
        and uptrend_histogram_vs_downtrend_since_highest_high >= 0.4246
        and entry_volume_price_efficiency >= 0.7243
    ):
        return True

    if (
        entry_volume_price_efficiency >= 0.8190
        and current_day_volume_to_recent_days_volume >= 131.07
        and distance_from_last_negative_macd_bar >= 12
    ):
        return True

    if (
        total_volume >= 29900908.0
        and failed_pressure_to_followthrough >= 0.3500
        and entry_close_to_lowest_low_recovery <= 1.0196
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
        macd_recovery_age_quality >= 18.45
        and current_day_low_to_ema_9 <= 1.0123227559458436
        and highest_high_quality <= 0.2095
    ):
        return True

    if (
        total_volume <= 339183.0
        and entry_bar_ema_9_to_ema_20 >= 1.0394
        and entry_bar_volume_to_total_volume >= 0.1249
    ):
        return True

    if (
        highest_high_quality <= 0.2095
        and pre_market_gains >= 0.2355
        and total_volume >= 85786861.0
    ):
        return True

    if (
        failed_pressure_to_followthrough >= 0.604
        and entry_bar_close_to_highest_high >= 1.0313
    ):
        return True

    if (
        current_day_high_to_previous_high <= 1.045
        and pre_market_volume <= 18560
    ):
        return True

    if (
        pullback_depth_vs_pre_high_move >= 2.206369
        and volume_since_lowest_low_to_entry_vs_since_highest_high >= 0.9337
        and highest_high_quality <= 11.662730449595951
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
        failed_pressure_to_followthrough >= 1.5
        and entry_body_to_highest_high_body <= 0.6
        and total_volume >= 10000000
        and entry_close_strength_to_highest_high_close_strength >= 2
    ):
        return True

    if (
        current_day_volume_to_recent_days_volume >= 100
        and volume_confirmation_quality <= 0.1
        and entry_volume_spike_without_high_context >= 10
        and entry_volume_price_efficiency <= 0.05
        and entry_body_to_previous_bar_body >= 10
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
        entry_volume_price_efficiency <= 0.0439789558119
        and highest_high_quality >= 10
        and entry_body_to_previous_bar_body >= 10
    ):
        return True

    if (
        entry_body_to_previous_bar_body >= 100
        and entry_close_strength_to_highest_high_close_strength >= 10
        and total_volume <= 1000000
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
    ):
        return True

    return False
