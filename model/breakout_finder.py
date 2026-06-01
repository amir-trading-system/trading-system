#pylint: skip-file

import concurrent.futures
import datetime
import pickle
import glob
import csv
import math
import tqdm

from dataclasses import dataclass, asdict
from typing import Optional, Any

import common


POSITIVE_FILE_NAME = "model/training/positive_results.csv"
FALSE_POSITIVE_FILE_NAME = "model/training/false_positive_results.csv"
POTENTIAL_HARD_RULES_FILE_NAME = "model/training/hard_rules.json"


def load_pickle_data(
    file_path: str,
) -> Any:
    with open(file_path, "rb") as f:
        obj = pickle.load(f)

    return obj


def load_data_for_training_model() -> list[dict[str, Any]]:
    pickled_data: list[dict[str, Any]] = []
    files = glob.glob("model/training/data/*.json")
    futures = []

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=10,
    ) as executor:
        for file_path in files:
            f = executor.submit(
                load_pickle_data,
                file_path,
            )
            futures.append(f)

    for future in concurrent.futures.as_completed(futures):
        pickled_object = future.result()
        pickled_data.append(pickled_object)

    return pickled_data


@dataclass
class BreakoutResult:
    symbol: str
    trade_date: str
    bar_time: datetime.datetime
    is_positive: bool

    breakout_type: str
    reason: str

    open: float
    high: float
    low: float
    close: float
    volume: float
    volume_average: float
    volume_ratio: float

    candle_body_pct_of_range: float
    upper_wick_pct_of_range: float
    lower_wick_pct_of_range: float
    close_position_in_range: float

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
    volume_vs_previous_bar_ratio: Optional[float]
    volume_vs_average_ratio: Optional[float]

    max_gain_after_breakout_pct: float
    max_gain_after_breakout_abs: float
    max_gain_after_breakout_high: Optional[float]
    max_gain_after_breakout_high_time: Optional[datetime.datetime]

    max_gain_after_breakout_next_30_minutes_pct: float
    max_gain_after_breakout_next_30_minutes_abs: float
    max_gain_after_breakout_next_30_minutes_high: Optional[float]
    max_gain_after_breakout_next_30_minutes_high_time: Optional[datetime.datetime]
    reached_10_percent_gain_within_30_minutes: bool
    minutes_until_10_percent_gain: Optional[float]

    went_below_lowest_low_before_10_percent_gain_30_minutes: bool
    lowest_low_break_before_10_percent_gain_30_minutes_time: Optional[datetime.datetime]
    lowest_low_break_before_10_percent_gain_30_minutes_price: Optional[float]

    vwap: Optional[float]
    ema_9: Optional[float]
    ema_20: Optional[float]
    macd: Optional[float]
    histogram: Optional[float]
    signal_line: Optional[float]


@dataclass
class FindBreakoutsResult:
    breakouts: list[BreakoutResult]
    is_positive: bool


def safe_float(value: Any, default: float) -> float:
    try:
        if value is None:
            return default

        float_value = float(value)

        if math.isnan(float_value):
            return default

        return float_value

    except Exception:
        return default


def pct_change(
    from_value: float,
    to_value: float,
) -> float:
    if from_value == 0:
        return 0.0

    return (to_value - from_value) / from_value


def get_bar_range(
    bar_object: common.objects.BarData,
) -> float:
    high = safe_float(bar_object.high, 0.0)
    low = safe_float(bar_object.low, 0.0)

    return max(0.000001, high - low)


def get_candle_stats(
    bar_object: common.objects.BarData,
) -> dict[str, float]:
    open_value = safe_float(bar_object.open_value, 0.0)
    high = safe_float(bar_object.high, 0.0)
    low = safe_float(bar_object.low, 0.0)
    close = safe_float(bar_object.close, 0.0)

    bar_range = max(0.000001, high - low)
    body = abs(close - open_value)
    upper_wick = high - max(open_value, close)
    lower_wick = min(open_value, close) - low

    return {
        "body_pct_of_range": body / bar_range,
        "upper_wick_pct_of_range": max(0.0, upper_wick / bar_range),
        "lower_wick_pct_of_range": max(0.0, lower_wick / bar_range),
        "close_position_in_range": (close - low) / bar_range,
    }


def get_volume_ratio(
    bar_object: common.objects.BarData,
) -> float:
    volume = safe_float(bar_object.volume, 0.0)
    volume_average = safe_float(bar_object.volume_average, 0.0)

    if volume_average <= 0:
        return 0.0

    return volume / volume_average


def calculate_max_gain_after_breakout(
    bar_index: int,
    bars: list[common.objects.BarData],
) -> dict[str, Optional[float] | Optional[datetime.datetime]]:
    breakout_bar = bars[bar_index]
    breakout_close = safe_float(breakout_bar.close, 0.0)
    future_bars = bars[bar_index + 1:]

    if breakout_close <= 0 or not future_bars:
        return {
            "max_gain_after_breakout_pct": 0.0,
            "max_gain_after_breakout_abs": 0.0,
            "max_gain_after_breakout_high": None,
            "max_gain_after_breakout_high_time": None,
        }

    highest_future_bar = max(
        future_bars,
        key=lambda bar_object: safe_float(bar_object.high, 0.0),
    )

    highest_future_high = safe_float(highest_future_bar.high, 0.0)
    gain_abs = max(0.0, highest_future_high - breakout_close)
    gain_pct = (gain_abs / breakout_close) * 100.0

    return {
        "max_gain_after_breakout_pct": gain_pct,
        "max_gain_after_breakout_abs": gain_abs,
        "max_gain_after_breakout_high": highest_future_high,
        "max_gain_after_breakout_high_time": highest_future_bar.bar_time,
    }




def calculate_max_gain_after_breakout_next_30_minutes(
    bar_index: int,
    bars: list[common.objects.BarData],
) -> dict[str, Optional[float] | Optional[datetime.datetime] | bool]:
    breakout_bar = bars[bar_index]
    breakout_close = safe_float(breakout_bar.close, 0.0)

    if breakout_close <= 0:
        return {
            "max_gain_after_breakout_next_30_minutes_pct": 0.0,
            "max_gain_after_breakout_next_30_minutes_abs": 0.0,
            "max_gain_after_breakout_next_30_minutes_high": None,
            "max_gain_after_breakout_next_30_minutes_high_time": None,
            "reached_10_percent_gain_within_30_minutes": False,
            "minutes_until_10_percent_gain": None,
        }

    end_time = breakout_bar.bar_time + datetime.timedelta(minutes=30)

    future_bars_next_30_minutes = [
        bar_object
        for bar_object in bars[bar_index + 1:]
        if breakout_bar.bar_time < bar_object.bar_time <= end_time
    ]

    if not future_bars_next_30_minutes:
        return {
            "max_gain_after_breakout_next_30_minutes_pct": 0.0,
            "max_gain_after_breakout_next_30_minutes_abs": 0.0,
            "max_gain_after_breakout_next_30_minutes_high": None,
            "max_gain_after_breakout_next_30_minutes_high_time": None,
            "reached_10_percent_gain_within_30_minutes": False,
            "minutes_until_10_percent_gain": None,
        }

    highest_future_bar = max(
        future_bars_next_30_minutes,
        key=lambda bar_object: safe_float(bar_object.high, 0.0),
    )

    highest_future_high = safe_float(highest_future_bar.high, 0.0)
    gain_abs = max(0.0, highest_future_high - breakout_close)
    gain_pct = (gain_abs / breakout_close) * 100.0

    ten_percent_target_price = breakout_close * 1.10
    first_10_percent_gain_bar = None

    for future_bar in future_bars_next_30_minutes:
        if safe_float(future_bar.high, 0.0) >= ten_percent_target_price:
            first_10_percent_gain_bar = future_bar
            break

    minutes_until_10_percent_gain = None
    if first_10_percent_gain_bar is not None:
        minutes_until_10_percent_gain = (
            first_10_percent_gain_bar.bar_time - breakout_bar.bar_time
        ).total_seconds() / 60.0

    return {
        "max_gain_after_breakout_next_30_minutes_pct": gain_pct,
        "max_gain_after_breakout_next_30_minutes_abs": gain_abs,
        "max_gain_after_breakout_next_30_minutes_high": highest_future_high,
        "max_gain_after_breakout_next_30_minutes_high_time": highest_future_bar.bar_time,
        "reached_10_percent_gain_within_30_minutes": first_10_percent_gain_bar is not None,
        "minutes_until_10_percent_gain": minutes_until_10_percent_gain,
    }



def calculate_lowest_low_break_before_10_percent_gain_next_30_minutes(
    bar_index: int,
    bars: list[common.objects.BarData],
    lowest_low_since_previous_high: Optional[float],
) -> dict[str, Optional[float] | Optional[datetime.datetime] | bool]:
    """
    Checks whether price goes below the setup's lowest low after the breakout,
    before reaching a 10% gain target, within the next 30 minutes.

    This is useful for identifying breakouts where the stock first invalidates
    the pullback/support low before making the desired move.
    """

    breakout_bar = bars[bar_index]
    breakout_close = safe_float(breakout_bar.close, 0.0)

    if breakout_close <= 0 or lowest_low_since_previous_high is None or lowest_low_since_previous_high <= 0:
        return {
            "went_below_lowest_low_before_10_percent_gain_30_minutes": False,
            "lowest_low_break_before_10_percent_gain_30_minutes_time": None,
            "lowest_low_break_before_10_percent_gain_30_minutes_price": None,
        }

    ten_percent_target_price = breakout_close * 1.10
    end_time = breakout_bar.bar_time + datetime.timedelta(minutes=30)

    future_bars_next_30_minutes = [
        bar_object
        for bar_object in bars[bar_index + 1:]
        if breakout_bar.bar_time < bar_object.bar_time <= end_time
    ]

    for future_bar in future_bars_next_30_minutes:
        future_low = safe_float(future_bar.low, 0.0)
        future_high = safe_float(future_bar.high, 0.0)

        if future_low < lowest_low_since_previous_high:
            return {
                "went_below_lowest_low_before_10_percent_gain_30_minutes": True,
                "lowest_low_break_before_10_percent_gain_30_minutes_time": future_bar.bar_time,
                "lowest_low_break_before_10_percent_gain_30_minutes_price": future_low,
            }

        if future_high >= ten_percent_target_price:
            return {
                "went_below_lowest_low_before_10_percent_gain_30_minutes": False,
                "lowest_low_break_before_10_percent_gain_30_minutes_time": None,
                "lowest_low_break_before_10_percent_gain_30_minutes_price": None,
            }

    return {
        "went_below_lowest_low_before_10_percent_gain_30_minutes": False,
        "lowest_low_break_before_10_percent_gain_30_minutes_time": None,
        "lowest_low_break_before_10_percent_gain_30_minutes_price": None,
    }

def find_volume_resistance_breakout_context(
    potential_confirmation_bar: common.objects.BarData,
    one_minute_timeframe_stock: common.objects.Stock,
) -> Optional[dict[str, Any]]:
    """
    Finds the actual resistance context used by the current volume-resistance breakout logic.

    This uses only bars known before/at the potential confirmation bar.
    """

    lookback_minutes = 30
    min_pullback_from_resistance_pct = 0.03
    min_close_above_resistance_pct = 0.02
    min_volume_expansion_vs_previous_bar = 1.8
    min_volume_expansion_vs_average = 1.8
    min_close_position_in_range = 0.70

    bars_before_current = sorted(
        [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if (
                potential_confirmation_bar.bar_time - datetime.timedelta(minutes=lookback_minutes)
                <= bar_object.bar_time
                < potential_confirmation_bar.bar_time
            )
        ],
        key=lambda bar_object: bar_object.bar_time,
    )

    if len(bars_before_current) < 3:
        return None

    previous_bar = bars_before_current[-1]

    current_open = safe_float(potential_confirmation_bar.open_value, 0.0)
    current_high = safe_float(potential_confirmation_bar.high, 0.0)
    current_low = safe_float(potential_confirmation_bar.low, 0.0)
    current_close = safe_float(potential_confirmation_bar.close, 0.0)
    current_volume = safe_float(potential_confirmation_bar.volume, 0.0)
    current_volume_average = safe_float(potential_confirmation_bar.volume_average, 0.0)
    previous_volume = safe_float(previous_bar.volume, 0.0)

    if current_close <= 0 or current_volume <= 0:
        return None

    if previous_volume <= 0:
        return None

    if current_volume_average <= 0:
        return None

    if current_close <= current_open:
        return None

    current_range = current_high - current_low
    if current_range <= 0:
        return None

    close_position_in_range = (current_close - current_low) / current_range
    if close_position_in_range < min_close_position_in_range:
        return None

    volume_vs_previous_bar_ratio = current_volume / previous_volume
    if volume_vs_previous_bar_ratio < min_volume_expansion_vs_previous_bar:
        return None

    volume_vs_average_ratio = current_volume / current_volume_average
    if volume_vs_average_ratio < min_volume_expansion_vs_average:
        return None

    candidate_contexts: list[dict[str, Any]] = []

    for i in range(1, len(bars_before_current) - 1):
        previous_local_bar = bars_before_current[i - 1]
        resistance_bar = bars_before_current[i]
        next_local_bar = bars_before_current[i + 1]

        resistance_price = safe_float(resistance_bar.high, 0.0)
        if resistance_price <= 0:
            continue

        is_local_high = (
            resistance_price >= safe_float(previous_local_bar.high, 0.0)
            and resistance_price >= safe_float(next_local_bar.high, 0.0)
        )

        if not is_local_high:
            continue

        breakout_close_above_resistance_pct = pct_change(
            resistance_price,
            current_close,
        )

        if breakout_close_above_resistance_pct < min_close_above_resistance_pct:
            continue

        bars_after_resistance_before_current = [
            bar_object
            for bar_object in bars_before_current
            if resistance_bar.bar_time < bar_object.bar_time < potential_confirmation_bar.bar_time
        ]

        if not bars_after_resistance_before_current:
            continue

        lowest_low_since_resistance_bar = min(
            bars_after_resistance_before_current,
            key=lambda bar_object: safe_float(bar_object.low, resistance_price),
        )

        lowest_low_since_resistance = safe_float(
            lowest_low_since_resistance_bar.low,
            resistance_price,
        )

        pullback_from_resistance_pct = pct_change(
            resistance_price,
            lowest_low_since_resistance,
        ) * -1

        if pullback_from_resistance_pct < min_pullback_from_resistance_pct:
            continue

        prior_close_above_resistance = any(
            safe_float(bar_object.close, 0.0) > resistance_price
            for bar_object in bars_after_resistance_before_current
        )

        if prior_close_above_resistance:
            continue

        candidate_contexts.append(
            {
                "resistance_bar": resistance_bar,
                "resistance_price": resistance_price,
                "lowest_low_since_resistance_bar": lowest_low_since_resistance_bar,
                "lowest_low_since_resistance": lowest_low_since_resistance,
                "pullback_from_resistance_pct": pullback_from_resistance_pct,
                "breakout_close_above_resistance_pct": breakout_close_above_resistance_pct,
                "minutes_since_resistance": (
                    potential_confirmation_bar.bar_time - resistance_bar.bar_time
                ).total_seconds() / 60.0,
                "volume_vs_previous_bar_ratio": volume_vs_previous_bar_ratio,
                "volume_vs_average_ratio": volume_vs_average_ratio,
            }
        )

    if not candidate_contexts:
        return None

    # Prefer the highest valid resistance that the current bar is breaking.
    return max(
        candidate_contexts,
        key=lambda context: context["resistance_price"],
    )




def find_market_open_premarket_runner_reclaim_context(
    potential_confirmation_bar: common.objects.BarData,
    one_minute_timeframe_stock: common.objects.Stock,
) -> Optional[dict[str, Any]]:
    """
    Finds the MASK-09:30 style pattern:
    premarket runner -> controlled pullback/reset above VWAP -> 09:30/early-open
    volume shock -> reclaim/break of recent micro resistance with a strong close.

    This is live-safe: it only uses bars before the potential confirmation bar
    plus the potential confirmation bar itself.
    """

    current_time = potential_confirmation_bar.bar_time.time()
    if not (datetime.time(9, 30) <= current_time <= datetime.time(9, 35)):
        return None

    current_date = potential_confirmation_bar.bar_time.date()

    bars_before_current = sorted(
        [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if (
                bar_object.bar_time.date() == current_date
                and bar_object.bar_time < potential_confirmation_bar.bar_time
            )
        ],
        key=lambda bar_object: bar_object.bar_time,
    )

    if len(bars_before_current) < 15:
        return None

    previous_bar = bars_before_current[-1]

    current_open = safe_float(potential_confirmation_bar.open_value, 0.0)
    current_high = safe_float(potential_confirmation_bar.high, 0.0)
    current_low = safe_float(potential_confirmation_bar.low, 0.0)
    current_close = safe_float(potential_confirmation_bar.close, 0.0)
    current_volume = safe_float(potential_confirmation_bar.volume, 0.0)
    current_volume_average = safe_float(potential_confirmation_bar.volume_average, 0.0)
    previous_volume = safe_float(previous_bar.volume, 0.0)

    if current_close <= 0 or current_volume <= 0 or current_volume_average <= 0 or previous_volume <= 0:
        return None

    premarket_bars = [
        bar_object
        for bar_object in bars_before_current
        if datetime.time(4, 0) <= bar_object.bar_time.time() < datetime.time(9, 30)
    ]

    if len(premarket_bars) < 10:
        return None

    # 1. The stock should already be a premarket runner with earlier ignition volume.
    earlier_ignition_bars = []
    for bar_object in premarket_bars:
        volume_average = safe_float(bar_object.volume_average, 0.0)
        if volume_average <= 0:
            continue

        bar_range = get_bar_range(bar_object)
        close_position_in_range = (safe_float(bar_object.close, 0.0) - safe_float(bar_object.low, 0.0)) / bar_range

        if (
            safe_float(bar_object.volume, 0.0) / volume_average >= 4.0
            and safe_float(bar_object.close, 0.0) > safe_float(bar_object.vwap, 0.0)
            and safe_float(bar_object.close, 0.0) > safe_float(bar_object.ema_9, 0.0)
            and safe_float(bar_object.close, 0.0) > safe_float(bar_object.open_value, 0.0)
            and close_position_in_range >= 0.50
        ):
            earlier_ignition_bars.append(bar_object)

    if not earlier_ignition_bars:
        return None

    premarket_high_bar = max(
        premarket_bars,
        key=lambda bar_object: safe_float(bar_object.high, 0.0),
    )

    premarket_high = safe_float(premarket_high_bar.high, 0.0)
    if premarket_high <= current_low * 1.08:
        return None

    # 2. Recent pullback/reset before the open.
    recent_pullback_bars = [
        bar_object
        for bar_object in bars_before_current
        if (
            potential_confirmation_bar.bar_time - datetime.timedelta(minutes=15)
            <= bar_object.bar_time
            < potential_confirmation_bar.bar_time
        )
    ]

    if len(recent_pullback_bars) < 5:
        return None

    had_recent_close_below_ema9 = any(
        safe_float(bar_object.close, 0.0) < safe_float(bar_object.ema_9, 0.0)
        for bar_object in recent_pullback_bars
    )

    if not had_recent_close_below_ema9:
        return None

    closes_above_vwap_count = sum(
        1
        for bar_object in recent_pullback_bars
        if safe_float(bar_object.close, 0.0) > safe_float(bar_object.vwap, 0.0)
    )

    if closes_above_vwap_count < len(recent_pullback_bars) * 0.70:
        return None

    recent_volume_ratios = [
        safe_float(bar_object.volume, 0.0) / safe_float(bar_object.volume_average, 0.0)
        for bar_object in recent_pullback_bars
        if safe_float(bar_object.volume_average, 0.0) > 0
    ]

    if not recent_volume_ratios:
        return None

    average_recent_volume_ratio = sum(recent_volume_ratios) / len(recent_volume_ratios)
    if average_recent_volume_ratio > 1.00:
        return None

    # 3. The open bar should retest the pullback shelf, not deeply break it.
    pullback_support_bar = min(
        recent_pullback_bars,
        key=lambda bar_object: safe_float(bar_object.low, 0.0),
    )
    pullback_support_low = safe_float(pullback_support_bar.low, 0.0)

    if pullback_support_low <= 0:
        return None

    retested_support = current_low <= pullback_support_low * 1.02
    deeply_broke_support = current_low < pullback_support_low * 0.97

    if not retested_support or deeply_broke_support:
        return None

    # 4. Break recent micro-resistance from the compressed pullback.
    recent_micro_resistance_bars = recent_pullback_bars[-7:]
    micro_resistance_bar = max(
        recent_micro_resistance_bars,
        key=lambda bar_object: safe_float(bar_object.high, 0.0),
    )
    micro_resistance_price = safe_float(micro_resistance_bar.high, 0.0)

    if micro_resistance_price <= 0:
        return None

    breakout_close_above_resistance_pct = pct_change(
        micro_resistance_price,
        current_close,
    )

    if breakout_close_above_resistance_pct < 0.02:
        return None

    # 5. Market-open volume shock.
    volume_vs_previous_bar_ratio = current_volume / previous_volume
    if volume_vs_previous_bar_ratio < 5.0:
        return None

    volume_vs_average_ratio = current_volume / current_volume_average
    if volume_vs_average_ratio < 1.5:
        return None

    # 6. Candle quality and reclaim alignment.
    if current_close <= current_open:
        return None

    current_range = current_high - current_low
    if current_range <= 0:
        return None

    close_position_in_range = (current_close - current_low) / current_range
    if close_position_in_range < 0.80:
        return None

    upper_wick_pct_of_range = (
        current_high - max(current_open, current_close)
    ) / current_range
    if upper_wick_pct_of_range > 0.25:
        return None

    if current_close <= safe_float(potential_confirmation_bar.ema_9, 0.0):
        return None

    if current_close <= safe_float(potential_confirmation_bar.ema_20, 0.0):
        return None

    if current_close <= safe_float(potential_confirmation_bar.vwap, 0.0):
        return None

    if safe_float(potential_confirmation_bar.ema_9, 0.0) <= safe_float(potential_confirmation_bar.ema_20, 0.0):
        return None

    return {
        "breakout_type": "market_open_premarket_runner_reclaim",
        "reason": "premarket_runner_pullback_reset_open_volume_reclaim",
        "resistance_bar": micro_resistance_bar,
        "resistance_price": micro_resistance_price,
        "lowest_low_since_resistance_bar": pullback_support_bar,
        "lowest_low_since_resistance": pullback_support_low,
        "pullback_from_resistance_pct": max(0.0, pct_change(micro_resistance_price, pullback_support_low) * -1),
        "breakout_close_above_resistance_pct": breakout_close_above_resistance_pct,
        "minutes_since_resistance": (
            potential_confirmation_bar.bar_time - micro_resistance_bar.bar_time
        ).total_seconds() / 60.0,
        "volume_vs_previous_bar_ratio": volume_vs_previous_bar_ratio,
        "volume_vs_average_ratio": volume_vs_average_ratio,
    }


def find_intraday_extreme_volume_ignition_context(
    potential_confirmation_bar: common.objects.BarData,
    one_minute_timeframe_stock: common.objects.Stock,
) -> Optional[dict[str, Any]]:
    """
    Finds the AIIO-13:00 style pattern:
    a very fresh intraday resistance gets crossed by an explosive volume shock candle.

    This detector intentionally does NOT require a large pullback from resistance;
    the defining edge is the extreme volume shock + large decisive close above a
    fresh level. That is what separated the AIIO 13:00 bar.
    """

    current_time = potential_confirmation_bar.bar_time.time()
    if not (datetime.time(9, 30) <= current_time < datetime.time(16, 0)):
        return None

    current_date = potential_confirmation_bar.bar_time.date()

    bars_before_current = sorted(
        [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if (
                bar_object.bar_time.date() == current_date
                and potential_confirmation_bar.bar_time - datetime.timedelta(minutes=12)
                <= bar_object.bar_time
                < potential_confirmation_bar.bar_time
            )
        ],
        key=lambda bar_object: bar_object.bar_time,
    )

    if len(bars_before_current) < 2:
        return None

    previous_bar = bars_before_current[-1]

    current_open = safe_float(potential_confirmation_bar.open_value, 0.0)
    current_high = safe_float(potential_confirmation_bar.high, 0.0)
    current_low = safe_float(potential_confirmation_bar.low, 0.0)
    current_close = safe_float(potential_confirmation_bar.close, 0.0)
    current_volume = safe_float(potential_confirmation_bar.volume, 0.0)
    current_volume_average = safe_float(potential_confirmation_bar.volume_average, 0.0)
    previous_volume = safe_float(previous_bar.volume, 0.0)

    if current_close <= 0 or current_volume <= 0 or current_volume_average <= 0 or previous_volume <= 0:
        return None

    if current_close <= current_open:
        return None

    current_range = current_high - current_low
    if current_range <= 0:
        return None

    close_position_in_range = (current_close - current_low) / current_range
    if close_position_in_range < 0.80:
        return None

    upper_wick_pct_of_range = (
        current_high - max(current_open, current_close)
    ) / current_range
    if upper_wick_pct_of_range > 0.25:
        return None

    volume_vs_previous_bar_ratio = current_volume / previous_volume
    if volume_vs_previous_bar_ratio < 10.0:
        return None

    volume_vs_average_ratio = current_volume / current_volume_average
    if volume_vs_average_ratio < 5.0:
        return None

    candidate_contexts: list[dict[str, Any]] = []

    for i, resistance_bar in enumerate(bars_before_current):
        resistance_price = safe_float(resistance_bar.high, 0.0)
        if resistance_price <= 0:
            continue

        minutes_since_resistance = (
            potential_confirmation_bar.bar_time - resistance_bar.bar_time
        ).total_seconds() / 60.0

        if minutes_since_resistance <= 0 or minutes_since_resistance > 10:
            continue

        breakout_close_above_resistance_pct = pct_change(
            resistance_price,
            current_close,
        )

        if breakout_close_above_resistance_pct < 0.08:
            continue

        bars_after_resistance_before_current = [
            bar_object
            for bar_object in bars_before_current
            if resistance_bar.bar_time < bar_object.bar_time < potential_confirmation_bar.bar_time
        ]

        prior_close_above_resistance = any(
            safe_float(bar_object.close, 0.0) > resistance_price
            for bar_object in bars_after_resistance_before_current
        )

        if prior_close_above_resistance:
            continue

        lowest_low_since_resistance_bar = None
        lowest_low_since_resistance = None
        pullback_from_resistance_pct = 0.0

        if bars_after_resistance_before_current:
            lowest_low_since_resistance_bar = min(
                bars_after_resistance_before_current,
                key=lambda bar_object: safe_float(bar_object.low, resistance_price),
            )
            lowest_low_since_resistance = safe_float(
                lowest_low_since_resistance_bar.low,
                resistance_price,
            )
            pullback_from_resistance_pct = max(
                0.0,
                pct_change(resistance_price, lowest_low_since_resistance) * -1,
            )
        else:
            lowest_low_since_resistance_bar = previous_bar
            lowest_low_since_resistance = safe_float(previous_bar.low, resistance_price)
            pullback_from_resistance_pct = max(
                0.0,
                pct_change(resistance_price, lowest_low_since_resistance) * -1,
            )

        candidate_contexts.append(
            {
                "breakout_type": "intraday_extreme_volume_ignition",
                "reason": "fresh_resistance_cross_with_extreme_volume_shock",
                "resistance_bar": resistance_bar,
                "resistance_price": resistance_price,
                "lowest_low_since_resistance_bar": lowest_low_since_resistance_bar,
                "lowest_low_since_resistance": lowest_low_since_resistance,
                "pullback_from_resistance_pct": pullback_from_resistance_pct,
                "breakout_close_above_resistance_pct": breakout_close_above_resistance_pct,
                "minutes_since_resistance": minutes_since_resistance,
                "volume_vs_previous_bar_ratio": volume_vs_previous_bar_ratio,
                "volume_vs_average_ratio": volume_vs_average_ratio,
            }
        )

    if not candidate_contexts:
        return None

    # Prefer the freshest high-quality level, then the highest resistance.
    return max(
        candidate_contexts,
        key=lambda context: (
            -context["minutes_since_resistance"],
            context["resistance_price"],
        ),
    )



def find_deep_pullback_support_reclaim_context(
    potential_confirmation_bar: common.objects.BarData,
    one_minute_timeframe_stock: common.objects.Stock,
) -> Optional[dict[str, Any]]:
    """
    Finds the HKIT-11:01 style pattern:
    major intraday runner -> deep pullback into earlier support/shelf -> support holds ->
    first strong reclaim candle back above recent micro resistance / EMA 9 / EMA 20.

    This is NOT an extreme volume ignition pattern. It is an early reclaim after a washout,
    so EMA 9 is allowed to still be below EMA 20. The confirmation comes from:
    - large prior run
    - deep but not fatal pullback
    - pullback low holds for a few bars
    - current bar reclaims local resistance and moving averages
    - volume expands enough, but does not need to be extreme
    - candle closes very strong with small/no upper wick
    """

    current_time = potential_confirmation_bar.bar_time.time()
    if not (datetime.time(9, 30) <= current_time < datetime.time(16, 0)):
        return None

    current_date = potential_confirmation_bar.bar_time.date()

    bars_before_current = sorted(
        [
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if (
                bar_object.bar_time.date() == current_date
                and bar_object.bar_time < potential_confirmation_bar.bar_time
            )
        ],
        key=lambda bar_object: bar_object.bar_time,
    )

    if len(bars_before_current) < 20:
        return None

    current_open = safe_float(potential_confirmation_bar.open_value, 0.0)
    current_high = safe_float(potential_confirmation_bar.high, 0.0)
    current_low = safe_float(potential_confirmation_bar.low, 0.0)
    current_close = safe_float(potential_confirmation_bar.close, 0.0)
    current_volume = safe_float(potential_confirmation_bar.volume, 0.0)
    current_volume_average = safe_float(potential_confirmation_bar.volume_average, 0.0)

    if current_close <= 0 or current_volume <= 0 or current_volume_average <= 0:
        return None

    # Use the last 90 minutes to find the prior major runner high.
    recent_90_min_bars = [
        bar_object
        for bar_object in bars_before_current
        if bar_object.bar_time >= potential_confirmation_bar.bar_time - datetime.timedelta(minutes=90)
    ]

    if len(recent_90_min_bars) < 10:
        return None

    prior_high_bar = max(
        recent_90_min_bars,
        key=lambda bar_object: safe_float(bar_object.high, 0.0),
    )
    prior_high = safe_float(prior_high_bar.high, 0.0)

    if prior_high <= 0:
        return None

    bars_after_prior_high_before_current = [
        bar_object
        for bar_object in bars_before_current
        if prior_high_bar.bar_time < bar_object.bar_time < potential_confirmation_bar.bar_time
    ]

    if len(bars_after_prior_high_before_current) < 3:
        return None

    pullback_low_bar = min(
        bars_after_prior_high_before_current,
        key=lambda bar_object: safe_float(bar_object.low, prior_high),
    )
    pullback_low = safe_float(pullback_low_bar.low, 0.0)

    if pullback_low <= 0:
        return None

    # The setup needs a real washout from a meaningful prior high.
    prior_high_to_pullback_low_pct = (prior_high - pullback_low) / prior_high

    if prior_high_to_pullback_low_pct < 0.20:
        return None

    # Avoid cases where the stock is completely destroyed rather than reclaiming.
    if prior_high_to_pullback_low_pct > 0.60:
        return None

    # The pullback low should be recent enough to be the active support/invalidation level.
    minutes_since_pullback_low = (
        potential_confirmation_bar.bar_time - pullback_low_bar.bar_time
    ).total_seconds() / 60.0

    if minutes_since_pullback_low <= 0 or minutes_since_pullback_low > 15:
        return None

    bars_after_pullback_low_before_current = [
        bar_object
        for bar_object in bars_before_current
        if pullback_low_bar.bar_time < bar_object.bar_time < potential_confirmation_bar.bar_time
    ]

    # After the washout low forms, support should not be materially broken before the reclaim.
    broke_pullback_low_after_it_formed = any(
        safe_float(bar_object.low, 0.0) < pullback_low * 0.997
        for bar_object in bars_after_pullback_low_before_current
    )

    if broke_pullback_low_after_it_formed:
        return None

    # The reclaim bar itself should also hold above the pullback low.
    if current_low < pullback_low * 0.997:
        return None

    # Current low should not be wildly far above the pullback low; otherwise it may be too late,
    # not the first reclaim from that support zone.
    current_low_above_pullback_low_pct = pct_change(pullback_low, current_low)
    if current_low_above_pullback_low_pct > 0.12:
        return None

    # Define recent micro resistance from the bounce/reclaim area.
    recent_reclaim_window_bars = [
        bar_object
        for bar_object in bars_before_current
        if bar_object.bar_time >= potential_confirmation_bar.bar_time - datetime.timedelta(minutes=10)
    ]

    if len(recent_reclaim_window_bars) < 3:
        return None

    micro_resistance_bar = max(
        recent_reclaim_window_bars,
        key=lambda bar_object: safe_float(bar_object.high, 0.0),
    )
    micro_resistance_price = safe_float(micro_resistance_bar.high, 0.0)

    if micro_resistance_price <= 0:
        return None

    breakout_close_above_resistance_pct = pct_change(
        micro_resistance_price,
        current_close,
    )

    # HKIT 11:01 was a reclaim, not a giant expansion; require meaningful but not huge clearance.
    if breakout_close_above_resistance_pct < 0.015:
        return None

    # The reclaim candle should clear EMA 9, EMA 20, and VWAP.
    current_ema_9 = safe_float(potential_confirmation_bar.ema_9, 0.0)
    current_ema_20 = safe_float(potential_confirmation_bar.ema_20, 0.0)
    current_vwap = safe_float(potential_confirmation_bar.vwap, 0.0)

    if current_ema_9 <= 0 or current_ema_20 <= 0 or current_vwap <= 0:
        return None

    if current_close <= current_ema_9:
        return None

    if current_close <= current_ema_20:
        return None

    if current_close <= current_vwap:
        return None

    # Do NOT require EMA 9 > EMA 20. In this pattern, buyers may enter before full trend alignment returns.

    previous_bar = bars_before_current[-1]
    previous_volume = safe_float(previous_bar.volume, 0.0)

    if previous_volume <= 0:
        return None

    volume_vs_previous_bar_ratio = current_volume / previous_volume
    if volume_vs_previous_bar_ratio < 1.5:
        return None

    volume_vs_average_ratio = current_volume / current_volume_average
    if volume_vs_average_ratio < 1.5:
        return None

    # Candle quality: green, closes near high, small upper wick.
    if current_close <= current_open:
        return None

    current_range = current_high - current_low
    if current_range <= 0:
        return None

    close_position_in_range = (current_close - current_low) / current_range
    if close_position_in_range < 0.80:
        return None

    upper_wick_pct_of_range = (
        current_high - max(current_open, current_close)
    ) / current_range

    if upper_wick_pct_of_range > 0.20:
        return None

    return {
        "breakout_type": "deep_pullback_support_reclaim_breakout",
        "reason": "major_runner_deep_pullback_support_hold_micro_resistance_reclaim",
        "resistance_bar": micro_resistance_bar,
        "resistance_price": micro_resistance_price,
        "lowest_low_since_resistance_bar": pullback_low_bar,
        "lowest_low_since_resistance": pullback_low,
        "pullback_from_resistance_pct": max(
            0.0,
            pct_change(micro_resistance_price, pullback_low) * -1,
        ),
        "breakout_close_above_resistance_pct": breakout_close_above_resistance_pct,
        "minutes_since_resistance": (
            potential_confirmation_bar.bar_time - micro_resistance_bar.bar_time
        ).total_seconds() / 60.0,
        "volume_vs_previous_bar_ratio": volume_vs_previous_bar_ratio,
        "volume_vs_average_ratio": volume_vs_average_ratio,
    }

def find_breakout_context(
    potential_confirmation_bar: common.objects.BarData,
    one_minute_timeframe_stock: common.objects.Stock,
) -> Optional[dict[str, Any]]:
    """
    Unified live-safe breakout detector.

    Pattern order matters:
    1. Market-open premarket runner reclaim catches MASK 09:30-like bars.
    2. Intraday extreme volume ignition catches AIIO 13:00-like bars.
    3. Deep pullback support reclaim catches HKIT 11:01-like bars.
    4. Standard volume-resistance breakout catches the broader pattern.
    """

    context = find_market_open_premarket_runner_reclaim_context(
        potential_confirmation_bar=potential_confirmation_bar,
        one_minute_timeframe_stock=one_minute_timeframe_stock,
    )
    if context is not None:
        return context

    context = find_intraday_extreme_volume_ignition_context(
        potential_confirmation_bar=potential_confirmation_bar,
        one_minute_timeframe_stock=one_minute_timeframe_stock,
    )
    if context is not None:
        return context

    context = find_deep_pullback_support_reclaim_context(
        potential_confirmation_bar=potential_confirmation_bar,
        one_minute_timeframe_stock=one_minute_timeframe_stock,
    )
    if context is not None:
        return context

    context = find_volume_resistance_breakout_context(
        potential_confirmation_bar=potential_confirmation_bar,
        one_minute_timeframe_stock=one_minute_timeframe_stock,
    )
    if context is not None:
        context["breakout_type"] = "volume_resistance_breakout"
        context["reason"] = "resistance_cross_with_volume_expansion"
        return context

    return None
def _is_valid_breakout(
    potential_confirmation_bar: common.objects.BarData,
    one_minute_timeframe_stock: common.objects.Stock,
) -> bool:
    return find_breakout_context(
        potential_confirmation_bar=potential_confirmation_bar,
        one_minute_timeframe_stock=one_minute_timeframe_stock,
    ) is not None

def build_breakout_result(
    data: dict[str, Any],
    bars: list[common.objects.BarData],
    bar_index: int,
    one_minute_timeframe_stock: common.objects.Stock,
) -> BreakoutResult:
    bar_object = bars[bar_index]

    specific_bar_time: datetime.datetime = data["day_timeframe_stock"].specific_bar_time
    is_positive: bool = data["day_timeframe_stock"].is_positive

    breakout_context = find_breakout_context(
        potential_confirmation_bar=bar_object,
        one_minute_timeframe_stock=one_minute_timeframe_stock,
    )

    resistance_bar = None
    lowest_low_since_resistance_bar = None
    resistance_price = None
    lowest_low_since_resistance = None
    pullback_from_resistance_pct = None
    breakout_close_above_resistance_pct = None
    minutes_since_resistance = None
    volume_vs_previous_bar_ratio = None
    volume_vs_average_ratio = None
    breakout_type = "unknown_breakout"
    reason = "unknown_reason"

    if breakout_context is not None:
        resistance_bar = breakout_context["resistance_bar"]
        lowest_low_since_resistance_bar = breakout_context["lowest_low_since_resistance_bar"]
        resistance_price = breakout_context["resistance_price"]
        lowest_low_since_resistance = breakout_context["lowest_low_since_resistance"]
        pullback_from_resistance_pct = breakout_context["pullback_from_resistance_pct"]
        breakout_close_above_resistance_pct = breakout_context["breakout_close_above_resistance_pct"]
        minutes_since_resistance = breakout_context["minutes_since_resistance"]
        volume_vs_previous_bar_ratio = breakout_context["volume_vs_previous_bar_ratio"]
        volume_vs_average_ratio = breakout_context["volume_vs_average_ratio"]
        breakout_type = breakout_context.get("breakout_type", "unknown_breakout")
        reason = breakout_context.get("reason", "unknown_reason")

    open_value = safe_float(bar_object.open_value, 0.0)
    high = safe_float(bar_object.high, 0.0)
    low = safe_float(bar_object.low, 0.0)
    close = safe_float(bar_object.close, 0.0)
    volume = safe_float(bar_object.volume, 0.0)
    volume_average = safe_float(bar_object.volume_average, 0.0)
    volume_ratio = get_volume_ratio(bar_object)
    bar_time = bar_object.bar_time

    candle_stats = get_candle_stats(bar_object)

    max_gain_after_breakout_stats = calculate_max_gain_after_breakout(
        bar_index=bar_index,
        bars=bars,
    )

    max_gain_after_breakout_next_30_minutes_stats = calculate_max_gain_after_breakout_next_30_minutes(
        bar_index=bar_index,
        bars=bars,
    )

    lowest_low_break_before_10_percent_gain_30_minutes_stats = calculate_lowest_low_break_before_10_percent_gain_next_30_minutes(
        bar_index=bar_index,
        bars=bars,
        lowest_low_since_previous_high=lowest_low_since_resistance,
    )

    return BreakoutResult(
        symbol=bar_object.symbol,
        trade_date=str(specific_bar_time.date()),
        bar_time=bar_time,
        is_positive=is_positive,

        breakout_type=breakout_type,
        reason=reason,

        open=open_value,
        high=high,
        low=low,
        close=close,
        volume=volume,
        volume_average=volume_average,
        volume_ratio=volume_ratio,

        candle_body_pct_of_range=candle_stats["body_pct_of_range"],
        upper_wick_pct_of_range=candle_stats["upper_wick_pct_of_range"],
        lower_wick_pct_of_range=candle_stats["lower_wick_pct_of_range"],
        close_position_in_range=candle_stats["close_position_in_range"],

        resistance_bar_time=(
            resistance_bar.bar_time
            if resistance_bar is not None
            else None
        ),
        resistance_price=resistance_price,
        resistance_bar_close=(
            safe_float(resistance_bar.close, 0.0)
            if resistance_bar is not None
            else None
        ),
        resistance_bar_volume=(
            safe_float(resistance_bar.volume, 0.0)
            if resistance_bar is not None
            else None
        ),
        resistance_bar_volume_average=(
            safe_float(resistance_bar.volume_average, 0.0)
            if resistance_bar is not None
            else None
        ),
        resistance_bar_wick_percentage=(
            safe_float(getattr(resistance_bar, "bar_wick_percentage", None), 0.0)
            if resistance_bar is not None
            else None
        ),

        lowest_low_since_resistance_time=(
            lowest_low_since_resistance_bar.bar_time
            if lowest_low_since_resistance_bar is not None
            else None
        ),
        lowest_low_since_resistance=lowest_low_since_resistance,
        lowest_low_since_resistance_close=(
            safe_float(lowest_low_since_resistance_bar.close, 0.0)
            if lowest_low_since_resistance_bar is not None
            else None
        ),
        lowest_low_since_resistance_bar_lower_wick_percentage=(
            safe_float(getattr(lowest_low_since_resistance_bar, "bar_lower_wick_percentage", None), 0.0)
            if lowest_low_since_resistance_bar is not None
            else None
        ),

        pullback_from_resistance_pct=pullback_from_resistance_pct,
        breakout_close_above_resistance_pct=breakout_close_above_resistance_pct,
        minutes_since_resistance=minutes_since_resistance,
        volume_vs_previous_bar_ratio=volume_vs_previous_bar_ratio,
        volume_vs_average_ratio=volume_vs_average_ratio,

        max_gain_after_breakout_pct=max_gain_after_breakout_stats["max_gain_after_breakout_pct"],
        max_gain_after_breakout_abs=max_gain_after_breakout_stats["max_gain_after_breakout_abs"],
        max_gain_after_breakout_high=max_gain_after_breakout_stats["max_gain_after_breakout_high"],
        max_gain_after_breakout_high_time=max_gain_after_breakout_stats["max_gain_after_breakout_high_time"],

        max_gain_after_breakout_next_30_minutes_pct=max_gain_after_breakout_next_30_minutes_stats["max_gain_after_breakout_next_30_minutes_pct"],
        max_gain_after_breakout_next_30_minutes_abs=max_gain_after_breakout_next_30_minutes_stats["max_gain_after_breakout_next_30_minutes_abs"],
        max_gain_after_breakout_next_30_minutes_high=max_gain_after_breakout_next_30_minutes_stats["max_gain_after_breakout_next_30_minutes_high"],
        max_gain_after_breakout_next_30_minutes_high_time=max_gain_after_breakout_next_30_minutes_stats["max_gain_after_breakout_next_30_minutes_high_time"],
        reached_10_percent_gain_within_30_minutes=max_gain_after_breakout_next_30_minutes_stats["reached_10_percent_gain_within_30_minutes"],
        minutes_until_10_percent_gain=max_gain_after_breakout_next_30_minutes_stats["minutes_until_10_percent_gain"],

        went_below_lowest_low_before_10_percent_gain_30_minutes=lowest_low_break_before_10_percent_gain_30_minutes_stats["went_below_lowest_low_before_10_percent_gain_30_minutes"],
        lowest_low_break_before_10_percent_gain_30_minutes_time=lowest_low_break_before_10_percent_gain_30_minutes_stats["lowest_low_break_before_10_percent_gain_30_minutes_time"],
        lowest_low_break_before_10_percent_gain_30_minutes_price=lowest_low_break_before_10_percent_gain_30_minutes_stats["lowest_low_break_before_10_percent_gain_30_minutes_price"],

        vwap=safe_float(getattr(bar_object, "vwap", 0), 0),
        ema_9=safe_float(getattr(bar_object, "ema_9", 0), 0),
        ema_20=safe_float(getattr(bar_object, "ema_20", 0), 0),
        macd=safe_float(getattr(bar_object, "macd", 0), 0),
        histogram=safe_float(getattr(bar_object, "histogram", 0), 0),
        signal_line=safe_float(getattr(bar_object, "signal_line", 0), 0),
    )

def find_breakouts_for_trade(
    data: dict[str, Any],
    one_minute_bars: list[common.objects.BarData],
    one_minute_timeframe_stock: common.objects.Stock,
) -> list[BreakoutResult]:
    """
    Finds only clean breakouts by the new logic.

    No resistance zones.
    No fake-breakout classification.
    Only rows where _is_valid_breakout(...) returns True are written.
    """

    results: list[BreakoutResult] = []

    bars = sorted(
        one_minute_bars,
        key=lambda bar: bar.bar_time,
    )

    if len(bars) < 15:
        return results

    for i in range(10, len(bars)):
        current_bar = bars[i]

        market_open_time = datetime.datetime(
            year=current_bar.bar_time.year,
            month=current_bar.bar_time.month,
            day=current_bar.bar_time.day,
            hour=9,
            minute=30,
        )

        market_close_time = datetime.datetime(
            year=current_bar.bar_time.year,
            month=current_bar.bar_time.month,
            day=current_bar.bar_time.day,
            hour=16,
        )

        if current_bar.bar_time < market_open_time or current_bar.bar_time >= market_close_time:
            continue

        if not _is_valid_breakout(
            potential_confirmation_bar=current_bar,
            one_minute_timeframe_stock=one_minute_timeframe_stock,
        ):
            continue

        results.append(
            build_breakout_result(
                data=data,
                bars=bars,
                bar_index=i,
                one_minute_timeframe_stock=one_minute_timeframe_stock,
            )
        )

    return results


def write_breakout_results_to_csv(
    results: list[BreakoutResult],
    output_file_path: str,
    desc: str,
) -> None:
    fieldnames = list(BreakoutResult.__dataclass_fields__.keys())

    with open(output_file_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for result in tqdm.tqdm(results, desc=desc):
            writer.writerow(asdict(result))

    print(f"Wrote {len(results)} breakout rows to: {output_file_path}")

def find_breakouts(data: dict[str, Any], index: int, total_length: int) -> FindBreakoutsResult:
    specific_bar_time: datetime.datetime = data["day_timeframe_stock"].specific_bar_time
    is_positive: bool = data["day_timeframe_stock"].is_positive

    one_minute_bars: list[common.objects.BarData] = [
        bar_object
        for bar_object in data["one_minute_timeframe_stock"].bars
        if bar_object.bar_time.date() == specific_bar_time.date()
    ]

    trade_breakouts = find_breakouts_for_trade(
        data=data,
        one_minute_bars=one_minute_bars,
        one_minute_timeframe_stock=data["one_minute_timeframe_stock"],
    )

    print(f"finished gathering breakouts for: {data['day_timeframe_stock'].symbol_name}. {index}/{total_length}. completed: {(index / total_length) * 100:.2f}%")

    return FindBreakoutsResult(
        breakouts=trade_breakouts,
        is_positive=is_positive,
    )


if __name__ == '__main__':
    training_model_data_list = load_data_for_training_model()

    positive_breakout_results: list[BreakoutResult] = []
    false_positive_breakout_results: list[BreakoutResult] = []

    futures = []

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=20,
    ) as executor:
        for i, data in enumerate(training_model_data_list):
            f = executor.submit(
                find_breakouts,
                data,
                i,
                len(training_model_data_list),
            )
            futures.append(f)

    for future in concurrent.futures.as_completed(futures):
        find_breakouts_result: FindBreakoutsResult = future.result()
        if find_breakouts_result.is_positive:
            positive_breakout_results.extend(find_breakouts_result.breakouts)
        else:
            false_positive_breakout_results.extend(find_breakouts_result.breakouts)

    write_breakout_results_to_csv(
        results=positive_breakout_results,
        output_file_path="model/training/resistance_breakouts_positive.csv",
        desc="write_positive_breakout_results_to_csv",
    )

    write_breakout_results_to_csv(
        results=false_positive_breakout_results,
        output_file_path="model/training/resistance_breakouts_false_positive.csv",
        desc="write_false_positive_breakout_results_to_csv",
    )

    print("")
    print("Done.")
    print(f"Positive breakout rows: {len(positive_breakout_results)}")
    print(f"False-positive breakout rows: {len(false_positive_breakout_results)}")
