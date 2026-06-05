#pylint: skip-file
# type: ignore
import concurrent.futures
import csv
import datetime
import glob
import math
import os
import pickle
from dataclasses import dataclass, asdict
from typing import Any, Optional

DISABLED_30PCT_FAMILIES = {"30pct_late_volume_shock_flat_base"}


def _is_disabled_30pct_family_context(context: object) -> bool:
    reason = getattr(context, "reason", None)
    breakout_type = getattr(context, "breakout_type", None)
    return reason in DISABLED_30PCT_FAMILIES or breakout_type in DISABLED_30PCT_FAMILIES


import buying_confirmator

# =========================
# CONFIG
# =========================

INPUT_FILES_GLOB = "model/training/data/*.json"

OUTPUT_COMBINED_FILE = "model/breakout_profile_combined.csv"

MAX_WORKERS = 10

MARKET_OPEN = datetime.time(9, 30)
MARKET_CLOSE = datetime.time(20, 0)  # v68: include post-market candidate bars such as LASE 2026-06-02 17:24

TARGET_GAIN_PCT = 0.20
FUTURE_ANALYSIS_MINUTES = 30
SUPPORT_LOW_INVALIDATION_TOLERANCE_PCT = 0.003
EMA20_CLOSE_BREAK_TOLERANCE_PCT = 0.0
EMA9_CLOSE_BREAK_TOLERANCE_PCT = 0.0



# =========================
# DATA CLASSES
# =========================

@dataclass
class BreakoutContext:
    breakout_type: str
    reason: str

    breakout_bar: Any

    resistance_bar: Any
    resistance_price: float

    lowest_low_since_resistance_bar: Any

    pullback_from_resistance_pct: float
    breakout_close_above_resistance_pct: float
    minutes_since_resistance: float

    volume_vs_previous_bar_ratio: float
    volume_vs_average_ratio: float

    # Raw helper metadata for validated structure/context patterns.
    helper_context: Optional[dict[str, Any]] = None


@dataclass
class BreakoutProfileRow:
    symbol: str
    trade_date: str
    is_positive: bool

    breakout_type: str
    reason: str
    breakout_time: datetime.datetime

    # Resistance / support structure
    resistance_bar_time: Optional[datetime.datetime]
    resistance_price: Optional[float]
    resistance_bar_close: Optional[float]
    resistance_bar_volume: Optional[float]
    resistance_bar_volume_average: Optional[float]
    resistance_bar_wick_percentage: Optional[float]

    lowest_low_since_resistance_time: Optional[datetime.datetime]
    lowest_low_since_resistance: Optional[float]
    lowest_low_since_resistance_close: Optional[float]
    lowest_low_since_resistance_bar_lower_wick_percentage: Optional[float]

    # Context-only pattern fields, grouped with other event times for visual review.
    multi_attack_absorption_base_before_entry: bool
    absorption_rejection_start_time: Optional[datetime.datetime]
    absorption_first_attack_time: Optional[datetime.datetime]
    absorption_second_attack_time: Optional[datetime.datetime]
    absorption_final_attack_time: Optional[datetime.datetime]
    absorption_zone_low: Optional[float]
    absorption_zone_high: Optional[float]
    absorption_attack_count: Optional[int]
    absorption_base_minutes: Optional[float]
    absorption_conflict_high_after_final_attack: Optional[float]

    pullback_from_resistance_pct: Optional[float]
    breakout_close_above_resistance_pct: Optional[float]
    minutes_since_resistance: Optional[float]

    # Breakout candle
    open: float
    high: float
    low: float
    close: float
    volume: float
    volume_average: float
    volume_average_last_3: float
    volume_average_last_10: float

    volume_vs_previous_bar_ratio: Optional[float]
    volume_vs_average_ratio: Optional[float]
    volume_vs_average_last_3_ratio: Optional[float]
    volume_vs_average_last_10_ratio: Optional[float]

    candle_body_pct_of_range: float
    upper_wick_pct_of_range: float
    lower_wick_pct_of_range: float
    close_position_in_range: float

    vwap: Optional[float]
    ema_9: Optional[float]
    ema_20: Optional[float]
    ema_12: Optional[float]
    ema_26: Optional[float]
    ema_200: Optional[float]
    macd: Optional[float]
    histogram: Optional[float]
    signal_line: Optional[float]

    close_to_ema_9_pct: Optional[float]
    close_to_ema_20_pct: Optional[float]
    close_to_vwap_pct: Optional[float]
    ema_9_to_vwap_pct: Optional[float]
    ema_9_to_ema_20_pct: Optional[float]

    # Pre-breakout windows
    pre_5_bar_gain_pct: Optional[float]
    pre_10_bar_gain_pct: Optional[float]
    pre_20_bar_gain_pct: Optional[float]

    pre_5_bar_range_pct: Optional[float]
    pre_10_bar_range_pct: Optional[float]
    pre_20_bar_range_pct: Optional[float]

    pre_5_bar_avg_volume_ratio: Optional[float]
    pre_10_bar_avg_volume_ratio: Optional[float]
    pre_20_bar_avg_volume_ratio: Optional[float]

    pre_5_bar_green_count: int
    pre_5_bar_red_count: int
    pre_10_bar_green_count: int
    pre_10_bar_red_count: int

    pre_5_bar_close_above_ema9_count: int
    pre_5_bar_close_above_vwap_count: int
    pre_10_bar_close_above_ema9_count: int
    pre_10_bar_close_above_vwap_count: int

    pre_5_bar_avg_close_to_ema9_pct: Optional[float]
    pre_5_bar_max_close_to_ema9_pct: Optional[float]
    pre_5_bar_avg_close_to_vwap_pct: Optional[float]
    pre_5_bar_max_close_to_vwap_pct: Optional[float]

    pre_10_bar_avg_close_to_ema9_pct: Optional[float]
    pre_10_bar_max_close_to_ema9_pct: Optional[float]
    pre_10_bar_avg_close_to_vwap_pct: Optional[float]
    pre_10_bar_max_close_to_vwap_pct: Optional[float]

    # Breakout history known live
    clean_breakout_count_today_before_current: int
    failed_clean_breakout_count_today_before_current: int
    previous_clean_breakout_failed_support_low: bool
    minutes_since_previous_clean_breakout: Optional[float]
    previous_clean_breakout_type: Optional[str]
    previous_clean_breakout_max_gain_until_current_pct: Optional[float]
    previous_clean_breakout_current_gain_pct: Optional[float]

    # Future labels for research only
    max_gain_after_breakout_next_30_minutes_pct: Optional[float]
    max_gain_after_breakout_next_30_minutes_abs: Optional[float]
    max_gain_after_breakout_next_30_minutes_high: Optional[float]
    max_gain_after_breakout_next_30_minutes_high_time: Optional[datetime.datetime]

    max_drawdown_after_breakout_next_30_minutes_pct: Optional[float]
    max_drawdown_after_breakout_next_30_minutes_abs: Optional[float]
    max_drawdown_after_breakout_next_30_minutes_low: Optional[float]
    max_drawdown_after_breakout_next_30_minutes_low_time: Optional[datetime.datetime]

    reached_20_percent_gain_within_30_minutes: bool
    minutes_until_20_percent_gain: Optional[float]

    went_below_lowest_low_before_20_percent_gain_30_minutes: bool
    lowest_low_break_before_20_percent_gain_30_minutes_time: Optional[datetime.datetime]
    lowest_low_break_before_20_percent_gain_30_minutes_price: Optional[float]

    # Full-session sequence label for research only.
    # Checks after breakout until market close, not only the next 30 minutes.
    reached_20_percent_gain_before_lowest_low_break_full_session: bool
    minutes_until_20_percent_gain_full_session: Optional[float]
    twenty_percent_gain_before_lowest_low_break_time_full_session: Optional[datetime.datetime]
    lowest_low_break_before_20_percent_gain_full_session: bool
    lowest_low_break_before_20_percent_gain_time_full_session: Optional[datetime.datetime]
    lowest_low_break_before_20_percent_gain_price_full_session: Optional[float]

    # Full-session max favorable excursion until setup-low invalidation.
    # This answers: after entry, what was the maximum gain before price went
    # below the setup support/lowest-low? If the low never breaks, it measures
    # max gain until market close.
    # Full-session EMA20 integrity label for research only.
    # Good entry = reaches +20% before the first future candle CLOSES below EMA20.
    reached_20_percent_gain_before_ema20_close_break_full_session: bool
    minutes_until_20_percent_gain_before_ema20_close_break_full_session: Optional[float]
    twenty_percent_gain_before_ema20_close_break_time_full_session: Optional[datetime.datetime]
    ema20_close_break_before_20_percent_gain_full_session: bool
    ema20_close_break_before_20_percent_gain_time_full_session: Optional[datetime.datetime]
    ema20_close_break_before_20_percent_gain_price_full_session: Optional[float]
    ema20_value_at_close_break_before_20_percent_gain_full_session: Optional[float]

    # Full-session EMA9 integrity label for research only.
    # Good trend row = reaches +20% before the first future candle CLOSES below EMA9.
    # Max-gain-before-EMA9-break tells us how far the trend could run while still
    # being defended by EMA9.
    reached_20_percent_gain_before_ema9_close_break_full_session: bool
    minutes_until_20_percent_gain_before_ema9_close_break_full_session: Optional[float]
    twenty_percent_gain_before_ema9_close_break_time_full_session: Optional[datetime.datetime]
    ema9_close_break_before_20_percent_gain_full_session: bool
    ema9_close_break_before_20_percent_gain_time_full_session: Optional[datetime.datetime]
    ema9_close_break_before_20_percent_gain_price_full_session: Optional[float]
    ema9_value_at_close_break_before_20_percent_gain_full_session: Optional[float]

    max_gain_before_ema9_close_break_full_session_pct: Optional[float]
    max_gain_before_ema9_close_break_full_session_abs: Optional[float]
    max_gain_before_ema9_close_break_full_session_high: Optional[float]
    max_gain_before_ema9_close_break_full_session_high_time: Optional[datetime.datetime]
    minutes_until_max_gain_before_ema9_close_break_full_session: Optional[float]
    ema9_close_break_for_max_gain_full_session: bool
    ema9_close_break_for_max_gain_full_session_time: Optional[datetime.datetime]
    ema9_close_break_for_max_gain_full_session_price: Optional[float]

    max_gain_before_lowest_low_break_full_session_pct: Optional[float]
    max_gain_before_lowest_low_break_full_session_abs: Optional[float]
    max_gain_before_lowest_low_break_full_session_high: Optional[float]
    max_gain_before_lowest_low_break_full_session_high_time: Optional[datetime.datetime]
    minutes_until_max_gain_before_lowest_low_break_full_session: Optional[float]
    lowest_low_break_for_max_gain_full_session: bool
    lowest_low_break_for_max_gain_full_session_time: Optional[datetime.datetime]
    lowest_low_break_for_max_gain_full_session_price: Optional[float]


@dataclass
class TrackedBreakout:
    breakout_bar: Any
    breakout_type: str
    lowest_low_since_resistance_bar: Any
    failed_support_low: bool = False


# =========================
# BASIC HELPERS
# =========================

def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        value = float(value)
        if math.isnan(value):
            return default
        return value
    except Exception:
        return default


def pct_change(base: Optional[float], value: Optional[float]) -> Optional[float]:
    base = safe_float(base, None)
    value = safe_float(value, None)

    if base is None or value is None or base <= 0:
        return None

    return (value - base) / base


def ratio(value: Optional[float], base: Optional[float]) -> Optional[float]:
    value = safe_float(value, None)
    base = safe_float(base, None)

    if value is None or base is None or base <= 0:
        return None

    return value / base


def minutes_between(start: datetime.datetime, end: datetime.datetime) -> float:
    return (end - start).total_seconds() / 60.0


def get_candle_stats(bar: Any) -> dict[str, float]:
    open_value = safe_float(getattr(bar, "open_value", None), 0.0)
    high = safe_float(getattr(bar, "high", None), 0.0)
    low = safe_float(getattr(bar, "low", None), 0.0)
    close = safe_float(getattr(bar, "close", None), 0.0)

    candle_range = max(0.000001, high - low)
    body = abs(close - open_value)
    upper_wick = high - max(open_value, close)
    lower_wick = min(open_value, close) - low

    return {
        "candle_body_pct_of_range": body / candle_range,
        "upper_wick_pct_of_range": max(0.0, upper_wick / candle_range),
        "lower_wick_pct_of_range": max(0.0, lower_wick / candle_range),
        "close_position_in_range": (close - low) / candle_range,
    }


def get_bars_same_day_until(
    bars: list[Any],
    current_bar: Any,
    include_current: bool = False,
) -> list[Any]:
    result = []

    for bar in bars:
        if bar.bar_time.date() != current_bar.bar_time.date():
            continue

        if include_current:
            if bar.bar_time <= current_bar.bar_time:
                result.append(bar)
        else:
            if bar.bar_time < current_bar.bar_time:
                result.append(bar)

    return sorted(result, key=lambda b: b.bar_time)


def get_future_bars(
    bars: list[Any],
    current_bar: Any,
    minutes: int,
) -> list[Any]:
    end_time = current_bar.bar_time + datetime.timedelta(minutes=minutes)

    return [
        bar
        for bar in bars
        if (
            bar.bar_time.date() == current_bar.bar_time.date()
            and current_bar.bar_time < bar.bar_time <= end_time
            and bar.bar_time.time() <= MARKET_CLOSE
        )
    ]


def get_future_bars_until_market_close(
    bars: list[Any],
    current_bar: Any,
) -> list[Any]:
    return [
        bar
        for bar in bars
        if (
            bar.bar_time.date() == current_bar.bar_time.date()
            and current_bar.bar_time < bar.bar_time
            and bar.bar_time.time() <= MARKET_CLOSE
        )
    ]


def load_pickle_data(file_path: str) -> Any:
    with open(file_path, "rb") as f:
        return pickle.load(f)


# =========================
# WINDOW FEATURE HELPERS
# =========================

def summarize_previous_window(
    bars_before_current: list[Any],
    window_size: int,
) -> dict[str, Any]:
    window = bars_before_current[-window_size:]

    prefix = f"pre_{window_size}_bar"

    if len(window) < 2:
        return {
            f"{prefix}_gain_pct": None,
            f"{prefix}_range_pct": None,
            f"{prefix}_avg_volume_ratio": None,
            f"{prefix}_green_count": 0,
            f"{prefix}_red_count": 0,
            f"{prefix}_close_above_ema9_count": 0,
            f"{prefix}_close_above_vwap_count": 0,
            f"{prefix}_avg_close_to_ema9_pct": None,
            f"{prefix}_max_close_to_ema9_pct": None,
            f"{prefix}_avg_close_to_vwap_pct": None,
            f"{prefix}_max_close_to_vwap_pct": None,
        }

    first_close = safe_float(getattr(window[0], "close", None), None)
    last_close = safe_float(getattr(window[-1], "close", None), None)

    highs = [safe_float(getattr(bar, "high", None), None) for bar in window]
    lows = [safe_float(getattr(bar, "low", None), None) for bar in window]
    highs = [x for x in highs if x is not None]
    lows = [x for x in lows if x is not None]

    volume_ratios = []
    close_to_ema9_values = []
    close_to_vwap_values = []

    green_count = 0
    red_count = 0
    close_above_ema9_count = 0
    close_above_vwap_count = 0

    for bar in window:
        open_value = safe_float(getattr(bar, "open_value", None), None)
        close = safe_float(getattr(bar, "close", None), None)
        volume = safe_float(getattr(bar, "volume", None), None)
        volume_average = safe_float(getattr(bar, "volume_average", None), None)
        ema9 = safe_float(getattr(bar, "ema_9", None), None)
        vwap = safe_float(getattr(bar, "vwap", None), None)

        if open_value is not None and close is not None:
            if close > open_value:
                green_count += 1
            elif close < open_value:
                red_count += 1

        vol_ratio = ratio(volume, volume_average)
        if vol_ratio is not None:
            volume_ratios.append(vol_ratio)

        close_to_ema9 = pct_change(ema9, close)
        if close_to_ema9 is not None:
            close_to_ema9_values.append(close_to_ema9)
            if close > ema9:
                close_above_ema9_count += 1

        close_to_vwap = pct_change(vwap, close)
        if close_to_vwap is not None:
            close_to_vwap_values.append(close_to_vwap)
            if close > vwap:
                close_above_vwap_count += 1

    gain_pct = pct_change(first_close, last_close)

    if highs and lows and first_close and first_close > 0:
        range_pct = (max(highs) - min(lows)) / first_close
    else:
        range_pct = None

    return {
        f"{prefix}_gain_pct": gain_pct,
        f"{prefix}_range_pct": range_pct,
        f"{prefix}_avg_volume_ratio": sum(volume_ratios) / len(volume_ratios) if volume_ratios else None,
        f"{prefix}_green_count": green_count,
        f"{prefix}_red_count": red_count,
        f"{prefix}_close_above_ema9_count": close_above_ema9_count,
        f"{prefix}_close_above_vwap_count": close_above_vwap_count,
        f"{prefix}_avg_close_to_ema9_pct": sum(close_to_ema9_values) / len(close_to_ema9_values) if close_to_ema9_values else None,
        f"{prefix}_max_close_to_ema9_pct": max(close_to_ema9_values) if close_to_ema9_values else None,
        f"{prefix}_avg_close_to_vwap_pct": sum(close_to_vwap_values) / len(close_to_vwap_values) if close_to_vwap_values else None,
        f"{prefix}_max_close_to_vwap_pct": max(close_to_vwap_values) if close_to_vwap_values else None,
    }


# =========================
# BREAKOUT DETECTORS
# =========================













# =========================
# TREND-START PATTERN DETECTORS
# =========================


















class _LiveStockWrapper:
    def __init__(
        self,
        bars: list[Any],
    ):
        self.bars = bars
        self.symbol = getattr(bars[0], "symbol", "") if bars else ""












def find_behavioral_buyer_control_phase_20pct_30min_entry_context(
    current_bar: Any,
    bars: list[Any],
    helper: Any = None,
    stock_wrapper: Any = None,
) -> Optional[BreakoutContext]:
    """
    Public momentum entry-bar detector for the 20% continuation study.

    This uses Helper.get_behavioral_buyer_control_phase_20pct_30min_entry_family(...) and converts
    the matched entry bar into the same BreakoutContext used by the exporter and
    future-label code. It intentionally detects first actionable ORB / VWAP /
    bull-flag / EMA-MACD / volume-breakout entry bars rather than every bar that
    remains in an uptrend.
    """

    # Fast prefilter before calling the expensive structural detector.
    # The helper checks complex resistance/support structures. There is no value
    # calling it on bars that are not constructive entry candidates at all.
    try:
        candle_range = float(current_bar.high) - float(current_bar.low)
        close_position_in_range = (float(current_bar.close) - float(current_bar.low)) / candle_range if candle_range > 0 else 0.0
        upper_wick_share_value = (float(current_bar.high) - max(float(current_bar.open_value), float(current_bar.close))) / candle_range if candle_range > 0 else 1.0
        volume_average = float(getattr(current_bar, "volume_average", 0.0) or 0.0)
        volume_ratio_value = float(current_bar.volume) / volume_average if volume_average > 0 else 0.0
        ema9_value = float(getattr(current_bar, "ema_9", 0.0) or 0.0)
    except Exception:
        return None

    if not (
        float(current_bar.close) > float(current_bar.open_value)
        and close_position_in_range >= 0.38
        and upper_wick_share_value <= 0.70
        and volume_ratio_value >= 0.50
        and (ema9_value <= 0 or float(current_bar.close) >= ema9_value * 0.965)
    ):
        return None

    if stock_wrapper is None:
        stock_wrapper = _LiveStockWrapper(bars=bars)
    if helper is None:
        helper = buying_confirmator.helper.Helper()

    # v84: the CSV/export path must use the same public gateway as the live
    # caller.  Earlier versions called the lower-level behavioral detector
    # directly, bypassing bar_has_potential(...) suppressions such as SDOT
    # 09:35/09:41/10:10 and duplicate delayed-exact-retest continuations.
    if hasattr(helper, "bar_has_potential"):
        bar_has_potential_result = helper.bar_has_potential(
            one_minute_timeframe_stock=stock_wrapper,
            potential_confirmation_bar=current_bar,
        )
        # v89: bar_has_potential now returns (bool, reason, context_details).
        # Keep backwards compatibility with older helpers returning 2-tuples.
        if isinstance(bar_has_potential_result, tuple) and len(bar_has_potential_result) >= 3:
            has_potential, potential_reason, _potential_context_details = bar_has_potential_result[:3]
        else:
            has_potential, potential_reason = bar_has_potential_result
        if not has_potential:
            return None
        matched_family = potential_reason
    else:
        # Fallback only for older helper/finder mismatches.
        if not hasattr(helper, "get_behavioral_buyer_control_phase_20pct_30min_entry_family"):
            return None
        matched_family = helper.get_behavioral_buyer_control_phase_20pct_30min_entry_family(
            one_minute_timeframe_stock=stock_wrapper,
            potential_confirmation_bar=current_bar,
        )
        if not matched_family:
            return None

    bars_before_current = get_bars_same_day_until(
        bars=bars,
        current_bar=current_bar,
        include_current=False,
    )

    if len(bars_before_current) < 3:
        return None

    # v22: use the exact resistance/support pair found by the helper.  Previous
    # versions re-computed these fields generically with max(recent highs) and
    # min(recent lows), which made the CSV look like invalid HKIT mappings even
    # when the helper matched a different internal support structure.
    helper_context = None
    if hasattr(helper, "get_last_behavioral_buyer_control_phase_20pct_30min_entry_context"):
        helper_context = helper.get_last_behavioral_buyer_control_phase_20pct_30min_entry_context()

    if helper_context:
        resistance_bar = helper_context.get("resistance_bar")
        support_low_bar = helper_context.get("support_bar")
        resistance_price = safe_float(helper_context.get("resistance_price"), None)
    else:
        # Fallback only for older helper/finder mismatches.
        recent_bars = bars_before_current[-20:] if len(bars_before_current) >= 20 else bars_before_current
        resistance_bar = max(
            recent_bars,
            key=lambda bar_object: safe_float(getattr(bar_object, "high", None), 0.0),
        )
        support_low_bar = min(
            recent_bars,
            key=lambda bar_object: safe_float(getattr(bar_object, "low", None), float("inf")),
        )
        resistance_price = safe_float(getattr(resistance_bar, "high", None), None)

    support_low = safe_float(getattr(support_low_bar, "low", None), None)
    breakout_close = safe_float(getattr(current_bar, "close", None), None)

    if (
        resistance_bar is None
        or support_low_bar is None
        or resistance_price is None
        or resistance_price <= 0
        or support_low is None
        or support_low <= 0
        or breakout_close is None
        or breakout_close <= 0
    ):
        return None

    previous_bar = bars_before_current[-1]

    volume_vs_previous_bar_ratio = ratio(
        safe_float(getattr(current_bar, "volume", None), None),
        safe_float(getattr(previous_bar, "volume", None), None),
    ) or 0.0

    volume_vs_average_ratio = ratio(
        safe_float(getattr(current_bar, "volume", None), None),
        safe_float(getattr(current_bar, "volume_average", None), None),
    ) or 0.0

    return BreakoutContext(
        breakout_type="behavioral_buyer_control_phase_20pct_30min_entry",
        reason=matched_family,
        breakout_bar=current_bar,
        resistance_bar=resistance_bar,
        resistance_price=resistance_price,
        lowest_low_since_resistance_bar=support_low_bar,
        pullback_from_resistance_pct=(resistance_price - support_low) / resistance_price,
        breakout_close_above_resistance_pct=(breakout_close - resistance_price) / resistance_price,
        minutes_since_resistance=minutes_between(resistance_bar.bar_time, current_bar.bar_time),
        volume_vs_previous_bar_ratio=volume_vs_previous_bar_ratio,
        volume_vs_average_ratio=volume_vs_average_ratio,
        helper_context=helper_context or {},
    )

def find_helper_30pct_trend_shift_candidate_context(
    current_bar: Any,
    bars: list[Any],
) -> Optional[BreakoutContext]:
    """
    Uses Helper.is_30pct_trend_shift_candidate(...) as a separate detector.

    This is the 30% trend-shift selector mined from the positive 30% trend
    starts and the later theory research pass: strict ORB quality breakout,
    aligned higher lows, dry-up reclaim, pre-20 rebuild, recent-high break,
    resistance/support, supply/demand, or late volume-shock flat-base expansion.
    The helper exports the matched 30% sub-family and enforces the current
    first-alert/late-family limiter.
    """

    stock_wrapper = _LiveStockWrapper(bars=bars)
    helper = buying_confirmator.helper.Helper()

    if not hasattr(helper, "is_30pct_trend_shift_candidate"):
        return None

    matched_family = None

    if hasattr(helper, "get_30pct_trend_shift_candidate_family"):
        matched_family = helper.get_30pct_trend_shift_candidate_family(
            one_minute_timeframe_stock=stock_wrapper,
            potential_confirmation_bar=current_bar,
        )
    else:
        has_pattern = helper.is_30pct_trend_shift_candidate(
            one_minute_timeframe_stock=stock_wrapper,
            potential_confirmation_bar=current_bar,
        )

        if has_pattern:
            matched_family = "30pct_unknown_family"

    if not matched_family:
        return None

    bars_before_current = get_bars_same_day_until(
        bars=bars,
        current_bar=current_bar,
        include_current=False,
    )

    # ORB can legitimately fire before 20 regular-session bars exist, so the
    # context builder must not discard early ORB rows. Use the available bars
    # for the generic context fields.
    if len(bars_before_current) < 3:
        return None

    recent_bars = bars_before_current[-20:]

    resistance_bar = max(
        recent_bars,
        key=lambda bar_object: safe_float(getattr(bar_object, "high", None), 0.0),
    )

    support_low_bar = min(
        recent_bars,
        key=lambda bar_object: safe_float(getattr(bar_object, "low", None), float("inf")),
    )

    resistance_price = safe_float(getattr(resistance_bar, "high", None), None)
    support_low = safe_float(getattr(support_low_bar, "low", None), None)
    breakout_close = safe_float(getattr(current_bar, "close", None), None)

    if (
        resistance_price is None
        or resistance_price <= 0
        or support_low is None
        or support_low <= 0
        or breakout_close is None
        or breakout_close <= 0
    ):
        return None

    previous_bar = bars_before_current[-1]

    volume_vs_previous_bar_ratio = ratio(
        safe_float(getattr(current_bar, "volume", None), None),
        safe_float(getattr(previous_bar, "volume", None), None),
    ) or 0.0

    volume_vs_average_ratio = ratio(
        safe_float(getattr(current_bar, "volume", None), None),
        safe_float(getattr(current_bar, "volume_average", None), None),
    ) or 0.0

    return BreakoutContext(
        breakout_type="thirty_pct_trend_shift_candidate",
        reason=matched_family,
        breakout_bar=current_bar,
        resistance_bar=resistance_bar,
        resistance_price=resistance_price,
        lowest_low_since_resistance_bar=support_low_bar,
        pullback_from_resistance_pct=(resistance_price - support_low) / resistance_price,
        breakout_close_above_resistance_pct=(breakout_close - resistance_price) / resistance_price,
        minutes_since_resistance=minutes_between(resistance_bar.bar_time, current_bar.bar_time),
        volume_vs_previous_bar_ratio=volume_vs_previous_bar_ratio,
        volume_vs_average_ratio=volume_vs_average_ratio,
    )




def find_breakout_context(
    current_bar: Any,
    bars: list[Any],
    allow_aligned_higher_low_buyer_ignition: bool = True,
    helper: Any = None,
    stock_wrapper: Any = None,
) -> Optional[BreakoutContext]:
    """
    Live/export decision for the public 20% momentum-entry experiment.

    Only the public 20% entry-bar detector is allowed to create an alert here:
    ORB5, ORB15, or 3+ confluence across VWAP reclaim, bull flag, EMA/MACD,
    and volume breakout families.

    `allow_aligned_higher_low_buyer_ignition` is kept in the signature for
    backward compatibility with existing callers, but it is ignored.
    """
    public_20pct_context = find_behavioral_buyer_control_phase_20pct_30min_entry_context(
        current_bar=current_bar,
        bars=bars,
        helper=helper,
        stock_wrapper=stock_wrapper,
    )

    if public_20pct_context is not None:
        return public_20pct_context

    return None


# =========================
# FUTURE RESEARCH LABELS
# =========================

def calculate_future_labels(
    bars: list[Any],
    context: BreakoutContext,
    future_minutes: int = FUTURE_ANALYSIS_MINUTES,
    target_gain_pct: float = TARGET_GAIN_PCT,
    invalidation_tolerance_pct: float = SUPPORT_LOW_INVALIDATION_TOLERANCE_PCT,
) -> dict[str, Any]:
    breakout_bar = context.breakout_bar
    future_bars = get_future_bars(bars, breakout_bar, future_minutes)
    future_bars_full_session = get_future_bars_until_market_close(bars, breakout_bar)

    breakout_close = safe_float(getattr(breakout_bar, "close", None), None)

    if breakout_close is None or breakout_close <= 0:
        return {
            "max_gain_after_breakout_next_30_minutes_pct": None,
            "max_gain_after_breakout_next_30_minutes_abs": None,
            "max_gain_after_breakout_next_30_minutes_high": None,
            "max_gain_after_breakout_next_30_minutes_high_time": None,
            "max_drawdown_after_breakout_next_30_minutes_pct": None,
            "max_drawdown_after_breakout_next_30_minutes_abs": None,
            "max_drawdown_after_breakout_next_30_minutes_low": None,
            "max_drawdown_after_breakout_next_30_minutes_low_time": None,
            "reached_20_percent_gain_within_30_minutes": False,
            "minutes_until_20_percent_gain": None,
            "went_below_lowest_low_before_20_percent_gain_30_minutes": False,
            "lowest_low_break_before_20_percent_gain_30_minutes_time": None,
            "lowest_low_break_before_20_percent_gain_30_minutes_price": None,
            "reached_20_percent_gain_before_lowest_low_break_full_session": False,
            "minutes_until_20_percent_gain_full_session": None,
            "twenty_percent_gain_before_lowest_low_break_time_full_session": None,
            "lowest_low_break_before_20_percent_gain_full_session": False,
            "lowest_low_break_before_20_percent_gain_time_full_session": None,
            "lowest_low_break_before_20_percent_gain_price_full_session": None,
            "reached_20_percent_gain_before_ema20_close_break_full_session": False,
            "minutes_until_20_percent_gain_before_ema20_close_break_full_session": None,
            "twenty_percent_gain_before_ema20_close_break_time_full_session": None,
            "ema20_close_break_before_20_percent_gain_full_session": False,
            "ema20_close_break_before_20_percent_gain_time_full_session": None,
            "ema20_close_break_before_20_percent_gain_price_full_session": None,
            "ema20_value_at_close_break_before_20_percent_gain_full_session": None,

            "reached_20_percent_gain_before_ema9_close_break_full_session": False,
            "minutes_until_20_percent_gain_before_ema9_close_break_full_session": None,
            "twenty_percent_gain_before_ema9_close_break_time_full_session": None,
            "ema9_close_break_before_20_percent_gain_full_session": False,
            "ema9_close_break_before_20_percent_gain_time_full_session": None,
            "ema9_close_break_before_20_percent_gain_price_full_session": None,
            "ema9_value_at_close_break_before_20_percent_gain_full_session": None,

            "max_gain_before_ema9_close_break_full_session_pct": None,
            "max_gain_before_ema9_close_break_full_session_abs": None,
            "max_gain_before_ema9_close_break_full_session_high": None,
            "max_gain_before_ema9_close_break_full_session_high_time": None,
            "minutes_until_max_gain_before_ema9_close_break_full_session": None,
            "ema9_close_break_for_max_gain_full_session": False,
            "ema9_close_break_for_max_gain_full_session_time": None,
            "ema9_close_break_for_max_gain_full_session_price": None,

            "max_gain_before_lowest_low_break_full_session_pct": None,
            "max_gain_before_lowest_low_break_full_session_abs": None,
            "max_gain_before_lowest_low_break_full_session_high": None,
            "max_gain_before_lowest_low_break_full_session_high_time": None,
            "minutes_until_max_gain_before_lowest_low_break_full_session": None,
            "lowest_low_break_for_max_gain_full_session": False,
            "lowest_low_break_for_max_gain_full_session_time": None,
            "lowest_low_break_for_max_gain_full_session_price": None,
        }

    max_high = None
    max_high_time = None
    min_low = None
    min_low_time = None

    reached_target = False
    minutes_until_target = None

    support_low = safe_float(getattr(context.lowest_low_since_resistance_bar, "low", None), None)
    invalidation_price = None
    if support_low is not None and support_low > 0:
        invalidation_price = support_low * (1 - invalidation_tolerance_pct)

    went_below_support_before_target = False
    support_break_time = None
    support_break_price = None

    for future_bar in future_bars:
        high = safe_float(getattr(future_bar, "high", None), None)
        low = safe_float(getattr(future_bar, "low", None), None)

        if high is not None:
            if max_high is None or high > max_high:
                max_high = high
                max_high_time = future_bar.bar_time

        if low is not None:
            if min_low is None or low < min_low:
                min_low = low
                min_low_time = future_bar.bar_time

        if (
            not reached_target
            and invalidation_price is not None
            and low is not None
            and low < invalidation_price
        ):
            went_below_support_before_target = True
            support_break_time = future_bar.bar_time
            support_break_price = low

        if not reached_target and high is not None and high >= breakout_close * (1 + target_gain_pct):
            reached_target = True
            minutes_until_target = minutes_between(breakout_bar.bar_time, future_bar.bar_time)
            # Stop checking "before target" support breaks after target is reached.
            # Still continue calculating max high / min low across full 30m window.

    # Full-session sequence label:
    # Did the breakout reach +20% before it broke below the setup support low,
    # checking from breakout until market close, not just 30 minutes?
    reached_target_before_support_break_full_session = False
    minutes_until_target_full_session = None
    target_time_full_session = None

    support_broke_before_target_full_session = False
    support_break_time_full_session = None
    support_break_price_full_session = None

    for future_bar in future_bars_full_session:
        high = safe_float(getattr(future_bar, "high", None), None)
        low = safe_float(getattr(future_bar, "low", None), None)

        if (
            invalidation_price is not None
            and low is not None
            and low < invalidation_price
        ):
            support_broke_before_target_full_session = True
            support_break_time_full_session = future_bar.bar_time
            support_break_price_full_session = low
            break

        if high is not None and high >= breakout_close * (1 + target_gain_pct):
            reached_target_before_support_break_full_session = True
            minutes_until_target_full_session = minutes_between(breakout_bar.bar_time, future_bar.bar_time)
            target_time_full_session = future_bar.bar_time
            break

    # EMA20 integrity sequence label:
    # Did the breakout reach +20% before the first future candle CLOSES below EMA20?
    # This is stricter than support-low invalidation and matches the idea that
    # the trend should continue without losing EMA20 after the entry bar.
    reached_target_before_ema20_close_break_full_session = False
    minutes_until_target_before_ema20_close_break_full_session = None
    target_before_ema20_close_break_time_full_session = None

    ema20_close_broke_before_target_full_session = False
    ema20_close_break_time_full_session = None
    ema20_close_break_price_full_session = None
    ema20_value_at_close_break_full_session = None

    for future_bar in future_bars_full_session:
        high = safe_float(getattr(future_bar, "high", None), None)
        close = safe_float(getattr(future_bar, "close", None), None)
        ema_20 = safe_float(getattr(future_bar, "ema_20", None), None)

        if (
            ema_20 is not None
            and ema_20 > 0
            and close is not None
            and close < ema_20 * (1 - EMA20_CLOSE_BREAK_TOLERANCE_PCT)
        ):
            ema20_close_broke_before_target_full_session = True
            ema20_close_break_time_full_session = future_bar.bar_time
            ema20_close_break_price_full_session = close
            ema20_value_at_close_break_full_session = ema_20
            break

        if high is not None and high >= breakout_close * (1 + target_gain_pct):
            reached_target_before_ema20_close_break_full_session = True
            minutes_until_target_before_ema20_close_break_full_session = minutes_between(
                breakout_bar.bar_time,
                future_bar.bar_time,
            )
            target_before_ema20_close_break_time_full_session = future_bar.bar_time
            break

    # EMA9 integrity sequence label:
    # Did the breakout reach +20% before the first future candle CLOSES below EMA9?
    # This is the clean "trend stayed defended by EMA9" label.
    reached_target_before_ema9_close_break_full_session = False
    minutes_until_target_before_ema9_close_break_full_session = None
    target_before_ema9_close_break_time_full_session = None

    ema9_close_broke_before_target_full_session = False
    ema9_close_break_time_full_session = None
    ema9_close_break_price_full_session = None
    ema9_value_at_close_break_full_session = None

    for future_bar in future_bars_full_session:
        high = safe_float(getattr(future_bar, "high", None), None)
        close = safe_float(getattr(future_bar, "close", None), None)
        ema_9 = safe_float(getattr(future_bar, "ema_9", None), None)

        if (
            ema_9 is not None
            and ema_9 > 0
            and close is not None
            and close < ema_9 * (1 - EMA9_CLOSE_BREAK_TOLERANCE_PCT)
        ):
            ema9_close_broke_before_target_full_session = True
            ema9_close_break_time_full_session = future_bar.bar_time
            ema9_close_break_price_full_session = close
            ema9_value_at_close_break_full_session = ema_9
            break

        if high is not None and high >= breakout_close * (1 + target_gain_pct):
            reached_target_before_ema9_close_break_full_session = True
            minutes_until_target_before_ema9_close_break_full_session = minutes_between(
                breakout_bar.bar_time,
                future_bar.bar_time,
            )
            target_before_ema9_close_break_time_full_session = future_bar.bar_time
            break

    # Max favorable gain after entry until first future candle closes below EMA9.
    # This answers: "how much max gain did the entry produce before the trend
    # fell apart / stopped being defended by EMA9?"
    max_gain_before_ema9_break_high = None
    max_gain_before_ema9_break_high_time = None
    ema9_break_for_max_gain = False
    ema9_break_for_max_gain_time = None
    ema9_break_for_max_gain_price = None

    for future_bar in future_bars_full_session:
        high = safe_float(getattr(future_bar, "high", None), None)
        close = safe_float(getattr(future_bar, "close", None), None)
        ema_9 = safe_float(getattr(future_bar, "ema_9", None), None)

        if (
            ema_9 is not None
            and ema_9 > 0
            and close is not None
            and close < ema_9 * (1 - EMA9_CLOSE_BREAK_TOLERANCE_PCT)
        ):
            ema9_break_for_max_gain = True
            ema9_break_for_max_gain_time = future_bar.bar_time
            ema9_break_for_max_gain_price = close
            break

        if high is not None:
            if max_gain_before_ema9_break_high is None or high > max_gain_before_ema9_break_high:
                max_gain_before_ema9_break_high = high
                max_gain_before_ema9_break_high_time = future_bar.bar_time

    max_gain_before_ema9_break_abs = None
    max_gain_before_ema9_break_pct = None
    minutes_until_max_gain_before_ema9_break = None

    if max_gain_before_ema9_break_high is not None:
        max_gain_before_ema9_break_abs = max_gain_before_ema9_break_high - breakout_close
        max_gain_before_ema9_break_pct = max_gain_before_ema9_break_abs / breakout_close
        minutes_until_max_gain_before_ema9_break = minutes_between(
            breakout_bar.bar_time,
            max_gain_before_ema9_break_high_time,
        )

    # Max favorable gain after entry until setup-low invalidation.
    # This is the metric for: "what was the maximum gain after entry
    # before price went below the setup low?" If the setup low never breaks,
    # it measures the maximum gain until market close.
    max_gain_before_low_break_high = None
    max_gain_before_low_break_high_time = None
    low_break_for_max_gain = False
    low_break_for_max_gain_time = None
    low_break_for_max_gain_price = None

    for future_bar in future_bars_full_session:
        high = safe_float(getattr(future_bar, "high", None), None)
        low = safe_float(getattr(future_bar, "low", None), None)

        if (
            invalidation_price is not None
            and low is not None
            and low < invalidation_price
        ):
            low_break_for_max_gain = True
            low_break_for_max_gain_time = future_bar.bar_time
            low_break_for_max_gain_price = low
            break

        if high is not None:
            if max_gain_before_low_break_high is None or high > max_gain_before_low_break_high:
                max_gain_before_low_break_high = high
                max_gain_before_low_break_high_time = future_bar.bar_time

    max_gain_before_low_break_abs = None
    max_gain_before_low_break_pct = None
    minutes_until_max_gain_before_low_break = None

    if max_gain_before_low_break_high is not None:
        max_gain_before_low_break_abs = max_gain_before_low_break_high - breakout_close
        max_gain_before_low_break_pct = max_gain_before_low_break_abs / breakout_close
        minutes_until_max_gain_before_low_break = minutes_between(
            breakout_bar.bar_time,
            max_gain_before_low_break_high_time,
        )

    max_gain_abs = None
    max_gain_pct = None

    if max_high is not None:
        max_gain_abs = max_high - breakout_close
        max_gain_pct = max_gain_abs / breakout_close

    max_drawdown_abs = None
    max_drawdown_pct = None

    if min_low is not None:
        max_drawdown_abs = breakout_close - min_low
        max_drawdown_pct = max_drawdown_abs / breakout_close

    return {
        "max_gain_after_breakout_next_30_minutes_pct": max_gain_pct,
        "max_gain_after_breakout_next_30_minutes_abs": max_gain_abs,
        "max_gain_after_breakout_next_30_minutes_high": max_high,
        "max_gain_after_breakout_next_30_minutes_high_time": max_high_time,

        "max_drawdown_after_breakout_next_30_minutes_pct": max_drawdown_pct,
        "max_drawdown_after_breakout_next_30_minutes_abs": max_drawdown_abs,
        "max_drawdown_after_breakout_next_30_minutes_low": min_low,
        "max_drawdown_after_breakout_next_30_minutes_low_time": min_low_time,

        "reached_20_percent_gain_within_30_minutes": reached_target,
        "minutes_until_20_percent_gain": minutes_until_target,

        "went_below_lowest_low_before_20_percent_gain_30_minutes": went_below_support_before_target,
        "lowest_low_break_before_20_percent_gain_30_minutes_time": support_break_time,
        "lowest_low_break_before_20_percent_gain_30_minutes_price": support_break_price,

        "reached_20_percent_gain_before_lowest_low_break_full_session": reached_target_before_support_break_full_session,
        "minutes_until_20_percent_gain_full_session": minutes_until_target_full_session,
        "twenty_percent_gain_before_lowest_low_break_time_full_session": target_time_full_session,
        "lowest_low_break_before_20_percent_gain_full_session": support_broke_before_target_full_session,
        "lowest_low_break_before_20_percent_gain_time_full_session": support_break_time_full_session,
        "lowest_low_break_before_20_percent_gain_price_full_session": support_break_price_full_session,

        "reached_20_percent_gain_before_ema20_close_break_full_session": reached_target_before_ema20_close_break_full_session,
        "minutes_until_20_percent_gain_before_ema20_close_break_full_session": minutes_until_target_before_ema20_close_break_full_session,
        "twenty_percent_gain_before_ema20_close_break_time_full_session": target_before_ema20_close_break_time_full_session,
        "ema20_close_break_before_20_percent_gain_full_session": ema20_close_broke_before_target_full_session,
        "ema20_close_break_before_20_percent_gain_time_full_session": ema20_close_break_time_full_session,
        "ema20_close_break_before_20_percent_gain_price_full_session": ema20_close_break_price_full_session,
        "ema20_value_at_close_break_before_20_percent_gain_full_session": ema20_value_at_close_break_full_session,

        "reached_20_percent_gain_before_ema9_close_break_full_session": reached_target_before_ema9_close_break_full_session,
        "minutes_until_20_percent_gain_before_ema9_close_break_full_session": minutes_until_target_before_ema9_close_break_full_session,
        "twenty_percent_gain_before_ema9_close_break_time_full_session": target_before_ema9_close_break_time_full_session,
        "ema9_close_break_before_20_percent_gain_full_session": ema9_close_broke_before_target_full_session,
        "ema9_close_break_before_20_percent_gain_time_full_session": ema9_close_break_time_full_session,
        "ema9_close_break_before_20_percent_gain_price_full_session": ema9_close_break_price_full_session,
        "ema9_value_at_close_break_before_20_percent_gain_full_session": ema9_value_at_close_break_full_session,

        "max_gain_before_ema9_close_break_full_session_pct": max_gain_before_ema9_break_pct,
        "max_gain_before_ema9_close_break_full_session_abs": max_gain_before_ema9_break_abs,
        "max_gain_before_ema9_close_break_full_session_high": max_gain_before_ema9_break_high,
        "max_gain_before_ema9_close_break_full_session_high_time": max_gain_before_ema9_break_high_time,
        "minutes_until_max_gain_before_ema9_close_break_full_session": minutes_until_max_gain_before_ema9_break,
        "ema9_close_break_for_max_gain_full_session": ema9_break_for_max_gain,
        "ema9_close_break_for_max_gain_full_session_time": ema9_break_for_max_gain_time,
        "ema9_close_break_for_max_gain_full_session_price": ema9_break_for_max_gain_price,

        "max_gain_before_lowest_low_break_full_session_pct": max_gain_before_low_break_pct,
        "max_gain_before_lowest_low_break_full_session_abs": max_gain_before_low_break_abs,
        "max_gain_before_lowest_low_break_full_session_high": max_gain_before_low_break_high,
        "max_gain_before_lowest_low_break_full_session_high_time": max_gain_before_low_break_high_time,
        "minutes_until_max_gain_before_lowest_low_break_full_session": minutes_until_max_gain_before_low_break,
        "lowest_low_break_for_max_gain_full_session": low_break_for_max_gain,
        "lowest_low_break_for_max_gain_full_session_time": low_break_for_max_gain_time,
        "lowest_low_break_for_max_gain_full_session_price": low_break_for_max_gain_price,
    }


# =========================
# BREAKOUT HISTORY HELPERS
# =========================

def update_tracked_breakouts(
    tracked_breakouts: list[TrackedBreakout],
    current_bar: Any,
    invalidation_tolerance_pct: float = SUPPORT_LOW_INVALIDATION_TOLERANCE_PCT,
) -> None:
    current_low = safe_float(getattr(current_bar, "low", None), None)

    if current_low is None:
        return

    for tracked in tracked_breakouts:
        support_low = safe_float(getattr(tracked.lowest_low_since_resistance_bar, "low", None), None)

        if support_low is None or support_low <= 0:
            continue

        invalidation_price = support_low * (1 - invalidation_tolerance_pct)

        if current_bar.bar_time > tracked.breakout_bar.bar_time and current_low < invalidation_price:
            tracked.failed_support_low = True


def get_previous_breakout_history(
    tracked_breakouts: list[TrackedBreakout],
    current_bar: Any,
) -> dict[str, Any]:
    previous_breakouts = [
        tracked
        for tracked in tracked_breakouts
        if tracked.breakout_bar.bar_time < current_bar.bar_time
    ]

    if not previous_breakouts:
        return {
            "clean_breakout_count_today_before_current": 0,
            "failed_clean_breakout_count_today_before_current": 0,
            "previous_clean_breakout_failed_support_low": False,
            "minutes_since_previous_clean_breakout": None,
            "previous_clean_breakout_type": None,
            "previous_clean_breakout_max_gain_until_current_pct": None,
            "previous_clean_breakout_current_gain_pct": None,
        }

    previous_breakouts = sorted(previous_breakouts, key=lambda x: x.breakout_bar.bar_time)
    last_breakout = previous_breakouts[-1]

    current_high = safe_float(getattr(current_bar, "high", None), None)
    current_close = safe_float(getattr(current_bar, "close", None), None)

    previous_breakout_close = safe_float(getattr(last_breakout.breakout_bar, "close", None), None)

    previous_current_gain_pct = pct_change(previous_breakout_close, current_close)

    # Max gain from previous breakout until current bar is calculated live-safe from bars already seen
    # in the main scanning function by passing current_high only for latest bar would be incomplete,
    # so this field is a current-price proxy unless calculated externally.
    previous_max_gain_until_current_pct = pct_change(previous_breakout_close, current_high)

    return {
        "clean_breakout_count_today_before_current": len(previous_breakouts),
        "failed_clean_breakout_count_today_before_current": sum(1 for tracked in previous_breakouts if tracked.failed_support_low),
        "previous_clean_breakout_failed_support_low": last_breakout.failed_support_low,
        "minutes_since_previous_clean_breakout": minutes_between(last_breakout.breakout_bar.bar_time, current_bar.bar_time),
        "previous_clean_breakout_type": last_breakout.breakout_type,
        "previous_clean_breakout_max_gain_until_current_pct": previous_max_gain_until_current_pct,
        "previous_clean_breakout_current_gain_pct": previous_current_gain_pct,
    }


# =========================
# ROW BUILDING
# =========================

def build_profile_row(
    data: dict[str, Any],
    bars: list[Any],
    context: BreakoutContext,
    tracked_breakouts: list[TrackedBreakout],
) -> BreakoutProfileRow:
    bar = context.breakout_bar
    bars_before_current = get_bars_same_day_until(bars, bar, include_current=False)

    previous_bar = bars_before_current[-1] if bars_before_current else None

    candle_stats = get_candle_stats(bar)

    window_5 = summarize_previous_window(bars_before_current, 5)
    window_10 = summarize_previous_window(bars_before_current, 10)
    window_20 = summarize_previous_window(bars_before_current, 20)

    history = get_previous_breakout_history(tracked_breakouts, bar)
    future_labels = calculate_future_labels(bars, context)

    day_stock = data.get("day_timeframe_stock")
    trade_date = str(bar.bar_time.date())
    is_positive = bool(getattr(day_stock, "is_positive", False))

    # Some user's data has specific_bar_time on day_timeframe_stock; this is optional here.
    if getattr(day_stock, "specific_bar_time", None) is not None:
        trade_date = str(day_stock.specific_bar_time.date())

    close = safe_float(getattr(bar, "close", None), 0.0)
    volume = safe_float(getattr(bar, "volume", None), 0.0)
    volume_average = safe_float(getattr(bar, "volume_average", None), 0.0)
    volume_average_last_3 = safe_float(getattr(bar, "volume_average_last_3", None), 0.0)
    volume_average_last_10 = safe_float(getattr(bar, "volume_average_last_10", None), 0.0)

    helper_context = context.helper_context or {}

    def _context_bar_time(key: str) -> Optional[datetime.datetime]:
        context_bar = helper_context.get(key)
        return getattr(context_bar, "bar_time", None) if context_bar is not None else None

    return BreakoutProfileRow(
        symbol=getattr(bar, "symbol", ""),
        trade_date=trade_date,
        is_positive=is_positive,

        breakout_type=context.breakout_type,
        reason=context.reason,
        breakout_time=bar.bar_time,

        resistance_bar_time=getattr(context.resistance_bar, "bar_time", None),
        resistance_price=context.resistance_price,
        resistance_bar_close=safe_float(getattr(context.resistance_bar, "close", None), None),
        resistance_bar_volume=safe_float(getattr(context.resistance_bar, "volume", None), None),
        resistance_bar_volume_average=safe_float(getattr(context.resistance_bar, "volume_average", None), None),
        resistance_bar_wick_percentage=safe_float(getattr(context.resistance_bar, "bar_wick_percentage", None), None),

        lowest_low_since_resistance_time=getattr(context.lowest_low_since_resistance_bar, "bar_time", None),
        lowest_low_since_resistance=safe_float(getattr(context.lowest_low_since_resistance_bar, "low", None), None),
        lowest_low_since_resistance_close=safe_float(getattr(context.lowest_low_since_resistance_bar, "close", None), None),
        lowest_low_since_resistance_bar_lower_wick_percentage=safe_float(getattr(context.lowest_low_since_resistance_bar, "bar_lower_wick_percentage", None), None),

        multi_attack_absorption_base_before_entry=bool(helper_context.get("multi_attack_absorption_base_before_entry", False)),
        absorption_rejection_start_time=_context_bar_time("absorption_rejection_start_bar"),
        absorption_first_attack_time=_context_bar_time("absorption_first_attack_bar"),
        absorption_second_attack_time=_context_bar_time("absorption_second_attack_bar"),
        absorption_final_attack_time=_context_bar_time("absorption_final_attack_bar"),
        absorption_zone_low=safe_float(helper_context.get("absorption_zone_low"), None),
        absorption_zone_high=safe_float(helper_context.get("absorption_zone_high"), None),
        absorption_attack_count=helper_context.get("absorption_attack_count"),
        absorption_base_minutes=safe_float(helper_context.get("absorption_base_minutes"), None),
        absorption_conflict_high_after_final_attack=safe_float(helper_context.get("absorption_conflict_high_after_final_attack"), None),

        pullback_from_resistance_pct=context.pullback_from_resistance_pct,
        breakout_close_above_resistance_pct=context.breakout_close_above_resistance_pct,
        minutes_since_resistance=context.minutes_since_resistance,

        open=safe_float(getattr(bar, "open_value", None), 0.0),
        high=safe_float(getattr(bar, "high", None), 0.0),
        low=safe_float(getattr(bar, "low", None), 0.0),
        close=close,
        volume=volume,
        volume_average=volume_average,
        volume_average_last_3=volume_average_last_3,
        volume_average_last_10=volume_average_last_10,

        volume_vs_previous_bar_ratio=ratio(volume, safe_float(getattr(previous_bar, "volume", None), None) if previous_bar else None),
        volume_vs_average_ratio=ratio(volume, volume_average),
        volume_vs_average_last_3_ratio=ratio(volume, volume_average_last_3),
        volume_vs_average_last_10_ratio=ratio(volume, volume_average_last_10),

        candle_body_pct_of_range=candle_stats["candle_body_pct_of_range"],
        upper_wick_pct_of_range=candle_stats["upper_wick_pct_of_range"],
        lower_wick_pct_of_range=candle_stats["lower_wick_pct_of_range"],
        close_position_in_range=candle_stats["close_position_in_range"],

        vwap=safe_float(getattr(bar, "vwap", None), None),
        ema_9=safe_float(getattr(bar, "ema_9", None), None),
        ema_20=safe_float(getattr(bar, "ema_20", None), None),
        ema_12=safe_float(getattr(bar, "ema_12", None), None),
        ema_26=safe_float(getattr(bar, "ema_26", None), None),
        ema_200=safe_float(getattr(bar, "ema_200", None), None),
        macd=safe_float(getattr(bar, "macd", None), None),
        histogram=safe_float(getattr(bar, "histogram", None), None),
        signal_line=safe_float(getattr(bar, "signal_line", None), None),

        close_to_ema_9_pct=pct_change(safe_float(getattr(bar, "ema_9", None), None), close),
        close_to_ema_20_pct=pct_change(safe_float(getattr(bar, "ema_20", None), None), close),
        close_to_vwap_pct=pct_change(safe_float(getattr(bar, "vwap", None), None), close),
        ema_9_to_vwap_pct=pct_change(safe_float(getattr(bar, "vwap", None), None), safe_float(getattr(bar, "ema_9", None), None)),
        ema_9_to_ema_20_pct=pct_change(safe_float(getattr(bar, "ema_20", None), None), safe_float(getattr(bar, "ema_9", None), None)),

        pre_5_bar_gain_pct=window_5["pre_5_bar_gain_pct"],
        pre_10_bar_gain_pct=window_10["pre_10_bar_gain_pct"],
        pre_20_bar_gain_pct=window_20["pre_20_bar_gain_pct"],

        pre_5_bar_range_pct=window_5["pre_5_bar_range_pct"],
        pre_10_bar_range_pct=window_10["pre_10_bar_range_pct"],
        pre_20_bar_range_pct=window_20["pre_20_bar_range_pct"],

        pre_5_bar_avg_volume_ratio=window_5["pre_5_bar_avg_volume_ratio"],
        pre_10_bar_avg_volume_ratio=window_10["pre_10_bar_avg_volume_ratio"],
        pre_20_bar_avg_volume_ratio=window_20["pre_20_bar_avg_volume_ratio"],

        pre_5_bar_green_count=window_5["pre_5_bar_green_count"],
        pre_5_bar_red_count=window_5["pre_5_bar_red_count"],
        pre_10_bar_green_count=window_10["pre_10_bar_green_count"],
        pre_10_bar_red_count=window_10["pre_10_bar_red_count"],

        pre_5_bar_close_above_ema9_count=window_5["pre_5_bar_close_above_ema9_count"],
        pre_5_bar_close_above_vwap_count=window_5["pre_5_bar_close_above_vwap_count"],
        pre_10_bar_close_above_ema9_count=window_10["pre_10_bar_close_above_ema9_count"],
        pre_10_bar_close_above_vwap_count=window_10["pre_10_bar_close_above_vwap_count"],

        pre_5_bar_avg_close_to_ema9_pct=window_5["pre_5_bar_avg_close_to_ema9_pct"],
        pre_5_bar_max_close_to_ema9_pct=window_5["pre_5_bar_max_close_to_ema9_pct"],
        pre_5_bar_avg_close_to_vwap_pct=window_5["pre_5_bar_avg_close_to_vwap_pct"],
        pre_5_bar_max_close_to_vwap_pct=window_5["pre_5_bar_max_close_to_vwap_pct"],

        pre_10_bar_avg_close_to_ema9_pct=window_10["pre_10_bar_avg_close_to_ema9_pct"],
        pre_10_bar_max_close_to_ema9_pct=window_10["pre_10_bar_max_close_to_ema9_pct"],
        pre_10_bar_avg_close_to_vwap_pct=window_10["pre_10_bar_avg_close_to_vwap_pct"],
        pre_10_bar_max_close_to_vwap_pct=window_10["pre_10_bar_max_close_to_vwap_pct"],

        clean_breakout_count_today_before_current=history["clean_breakout_count_today_before_current"],
        failed_clean_breakout_count_today_before_current=history["failed_clean_breakout_count_today_before_current"],
        previous_clean_breakout_failed_support_low=history["previous_clean_breakout_failed_support_low"],
        minutes_since_previous_clean_breakout=history["minutes_since_previous_clean_breakout"],
        previous_clean_breakout_type=history["previous_clean_breakout_type"],
        previous_clean_breakout_max_gain_until_current_pct=history["previous_clean_breakout_max_gain_until_current_pct"],
        previous_clean_breakout_current_gain_pct=history["previous_clean_breakout_current_gain_pct"],

        max_gain_after_breakout_next_30_minutes_pct=future_labels["max_gain_after_breakout_next_30_minutes_pct"],
        max_gain_after_breakout_next_30_minutes_abs=future_labels["max_gain_after_breakout_next_30_minutes_abs"],
        max_gain_after_breakout_next_30_minutes_high=future_labels["max_gain_after_breakout_next_30_minutes_high"],
        max_gain_after_breakout_next_30_minutes_high_time=future_labels["max_gain_after_breakout_next_30_minutes_high_time"],

        max_drawdown_after_breakout_next_30_minutes_pct=future_labels["max_drawdown_after_breakout_next_30_minutes_pct"],
        max_drawdown_after_breakout_next_30_minutes_abs=future_labels["max_drawdown_after_breakout_next_30_minutes_abs"],
        max_drawdown_after_breakout_next_30_minutes_low=future_labels["max_drawdown_after_breakout_next_30_minutes_low"],
        max_drawdown_after_breakout_next_30_minutes_low_time=future_labels["max_drawdown_after_breakout_next_30_minutes_low_time"],

        reached_20_percent_gain_within_30_minutes=future_labels["reached_20_percent_gain_within_30_minutes"],
        minutes_until_20_percent_gain=future_labels["minutes_until_20_percent_gain"],

        went_below_lowest_low_before_20_percent_gain_30_minutes=future_labels["went_below_lowest_low_before_20_percent_gain_30_minutes"],
        lowest_low_break_before_20_percent_gain_30_minutes_time=future_labels["lowest_low_break_before_20_percent_gain_30_minutes_time"],
        lowest_low_break_before_20_percent_gain_30_minutes_price=future_labels["lowest_low_break_before_20_percent_gain_30_minutes_price"],

        reached_20_percent_gain_before_lowest_low_break_full_session=future_labels["reached_20_percent_gain_before_lowest_low_break_full_session"],
        minutes_until_20_percent_gain_full_session=future_labels["minutes_until_20_percent_gain_full_session"],
        twenty_percent_gain_before_lowest_low_break_time_full_session=future_labels["twenty_percent_gain_before_lowest_low_break_time_full_session"],
        lowest_low_break_before_20_percent_gain_full_session=future_labels["lowest_low_break_before_20_percent_gain_full_session"],
        lowest_low_break_before_20_percent_gain_time_full_session=future_labels["lowest_low_break_before_20_percent_gain_time_full_session"],
        lowest_low_break_before_20_percent_gain_price_full_session=future_labels["lowest_low_break_before_20_percent_gain_price_full_session"],

        reached_20_percent_gain_before_ema20_close_break_full_session=future_labels["reached_20_percent_gain_before_ema20_close_break_full_session"],
        minutes_until_20_percent_gain_before_ema20_close_break_full_session=future_labels["minutes_until_20_percent_gain_before_ema20_close_break_full_session"],
        twenty_percent_gain_before_ema20_close_break_time_full_session=future_labels["twenty_percent_gain_before_ema20_close_break_time_full_session"],
        ema20_close_break_before_20_percent_gain_full_session=future_labels["ema20_close_break_before_20_percent_gain_full_session"],
        ema20_close_break_before_20_percent_gain_time_full_session=future_labels["ema20_close_break_before_20_percent_gain_time_full_session"],
        ema20_close_break_before_20_percent_gain_price_full_session=future_labels["ema20_close_break_before_20_percent_gain_price_full_session"],
        ema20_value_at_close_break_before_20_percent_gain_full_session=future_labels["ema20_value_at_close_break_before_20_percent_gain_full_session"],

        reached_20_percent_gain_before_ema9_close_break_full_session=future_labels["reached_20_percent_gain_before_ema9_close_break_full_session"],
        minutes_until_20_percent_gain_before_ema9_close_break_full_session=future_labels["minutes_until_20_percent_gain_before_ema9_close_break_full_session"],
        twenty_percent_gain_before_ema9_close_break_time_full_session=future_labels["twenty_percent_gain_before_ema9_close_break_time_full_session"],
        ema9_close_break_before_20_percent_gain_full_session=future_labels["ema9_close_break_before_20_percent_gain_full_session"],
        ema9_close_break_before_20_percent_gain_time_full_session=future_labels["ema9_close_break_before_20_percent_gain_time_full_session"],
        ema9_close_break_before_20_percent_gain_price_full_session=future_labels["ema9_close_break_before_20_percent_gain_price_full_session"],
        ema9_value_at_close_break_before_20_percent_gain_full_session=future_labels["ema9_value_at_close_break_before_20_percent_gain_full_session"],

        max_gain_before_ema9_close_break_full_session_pct=future_labels["max_gain_before_ema9_close_break_full_session_pct"],
        max_gain_before_ema9_close_break_full_session_abs=future_labels["max_gain_before_ema9_close_break_full_session_abs"],
        max_gain_before_ema9_close_break_full_session_high=future_labels["max_gain_before_ema9_close_break_full_session_high"],
        max_gain_before_ema9_close_break_full_session_high_time=future_labels["max_gain_before_ema9_close_break_full_session_high_time"],
        minutes_until_max_gain_before_ema9_close_break_full_session=future_labels["minutes_until_max_gain_before_ema9_close_break_full_session"],
        ema9_close_break_for_max_gain_full_session=future_labels["ema9_close_break_for_max_gain_full_session"],
        ema9_close_break_for_max_gain_full_session_time=future_labels["ema9_close_break_for_max_gain_full_session_time"],
        ema9_close_break_for_max_gain_full_session_price=future_labels["ema9_close_break_for_max_gain_full_session_price"],

        max_gain_before_lowest_low_break_full_session_pct=future_labels["max_gain_before_lowest_low_break_full_session_pct"],
        max_gain_before_lowest_low_break_full_session_abs=future_labels["max_gain_before_lowest_low_break_full_session_abs"],
        max_gain_before_lowest_low_break_full_session_high=future_labels["max_gain_before_lowest_low_break_full_session_high"],
        max_gain_before_lowest_low_break_full_session_high_time=future_labels["max_gain_before_lowest_low_break_full_session_high_time"],
        minutes_until_max_gain_before_lowest_low_break_full_session=future_labels["minutes_until_max_gain_before_lowest_low_break_full_session"],
        lowest_low_break_for_max_gain_full_session=future_labels["lowest_low_break_for_max_gain_full_session"],
        lowest_low_break_for_max_gain_full_session_time=future_labels["lowest_low_break_for_max_gain_full_session_time"],
        lowest_low_break_for_max_gain_full_session_price=future_labels["lowest_low_break_for_max_gain_full_session_price"],
    )


# =========================
# PER-FILE PROCESSING
# =========================

def process_training_file(file_path: str) -> list[BreakoutProfileRow]:
    data = load_pickle_data(file_path)

    stock = data.get("one_minute_timeframe_stock")
    day_stock = data.get("day_timeframe_stock")

    if stock is None or not hasattr(stock, "bars"):
        return []

    bars = sorted(stock.bars, key=lambda b: b.bar_time)

    # Keep only the target trade date if specific_bar_time exists.
    if getattr(day_stock, "specific_bar_time", None) is not None:
        trade_date = day_stock.specific_bar_time.date()
        bars = [bar for bar in bars if bar.bar_time.date() == trade_date]

    if len(bars) < 10:
        return []

    rows: list[BreakoutProfileRow] = []
    tracked_breakouts: list[TrackedBreakout] = []

    # Reuse these for the whole file/day. Creating a Helper and wrapper for
    # every bar made the hot path much slower and prevented any helper-side
    # caching from being useful.
    helper_for_day = buying_confirmator.helper.Helper()
    stock_wrapper_for_day = _LiveStockWrapper(bars=bars)

    for current_bar in bars:
        # We normally profile regular session only, including the 09:30 opening bar.
        # v115: preserve user change for pre-market expected entries. If the
        # expected/target bar itself is pre-market, do not skip pre-market bars;
        # otherwise keep the normal regular-session filter. This is required for
        # cases like RMSG 2026-06-05 08:30.
        expected_bar_time = getattr(stock, "expected_bar_time", None)
        if expected_bar_time is None:
            expected_bar_time = getattr(day_stock, "expected_bar_time", None)

        if (
            current_bar.bar_time.time() < MARKET_OPEN
            and (
                expected_bar_time is None
                or expected_bar_time.time() > MARKET_OPEN
            )
        ):
            continue

        if current_bar.bar_time.time() > MARKET_CLOSE:
            continue

        update_tracked_breakouts(tracked_breakouts, current_bar)

        history_before_current = get_previous_breakout_history(
            tracked_breakouts=tracked_breakouts,
            current_bar=current_bar,
        )

        # The aligned-higher-low pattern is a broad confirmed-trend pattern.
        # Latest profiling showed it works best only in the first 1-2 broader
        # detected setups of the day, so allow it only when there is at most
        # one previous detected breakout before the current bar. Other detector
        # families are still allowed after this point.
        allow_aligned_higher_low_buyer_ignition = (
            history_before_current["clean_breakout_count_today_before_current"] <= 1
        )

        context = find_breakout_context(
            current_bar=current_bar,
            bars=bars,
            allow_aligned_higher_low_buyer_ignition=allow_aligned_higher_low_buyer_ignition,
            helper=helper_for_day,
            stock_wrapper=stock_wrapper_for_day,
        )

        if context is None:
            continue

        row = build_profile_row(
            data=data,
            bars=bars,
            context=context,
            tracked_breakouts=tracked_breakouts,
        )

        rows.append(row)

        tracked_breakouts.append(
            TrackedBreakout(
                breakout_bar=current_bar,
                breakout_type=context.breakout_type,
                lowest_low_since_resistance_bar=context.lowest_low_since_resistance_bar,
                failed_support_low=False,
            )
        )

    return rows


# =========================
# CSV WRITING
# =========================

def _row_signal_key(row: BreakoutProfileRow) -> tuple:
    """Stable de-duplication key for one detected signal/context.

    The training folder can contain multiple source files for the same
    symbol/date. Without this guard, the exporter writes the same detected
    signal several times, which makes the CSV look like the same resistance /
    support properties are repeated 5x, 10x, etc.  We de-dupe by the actual
    signal identity, not by the whole row, because future-label fields can vary
    slightly across duplicate source files while the signal itself is identical.
    """
    return (
        row.symbol,
        row.trade_date,
        row.breakout_type,
        row.reason,
        row.breakout_time,
        row.resistance_bar_time,
        row.lowest_low_since_resistance_time,
    )


def dedupe_profile_rows(rows: list[BreakoutProfileRow]) -> list[BreakoutProfileRow]:
    seen: set[tuple] = set()
    deduped_rows: list[BreakoutProfileRow] = []
    for row in rows:
        key = _row_signal_key(row)
        if key in seen:
            continue
        seen.add(key)
        deduped_rows.append(row)
    return deduped_rows


def _training_file_symbol_date_key(file_path: str) -> tuple[str, str]:
    """Return (SYMBOL, YYYY-MM-DD) parsed from the training filename.

    Example:
        VCIG-2026-05-26 13:27:00.json -> ("VCIG", "2026-05-26")
        VCIG-2026-05-26 13:26:00.json -> ("VCIG", "2026-05-26")

    This intentionally keeps only one file per symbol/day.  It is much cheaper
    than loading every JSON/pickle just to discover duplicates, and it matches
    the current research workflow where we only need one intraday bar file per
    symbol/date.
    """
    filename = os.path.basename(file_path)
    stem = os.path.splitext(filename)[0]

    # Expected shape: SYMBOL-YYYY-MM-DD HH:MM:SS
    # Keep this simple and transparent; if the filename does not match, fall
    # back to the full stem so the file is not accidentally dropped.
    parts = stem.split("-", 1)
    if len(parts) != 2:
        return (stem.upper(), "")

    symbol = parts[0].upper()
    rest = parts[1]
    # rest starts with YYYY-MM-DD... after splitting only once.
    trade_date = rest[:10]
    if len(trade_date) == 10 and trade_date[4] == "-" and trade_date[7] == "-":
        return (symbol, trade_date)

    return (stem.upper(), "")


def distinct_training_files(file_paths: list[str]) -> list[str]:
    """Keep only one training file per SYMBOL-YYYY-MM-DD before processing."""
    seen: dict[tuple[str, str], str] = {}
    unique_files: list[str] = []
    duplicate_count = 0

    for file_path in sorted(file_paths):
        key = _training_file_symbol_date_key(file_path)
        if key in seen:
            duplicate_count += 1
            continue

        seen[key] = file_path
        unique_files.append(file_path)

    if duplicate_count:
        print(f"Removed {duplicate_count} duplicate symbol/day training files before processing")

    return unique_files


def write_rows_to_csv(
    rows: list[BreakoutProfileRow],
    output_file_path: str,
) -> None:
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    original_row_count = len(rows)
    rows = dedupe_profile_rows(rows)
    duplicate_count = original_row_count - len(rows)
    if duplicate_count:
        print(f"Removed {duplicate_count} duplicate signal rows before writing CSV")

    # v33: put all event/context time columns next to each other near the
    # beginning of the CSV so resistance/support/entry chronology is easy to
    # inspect visually. Keep every dataclass field, only change order.
    all_fieldnames = list(BreakoutProfileRow.__dataclass_fields__.keys())
    leading_fields = [
        "symbol",
        "trade_date",
        "is_positive",
        "breakout_type",
        "reason",
    ]
    time_fields = [
        field_name
        for field_name in all_fieldnames
        if (
            field_name not in leading_fields
            and (
                field_name == "breakout_time"
                or field_name.endswith("_time")
                or "_time_" in field_name
            )
        )
    ]
    remaining_fields = [
        field_name
        for field_name in all_fieldnames
        if field_name not in leading_fields and field_name not in time_fields
    ]
    fieldnames = [field_name for field_name in leading_fields if field_name in all_fieldnames] + time_fields + remaining_fields

    with open(output_file_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(asdict(row))

    print(f"Wrote {len(rows)} rows to {output_file_path}")


def main() -> None:
    raw_files = glob.glob(INPUT_FILES_GLOB)
    files = distinct_training_files(raw_files)

    print(f"Found {len(raw_files)} files, processing {len(files)} distinct files")

    all_rows: list[BreakoutProfileRow] = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_file = {
            executor.submit(process_training_file, file_path): file_path
            for file_path in files
        }

        completed = 0

        for future in concurrent.futures.as_completed(future_to_file):
            file_path = future_to_file[future]
            completed += 1

            try:
                file_rows = future.result()
                all_rows.extend(file_rows)
            except Exception as exc:
                print(f"Failed processing {file_path}: {exc}")

            if completed % 50 == 0:
                print(f"Completed {completed}/{len(files)} files. Rows so far: {len(all_rows)}")

    write_rows_to_csv(all_rows, OUTPUT_COMBINED_FILE)

    print("")
    print("Done.")
    print(f"Total rows: {len(all_rows)}")


if __name__ == "__main__":
    main()
