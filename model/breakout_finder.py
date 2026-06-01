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


# =========================
# CONFIG
# =========================

INPUT_FILES_GLOB = "model/training/data/*.json"

OUTPUT_POSITIVE_FILE = "model/training/breakout_profile_positive.csv"
OUTPUT_FALSE_POSITIVE_FILE = "model/training/breakout_profile_false_positive.csv"
OUTPUT_COMBINED_FILE = "model/training/breakout_profile_combined.csv"

MAX_WORKERS = 10

MARKET_OPEN = datetime.time(9, 30)
MARKET_CLOSE = datetime.time(16, 0)

TEN_PERCENT_TARGET = 0.10
FUTURE_ANALYSIS_MINUTES = 30
SUPPORT_LOW_INVALIDATION_TOLERANCE_PCT = 0.003


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

    reached_10_percent_gain_within_30_minutes: bool
    minutes_until_10_percent_gain: Optional[float]

    went_below_lowest_low_before_10_percent_gain_30_minutes: bool
    lowest_low_break_before_10_percent_gain_30_minutes_time: Optional[datetime.datetime]
    lowest_low_break_before_10_percent_gain_30_minutes_price: Optional[float]


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

def find_recent_resistance_context(
    current_bar: Any,
    bars: list[Any],
    lookback_minutes: int = 30,
    min_pullback_from_resistance_pct: float = 0.03,
    min_close_above_resistance_pct: float = 0.02,
) -> Optional[BreakoutContext]:
    bars_before_current = get_bars_same_day_until(bars, current_bar, include_current=False)

    if len(bars_before_current) < 3:
        return None

    lookback_start = current_bar.bar_time - datetime.timedelta(minutes=lookback_minutes)

    lookback_bars = [
        bar
        for bar in bars_before_current
        if lookback_start <= bar.bar_time < current_bar.bar_time
    ]

    if len(lookback_bars) < 3:
        return None

    # Find candidate resistance highs that:
    # 1. caused a pullback,
    # 2. were not closed above before current bar,
    # 3. are crossed decisively by current bar.
    candidates: list[tuple[float, Any, Any, float, float, float]] = []

    for resistance_bar in lookback_bars[:-1]:
        resistance_price = safe_float(getattr(resistance_bar, "high", None), None)
        if resistance_price is None or resistance_price <= 0:
            continue

        bars_after_resistance = [
            bar
            for bar in lookback_bars
            if bar.bar_time > resistance_bar.bar_time
        ]

        if not bars_after_resistance:
            continue

        lowest_low_bar = min(bars_after_resistance, key=lambda b: safe_float(getattr(b, "low", None), float("inf")))
        lowest_low = safe_float(getattr(lowest_low_bar, "low", None), None)
        if lowest_low is None or lowest_low <= 0:
            continue

        pullback_pct = (resistance_price - lowest_low) / resistance_price
        if pullback_pct < min_pullback_from_resistance_pct:
            continue

        prior_close_above_resistance = any(
            safe_float(getattr(bar, "close", None), 0.0) > resistance_price
            for bar in bars_after_resistance
        )

        if prior_close_above_resistance:
            continue

        close = safe_float(getattr(current_bar, "close", None), None)
        if close is None:
            continue

        close_above_resistance_pct = (close - resistance_price) / resistance_price
        if close_above_resistance_pct < min_close_above_resistance_pct:
            continue

        minutes_since_resistance = minutes_between(resistance_bar.bar_time, current_bar.bar_time)

        # Prefer the closest/highest meaningful resistance.
        # Score rewards current decisive cross and fresh pullback quality.
        score = (
            close_above_resistance_pct * 100
            + pullback_pct * 50
            - minutes_since_resistance * 0.02
        )

        candidates.append(
            (
                score,
                resistance_bar,
                lowest_low_bar,
                resistance_price,
                pullback_pct,
                close_above_resistance_pct,
            )
        )

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    _, resistance_bar, lowest_low_bar, resistance_price, pullback_pct, close_above_resistance_pct = candidates[0]

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
        breakout_type="volume_resistance_breakout",
        reason="resistance_cross_with_volume_expansion",
        breakout_bar=current_bar,
        resistance_bar=resistance_bar,
        resistance_price=resistance_price,
        lowest_low_since_resistance_bar=lowest_low_bar,
        pullback_from_resistance_pct=pullback_pct,
        breakout_close_above_resistance_pct=close_above_resistance_pct,
        minutes_since_resistance=minutes_between(resistance_bar.bar_time, current_bar.bar_time),
        volume_vs_previous_bar_ratio=volume_vs_previous_bar_ratio,
        volume_vs_average_ratio=volume_vs_average_ratio,
    )


def is_candle_quality_good(
    bar: Any,
    min_close_position: float = 0.70,
    max_upper_wick: float = 0.25,
) -> bool:
    open_value = safe_float(getattr(bar, "open_value", None), None)
    close = safe_float(getattr(bar, "close", None), None)

    if open_value is None or close is None:
        return False

    if close <= open_value:
        return False

    stats = get_candle_stats(bar)

    if stats["close_position_in_range"] < min_close_position:
        return False

    if stats["upper_wick_pct_of_range"] > max_upper_wick:
        return False

    return True


def find_volume_resistance_breakout_context(
    current_bar: Any,
    bars: list[Any],
) -> Optional[BreakoutContext]:
    context = find_recent_resistance_context(
        current_bar=current_bar,
        bars=bars,
        lookback_minutes=30,
        min_pullback_from_resistance_pct=0.03,
        min_close_above_resistance_pct=0.02,
    )

    if context is None:
        return None

    if context.volume_vs_previous_bar_ratio < 1.8:
        return None

    if context.volume_vs_average_ratio < 1.8:
        return None

    if not is_candle_quality_good(
        bar=current_bar,
        min_close_position=0.70,
        max_upper_wick=0.25,
    ):
        return None

    return context


def find_intraday_extreme_volume_ignition_context(
    current_bar: Any,
    bars: list[Any],
) -> Optional[BreakoutContext]:
    context = find_recent_resistance_context(
        current_bar=current_bar,
        bars=bars,
        lookback_minutes=20,
        min_pullback_from_resistance_pct=0.01,
        min_close_above_resistance_pct=0.08,
    )

    if context is None:
        return None

    if context.volume_vs_previous_bar_ratio < 10.0:
        return None

    if context.volume_vs_average_ratio < 5.0:
        return None

    if not is_candle_quality_good(
        bar=current_bar,
        min_close_position=0.80,
        max_upper_wick=0.20,
    ):
        return None

    context.breakout_type = "intraday_extreme_volume_ignition"
    context.reason = "extreme_volume_ignition_through_fresh_resistance"

    return context


def find_market_open_premarket_runner_reclaim_context(
    current_bar: Any,
    bars: list[Any],
) -> Optional[BreakoutContext]:
    if not (datetime.time(9, 30) <= current_bar.bar_time.time() <= datetime.time(9, 35)):
        return None

    bars_before_current = get_bars_same_day_until(bars, current_bar, include_current=False)

    if len(bars_before_current) < 15:
        return None

    previous_bar = bars_before_current[-1]

    premarket_bars = [
        bar
        for bar in bars_before_current
        if datetime.time(4, 0) <= bar.bar_time.time() < datetime.time(9, 30)
    ]

    if len(premarket_bars) < 10:
        return None

    # Earlier premarket ignition.
    earlier_ignition_bars = [
        bar
        for bar in premarket_bars
        if (
            ratio(getattr(bar, "volume", None), getattr(bar, "volume_average", None)) is not None
            and ratio(getattr(bar, "volume", None), getattr(bar, "volume_average", None)) >= 4.0
            and safe_float(getattr(bar, "close", None), 0.0) > safe_float(getattr(bar, "vwap", None), float("inf"))
            and safe_float(getattr(bar, "close", None), 0.0) > safe_float(getattr(bar, "ema_9", None), float("inf"))
            and safe_float(getattr(bar, "close", None), 0.0) > safe_float(getattr(bar, "open_value", None), float("inf"))
        )
    ]

    if not earlier_ignition_bars:
        return None

    premarket_high_bar = max(premarket_bars, key=lambda b: safe_float(getattr(b, "high", None), 0.0))

    current_low = safe_float(getattr(current_bar, "low", None), None)
    if current_low is None or current_low <= 0:
        return None

    if safe_float(getattr(premarket_high_bar, "high", None), 0.0) <= current_low * 1.08:
        return None

    recent_pullback_bars = [
        bar
        for bar in bars_before_current
        if current_bar.bar_time - datetime.timedelta(minutes=15) <= bar.bar_time < current_bar.bar_time
    ]

    if len(recent_pullback_bars) < 5:
        return None

    had_recent_close_below_ema9 = any(
        safe_float(getattr(bar, "close", None), 0.0) < safe_float(getattr(bar, "ema_9", None), -float("inf"))
        for bar in recent_pullback_bars
    )

    if not had_recent_close_below_ema9:
        return None

    recent_closes_above_vwap_count = sum(
        1
        for bar in recent_pullback_bars
        if safe_float(getattr(bar, "close", None), 0.0) > safe_float(getattr(bar, "vwap", None), float("inf"))
    )

    if recent_closes_above_vwap_count < len(recent_pullback_bars) * 0.7:
        return None

    recent_volume_ratios = [
        ratio(getattr(bar, "volume", None), getattr(bar, "volume_average", None))
        for bar in recent_pullback_bars
    ]
    recent_volume_ratios = [x for x in recent_volume_ratios if x is not None]

    if not recent_volume_ratios:
        return None

    recent_average_volume_ratio = sum(recent_volume_ratios) / len(recent_volume_ratios)

    if recent_average_volume_ratio > 0.8:
        return None

    pullback_support_low_bar = min(recent_pullback_bars, key=lambda b: safe_float(getattr(b, "low", None), float("inf")))
    pullback_support_low = safe_float(getattr(pullback_support_low_bar, "low", None), None)

    if pullback_support_low is None or pullback_support_low <= 0:
        return None

    if current_low > pullback_support_low * 1.015:
        return None

    if current_low < pullback_support_low * 0.985:
        return None

    recent_micro_resistance_bar = max(recent_pullback_bars[-7:], key=lambda b: safe_float(getattr(b, "high", None), 0.0))
    recent_micro_resistance = safe_float(getattr(recent_micro_resistance_bar, "high", None), None)

    current_close = safe_float(getattr(current_bar, "close", None), None)
    if recent_micro_resistance is None or recent_micro_resistance <= 0 or current_close is None:
        return None

    breakout_close_above_micro_resistance_pct = (
        current_close - recent_micro_resistance
    ) / recent_micro_resistance

    if breakout_close_above_micro_resistance_pct < 0.02:
        return None

    volume_vs_previous_bar_ratio = ratio(getattr(current_bar, "volume", None), getattr(previous_bar, "volume", None)) or 0.0
    volume_vs_average_ratio = ratio(getattr(current_bar, "volume", None), getattr(current_bar, "volume_average", None)) or 0.0

    if volume_vs_previous_bar_ratio < 5.0:
        return None

    if volume_vs_average_ratio < 1.5:
        return None

    if not is_candle_quality_good(current_bar, min_close_position=0.80, max_upper_wick=0.20):
        return None

    if current_close <= safe_float(getattr(current_bar, "ema_9", None), float("inf")):
        return None

    if current_close <= safe_float(getattr(current_bar, "ema_20", None), float("inf")):
        return None

    if current_close <= safe_float(getattr(current_bar, "vwap", None), float("inf")):
        return None

    context = BreakoutContext(
        breakout_type="market_open_premarket_runner_reclaim",
        reason="premarket_runner_open_reclaim_after_reset",
        breakout_bar=current_bar,
        resistance_bar=recent_micro_resistance_bar,
        resistance_price=recent_micro_resistance,
        lowest_low_since_resistance_bar=pullback_support_low_bar,
        pullback_from_resistance_pct=(recent_micro_resistance - pullback_support_low) / recent_micro_resistance,
        breakout_close_above_resistance_pct=breakout_close_above_micro_resistance_pct,
        minutes_since_resistance=minutes_between(recent_micro_resistance_bar.bar_time, current_bar.bar_time),
        volume_vs_previous_bar_ratio=volume_vs_previous_bar_ratio,
        volume_vs_average_ratio=volume_vs_average_ratio,
    )

    return context


def find_deep_pullback_support_reclaim_context(
    current_bar: Any,
    bars: list[Any],
) -> Optional[BreakoutContext]:
    bars_before_current = get_bars_same_day_until(bars, current_bar, include_current=False)

    if len(bars_before_current) < 20:
        return None

    recent_90_min_bars = [
        bar
        for bar in bars_before_current
        if bar.bar_time >= current_bar.bar_time - datetime.timedelta(minutes=90)
    ]

    if len(recent_90_min_bars) < 10:
        return None

    prior_high_bar = max(recent_90_min_bars, key=lambda b: safe_float(getattr(b, "high", None), 0.0))

    prior_high = safe_float(getattr(prior_high_bar, "high", None), None)
    current_low = safe_float(getattr(current_bar, "low", None), None)

    if prior_high is None or prior_high <= 0 or current_low is None or current_low <= 0:
        return None

    prior_high_to_current_low_pullback_pct = (prior_high - current_low) / prior_high

    if prior_high_to_current_low_pullback_pct < 0.20:
        return None

    if prior_high_to_current_low_pullback_pct > 0.55:
        return None

    bars_after_prior_high = [
        bar
        for bar in bars_before_current
        if bar.bar_time > prior_high_bar.bar_time
    ]

    if len(bars_after_prior_high) < 3:
        return None

    pullback_low_bar = min(bars_after_prior_high, key=lambda b: safe_float(getattr(b, "low", None), float("inf")))
    pullback_low = safe_float(getattr(pullback_low_bar, "low", None), None)

    if pullback_low is None or pullback_low <= 0:
        return None

    if pullback_low_bar.bar_time < current_bar.bar_time - datetime.timedelta(minutes=15):
        return None

    bars_after_pullback_low = [
        bar
        for bar in bars_before_current
        if bar.bar_time > pullback_low_bar.bar_time
    ]

    broke_pullback_low_after_it_formed = any(
        safe_float(getattr(bar, "low", None), float("inf")) < pullback_low * 0.997
        for bar in bars_after_pullback_low
    )

    if broke_pullback_low_after_it_formed:
        return None

    if current_low < pullback_low * 0.997:
        return None

    recent_reclaim_window_bars = [
        bar
        for bar in bars_before_current
        if bar.bar_time >= current_bar.bar_time - datetime.timedelta(minutes=10)
    ]

    if len(recent_reclaim_window_bars) < 3:
        return None

    recent_micro_resistance_bar = max(recent_reclaim_window_bars, key=lambda b: safe_float(getattr(b, "high", None), 0.0))
    recent_micro_resistance = safe_float(getattr(recent_micro_resistance_bar, "high", None), None)
    current_close = safe_float(getattr(current_bar, "close", None), None)

    if recent_micro_resistance is None or recent_micro_resistance <= 0 or current_close is None:
        return None

    close_above_micro_resistance_pct = (current_close - recent_micro_resistance) / recent_micro_resistance

    if close_above_micro_resistance_pct < 0.015:
        return None

    if current_close <= safe_float(getattr(current_bar, "ema_9", None), float("inf")):
        return None

    if current_close <= safe_float(getattr(current_bar, "ema_20", None), float("inf")):
        return None

    if current_close <= safe_float(getattr(current_bar, "vwap", None), float("inf")):
        return None

    previous_bar = bars_before_current[-1]

    volume_vs_previous_bar_ratio = ratio(getattr(current_bar, "volume", None), getattr(previous_bar, "volume", None)) or 0.0
    volume_vs_average_ratio = ratio(getattr(current_bar, "volume", None), getattr(current_bar, "volume_average", None)) or 0.0

    if volume_vs_previous_bar_ratio < 1.5:
        return None

    if volume_vs_average_ratio < 1.5:
        return None

    if not is_candle_quality_good(current_bar, min_close_position=0.80, max_upper_wick=0.20):
        return None

    return BreakoutContext(
        breakout_type="deep_pullback_support_reclaim_breakout",
        reason="deep_pullback_support_hold_and_reclaim",
        breakout_bar=current_bar,
        resistance_bar=recent_micro_resistance_bar,
        resistance_price=recent_micro_resistance,
        lowest_low_since_resistance_bar=pullback_low_bar,
        pullback_from_resistance_pct=(recent_micro_resistance - pullback_low) / recent_micro_resistance,
        breakout_close_above_resistance_pct=close_above_micro_resistance_pct,
        minutes_since_resistance=minutes_between(recent_micro_resistance_bar.bar_time, current_bar.bar_time),
        volume_vs_previous_bar_ratio=volume_vs_previous_bar_ratio,
        volume_vs_average_ratio=volume_vs_average_ratio,
    )


# =========================
# TREND-START PATTERN DETECTORS
# =========================


def build_micro_context(
    current_bar: Any,
    bars_before_current: list[Any],
    breakout_type: str,
    reason: str,
    resistance_window_minutes: int = 10,
) -> Optional[BreakoutContext]:
    """
    Creates a BreakoutContext for trend-start patterns that break a recent micro-resistance
    rather than a formal swing resistance.
    """
    if not bars_before_current:
        return None

    current_close = safe_float(getattr(current_bar, "close", None), None)
    current_volume = safe_float(getattr(current_bar, "volume", None), None)
    current_volume_average = safe_float(getattr(current_bar, "volume_average", None), None)

    if current_close is None or current_close <= 0:
        return None

    recent_bars = [
        bar
        for bar in bars_before_current
        if bar.bar_time >= current_bar.bar_time - datetime.timedelta(minutes=resistance_window_minutes)
    ]

    if len(recent_bars) < 3:
        return None

    resistance_bar = max(recent_bars, key=lambda b: safe_float(getattr(b, "high", None), 0.0))
    support_bar = min(recent_bars, key=lambda b: safe_float(getattr(b, "low", None), float("inf")))

    resistance_price = safe_float(getattr(resistance_bar, "high", None), None)
    support_low = safe_float(getattr(support_bar, "low", None), None)

    if resistance_price is None or resistance_price <= 0 or support_low is None or support_low <= 0:
        return None

    previous_bar = bars_before_current[-1]

    return BreakoutContext(
        breakout_type=breakout_type,
        reason=reason,
        breakout_bar=current_bar,
        resistance_bar=resistance_bar,
        resistance_price=resistance_price,
        lowest_low_since_resistance_bar=support_bar,
        pullback_from_resistance_pct=(resistance_price - support_low) / resistance_price,
        breakout_close_above_resistance_pct=(current_close - resistance_price) / resistance_price,
        minutes_since_resistance=minutes_between(resistance_bar.bar_time, current_bar.bar_time),
        volume_vs_previous_bar_ratio=ratio(current_volume, safe_float(getattr(previous_bar, "volume", None), None)) or 0.0,
        volume_vs_average_ratio=ratio(current_volume, current_volume_average) or 0.0,
    )


def find_vwap_reclaim_trend_start_context(
    current_bar: Any,
    bars: list[Any],
) -> Optional[BreakoutContext]:
    """
    Pattern: price was weak/near-below VWAP, then reclaims VWAP/EMA9 with volume and a strong close.
    This tries to catch a new trend transition, not a late continuation.
    """
    bars_before_current = get_bars_same_day_until(bars, current_bar, include_current=False)

    if len(bars_before_current) < 10:
        return None

    previous_bar = bars_before_current[-1]
    current_close = safe_float(getattr(current_bar, "close", None), None)
    current_vwap = safe_float(getattr(current_bar, "vwap", None), None)
    current_ema9 = safe_float(getattr(current_bar, "ema_9", None), None)
    previous_close = safe_float(getattr(previous_bar, "close", None), None)
    previous_vwap = safe_float(getattr(previous_bar, "vwap", None), None)

    if None in (current_close, current_vwap, current_ema9, previous_close, previous_vwap):
        return None

    if current_close <= current_vwap:
        return None

    if current_close <= current_ema9:
        return None

    # Require actual reclaim or recent weakness near/below VWAP, not already extended above VWAP.
    recent_10 = bars_before_current[-10:]
    closes_below_or_near_vwap = sum(
        1
        for bar in recent_10
        if pct_change(safe_float(getattr(bar, "vwap", None), None), safe_float(getattr(bar, "close", None), None)) is not None
        and pct_change(safe_float(getattr(bar, "vwap", None), None), safe_float(getattr(bar, "close", None), None)) <= 0.015
    )

    if closes_below_or_near_vwap < 3 and previous_close > previous_vwap:
        return None

    # Avoid very overheated VWAP reclaims.
    if pct_change(current_vwap, current_close) is not None and pct_change(current_vwap, current_close) > 0.12:
        return None

    if ratio(getattr(current_bar, "volume", None), getattr(current_bar, "volume_average", None)) is None:
        return None

    if ratio(getattr(current_bar, "volume", None), getattr(current_bar, "volume_average", None)) < 1.8:
        return None

    if not is_candle_quality_good(current_bar, min_close_position=0.78, max_upper_wick=0.22):
        return None

    context = build_micro_context(
        current_bar=current_bar,
        bars_before_current=bars_before_current,
        breakout_type="vwap_reclaim_trend_start",
        reason="vwap_reclaim_with_volume_and_strong_close",
        resistance_window_minutes=10,
    )

    if context is None:
        return None

    # It should break or at least close very near recent micro resistance.
    if context.breakout_close_above_resistance_pct < -0.002:
        return None

    return context


def find_ema_reclaim_after_pullback_context(
    current_bar: Any,
    bars: list[Any],
) -> Optional[BreakoutContext]:
    """
    Pattern: existing runner pulls back, then current bar reclaims EMA9/EMA20 and recent micro resistance.
    This is the broader version of the HKIT-type support reclaim.
    """
    bars_before_current = get_bars_same_day_until(bars, current_bar, include_current=False)

    if len(bars_before_current) < 20:
        return None

    current_close = safe_float(getattr(current_bar, "close", None), None)
    current_ema9 = safe_float(getattr(current_bar, "ema_9", None), None)
    current_ema20 = safe_float(getattr(current_bar, "ema_20", None), None)
    current_vwap = safe_float(getattr(current_bar, "vwap", None), None)

    if None in (current_close, current_ema9, current_ema20, current_vwap):
        return None

    if current_close <= current_ema9 or current_close <= current_ema20 or current_close <= current_vwap:
        return None

    recent_60 = [
        bar
        for bar in bars_before_current
        if bar.bar_time >= current_bar.bar_time - datetime.timedelta(minutes=60)
    ]

    if len(recent_60) < 10:
        return None

    prior_high_bar = max(recent_60, key=lambda b: safe_float(getattr(b, "high", None), 0.0))
    prior_high = safe_float(getattr(prior_high_bar, "high", None), None)
    current_low = safe_float(getattr(current_bar, "low", None), None)

    if prior_high is None or prior_high <= 0 or current_low is None or current_low <= 0:
        return None

    pullback_from_prior_high = (prior_high - current_low) / prior_high

    if pullback_from_prior_high < 0.08:
        return None

    if pullback_from_prior_high > 0.55:
        return None

    recent_10 = bars_before_current[-10:]

    had_recent_close_below_ema9_or_ema20 = any(
        safe_float(getattr(bar, "close", None), 0.0) < safe_float(getattr(bar, "ema_9", None), -float("inf"))
        or safe_float(getattr(bar, "close", None), 0.0) < safe_float(getattr(bar, "ema_20", None), -float("inf"))
        for bar in recent_10
    )

    if not had_recent_close_below_ema9_or_ema20:
        return None

    context = build_micro_context(
        current_bar=current_bar,
        bars_before_current=bars_before_current,
        breakout_type="ema_reclaim_after_pullback",
        reason="ema9_ema20_reclaim_after_pullback",
        resistance_window_minutes=10,
    )

    if context is None:
        return None

    if context.breakout_close_above_resistance_pct < 0.005:
        return None

    if context.volume_vs_previous_bar_ratio < 1.4:
        return None

    if context.volume_vs_average_ratio < 1.3:
        return None

    if not is_candle_quality_good(current_bar, min_close_position=0.78, max_upper_wick=0.22):
        return None

    return context


def find_volume_dryup_expansion_context(
    current_bar: Any,
    bars: list[Any],
) -> Optional[BreakoutContext]:
    """
    Pattern: volume dries up during a short base/pullback, then expands through micro resistance.
    """
    bars_before_current = get_bars_same_day_until(bars, current_bar, include_current=False)

    if len(bars_before_current) < 10:
        return None

    recent_5 = bars_before_current[-5:]
    recent_10 = bars_before_current[-10:]

    pre_5_volume_ratios = [
        ratio(getattr(bar, "volume", None), getattr(bar, "volume_average", None))
        for bar in recent_5
    ]
    pre_5_volume_ratios = [x for x in pre_5_volume_ratios if x is not None]

    if not pre_5_volume_ratios:
        return None

    pre_5_avg_volume_ratio = sum(pre_5_volume_ratios) / len(pre_5_volume_ratios)

    if pre_5_avg_volume_ratio > 0.90:
        return None

    context = build_micro_context(
        current_bar=current_bar,
        bars_before_current=bars_before_current,
        breakout_type="volume_dryup_expansion",
        reason="volume_dryup_then_expansion_over_micro_resistance",
        resistance_window_minutes=10,
    )

    if context is None:
        return None

    if context.breakout_close_above_resistance_pct < 0.01:
        return None

    if context.volume_vs_previous_bar_ratio < 2.5:
        return None

    if context.volume_vs_average_ratio < 1.8:
        return None

    current_close = safe_float(getattr(current_bar, "close", None), None)
    current_ema9 = safe_float(getattr(current_bar, "ema_9", None), None)
    current_vwap = safe_float(getattr(current_bar, "vwap", None), None)

    if current_close is None or current_ema9 is None or current_vwap is None:
        return None

    if current_close <= current_ema9 or current_close <= current_vwap:
        return None

    if not is_candle_quality_good(current_bar, min_close_position=0.75, max_upper_wick=0.25):
        return None

    return context


def count_higher_lows(window: list[Any], tolerance_pct: float = 0.005) -> int:
    if len(window) < 2:
        return 0

    count = 0
    for previous_bar, current_bar in zip(window, window[1:]):
        previous_low = safe_float(getattr(previous_bar, "low", None), None)
        current_low = safe_float(getattr(current_bar, "low", None), None)
        if previous_low is None or previous_low <= 0 or current_low is None:
            continue
        if current_low >= previous_low * (1 - tolerance_pct):
            count += 1
    return count


def find_higher_low_compression_breakout_context(
    current_bar: Any,
    bars: list[Any],
) -> Optional[BreakoutContext]:
    """
    Pattern: higher/flat lows + range compression + volume expansion through recent high.
    """
    bars_before_current = get_bars_same_day_until(bars, current_bar, include_current=False)

    if len(bars_before_current) < 20:
        return None

    recent_5 = bars_before_current[-5:]
    recent_20 = bars_before_current[-20:]

    if count_higher_lows(recent_5, tolerance_pct=0.006) < 3:
        return None

    first_close_5 = safe_float(getattr(recent_5[0], "close", None), None)
    first_close_20 = safe_float(getattr(recent_20[0], "close", None), None)

    if first_close_5 is None or first_close_5 <= 0 or first_close_20 is None or first_close_20 <= 0:
        return None

    range_5 = (max(safe_float(getattr(b, "high", None), 0.0) for b in recent_5) - min(safe_float(getattr(b, "low", None), float("inf")) for b in recent_5)) / first_close_5
    range_20 = (max(safe_float(getattr(b, "high", None), 0.0) for b in recent_20) - min(safe_float(getattr(b, "low", None), float("inf")) for b in recent_20)) / first_close_20

    if range_20 <= 0:
        return None

    # We want a recent base/compression, not already expanding wildly.
    if range_5 > range_20 * 0.75:
        return None

    context = build_micro_context(
        current_bar=current_bar,
        bars_before_current=bars_before_current,
        breakout_type="higher_low_compression_breakout",
        reason="higher_lows_compression_then_volume_breakout",
        resistance_window_minutes=10,
    )

    if context is None:
        return None

    if context.breakout_close_above_resistance_pct < 0.01:
        return None

    if context.volume_vs_previous_bar_ratio < 1.8:
        return None

    if context.volume_vs_average_ratio < 1.5:
        return None

    current_close = safe_float(getattr(current_bar, "close", None), None)
    current_ema9 = safe_float(getattr(current_bar, "ema_9", None), None)

    if current_close is None or current_ema9 is None or current_close <= current_ema9:
        return None

    if not is_candle_quality_good(current_bar, min_close_position=0.75, max_upper_wick=0.25):
        return None

    return context


def find_first_pullback_hold_above_vwap_context(
    current_bar: Any,
    bars: list[Any],
) -> Optional[BreakoutContext]:
    """
    Pattern: prior push, first controlled pullback holds above VWAP, then breakout/reclaim with volume.
    """
    bars_before_current = get_bars_same_day_until(bars, current_bar, include_current=False)

    if len(bars_before_current) < 20:
        return None

    recent_45 = [
        bar
        for bar in bars_before_current
        if bar.bar_time >= current_bar.bar_time - datetime.timedelta(minutes=45)
    ]

    if len(recent_45) < 10:
        return None

    prior_high_bar = max(recent_45, key=lambda b: safe_float(getattr(b, "high", None), 0.0))
    prior_high = safe_float(getattr(prior_high_bar, "high", None), None)

    if prior_high is None or prior_high <= 0:
        return None

    bars_after_prior_high = [bar for bar in bars_before_current if bar.bar_time > prior_high_bar.bar_time]

    if len(bars_after_prior_high) < 3:
        return None

    pullback_low_bar = min(bars_after_prior_high, key=lambda b: safe_float(getattr(b, "low", None), float("inf")))
    pullback_low = safe_float(getattr(pullback_low_bar, "low", None), None)
    pullback_vwap = safe_float(getattr(pullback_low_bar, "vwap", None), None)

    if pullback_low is None or pullback_low <= 0 or pullback_vwap is None or pullback_vwap <= 0:
        return None

    pullback_from_high = (prior_high - pullback_low) / prior_high

    if pullback_from_high < 0.03 or pullback_from_high > 0.22:
        return None

    # The pullback should hold at/above VWAP.
    if pullback_low < pullback_vwap * 0.995:
        return None

    # Avoid late recycled patterns: recent previous lows after pullback should not break it.
    if any(safe_float(getattr(bar, "low", None), float("inf")) < pullback_low * 0.997 for bar in bars_after_prior_high if bar.bar_time > pullback_low_bar.bar_time):
        return None

    context = build_micro_context(
        current_bar=current_bar,
        bars_before_current=bars_before_current,
        breakout_type="first_pullback_hold_above_vwap",
        reason="first_pullback_holds_vwap_then_breaks_micro_resistance",
        resistance_window_minutes=10,
    )

    if context is None:
        return None

    if context.breakout_close_above_resistance_pct < 0.01:
        return None

    if context.volume_vs_previous_bar_ratio < 1.5:
        return None

    if context.volume_vs_average_ratio < 1.5:
        return None

    current_close = safe_float(getattr(current_bar, "close", None), None)
    current_ema9 = safe_float(getattr(current_bar, "ema_9", None), None)
    current_vwap = safe_float(getattr(current_bar, "vwap", None), None)

    if current_close is None or current_ema9 is None or current_vwap is None:
        return None

    if current_close <= current_ema9 or current_close <= current_vwap:
        return None

    if not is_candle_quality_good(current_bar, min_close_position=0.75, max_upper_wick=0.25):
        return None

    # Override support low to the actual VWAP pullback low.
    context.lowest_low_since_resistance_bar = pullback_low_bar
    context.pullback_from_resistance_pct = pullback_from_high

    return context


def find_breakout_context(
    current_bar: Any,
    bars: list[Any],
) -> Optional[BreakoutContext]:
    # Detector priority matters:
    # specific patterns first, broad fallback last.
    for detector in (
        find_market_open_premarket_runner_reclaim_context,
        find_intraday_extreme_volume_ignition_context,
        find_deep_pullback_support_reclaim_context,
        find_vwap_reclaim_trend_start_context,
        find_ema_reclaim_after_pullback_context,
        find_volume_dryup_expansion_context,
        find_higher_low_compression_breakout_context,
        find_first_pullback_hold_above_vwap_context,
        find_volume_resistance_breakout_context,
    ):
        context = detector(current_bar, bars)
        if context is not None:
            return context

    return None


# =========================
# FUTURE RESEARCH LABELS
# =========================

def calculate_future_labels(
    bars: list[Any],
    context: BreakoutContext,
    future_minutes: int = FUTURE_ANALYSIS_MINUTES,
    target_gain_pct: float = TEN_PERCENT_TARGET,
    invalidation_tolerance_pct: float = SUPPORT_LOW_INVALIDATION_TOLERANCE_PCT,
) -> dict[str, Any]:
    breakout_bar = context.breakout_bar
    future_bars = get_future_bars(bars, breakout_bar, future_minutes)

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
            "reached_10_percent_gain_within_30_minutes": False,
            "minutes_until_10_percent_gain": None,
            "went_below_lowest_low_before_10_percent_gain_30_minutes": False,
            "lowest_low_break_before_10_percent_gain_30_minutes_time": None,
            "lowest_low_break_before_10_percent_gain_30_minutes_price": None,
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

        "reached_10_percent_gain_within_30_minutes": reached_target,
        "minutes_until_10_percent_gain": minutes_until_target,

        "went_below_lowest_low_before_10_percent_gain_30_minutes": went_below_support_before_target,
        "lowest_low_break_before_10_percent_gain_30_minutes_time": support_break_time,
        "lowest_low_break_before_10_percent_gain_30_minutes_price": support_break_price,
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

        reached_10_percent_gain_within_30_minutes=future_labels["reached_10_percent_gain_within_30_minutes"],
        minutes_until_10_percent_gain=future_labels["minutes_until_10_percent_gain"],

        went_below_lowest_low_before_10_percent_gain_30_minutes=future_labels["went_below_lowest_low_before_10_percent_gain_30_minutes"],
        lowest_low_break_before_10_percent_gain_30_minutes_time=future_labels["lowest_low_break_before_10_percent_gain_30_minutes_time"],
        lowest_low_break_before_10_percent_gain_30_minutes_price=future_labels["lowest_low_break_before_10_percent_gain_30_minutes_price"],
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

    for current_bar in bars:
        # We profile regular session only, including the 09:30 opening bar.
        if current_bar.bar_time.time() < MARKET_OPEN:
            continue

        if current_bar.bar_time.time() > MARKET_CLOSE:
            continue

        update_tracked_breakouts(tracked_breakouts, current_bar)

        context = find_breakout_context(current_bar, bars)

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

def write_rows_to_csv(
    rows: list[BreakoutProfileRow],
    output_file_path: str,
) -> None:
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    fieldnames = list(BreakoutProfileRow.__dataclass_fields__.keys())

    with open(output_file_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(asdict(row))

    print(f"Wrote {len(rows)} rows to {output_file_path}")


def main() -> None:
    files = glob.glob(INPUT_FILES_GLOB)

    print(f"Found {len(files)} files")

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

    positive_rows = [row for row in all_rows if row.is_positive]
    false_positive_rows = [row for row in all_rows if not row.is_positive]

    write_rows_to_csv(positive_rows, OUTPUT_POSITIVE_FILE)
    write_rows_to_csv(false_positive_rows, OUTPUT_FALSE_POSITIVE_FILE)
    write_rows_to_csv(all_rows, OUTPUT_COMBINED_FILE)

    print("")
    print("Done.")
    print(f"Total rows: {len(all_rows)}")
    print(f"Positive rows: {len(positive_rows)}")
    print(f"False-positive rows: {len(false_positive_rows)}")


if __name__ == "__main__":
    main()
