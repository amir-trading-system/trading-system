def should_be_rejected_by_hard_rules(
    features_data: dict[str, float],
) -> bool:
    current_day_volume_to_recent_days_volume = features_data["feature_current_day_volume_to_recent_days_volume"]
    current_day_high_to_previous_high = features_data["feature_current_day_high_to_previous_high"]
    gains_until_entry_bar = features_data["feature_gains_until_entry_bar"]
    controlled_volume_entry_quality = features_data["feature_controlled_volume_entry_quality"]
    entry_extension_pressure = features_data["feature_entry_extension_pressure"]
    weak_wick_volume_rejection = features_data["feature_weak_wick_volume_rejection"]
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
    ):
        return True

    if (
        entry_bar_low_to_ema_9 > 1.0070604682
        and gains_since_lowest_low <= 0.0916305929
        and entry_rejection_pressure > 0.0234738560
        and entry_close_to_previous_bar_high > 1.0530339479
        and current_day_vwap_to_recent_days <= 2.8522806168
        and entry_followthrough_after_near_reclaim > 1.0850483775
        and bars_above_volume_average_vs_under_since_highest_high > 0
    ):
        return True

    if (
        entry_breakout_efficiency_from_ema_9 <= 0.4921557903
        and gains_until_entry_bar > 0.2806035727
        and current_day_volume_to_recent_days_volume <= 5.4054927826
        and pre_market_volume > 19492
        and current_day_low_to_ema_9 <= 1.1302526593
        and entry_close_strength_to_highest_high_close_strength <= 3.1998206377
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
    ):
        return True

    if (
        current_day_ema_20_to_recent_days_ema_20 <= 1.0401
        and entry_body_to_highest_high_body <= 0.807
        and volume_since_highest_high_to_volume_before <= 0.331
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
        entry_bar_low_to_ema_9 > 1.0070604682
        and gains_since_lowest_low <= 0.1303373128
        and entry_bar_upper_wick > 0.0226323679
        and entry_close_to_previous_bar_high > 1.0530339479
        and pre_market_gains <= 1.1489825845
        and current_day_low_to_ema_9 > 0.7408934236
        and macd_recovery_age_quality > 15.2474050522
        and near_high_weak_followthrough > 0.8235469460
        and entry_bar_lower_wick <= 0.3502510786
        and entry_volume_spike_without_high_context < 2.743258749282846
    ):
        return True

    if (
        entry_bar_vwap_to_ema_20 <= 0.9624572694
        and gains_until_entry_bar <= 1.0722402930
        and entry_volume_to_highest_volume_in_pullback <= 1.8528105021
        and current_day_movement_to_recent_days_movement > 8.3926472664
        and entry_body_to_highest_high_body <= 13.3459329605
        and current_day_vwap_to_recent_days > 1.5232991576
        and gains_since_lowest_low <= 0.56
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
    ):
        return True

    if (
        entry_body_to_recent_bars_body_average <= 3.138
        and pullback_depth_vs_pre_high_move >= 1.3531
        and entry_bar_volume_to_previous_bar_volume <= 2.0443
        and entry_bar_histogram_to_previous >= 0.5029
        and current_day_movement_to_recent_days_movement <= 6.104
        and pre_market_gains >= -0.0091
    ):
        return True

    if (
        volume_since_highest_high_to_volume_before <= 0.0113413654328
        and entry_bar_volume_to_previous_bar_volume <= 1.37210073325
    ):
        return True

    if (
        entry_bar_upper_wick >= 0.2837
        and current_day_low_to_ema_9 >= 1.1456
        and entry_followthrough_after_near_reclaim >= 1.1020
        and recent_bars_positive_bars_pct <= 0.7
    ):
        return True

    if (
        entry_close_position_vs_previous_close_position <= 0.731694032711
        and volume_since_highest_high_to_volume_before <= 0.144645677467
        and volume_without_macd_confirmation >= 0.7320706574892093
    ):
        return True

    if (
        entry_bar_low_to_ema_9 > 1.0070604682
        and gains_since_lowest_low > 0.1303373128
        and histogram_changed_to_positive_direction_vs_negative_pct > 1.0309523940
        and current_day_ema_9_to_recent_days_ema_9 <= 2.0428084135
        and entry_bar_macd_to_previous <= 1.1608323455
        and pre_market_volume > 6389.9147949219
        and entry_volume_to_highest_volume_in_pullback > 1.0537672043
        and entry_extension_pressure <= 0.2560228407
    ):
        return True

    if (
        gains_since_lowest_low <= 0.1226
        and previous_bar_volume_to_its_previous_volume <= 0.8477
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
        entry_bar_volume_to_recent_bars_average <= 1.613
        and entry_body_to_previous_bar_body <= 1.591
        and price_movement_from_highest_high_to_lowest_low <= 0.271
        and recent_bars_positive_bars_pct <= 0.701
    ):
        return True

    if (
        reclaim_close_strength_since_highest_high >= 0.5555
        and entry_rejection_pressure >= 0.1428
        and entry_breakout_efficiency_from_ema_9 <= 0.6955
        and entry_bar_body >= 0.6666
        and current_day_vwap_to_recent_days <= 2.1286
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
        and gains_since_lowest_low <= 0.1342
        and entry_body_to_previous_bar_body >= 2.8959
        and current_day_ema_9_to_recent_days_ema_9 <= 1.4339
        and entry_bar_close_to_highest_high >= 1.0178
        and bars_since_highest_high_to_bars_before <= 0.0141
        and recent_bars_up_trend_pct >= 0.4
    ):
        return True

    if (
        entry_bar_low_to_ema_9 <= 1.0070604682
        and entry_breakout_efficiency_from_ema_9 <= 0.9983366132
        and current_day_ema_9_to_recent_days_ema_9 <= 0.9913356900
        and entry_body_to_highest_high_body <= 4.6936500072
        and entry_rejection_pressure > 0.0012531328
        and entry_bar_vwap_to_ema_20 >= 0.7832668372258171
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
        entry_breakout_efficiency_from_ema_9 <= 0.4368653595
        and entry_bar_macd_to_previous > 0.4929415584
        and entry_close_to_vwap > 1.1723103523
        and highest_high_quality > 1.6963175535
        and reclaim_close_strength_since_highest_high > 0.2052604109
        and entry_bar_low_to_ema_9 <= 1.0156897902
        and bars_since_highest_high_to_bars_before <= 0.9219741821
        and uptrend_histogram_vs_downtrend_since_highest_high <= 0.3951525092
        and volume_since_lowest_low_to_entry_vs_since_highest_high > 0.4856138527
    ):
        return True

    if (
        entry_breakout_efficiency_from_ema_9 > 0.4910371602
        and bars_since_highest_high_to_bars_before <= 0.0018091702
        and entry_body_to_highest_high_body <= 1.6986946464
        and current_day_movement_to_recent_days_movement > 0.6746948957
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
        entry_close_strength_to_highest_high_close_strength <= 0.6933561644938037
        and entry_bar_volume_to_previous_bar_volume <= 1.9862868213373515
        and entry_bar_body <= 0.7009402985074643
    ):
        return True

    if (
        recent_bars_up_trend_pct >= 0.9
        and entry_bar_volume_to_volume_average <= 1.8993538884
    ):
        return True

    if (
        entry_bar_volume_to_volume_average <= 1.62644665002
        and current_day_ema_9_to_recent_days_ema_9 >= 2.00302421228
    ):
        return True

    if (
        entry_bar_open_to_ema_9 >= 1.02100165
        and entry_bar_close_to_highest_high <= 1.01447752
        and current_day_ema_9_to_ema_20 >= 1.153187004
        and entry_bar_body <= 0.6229021941816995
        and pullback_health <= 2.199284663467352
    ):
        return True

    if (
        controlled_volume_entry_quality <= 1.418
        and pullback_depth_vs_pre_high_move >= 1.93
        and entry_bar_open_to_ema_9 <= 1.0014
    ):
        return True

    if (
        current_day_ema_9_to_recent_days_ema_9 >= 1.27426832716
        and current_day_ema_20_to_recent_days_ema_20 <= 1.13188273075
        and entry_bar_ema_9_to_vwap <= 1.04418374495
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
    ):
        return True

    if (
        current_day_ema_20_to_recent_days_ema_20 <= 0.9703
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
    ):
        return True

    if (
        highest_high_quality >= 45.2194
        and pullback_depth_vs_pre_high_move <= 0.4973
    ):
        return True

    if (
        entry_volume_price_efficiency <= 0.01892
        and gains_since_lowest_low <= 0.03203
    ):
        return True

    if (
        minutes_since_market_open <= 29
        and pullback_depth_vs_pre_high_move <= 0.6014838509
        and profit_since_open_to_bars_count_since_open >= 0.01742149356
        and inefficient_breakout_extension <= 0.0
    ):
        return True

    if (
        macd_recovery_followthrough_quality >= 28.65018165941634
        and entry_histogram_to_highest_histogram <= 0.4210012484394506
    ):
        return True

    if (
        current_day_ema_9_to_ema_20 <= 1.259989
        and controlled_volume_entry_quality <= 0.776765
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
    ):
        return True

    if (
        entry_body_to_recent_bars_body_average >= 9.759273
        and entry_close_strength_to_highest_high_close_strength <= 1.041007
        and entry_close_to_vwap >= 1.1484540592
        and entry_bar_volume_to_total_volume < 0.6347828598662643
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
        current_day_low_to_ema_9 >= 1.358228224
        and entry_bar_vwap_to_ema_20 <= 0.8898687606
        and entry_breakout_efficiency_from_ema_9 >= 0.5188943549
        and pre_market_gains >= 0.2355555555555554
    ):
        return True

    if (
        entry_bar_upper_wick >= 0.2987368421
        and entry_extension_pressure >= 0.2814410998
        and current_day_ema_9_to_ema_20 >= 1.2564937075
    ):
        return True

    if (
        highest_high_to_entry_elapsed_minutes <= 2.0
        and entry_bar_volume_to_total_volume <= 0.013987671038471768
        and entry_volume_spike_without_high_context <= 2.1745357952992115
    ):
        return True

    if (
        previous_bar_high_to_highest_high >= 1.0022882983263004
        and volume_since_lowest_low_to_entry_vs_since_highest_high <= 0.4224316619731764
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
        entry_volume_to_highest_volume_in_pullback >= 2.3644566162
        and volume_without_macd_confirmation <= 1.3859621588
        and entry_close_to_vwap <= 1.192665838838092
        and bars_above_volume_average_vs_under_since_highest_high <= 1.0
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
        current_day_ema_9_to_recent_days_ema_9 <= 0.927
        and entry_body_to_highest_high_body <= 0.863
    ):
        return True

    if (
        entry_bar_vwap_to_ema_20 <= 0.9514810741
        and current_day_vwap_to_recent_days <= 2.7823119164
        and profit_since_open_to_bars_count_since_open > 0.0132751414
        and bars_above_volume_average_vs_under_since_highest_high > 0.2250000015
        and entry_followthrough_after_near_reclaim > 1.0432881853785902
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
        entry_bar_volume <= 40500
        and recent_bars_positive_bars_pct <= 0.4
        and pre_market_volume <= 7450
    ):
        return True

    if (
        bars_since_highest_high_to_bars_before <= 0.001774
        and entry_body_to_highest_high_body <= 1.271
        and entry_body_to_previous_bar_body <= 2.81
    ):
        return True

    if (
        bars_since_highest_high_to_bars_before <= 0.1951219512195122
        and gains_since_lowest_low <= 0.2146118721461188
        and pre_market_volume <= 0.0
    ):
        return True

    if (
        current_day_ema_9_to_ema_20 <= 1.120
        and entry_bar_volume_to_recent_bars_average <= 1.094
        and entry_close_strength_to_highest_high_close_strength <= 1.316
        and gains_since_lowest_low <= 0.139
    ):
        return True

    if (
        current_day_ema_20_to_recent_days_ema_20 <= 0.908
        and pullback_health <= 2.137
        and total_volume <= 3855000
        and entry_close_strength_to_highest_high_close_strength <= 2.227
    ):
        return True

    if (
        recent_bars_up_trend_pct <= 0.40
        and current_day_high_to_previous_high <= 1.0216
        and controlled_volume_entry_quality <= 5.631135876710102
    ):
        return True

    if (
        pullback_depth_vs_pre_high_move <= 0.88375
        and entry_body_to_previous_bar_body <= 0.98432
        and emas_distances_to_recent_bars_ema_distances <= 0.140767
        and pullback_health <= 5.634074932605927
    ):
        return True

    if (
        current_day_ema_9_to_recent_days_ema_9 <= 0.881
        and entry_close_to_previous_bar_close >= 1.307
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
        highest_high_to_entry_elapsed_minutes <= 2
        and entry_bar_volume_to_total_volume <= 0.0167
        and entry_bar_close_to_highest_high <= 1.0121
    ):
        return True

    if (
        reclaim_close_strength_since_highest_high <= 0.055556
        and entry_upper_wick_to_recent_upper_wick_average <= 0.293437
    ):
        return True

    if (
        entry_body_to_highest_high_body <= 0.334147
        and entry_volume_to_highest_volume_in_pullback <= 0.623601
    ):
        return True

    if (
        failed_pressure_to_followthrough >= 0.613675803152515
        and entry_bar_ema_9_to_ema_20 >= 1.0561902776954681
    ):
        return True

    if (
        volume_without_macd_confirmation <= 0.4212260308300548
        and entry_close_strength_to_highest_high_close_strength <= 1.3536733454766223
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
        weak_wick_volume_rejection
        and bars_above_volume_average_vs_under_since_highest_high <= 0.615
    ):
        return True

    if (
        current_day_vwap_to_recent_days <= 1.42
        and current_day_high_to_recent_days_highs >= 1.44
    ):
        return True

    if (
        controlled_volume_entry_quality <= 0.905
        and entry_body_to_previous_bar_body >= 21.15
    ):
        return True

    if (
        current_day_vwap_to_recent_days <= 1.423
        and current_day_high_to_recent_days_highs >= 1.488
    ):
        return True

    if (
        current_day_movement_to_recent_days_movement >= 3.966
        and current_day_low_to_ema_9 >= 1.58
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
    ):
        return True

    if (
        entry_volume_spike_without_high_context <= 1.927
        and volume_confirmation_quality <= 0.521
    ):
        return True

    return False
