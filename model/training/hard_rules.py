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
    entry_bar_histogram_to_lowest_histogram = features_data["feature_entry_bar_histogram_to_lowest_histogram"]
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
    histogram_changed_to_positive_direction_vs_negative_pct = features_data["feature_histogram_changed_to_positive_direction_vs_negative_pct"]
    entry_bar_volume_to_recent_bars_average = features_data["feature_entry_bar_volume_to_recent_bars_average"]
    entry_upper_wick_to_recent_upper_wick_average = features_data["feature_entry_upper_wick_to_recent_upper_wick_average"]
    entry_body_to_highest_high_body = features_data["feature_entry_body_to_highest_high_body"]
    previous_bar_close_to_highest_high = features_data["feature_previous_bar_close_to_highest_high"]
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
    clean_breakout_efficiency = features_data["feature_clean_breakout_efficiency"]
    current_day_ema_9_to_ema_20_distance_to_recent_days = features_data["feature_current_day_ema_9_to_ema_20_distance_to_recent_days"]
    entry_bar_volume_to_previous_bar_volume = features_data["feature_entry_bar_volume_to_previous_bar_volume"]
    entry_bar_macd_to_previous = features_data["feature_entry_bar_macd_to_previous"]
    failed_attempts_pressure = features_data["feature_failed_attempts_pressure"]
    entry_close_position_vs_previous_close_position = features_data["feature_entry_close_position_vs_previous_close_position"]
    entry_bar_open_to_ema_9 = features_data["feature_entry_bar_open_to_ema_9"]
    profit_since_open_to_bars_count_since_open = features_data["feature_profit_since_open_to_bars_count_since_open"]
    entry_close_strength_to_highest_high_close_strength = features_data["feature_entry_close_strength_to_highest_high_close_strength"]
    reclaim_close_strength_since_highest_high = features_data["feature_reclaim_close_strength_since_highest_high"]
    entry_bar_lower_wick = features_data["feature_entry_bar_lower_wick"]
    entry_close_to_previous_bar_high = features_data["feature_entry_close_to_previous_bar_high"]
    volume_without_macd_confirmation = features_data["feature_volume_without_macd_confirmation"]
    bars_above_volume_average_vs_under_since_highest_high = features_data["feature_bars_above_volume_average_vs_under_since_highest_high"]
    macd_recovery_age_quality = features_data["feature_macd_recovery_age_quality"]
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
    distance_from_last_negative_macd_bar = features_data["feature_distance_from_last_negative_macd_bar"]
    reclaim_speed_from_lowest_low = features_data["feature_reclaim_speed_from_lowest_low"]
    entry_bar_movement_recent_bars_average = features_data["feature_entry_bar_movement_recent_bars_average"]
    entry_bar_volume = features_data["feature_entry_bar_volume"]
    current_day_ema_9_to_recent_days_ema_9 = features_data["feature_current_day_ema_9_to_recent_days_ema_9"]
    current_day_high_to_recent_days_highs = features_data["feature_current_day_high_to_recent_days_highs"]
    positive_vs_negative_volume_during_pullback = features_data["feature_positive_vs_negative_volume_during_pullback"]
    entry_bar_ema_9_to_ema_20 = features_data["feature_entry_bar_ema_9_to_ema_20"]

    ############### ---------------- broader rules ---------------- ###############

    # Reject: previous bar already reached/pushed the high,
    # EMA structure is stretched,
    # and entry candle shows rejection versus recent upper wicks
    if (
        previous_bar_high_to_highest_high >= 1.0031150793650794
        and entry_bar_ema_9_to_ema_20 >= 1.053391820032275
        and entry_upper_wick_to_recent_upper_wick_average >= 0.6957268870518433
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

    ############### ---------------- unique rules ---------------- ###############

    # Reject: entry too extended
    # Changed extension threshold from 0.4078 -> 0.48.
    # Old version removed 2 positives. This version removed 0 positives.
    if entry_bar_ema_9_to_vwap > 1.122 and entry_extension_pressure > 0.428:
        return True

    # Reject: wick-volume rejection, but only if entry volume does not rescue it.
    # Old version removed 1 positive.
    # This version removed 0 positives and still caught the FP cases.
    if weak_wick_volume_rejection and entry_bar_volume_to_highest_high_volume <= 1.5:
        return True

    # Reject: weak context + inefficient breakout + not enough relative volume
    # Rescue if gains into entry are still controlled and profit pace from open is low
    if (
        current_day_vwap_to_recent_days <= 1.36
        and entry_breakout_efficiency_from_ema_9 <= 0.40
        and current_day_volume_to_recent_days_volume <= 145
        and current_day_volume_to_recent_days_volume > 2.0
        and not (
            gains_until_entry_bar <= 0.278
            and profit_since_open_to_bars_count_since_open <= 0.00130
        )
    ):
        return True

    # Reject: weak current-day high context.
    # This replaces the bugged current_high_to_previous rule.
    # Uses feature_current_day_high_to_previous_high correctly.
    if (
        current_day_vwap_to_recent_days <= 2.12
        and current_day_high_to_recent_days_highs > 1.81
        and current_day_high_to_previous_high <= 1.40
        and gains_until_entry_bar <= 0.70
        and entry_breakout_efficiency_from_ema_9 <= 0.55
        and not (
            current_day_high_to_previous_high >= 1.319
            and entry_bar_ema_9_to_vwap <= 1.073
        )
    ):
        return True

    # Rescue valid positives where entry is not too far above old high
    # and body is not abnormally expanded versus recent bars
    if (
        current_day_high_to_recent_days_highs > 3.31
        and entry_breakout_efficiency_from_ema_9 <= 0.40
        and gains_until_entry_bar > 0.60
        and not (
            entry_bar_close_to_highest_high <= 1.023
            and entry_body_to_recent_bars_body_average <= 5.55
        )
    ):
        return True

    # Reject: big current-day movement, but weak VWAP context
    if current_day_vwap_to_recent_days <= 1.42 and current_day_movement_to_recent_days_movement > 6.10:
        return True

    # Reject: weak previous-high reclaim with high breakout-efficiency ratio
    if current_day_high_to_previous_high <= 1.02 and entry_breakout_efficiency_from_ema_9 > 0.64:
        return True

    # Additional rescue: controlled body versus recent candles
    if (
        entry_histogram_to_highest_histogram <= 0.417
        and entry_volume_to_highest_volume_in_pullback > 2.16
        and not (
            entry_bar_body >= 0.90
            and entry_close_strength_to_highest_high_close_strength >= 2.0
        )
        and not (
            entry_body_to_recent_bars_body_average <= 3.26
        )
    ):
        return True

    if (
        current_day_ema_20_to_recent_days_ema_20 <= 0.988
        and entry_bar_histogram_to_lowest_histogram > 1.28
        and not (
            entry_close_strength_to_highest_high_close_strength >= 1.27
            and entry_bar_ema_9_to_vwap <= 1.10
        )
    ):
        return True

    # Reject: elevated day structure, but inefficient entry breakout
    # Rescue if EMA9 is already meaningfully above VWAP
    if (
        current_day_low_to_ema_9 > 1.29
        and entry_breakout_efficiency_from_ema_9 <= 0.36
        and controlled_volume_entry_quality > 1.0
        and not entry_bar_ema_9_to_vwap >= 1.118
    ):
        return True

    # Reject: deep pullback, but weak entry body
    if price_movement_from_highest_high_to_lowest_low > 5 and entry_bar_body < 0.65:
        return True

    # Reject: weak current-day breakout context + entry candle loses EMA9
    if current_day_high_to_previous_high <= 1.28 and entry_bar_low_to_ema_9 <= 0.984:
        return True

    if (
        bars_since_highest_high_to_bars_before <= 0.011
        and entry_breakout_efficiency_from_ema_9 <= 0.27
        and not (
            entry_body_to_recent_bars_body_average <= 6.42
            and entry_bar_upper_wick <= 0.145
        )
    ):
        return True

    # Reject: no post-high volume rebuild + inefficient breakout
    # Rescue very fast continuation if entry body strongly improves over previous bar
    # and histogram is not weak versus the highest-high histogram
    if (
        volume_since_highest_high_to_volume_before <= 0.045
        and entry_breakout_efficiency_from_ema_9 <= 0.27
        and not (
            entry_body_to_previous_bar_body >= 20.0
            and entry_histogram_to_highest_histogram >= 1.0
            and highest_high_to_entry_elapsed_minutes <= 2
        )
    ):
        return True

    # Reject: previous bar had weak volume, and entry candle shows rejection
    if previous_bar_volume_to_its_previous_volume <= 0.49 and entry_bar_upper_wick >= 0.33:
        return True

    # Reject: previous bar was not close to reclaiming high, and entry rejects
    # Rescue if recent trend is strong enough
    if (
        previous_bar_high_to_highest_high <= 0.973
        and entry_bar_upper_wick >= 0.343
        and not (
            recent_bars_up_trend_pct >= 0.70
        )
    ):
        return True

    # Reject: previous bar already pushed above old high,
    # and histogram already moved strongly in positive direction
    if previous_bar_high_to_highest_high >= 1.010 and histogram_changed_to_positive_direction_vs_negative_pct >= 1.04:
        return True

    # Reject: active current-day move, but entry is already too extended
    if current_day_movement_to_recent_days_movement >= 1.30 and entry_extension_pressure >= 0.68:
        return True

    # Reject: entry volume spike is large versus highest-high volume,
    # but not truly strong versus recent bars
    if entry_bar_volume_to_recent_bars_average <= 5.80 and entry_bar_volume_to_highest_high_volume >= 5.60:
        return True

    # Reject: entry candle shows abnormal rejection
    # and the entry body is weak compared with the highest-high candle
    if entry_upper_wick_to_recent_upper_wick_average >= 2.13 and entry_body_to_highest_high_body <= 1.17:
        return True

    # Reject: previous bar already closed very close to old high,
    # but entry comes with almost no real rebuild after the highest high
    if previous_bar_close_to_highest_high >= 0.997 and bars_since_highest_high_to_bars_before <= 0.002:
        return True

    # Reject: very shallow pullback versus the pre-high move,
    # while the current day volume is already extremely expanded
    if pullback_depth_vs_pre_high_move <= 0.42 and current_day_volume_to_recent_days_volume >= 72:
        return True

    # Reject: weak recent uptrend, but entry is already stretched above old high
    if (
        recent_bars_up_trend_pct <= 0.50
        and (
            entry_bar_close_to_highest_high >= 1.091
            or entry_breakout_efficiency_from_ema_9 >= 0.886
        )
    ):
        return True

    # Reject: deep pullback, but entry body is not strong enough versus recent bars
    if entry_body_to_recent_bars_body_average <= 3.0 and pullback_depth_vs_pre_high_move >= 2.82:
        return True

    # Reject: low premarket volume + weak gains into entry
    if gains_until_entry_bar <= 0.347 and pre_market_volume <= 2242:
        return True

    # Reject: almost no rebuild after highest high + not enough current-day volume context
    if current_day_volume_to_recent_days_volume <= 4.25 and bars_since_highest_high_to_bars_before <= 0.00163:
        return True

    # Reject: histogram expands, but price is not strong enough above VWAP
    if entry_close_to_vwap <= 1.13 and entry_bar_histogram_to_previous >= 4.70:
        return True

    # Reject: inefficient breakout + high EMA9/VWAP,
    # unless the entry candle itself is strong
    if (
        entry_breakout_efficiency_from_ema_9 <= 0.263
        and entry_bar_ema_9_to_vwap > 1.122
        and not (
            entry_bar_body >= 0.82
            and entry_close_strength_to_highest_high_close_strength >= 1.30
        )
    ):
        return True

    # Reject: weak volume-price efficiency + weak controlled volume
    # Rescue if there was meaningful post-high volume rebuild
    # and entry close quality is strong versus the highest-high candle
    if (
        entry_volume_price_efficiency <= 0.050
        and controlled_volume_entry_quality <= 0.852
        and not (
            volume_since_highest_high_to_volume_before >= 0.2138
            and entry_close_strength_to_highest_high_close_strength >= 1.69
        )
    ):
        return True

    # Reject: almost no bounce from pullback low,
    # and entry volume is weak versus highest pullback volume
    if gains_since_lowest_low <= 0.047 and entry_volume_to_highest_volume_in_pullback <= 1.09:
        return True

    if gains_since_lowest_low <= 0.05 and current_day_movement_to_recent_days_movement >= 7.5:
        return True

    # Reject: many recent positive bars, but entry candle still loses EMA9
    if recent_bars_positive_bars_pct >= 0.77 and entry_bar_low_to_ema_9 <= 0.995:
        return True

    if (
        emas_distances_to_recent_bars_ema_distances >= 1.017
        and entry_bar_ema_9_to_vwap >= 1.040
        and not (
            entry_body_to_recent_bars_body_average >= 5.50
            and entry_extension_pressure <= 0.17
        )
    ):
        return True

    # Reject: entry loses EMA9, but previous bar was already near old high
    if entry_bar_low_to_ema_9 <= 0.990 and previous_bar_close_to_highest_high >= 0.984:
        return True

    # Reject: early setup where previous bar was already near the old high,
    # but entry does not add enough follow-through over previous close
    if (
        minutes_since_market_open <= 23
        and previous_bar_close_to_highest_high >= 0.984
        and entry_close_to_previous_bar_close <= 1.095
    ):
        return True

    # Reject: very early setup, weak entry body versus previous bar,
    # but the candle still looks like a clean breakout
    if (
        minutes_since_market_open <= 23
        and entry_body_to_previous_bar_body <= 1.86
        and clean_breakout_efficiency >= 1.0
    ):
        return True

    # Reject: stretched EMA structure + volume spike, but weak MACD follow-through
    if (
        current_day_ema_9_to_ema_20_distance_to_recent_days >= 5.33
        and entry_bar_volume_to_previous_bar_volume >= 7.60
        and entry_bar_macd_to_previous <= 0.67
    ):
        return True

    # Reject: entry volume is only strong versus previous bar,
    # but weak versus the original highest-high volume
    if entry_bar_volume_to_previous_bar_volume >= 15.60 and entry_bar_volume_to_highest_high_volume <= 0.91:
        return True

    # Reject: stretched EMA structure + failed attempts + abnormal close-position shift
    if (
        current_day_ema_9_to_ema_20_distance_to_recent_days >= 4.60
        and failed_attempts_pressure >= 0.34
        and entry_close_position_vs_previous_close_position >= 2.30
    ):
        return True

    # Reject: entry opens below EMA9 and entry volume is weak vs recent bars
    if entry_bar_open_to_ema_9 <= 0.9885 and entry_bar_volume_to_recent_bars_average <= 2.14:
        return True

    if entry_bar_ema_9_to_vwap <= 1.0144 and entry_body_to_highest_high_body <= 1.445:
        return True

    if profit_since_open_to_bars_count_since_open >= 0.00775 and volume_since_highest_high_to_volume_before <= 0.0103:
        return True

    if entry_bar_open_to_ema_9 >= 1.007 and entry_close_position_vs_previous_close_position <= 0.68:
        return True

    # Reject: weak recent trend + weak previous-high context
    if (
        recent_bars_up_trend_pct <= 0.40
        and current_day_high_to_previous_high <= 1.0216
    ):
        return True

    # Reject: compressed EMA structure, but entry candle body is extremely strong
    if (
        emas_distances_to_recent_bars_ema_distances <= 0.119
        and entry_bar_body >= 0.986
    ):
        return True

    if (
        entry_close_to_previous_bar_close <= 1.0624
        and controlled_volume_entry_quality <= 0.7611
    ):
        return True

    # Reject: entry is extended, but candle shows large upper-wick rejection
    if (
        entry_bar_upper_wick >= 0.333333
        and entry_extension_pressure >= 0.325339
    ):
        return True

    # Reject: weak reclaim close after highest high,
    # and entry upper wick is unusually small versus recent upper wicks
    if (
        reclaim_close_strength_since_highest_high <= 0.110868
        and entry_upper_wick_to_recent_upper_wick_average <= 0.264035
    ):
        return True

    # Reject: shallow pullback, weak body versus previous bar,
    # and compressed EMA-distance structure
    if (
        pullback_depth_vs_pre_high_move <= 0.88375
        and entry_body_to_previous_bar_body <= 0.98432
        and emas_distances_to_recent_bars_ema_distances <= 0.140767
    ):
        return True

    # Reject: almost full-body candle after large post-high volume participation
    if (
        entry_bar_body >= 0.966085
        and volume_since_highest_high_to_volume_before >= 0.578934
        and entry_bar_lower_wick <= 0.015361
    ):
        return True

    if entry_close_to_previous_bar_high <= 1.102621092 and profit_since_open_to_bars_count_since_open >= 0.01616006036:
        return True

    if volume_without_macd_confirmation <= 1.19487729 and bars_above_volume_average_vs_under_since_highest_high <= 0:
        return True

    if current_day_movement_to_recent_days_movement >= 18.4136654 and bars_since_highest_high_to_bars_before <= 0.0112745098:
        return True

    if current_day_movement_to_recent_days_movement >= 9.548780488 and volume_since_highest_high_to_volume_before <= 0.01110606138:
        return True

    if macd_recovery_age_quality >= 17.66563587 and entry_bar_vwap_to_ema_20 <= 0.832889939:
        return True

    if failed_pressure_to_followthrough >= 0.4016287815 and entry_close_position_vs_previous_close_position >= 8.03125:
        return True

    if entry_body_to_recent_bars_body_average <= 1.63759 and entry_close_to_vwap >= 1.27141:
        return True

    if entry_upper_wick_to_recent_upper_wick_average <= 0 and bars_since_highest_high_to_bars_before <= 0.00269945:
        return True

    if (
        entry_body_to_previous_bar_body >= 69.0345
        and (
            entry_bar_ema_9_to_vwap >= 1.16935
            or entry_bar_vwap_to_ema_20 <= 0.885003
        )
    ):
        return True

    if highest_high_quality >= 14.5937 and volume_since_highest_high_to_volume_before <= 0.0111551:
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

    if macd_recovery_followthrough_quality >= 38.3995 and volume_since_highest_high_to_volume_before <= 0.0265052:
        return True

    if (
        previous_bar_high_to_highest_high >= 1.005804598
        and (
            entry_bar_volume_to_previous_bar_volume >= 2.483333125
        )
    ):
        return True

    # Reject: previous bar was already near the high,
    # but entry close quality is weak and entry volume is not impressive vs average
    if (
        previous_bar_close_to_highest_high >= 0.97686
        and entry_close_position_vs_previous_close_position <= 0.79938
        and entry_bar_volume_to_volume_average <= 2.31401
    ):
        return True

    # Reject: previous bar was already near high,
    # reclaim strength is weak,
    # and entry volume is not strong versus the previous bar
    if (
        previous_bar_close_to_highest_high >= 0.99062
        and reclaim_close_strength_since_highest_high <= 0.29509
        and entry_bar_volume_to_previous_bar_volume <= 1.45341
    ):
        return True

    # Reject: high volume-price efficiency while histogram already moved positive
    if (
        entry_volume_price_efficiency >= 0.81739
        and histogram_changed_to_positive_direction_vs_negative_pct >= 2.0
        and volume_since_lowest_low_to_entry_vs_since_highest_high >= 0.86157
    ):
        return True

    if (
        entry_volume_price_efficiency <= 0.03799
        and current_day_ema_9_to_ema_20_distance_to_recent_days >= 9.24778
        and failed_attempts_pressure >= 0.14996
    ):
        return True

    # Reject: low premarket participation + weak follow-through + weak volume/MACD confirmation
    if (
        pre_market_volume <= 12626.2
        and entry_followthrough_after_near_reclaim <= 1.1097255811
        and volume_without_macd_confirmation <= 1.3859621588
    ):
        return True

    # Reject: entry is floating above EMA9, but bounce/follow-through is weak
    if (
        entry_bar_low_to_ema_9 >= 1.0093729767
        and gains_since_lowest_low <= 0.0738457243
        and entry_close_position_vs_previous_close_position <= 1.0
    ):
        return True

    # Reject: previous bar was not close enough to high, and entry shows rejection
    if (
        previous_bar_close_to_highest_high <= 0.9768057971
        and entry_close_to_previous_bar_high <= 1.0443794455
        and entry_bar_upper_wick >= 0.1618463677
    ):
        return True

    # Reject: high volume efficiency + high recent volume, but with upper-wick rejection
    if (
        entry_volume_price_efficiency >= 0.2663313036
        and entry_bar_volume_to_recent_bars_average >= 4.1439257575
        and entry_bar_upper_wick >= 0.1618463677
    ):
        return True

    # Reject: deep pullback versus pre-high move,
    # but entry body is weak versus recent candles
    if (
        entry_body_to_recent_bars_body_average <= 2.7161
        and pullback_depth_vs_pre_high_move >= 2.3676
    ):
        return True

    # Reject: weak daily EMA20 context,
    # and entry volume is weaker than previous bar
    if (
        current_day_ema_20_to_recent_days_ema_20 <= 1.0059
        and entry_bar_volume_to_previous_bar_volume <= 0.6496
    ):
        return True

    # Reject: very large body versus highest-high body,
    # but weak volume/MACD confirmation
    if (
        volume_without_macd_confirmation <= 0.4503
        and entry_body_to_highest_high_body >= 21.0911
    ):
        return True

    # Reject: failed-pressure/fake-reclaim pattern,
    # while recent bars are not positive enough
    if (
        failed_pressure_to_followthrough >= 0.3708
        and recent_bars_positive_bars_pct <= 0.30
    ):
        return True

    # Reject: very high total-volume day with oversized entry volume vs average
    if (
        total_volume >= 21435696.25
        and entry_bar_volume_to_volume_average >= 6.1061
    ):
        return True

    # Reject: low total-volume name, but entry is already extended above VWAP/EMA structure
    if (
        total_volume <= 647365.35
        and entry_bar_ema_9_to_vwap >= 1.1237
    ):
        return True

    # Reject: almost no premarket participation and current-day move is not strong enough
    if (
        pre_market_volume <= 229.31
        and current_day_movement_to_recent_days_movement <= 4.4058
    ):
        return True

    # Reject: weak current-day VWAP context and weak volume from low into entry
    if (
        current_day_vwap_to_recent_days <= 1.3480
        and volume_since_lowest_low_to_entry_vs_since_highest_high <= 0.2413
    ):
        return True

    # Reject: shallow/no real pullback, while VWAP is still below EMA20
    if (
        pullback_depth_vs_pre_high_move <= 0.4873
        and entry_bar_vwap_to_ema_20 <= 0.8890
    ):
        return True

    # Reject: MACD recovery looks old/extended, but entry MACD weakens versus previous bar
    if (
        macd_recovery_followthrough_quality >= 18.7867
        and entry_bar_macd_to_previous <= 0.8328
    ):
        return True

    # Reject: weak entry body, but stock already has fast profit pace from open
    if (
        entry_bar_body <= 0.3877
        and profit_since_open_to_bars_count_since_open >= 0.00455
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

    if (
        entry_bar_upper_wick >= 0.06666666667
        and pullback_depth_vs_pre_high_move >= 4.36527928
        and entry_bar_volume_to_recent_bars_average <= 2.253715889
    ):
        return True

    if (
        reclaim_close_strength_since_highest_high <= 0.173553719
        and pullback_depth_vs_pre_high_move >= 1.687493832
        and entry_close_position_vs_previous_close_position >= 4.728543479
    ):
        return True

    # Reject: short-term EMA is stretched over EMA20,
    # broader EMA20 context is not strong enough,
    # and entry body is oversized versus recent candles
    if (
        current_day_ema_9_to_ema_20 >= 1.294666093
        and current_day_ema_20_to_recent_days_ema_20 <= 1.392372919
        and (
            entry_body_to_recent_bars_body_average >= 4.089472023
            or entry_bar_low_to_ema_9 >= 1.017979924
        )
    ):
        return True

    if (
        current_day_ema_9_to_ema_20 >= 1.294000557
        and current_day_ema_20_to_recent_days_ema_20 <= 1.393020797
        and gains_until_entry_bar <= 0.8812913898
    ):
        return True

    # Reject: entry opens stretched above EMA9,
    # but does not clear the previous highest-high strongly enough,
    # while EMA9 is already stretched over EMA20
    if (
        entry_bar_open_to_ema_9 >= 1.02100165
        and entry_bar_close_to_highest_high <= 1.01447752
        and current_day_ema_9_to_ema_20 >= 1.153187004
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

    if (
        macd_recovery_age_quality >= 45.11816621
        and distance_from_last_negative_macd_bar >= 32.94
    ):
        return True

    if (
        pre_market_volume <= 3288
        and entry_bar_lower_wick >= 0.1688700749
        and reclaim_speed_from_lowest_low >= 0.7738171698
    ):
        return True

    if (
        entry_close_strength_to_highest_high_close_strength <= 1.155866609
        and entry_bar_lower_wick >= 0.1093905084
        and entry_close_position_vs_previous_close_position >= 3.164044884
    ):
        return True

    # Effective rules:

    # Reject: post-high volume participation without MACD confirmation
    if (
        volume_since_highest_high_to_volume_before >= 0.1184412594
        and volume_without_macd_confirmation >= 109.6745643
        and previous_bar_volume_to_its_previous_volume >= 1.213324829
    ):
        return True

    # Reject: early shallow-pullback chase after fast open profit
    if (
        minutes_since_market_open <= 29
        and pullback_depth_vs_pre_high_move <= 0.6014838509
        and profit_since_open_to_bars_count_since_open >= 0.01742149356
    ):
        return True

    # Reject: expanded EMA-distance structure,
    # tiny high-to-low reset,
    # and fast profit pace from open
    if (
        emas_distances_to_recent_bars_ema_distances >= 0.207173644
        and price_movement_from_highest_high_to_lowest_low <= 0.22
        and profit_since_open_to_bars_count_since_open >= 0.007082560815
    ):
        return True

    # Reject: weak close-position improvement early,
    # with low absolute entry volume
    if (
        entry_close_position_vs_previous_close_position <= 0.8047079751
        and minutes_since_market_open <= 42
        and entry_bar_volume <= 191259.5
    ):
        return True

    # Reject: weak current-day VWAP context,
    # tiny pullback/reset,
    # and entry is already extended
    if (
        current_day_vwap_to_recent_days <= 1.22341473
        and price_movement_from_highest_high_to_lowest_low <= 0.42755
        and entry_extension_pressure >= 0.2245726894
    ):
        return True

    # Reject: recent bars look positive,
    # but entry volume-price efficiency is very weak
    # and premarket participation is low
    if (
        entry_volume_price_efficiency <= 0.02588854677
        and pre_market_volume <= 47862
        and recent_bars_positive_bars_pct >= 0.6
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

    # Reject: current EMA9/EMA20 expansion is not strong,
    # but entry histogram is very high versus highest-high histogram
    if (
        current_day_ema_9_to_ema_20_distance_to_recent_days <= 0.1387122378381986
        and entry_histogram_to_highest_histogram >= 1.8977198438479372
    ):
        return True

    # Reject: very late-day setup,
    # with histogram already stretched versus highest-high histogram
    if (
        minutes_since_market_open >= 339.85
        and entry_histogram_to_highest_histogram >= 1.8977198438479372
    ):
        return True

    # Reject: low-volume name,
    # post-high volume bars dominate,
    # but volume lacks MACD confirmation
    if (
        total_volume <= 616414.7
        and bars_above_volume_average_vs_under_since_highest_high >= 1.38
        and volume_without_macd_confirmation <= 0.7523717610985081
    ):
        return True

    # Reject: weak reclaim strength after highest high,
    # high highest-high quality,
    # but weak entry close strength versus highest-high close strength
    if (
        reclaim_close_strength_since_highest_high <= 0.0717770035
        and highest_high_quality >= 10.3882806384
        and entry_close_strength_to_highest_high_close_strength <= 1.1112795315
    ):
        return True

    # Reject: entry histogram weakens versus previous,
    # while current-day low is already far above EMA9
    if (
        entry_bar_histogram_to_previous <= -0.0642453770
        and current_day_low_to_ema_9 >= 1.2470085753
    ):
        return True

    # Reject: price has already gained a lot,
    # but current-day volume is weak versus recent days
    # and entry volume-price efficiency is not strong enough
    if (
        current_day_volume_to_recent_days_volume <= 3.3266385818
        and gains_until_entry_bar >= 0.8579580645
        and entry_volume_price_efficiency <= 0.1021919641
    ):
        return True

    # Reject: weak highest-high quality,
    # fake/failed reclaim pressure,
    # and weak current-day VWAP context
    if (
        highest_high_quality <= 0.2531756429
        and failed_pressure_to_followthrough >= 0.2381467257
        and current_day_vwap_to_recent_days <= 1.5574589307
    ):
        return True

    # Reject: no real reset below EMA9,
    # but current-day EMA9 context is not strong enough
    # and MACD recovery is already active
    if (
        macd_recovery_age_quality >= 3.9063163683
        and current_day_ema_9_to_recent_days_ema_9 <= 1.1530989632
        and current_day_low_to_ema_9 >= 1.1355114046
    ):
        return True

    # Reject: very large current-day movement,
    # almost no lower wick on entry,
    # and most volume participation came after the low
    if (
        current_day_movement_to_recent_days_movement >= 9.1927298390
        and entry_bar_lower_wick <= 0.0022260818
        and volume_since_lowest_low_to_entry_vs_since_highest_high >= 0.6822743076
    ):
        return True

    # Reject: large-volume / high-liquidity move,
    # weak follow-through after near reclaim,
    # and stretched EMA9/EMA20 structure
    if (
        total_volume >= 23263697.0
        and entry_followthrough_after_near_reclaim <= 1.076412
        and current_day_ema_9_to_ema_20 >= 1.28501
    ):
        return True

    # Reject: entry candle movement is very large versus recent bars,
    # but close strength is weak versus the highest-high candle
    if (
        entry_bar_movement_recent_bars_average >= 12.721924
        and entry_close_strength_to_highest_high_close_strength <= 1.044746
    ):
        return True

    # # Reject: low absolute entry volume,
    # # high breakout efficiency,
    # # and previous bar already reached/pushed old high
    # if (
    #     entry_bar_volume <= 41006.812998
    #     and entry_breakout_efficiency_from_ema_9 >= 0.64336
    #     and previous_bar_high_to_highest_high >= 1.0
    # ):
    #     return True

    # Reject: pullback has more positive than negative volume,
    # failed-pressure/followthrough is present,
    # and entry volume is already spiking versus recent bars
    if (
        positive_vs_negative_volume_during_pullback >= 1.869628616
        and failed_pressure_to_followthrough >= 0.1800401615
        and entry_bar_volume_to_recent_bars_average >= 3.672319135
    ):
        return True

    # Reject: entry low is elevated above EMA9,
    # VWAP is weak versus EMA20,
    # but breakout efficiency is already high
    if (
        current_day_low_to_ema_9 >= 1.358228224
        and entry_bar_vwap_to_ema_20 <= 0.8898687606
        and entry_breakout_efficiency_from_ema_9 >= 0.5188943549
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

    # Reject: histogram has shifted strongly positive,
    # controlled-volume quality is not strong,
    # and previous bar already reached the high
    if (
        histogram_changed_to_positive_direction_vs_negative_pct >= 2.0
        and controlled_volume_entry_quality <= 7.923442547
        and previous_bar_high_to_highest_high >= 0.996835443
    ):
        return True

    # Reject: entry body is massively larger than previous bar body,
    # but current-day volume and high context are weak
    if (
        entry_body_to_previous_bar_body >= 19.52153846
        and current_day_volume_to_recent_days_volume <= 2.403095476
        and current_day_high_to_recent_days_highs <= 1.322865281
    ):
        return True

    # Reject: elevated low above EMA9,
    # weak reclaim strength after highest high,
    # and weak rebuild volume from low to entry
    if (
        reclaim_close_strength_since_highest_high <= 0.1084281907
        and current_day_low_to_ema_9 >= 1.229224184
        and volume_since_lowest_low_to_entry_vs_since_highest_high <= 0.2690279056
    ):
        return True

    # Reject: almost no post-high volume rebuild,
    # histogram has already recovered strongly from the lowest histogram,
    # but follow-through after near reclaim is weak
    if (
        volume_since_highest_high_to_volume_before <= 0.004922081116
        and entry_bar_histogram_to_lowest_histogram >= 1.518685818
        and entry_followthrough_after_near_reclaim <= 1.063911182
    ):
        return True

    # Reject: large recovery from lowest low,
    # but almost no actual bounce from the low,
    # and recent bars are not positive enough
    if (
        entry_close_to_lowest_low_recovery >= 2.431875
        and gains_since_lowest_low <= 0.04515823721
        and recent_bars_positive_bars_pct <= 0.40
    ):
        return True

    return False

def should_be_rescued_by_hard_rules(
    features_data: dict[str, float],
) -> bool:
    current_day_ema_20_to_recent_days_ema_20 = features_data["feature_current_day_ema_20_to_recent_days_ema_20"]
    current_day_low_to_ema_9 = features_data["feature_current_day_low_to_ema_9"]
    volume_since_highest_high_to_volume_before = features_data["feature_volume_since_highest_high_to_volume_before"]
    previous_bar_volume_to_its_previous_volume = features_data["feature_previous_bar_volume_to_its_previous_volume"]
    entry_body_to_recent_bars_body_average = features_data["feature_entry_body_to_recent_bars_body_average"]
    entry_body_to_highest_high_body = features_data["feature_entry_body_to_highest_high_body"]
    gains_since_lowest_low = features_data["feature_gains_since_lowest_low"]
    pre_market_gains = features_data["feature_pre_market_gains"]
    entry_bar_movement_recent_bars_average = features_data["feature_entry_bar_movement_recent_bars_average"]
    entry_body_to_previous_bar_body = features_data["feature_entry_body_to_previous_bar_body"]
    entry_bar_volume = features_data["feature_entry_bar_volume"]
    highest_high_quality = features_data["feature_highest_high_quality"]
    entry_close_to_previous_bar_high = features_data["feature_entry_close_to_previous_bar_high"]
    volume_without_macd_confirmation = features_data["feature_volume_without_macd_confirmation"]
    entry_breakout_efficiency_from_ema_9 = features_data["feature_entry_breakout_efficiency_from_ema_9"]
    current_day_vwap_to_recent_days = features_data["feature_current_day_vwap_to_recent_days"]
    entry_bar_histogram_to_previous = features_data["feature_entry_bar_histogram_to_previous"]
    entry_close_to_vwap = features_data["feature_entry_close_to_vwap"]
    macd_recovery_age_quality = features_data["feature_macd_recovery_age_quality"]
    controlled_volume_entry_quality = features_data["feature_controlled_volume_entry_quality"]
    failed_attempts_pressure = features_data["feature_failed_attempts_pressure"]
    current_day_ema_9_to_recent_days_ema_9 = features_data["feature_current_day_ema_9_to_recent_days_ema_9"]
    entry_close_to_lowest_low_recovery = features_data["feature_entry_close_to_lowest_low_recovery"]
    entry_bar_ema_9_to_vwap = features_data["feature_entry_bar_ema_9_to_vwap"]
    entry_bar_volume_to_total_volume = features_data["feature_entry_bar_volume_to_total_volume"]
    failed_pressure_to_followthrough = features_data["feature_failed_pressure_to_followthrough"]
    pullback_depth_vs_pre_high_move = features_data["feature_pullback_depth_vs_pre_high_move"]
    entry_bar_low_to_ema_9 = features_data["feature_entry_bar_low_to_ema_9"]
    bars_since_highest_high_to_bars_before = features_data["feature_bars_since_highest_high_to_bars_before"]
    inefficient_breakout_extension = features_data["feature_inefficient_breakout_extension"]
    strong_vwap_volume_reentry = features_data["feature_strong_vwap_volume_reentry"]
    bars_since_lowest_low_to_entry = features_data["feature_bars_since_lowest_low_to_entry"]
    entry_bar_histogram_to_lowest_histogram = features_data["feature_entry_bar_histogram_to_lowest_histogram"]
    current_day_ema_9_to_ema_20 = features_data["feature_current_day_ema_9_to_ema_20"]
    entry_bar_lower_wick = features_data["feature_entry_bar_lower_wick"]
    current_day_movement_to_recent_days_movement = features_data["feature_current_day_movement_to_recent_days_movement"]
    reclaim_close_strength_since_highest_high = features_data["feature_reclaim_close_strength_since_highest_high"]
    emas_distances_to_recent_bars_ema_distances = features_data["feature_emas_distances_to_recent_bars_ema_distances"]

    # Rescue: very strong broader EMA20 context,
    # and current-day low is deeply below EMA9
    if (
        current_day_ema_20_to_recent_days_ema_20 >= 1.8320
        and current_day_low_to_ema_9 <= 0.5501
    ):
        return True

    # Rescue: very little volume after highest high,
    # previous bar had volume spike,
    # and entry body is strong enough versus recent bars
    if (
        volume_since_highest_high_to_volume_before <= 0.0042471454
        and previous_bar_volume_to_its_previous_volume >= 2.4255379381
        and entry_body_to_recent_bars_body_average >= 2.090348
        and entry_body_to_highest_high_body <= 3.968254
    ):
        return True

    # Rescue: negative premarket / weak bounce pattern,
    # but entry movement stayed controlled
    if (
        gains_since_lowest_low <= 0.042952
        and pre_market_gains <= -0.0325203
        and entry_bar_movement_recent_bars_average <= 2.68926
    ):
        return True

    # Rescue: very low bounce from low,
    # weak body versus previous bar,
    # and very low absolute entry volume
    if (
        gains_since_lowest_low <= 0.042952
        and entry_body_to_previous_bar_body <= 0.783092
        and entry_bar_volume <= 27943.2
        and highest_high_quality >= 1.2694991511
    ):
        return True

    # Rescue: weak breakout efficiency,
    # but strong volume context without MACD confirmation
    if (
        entry_close_to_previous_bar_high <= 1.04277
        and volume_without_macd_confirmation >= 39.4235
        and entry_breakout_efficiency_from_ema_9 <= 0.234494
    ):
        return True

    # Rescue: very strong VWAP context,
    # even though entry histogram is weak versus previous
    if (
        current_day_vwap_to_recent_days >= 3.73543
        and entry_bar_histogram_to_previous <= 0.0866119
    ):
        return True

    # Rescue: entry is not too extended above VWAP,
    # but MACD recovery is mature/established
    if (
        entry_close_to_vwap <= 1.091831446
        and macd_recovery_age_quality >= 25.08706195
        and controlled_volume_entry_quality >= 2.3678374659
    ):
        return True

    # Rescue: strong failed-attempt pressure,
    # but price had a deep reset below EMA9
    if (
        failed_attempts_pressure >= 0.8286174979
        and current_day_low_to_ema_9 <= 0.6858215054
    ):
        return True

    # Rescue: strong current-day EMA9 context,
    # and entry recovered strongly from the lowest low
    if (
        current_day_ema_9_to_recent_days_ema_9 >= 1.433818076
        and entry_close_to_lowest_low_recovery >= 3.1746875
        and entry_bar_ema_9_to_vwap <= 1.1263824316
    ):
        return True

    # Rescue: strong bounce from lowest low,
    # with high entry-volume share of total day volume
    if (
        gains_since_lowest_low >= 0.4225563909774436
        and entry_bar_volume_to_total_volume >= 0.1586696945759777
    ):
        return True

    # Rescue: strong failed-pressure/fake-reclaim structure,
    # but entry is still close to previous bar high
    if (
        failed_pressure_to_followthrough >= 1.15214089953198
        and entry_close_to_previous_bar_high <= 1.0165910520531982
    ):
        return True

    # Rescue: very deep pullback,
    # but entry bar low stayed above EMA9
    if (
        pullback_depth_vs_pre_high_move >= 7.2254148073
        and entry_bar_low_to_ema_9 >= 1.0265863377
        and bars_since_highest_high_to_bars_before >= 0.0756143667
    ):
        return True

    # Rescue: extremely large entry body versus highest-high body,
    # but not oversized versus previous bar body
    if (
        entry_body_to_highest_high_body >= 52.3689565217
        and entry_body_to_previous_bar_body <= 1.8368582888
    ):
        return True

    if (
        inefficient_breakout_extension >= 1.0
        and failed_attempts_pressure >= 1.0059454889
        and macd_recovery_age_quality <= 1.2094179809
    ):
        return True

    # Rescue: strong VWAP/volume reentry
    # and strong breakout efficiency from EMA9
    if (
        strong_vwap_volume_reentry >= 1.0
        and entry_breakout_efficiency_from_ema_9 >= 0.6415188226
        and failed_pressure_to_followthrough <= 0.4607633265
    ):
        return True

    # Rescue candidate: long rebuild from lowest low,
    # but very low absolute entry volume
    if (
        entry_bar_volume <= 79876.0
        and bars_since_lowest_low_to_entry >= 121.6
    ):
        return True

    # Rescue: failed/fake reclaim pressure is high,
    # histogram recovered from the lowest histogram,
    # and EMA9 is structurally above EMA20
    if (
        failed_pressure_to_followthrough >= 0.7378812986
        and entry_bar_histogram_to_lowest_histogram >= 1.392130531
        and current_day_ema_9_to_ema_20 >= 1.185506552
    ):
        return True

    # Rescue: very strong VWAP context,
    # weak highest-high quality,
    # and little/no volume-without-MACD problem
    if (
        current_day_vwap_to_recent_days >= 3.506664984
        and highest_high_quality <= 1.07155698
        and volume_without_macd_confirmation <= 0.9464648456
    ):
        return True

    # Rescue: negative premarket,
    # strong EMA9/EMA20 structure,
    # but weak highest-high quality
    if (
        pre_market_gains <= -0.05704768928
        and current_day_ema_9_to_ema_20 >= 1.185506552
        and highest_high_quality <= 2.432910481
    ):
        return True

    # Rescue: weak highest-high quality,
    # deep reset below EMA9,
    # and entry candle has meaningful lower wick support
    if (
        highest_high_quality <= 1.07155698
        and current_day_low_to_ema_9 <= 0.8111091415
        and entry_bar_lower_wick >= 0.2144470405
    ):
        return True

    # Rescue: very large current-day movement,
    # but entry is still close to VWAP
    if (
        current_day_movement_to_recent_days_movement >= 16.83076642
        and entry_bar_ema_9_to_vwap <= 1.034873419
    ):
        return True

    # Rescue: previous bar volume expanded strongly,
    # and failed/fake reclaim pressure is high
    if (
        previous_bar_volume_to_its_previous_volume >= 2.382264508
        and failed_pressure_to_followthrough >= 0.7411936438
    ):
        return True

    # Rescue: weak reclaim close strength,
    # but inefficient breakout extension and EMA-distance structure are strong
    if (
        reclaim_close_strength_since_highest_high <= 0.08346153846
        and inefficient_breakout_extension >= 0.75
        and emas_distances_to_recent_bars_ema_distances >= 1.0
    ):
        return True

    return False
