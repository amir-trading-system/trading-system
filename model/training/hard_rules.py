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
    fake_reclaim_pressure = features_data["feature_fake_reclaim_pressure"]
    positive_vs_negative_volume_during_pullback = features_data["feature_positive_vs_negative_volume_during_pullback"]
    volume_confirmation_quality = features_data["feature_volume_confirmation_quality"]
    entry_bar_movement_recent_bars_average = features_data["feature_entry_bar_movement_recent_bars_average"]
    distance_from_last_negative_macd_bar = features_data["feature_distance_from_last_negative_macd_bar"]
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
        (
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

    if (
        entry_bar_volume_to_recent_bars_average >= 4.6813
        and reclaim_close_strength_since_highest_high >= 0.5359
        and pullback_health <= 3.72281
        and entry_upper_wick_to_recent_upper_wick_average <= 0.58855
        and entry_close_to_lowest_low_recovery >= 1.34
        and pre_market_gains >= -0.01879
        and previous_bar_volume_to_its_previous_volume >= 0.3763
        and pre_market_volume >= 876.0
    ):
        return True

    if (
        highest_high_to_entry_elapsed_minutes <= 4
        and entry_bar_volume_to_total_volume <= 0.0186582446829219
        and entry_bar_close_to_highest_high <= 1.0121
        and entry_bar_open_to_ema_9 >= 1.003
        and current_day_ema_9_to_recent_days_ema_9 <= 4.0
    ):
        return True

    if (
        (
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
        total_volume <= 339183.0
        and entry_bar_ema_9_to_ema_20 >= 1.0394
        and entry_bar_volume_to_total_volume >= 0.1249
        and previous_bar_high_to_highest_high <= 1.0249
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
        entry_close_to_previous_bar_close <= 1.0102765726681129
        and entry_bar_ema_9_to_ema_20 <= 1.0103896409199724
    ):
        return True

    if (
        current_day_ema_9_to_ema_20 > 2.1
        and entry_volume_price_efficiency <= 0.1312743542123923
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
    weak_wick_volume_rejection = features_data["feature_weak_wick_volume_rejection"]
    failed_attempts_pressure = features_data["feature_failed_attempts_pressure"]
    bars_since_lowest_low_to_entry = features_data["feature_bars_since_lowest_low_to_entry"]
    clean_reentry_confirmation = features_data["feature_clean_reentry_confirmation"]
    crossed_at_least_one_bar_from_recent_bars = features_data["feature_crossed_at_least_one_bar_from_recent_bars"]
    previous_bar_already_crossed_highest_high = features_data["feature_previous_bar_already_crossed_highest_high"]
    strong_vwap_volume_reentry = features_data["feature_strong_vwap_volume_reentry"]
    current_histogram_is_bigger_than_previous = features_data["feature_current_histogram_is_bigger_than_previous"]
    late_chase_after_high = features_data["feature_late_chase_after_high"]

    # Success Pattern 1:
    # Clean high breakout continuation.
    if (
        entry_bar_close_to_highest_high >= 1.047401043
        and entry_bar_histogram_to_previous <= 0.9876351128
        and current_day_ema_9_to_ema_20 >= 1.047288046
        and total_volume >= 604175
        and (
            entry_volume_price_efficiency <= 0.7632405201
            or distance_from_last_negative_macd_bar <= 11
        )
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
        and (
            entry_volume_price_efficiency <= 0.757661104
            or distance_from_last_negative_macd_bar <= 11
        )
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
        and (
            entry_bar_volume > 155009.25
            or current_day_ema_20_to_recent_days_ema_20 <= 1.056790182
            or entry_bar_open_to_ema_9 <= 1.0051742
            or gains_since_lowest_low <= 0.0664616589
        )
        and entry_bar_histogram_to_previous <= 1.267360974621521
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
        and (
            volume_since_lowest_low_to_entry_vs_since_highest_high <= 0.9289029302
            or entry_bar_movement_recent_bars_average <= 7.072084165
        )
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
        and entry_breakout_efficiency_from_ema_9 > 0.28193128446857685
        and (
            entry_breakout_efficiency_from_ema_9 <= 0.4935715804
            or reclaim_close_strength_since_highest_high <= 0.4322637363
            or current_day_ema_9_to_recent_days_ema_9 <= 1.708970385
            or entry_volume_price_efficiency > 0.2126894303
        )
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
        and pre_market_volume <= 24508381.2
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
        and (
            volume_since_lowest_low_to_entry_vs_since_highest_high <= 0.7353464202
            or clean_breakout_efficiency <= 0
            or entry_bar_histogram_to_previous <= 0.8751089841
        )
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
        and (
            entry_volume_price_efficiency <= 0.16389987
            or entry_breakout_efficiency_from_ema_9 > 0.3063767961
        )
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
        and (
            reclaim_speed_from_lowest_low <= 0.6929185565
            or entry_volume_spike_without_high_context > 1.295573914
            or entry_body_to_recent_bars_body_average <= 1.189382887
            or current_day_ema_9_to_ema_20 <= 0.9967936267
        )
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
        and (
            previous_bar_high_to_highest_high > 0.9887115942
            or entry_bar_close_to_highest_high > 1.016633188
            or entry_bar_volume > 79504.66
        )
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
        and entry_bar_close_to_highest_high <= 1.106389022
        and entry_breakout_efficiency_from_ema_9 > 0.23894240653459617
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
        and current_day_low_to_ema_9 <= 1.01415676
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
        and current_day_high_to_previous_high > 1.0389189189189187
        and (
            entry_upper_wick_to_recent_upper_wick_average <= 1.489878601
            or entry_volume_price_efficiency <= 0.0914612848
            or (
                bars_since_highest_high_to_bars_before > 0.03194444444
                and current_day_ema_20_to_recent_days_ema_20 <= 1.168615583
            )
        )
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
        and late_chase_after_high <= 0
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
        and (
            entry_bar_vwap_to_ema_20 > 0.9331148889
            or current_day_volume_to_recent_days_volume <= 422.9847087
            or current_day_movement_to_recent_days_movement <= 11.05521599
            or controlled_volume_entry_quality <= 172.7556804
            or (
                current_day_volume_to_recent_days_volume <= 950.425369
                and current_day_ema_9_to_ema_20 <= 1.084503536
            )
        )
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
        and (
            entry_bar_volume_to_volume_average > 2.80820461
            or entry_bar_open_to_ema_9 > 1.01936471
            or pullback_depth_vs_pre_high_move > 1.733580424
            or entry_bar_volume_to_total_volume <= 0.0192017821
        )
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
        and (
            entry_bar_volume_to_highest_high_volume <= 1.368278618
            or current_day_ema_20_to_recent_days_ema_20 <= 1.030645218
            or entry_bar_movement_recent_bars_average <= 3.982817294
            or entry_bar_lower_wick > 0.1253896104
        )
        and entry_volume_spike_without_high_context <= 8.057409172757124
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
        and (
            emas_distances_to_recent_bars_ema_distances > 0.0933982807
            or current_day_ema_9_to_ema_20 <= 1.082003055
        )
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
        and failed_pressure_to_followthrough <= 0.5579329452
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
        and controlled_volume_entry_quality > 0.26191178523047526
        and entry_close_strength_to_highest_high_close_strength > 1.1229946524064298
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
        and pullback_depth_vs_pre_high_move <= 5.122711300887382
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
        and entry_bar_low_to_ema_9 > 0.9972093493205755
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
        and uptrend_histogram_vs_downtrend_since_highest_high <= 0.2307692307692307
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
        and failed_pressure_to_followthrough <= 0.4069854363632191
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
        and (
            entry_body_to_recent_bars_body_average <= 8.434378194
            or previous_bar_volume_to_its_previous_volume > 0.906032568
        )
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
        and entry_bar_histogram_to_highest_histogram <= 1.377835226325808
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
        and entry_close_position_vs_previous_close_position > 0.899350649350649
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
        and entry_bar_volume_to_highest_volume_in_pullback > 1.0192219262524285
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

    # Mined Remaining Positive Pattern:
    # mined_remaining_low_rejection_volume_base
    # Covers: 16 positives / 0 FP
    # Includes: 3 currently untagged positives, 13 already-tagged positives
    # Conditions: 12
    if (
        weak_wick_volume_rejection <= 0.8267089309
        and entry_volume_price_efficiency <= 13.54870455
        and current_day_volume_to_recent_days_volume <= 757.3834509
        and current_day_ema_9_to_recent_days_ema_9 <= 2.225949322
        and current_day_ema_20_to_recent_days_ema_20 <= 1.075124718
        and entry_bar_lower_wick > 0.006737036502
        and entry_bar_ema_9_to_ema_20 <= 1.06134999
        and failed_attempts_pressure <= 0.9366171075
        and bars_since_lowest_low_to_entry > 11.68045476
        and volume_since_lowest_low_to_entry_vs_since_highest_high > 0.5967076417
        and profit_since_open_to_bars_count_since_open > 0.00546872876
        and entry_bar_volume_to_volume_average <= 8.764365613
    ):
        score += 1
        reasons.append("mined_remaining_low_rejection_volume_base")

    # Mined Remaining Positive Pattern:
    # mined_remaining_controlled_rejection_body_reclaim
    # Covers: 13 positives / 0 FP
    # Includes: 3 currently untagged positives, 10 already-tagged positives
    # Conditions: 11
    if (
        weak_wick_volume_rejection <= 0.4675156737
        and clean_breakout_efficiency <= 0.6213551525
        and entry_rejection_pressure > 0.09344328609
        and entry_rejection_pressure <= 0.7751065391
        and entry_followthrough_after_near_reclaim <= 1.58449653
        and current_day_movement_to_recent_days_movement <= 40.66453227
        and entry_bar_body > 0.451868423
        and entry_bar_upper_wick <= 0.3756447434
        and gains_since_lowest_low > 0.3931919675
        and distance_from_last_negative_macd_bar <= 11.62031027
        and pre_market_volume <= 11956998.67
    ):
        score += 1
        reasons.append("mined_remaining_controlled_rejection_body_reclaim")

    # Mined Remaining Positive Pattern:
    # mined_remaining_histogram_vwap_reclaim
    # Covers: 13 positives / 0 FP
    # Includes: 3 currently untagged positives, 10 already-tagged positives
    # Conditions: 12
    if (
        volume_confirmation_quality <= 1.00665296
        and current_day_vwap_to_recent_days <= 3.087522314
        and current_day_high_to_previous_high <= 4.236543187
        and entry_bar_upper_wick <= 0.1416590098
        and entry_bar_lower_wick <= 0.5526584537
        and entry_bar_ema_9_to_ema_20 > 1.010502795
        and entry_breakout_efficiency_from_ema_9 > -10.91856465
        and recent_bars_up_trend_pct <= 0.5219878486
        and reclaim_speed_from_lowest_low <= 10.73887275
        and entry_bar_vwap_to_ema_20 <= 0.9723256055
        and entry_bar_histogram_to_highest_histogram <= 10.67842787
        and histogram_changed_to_positive_direction_vs_negative_pct > 1.074236088
        and controlled_volume_entry_quality <= 79.51599724742799
    ):
        score += 1
        reasons.append("mined_remaining_histogram_vwap_reclaim")

    # Mined Remaining Positive Pattern:
    # mined_remaining_clean_reentry_volume_balance
    # Covers: 11 positives / 0 FP
    # Includes: 3 currently untagged positives, 8 already-tagged positives
    # Conditions: 10
    if (
        clean_reentry_confirmation > 0.1018242022
        and macd_recovery_age_quality <= 35.56919472
        and volume_confirmation_quality <= 3.90772414
        and entry_bar_low_to_ema_9 > 0.9657317152
        and crossed_at_least_one_bar_from_recent_bars > 0.2646963584
        and previous_bar_close_to_highest_high <= 1.008240985
        and reclaim_close_strength_since_highest_high > 0.6533897158
        and entry_bar_volume_to_volume_average <= 3.029036107
        and positive_vs_negative_volume_during_pullback > 0.9680152797
        and positive_vs_negative_volume_during_pullback <= 2.122585019
    ):
        score += 1
        reasons.append("mined_remaining_clean_reentry_volume_balance")

    # Mined Remaining Positive Pattern:
    # mined_remaining_high_ema_body_reclaim
    # Covers: 8 positives / 0 FP
    # Includes: 3 currently untagged positives, 5 already-tagged positives
    # Conditions: 12
    if (
        clean_breakout_efficiency <= 0.5521400336
        and volume_without_macd_confirmation <= 1.189778951
        and macd_recovery_followthrough_quality <= 42.03586994
        and current_day_low_to_ema_9 <= 1.290495366
        and entry_bar_close_to_highest_high > 1.026396429
        and entry_bar_lower_wick > 0.02515218016
        and entry_bar_open_to_ema_9 <= 1.034347602
        and entry_bar_ema_9_to_ema_20 > 1.041769086
        and previous_bar_already_crossed_highest_high <= 0.1742370134
        and previous_bar_close_to_highest_high <= 1.009323884
        and profit_since_open_to_bars_count_since_open <= 0.00866881372
        and entry_bar_volume_to_recent_bars_average <= 2.227198621
    ):
        score += 1
        reasons.append("mined_remaining_high_ema_body_reclaim")

    # Mined Remaining Positive Pattern:
    # mined_remaining_clean_breakout_failed_pressure_reclaim
    # Covers: 8 positives / 0 FP
    # Includes: 3 currently untagged positives, 5 already-tagged positives
    # Conditions: 12
    if (
        clean_breakout_efficiency > 0.8679911321
        and failed_pressure_to_followthrough <= 0.2806502301
        and current_day_volume_to_recent_days_volume <= 2151.330641
        and current_day_ema_9_to_ema_20 <= 2.068578148
        and gains_until_entry_bar > 0.6508998443
        and gains_until_entry_bar <= 3.315219202
        and failed_attempts_pressure > 0.2393804472
        and entry_body_to_recent_bars_body_average <= 28.41616542
        and highest_high_to_entry_elapsed_minutes <= 289.5805694
        and entry_close_to_lowest_low_recovery <= 2.556267822
        and bars_since_highest_high_to_bars_before <= 0.2501828326
        and distance_from_last_negative_macd_bar <= 7.587303113
    ):
        score += 1
        reasons.append("mined_remaining_clean_breakout_failed_pressure_reclaim")

    # Mined Remaining Positive Pattern:
    # mined_remaining_compressed_body_volume_reclaim
    # Covers: 11 positives / 0 FP
    # Includes: 2 currently untagged positives, 9 already-tagged positives
    # Conditions: 8
    if (
        entry_bar_body <= 0.7768401479
        and entry_bar_ema_9_to_ema_20 <= 1.021455112
        and entry_bar_movement_recent_bars_average > 4.413576269
        and recent_bars_up_trend_pct <= 0.4243145738
        and entry_close_to_previous_bar_close > 1.018255787
        and positive_vs_negative_volume_during_pullback <= 1.14657416
        and entry_bar_volume_to_previous_bar_volume > 1.725867421
        and entry_bar_volume_to_previous_bar_volume <= 47.81485838
        and controlled_volume_entry_quality > 0.19849641316811606
    ):
        score += 1
        reasons.append("mined_remaining_compressed_body_volume_reclaim")

    # Mined Remaining Positive Pattern:
    # mined_remaining_clean_reentry_fake_pressure_reclaim
    # Covers: 8 positives / 0 FP
    # Includes: 3 currently untagged positives, 5 already-tagged positives
    # Conditions: 7
    if (
        clean_reentry_confirmation > 0.7113957134
        and near_high_weak_followthrough <= 0.9531700096
        and fake_reclaim_pressure > 0.4975582556
        and current_day_low_to_ema_9 > 0.8086961169
        and entry_bar_movement_recent_bars_average > 2.936756911
        and entry_breakout_efficiency_from_ema_9 > 0.487023271
        and previous_bar_high_to_highest_high <= 1.026179614
    ):
        score += 1
        reasons.append("mined_remaining_clean_reentry_fake_pressure_reclaim")

    # Mined Final Positive Pattern:
    # mined_final_body_high_reclaim_balance
    # Covers: 13 positives / 0 FP
    # Includes: 3 currently untagged positives, 10 already-tagged positives
    # Conditions: 6
    if (
        current_day_vwap_to_recent_days <= 3.0883252621
        and entry_body_to_highest_high_body > 0.7158285677
        and entry_body_to_previous_bar_body <= 1.3461538553
        and entry_close_position_vs_previous_close_position > 0.8199965954
        and entry_close_to_previous_bar_high <= 1.022669971
        and volume_since_lowest_low_to_entry_vs_since_highest_high <= 0.9546654224
    ):
        score += 1
        reasons.append("mined_final_body_high_reclaim_balance")

    # Mined Final Positive Pattern:
    # mined_final_histogram_volume_reclaim
    # Covers: 7 positives / 0 FP
    # Includes: 3 currently untagged positives, 4 already-tagged positives
    # Conditions: 13
    if (
        current_day_ema_20_to_recent_days_ema_20 > 0.8869609237
        and current_day_movement_to_recent_days_movement > 0.6063295007
        and entry_bar_histogram_to_highest_histogram > 0.5869852006
        and entry_bar_upper_wick <= 0.3582621068
        and entry_bar_volume_to_recent_bars_average > 1.035813272
        and entry_bar_volume_to_recent_bars_average <= 1.4356510639
        and entry_bar_vwap_to_ema_20 > 0.948479861
        and entry_bar_vwap_to_ema_20 <= 1.0228150487
        and entry_body_to_recent_bars_body_average > 0.7887629867
        and entry_rejection_pressure <= 0.668664068
        and entry_volume_price_efficiency > 0.021060274
        and failed_attempts_pressure > 0.5981762707
        and macd_recovery_followthrough_quality <= 47.7695560455
    ):
        score += 1
        reasons.append("mined_final_histogram_volume_reclaim")

    # Mined Final Positive Pattern:
    # mined_final_early_uptrend_low_rejection_reclaim
    # Covers: 8 positives / 0 FP
    # Includes: 2 currently untagged positives, 6 already-tagged positives
    # Conditions: 13
    if (
        bars_above_volume_average_vs_under_since_highest_high <= 1.2346978034
        and entry_bar_histogram_to_highest_histogram <= 47.1856528401
        and entry_bar_upper_wick <= 0.5343652246
        and entry_bar_volume_to_highest_volume_in_pullback <= 0.9580695784
        and entry_close_to_previous_bar_high <= 2.6711447535
        and entry_rejection_pressure <= 0.0750613524
        and entry_volume_price_efficiency <= 13.6050896871
        and gains_since_lowest_low <= 0.8451647291
        and histogram_changed_to_positive_direction_vs_negative_pct > 0.7944070617
        and minutes_since_market_open <= 72.0747458479
        and recent_bars_up_trend_pct > 0.684337374
        and strong_vwap_volume_reentry <= 0.7865783888
        and volume_confirmation_quality <= 12.316440904
        and volume_without_macd_confirmation <= 5.745776039866115
    ):
        score += 1
        reasons.append("mined_final_early_uptrend_low_rejection_reclaim")

    # Mined Final Positive Pattern:
    # mined_final_high_quality_wick_reclaim
    # Covers: 14 positives / 0 FP
    # Includes: 2 currently untagged positives, 12 already-tagged positives
    # New untagged gain after earlier rules: 1
    # Conditions: 12
    if (
        current_histogram_is_bigger_than_previous <= 0.9152817702
        and entry_bar_upper_wick > 0.1627729364
        and entry_bar_volume_to_highest_high_volume <= 2.2357392947
        and entry_body_to_previous_bar_body > -2.2648822603
        and entry_close_position_vs_previous_close_position <= 10.1107738003
        and entry_rejection_pressure <= 0.5744646023
        and highest_high_quality > 11.9448701502
        and macd_recovery_age_quality <= 23.4001856429
        and pre_market_gains <= 3.8039290651
        and recent_bars_positive_bars_pct <= 0.6590139116
        and reclaim_speed_from_lowest_low <= 1.3731545122
        and weak_wick_volume_rejection <= 0.6614048959
    ):
        score += 1
        reasons.append("mined_final_high_quality_wick_reclaim")

    # Mined Final Positive Pattern:
    # mined_final_high_recent_day_quiet_volume_reclaim
    # Covers: 4 positives / 0 FP
    # Includes: 2 currently untagged positives, 2 already-tagged positives
    # New untagged gain after earlier rules: 1
    # Conditions: 13
    if (
        clean_reentry_confirmation <= 0.7837463048
        and current_day_high_to_previous_high <= 3.9678742432
        and current_day_high_to_recent_days_highs > 3.0481580699
        and entry_bar_volume_to_highest_volume_in_pullback <= 0.7926409544
        and entry_close_to_vwap <= 1.8788432603
        and entry_rejection_pressure <= 2.1429751665
        and entry_volume_price_efficiency > -0.0499494257
        and entry_volume_spike_without_high_context <= 5.457498789
        and lowest_low_to_entry_elapsed_minutes <= 43.5558783
        and macd_recovery_age_quality <= 23.036249387
        and pre_market_gains <= 3.772352479
        and volume_confirmation_quality <= 1.2791586105
        and weak_wick_volume_rejection <= 0.2287135754
    ):
        score += 1
        reasons.append("mined_final_high_recent_day_quiet_volume_reclaim")

    # Mined Final Positive Pattern:
    # mined_final_fast_macd_reclaim
    # Covers: 17 positives / 0 FP
    # Includes: 1 currently untagged positive, 16 already-tagged positives
    # New untagged gain after earlier rules: 1
    # Conditions: 13
    if (
        crossed_at_least_one_bar_from_recent_bars > 0.4007793737
        and distance_from_last_negative_macd_bar <= 5.3003959517
        and emas_distances_to_recent_bars_ema_distances <= 0.5944158853
        and entry_bar_body > 0.36835787
        and entry_bar_macd_to_previous > 0.5655529421
        and gains_until_entry_bar <= 5.075028692
        and previous_bar_already_crossed_highest_high <= 0.0892275428
        and recent_bars_up_trend_pct > 0.7804952703
        and reclaim_close_strength_since_highest_high > 0.0711445648
        and reclaim_close_strength_since_highest_high <= 0.8034318679
        and reclaim_speed_from_lowest_low <= 0.5568540645
        and strong_vwap_volume_reentry <= 0.4440994903
        and uptrend_histogram_vs_downtrend_since_highest_high <= 2.6369301708
        and pullback_health > 0.5648384804851242
    ):
        score += 1
        reasons.append("mined_final_fast_macd_reclaim")

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
        "broad_reset_buyer_volume": {
            "broad_reset_buyer_volume_confirmation",
            "broad_reset_efficiency_reclaim",
        },
    }

    soft_groups = {
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
        "mined_remaining_feature_only_rescue": {
            "mined_remaining_low_rejection_volume_base",
            "mined_remaining_controlled_rejection_body_reclaim",
            "mined_remaining_histogram_vwap_reclaim",
            "mined_remaining_clean_reentry_volume_balance",
            "mined_remaining_high_ema_body_reclaim",
            "mined_remaining_clean_breakout_failed_pressure_reclaim",
            "mined_remaining_compressed_body_volume_reclaim",
            "mined_remaining_clean_reentry_fake_pressure_reclaim",
        },
        "mined_final_feature_only_rescue": {
            "mined_final_body_high_reclaim_balance",
            "mined_final_histogram_volume_reclaim",
            "mined_final_early_uptrend_low_rejection_reclaim",
            "mined_final_high_quality_wick_reclaim",
            "mined_final_high_recent_day_quiet_volume_reclaim",
            "mined_final_fast_macd_reclaim",
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
