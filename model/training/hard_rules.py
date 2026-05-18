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
    positive_vs_negative_volume_during_pullback = features_data["feature_positive_vs_negative_volume_during_pullback"]
    histogram_changed_to_positive_direction_vs_negative_pct = features_data["feature_histogram_changed_to_positive_direction_vs_negative_pct"]
    macd_recovery_age_quality = features_data["feature_macd_recovery_age_quality"]
    previous_bar_close_to_highest_high = features_data["feature_previous_bar_close_to_highest_high"]
    failed_attempts_pressure = features_data["feature_failed_attempts_pressure"]
    uptrend_histogram_vs_downtrend_since_highest_high = features_data["feature_uptrend_histogram_vs_downtrend_since_highest_high"]
    entry_volume_spike_without_high_context = features_data["feature_entry_volume_spike_without_high_context"]
    inefficient_breakout_extension = features_data["feature_inefficient_breakout_extension"]
    fake_reclaim_pressure = features_data["feature_fake_reclaim_pressure"]
    volume_confirmation_quality = features_data["feature_volume_confirmation_quality"]

    ############### ---------------- broader rules ---------------- ###############

    # Reject: entry is above EMA9 but the bounce from low is weak,
    # previous-high reclaim is stretched, and MACD recovery quality is limited.
    # This is a broad weak-reclaim / weak-bounce continuation failure pattern.
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

    # Reject: tiny bounce from low,
    # entry reclaims/stretches above previous high,
    # but followthrough after near-reclaim is already weak/extended.
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

    # Reject: weak bounce from low,
    # compressed high-to-low movement,
    # entry remains close above EMA9,
    # and the retest happens too close to the highest-high event.
    if (
        entry_bar_low_to_ema_9 > 1.0102430582
        and gains_since_lowest_low <= 0.1303373128
        and entry_bar_upper_wick > 0.0226323679
        and entry_bar_open_to_ema_9 <= 1.0409949422
        and price_movement_from_highest_high_to_lowest_low <= 0.3924999982
        and bars_since_highest_high_to_bars_before <= 0.0039101022
        and highest_high_quality > 0.5145126132018534
    ):
        return True

    # Reject: weak bounce from low,
    # stretched reclaim above previous high,
    # older MACD recovery,
    # and weak near-high followthrough.
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

    # Reject: entry low is not meaningfully above EMA9,
    # broader VWAP/high context is elevated,
    # but pullback health is weak.
    if (
        entry_bar_low_to_ema_9 <= 1.0070604682
        and current_day_vwap_to_recent_days > 1.2754222155
        and current_day_high_to_recent_days_highs > 1.3807946444
        and entry_breakout_efficiency_from_ema_9 <= 0.8878360987
        and recent_bars_positive_bars_pct <= 0.75
        and current_day_vwap_to_recent_days <= 2.0629848242
        and gains_since_lowest_low > 0.2177865580
        and pullback_health <= 4.0576481819
        and current_day_ema_20_to_recent_days_ema_20 > 1.0366392136
    ):
        return True

    # Reject: entry low is not meaningfully above EMA9,
    # breakout efficiency is not exceptional,
    # broader EMA9 context is weak,
    # and the entry body is weak versus the highest-high candle.
    if (
        entry_bar_low_to_ema_9 <= 1.0070604682
        and entry_breakout_efficiency_from_ema_9 <= 0.9983366132
        and current_day_ema_9_to_recent_days_ema_9 <= 0.9913356900
        and entry_body_to_highest_high_body <= 4.6936500072
        and entry_rejection_pressure > 0.0012531328
        and entry_bar_vwap_to_ema_20 >= 0.7832668372258171
    ):
        return True

    # Reject: entry is above EMA9 after a weak bounce,
    # but close strength versus the highest-high candle is weak
    # and extension pressure is not strong enough.
    if (
        entry_bar_low_to_ema_9 > 1.0070604682
        and gains_since_lowest_low <= 0.1303373128
        and entry_close_strength_to_highest_high_close_strength <= 1.1170654297
        and entry_extension_pressure <= 0.4081256241
    ):
        return True

    # Reject: entry is extended above VWAP in a non-exceptional VWAP context,
    # but the body/volume quality is not strong enough to justify the chase.
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

    # Reject: trade already has meaningful gains,
    # but breakout efficiency is weak and day-volume context is not strong enough.
    if (
        entry_breakout_efficiency_from_ema_9 <= 0.4921557903
        and gains_until_entry_bar > 0.2806035727
        and current_day_volume_to_recent_days_volume <= 5.4054927826
        and pre_market_volume > 19492
        and current_day_low_to_ema_9 <= 1.1302526593
        and entry_close_strength_to_highest_high_close_strength <= 3.1998206377
    ):
        return True

    # Reject: large-volume setup with elevated EMA9/EMA20 entry structure,
    # but followthrough after near reclaim remains limited.
    if (
        entry_bar_ema_9_to_ema_20 > 1.0544950962
        and current_day_high_to_recent_days_highs <= 1.879216373
        and total_volume > 7206239
        and entry_followthrough_after_near_reclaim <= 1.4948156476
    ):
        return True

    # Reject: moderate current-day extension with strong EMA9/EMA20 entry structure,
    # but the move is not exceptional versus recent days.
    # This catches the new "controlled continuation / not enough real breakout quality" FP pattern.
    if (
        entry_bar_ema_9_to_ema_20 > 1.0544950962
        and current_day_movement_to_recent_days_movement <= 5.2332162857
        and current_day_high_to_recent_days_highs > 1.4097422957
        and current_day_high_to_recent_days_highs <= 1.9136073589
    ):
        return True

    # Reject: weak VWAP/EMA20 structure after a large current-day move,
    # with controlled gains, weak pullback-volume position,
    # and weak body versus highest-high body
    if (
        entry_bar_vwap_to_ema_20 <= 0.9624572694
        and gains_until_entry_bar <= 1.0722402930
        and entry_volume_to_highest_volume_in_pullback <= 1.8528105021
        and current_day_movement_to_recent_days_movement > 8.3926472664
        and entry_body_to_highest_high_body <= 13.3459329605
        and current_day_vwap_to_recent_days > 1.5232991576
    ):
        return True

    # Reject: shallow pullback, entry stays elevated above EMA9,
    # but volume-price efficiency and histogram confirmation are weak.
    if (
        reclaim_close_strength_since_highest_high <= 0.9412434996
        and weak_wick_volume_rejection <= 0.5
        and pullback_depth_vs_pre_high_move <= 0.5513598025
        and entry_close_to_vwap <= 1.3177151084
        and entry_bar_low_to_ema_9 > 1.0102430583
        and entry_volume_price_efficiency <= 0.0948949792
        and entry_bar_histogram_to_previous <= 1.5178890825
        and entry_body_to_recent_bars_body_average < 15.266666666666838
    ):
        return True

    # Reject: weak broader VWAP/EMA20 context,
    # entry already has meaningful gains,
    # but the entry candle is weak / low-wick continuation
    if (
        entry_bar_vwap_to_ema_20 > 0.9583664536
        and gains_until_entry_bar > 0.3910978436
        and current_day_vwap_to_recent_days <= 1.2782940269
        and current_day_ema_20_to_recent_days_ema_20 <= 1.0701962709
        and entry_bar_lower_wick <= 0.1419752426
    ):
        return True

    # Reject: large volume entry with strong reclaim,
    # but weak follow-through quality and limited pullback health
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

    # Reject: setup is already elevated above EMA9,
    # entry candle shows upper-wick rejection,
    # and followthrough after near-reclaim is stretched
    if (
        entry_bar_upper_wick >= 0.2837
        and current_day_low_to_ema_9 >= 1.1456
        and entry_followthrough_after_near_reclaim >= 1.1020
        and recent_bars_positive_bars_pct <= 0.7
    ):
        return True

    # Reject: reclaim strength and rejection pressure are present,
    # but breakout efficiency remains weak in a non-exceptional VWAP context
    if (
        reclaim_close_strength_since_highest_high >= 0.5555
        and entry_rejection_pressure >= 0.1428
        and entry_breakout_efficiency_from_ema_9 <= 0.6955
        and entry_bar_body >= 0.6666
        and current_day_vwap_to_recent_days <= 2.1286
    ):
        return True

    # Reject: entry is extended above EMA9 after a real bounce,
    # but histogram confirmation is fading and volume is not expanding enough.
    if (
        entry_bar_low_to_ema_9 > 1.0070604682
        and gains_since_lowest_low > 0.13386581469648836
        and histogram_changed_to_positive_direction_vs_negative_pct <= 1.0309523941
        and entry_bar_volume_to_volume_average <= 2.9935019017
        and volume_since_highest_high_to_volume_before <= 0.8390479982
        and entry_bar_ema_9_to_ema_20 > 1.0682371259
        and entry_close_to_previous_bar_high <= 1.3992085457
    ):
        return True

    # Reject: weak breakout efficiency, MACD fade,
    # previous bar failed to hold near the highest-high,
    # and entry volume is concentrated in the pullback area.
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

    # Reject: weak breakout efficiency with MACD fade,
    # prior close is below the high, but entry volume spikes
    # while VWAP/EMA20 structure remains weak.
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

    # Reject: VWAP chase with weak breakout efficiency,
    # enough reclaim strength to look tempting,
    # but failed-attempt pressure is low and trend quality is not enough.
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

    # Reject: VWAP chase with weak breakout efficiency,
    # weak histogram followthrough after the high,
    # and volume rebuild that depends too much on post-high volume.
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

    # Reject: entry low is not meaningfully above EMA9,
    # day context is elevated, but VWAP/EMA20 structure is weak
    # and volume rebuild depends too much on post-high volume.
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

    # Reject: there was a real bounce from the low,
    # but histogram direction/confirmation is not translating into clean continuation,
    # and extension pressure remains weak.
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

    # Reject: immediate retest after highest-high,
    # breakout efficiency exists,
    # but the entry body is weak versus the highest-high candle.
    if (
        entry_breakout_efficiency_from_ema_9 > 0.4910371602
        and bars_since_highest_high_to_bars_before <= 0.0018091702
        and entry_body_to_highest_high_body <= 1.6986946464
        and current_day_movement_to_recent_days_movement > 0.6746948957
    ):
        return True

    # Reject: entry is slightly above EMA9 after a tiny bounce,
    # but upper-wick pressure is unusually high versus recent upper wicks.
    if (
        entry_bar_low_to_ema_9 > 1.0070604682
        and gains_since_lowest_low <= 0.1303373128
        and entry_bar_low_to_ema_9 <= 1.0369659067
        and entry_volume_to_highest_volume_in_pullback <= 2.4220101834
        and entry_upper_wick_to_recent_upper_wick_average > 1.6921178699
    ):
        return True

    # Reject: pullback is deep and histogram bounces,
    # but entry participation is not expanding strongly enough
    # and the full current-day move is still modest
    if (
        entry_body_to_recent_bars_body_average <= 3.138
        and pullback_depth_vs_pre_high_move >= 1.3531
        and entry_bar_volume_to_previous_bar_volume <= 2.0443
        and entry_bar_histogram_to_previous >= 0.5029
        and current_day_movement_to_recent_days_movement <= 6.104
        and pre_market_gains >= -0.0091
    ):
        return True

    # Reject: large high-to-low movement,
    # entry has meaningful upper wick,
    # close position versus previous candle is stretched,
    # and entry volume is large enough relative to total volume
    if (
        price_movement_from_highest_high_to_lowest_low >= 1.3499
        and entry_bar_upper_wick >= 0.1702
        and entry_close_position_vs_previous_close_position >= 1.7663
        and entry_bar_volume_to_total_volume >= 0.02298
    ):
        return True

    # Reject: failed-pressure/followthrough is high,
    # close position is stretched,
    # and volume quality is too controlled/imbalanced
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

    # Reject: weak bounce from lowest low,
    # previous volume support is weak/limited,
    # and entry shows wick rejection without strong highest-high volume confirmation
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

    # Reject: weak bounce above EMA9,
    # almost no positive-vs-negative pullback volume support,
    # and broader EMA structure is not strong enough.
    if (
        pre_market_gains > 0.0056163829285651445
        and entry_bar_low_to_ema_9 > 1.007060468196869
        and positive_vs_negative_volume_during_pullback <= 0.09442323446273804
        and gains_since_lowest_low <= 0.14852026104927063
        and current_day_ema_9_to_ema_20 <= 1.370779812335968
        and current_day_low_to_ema_9 > 0.7675630450248718
    ):
        return True

    # Reject: post-high volume is limited,
    # entry volume is not expanding enough,
    # and bounce from low is already meaningful but inefficient.
    if (
        pre_market_gains <= 0.0056163829285651445
        and price_movement_from_highest_high_to_lowest_low > 0.397149994969368
        and volume_since_highest_high_to_volume_before <= 0.8350349962711334
        and entry_bar_volume_to_previous_bar_volume > 1.1702489852905273
        and gains_since_lowest_low > 0.14865899831056595
        and entry_bar_volume_to_volume_average <= 2.095898747444153
    ):
        return True

    # Reject: compressed high-to-low movement,
    # weak current-day context,
    # low gains into entry,
    # and poor volume-price efficiency.
    if (
        pre_market_gains <= 0.0056163829285651445
        and price_movement_from_highest_high_to_lowest_low <= 0.397149994969368
        and current_day_vwap_to_recent_days <= 2.1310880184173584
        and gains_until_entry_bar <= 0.34598593413829803
        and highest_high_quality > 2.8904706239700317
        and entry_volume_price_efficiency <= 0.04760081134736538
    ):
        return True

    # Reject: elevated current-day context,
    # entry is not cleanly above EMA9,
    # recent positive bars exist,
    # but uptrend quality is not strong enough.
    if (
        pre_market_gains > 0.0056163829285651445
        and entry_bar_low_to_ema_9 <= 1.007060468196869
        and current_day_ema_9_to_recent_days_ema_9 > 0.9913356900215149
        and current_day_high_to_recent_days_highs > 1.3778034448623657
        and current_day_vwap_to_recent_days > 1.4217395186424255
        and recent_bars_positive_bars_pct > 0.75
        and recent_bars_up_trend_pct <= 0.75
    ):
        return True

    # Reject: large day movement + weak bounce after highest-high,
    # entry body looks big compared with previous bar,
    # but the move is still close to the highest-high structure
    # and recent trend participation is not weak enough to save it.
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

    # Reject: entry body explodes relative to recent bodies,
    # but close strength versus the highest-high candle remains weak.
    # Extra VWAP stretch separates it from the positive that looked similar.
    if (
        entry_body_to_recent_bars_body_average >= 9.759273
        and entry_close_strength_to_highest_high_close_strength <= 1.041007
        and entry_close_to_vwap >= 1.1484540592
        and entry_body_to_highest_high_body < 27.43055555555685
    ):
        return True

    # Reject: failed pressure/followthrough setup,
    # controlled volume looks present,
    # but premarket gain context is not strong enough.
    if (
        failed_pressure_to_followthrough >= 0.4017
        and entry_close_position_vs_previous_close_position >= 1.6041
        and bars_above_volume_average_vs_under_since_highest_high <= 0.8334
        and controlled_volume_entry_quality >= 2.2409
        and minutes_since_market_open >= 60
        and current_day_low_to_ema_9 >= 0.8095
        and pre_market_gains <= 0.1956521739
    ):
        return True

    # Reject: large relative volume on entry,
    # but close strength versus the highest-high candle is poor.
    # Requires at least some premarket participation to avoid the positive overlap.
    if (
        entry_close_strength_to_highest_high_close_strength <= 0.947374
        and entry_bar_volume_to_recent_bars_average >= 9.089611
        and pre_market_volume >= 369
    ):
        return True

    # Reject: previous bar already reached/pushed the high,
    # EMA structure is stretched,
    # and entry candle shows rejection versus recent upper wicks
    if (
        previous_bar_high_to_highest_high >= 1.0031150793650794
        and entry_bar_ema_9_to_ema_20 >= 1.053391820032275
        and entry_upper_wick_to_recent_upper_wick_average >= 0.6957268870518433
        and previous_bar_volume_to_its_previous_volume < 1.9726128342701927
    ):
        return True

    # Reject: entry candle is floating above EMA9,
    # but body is weak and entry volume is not strong versus recent bars
    if (
        entry_bar_low_to_ema_9 >= 1.031512679899293
        and entry_bar_body <= 0.7009402985074643
        and entry_bar_volume_to_recent_bars_average <= 2.1133747452245917
    ):
        return True

    # Reject: weak close quality versus highest-high candle,
    # weak entry volume versus previous bar,
    # and entry body is not strong enough
    if (
        entry_close_strength_to_highest_high_close_strength <= 0.6933561644938037
        and entry_bar_volume_to_previous_bar_volume <= 1.9862868213373515
        and entry_bar_body <= 0.7009402985074643
    ):
        return True

    # Reject: almost no post-high volume rebuild,
    # and entry volume does not expand versus previous bar
    if (
        volume_since_highest_high_to_volume_before <= 0.0113413654328
        and entry_bar_volume_to_previous_bar_volume <= 1.37210073325
    ):
        return True

    # Reject: very fast reclaim after highest high,
    # but EMA9 is still weak/below EMA20
    if (
        highest_high_to_entry_elapsed_minutes <= 2
        and current_day_ema_9_to_ema_20 <= 0.933573312373
    ):
        return True

    # Reject: shallow pullback,
    # while entry is already far above VWAP
    if (
        pullback_depth_vs_pre_high_move <= 0.541837652642
        and entry_close_to_vwap >= 1.31664343091
        and pre_market_gains <= 0.5459247224478744
    ):
        return True

    # Reject: recent bars are already strongly uptrending,
    # but entry volume is weak versus average volume
    if (
        recent_bars_up_trend_pct >= 0.9
        and entry_bar_volume_to_volume_average <= 1.8993538884
    ):
        return True

    # Reject: current-day EMA9 context is extremely expanded,
    # but entry volume is weak versus average
    if (
        entry_bar_volume_to_volume_average <= 1.62644665002
        and current_day_ema_9_to_recent_days_ema_9 >= 2.00302421228
    ):
        return True

    # Reject: entry opens stretched above EMA9,
    # but does not clear the previous highest-high strongly enough,
    # while EMA9 is already stretched over EMA20
    if (
        entry_bar_open_to_ema_9 >= 1.02100165
        and entry_bar_close_to_highest_high <= 1.01447752
        and current_day_ema_9_to_ema_20 >= 1.153187004
        and entry_bar_body <= 0.6229021941816995
        and pullback_health <= 2.199284663467352
    ):
        return True

    # Reject: large upper wick after fast profit from open
    if (
        entry_bar_upper_wick >= 0.407658746728
        and profit_since_open_to_bars_count_since_open >= 0.00472397211875
    ):
        return True

    # Reject: weak close-position improvement,
    # with little post-high volume rebuild
    if (
        entry_close_position_vs_previous_close_position <= 0.731694032711
        and volume_since_highest_high_to_volume_before <= 0.144645677467
        and volume_without_macd_confirmation >= 0.7320706574892093
    ):
        return True

    # Reject: weak previous-high reclaim,
    # high breakout-efficiency ratio,
    # but only when controlled-volume quality is weak
    if (
        current_day_high_to_previous_high <= 1.02
        and entry_breakout_efficiency_from_ema_9 > 0.64
        and controlled_volume_entry_quality <= 1.94325300464
        and entry_close_to_vwap <= 1.141160582354013
    ):
        return True

    # Reject: current-day EMA9 is expanded versus recent days,
    # but EMA20 broader context is weak,
    # and entry is not strongly above VWAP
    if (
        current_day_ema_9_to_recent_days_ema_9 >= 1.27426832716
        and current_day_ema_20_to_recent_days_ema_20 <= 1.13188273075
        and entry_bar_ema_9_to_vwap <= 1.04418374495
    ):
        return True

    # Reject: weak volume rebuild from lowest low,
    # weak profit pace from open,
    # and no meaningful premarket strength
    if (
        volume_since_lowest_low_to_entry_vs_since_highest_high <= 0.291147893564
        and profit_since_open_to_bars_count_since_open <= 0.00369869518854
        and pre_market_gains <= 0.00634941981096
    ):
        return True

    # Reject: large absolute entry volume,
    # but weak current-day relative volume,
    # and entry body is not strong versus recent bars
    if (
        entry_bar_volume >= 1130008.45
        and current_day_volume_to_recent_days_volume <= 8.40179578213
        and entry_body_to_recent_bars_body_average <= 3.07563963964
    ):
        return True

    # Reject: recent bars are almost all positive,
    # but the entry body is already large, suggesting chase/late continuation.
    if (
        recent_bars_positive_bars_pct > 0.8499999940
        and entry_bar_body > 0.8969591260
    ):
        return True

    # Reject: previous bar already broke above the old high,
    # and the entry candle shows real rejection pressure
    if (
        entry_rejection_pressure >= 0.5684
        and previous_bar_high_to_highest_high >= 1.0109
    ):
        return True

    # Reject: entry is floating too far above EMA9,
    # while the pullback/reset was too shallow
    if (
        entry_bar_low_to_ema_9 >= 1.0323
        and pullback_depth_vs_pre_high_move <= 0.4322
    ):
        return True

    # Reject: low-liquidity setup where MACD/histogram is already stretched
    if (
        total_volume <= 499196.6
        and entry_histogram_to_highest_histogram >= 2.1306
    ):
        return True

    # Reject: low relative current-day volume,
    # entry candle is floating above EMA9,
    # and EMA9 is stretched above VWAP
    if (
        current_day_volume_to_recent_days_volume <= 5.698130559
        and entry_bar_low_to_ema_9 >= 1.0189563
        and entry_bar_ema_9_to_vwap >= 1.09945013
    ):
        return True

    # Reject: tiny absolute entry volume with very poor price/volume efficiency
    if (
        entry_bar_volume <= 30071.26
        and entry_volume_price_efficiency <= 0.02117
    ):
        return True

    # Reject: entry body is weak and reclaim strength after highest high is poor
    if (
        entry_bar_body <= 0.5157
        and reclaim_close_strength_since_highest_high <= 0.0770
        and volume_without_macd_confirmation > 0.5537641273329578
    ):
        return True

    # Reject: abnormal upper-wick rejection,
    # while the entry body is weak versus the highest-high candle
    if (
        entry_upper_wick_to_recent_upper_wick_average >= 1.5719
        and entry_body_to_highest_high_body <= 0.5112
    ):
        return True

    # Reject: strong/high-quality highest-high area,
    # but the setup gives almost no real pullback before entry
    if (
        highest_high_quality >= 45.2194
        and pullback_depth_vs_pre_high_move <= 0.4973
    ):
        return True

    # Reject: very poor volume-price efficiency,
    # and almost no actual bounce from the pullback low
    if (
        entry_volume_price_efficiency <= 0.01892
        and gains_since_lowest_low <= 0.03203
    ):
        return True

    # Reject: weak body, weak recovery from low,
    # and MACD recovery/follow-through quality is not mature
    if (
        entry_bar_body <= 0.4061
        and entry_close_to_lowest_low_recovery <= 1.1066
        and macd_recovery_followthrough_quality <= 13.9401
    ):
        return True

    # Reject: wick-volume rejection,
    # only when entry volume is clearly weak versus highest-high volume
    if (
        weak_wick_volume_rejection
        and entry_bar_volume_to_highest_high_volume <= 1.10680219491
        and inefficient_breakout_extension < 1.0
        and previous_bar_close_to_highest_high >= 0.9664413613186292
    ):
        return True

    # Reject: early shallow-pullback chase after fast open profit
    if (
        minutes_since_market_open <= 29
        and pullback_depth_vs_pre_high_move <= 0.6014838509
        and profit_since_open_to_bars_count_since_open >= 0.01742149356
        and inefficient_breakout_extension <= 0.0
    ):
        return True

    # Reject: MACD recovery/followthrough score looks large,
    # but the entry histogram is still weak versus the highest-high histogram.
    # This means the recovery score is inflated, while true momentum has not rebuilt.
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

    # Reject: weak broader VWAP context,
    # while current-day EMA9/EMA20 distance is extremely stretched versus recent days.
    # This is a poor-quality intraday stretch where the move is internally extended
    # but not broadly strong versus recent VWAP context.
    if (
        current_day_vwap_to_recent_days <= 1.4039128316808989
        and current_day_ema_9_to_ema_20_distance_to_recent_days >= 7.446534377544922
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
        current_day_volume_to_recent_days_volume <= 1.182418
        and current_day_ema_9_to_ema_20 <= 1.225573
    ):
        return True

    # Reject: recent bars look positive,
    # but entry volume-price efficiency is very weak
    # and premarket participation is low
    if (
        entry_volume_price_efficiency <= 0.02588854677
        and pre_market_volume <= 47862
        and recent_bars_positive_bars_pct >= 0.6
        and entry_close_to_previous_bar_high >= 1.0431372549019609
    ):
        return True

    # Reject: entry low is elevated above EMA9,
    # VWAP is weak versus EMA20,
    # but breakout efficiency is already high
    if (
        current_day_low_to_ema_9 >= 1.358228224
        and entry_bar_vwap_to_ema_20 <= 0.8898687606
        and entry_breakout_efficiency_from_ema_9 >= 0.5188943549
        and pre_market_gains >= 0.2355555555555554
    ):
        return True

    # Reject: large upper-wick rejection + extension pressure
    # in already stretched EMA structure
    if (
        entry_bar_upper_wick >= 0.2987368421
        and entry_extension_pressure >= 0.2814410998
        and current_day_ema_9_to_ema_20 >= 1.2564937075
    ):
        return True

    # Reject: weak VWAP context,
    # entry close is not strong above VWAP,
    # but volume is already spiking versus average
    if (
        current_day_vwap_to_recent_days <= 1.139442758
        and entry_close_to_vwap <= 1.116062675
        and entry_bar_volume_to_volume_average >= 2.449822397
    ):
        return True

    if (
        current_day_movement_to_recent_days_movement >= 4.478947923630989
        and bars_since_highest_high_to_bars_before <= 0.001501164841972015
        and entry_followthrough_after_near_reclaim >= 1.0477563200701343
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
        current_day_movement_to_recent_days_movement >= 21.994522607223317
        and highest_high_to_entry_elapsed_minutes <= 5.0
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
    ):
        return True

    # Reject: high pullback-volume concentration,
    # but weak volume/MACD confirmation
    if (
        entry_volume_to_highest_volume_in_pullback >= 2.3644566162
        and volume_without_macd_confirmation <= 1.3859621588
        and entry_close_to_vwap <= 1.192665838838092
    ):
        return True

    # Reject: huge body versus highest-high body,
    # but pullback was still too shallow
    if (
        entry_body_to_highest_high_body >= 21.0911
        and pullback_depth_vs_pre_high_move <= 0.8421832074
        and entry_close_to_vwap < 1.214043135738546
        and pre_market_gains <= 0.203125
    ):
        return True

    # Reject: weak/small-cap structure with entry VWAP above EMA20
    if (
        entry_bar_vwap_to_ema_20 >= 1.0043248885
        and total_volume <= 353487.7
    ):
        return True

    # Reject: weak VWAP/EMA20 structure,
    # weak broader VWAP context,
    # strong profit pace from open,
    # and post-high volume imbalance
    if (
        entry_bar_vwap_to_ema_20 <= 0.9514810741
        and current_day_vwap_to_recent_days <= 2.7823119164
        and profit_since_open_to_bars_count_since_open > 0.0132751414
        and bars_above_volume_average_vs_under_since_highest_high > 0.2250000015
        and entry_followthrough_after_near_reclaim > 1.0432881853785902
    ):
        return True

    # Reject: current-day move is active,
    # entry tries to reclaim from a pullback-volume area,
    # but histogram strength is weak and the entry does not cleanly separate
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

    # Reject: active current-day move with weak histogram quality,
    # entry remains near EMA9/low structure,
    # and the candle has almost no lower-wick support
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

    # Reject: moderate current-day move,
    # entry body is in a narrow weak/unstable range,
    # breakout efficiency is present,
    # but volume rebuild from low is too dependent on post-high volume
    # and entry volume is weak versus the pullback high-volume area
    if (
        current_day_movement_to_recent_days_movement <= 7.55102396
        and entry_bar_body > 0.7834697664
        and entry_bar_body <= 0.837882787
        and entry_breakout_efficiency_from_ema_9 > 0.4921557903
        and entry_volume_to_highest_volume_in_pullback <= 1.998335183
        and volume_since_lowest_low_to_entry_vs_since_highest_high > 0.9336597621
    ):
        return True

    # Reject: entry extension is very high,
    # but MACD is already weak versus the previous bar
    if (
        entry_extension_pressure > 0.7173990309
        and entry_bar_macd_to_previous <= 1.1105212569
    ):
        return True

    # Reject: extremely weak breakout efficiency,
    # while entry low is not meaningfully above EMA9
    if (
        entry_breakout_efficiency_from_ema_9 <= 0.1347363219
        and entry_bar_low_to_ema_9 <= 1.0026425123
    ):
        return True

    # Reject: immediate retest after highest-high,
    # but entry body is weak both versus highest-high body
    # and versus previous bar body.
    if (
        bars_since_highest_high_to_bars_before <= 0.001774
        and entry_body_to_highest_high_body <= 1.271
        and entry_body_to_previous_bar_body <= 2.81
    ):
        return True

    # Reject: compressed high-to-low reset,
    # weak entry volume versus recent bars,
    # weak body versus previous bar,
    # and weak recent positive-bar structure.
    if (
        entry_bar_volume_to_recent_bars_average <= 1.613
        and entry_body_to_previous_bar_body <= 1.591
        and price_movement_from_highest_high_to_lowest_low <= 0.271
        and recent_bars_positive_bars_pct <= 0.701
    ):
        return True

    # Reject: compressed high-to-low reset,
    # weak entry volume versus recent bars,
    # weak body versus previous bar,
    # and weak recent positive-bar structure.
    if (
        entry_bar_volume_to_recent_bars_average <= 1.613
        and entry_body_to_previous_bar_body <= 1.591
        and price_movement_from_highest_high_to_lowest_low <= 0.271
        and recent_bars_positive_bars_pct <= 0.701
    ):
        return True

    # Reject: broader EMA20 context is weak,
    # entry body is weak versus the highest-high candle,
    # and there was not enough post-high volume rebuild.
    if (
        current_day_ema_20_to_recent_days_ema_20 <= 1.0401
        and entry_body_to_highest_high_body <= 0.807
        and volume_since_highest_high_to_volume_before <= 0.331
    ):
        return True

    # Reject: no premarket volume,
    # weak bounce from lowest low,
    # and entry still happens close enough to the highest-high event.
    if (
        bars_since_highest_high_to_bars_before <= 0.1951219512195122
        and gains_since_lowest_low <= 0.2146118721461188
        and pre_market_volume <= 0.0
    ):
        return True

    # Reject: weak EMA9/EMA20 structure,
    # weak entry volume versus recent bars,
    # weak close strength versus highest-high candle,
    # and weak bounce from low.
    if (
        current_day_ema_9_to_ema_20 <= 1.120
        and entry_bar_volume_to_recent_bars_average <= 1.094
        and entry_close_strength_to_highest_high_close_strength <= 1.316
        and gains_since_lowest_low <= 0.139
    ):
        return True

    # Reject: broader EMA20 context is weak,
    # pullback health is weak,
    # total volume is limited,
    # and close strength is not enough to justify the reclaim.
    if (
        current_day_ema_20_to_recent_days_ema_20 <= 0.908
        and pullback_health <= 2.137
        and total_volume <= 3855000
        and entry_close_strength_to_highest_high_close_strength <= 2.227
    ):
        return True

    ############### ---------------- unique rules ---------------- ###############

    # Reject: weak recent trend + weak previous-high context
    if (
        recent_bars_up_trend_pct <= 0.40
        and current_day_high_to_previous_high <= 1.0216
        and controlled_volume_entry_quality <= 5.631135876710102
    ):
        return True

    # Reject: shallow pullback, weak body versus previous bar,
    # and compressed EMA-distance structure
    if (
        pullback_depth_vs_pre_high_move <= 0.88375
        and entry_body_to_previous_bar_body <= 0.98432
        and emas_distances_to_recent_bars_ema_distances <= 0.140767
        and pullback_health <= 5.634074932605927
    ):
        return True

    if (
        entry_body_to_previous_bar_body >= 69.0345
        and (
            entry_bar_ema_9_to_vwap >= 1.16935
            or entry_bar_vwap_to_ema_20 <= 0.885003
        )
        and entry_bar_volume_to_total_volume >= 0.0103088631576093
    ):
        return True

    if (
        current_day_ema_9_to_ema_20_distance_to_recent_days >= 15.8314
        and (
            entry_followthrough_after_near_reclaim >= 1.46395
            or near_high_weak_followthrough <= 0.683098
            or entry_close_to_previous_bar_high >= 1.34121
            or entry_close_to_previous_bar_close >= 1.3729
            or pre_market_volume <= 210.48
        )
    ):
        return True

    if (
        reclaim_close_strength_since_highest_high <= 0.173553719
        and pullback_depth_vs_pre_high_move >= 1.687493832
        and entry_close_position_vs_previous_close_position >= 4.728543479
        and pullback_health <= 2.7758057632396795
    ):
        return True

    # Reject: very large current-day movement,
    # almost no lower wick on entry,
    # and most volume participation came after the low
    if (
        current_day_movement_to_recent_days_movement >= 9.1927298390
        and entry_bar_lower_wick <= 0.0022260818
        and volume_since_lowest_low_to_entry_vs_since_highest_high >= 0.6822743076
        and current_day_low_to_ema_9 <= 1.0293851964429035
    ):
        return True

    # Reject: entry bar owns a large part of total volume,
    # while VWAP is still weak versus EMA20.
    # This is usually a late/forced reclaim, not a clean continuation.
    if (
        entry_bar_volume_to_total_volume >= 0.1046935351294476
        and entry_bar_vwap_to_ema_20 <= 0.9426331149875774
    ):
        return True

    # Reject: failed pressure and fake-reclaim pressure are nearly aligned.
    # This means the reclaim is not creating a new clean pressure profile;
    # it is mostly recycling the same failed-pressure structure.
    if (
        failed_pressure_to_followthrough >= 0.4087759498495121
        and fake_reclaim_pressure <= 0.4155040928633324
    ):
        return True

    # Reject: entry has a volume spike,
    # but volume confirmation quality is still weak/capped.
    # This is a fake participation pattern, not a clean volume confirmation.
    if (
        entry_volume_spike_without_high_context <= 1.9263097571372707
        and volume_confirmation_quality <= 0.5200111706836894
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

    # Reject: weak wick-volume rejection,
    # and post-high volume balance is not strong enough.
    if (
        weak_wick_volume_rejection
        and bars_above_volume_average_vs_under_since_highest_high <= 0.615
    ):
        return True

    # Reject: current-day high expanded versus recent days,
    # but VWAP context did not confirm enough.
    # This is a fake-strength / wick-extension profile.
    if (
        current_day_vwap_to_recent_days <= 1.42
        and current_day_high_to_recent_days_highs >= 1.44
    ):
        return True

    return False
