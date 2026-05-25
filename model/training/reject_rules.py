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
    entry_bar_volume_to_highest_volume_in_pullback = features_data["feature_entry_bar_volume_to_highest_volume_in_pullback"]
    entry_bar_histogram_to_highest_histogram = features_data["feature_entry_bar_histogram_to_highest_histogram"]
    distance_from_highest_high = features_data["feature_distance_from_highest_high"]
    lowest_low_to_entry_elapsed_minutes = features_data["feature_lowest_low_to_entry_elapsed_minutes"]
    bars_since_lowest_low_to_entry = features_data["feature_bars_since_lowest_low_to_entry"]
    crossed_at_least_one_bar_from_recent_bars = features_data["feature_crossed_at_least_one_bar_from_recent_bars"]
    entry_bar_histogram_to_highest_high = features_data["feature_entry_bar_histogram_to_highest_high"]
    strong_vwap_volume_reentry = features_data["feature_strong_vwap_volume_reentry"]
    reclaim_speed_from_lowest_low = features_data["feature_reclaim_speed_from_lowest_low"]

    if (
        current_day_low_to_ema_9 > 0.3948193341
        and entry_bar_body <= 0.7694405615
        and entry_bar_histogram_to_highest_high > 0.713622421
        and entry_bar_low_to_ema_9 > 1.007261813
        and entry_bar_volume > 20205
        and entry_bar_volume_to_highest_high_volume <= 2.096042037
        and entry_body_to_highest_high_body <= 1.632857144
        and entry_rejection_pressure > 0.001432664809
        and entry_volume_spike_without_high_context <= 5.177247047
        and pre_market_gains <= 1.528925538
        and previous_bar_close_to_highest_high > 0.9752454758
        and previous_bar_volume_to_its_previous_volume > 0.2773110047
        and profit_since_open_to_bars_count_since_open > 0.001525149797
        and volume_without_macd_confirmation <= 3.347349882
    ):
        return True

    if (
        current_day_ema_9_to_ema_20_distance_to_recent_days > 0.990100801
        and entry_bar_histogram_to_highest_histogram > 0.3627116829
        and entry_bar_low_to_ema_9 > 1.010243058
        and entry_bar_volume_to_highest_high_volume > 0.4413036257
        and entry_body_to_recent_bars_body_average <= 14.07715321
        and fake_reclaim_pressure <= 1.705502808
        and gains_since_lowest_low <= 0.1741659939
        and minutes_since_market_open <= 355.5
        and previous_bar_volume_to_its_previous_volume <= 2.734791994
        and price_movement_from_highest_high_to_lowest_low <= 0.375
        and pullback_depth_vs_pre_high_move <= 0.7629830241
    ):
        return True

    if (
        highest_high_quality > 0.907874061
        and macd_recovery_age_quality > 1.0022545
        and current_day_low_to_ema_9 <= 1.048352152
        and entry_close_strength_to_highest_high_close_strength <= 2.593818561
        and highest_high_to_entry_elapsed_minutes <= 21
        and highest_high_to_entry_elapsed_minutes <= 23
        and entry_bar_vwap_to_ema_20 <= 0.9623598503
        and emas_distances_to_recent_bars_ema_distances > 0.1273369017
        and positive_vs_negative_volume_during_pullback <= 1.83420751
        and entry_bar_histogram_to_lowest_histogram <= 1.297909623
    ):
        return True

    if (
        entry_bar_ema_9_to_vwap > 1.082769752
        and entry_bar_histogram_to_lowest_histogram <= 2.151613951
        and entry_bar_lower_wick > 0.2701835781
        and entry_bar_volume_to_previous_bar_volume <= 3.491748929
        and entry_body_to_recent_bars_body_average <= 8.75
        and entry_close_strength_to_highest_high_close_strength <= 3.718247294
        and entry_close_to_previous_bar_close <= 1.552034914
        and positive_vs_negative_volume_during_pullback > 0.2020323575
        and uptrend_histogram_vs_downtrend_since_highest_high <= 2
    ):
        return True

    if (
        bars_since_highest_high_to_bars_before <= 0.008774044458
        and current_day_ema_9_to_ema_20_distance_to_recent_days <= 8.457616806
        and emas_distances_to_recent_bars_ema_distances <= 0.2957231849
        and entry_bar_open_to_ema_9 <= 1.017704129
        and entry_bar_upper_wick <= 0.5309828818
        and entry_bar_volume > 18668.63965
        and entry_bar_volume_to_total_volume <= 0.04469957016
        and entry_bar_vwap_to_ema_20 <= 0.946212709
        and gains_until_entry_bar <= 1.501322269
        and highest_high_quality > 2.576636672
        and previous_bar_close_to_highest_high > 0.9275676608
        and volume_since_highest_high_to_volume_before > 0.0008613147656
    ):
        return True

    if (
        bars_since_lowest_low_to_entry > 10.5
        and current_day_low_to_ema_9 <= 1.053010821
        and current_day_volume_to_recent_days_volume <= 197.5258408
        and distance_from_last_negative_macd_bar > 1.5
        and entry_bar_low_to_ema_9 <= 1.057357073
        and entry_bar_open_to_ema_9 > 0.997000128
        and entry_bar_volume_to_recent_bars_average <= 26.03781414
        and entry_close_to_lowest_low_recovery > 1.094059467
        and highest_high_quality > 1.574973524
        and lowest_low_to_entry_elapsed_minutes > 8.5
        and uptrend_histogram_vs_downtrend_since_highest_high <= 0.4057287425
    ):
        return True

    if (
        current_day_ema_9_to_ema_20_distance_to_recent_days <= 11.27818871
        and distance_from_highest_high > 4.5
        and entry_bar_histogram_to_highest_histogram > -0.5815722346
        and entry_bar_histogram_to_previous > 0.9340884686
        and entry_bar_lower_wick <= 0.1828590482
        and entry_bar_macd_to_previous <= 2.421082854
        and entry_close_to_vwap <= 1.15113014
        and entry_followthrough_after_near_reclaim <= 1.158268571
        and entry_rejection_pressure > 0.2250847742
        and reclaim_speed_from_lowest_low > 0.01257759053
    ):
        return True

    if (
        bars_since_lowest_low_to_entry <= 3.5
        and current_day_ema_9_to_ema_20_distance_to_recent_days <= 62.20866108
        and entry_bar_ema_9_to_vwap > 1.034896374
        and entry_bar_volume_to_highest_high_volume <= 1.504539549
        and entry_close_to_previous_bar_high > 1.074454546
        and previous_bar_high_to_highest_high <= 0.9939777851
        and previous_bar_volume_to_its_previous_volume <= 1.719502091
        and pullback_depth_vs_pre_high_move <= 0.780095309
    ):
        return True

    if (
        current_day_vwap_to_recent_days > 1.225785911
        and entry_bar_low_to_ema_9 > 1.015325069
        and entry_bar_lower_wick <= 0.3334510624
        and entry_bar_open_to_ema_9 > 1.015580714
        and entry_bar_upper_wick > 0.3118715435
        and entry_bar_vwap_to_ema_20 <= 1.027661383
        and pullback_depth_vs_pre_high_move > 0.765894264
        and volume_confirmation_quality > 0.1907785684
    ):
        return True

    if (
        current_day_ema_20_to_recent_days_ema_20 > 1.052795529
        and current_day_volume_to_recent_days_volume > 1.058630824
        and entry_bar_low_to_ema_9 <= 1.006791234
        and macd_recovery_age_quality <= 26.94335651
        and near_high_weak_followthrough > 0.6534158289
        and pre_market_volume <= 4998.5
        and volume_without_macd_confirmation > 1.091310799
    ):
        return True

    if (
        emas_distances_to_recent_bars_ema_distances > 0.1106065884
        and emas_distances_to_recent_bars_ema_distances <= 0.1564210057
        and entry_bar_close_to_highest_high <= 1.135587871
        and entry_bar_volume_to_previous_bar_volume <= 1.803164303
        and entry_bar_volume_to_recent_bars_average <= 2.538373828
        and entry_bar_vwap_to_ema_20 <= 0.9696556926
        and failed_pressure_to_followthrough > 0.002248052799
        and lowest_low_to_entry_elapsed_minutes <= 2.5
        and pre_market_gains <= 0.7259792089
    ):
        return True

    if (
        bars_since_lowest_low_to_entry > 3.5
        and controlled_volume_entry_quality <= 7.071050406
        and current_day_high_to_previous_high > 1.105437458
        and entry_bar_histogram_to_highest_high <= 1.283173323
        and entry_bar_volume_to_recent_bars_average <= 2.46436727
        and entry_bar_volume_to_volume_average <= 3.040188789
        and entry_close_to_previous_bar_high <= 1.090274036
        and entry_close_to_vwap > 1.069336712
        and recent_bars_positive_bars_pct > 0.450000003
    ):
        return True

    if (
        current_day_low_to_ema_9 > 0.4654018283
        and current_day_movement_to_recent_days_movement > 0.8634671271
        and distance_from_highest_high <= 3.5
        and entry_bar_open_to_ema_9 > 1.011614263
        and entry_bar_vwap_to_ema_20 <= 0.9697213471
        and entry_body_to_highest_high_body <= 2.53125
        and highest_high_quality > 2.613798141
        and previous_bar_close_to_highest_high > 0.9315455556
        and pullback_depth_vs_pre_high_move <= 7.982297182
    ):
        return True

    if (
        current_day_volume_to_recent_days_volume <= 703.3054199
        and entry_bar_ema_9_to_vwap <= 1.435429037
        and entry_bar_volume_to_total_volume <= 0.1350661144
        and entry_rejection_pressure > 0.2498437762
        and entry_volume_spike_without_high_context <= 1.367694974
        and highest_high_quality <= 66.52034187
        and highest_high_to_entry_elapsed_minutes > 3.5
        and pre_market_volume <= 13579827
        and previous_bar_volume_to_its_previous_volume <= 0.6207201183
    ):
        return True

    if (
        entry_bar_low_to_ema_9 > 1.012828231
        and entry_close_to_previous_bar_high <= 1.297641873
        and entry_rejection_pressure > 0.1781633571
        and gains_until_entry_bar <= 2.989003778
        and previous_bar_close_to_highest_high > 0.9875080884
        and volume_confirmation_quality <= 1.72980243
        and volume_since_lowest_low_to_entry_vs_since_highest_high > 0.6912430525
    ):
        return True

    if (
        current_day_vwap_to_recent_days > 0.8840062022
        and entry_bar_low_to_ema_9 > 1.006311774
        and entry_bar_volume <= 4122598
        and entry_bar_volume_to_highest_volume_in_pullback <= 8.049009562
        and entry_body_to_highest_high_body <= 3.53125
        and entry_volume_price_efficiency <= 3.518256426
        and pre_market_gains > -0.05602339841
        and previous_bar_close_to_highest_high > 0.9641307294
        and volume_since_highest_high_to_volume_before <= 0.01759812422
    ):
        return True

    if (
        current_day_ema_9_to_ema_20_distance_to_recent_days <= 2.93526125
        and current_day_vwap_to_recent_days <= 3.399968147
        and entry_bar_body > 0.2872670814
        and entry_bar_body <= 0.9736668766
        and entry_bar_histogram_to_previous > 1.065275609
        and entry_bar_low_to_ema_9 > 1.007060468
        and entry_bar_low_to_ema_9 <= 1.07849741
        and entry_bar_volume <= 2578833.5
        and entry_bar_volume_to_volume_average <= 5.240484953
        and entry_bar_vwap_to_ema_20 <= 1.166416168
        and highest_high_to_entry_elapsed_minutes <= 4.5
        and previous_bar_close_to_highest_high > 0.982717365
        and previous_bar_high_to_highest_high > 0.9890772998
    ):
        return True

    if (
        emas_distances_to_recent_bars_ema_distances <= 0.1689215526
        and entry_bar_close_to_highest_high <= 1.043924272
        and entry_bar_volume_to_recent_bars_average <= 1.946778297
        and entry_bar_vwap_to_ema_20 <= 0.9454233944
        and previous_bar_high_to_highest_high > 0.9869109094
        and volume_since_lowest_low_to_entry_vs_since_highest_high > 0.8193178177
    ):
        return True

    if (
        bars_since_lowest_low_to_entry > 13.5
        and current_day_ema_9_to_ema_20 <= 1.456079483
        and distance_from_last_negative_macd_bar <= 19.5
        and entry_bar_ema_9_to_ema_20 <= 1.078942776
        and entry_body_to_highest_high_body <= 52.60869598
        and entry_body_to_previous_bar_body <= 2.773749948
        and entry_close_to_lowest_low_recovery > 1.015999258
        and entry_close_to_lowest_low_recovery <= 2.411666632
        and entry_close_to_vwap > 1.070587277
        and entry_volume_price_efficiency <= 1.747485936
        and previous_bar_close_to_highest_high > 0.979554683
        and profit_since_open_to_bars_count_since_open > 0.0009796297527
        and pullback_depth_vs_pre_high_move > 1.010968328
        and volume_without_macd_confirmation <= 138.1645584
    ):
        return True

    if (
        current_day_ema_9_to_recent_days_ema_9 > 0.9682975113
        and entry_bar_low_to_ema_9 > 1.007064581
        and entry_bar_upper_wick > 0.07549857721
        and entry_bar_volume_to_total_volume > 0.035168631
        and entry_upper_wick_to_recent_upper_wick_average > 0.5023422539
        and entry_upper_wick_to_recent_upper_wick_average <= 3.96203959
        and gains_since_lowest_low <= 0.2105717137
        and highest_high_to_entry_elapsed_minutes <= 4.5
        and pre_market_gains <= 0.04537976906
    ):
        return True

    if (
        entry_bar_histogram_to_highest_histogram <= 2.916334152
        and entry_bar_macd_to_previous <= 1.18422693
        and entry_bar_volume_to_highest_volume_in_pullback <= 2.039056778
        and entry_bar_volume_to_volume_average <= 2.078589797
        and entry_close_to_previous_bar_close > 1.077357113
        and entry_rejection_pressure <= 0.3083916157
        and macd_recovery_followthrough_quality > 1.545556247
        and volume_without_macd_confirmation <= 1.708280623
    ):
        return True

    if (
        bars_above_volume_average_vs_under_since_highest_high > 0.2722222358
        and bars_above_volume_average_vs_under_since_highest_high <= 3.75
        and current_day_ema_9_to_ema_20 <= 1.488875508
        and current_day_high_to_recent_days_highs > 0.8672295213
        and distance_from_highest_high <= 74.5
        and entry_bar_body > 0.5604878068
        and entry_bar_close_to_highest_high > 1.011305332
        and entry_bar_low_to_ema_9 > 1.007342935
        and entry_bar_volume_to_volume_average > 2.204502106
        and gains_until_entry_bar <= 1.971365035
        and macd_recovery_age_quality > 0.3023335636
        and near_high_weak_followthrough > 0.8526823223
        and pullback_health <= 19.83761978
    ):
        return True

    if (
        entry_bar_ema_9_to_vwap > 1.082769752
        and entry_bar_histogram_to_highest_histogram > 0.8403291106
        and entry_bar_volume_to_total_volume <= 0.3913063109
        and entry_body_to_recent_bars_body_average <= 2.421025872
        and gains_until_entry_bar > 0.2645576745
        and pullback_depth_vs_pre_high_move <= 0.6512024105
    ):
        return True

    if (
        current_day_ema_20_to_recent_days_ema_20 <= 1.121191442
        and entry_bar_body <= 0.5581818223
        and entry_close_to_previous_bar_close <= 1.360087812
        and entry_volume_spike_without_high_context <= 2.508698463
        and fake_reclaim_pressure <= 0.4436782897
        and previous_bar_high_to_highest_high > 0.9942194521
    ):
        return True

    if (
        entry_bar_ema_9_to_vwap > 1.133062124
        and entry_bar_volume_to_volume_average <= 1.689962864
        and entry_extension_pressure > 0.372032851
        and previous_bar_close_to_highest_high <= 0.9900442362
    ):
        return True

    if (
        current_day_high_to_recent_days_highs > 0.7507748902
        and current_day_low_to_ema_9 <= 1.139907777
        and current_day_movement_to_recent_days_movement <= 32.88862991
        and current_day_volume_to_recent_days_volume <= 875.9853821
        and current_day_vwap_to_recent_days > 1.454364538
        and entry_bar_body > 0.5109468102
        and entry_bar_close_to_highest_high <= 1.045481384
        and entry_bar_histogram_to_highest_histogram <= 0.8661656678
        and entry_bar_volume > 33694.59961
        and entry_bar_volume_to_volume_average <= 2.624112844
        and entry_bar_vwap_to_ema_20 <= 0.962839365
        and entry_volume_price_efficiency > 0.01550700841
        and lowest_low_to_entry_elapsed_minutes > 2.5
        and previous_bar_volume_to_its_previous_volume > 0.7161327899
        and pullback_health > 0.2186572626
        and volume_since_highest_high_to_volume_before <= 25.43840027
    ):
        return True

    if (
        bars_above_volume_average_vs_under_since_highest_high <= 0.9181818366
        and entry_bar_body <= 0.9964788854
        and entry_bar_ema_9_to_ema_20 <= 1.064846516
        and entry_bar_low_to_ema_9 > 1.006782889
        and entry_close_to_previous_bar_close <= 1.109350085
        and entry_volume_price_efficiency <= 0.4933377206
        and gains_since_lowest_low <= 0.3378870934
        and minutes_since_market_open > 53
        and near_high_weak_followthrough <= 0.9518693388
        and positive_vs_negative_volume_during_pullback <= 2.33378005
        and pre_market_volume <= 8486279
        and previous_bar_close_to_highest_high > 0.9837848246
        and profit_since_open_to_bars_count_since_open > 0.001342775533
        and volume_confirmation_quality > 0.1957733929
    ):
        return True

    if (
        bars_above_volume_average_vs_under_since_highest_high > 0.2833333388
        and bars_since_highest_high_to_bars_before > 0.004706116859
        and crossed_at_least_one_bar_from_recent_bars <= 0.5
        and entry_extension_pressure > 0.3980751336
        and entry_followthrough_after_near_reclaim > 1.052758813
        and entry_rejection_pressure <= 0.448347494
        and gains_until_entry_bar > 0.2575407252
    ):
        return True

    if (
        distance_from_last_negative_macd_bar > 0.5
        and entry_bar_histogram_to_previous > 0.8973072767
        and entry_bar_movement_recent_bars_average > 4.271438837
        and entry_rejection_pressure > 0.4579292238
        and entry_rejection_pressure <= 1.00746125
        and entry_volume_spike_without_high_context <= 2.44371748
        and positive_vs_negative_volume_during_pullback > 0.8280515075
    ):
        return True

    if (
        current_day_ema_9_to_ema_20 > 1.127568305
        and entry_bar_ema_9_to_vwap > 1.059993267
        and entry_bar_histogram_to_highest_high <= 1.373863101
        and entry_bar_histogram_to_lowest_histogram <= 3.183271527
        and entry_bar_volume_to_volume_average <= 3.27557838
        and entry_body_to_highest_high_body <= 5.090906143
        and entry_body_to_previous_bar_body <= 7.108420849
        and entry_volume_price_efficiency > 0.04680577293
        and previous_bar_high_to_highest_high > 0.9739197195
        and profit_since_open_to_bars_count_since_open > 0.001346467761
        and volume_since_highest_high_to_volume_before <= 0.04159185477
        and volume_without_macd_confirmation > 1.793002427
    ):
        return True

    if (
        bars_since_lowest_low_to_entry <= 148
        and current_day_high_to_recent_days_highs > 1.33207345
        and entry_bar_ema_9_to_vwap > 1.036095798
        and entry_bar_histogram_to_previous <= 7.061025143
        and entry_bar_upper_wick <= 0.3777113408
        and entry_bar_volume_to_previous_bar_volume > 1.864426255
        and entry_close_strength_to_highest_high_close_strength > 1.099067092
        and entry_volume_price_efficiency > 0.01015808573
        and entry_volume_price_efficiency <= 0.02891539689
        and minutes_since_market_open > 19.5
        and pre_market_volume <= 266917
    ):
        return True

    if (
        current_day_ema_9_to_ema_20 <= 1.303220093
        and current_day_low_to_ema_9 <= 0.8846435249
        and entry_followthrough_after_near_reclaim > 1.103989959
        and entry_volume_spike_without_high_context > 1.263534904
        and minutes_since_market_open > 104.5
        and positive_vs_negative_volume_during_pullback > 0.9473784864
        and previous_bar_high_to_highest_high <= 0.9818832576
        and profit_since_open_to_bars_count_since_open <= 0.0098955594
        and reclaim_close_strength_since_highest_high > 0.1096149348
    ):
        return True

    if (
        distance_from_highest_high <= 124
        and entry_bar_close_to_highest_high <= 1.045296669
        and entry_bar_histogram_to_highest_histogram <= 1.19168514
        and entry_bar_lower_wick <= 0.3195833266
        and entry_bar_open_to_ema_9 > 0.9714248776
        and entry_bar_upper_wick <= 0.1224450655
        and entry_bar_volume_to_total_volume > 0.01537841512
        and entry_body_to_highest_high_body <= 3.287479758
        and entry_body_to_recent_bars_body_average > 2.901790857
        and entry_close_to_lowest_low_recovery <= 3.464285731
        and entry_rejection_pressure <= 0.1654646024
        and entry_volume_spike_without_high_context <= 3.849831343
        and failed_attempts_pressure <= 0.7391435802
        and gains_until_entry_bar > 0.1546464488
        and highest_high_quality <= 13.61110258
        and histogram_changed_to_positive_direction_vs_negative_pct <= 1.75
        and minutes_since_market_open <= 191
        and strong_vwap_volume_reentry <= 0.5
    ):
        return True

    if (
        clean_breakout_efficiency > 0.5
        and current_day_ema_20_to_recent_days_ema_20 <= 1.571746111
        and entry_extension_pressure <= 0.3833960891
        and entry_upper_wick_to_recent_upper_wick_average <= 0.6057751775
        and minutes_since_market_open <= 29.5
        and previous_bar_volume_to_its_previous_volume <= 1.556341767
        and profit_since_open_to_bars_count_since_open > 0.007602220634
        and uptrend_histogram_vs_downtrend_since_highest_high <= 0.6339712739
    ):
        return True

    if (
        entry_bar_close_to_highest_high <= 1.043531597
        and entry_bar_low_to_ema_9 > 1.011304021
        and entry_bar_vwap_to_ema_20 > 0.9603820443
        and entry_body_to_highest_high_body <= 17.125
        and fake_reclaim_pressure <= 0.4190528095
        and gains_since_lowest_low <= 0.1707759276
        and lowest_low_to_entry_elapsed_minutes <= 76
        and previous_bar_close_to_highest_high <= 1.007362843
        and previous_bar_high_to_highest_high > 0.9852338731
    ):
        return True

    if (
        bars_since_lowest_low_to_entry <= 3.5
        and current_day_ema_9_to_recent_days_ema_9 <= 3.498072624
        and entry_bar_ema_9_to_ema_20 <= 1.029673398
        and entry_bar_lower_wick <= 0.6599602103
        and entry_body_to_highest_high_body <= 1.53372848
        and entry_breakout_efficiency_from_ema_9 <= 0.7222301364
        and entry_close_to_previous_bar_close <= 1.113800228
        and entry_close_to_vwap > 1.096868455
        and entry_followthrough_after_near_reclaim <= 1.390912592
        and failed_attempts_pressure <= 1.269806921
        and gains_until_entry_bar > 0.2242122218
        and highest_high_to_entry_elapsed_minutes <= 7.5
        and volume_confirmation_quality > 0.1984702945
        and volume_confirmation_quality <= 1.750842631
    ):
        return True

    if (
        bars_since_highest_high_to_bars_before > 0.003858599113
        and controlled_volume_entry_quality > 0.2726772875
        and current_day_ema_9_to_recent_days_ema_9 > 1.300430179
        and current_day_low_to_ema_9 <= 1.056851625
        and entry_bar_body > 0.5084751248
        and entry_bar_body <= 0.9942080677
        and entry_body_to_highest_high_body <= 3.574490666
        and entry_close_to_lowest_low_recovery <= 1.293169022
        and entry_close_to_previous_bar_high <= 1.551721752
        and entry_close_to_vwap <= 1.69347626
        and entry_upper_wick_to_recent_upper_wick_average <= 0.7305086255
        and entry_volume_price_efficiency <= 1.469515085
        and entry_volume_spike_without_high_context > 0.06084682234
        and pullback_health <= 15.80405378
        and volume_confirmation_quality > 0.05133007467
    ):
        return True

    if (
        entry_bar_low_to_ema_9 > 1.005613983
        and entry_bar_macd_to_previous <= 1.187287331
        and entry_bar_volume_to_recent_bars_average <= 2.043838024
        and entry_bar_volume_to_volume_average <= 3.235146523
        and entry_extension_pressure > 0.08043476939
        and macd_recovery_age_quality > 1.223587573
        and minutes_since_market_open <= 325
        and previous_bar_volume_to_its_previous_volume <= 2.394884944
    ):
        return True

    if (
        entry_bar_body > 0.743615061
        and entry_bar_movement_recent_bars_average > 3.233096957
        and highest_high_to_entry_elapsed_minutes > 13.5
        and highest_high_to_entry_elapsed_minutes <= 72
        and previous_bar_close_to_highest_high > 0.9859834909
        and previous_bar_high_to_highest_high > 0.986841917
        and uptrend_histogram_vs_downtrend_since_highest_high <= 0.5080645084
        and volume_confirmation_quality > 0.08617626131
        and volume_since_highest_high_to_volume_before <= 0.1821945831
    ):
        return True

    if (
        current_day_vwap_to_recent_days > 0.9087890983
        and entry_bar_histogram_to_previous > 0.9761474133
        and entry_bar_volume_to_volume_average > 2.204502106
        and entry_body_to_recent_bars_body_average <= 7.701242447
        and entry_close_to_vwap > 1.117941022
        and failed_pressure_to_followthrough <= 0.9336367249
        and macd_recovery_followthrough_quality > 0.3087845445
        and near_high_weak_followthrough > 0.5134474933
        and pullback_depth_vs_pre_high_move <= 0.55175367
    ):
        return True

    if (
        entry_bar_ema_9_to_vwap <= 1.202802122
        and entry_bar_histogram_to_previous <= 0.9257348776
        and entry_bar_upper_wick > 0.1706150174
        and entry_bar_volume_to_volume_average <= 5.824245691
        and entry_body_to_previous_bar_body <= 7.488095284
        and highest_high_quality <= 61.52493095
        and near_high_weak_followthrough > 0.6182557344
        and pre_market_gains > -0.04148284346
        and previous_bar_volume_to_its_previous_volume <= 1.018489897
        and profit_since_open_to_bars_count_since_open > 0.001342823904
        and volume_confirmation_quality > 0.7366503775
    ):
        return True

    if (
        current_day_ema_20_to_recent_days_ema_20 <= 1.09963274
        and current_day_ema_9_to_recent_days_ema_9 <= 2.082899332
        and distance_from_highest_high > 3.5
        and entry_bar_body > 0.6028552651
        and entry_bar_volume > 45407.84961
        and entry_bar_volume_to_highest_volume_in_pullback <= 1.514511704
        and entry_close_position_vs_previous_close_position > 0.9143256843
        and entry_close_strength_to_highest_high_close_strength <= 3.367026925
        and entry_upper_wick_to_recent_upper_wick_average <= 0.9606960416
        and gains_since_lowest_low <= 0.4150217921
        and gains_until_entry_bar > 0.3657626063
        and macd_recovery_age_quality > 0.3420196772
        and uptrend_histogram_vs_downtrend_since_highest_high <= 0.4713740498
        and volume_since_highest_high_to_volume_before > 0.5385022759
    ):
        return True

    if (
        current_day_ema_9_to_ema_20 > 1.137403965
        and entry_bar_body > 0.8267814219
        and entry_bar_low_to_ema_9 <= 1.007787764
        and entry_bar_volume_to_highest_volume_in_pullback > 0.690567106
        and entry_bar_volume_to_recent_bars_average > 4.527231693
        and entry_close_to_vwap > 1.102737606
        and failed_attempts_pressure <= 0.3054267168
        and previous_bar_close_to_highest_high > 0.8925486207
        and profit_since_open_to_bars_count_since_open > 0.001178309729
        and reclaim_close_strength_since_highest_high > 0.1046954133
        and volume_confirmation_quality > 0.1217596047
    ):
        return True

    if (
        current_day_ema_9_to_ema_20 <= 1.187453568
        and current_day_low_to_ema_9 > 0.378665641
        and entry_bar_volume_to_highest_volume_in_pullback > 1.200713217
        and entry_bar_vwap_to_ema_20 <= 0.962839365
        and entry_rejection_pressure > 0.3067124039
        and lowest_low_to_entry_elapsed_minutes > 3.5
        and previous_bar_close_to_highest_high > 0.912048161
        and previous_bar_high_to_highest_high <= 0.9969585836
        and reclaim_speed_from_lowest_low <= 0.2803645432
    ):
        return True

    if (
        current_day_low_to_ema_9 <= 1.288312078
        and emas_distances_to_recent_bars_ema_distances <= 0.2679452002
        and entry_bar_lower_wick <= 0.4178787917
        and entry_bar_movement_recent_bars_average <= 197.3500004
        and entry_body_to_highest_high_body <= 24.63194466
        and entry_breakout_efficiency_from_ema_9 <= 0.6202077866
        and fake_reclaim_pressure <= 0.0006478783325
        and previous_bar_high_to_highest_high > 0.9939716756
    ):
        return True

    if (
        bars_above_volume_average_vs_under_since_highest_high <= 1.75
        and bars_since_lowest_low_to_entry > 1.5
        and current_day_ema_20_to_recent_days_ema_20 > 0.8247537613
        and current_day_ema_20_to_recent_days_ema_20 <= 1.93534708
        and current_day_vwap_to_recent_days <= 3.277980685
        and entry_bar_histogram_to_previous <= 4.934457302
        and entry_bar_low_to_ema_9 > 1.010614336
        and entry_bar_upper_wick > 0.09013540298
        and entry_bar_volume_to_highest_high_volume > 0.5112170875
        and entry_bar_volume_to_recent_bars_average <= 20.25230122
        and entry_bar_vwap_to_ema_20 <= 1.000214934
        and entry_body_to_highest_high_body > 0.3405051157
        and entry_body_to_recent_bars_body_average > 2.172985673
        and entry_breakout_efficiency_from_ema_9 <= 0.7422892749
        and pre_market_gains > -0.07316993549
        and pre_market_gains <= 0.7324700952
        and pre_market_volume > 66784
        and pre_market_volume <= 43360650
        and previous_bar_close_to_highest_high > 0.929792136
        and previous_bar_volume_to_its_previous_volume <= 1.166927993
        and pullback_depth_vs_pre_high_move <= 3.254099846
    ):
        return True

    if (
        bars_above_volume_average_vs_under_since_highest_high <= 4.5
        and bars_since_lowest_low_to_entry <= 92.5
        and current_day_low_to_ema_9 <= 1.181032598
        and entry_bar_histogram_to_highest_histogram > -0.3280959651
        and entry_bar_volume_to_recent_bars_average > 1.936686993
        and entry_bar_vwap_to_ema_20 <= 1.036588609
        and entry_body_to_highest_high_body <= 1.912507117
        and entry_body_to_recent_bars_body_average <= 2.526272535
        and gains_since_lowest_low <= 0.5347189903
        and volume_without_macd_confirmation <= 1.428282917
    ):
        return True

    if (
        current_day_volume_to_recent_days_volume <= 3.584108233
        and entry_close_to_vwap <= 1.115306497
        and previous_bar_high_to_highest_high <= 0.9710122943
    ):
        return True

    if (
        crossed_at_least_one_bar_from_recent_bars <= 0.1081556292
        and entry_bar_body > 0.5428281173
        and entry_body_to_recent_bars_body_average <= 16.74114255
        and entry_rejection_pressure > 0.02890593418
        and entry_rejection_pressure <= 0.2128283407
        and histogram_changed_to_positive_direction_vs_negative_pct <= 1.16996461
        and previous_bar_high_to_highest_high > 0.9788089213
        and recent_bars_positive_bars_pct > 0.5727830958
        and reclaim_close_strength_since_highest_high <= 0.7610173772
        and uptrend_histogram_vs_downtrend_since_highest_high > 0.595652981
    ):
        return True

    if (
        bars_since_lowest_low_to_entry <= 92.5
        and current_day_low_to_ema_9 > 0.6863723993
        and entry_bar_low_to_ema_9 > 1.005810797
        and entry_body_to_recent_bars_body_average > 3.449494958
        and entry_close_strength_to_highest_high_close_strength <= 2.242525518
        and entry_rejection_pressure > 0.1779622138
        and previous_bar_high_to_highest_high > 0.9957983196
        and profit_since_open_to_bars_count_since_open > 0.00122638722
    ):
        return True

    if (
        entry_bar_body <= 0.6156505346
        and entry_bar_volume_to_total_volume <= 0.1838549227
        and entry_close_position_vs_previous_close_position <= 0.7276546061
        and previous_bar_close_to_highest_high > 0.9594801962
    ):
        return True

    if (
        bars_above_volume_average_vs_under_since_highest_high <= 0.5322978199
        and controlled_volume_entry_quality <= 3.853291988
        and current_day_ema_9_to_ema_20 <= 1.529024184
        and entry_bar_ema_9_to_vwap > 1.081573904
        and entry_bar_low_to_ema_9 <= 1.006263912
        and entry_bar_volume_to_total_volume > 0.02743789274
        and entry_followthrough_after_near_reclaim > 1.100753486
        and previous_bar_close_to_highest_high <= 0.9764721692
        and volume_confirmation_quality > 0.187183328
    ):
        return True

    if (
        current_day_ema_9_to_ema_20_distance_to_recent_days > 0.7718091905
        and current_day_low_to_ema_9 <= 1.133395135
        and entry_bar_close_to_highest_high <= 1.035342574
        and entry_bar_macd_to_previous > 0.2653241009
        and entry_bar_volume <= 168668.5
        and entry_body_to_highest_high_body > 0.1658333391
        and entry_body_to_previous_bar_body <= 613.7857056
        and entry_body_to_recent_bars_body_average > 2.080657244
        and entry_breakout_efficiency_from_ema_9 > 0.2450819239
        and entry_close_position_vs_previous_close_position <= 1.114959359
        and highest_high_quality <= 10.80067825
        and profit_since_open_to_bars_count_since_open > 0.004119969206
    ):
        return True

    if (
        current_day_ema_9_to_recent_days_ema_9 <= 1.233441174
        and current_day_low_to_ema_9 > 0.6507913172
        and current_day_volume_to_recent_days_volume <= 2595.658142
        and entry_bar_lower_wick > 0.000113610542
        and entry_bar_volume > 42657.5
        and entry_bar_volume_to_recent_bars_average > 0.9890369773
        and entry_close_to_vwap > 1.127638578
        and entry_volume_price_efficiency > 0.05116360821
        and entry_volume_price_efficiency <= 0.118193876
        and gains_since_lowest_low > 0.2282149643
        and reclaim_speed_from_lowest_low <= 2.585227251
        and volume_confirmation_quality <= 0.9990324676
    ):
        return True

    if (
        current_day_ema_20_to_recent_days_ema_20 > 1.181806445
        and entry_bar_close_to_highest_high <= 1.065692842
        and entry_bar_upper_wick <= 0.1467587948
        and entry_bar_volume_to_recent_bars_average > 1.786172926
        and entry_bar_volume_to_total_volume > 0.01543603046
        and entry_bar_vwap_to_ema_20 <= 0.9441494048
        and gains_since_lowest_low <= 0.4574412704
        and lowest_low_to_entry_elapsed_minutes <= 36.5
        and volume_without_macd_confirmation <= 1.511621058
    ):
        return True

    if (
        bars_above_volume_average_vs_under_since_highest_high <= 0.7908653915
        and current_day_volume_to_recent_days_volume <= 393.5019684
        and emas_distances_to_recent_bars_ema_distances > 0.1004347838
        and entry_bar_body > 0.7521432042
        and entry_bar_histogram_to_lowest_histogram <= 2.491627932
        and entry_close_position_vs_previous_close_position <= 1.112148225
        and gains_since_lowest_low > 0.07983461022
        and gains_until_entry_bar > 0.3933193833
        and macd_recovery_age_quality <= 2.453852773
        and macd_recovery_followthrough_quality <= 55.13739204
        and recent_bars_positive_bars_pct <= 0.75
        and uptrend_histogram_vs_downtrend_since_highest_high > 0.1062030084
        and volume_since_highest_high_to_volume_before > 0.03320486471
        and volume_since_lowest_low_to_entry_vs_since_highest_high > 0.2333731651
    ):
        return True

    if (
        current_day_high_to_previous_high > 0.8228242099
        and distance_from_last_negative_macd_bar <= 25
        and entry_bar_lower_wick <= 0.1077453047
        and entry_bar_movement_recent_bars_average > 3.863284588
        and entry_bar_volume <= 42657.5
        and entry_bar_volume_to_highest_volume_in_pullback > 0.6308940053
        and pre_market_gains <= 0.0752125904
        and volume_since_lowest_low_to_entry_vs_since_highest_high > 0.4974430054
    ):
        return True

    if (
        distance_from_last_negative_macd_bar <= 11
        and entry_bar_lower_wick > 0.06952549517
        and entry_bar_open_to_ema_9 <= 1.023573697
        and entry_bar_volume_to_highest_high_volume > 0.6937294304
        and entry_bar_volume_to_previous_bar_volume <= 12.42280722
        and entry_body_to_highest_high_body <= 260.75
        and entry_close_to_vwap > 1.131670415
        and highest_high_quality <= 1.7113114
        and pre_market_gains > 0.07249574363
        and previous_bar_close_to_highest_high <= 0.9722762704
    ):
        return True

    if (
        bars_above_volume_average_vs_under_since_highest_high <= 0.5241998434
        and entry_bar_ema_9_to_vwap > 1.092662632
        and entry_bar_lower_wick > 0.003541076556
        and entry_bar_volume_to_highest_high_volume > 0.5595470667
        and entry_close_to_previous_bar_high > 1.108455241
        and entry_followthrough_after_near_reclaim > 1.149884939
        and lowest_low_to_entry_elapsed_minutes > 42.5
    ):
        return True

    if (
        current_day_ema_20_to_recent_days_ema_20 > 1.260445952
        and current_day_movement_to_recent_days_movement > 1.696864069
        and current_day_movement_to_recent_days_movement <= 7.225411177
        and entry_bar_movement_recent_bars_average > 4.127065063
        and entry_bar_upper_wick > 0.003718244872
        and entry_breakout_efficiency_from_ema_9 <= 0.7960582078
        and entry_close_to_lowest_low_recovery <= 2.191666603
        and highest_high_quality <= 0.8012506664
        and minutes_since_market_open <= 159
        and pre_market_gains <= 0.2754076719
        and profit_since_open_to_bars_count_since_open > 0.0005850728194
    ):
        return True

    if (
        entry_bar_ema_9_to_vwap <= 1.103215933
        and entry_bar_histogram_to_highest_high > 0.6564392149
        and entry_bar_histogram_to_highest_histogram > 0.2851341367
        and entry_bar_histogram_to_highest_histogram <= 1.930927575
        and entry_bar_histogram_to_lowest_histogram <= 1.258744717
        and entry_bar_volume > 26639.09961
        and entry_bar_volume_to_recent_bars_average > 3.540124416
        and entry_bar_volume_to_total_volume <= 0.3286348581
        and entry_bar_vwap_to_ema_20 <= 0.9423939586
        and near_high_weak_followthrough > 0.8381360769
        and price_movement_from_highest_high_to_lowest_low > 0.2085499987
        and recent_bars_up_trend_pct > 0.3500000089
        and reclaim_close_strength_since_highest_high <= 0.7910016179
    ):
        return True

    if (
        entry_bar_body > 0.5363540649
        and entry_breakout_efficiency_from_ema_9 > 0.4215268493
        and highest_high_quality <= 1.241615772
        and previous_bar_close_to_highest_high <= 0.9974049032
        and price_movement_from_highest_high_to_lowest_low <= 2.41474998
        and volume_since_highest_high_to_volume_before > 0.0669577606
        and volume_since_lowest_low_to_entry_vs_since_highest_high > 0.8244231641
        and volume_without_macd_confirmation <= 11.51700687
    ):
        return True

    # Major reject family: weak reclaim / weak breakout / weak extension.
    # These are setups where the candle may look like a reclaim,
    # but breakout efficiency, bounce quality, rejection pressure,
    # or extension quality is structurally weak.
    if (
        (
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
            and gains_since_lowest_low >= 0.038548752834467
            and histogram_changed_to_positive_direction_vs_negative_pct > 1.030952394
            and current_day_ema_9_to_recent_days_ema_9 <= 2.0428084135
            and entry_bar_macd_to_previous <= 1.1608323455
            and pre_market_volume > 6389.9147949219
            and entry_volume_to_highest_volume_in_pullback > 1.0537672043
            and entry_extension_pressure <= 0.2560228407
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
            pre_market_volume > 4998.5
            and current_day_ema_9_to_recent_days_ema_9 <= 1.1541311145
            and entry_bar_ema_9_to_ema_20 > 1.0535026193
            and current_day_movement_to_recent_days_movement <= 7.0314149857
            and entry_bar_volume_to_highest_high_volume <= 1.4427253604
        )
    ):
        return True

    # Major reject family: volume reclaim / pressure failure.
    # These setups show pressure, volume spikes, or close-position expansion,
    # but the followthrough/confirmation structure is still weak.
    if (
        (
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
        highest_high_to_entry_elapsed_minutes <= 4
        and entry_bar_volume_to_total_volume <= 0.0186582446829219
        and entry_bar_close_to_highest_high <= 1.0121
        and entry_bar_open_to_ema_9 >= 1.003
        and current_day_ema_9_to_recent_days_ema_9 <= 4.0
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
        entry_bar_open_to_ema_9 >= 1.02100165
        and entry_bar_close_to_highest_high <= 1.05555555556
        and current_day_ema_9_to_ema_20 >= 1.153187004
        and entry_bar_body <= 0.6721874999999996
        and pullback_health <= 2.6589815963267025
    ):
        return True

    if (
        pullback_depth_vs_pre_high_move <= 0.4368705484108274
        and profit_since_open_to_bars_count_since_open >= 0.00576
        and entry_bar_volume_to_volume_average <= 8.50
    ):
        return True

    if (
        entry_bar_low_to_ema_9 >= 1.0372845392925112
        and entry_bar_histogram_to_lowest_histogram >= 1.266386431558122
        and distance_from_last_negative_macd_bar >= 12
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
        entry_bar_volume_to_total_volume >= 0.1046935351294476
        and entry_bar_vwap_to_ema_20 <= 0.9426331149875774
    ):
        return True

    if (
        reclaim_close_strength_since_highest_high <= 0.0601
        and entry_upper_wick_to_recent_upper_wick_average <= 0.4476
    ):
        return True

    if (
        controlled_volume_entry_quality <= 0.905
        and entry_body_to_previous_bar_body >= 21.15
        and entry_bar_volume_to_previous_bar_volume >= 4.345645918894326
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
        entry_volume_price_efficiency >= 0.8190
        and current_day_volume_to_recent_days_volume >= 131.07
        and distance_from_last_negative_macd_bar >= 12
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

    return False
