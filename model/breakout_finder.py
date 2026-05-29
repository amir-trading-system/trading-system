#pylint: skip-file

import concurrent.futures
import datetime
import pickle
import glob
import csv
import math
import statistics
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
class ResistanceZone:
    symbol: str
    resistance_price: float
    zone_low: float
    zone_high: float
    first_touch_time: datetime.datetime
    last_touch_time: datetime.datetime
    touch_count: int
    rejection_count: int
    max_rejection_pct: float
    max_rejection_abs: float
    source: str


@dataclass
class BreakoutResult:
    symbol: str
    trade_date: str
    bar_time: datetime.datetime
    is_positive: bool

    breakout_type: str  # valid_breakout / false_breakout
    breakout_time: datetime.datetime

    resistance_price: float
    zone_low: float
    zone_high: float
    resistance_touch_count: int
    resistance_rejection_count: int
    resistance_max_rejection_pct: float
    resistance_max_rejection_abs: float
    resistance_source: str

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

    close_above_zone_pct: float
    close_above_zone_abs: float

    max_gain_after_breakout_pct: float
    max_gain_after_breakout_abs: float
    max_gain_after_breakout_high: Optional[float]
    max_gain_after_breakout_high_time: Optional[datetime.datetime]

    vwap: Optional[float]
    ema_9: Optional[float]
    ema_20: Optional[float]
    macd: Optional[float]
    histogram: Optional[float]
    signal_line: Optional[float]

    follow_through_high_1m: Optional[float]
    follow_through_high_3m: Optional[float]
    follow_through_high_5m: Optional[float]

    max_pullback_below_zone_1m: Optional[float]
    max_pullback_below_zone_3m: Optional[float]
    max_pullback_below_zone_5m: Optional[float]

    failed_within_1m: bool
    failed_within_3m: bool
    failed_within_5m: bool

    reason: str


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


def calculate_dynamic_zone_tolerance(
    price: float,
    recent_bars: list[common.objects.BarData],
) -> float:
    """
    Resistance should be a zone, not one exact price.

    This gives larger tolerance when the stock is volatile,
    but still keeps the zone tight enough for low-priced stocks.
    """

    recent_ranges = [
        get_bar_range(bar_object)
        for bar_object in recent_bars[-20:]
        if safe_float(bar_object.high, 0.0) > safe_float(bar_object.low, 0.0)
    ]

    median_range = statistics.median(recent_ranges) if recent_ranges else price * 0.005

    return max(
        0.01,
        price * 0.004,
        median_range * 0.25,
    )


def bar_rejected_from_level(
    bars: list[common.objects.BarData],
    touch_index: int,
    level: float,
    lookahead_bars: int = 5,
    min_rejection_pct: float = 0.018,
) -> tuple[bool, float, float]:
    """
    Checks whether price touched a level and then rejected from it.

    Returns:
        rejected
        rejection_pct
        rejection_abs
    """

    if touch_index >= len(bars):
        return False, 0.0, 0.0

    touch_bar = bars[touch_index]
    touch_high = safe_float(touch_bar.high, 0.0)

    future_bars = bars[touch_index + 1: touch_index + 1 + lookahead_bars]

    if not future_bars:
        return False, 0.0, 0.0

    min_future_low = min(
        safe_float(bar_object.low, touch_high)
        for bar_object in future_bars
    )

    rejection_abs = max(0.0, touch_high - min_future_low)
    rejection_pct = rejection_abs / level if level > 0 else 0.0

    return rejection_pct >= min_rejection_pct, rejection_pct, rejection_abs


def find_meaningful_resistance_zones(
    bars_until_now: list[common.objects.BarData],
    symbol: str,
    min_prior_bars: int = 8,
    min_touches: int = 1,
    min_rejections: int = 1,
    lookback_bars: int = 90,
) -> list[ResistanceZone]:
    """
    Finds meaningful prior resistance zones before the current breakout candidate.

    Meaningful resistance:
    - local swing high
    - caused rejection
    - optionally repeated touches around same zone
    """

    if len(bars_until_now) < min_prior_bars:
        return []

    bars = bars_until_now[-lookback_bars:]

    candidate_levels: list[float] = []

    for i in range(1, len(bars) - 1):
        prev_bar = bars[i - 1]
        bar_object = bars[i]
        next_bar = bars[i + 1]

        high = safe_float(bar_object.high, 0.0)

        is_local_swing_high = (
            high >= safe_float(prev_bar.high, 0.0)
            and high >= safe_float(next_bar.high, 0.0)
        )

        rejected, _, _ = bar_rejected_from_level(
            bars=bars,
            touch_index=i,
            level=high,
            lookahead_bars=5,
            min_rejection_pct=0.018,
        )

        if is_local_swing_high and rejected:
            candidate_levels.append(high)

    # Also include the highest high so far if it caused rejection.
    highest_bar_index = max(
        range(len(bars)),
        key=lambda idx: safe_float(bars[idx].high, 0.0),
    )

    highest_high = safe_float(bars[highest_bar_index].high, 0.0)

    rejected, _, _ = bar_rejected_from_level(
        bars=bars,
        touch_index=highest_bar_index,
        level=highest_high,
        lookahead_bars=8,
        min_rejection_pct=0.018,
    )

    if rejected:
        candidate_levels.append(highest_high)

    zones: list[ResistanceZone] = []

    for level in candidate_levels:
        tolerance = calculate_dynamic_zone_tolerance(
            price=level,
            recent_bars=bars,
        )

        zone_low = level - tolerance
        zone_high = level + tolerance

        touches: list[common.objects.BarData] = []
        rejection_count = 0
        max_rejection_pct = 0.0
        max_rejection_abs = 0.0

        for i, bar_object in enumerate(bars):
            high = safe_float(bar_object.high, 0.0)
            close = safe_float(bar_object.close, 0.0)

            touched_zone = (
                zone_low <= high <= zone_high
                or zone_low <= close <= zone_high
                or high > zone_high and close < zone_high
            )

            if not touched_zone:
                continue

            rejected, rejection_pct, rejection_abs = bar_rejected_from_level(
                bars=bars,
                touch_index=i,
                level=level,
                lookahead_bars=5,
                min_rejection_pct=0.012,
            )

            touches.append(bar_object)

            if rejected:
                rejection_count += 1
                max_rejection_pct = max(max_rejection_pct, rejection_pct)
                max_rejection_abs = max(max_rejection_abs, rejection_abs)

        if len(touches) < min_touches:
            continue

        if rejection_count < min_rejections:
            continue

        zones.append(
            ResistanceZone(
                symbol=symbol,
                resistance_price=level,
                zone_low=zone_low,
                zone_high=zone_high,
                first_touch_time=touches[0].bar_time,
                last_touch_time=touches[-1].bar_time,
                touch_count=len(touches),
                rejection_count=rejection_count,
                max_rejection_pct=max_rejection_pct,
                max_rejection_abs=max_rejection_abs,
                source="swing_high_with_rejection",
            )
        )

    zones = sorted(
        zones,
        key=lambda zone: zone.resistance_price,
    )

    deduped: list[ResistanceZone] = []

    for zone in zones:
        if not deduped:
            deduped.append(zone)
            continue

        previous = deduped[-1]
        zones_overlap = zone.zone_low <= previous.zone_high

        if zones_overlap:
            previous_score = (
                previous.touch_count * 1.0
                + previous.rejection_count * 2.0
                + previous.max_rejection_pct * 100.0
            )

            current_score = (
                zone.touch_count * 1.0
                + zone.rejection_count * 2.0
                + zone.max_rejection_pct * 100.0
            )

            if current_score > previous_score:
                deduped[-1] = zone
        else:
            deduped.append(zone)

    return deduped


def is_valid_breakout_bar(
    bar_object: common.objects.BarData,
    resistance_zone: ResistanceZone,
    recent_bars: list[common.objects.BarData],
) -> tuple[bool, str]:
    """
    Valid breakout means:
    - high breaks above zone
    - close confirms above zone
    - volume confirms
    - candle is not mostly upper wick
    - close is strong inside candle range
    """

    open_value = safe_float(bar_object.open_value, 0.0)
    high = safe_float(bar_object.high, 0.0)
    close = safe_float(bar_object.close, 0.0)

    volume_ratio = get_volume_ratio(bar_object)
    candle_stats = get_candle_stats(bar_object)

    zone_high = resistance_zone.zone_high
    zone_width = resistance_zone.zone_high - resistance_zone.zone_low

    min_close_above = max(
        0.005,
        close * 0.0015,
        zone_width * 0.25,
    )

    high_above_zone = high > zone_high + min_close_above
    close_above_zone = close > zone_high + min_close_above

    if not high_above_zone:
        return False, "high_did_not_clear_zone"

    if not close_above_zone:
        return False, "high_broke_zone_but_close_did_not_confirm"

    if close <= open_value:
        return False, "red_breakout_candle"

    if volume_ratio < 1.5:
        return False, "volume_ratio_too_low"

    if candle_stats["close_position_in_range"] < 0.60:
        return False, "close_not_strong_enough_in_range"

    if candle_stats["upper_wick_pct_of_range"] > 0.45:
        return False, "upper_wick_too_large"

    # This marks very late/extended moves as not "clean structure breakouts".
    # If this filters out too many good positive examples, loosen or remove it.
    last_5 = recent_bars[-5:]

    if len(last_5) >= 5:
        green_count = sum(
            1
            for b in last_5
            if safe_float(b.close, 0.0) > safe_float(b.open_value, 0.0)
        )

        move_from_5_bars_ago = pct_change(
            safe_float(last_5[0].close, close),
            close,
        )

        if green_count >= 5 and move_from_5_bars_ago > 0.25:
            return False, "too_extended_after_5_green_bars"

    return True, "valid_breakout_confirmed"


def is_false_breakout_bar(
    bar_object: common.objects.BarData,
    resistance_zone: ResistanceZone,
    future_bars: list[common.objects.BarData],
) -> tuple[bool, str]:
    """
    False breakout means:
    - high breaks above resistance but close fails
    OR
    - close breaks above resistance but price quickly loses the zone
    """

    high = safe_float(bar_object.high, 0.0)
    close = safe_float(bar_object.close, 0.0)

    zone_high = resistance_zone.zone_high
    zone_low = resistance_zone.zone_low

    volume_ratio = get_volume_ratio(bar_object)
    candle_stats = get_candle_stats(bar_object)

    high_broke_zone = high > zone_high

    if not high_broke_zone:
        return False, "no_breakout_attempt"

    if close <= zone_high:
        return True, "wick_break_above_resistance_close_failed"

    if (
        candle_stats["upper_wick_pct_of_range"] > 0.55
        and candle_stats["close_position_in_range"] < 0.55
    ):
        return True, "breakout_with_large_upper_wick"

    next_3 = future_bars[:3]

    if next_3:
        failed_next_3 = any(
            safe_float(future_bar.close, 0.0) < zone_low
            for future_bar in next_3
        )

        if failed_next_3:
            return True, "closed_above_but_failed_below_zone_within_3_bars"

    if volume_ratio >= 2.0 and close <= zone_high:
        return True, "high_volume_failed_breakout"

    return False, "breakout_attempt_did_not_fail"


def calculate_follow_through_stats(
    bar_index: int,
    bars: list[common.objects.BarData],
    zone: ResistanceZone,
) -> dict[str, Optional[float] | bool]:
    def future_slice(minutes: int) -> list[common.objects.BarData]:
        return bars[bar_index + 1: bar_index + 1 + minutes]

    def max_future_high(minutes: int) -> Optional[float]:
        future = future_slice(minutes)

        if not future:
            return None

        return max(
            safe_float(bar_object.high, 0.0)
            for bar_object in future
        )

    def max_pullback_below_zone(minutes: int) -> Optional[float]:
        future = future_slice(minutes)

        if not future:
            return None

        min_low = min(
            safe_float(bar_object.low, 0.0)
            for bar_object in future
        )

        return max(0.0, zone.zone_low - min_low)

    def failed_within(minutes: int) -> bool:
        future = future_slice(minutes)

        if not future:
            return False

        return any(
            safe_float(bar_object.close, 0.0) < zone.zone_low
            for bar_object in future
        )

    return {
        "follow_through_high_1m": max_future_high(1),
        "follow_through_high_3m": max_future_high(3),
        "follow_through_high_5m": max_future_high(5),

        "max_pullback_below_zone_1m": max_pullback_below_zone(1),
        "max_pullback_below_zone_3m": max_pullback_below_zone(3),
        "max_pullback_below_zone_5m": max_pullback_below_zone(5),

        "failed_within_1m": failed_within(1),
        "failed_within_3m": failed_within(3),
        "failed_within_5m": failed_within(5),
    }


def calculate_max_gain_after_breakout(
    bar_index: int,
    bars: list[common.objects.BarData],
) -> dict[str, Optional[float] | Optional[datetime.datetime]]:
    """
    Calculates the maximum upside after a breakout.

    The gain is measured from the breakout candle close to the highest
    future high in the remaining bars of the same trading day.

    Example:
        breakout close = 2.00
        highest later high = 2.50
        max_gain_after_breakout_pct = 25.0
    """

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


def build_breakout_result(
    data: dict[str, Any],
    bars: list[common.objects.BarData],
    bar_index: int,
    zone: ResistanceZone,
    breakout_type: str,
    reason: str,
) -> BreakoutResult:
    bar_object = bars[bar_index]

    specific_bar_time: datetime.datetime = data["day_timeframe_stock"].specific_bar_time
    is_positive: bool = data["day_timeframe_stock"].is_positive

    open_value = safe_float(bar_object.open_value, 0.0)
    high = safe_float(bar_object.high, 0.0)
    low = safe_float(bar_object.low, 0.0)
    close = safe_float(bar_object.close, 0.0)
    volume = safe_float(bar_object.volume, 0.0)
    volume_average = safe_float(bar_object.volume_average, 0.0)
    volume_ratio = get_volume_ratio(bar_object)
    bar_time = bar_object.bar_time

    candle_stats = get_candle_stats(bar_object)

    follow_through_stats = calculate_follow_through_stats(
        bar_index=bar_index,
        bars=bars,
        zone=zone,
    )

    max_gain_after_breakout_stats = calculate_max_gain_after_breakout(
        bar_index=bar_index,
        bars=bars,
    )

    return BreakoutResult(
        symbol=bar_object.symbol,
        trade_date=str(specific_bar_time.date()),
        bar_time=bar_time,
        is_positive=is_positive,

        breakout_type=breakout_type,
        breakout_time=bar_object.bar_time,

        resistance_price=zone.resistance_price,
        zone_low=zone.zone_low,
        zone_high=zone.zone_high,
        resistance_touch_count=zone.touch_count,
        resistance_rejection_count=zone.rejection_count,
        resistance_max_rejection_pct=zone.max_rejection_pct,
        resistance_max_rejection_abs=zone.max_rejection_abs,
        resistance_source=zone.source,

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

        close_above_zone_pct=pct_change(zone.zone_high, close),
        close_above_zone_abs=close - zone.zone_high,

        max_gain_after_breakout_pct=max_gain_after_breakout_stats["max_gain_after_breakout_pct"],
        max_gain_after_breakout_abs=max_gain_after_breakout_stats["max_gain_after_breakout_abs"],
        max_gain_after_breakout_high=max_gain_after_breakout_stats["max_gain_after_breakout_high"],
        max_gain_after_breakout_high_time=max_gain_after_breakout_stats["max_gain_after_breakout_high_time"],

        vwap=safe_float(getattr(bar_object, "vwap", 0), 0),
        ema_9=safe_float(getattr(bar_object, "ema_9", 0), 0),
        ema_20=safe_float(getattr(bar_object, "ema_20", 0), 0),
        macd=safe_float(getattr(bar_object, "macd", 0), 0),
        histogram=safe_float(getattr(bar_object, "histogram", 0), 0),
        signal_line=safe_float(getattr(bar_object, "signal_line", 0), 0),

        follow_through_high_1m=follow_through_stats["follow_through_high_1m"],
        follow_through_high_3m=follow_through_stats["follow_through_high_3m"],
        follow_through_high_5m=follow_through_stats["follow_through_high_5m"],

        max_pullback_below_zone_1m=follow_through_stats["max_pullback_below_zone_1m"],
        max_pullback_below_zone_3m=follow_through_stats["max_pullback_below_zone_3m"],
        max_pullback_below_zone_5m=follow_through_stats["max_pullback_below_zone_5m"],

        failed_within_1m=follow_through_stats["failed_within_1m"],
        failed_within_3m=follow_through_stats["failed_within_3m"],
        failed_within_5m=follow_through_stats["failed_within_5m"],

        reason=reason,
    )


def find_breakouts_for_trade(
    data: dict[str, Any],
    one_minute_bars: list[common.objects.BarData],
) -> list[BreakoutResult]:
    """
    Finds valid and false breakouts for one stock/day.
    """

    results: list[BreakoutResult] = []

    bars = sorted(
        one_minute_bars,
        key=lambda bar: bar.bar_time,
    )

    if len(bars) < 15:
        return results

    symbol = bars[0].symbol

    for i in range(10, len(bars)):
        current_bar = bars[i]
        bars_before_current = bars[:i]
        recent_bars = bars[max(0, i - 10):i]
        future_bars = bars[i + 1:i + 6]

        market_open_time = datetime.datetime(
            year=current_bar.bar_time.year,
            month=current_bar.bar_time.month,
            day=current_bar.bar_time.day,
            hour=9,
            minute=30
        )

        market_close_time = datetime.datetime(
            year=current_bar.bar_time.year,
            month=current_bar.bar_time.month,
            day=current_bar.bar_time.day,
            hour=16,
        )

        if current_bar.bar_time <= market_open_time or current_bar.bar_time >= market_close_time:
            continue

        resistance_zones = find_meaningful_resistance_zones(
            bars_until_now=bars_before_current,
            symbol=symbol,
            min_prior_bars=8,
            min_touches=1,
            min_rejections=1,
            lookback_bars=90,
        )

        if not resistance_zones:
            continue

        candidate_zones = [
            zone
            for zone in resistance_zones
            if safe_float(current_bar.high, 0.0) > zone.zone_high
        ]

        if not candidate_zones:
            continue

        # Use the highest broken resistance, so one candle does not create
        # duplicate rows for every lower old resistance.
        selected_zone = sorted(
            candidate_zones,
            key=lambda zone: zone.resistance_price,
            reverse=True,
        )[0]

        is_valid, valid_reason = is_valid_breakout_bar(
            bar_object=current_bar,
            resistance_zone=selected_zone,
            recent_bars=recent_bars,
        )

        if is_valid:
            results.append(
                build_breakout_result(
                    data=data,
                    bars=bars,
                    bar_index=i,
                    zone=selected_zone,
                    breakout_type="valid_breakout",
                    reason=valid_reason,
                )
            )
            continue

        is_false, false_reason = is_false_breakout_bar(
            bar_object=current_bar,
            resistance_zone=selected_zone,
            future_bars=future_bars,
        )

        if is_false:
            results.append(
                build_breakout_result(
                    data=data,
                    bars=bars,
                    bar_index=i,
                    zone=selected_zone,
                    breakout_type="false_breakout",
                    reason=false_reason,
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


def write_breakout_summary_to_csv(
    results: list[BreakoutResult],
    output_file_path: str,
) -> None:
    grouped: dict[tuple[bool, str, str], int] = {}

    for result in results:
        key = (
            result.is_positive,
            result.breakout_type,
            result.reason,
        )
        grouped[key] = grouped.get(key, 0) + 1

    rows = []

    for (is_positive, breakout_type, reason), count in grouped.items():
        rows.append(
            {
                "is_positive": is_positive,
                "breakout_type": breakout_type,
                "reason": reason,
                "count": count,
            }
        )

    rows = sorted(
        rows,
        key=lambda row: (
            str(row["is_positive"]),
            row["breakout_type"],
            -row["count"],
        ),
    )

    fieldnames = [
        "is_positive",
        "breakout_type",
        "reason",
        "count",
    ]

    with open(output_file_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} summary rows to: {output_file_path}")

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
                len(training_model_data_list)
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

    write_breakout_summary_to_csv(
        results=positive_breakout_results,
        output_file_path="model/training/resistance_breakouts_positive_summary.csv",
    )

    write_breakout_summary_to_csv(
        results=false_positive_breakout_results,
        output_file_path="model/training/resistance_breakouts_false_positive_summary.csv",
    )

    print("")
    print("Done.")
    print(f"Positive breakout rows: {len(positive_breakout_results)}")
    print(f"False-positive breakout rows: {len(false_positive_breakout_results)}")
