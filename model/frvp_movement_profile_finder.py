# pylint: skip-file
"""
FRVP movement-profile finder v8.

Purpose:
    Before scanning entries, identify the movement ranges that should be used
    for FRVP/volume-profile analysis. The output is intentionally compact and
    only contains fields relevant to the Confirmed Value Breakout workflow.

Core idea:
    1. Find meaningful volume-campaign / impulse movement segments.
    2. Calculate an approximate FRVP on each movement segment.
    3. Export VAL / POC / VAH, upper fight-zone estimates, and the first later
       bars that reclaim VAH / fight zone with volume.

Important:
    This approximates TradingView FRVP from 1-minute OHLCV bars. v8 uses fixed
    row-count bins (similar to TradingView's Number of Rows mode) plus
    body-weighted OHLCV allocation. This should better match visual TradingView
    levels than one-cent/tick bins, although it still cannot be penny-perfect
    without lower-timeframe/tick volume-at-price data.
"""

import concurrent.futures
import csv
import datetime
import glob
import math
import os
import pickle
from dataclasses import asdict, dataclass
from statistics import median
from typing import Any, Optional

# The training files are pickled objects even though the historical glob uses *.json.
INPUT_FILES_GLOB = "model/training/data/*.json"
OUTPUT_COMBINED_FILE = "model/frvp_movement_profiles.csv"
OUTPUT_CANDIDATES_FILE = "model/frvp_movement_profile_candidates.csv"
OUTPUT_VALID_FILE = "model/frvp_movement_profiles_valid.csv"
MAX_WORKERS = 10

MARKET_OPEN = datetime.time(9, 30)
MARKET_CLOSE = datetime.time(20, 0)
PREMARKET_START = datetime.time(4, 0)

FRVP_VALUE_AREA_PCT = 0.70
FRVP_TICK_SIZE = 0.01  # fallback only; v8 normally uses fixed row-count bins
FRVP_ROW_COUNT = 60

# OHLCV-to-volume-profile approximation.
# v8 uses fixed row-count bins, similar to TradingView's Number of Rows setting.
# The previous tick/penny-bin method was too granular and over-inflated VAH in
# examples like PAVS. We still allocate most volume to candle body and less to
# wicks to avoid treating long tails as accepted value.
FRVP_BODY_VOLUME_SHARE = 0.70
FRVP_UPPER_WICK_VOLUME_SHARE = 0.15
FRVP_LOWER_WICK_VOLUME_SHARE = 0.15

# Movement detection settings.
MIN_SEGMENT_BARS = 2
MIN_SEGMENT_VOLUME = 50_000
MIN_SEGMENT_RANGE_PCT = 0.035
MIN_ABS_HIGH_VOLUME_BAR = 10_000
HIGH_VOLUME_MEDIAN_MULTIPLIER = 2.50
HIGH_VOLUME_P75_MULTIPLIER = 1.15
CLUSTER_MERGE_GAP_BARS = 4
MAX_SEGMENT_DURATION_BARS = 150
DRYNESS_CONSECUTIVE_BARS = 3
DRYNESS_VOLUME_RATIO_TO_CLUSTER_AVG = 0.45
NEW_HIGH_TOLERANCE_PCT = 0.002

# Upper war-zone detection settings.
# The old v2 fight-zone detector only found the first small volume shelf above VAH.
# v3 expands that into the full contested area above VAH by combining:
#   1) first meaningful volume shelf,
#   2) cumulative above-VAH volume coverage,
#   3) repeated/rejected highs near the upper shelf.
UPPER_FIGHT_MIN_ABOVE_VAH_VOLUME_PCT = 0.012
UPPER_FIGHT_ABOVE_VAH_COVERAGE_PCT = 0.72
UPPER_FIGHT_MAX_TAIL_VOLUME_PCT = 0.08
UPPER_FIGHT_REPEATED_HIGH_BUCKET_PCT = 0.012
UPPER_FIGHT_REPEATED_HIGH_MIN_TOUCHES = 2
UPPER_FIGHT_REJECTION_MIN_UPPER_WICK_SHARE = 0.30
UPPER_FIGHT_REJECTION_MIN_VOLUME_TO_SEGMENT_AVG = 0.45

# Later validation / candidate-entry debug settings.
ENTRY_SCAN_MAX_BARS_AFTER_PROFILE = 300
ENTRY_VOLUME_AVG_LOOKBACK = 10
ENTRY_VOLUME_MAX_LOOKBACK = 5
ENTRY_MIN_VOLUME_VS_RECENT_AVG = 1.50
ENTRY_MIN_VOLUME_VS_RECENT_MAX = 1.20
ENTRY_MIN_DECISIVE_VOLUME_VS_RECENT_AVG = 1.25
ENTRY_MIN_DECISIVE_VOLUME_VS_PREVIOUS = 1.35
ENTRY_MIN_DECISIVE_CLOSE_ABOVE_LINE_PCT = 0.01
ENTRY_MIN_CLOSE_POSITION = 0.55
ENTRY_MAX_UPPER_WICK_SHARE = 0.45
LEVEL_TOLERANCE_PCT = 0.002


@dataclass
class MovementProfileRow:
    symbol: str
    trade_date: str
    is_positive: bool

    movement_id: int
    profile_role: str
    session_type: str
    movement_type: str
    movement_start_time: datetime.datetime
    movement_end_time: datetime.datetime
    movement_duration_minutes: float
    movement_bar_count: int

    movement_start_open: float
    movement_end_close: float
    movement_low: float
    movement_low_time: datetime.datetime
    movement_high: float
    movement_high_time: datetime.datetime
    movement_range_pct: float
    movement_gain_from_start_open_pct: float
    movement_gain_from_low_to_high_pct: float

    movement_total_volume: float
    movement_avg_volume: float
    movement_max_volume: float
    movement_max_volume_time: datetime.datetime
    movement_high_volume_bar_count: int
    movement_volume_after_high_pct: Optional[float]

    # Movement/no-movement diagnostics. These are intentionally exported before
    # adding hard filters so we can learn which values separate real movements
    # from thin/choppy ranges such as CAST.
    movement_median_volume: float
    movement_volume_per_minute: float
    movement_top_3_volume_pct: float
    movement_bars_volume_over_10k: int
    movement_bars_volume_over_25k: int
    movement_bars_volume_over_50k: int
    movement_meaningful_range_bar_count: int
    movement_large_range_bar_count: int
    movement_zero_range_bar_count: int
    movement_flat_bar_count: int
    movement_green_bar_count: int
    movement_red_bar_count: int
    movement_green_volume_pct: Optional[float]
    movement_red_volume_pct: Optional[float]
    movement_range_per_100k_volume: Optional[float]
    movement_abs_close_change_per_100k_volume: Optional[float]
    movement_high_from_start_pct: Optional[float]
    movement_low_from_start_pct: Optional[float]
    movement_close_near_high_bar_count: int
    movement_close_near_low_bar_count: int
    movement_quality_score: float
    movement_quality_notes: str
    movement_is_valid: bool
    movement_invalid_reasons: str

    impulse_cluster_start_time: datetime.datetime
    impulse_cluster_end_time: datetime.datetime
    impulse_cluster_bar_count: int
    impulse_cluster_total_volume: float
    impulse_cluster_avg_volume: float
    high_volume_threshold: float

    frvp_value_area_pct: float
    frvp_val: float
    frvp_poc: float
    frvp_vah: float
    frvp_profile_low: float
    frvp_profile_high: float
    frvp_total_volume: float
    frvp_volume_below_val_pct: float
    frvp_volume_inside_value_pct: float
    frvp_volume_above_vah_pct: float

    upper_fight_zone_low: Optional[float]
    upper_fight_zone_high: Optional[float]
    upper_fight_zone_volume: Optional[float]
    upper_fight_zone_volume_pct: Optional[float]
    upper_fight_zone_width_pct: Optional[float]

    first_close_above_vah_time: Optional[datetime.datetime]
    first_close_above_vah_close: Optional[float]
    first_close_above_fight_zone_time: Optional[datetime.datetime]
    first_close_above_fight_zone_close: Optional[float]
    first_confirmed_breakout_time: Optional[datetime.datetime]
    first_confirmed_breakout_close: Optional[float]
    first_confirmed_breakout_volume: Optional[float]
    first_confirmed_breakout_volume_vs_recent_avg: Optional[float]
    first_confirmed_breakout_volume_vs_recent_max: Optional[float]

    profile_quality_score: float
    profile_quality_notes: str


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        result = float(value)
        if math.isnan(result):
            return default
        return result
    except Exception:
        return default


def ratio(value: Optional[float], base: Optional[float]) -> Optional[float]:
    value = safe_float(value, None)
    base = safe_float(base, None)
    if value is None or base is None or base <= 0:
        return None
    return value / base


def pct_change(base: Optional[float], value: Optional[float]) -> Optional[float]:
    base = safe_float(base, None)
    value = safe_float(value, None)
    if base is None or value is None or base <= 0:
        return None
    return (value - base) / base


def minutes_between(start: datetime.datetime, end: datetime.datetime) -> float:
    return (end - start).total_seconds() / 60.0


def bar_open(bar: Any) -> float:
    return safe_float(getattr(bar, "open_value", None), 0.0) or 0.0


def bar_high(bar: Any) -> float:
    return safe_float(getattr(bar, "high", None), 0.0) or 0.0


def bar_low(bar: Any) -> float:
    return safe_float(getattr(bar, "low", None), 0.0) or 0.0


def bar_close(bar: Any) -> float:
    return safe_float(getattr(bar, "close", None), 0.0) or 0.0


def bar_volume(bar: Any) -> float:
    return safe_float(getattr(bar, "volume", None), 0.0) or 0.0


def candle_stats(bar: Any) -> dict[str, float]:
    open_value = bar_open(bar)
    high = bar_high(bar)
    low = bar_low(bar)
    close = bar_close(bar)
    candle_range = max(0.000001, high - low)
    return {
        "close_position": (close - low) / candle_range,
        "upper_wick_share": (high - max(open_value, close)) / candle_range,
        "range_pct": candle_range / max(0.000001, open_value),
    }


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    k = (len(values) - 1) * pct
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values[int(k)]
    return values[f] * (c - k) + values[c] * (k - f)


def load_pickle_data(file_path: str) -> Any:
    with open(file_path, "rb") as f:
        return pickle.load(f)


def get_trade_date(data: dict[str, Any], bars: list[Any]) -> str:
    day_stock = data.get("day_timeframe_stock")
    if getattr(day_stock, "specific_bar_time", None) is not None:
        return str(day_stock.specific_bar_time.date())
    if bars:
        return str(bars[0].bar_time.date())
    return ""


def filter_trade_date_bars(data: dict[str, Any], bars: list[Any]) -> list[Any]:
    day_stock = data.get("day_timeframe_stock")
    if getattr(day_stock, "specific_bar_time", None) is None:
        return bars
    trade_date = day_stock.specific_bar_time.date()
    return [bar for bar in bars if bar.bar_time.date() == trade_date]


def bars_for_session(bars: list[Any], session_type: str) -> list[Any]:
    if session_type == "premarket":
        return [
            bar for bar in bars
            if PREMARKET_START <= bar.bar_time.time() < MARKET_OPEN
        ]
    if session_type == "rth":
        return [
            bar for bar in bars
            if MARKET_OPEN <= bar.bar_time.time() <= MARKET_CLOSE
        ]
    raise ValueError(f"Unknown session type: {session_type}")


def session_high_volume_threshold(session_bars: list[Any]) -> float:
    volumes = [bar_volume(bar) for bar in session_bars if bar_volume(bar) > 0]
    if not volumes:
        return MIN_ABS_HIGH_VOLUME_BAR
    med = median(volumes)
    p75 = percentile(volumes, 0.75)
    return max(
        MIN_ABS_HIGH_VOLUME_BAR,
        med * HIGH_VOLUME_MEDIAN_MULTIPLIER,
        p75 * HIGH_VOLUME_P75_MULTIPLIER,
    )


def is_high_volume_impulse_bar(bar: Any, high_volume_threshold: float) -> bool:
    stats = candle_stats(bar)
    return bool(
        bar_volume(bar) >= high_volume_threshold
        and bar_volume(bar) >= MIN_ABS_HIGH_VOLUME_BAR
        and stats["range_pct"] >= 0.005
    )


def high_volume_clusters(session_bars: list[Any], threshold: float) -> list[tuple[int, int]]:
    indexes = [
        index for index, bar in enumerate(session_bars)
        if is_high_volume_impulse_bar(bar, threshold)
    ]
    if not indexes:
        return []

    clusters: list[tuple[int, int]] = []
    start = indexes[0]
    end = indexes[0]

    for index in indexes[1:]:
        if index - end <= CLUSTER_MERGE_GAP_BARS:
            end = index
        else:
            clusters.append((start, end))
            start = index
            end = index

    clusters.append((start, end))
    return clusters


def extend_cluster_to_movement(
    session_bars: list[Any],
    cluster_start: int,
    cluster_end: int,
    high_volume_threshold: float,
) -> tuple[int, int]:
    # Include 1-2 setup bars immediately before the first high-volume bar if they
    # are already moving or have non-trivial volume. This helps align with manual
    # TradingView ranges where the move starts just before the largest volume bar.
    start = cluster_start
    for candidate in range(cluster_start - 1, max(-1, cluster_start - 3), -1):
        if candidate < 0:
            break
        candidate_bar = session_bars[candidate]
        next_bar = session_bars[candidate + 1]
        if (
            bar_volume(candidate_bar) >= high_volume_threshold * 0.35
            or bar_high(next_bar) > bar_high(candidate_bar) * 1.01
        ):
            start = candidate
        else:
            break

    cluster_volumes = [bar_volume(bar) for bar in session_bars[cluster_start:cluster_end + 1]]
    cluster_avg_volume = sum(cluster_volumes) / len(cluster_volumes) if cluster_volumes else high_volume_threshold
    dry_volume_threshold = max(MIN_ABS_HIGH_VOLUME_BAR, cluster_avg_volume * DRYNESS_VOLUME_RATIO_TO_CLUSTER_AVG)

    end = cluster_end
    highest_high = max(bar_high(bar) for bar in session_bars[start:end + 1])
    bars_since_high_progress = 0
    dry_count = 0

    max_end = min(len(session_bars) - 1, start + MAX_SEGMENT_DURATION_BARS - 1)
    index = cluster_end + 1

    while index <= max_end:
        bar = session_bars[index]
        high = bar_high(bar)
        volume = bar_volume(bar)

        made_high_progress = high > highest_high * (1 + NEW_HIGH_TOLERANCE_PCT)
        if made_high_progress:
            highest_high = high
            bars_since_high_progress = 0
            dry_count = 0
        else:
            bars_since_high_progress += 1

        # Keep the immediate rejection / sell response as part of the first movement
        # if it still has material volume. End only after several low-volume bars
        # with no upside progress.
        is_dry = volume < dry_volume_threshold and bars_since_high_progress >= 2
        if is_dry:
            dry_count += 1
        else:
            dry_count = 0

        if dry_count >= DRYNESS_CONSECUTIVE_BARS:
            end = index - DRYNESS_CONSECUTIVE_BARS
            break

        end = index
        index += 1

    return (start, max(start, end))


def movement_passes_minimums(segment_bars: list[Any]) -> bool:
    if len(segment_bars) < MIN_SEGMENT_BARS:
        return False

    total_volume = sum(bar_volume(bar) for bar in segment_bars)
    if total_volume < MIN_SEGMENT_VOLUME:
        return False

    lows = [bar_low(bar) for bar in segment_bars]
    highs = [bar_high(bar) for bar in segment_bars]
    start_open = bar_open(segment_bars[0])
    range_pct = (max(highs) - min(lows)) / max(0.000001, start_open)
    return range_pct >= MIN_SEGMENT_RANGE_PCT


def detect_movement_segments(
    session_bars: list[Any],
    session_type: str,
) -> list[dict[str, Any]]:
    if len(session_bars) < MIN_SEGMENT_BARS:
        return []

    threshold = session_high_volume_threshold(session_bars)
    clusters = high_volume_clusters(session_bars, threshold)
    if not clusters:
        return []

    raw_segments: list[dict[str, Any]] = []
    consumed_until = -1

    for cluster_start, cluster_end in clusters:
        if cluster_start <= consumed_until:
            continue

        start, end = extend_cluster_to_movement(
            session_bars=session_bars,
            cluster_start=cluster_start,
            cluster_end=cluster_end,
            high_volume_threshold=threshold,
        )

        if start <= consumed_until:
            start = consumed_until + 1

        segment_bars = session_bars[start:end + 1]
        if not movement_passes_minimums(segment_bars):
            continue

        raw_segments.append({
            "session_type": session_type,
            "start_index": start,
            "end_index": end,
            "cluster_start_index": cluster_start,
            "cluster_end_index": cluster_end,
            "high_volume_threshold": threshold,
        })
        consumed_until = end + CLUSTER_MERGE_GAP_BARS

    return raw_segments



def make_fixed_segment(
    session_bars: list[Any],
    session_type: str,
    start_index: int,
    end_index: int,
    role: str,
) -> Optional[dict[str, Any]]:
    if not session_bars or start_index < 0 or end_index >= len(session_bars) or end_index < start_index:
        return None
    threshold = session_high_volume_threshold(session_bars)
    segment_bars = session_bars[start_index:end_index + 1]
    if not movement_passes_minimums(segment_bars):
        return None

    # Pick the strongest local high-volume cluster inside the fixed segment only for debug columns.
    local_high_volume_indexes = [
        idx for idx in range(start_index, end_index + 1)
        if is_high_volume_impulse_bar(session_bars[idx], threshold)
    ]
    if local_high_volume_indexes:
        cluster_start = local_high_volume_indexes[0]
        cluster_end = local_high_volume_indexes[-1]
    else:
        max_vol_index = max(range(start_index, end_index + 1), key=lambda i: bar_volume(session_bars[i]))
        cluster_start = max_vol_index
        cluster_end = max_vol_index

    return {
        "session_type": session_type,
        "start_index": start_index,
        "end_index": end_index,
        "cluster_start_index": cluster_start,
        "cluster_end_index": cluster_end,
        "high_volume_threshold": threshold,
        "profile_role": role,
    }


def find_premarket_core_after_early_spike(session_bars: list[Any]) -> Optional[dict[str, Any]]:
    """Create a candidate profile that ignores a very early liquidity shock.

    This targets cases like HKIT where the first 1-2 bars make an extreme high,
    then the real later value is built far below that spike. It is intentionally
    conservative: if the early high is not extreme versus later trading, return None.
    """
    if len(session_bars) < 12:
        return None

    high_index = max(range(len(session_bars)), key=lambda i: bar_high(session_bars[i]))
    high_price = bar_high(session_bars[high_index])
    first_quarter_limit = max(3, int(len(session_bars) * 0.25))
    if high_index > first_quarter_limit:
        return None

    later_bars = session_bars[min(len(session_bars) - 1, high_index + 5):]
    later_closes = [bar_close(b) for b in later_bars if bar_close(b) > 0]
    if len(later_closes) < 5:
        return None
    later_median_close = median(later_closes)

    # Require an extreme early high that the rest of premarket clearly failed to accept.
    if high_price < later_median_close * 1.35:
        return None

    # Start after the rejection has migrated below roughly the later median area.
    start_index = None
    for idx in range(high_index + 1, len(session_bars)):
        if bar_close(session_bars[idx]) <= later_median_close * 1.15:
            start_index = idx
            break
    if start_index is None:
        start_index = min(len(session_bars) - 1, high_index + 5)

    # Avoid starting too late on a tiny isolated bar; walk back one bar if it is part of the same sell response.
    if start_index > high_index + 1 and bar_volume(session_bars[start_index - 1]) >= bar_volume(session_bars[start_index]) * 0.50:
        start_index -= 1

    return make_fixed_segment(
        session_bars=session_bars,
        session_type="premarket",
        start_index=start_index,
        end_index=len(session_bars) - 1,
        role="premarket_core_after_early_spike",
    )


def first_n_campaign_segments(session_bars: list[Any], session_type: str, limit: int) -> list[dict[str, Any]]:
    segments = detect_movement_segments(session_bars, session_type)
    return segments[:limit]


def calculate_volume_profile(
    profile_bars: list[Any],
    tick_size: float = FRVP_TICK_SIZE,
    value_area_pct: float = FRVP_VALUE_AREA_PCT,
    row_count: int = FRVP_ROW_COUNT,
) -> Optional[dict[str, Any]]:
    """Approximate a TradingView-style FRVP from 1-minute OHLCV bars.

    v8 change:
        Use a fixed number of profile rows instead of one-cent/tick bins.

    Why:
        TradingView FRVP is usually viewed with a fixed "Number of Rows" style
        profile. The old penny-bin method created too many tiny bins and, on
        wide small-cap moves, often pushed VAH/fight-zone levels too high.
        Fixed rows are much closer to how the visual TradingView profile is read.

    Volume allocation:
        70% of each 1-minute bar volume is allocated across the candle body,
        15% across the upper wick, and 15% across the lower wick.
    """
    _ = tick_size  # kept for backward-compatible call sites; fixed rows are used below.
    if not profile_bars:
        return None

    raw_lows = [bar_low(bar) for bar in profile_bars if bar_low(bar) > 0]
    raw_highs = [bar_high(bar) for bar in profile_bars if bar_high(bar) > 0]
    if not raw_lows or not raw_highs:
        return None

    profile_low_raw = min(raw_lows)
    profile_high_raw = max(raw_highs)
    if profile_high_raw <= profile_low_raw:
        return None

    rows = max(8, int(row_count or FRVP_ROW_COUNT))
    row_height = (profile_high_raw - profile_low_raw) / rows
    if row_height <= 0:
        return None

    edges = [profile_low_raw + i * row_height for i in range(rows + 1)]
    centers = [round((edges[i] + edges[i + 1]) / 2.0, 4) for i in range(rows)]
    volume_by_index = [0.0 for _ in range(rows)]

    def _index_for_price(price_value: float) -> int:
        if price_value <= edges[0]:
            return 0
        if price_value >= edges[-1]:
            return rows - 1
        idx = int((price_value - edges[0]) / row_height)
        return min(max(idx, 0), rows - 1)

    def _add_volume_range(price_a: float, price_b: float, allocated_volume: float) -> None:
        """Spread allocated volume by overlap length across fixed profile rows."""
        if allocated_volume <= 0:
            return

        low_price = min(price_a, price_b)
        high_price = max(price_a, price_b)
        if low_price <= 0 or high_price <= 0:
            return

        low_price = max(low_price, profile_low_raw)
        high_price = min(high_price, profile_high_raw)

        if abs(high_price - low_price) < 1e-9:
            volume_by_index[_index_for_price(low_price)] += allocated_volume
            return

        seg_len = high_price - low_price
        start_idx = _index_for_price(low_price)
        end_idx = _index_for_price(high_price)
        for idx in range(start_idx, end_idx + 1):
            overlap = max(0.0, min(high_price, edges[idx + 1]) - max(low_price, edges[idx]))
            if overlap > 0:
                volume_by_index[idx] += allocated_volume * (overlap / seg_len)

    for bar in profile_bars:
        high = bar_high(bar)
        low = bar_low(bar)
        open_value = bar_open(bar)
        close = bar_close(bar)
        volume = bar_volume(bar)

        if high <= 0 or low <= 0 or volume <= 0:
            continue
        if high < low:
            high, low = low, high

        open_value = min(max(open_value, low), high)
        close = min(max(close, low), high)

        body_low = min(open_value, close)
        body_high = max(open_value, close)
        upper_wick_low = body_high
        upper_wick_high = high
        lower_wick_low = low
        lower_wick_high = body_low

        body_width = max(0.0, body_high - body_low)
        upper_wick_width = max(0.0, upper_wick_high - upper_wick_low)
        lower_wick_width = max(0.0, lower_wick_high - lower_wick_low)

        body_volume = volume * FRVP_BODY_VOLUME_SHARE
        upper_volume = volume * FRVP_UPPER_WICK_VOLUME_SHARE
        lower_volume = volume * FRVP_LOWER_WICK_VOLUME_SHARE

        if upper_wick_width <= 1e-9:
            body_volume += upper_volume
            upper_volume = 0.0
        if lower_wick_width <= 1e-9:
            body_volume += lower_volume
            lower_volume = 0.0

        _add_volume_range(body_low, body_high, body_volume)
        _add_volume_range(upper_wick_low, upper_wick_high, upper_volume)
        _add_volume_range(lower_wick_low, lower_wick_high, lower_volume)

    if not any(volume_by_index):
        return None

    total_volume = sum(volume_by_index)
    poc_index = max(range(rows), key=lambda idx: volume_by_index[idx])
    target_volume = total_volume * value_area_pct

    included_indexes = {poc_index}
    included_volume = volume_by_index[poc_index]
    lower_index = poc_index - 1
    upper_index = poc_index + 1

    while included_volume < target_volume and (lower_index >= 0 or upper_index < rows):
        lower_volume = volume_by_index[lower_index] if lower_index >= 0 else -1
        upper_volume = volume_by_index[upper_index] if upper_index < rows else -1
        if upper_volume >= lower_volume:
            included_indexes.add(upper_index)
            included_volume += upper_volume
            upper_index += 1
        else:
            included_indexes.add(lower_index)
            included_volume += lower_volume
            lower_index -= 1

    min_idx = min(included_indexes)
    max_idx = max(included_indexes)

    poc = centers[poc_index]
    val = edges[min_idx]
    vah = edges[max_idx + 1]

    volume_by_price = {
        centers[idx]: volume_by_index[idx]
        for idx in range(rows)
        if volume_by_index[idx] > 0
    }

    volume_below_val = sum(volume_by_index[idx] for idx in range(rows) if centers[idx] < val)
    volume_inside_value = sum(volume_by_index[idx] for idx in range(rows) if val <= centers[idx] <= vah)
    volume_above_vah = sum(volume_by_index[idx] for idx in range(rows) if centers[idx] > vah)

    return {
        "volume_by_price": volume_by_price,
        "total_volume": total_volume,
        "poc": round(poc, 4),
        "val": round(val, 4),
        "vah": round(vah, 4),
        "profile_low": round(profile_low_raw, 4),
        "profile_high": round(profile_high_raw, 4),
        "volume_below_val_pct": volume_below_val / total_volume if total_volume > 0 else 0.0,
        "volume_inside_value_pct": volume_inside_value / total_volume if total_volume > 0 else 0.0,
        "volume_above_vah_pct": volume_above_vah / total_volume if total_volume > 0 else 0.0,
    }


def _empty_upper_fight_zone() -> dict[str, Optional[float]]:
    return {
        "low": None,
        "high": None,
        "volume": None,
        "total_volume": None,
        "upper_fight_zone_low": None,
        "upper_fight_zone_high": None,
        "upper_fight_zone_volume": None,
        "upper_fight_zone_volume_pct": None,
        "upper_fight_zone_width_pct": None,
    }


def _build_upper_fight_zone_result(
    low: Optional[float],
    high: Optional[float],
    volume: Optional[float],
    total_volume: Optional[float],
) -> dict[str, Optional[float]]:
    low = safe_float(low, None)
    high = safe_float(high, None)
    volume = safe_float(volume, None)
    total_volume = safe_float(total_volume, None)

    if low is None or high is None or low <= 0 or high <= 0:
        return _empty_upper_fight_zone()

    if high < low:
        low, high = high, low

    volume_pct = None
    if volume is not None and total_volume is not None and total_volume > 0:
        volume_pct = volume / total_volume

    width_pct = (high - low) / low if low > 0 else None

    return {
        "low": low,
        "high": high,
        "volume": volume,
        "total_volume": total_volume,
        "upper_fight_zone_low": low,
        "upper_fight_zone_high": high,
        "upper_fight_zone_volume": volume,
        "upper_fight_zone_volume_pct": volume_pct,
        "upper_fight_zone_width_pct": width_pct,
    }


def _smooth_values(values: list[float], radius: int = 1) -> list[float]:
    if not values:
        return []
    result: list[float] = []
    for idx in range(len(values)):
        start = max(0, idx - radius)
        end = min(len(values), idx + radius + 1)
        subset = values[start:end]
        result.append(sum(subset) / len(subset))
    return result


def _find_contiguous_zone(
    prices: list[float],
    volumes: list[float],
    start_index: int,
    threshold: float,
    max_gap_bins: int = 1,
) -> Optional[tuple[int, int, float]]:
    """Find first contiguous high-volume zone starting at/after start_index."""
    current_start = None
    current_end = None
    current_volume = 0.0
    gap_count = 0

    for idx in range(start_index, len(prices)):
        is_high = volumes[idx] >= threshold
        if is_high:
            if current_start is None:
                current_start = idx
                current_volume = 0.0
            current_end = idx
            current_volume += volumes[idx]
            gap_count = 0
        elif current_start is not None:
            if gap_count < max_gap_bins:
                current_end = idx
                current_volume += volumes[idx]
                gap_count += 1
            else:
                break

    if current_start is None or current_end is None:
        return None

    # Avoid treating one isolated row as a real fight unless it has exceptional volume.
    row_count = current_end - current_start + 1
    if row_count < 2 and current_volume < threshold * 1.75:
        return None

    return current_start, current_end, current_volume


def _renewed_volume_fight_zone_above_vah(
    profile: dict[str, Any],
) -> dict[str, Optional[float]]:
    """Detect the real upper seller/buyer fight zone using volume behavior.

    User-defined behavior:
      fight zone = after volume has already reduced/dried up, volume becomes
      high again at/above a price area, showing renewed seller/buyer conflict.

    Therefore, a far upper wick/tail is NOT automatically a fight zone. If the
    volume simply fades above VAH and never expands again, the required upper
    line should stop at the volume-drop boundary, not at the spike high.
    """
    volume_by_price: dict[float, float] = profile["volume_by_price"]
    vah = safe_float(profile.get("vah"), None)
    total_volume = safe_float(profile.get("total_volume"), 0.0) or 0.0
    profile_high = safe_float(profile.get("profile_high"), None)

    if vah is None or vah <= 0 or profile_high is None or total_volume <= 0:
        return _empty_upper_fight_zone()

    above_prices = [price for price in sorted(volume_by_price) if vah < price <= profile_high]
    if not above_prices:
        return _empty_upper_fight_zone()

    raw_volumes = [safe_float(volume_by_price.get(price), 0.0) or 0.0 for price in above_prices]
    smoothed = _smooth_values(raw_volumes, radius=1)
    above_total = sum(raw_volumes)

    if above_total / total_volume < UPPER_FIGHT_MIN_ABOVE_VAH_VOLUME_PCT:
        return _empty_upper_fight_zone()

    nonzero = [v for v in smoothed if v > 0]
    if not nonzero:
        return _empty_upper_fight_zone()

    # The initial above-VAH area is the first push out of value. Use the first
    # 20% of rows above VAH, capped, to define what "active" volume looked like
    # before any drying-up phase.
    initial_window_size = max(3, min(10, max(3, len(smoothed) // 5)))
    initial_peak = max(smoothed[:initial_window_size])
    median_above = median(nonzero)
    max_above = max(nonzero)

    if initial_peak <= 0:
        return _empty_upper_fight_zone()

    # A dry-up is a real contraction from the initial active zone. Require two
    # consecutive rows under the dry threshold to reduce noise.
    dry_threshold = max(initial_peak * 0.42, median_above * 0.80)
    dry_start_idx = None
    consecutive_dry = 0

    for idx, value in enumerate(smoothed):
        if value <= dry_threshold:
            consecutive_dry += 1
            if consecutive_dry >= 2:
                dry_start_idx = idx - consecutive_dry + 1
                break
        else:
            consecutive_dry = 0

    # If volume never really dries, the whole above-VAH area is a continuous
    # contested zone. Use the non-tail cumulative high, not the absolute spike.
    if dry_start_idx is None:
        target = above_total * UPPER_FIGHT_ABOVE_VAH_COVERAGE_PCT
        cumulative = 0.0
        high_idx = 0
        for idx, vol in enumerate(raw_volumes):
            cumulative += vol
            high_idx = idx
            if cumulative >= target:
                break
        return _build_upper_fight_zone_result(
            low=above_prices[0],
            high=above_prices[high_idx],
            volume=sum(raw_volumes[: high_idx + 1]),
            total_volume=total_volume,
        )

    # Boundary where active above-VAH volume dried. This is the line that should
    # be cleared if no renewed fight appears above it.
    boundary_idx = max(0, dry_start_idx - 1)
    volume_drop_boundary = above_prices[boundary_idx]
    boundary_volume = sum(raw_volumes[: boundary_idx + 1])

    # A renewed fight zone must happen AFTER the dry-up, and must show high
    # volume again relative to both the dry-up and the initial active volume.
    renewed_threshold = max(
        initial_peak * 0.58,
        median_above * 1.40,
        max_above * 0.35,
    )

    # Give the dry-up at least two rows before looking for renewed conflict.
    renewed_start_search = min(len(above_prices), dry_start_idx + 2)
    renewed_zone = _find_contiguous_zone(
        prices=above_prices,
        volumes=smoothed,
        start_index=renewed_start_search,
        threshold=renewed_threshold,
        max_gap_bins=1,
    )

    if renewed_zone is None:
        # PAVS-style behavior: volume dries above the upper boundary and does
        # not become high again. Do NOT use the upper spike/tail as fight zone.
        return _build_upper_fight_zone_result(
            low=above_prices[0],
            high=volume_drop_boundary,
            volume=boundary_volume,
            total_volume=total_volume,
        )

    renewed_start_idx, renewed_end_idx, renewed_volume_smoothed = renewed_zone

    # When a renewed fight exists, require clearing the entire renewed conflict
    # shelf. Start low at the first above-VAH active area, but high comes from
    # the renewed zone.
    zone_volume = sum(raw_volumes[: boundary_idx + 1]) + sum(raw_volumes[renewed_start_idx : renewed_end_idx + 1])
    return _build_upper_fight_zone_result(
        low=above_prices[0],
        high=above_prices[renewed_end_idx],
        volume=zone_volume,
        total_volume=total_volume,
    )


def _repeated_rejection_zone_above_vah(
    profile: dict[str, Any],
    profile_bars: list[Any],
    current_zone_high: Optional[float],
) -> Optional[dict[str, Optional[float]]]:
    """Optional price-action confirmation for an already renewed-volume zone.

    Repeated highs are only allowed to extend the zone when they are near the
    volume-defined upper boundary. This prevents a single far-away wick from
    turning into a required fight-zone high.
    """
    if not profile_bars or current_zone_high is None:
        return None

    vah = profile["vah"]
    total_volume = profile["total_volume"]
    avg_segment_volume = sum(bar_volume(b) for b in profile_bars) / len(profile_bars)
    bucket_size = max(FRVP_TICK_SIZE, vah * UPPER_FIGHT_REPEATED_HIGH_BUCKET_PCT)
    max_allowed_high = current_zone_high * 1.08

    buckets: dict[int, dict[str, float]] = {}
    for bar in profile_bars:
        high = bar_high(bar)
        close = bar_close(bar)
        if high <= vah * (1 + LEVEL_TOLERANCE_PCT):
            continue
        if high > max_allowed_high:
            continue

        stats = candle_stats(bar)
        volume = bar_volume(bar)
        meaningful_volume = volume >= avg_segment_volume * UPPER_FIGHT_REJECTION_MIN_VOLUME_TO_SEGMENT_AVG
        rejection_like = stats["upper_wick_share"] >= UPPER_FIGHT_REJECTION_MIN_UPPER_WICK_SHARE or close < high * 0.985
        if not (meaningful_volume or rejection_like):
            continue

        bucket = int(round(high / bucket_size))
        item = buckets.setdefault(bucket, {"touches": 0.0, "volume": 0.0, "high": 0.0, "low": high})
        item["touches"] += 1.0
        item["volume"] += volume
        item["high"] = max(item["high"], high)
        item["low"] = min(item["low"], high)

    valid_buckets = [item for item in buckets.values() if item["touches"] >= UPPER_FIGHT_REPEATED_HIGH_MIN_TOUCHES]
    if not valid_buckets:
        return None

    chosen = max(valid_buckets, key=lambda item: item["high"])
    return {
        "low": max(vah + FRVP_TICK_SIZE, chosen["low"] - bucket_size),
        "high": chosen["high"],
        "volume": chosen["volume"],
        "total_volume": total_volume,
    }


def find_upper_fight_zone(
    profile: dict[str, Any],
    profile_bars: Optional[list[Any]] = None,
) -> dict[str, Optional[float]]:
    """Detect the upper line using renewed-volume fight-zone behavior.

    v10 definition:
      - First find the above-VAH volume drop boundary.
      - Only extend beyond that boundary if volume gets high again after the
        dry-up, meaning a true renewed fight zone exists.
      - A far upper tail with fading volume is not a fight zone.
    """
    volume_zone = _renewed_volume_fight_zone_above_vah(profile)
    current_high = safe_float(volume_zone.get("upper_fight_zone_high"), None)

    rejection_zone = _repeated_rejection_zone_above_vah(
        profile=profile,
        profile_bars=profile_bars or [],
        current_zone_high=current_high,
    )

    if rejection_zone is None:
        return volume_zone

    # Only merge if repeated rejection is reasonably near the volume-defined
    # boundary. This is an extension of a real zone, not a tail capture.
    return _build_upper_fight_zone_result(
        low=min(
            safe_float(volume_zone.get("upper_fight_zone_low"), None) or rejection_zone["low"],
            safe_float(rejection_zone.get("low"), None) or volume_zone["upper_fight_zone_low"],
        ),
        high=max(
            safe_float(volume_zone.get("upper_fight_zone_high"), None) or rejection_zone["high"],
            safe_float(rejection_zone.get("high"), None) or volume_zone["upper_fight_zone_high"],
        ),
        volume=(safe_float(volume_zone.get("upper_fight_zone_volume"), 0.0) or 0.0)
        + (safe_float(rejection_zone.get("volume"), 0.0) or 0.0),
        total_volume=safe_float(volume_zone.get("total_volume"), None) or safe_float(rejection_zone.get("total_volume"), None),
    )


def scan_later_breakout_debug(
    all_bars: list[Any],
    profile_end_bar: Any,
    vah: float,
    fight_zone_high: Optional[float],
) -> dict[str, Any]:
    effective_line = max(vah, fight_zone_high or vah)
    future_bars = [
        bar for bar in all_bars
        if (
            bar.bar_time.date() == profile_end_bar.bar_time.date()
            and bar.bar_time > profile_end_bar.bar_time
            and bar.bar_time.time() <= MARKET_CLOSE
        )
    ][:ENTRY_SCAN_MAX_BARS_AFTER_PROFILE]

    first_close_above_vah = None
    first_close_above_fight = None
    first_confirmed = None

    same_day_before: list[Any] = [
        bar for bar in all_bars
        if bar.bar_time.date() == profile_end_bar.bar_time.date()
        and bar.bar_time <= profile_end_bar.bar_time
    ]

    for bar in future_bars:
        close = bar_close(bar)
        if first_close_above_vah is None and close > vah * (1 + LEVEL_TOLERANCE_PCT):
            first_close_above_vah = bar
        if first_close_above_fight is None and close > effective_line * (1 + LEVEL_TOLERANCE_PCT):
            first_close_above_fight = bar

        prior_bars = same_day_before[-ENTRY_VOLUME_AVG_LOOKBACK:]
        prior_for_max = same_day_before[-ENTRY_VOLUME_MAX_LOOKBACK:]
        previous_bar = same_day_before[-1] if same_day_before else None

        recent_avg_volume = sum(bar_volume(b) for b in prior_bars) / len(prior_bars) if prior_bars else None
        recent_max_volume = max((bar_volume(b) for b in prior_for_max), default=None)
        previous_volume = bar_volume(previous_bar) if previous_bar is not None else None

        current_volume = bar_volume(bar)
        vol_vs_avg = ratio(current_volume, recent_avg_volume)
        vol_vs_max = ratio(current_volume, recent_max_volume)
        vol_vs_previous = ratio(current_volume, previous_volume)
        stats = candle_stats(bar)

        strict_volume_pass = bool(
            (vol_vs_avg or 0) >= ENTRY_MIN_VOLUME_VS_RECENT_AVG
            and (vol_vs_max or 0) >= ENTRY_MIN_VOLUME_VS_RECENT_MAX
        )
        decisive_first_clear_pass = bool(
            (vol_vs_avg or 0) >= ENTRY_MIN_DECISIVE_VOLUME_VS_RECENT_AVG
            and (vol_vs_previous or 0) >= ENTRY_MIN_DECISIVE_VOLUME_VS_PREVIOUS
            and close >= effective_line * (1 + ENTRY_MIN_DECISIVE_CLOSE_ABOVE_LINE_PCT)
        )

        if (
            close > effective_line * (1 + LEVEL_TOLERANCE_PCT)
            and (strict_volume_pass or decisive_first_clear_pass)
            and stats["close_position"] >= ENTRY_MIN_CLOSE_POSITION
            and stats["upper_wick_share"] <= ENTRY_MAX_UPPER_WICK_SHARE
        ):
            first_confirmed = {
                "bar": bar,
                "volume_vs_recent_avg": vol_vs_avg,
                "volume_vs_recent_max": vol_vs_max,
            }
            break

        same_day_before.append(bar)

    return {
        "first_close_above_vah_time": getattr(first_close_above_vah, "bar_time", None),
        "first_close_above_vah_close": bar_close(first_close_above_vah) if first_close_above_vah else None,
        "first_close_above_fight_zone_time": getattr(first_close_above_fight, "bar_time", None),
        "first_close_above_fight_zone_close": bar_close(first_close_above_fight) if first_close_above_fight else None,
        "first_confirmed_breakout_time": getattr(first_confirmed["bar"], "bar_time", None) if first_confirmed else None,
        "first_confirmed_breakout_close": bar_close(first_confirmed["bar"]) if first_confirmed else None,
        "first_confirmed_breakout_volume": bar_volume(first_confirmed["bar"]) if first_confirmed else None,
        "first_confirmed_breakout_volume_vs_recent_avg": first_confirmed["volume_vs_recent_avg"] if first_confirmed else None,
        "first_confirmed_breakout_volume_vs_recent_max": first_confirmed["volume_vs_recent_max"] if first_confirmed else None,
    }



def build_movement_diagnostics(segment_bars: list[Any]) -> dict[str, Any]:
    """Return diagnostic features that help decide movement yes/no.

    These values are exported only for review. They deliberately do not filter
    rows yet. After reviewing known good profiles vs no-movement examples, use
    these columns to add a real movement-quality gate.
    """
    if not segment_bars:
        return {
            "movement_median_volume": 0.0,
            "movement_volume_per_minute": 0.0,
            "movement_top_3_volume_pct": 0.0,
            "movement_bars_volume_over_10k": 0,
            "movement_bars_volume_over_25k": 0,
            "movement_bars_volume_over_50k": 0,
            "movement_meaningful_range_bar_count": 0,
            "movement_large_range_bar_count": 0,
            "movement_zero_range_bar_count": 0,
            "movement_flat_bar_count": 0,
            "movement_green_bar_count": 0,
            "movement_red_bar_count": 0,
            "movement_green_volume_pct": None,
            "movement_red_volume_pct": None,
            "movement_range_per_100k_volume": None,
            "movement_abs_close_change_per_100k_volume": None,
            "movement_high_from_start_pct": None,
            "movement_low_from_start_pct": None,
            "movement_close_near_high_bar_count": 0,
            "movement_close_near_low_bar_count": 0,
            "movement_quality_score": 0.0,
            "movement_quality_notes": "empty_segment",
            "movement_is_valid": False,
            "movement_invalid_reasons": "empty_segment",
        }

    volumes = [bar_volume(bar) for bar in segment_bars]
    total_volume = sum(volumes)
    start_open = bar_open(segment_bars[0])
    end_close = bar_close(segment_bars[-1])
    highs = [bar_high(bar) for bar in segment_bars]
    lows = [bar_low(bar) for bar in segment_bars]
    movement_high = max(highs)
    movement_low = min(lows)
    movement_range_abs = movement_high - movement_low
    movement_close_change_abs = abs(end_close - start_open)
    duration_minutes = max(1.0, minutes_between(segment_bars[0].bar_time, segment_bars[-1].bar_time) + 1.0)

    meaningful_range_bar_count = 0
    large_range_bar_count = 0
    zero_range_bar_count = 0
    flat_bar_count = 0
    green_bar_count = 0
    red_bar_count = 0
    green_volume = 0.0
    red_volume = 0.0
    close_near_high_count = 0
    close_near_low_count = 0

    for bar in segment_bars:
        open_value = bar_open(bar)
        high = bar_high(bar)
        low = bar_low(bar)
        close = bar_close(bar)
        volume = bar_volume(bar)
        bar_range = high - low
        range_pct = bar_range / max(0.000001, open_value)
        stats = candle_stats(bar)

        if bar_range <= 0.000001:
            zero_range_bar_count += 1
        if range_pct < 0.002:
            flat_bar_count += 1
        if range_pct >= 0.01:
            meaningful_range_bar_count += 1
        if range_pct >= 0.03:
            large_range_bar_count += 1
        if close > open_value:
            green_bar_count += 1
            green_volume += volume
        elif close < open_value:
            red_bar_count += 1
            red_volume += volume
        if stats["close_position"] >= 0.70:
            close_near_high_count += 1
        if stats["close_position"] <= 0.30:
            close_near_low_count += 1

    top_3_volume = sum(sorted(volumes, reverse=True)[:3])
    volume_denominator = total_volume / 100000.0 if total_volume > 0 else None
    range_per_100k = movement_range_abs / volume_denominator if volume_denominator and volume_denominator > 0 else None
    close_change_per_100k = movement_close_change_abs / volume_denominator if volume_denominator and volume_denominator > 0 else None

    notes: list[str] = []
    score = 0.0

    movement_range_pct = movement_range_abs / max(0.000001, start_open)
    close_change_pct_abs = abs((end_close - start_open) / max(0.000001, start_open))

    if movement_range_pct >= 0.20:
        score += 2.0
    elif movement_range_pct >= 0.10:
        score += 1.25
    elif movement_range_pct >= 0.05:
        score += 0.50
    else:
        notes.append("weak_range")

    if close_change_pct_abs >= 0.10:
        score += 1.0
    elif close_change_pct_abs < 0.02:
        notes.append("weak_close_displacement")

    if total_volume >= 500000:
        score += 1.50
    elif total_volume >= 250000:
        score += 1.00
    elif total_volume >= 100000:
        score += 0.50
    else:
        notes.append("thin_total_volume")

    if sum(1 for volume in volumes if volume >= 10000) >= 3:
        score += 1.0
    else:
        notes.append("few_10k_volume_bars")

    if meaningful_range_bar_count >= 5:
        score += 1.0
    elif meaningful_range_bar_count < 2:
        notes.append("few_meaningful_range_bars")

    if flat_bar_count / max(1, len(segment_bars)) >= 0.35:
        notes.append("many_flat_bars")
        score -= 0.75

    if zero_range_bar_count / max(1, len(segment_bars)) >= 0.20:
        notes.append("many_zero_range_bars")
        score -= 0.75

    top_3_pct = top_3_volume / total_volume if total_volume > 0 else 0.0
    if top_3_pct >= 0.80 and len(segment_bars) > 6:
        notes.append("volume_too_concentrated")
        score -= 0.50
    elif top_3_pct <= 0.65:
        score += 0.35

    if range_per_100k is not None:
        # This is price movement created per 100k shares. Very tiny values can
        # expose volume printing without actual movement.
        if range_per_100k <= max(0.0025, start_open * 0.002):
            notes.append("low_price_volume_efficiency")
        else:
            score += 0.35

    if close_near_high_count > close_near_low_count:
        score += 0.25

    invalid_reasons: list[str] = []
    # Initial movement/no-movement gate derived from the diagnostic run.
    # It is intentionally conservative: it removes thin/choppy profiles like CAST
    # while preserving known good cases such as AKAN, SDOT, PAVS and HKIT.
    if movement_range_pct < 0.08:
        invalid_reasons.append("range_lt_8pct")
    if total_volume < 100000:
        invalid_reasons.append("volume_lt_100k")
    if sum(1 for volume in volumes if volume >= 10000) < 3:
        invalid_reasons.append("less_than_3_10k_volume_bars")
    if meaningful_range_bar_count < 5:
        invalid_reasons.append("less_than_5_meaningful_range_bars")
    if flat_bar_count / max(1, len(segment_bars)) >= 0.65:
        invalid_reasons.append("flat_bar_pct_gte_65")
    if zero_range_bar_count / max(1, len(segment_bars)) >= 0.55:
        invalid_reasons.append("zero_range_bar_pct_gte_55")
    if max(0.0, score) < 3.0:
        invalid_reasons.append("movement_quality_score_lt_3")

    movement_is_valid = not invalid_reasons

    return {
        "movement_median_volume": median([v for v in volumes if v > 0]) if any(v > 0 for v in volumes) else 0.0,
        "movement_volume_per_minute": total_volume / duration_minutes,
        "movement_top_3_volume_pct": top_3_pct,
        "movement_bars_volume_over_10k": sum(1 for volume in volumes if volume >= 10000),
        "movement_bars_volume_over_25k": sum(1 for volume in volumes if volume >= 25000),
        "movement_bars_volume_over_50k": sum(1 for volume in volumes if volume >= 50000),
        "movement_meaningful_range_bar_count": meaningful_range_bar_count,
        "movement_large_range_bar_count": large_range_bar_count,
        "movement_zero_range_bar_count": zero_range_bar_count,
        "movement_flat_bar_count": flat_bar_count,
        "movement_green_bar_count": green_bar_count,
        "movement_red_bar_count": red_bar_count,
        "movement_green_volume_pct": green_volume / total_volume if total_volume > 0 else None,
        "movement_red_volume_pct": red_volume / total_volume if total_volume > 0 else None,
        "movement_range_per_100k_volume": range_per_100k,
        "movement_abs_close_change_per_100k_volume": close_change_per_100k,
        "movement_high_from_start_pct": pct_change(start_open, movement_high),
        "movement_low_from_start_pct": pct_change(start_open, movement_low),
        "movement_close_near_high_bar_count": close_near_high_count,
        "movement_close_near_low_bar_count": close_near_low_count,
        "movement_quality_score": round(max(0.0, score), 3),
        "movement_quality_notes": ";".join(notes),
        "movement_is_valid": movement_is_valid,
        "movement_invalid_reasons": ";".join(invalid_reasons),
    }


def build_quality_score_and_notes(
    segment_bars: list[Any],
    profile: dict[str, Any],
    fight_zone: dict[str, Optional[float]],
) -> tuple[float, str]:
    notes: list[str] = []
    score = 0.0

    start_open = bar_open(segment_bars[0])
    movement_range_pct = (max(bar_high(b) for b in segment_bars) - min(bar_low(b) for b in segment_bars)) / max(0.000001, start_open)
    total_volume = sum(bar_volume(b) for b in segment_bars)
    max_volume = max(bar_volume(b) for b in segment_bars)
    avg_volume = total_volume / len(segment_bars)

    if len(segment_bars) >= 5:
        score += 1.0
    else:
        notes.append("short_impulse")

    if movement_range_pct >= 0.10:
        score += 1.5
    elif movement_range_pct >= 0.05:
        score += 1.0
    else:
        notes.append("small_range")

    if total_volume >= 500_000:
        score += 1.5
    elif total_volume >= 100_000:
        score += 1.0
    else:
        notes.append("low_total_volume")

    if max_volume >= avg_volume * 2.5:
        notes.append("concentrated_volume_spike")
    else:
        score += 0.5

    if profile["volume_inside_value_pct"] >= 0.65:
        score += 0.5

    if fight_zone.get("upper_fight_zone_high") is not None:
        score += 0.5
    else:
        notes.append("no_upper_fight_zone_detected")

    return (round(score, 3), ";".join(notes))


def build_movement_row(
    data: dict[str, Any],
    all_bars: list[Any],
    session_bars: list[Any],
    segment: dict[str, Any],
    movement_id: int,
    profile_role: str = "volume_campaign",
) -> Optional[MovementProfileRow]:
    start_index = segment["start_index"]
    end_index = segment["end_index"]
    cluster_start_index = segment["cluster_start_index"]
    cluster_end_index = segment["cluster_end_index"]
    segment_bars = session_bars[start_index:end_index + 1]
    cluster_bars = session_bars[cluster_start_index:cluster_end_index + 1]

    profile = calculate_volume_profile(segment_bars)
    if profile is None:
        return None

    fight_zone = find_upper_fight_zone(profile, segment_bars)
    later_debug = scan_later_breakout_debug(
        all_bars=all_bars,
        profile_end_bar=segment_bars[-1],
        vah=profile["vah"],
        fight_zone_high=fight_zone.get("upper_fight_zone_high"),
    )
    quality_score, quality_notes = build_quality_score_and_notes(segment_bars, profile, fight_zone)
    movement_diagnostics = build_movement_diagnostics(segment_bars)

    highs = [bar_high(bar) for bar in segment_bars]
    lows = [bar_low(bar) for bar in segment_bars]
    volumes = [bar_volume(bar) for bar in segment_bars]
    high_bar = max(segment_bars, key=lambda b: bar_high(b))
    low_bar = min(segment_bars, key=lambda b: bar_low(b))
    max_volume_bar = max(segment_bars, key=lambda b: bar_volume(b))
    volume_after_high = sum(bar_volume(bar) for bar in segment_bars if bar.bar_time > high_bar.bar_time)
    total_volume = sum(volumes)
    start_open = bar_open(segment_bars[0])
    movement_high = max(highs)
    movement_low = min(lows)

    cluster_total_volume = sum(bar_volume(bar) for bar in cluster_bars)
    cluster_avg_volume = cluster_total_volume / len(cluster_bars) if cluster_bars else 0.0
    high_volume_bar_count = sum(1 for volume in volumes if volume >= segment["high_volume_threshold"])

    day_stock = data.get("day_timeframe_stock")
    is_positive = bool(getattr(day_stock, "is_positive", False))
    symbol = getattr(segment_bars[0], "symbol", "")

    return MovementProfileRow(
        symbol=symbol,
        trade_date=get_trade_date(data, all_bars),
        is_positive=is_positive,
        movement_id=movement_id,
        profile_role=profile_role,
        session_type=segment["session_type"],
        movement_type="volume_campaign",
        movement_start_time=segment_bars[0].bar_time,
        movement_end_time=segment_bars[-1].bar_time,
        movement_duration_minutes=minutes_between(segment_bars[0].bar_time, segment_bars[-1].bar_time),
        movement_bar_count=len(segment_bars),
        movement_start_open=start_open,
        movement_end_close=bar_close(segment_bars[-1]),
        movement_low=movement_low,
        movement_low_time=low_bar.bar_time,
        movement_high=movement_high,
        movement_high_time=high_bar.bar_time,
        movement_range_pct=(movement_high - movement_low) / max(0.000001, start_open),
        movement_gain_from_start_open_pct=pct_change(start_open, bar_close(segment_bars[-1])) or 0.0,
        movement_gain_from_low_to_high_pct=pct_change(movement_low, movement_high) or 0.0,
        movement_total_volume=total_volume,
        movement_avg_volume=total_volume / len(segment_bars),
        movement_max_volume=bar_volume(max_volume_bar),
        movement_max_volume_time=max_volume_bar.bar_time,
        movement_high_volume_bar_count=high_volume_bar_count,
        movement_volume_after_high_pct=volume_after_high / total_volume if total_volume > 0 else None,
        movement_median_volume=movement_diagnostics["movement_median_volume"],
        movement_volume_per_minute=movement_diagnostics["movement_volume_per_minute"],
        movement_top_3_volume_pct=movement_diagnostics["movement_top_3_volume_pct"],
        movement_bars_volume_over_10k=movement_diagnostics["movement_bars_volume_over_10k"],
        movement_bars_volume_over_25k=movement_diagnostics["movement_bars_volume_over_25k"],
        movement_bars_volume_over_50k=movement_diagnostics["movement_bars_volume_over_50k"],
        movement_meaningful_range_bar_count=movement_diagnostics["movement_meaningful_range_bar_count"],
        movement_large_range_bar_count=movement_diagnostics["movement_large_range_bar_count"],
        movement_zero_range_bar_count=movement_diagnostics["movement_zero_range_bar_count"],
        movement_flat_bar_count=movement_diagnostics["movement_flat_bar_count"],
        movement_green_bar_count=movement_diagnostics["movement_green_bar_count"],
        movement_red_bar_count=movement_diagnostics["movement_red_bar_count"],
        movement_green_volume_pct=movement_diagnostics["movement_green_volume_pct"],
        movement_red_volume_pct=movement_diagnostics["movement_red_volume_pct"],
        movement_range_per_100k_volume=movement_diagnostics["movement_range_per_100k_volume"],
        movement_abs_close_change_per_100k_volume=movement_diagnostics["movement_abs_close_change_per_100k_volume"],
        movement_high_from_start_pct=movement_diagnostics["movement_high_from_start_pct"],
        movement_low_from_start_pct=movement_diagnostics["movement_low_from_start_pct"],
        movement_close_near_high_bar_count=movement_diagnostics["movement_close_near_high_bar_count"],
        movement_close_near_low_bar_count=movement_diagnostics["movement_close_near_low_bar_count"],
        movement_quality_score=movement_diagnostics["movement_quality_score"],
        movement_quality_notes=movement_diagnostics["movement_quality_notes"],
        movement_is_valid=movement_diagnostics["movement_is_valid"],
        movement_invalid_reasons=movement_diagnostics["movement_invalid_reasons"],
        impulse_cluster_start_time=cluster_bars[0].bar_time,
        impulse_cluster_end_time=cluster_bars[-1].bar_time,
        impulse_cluster_bar_count=len(cluster_bars),
        impulse_cluster_total_volume=cluster_total_volume,
        impulse_cluster_avg_volume=cluster_avg_volume,
        high_volume_threshold=segment["high_volume_threshold"],
        frvp_value_area_pct=FRVP_VALUE_AREA_PCT,
        frvp_val=profile["val"],
        frvp_poc=profile["poc"],
        frvp_vah=profile["vah"],
        frvp_profile_low=profile["profile_low"],
        frvp_profile_high=profile["profile_high"],
        frvp_total_volume=profile["total_volume"],
        frvp_volume_below_val_pct=profile["volume_below_val_pct"],
        frvp_volume_inside_value_pct=profile["volume_inside_value_pct"],
        frvp_volume_above_vah_pct=profile["volume_above_vah_pct"],
        upper_fight_zone_low=fight_zone.get("upper_fight_zone_low"),
        upper_fight_zone_high=fight_zone.get("upper_fight_zone_high"),
        upper_fight_zone_volume=fight_zone.get("upper_fight_zone_volume"),
        upper_fight_zone_volume_pct=fight_zone.get("upper_fight_zone_volume_pct"),
        upper_fight_zone_width_pct=fight_zone.get("upper_fight_zone_width_pct"),
        first_close_above_vah_time=later_debug["first_close_above_vah_time"],
        first_close_above_vah_close=later_debug["first_close_above_vah_close"],
        first_close_above_fight_zone_time=later_debug["first_close_above_fight_zone_time"],
        first_close_above_fight_zone_close=later_debug["first_close_above_fight_zone_close"],
        first_confirmed_breakout_time=later_debug["first_confirmed_breakout_time"],
        first_confirmed_breakout_close=later_debug["first_confirmed_breakout_close"],
        first_confirmed_breakout_volume=later_debug["first_confirmed_breakout_volume"],
        first_confirmed_breakout_volume_vs_recent_avg=later_debug["first_confirmed_breakout_volume_vs_recent_avg"],
        first_confirmed_breakout_volume_vs_recent_max=later_debug["first_confirmed_breakout_volume_vs_recent_max"],
        profile_quality_score=quality_score,
        profile_quality_notes=quality_notes,
    )


def process_training_file(file_path: str) -> list[MovementProfileRow]:
    data = load_pickle_data(file_path)
    stock = data.get("one_minute_timeframe_stock")
    if stock is None or not hasattr(stock, "bars"):
        return []

    all_bars = sorted(stock.bars, key=lambda b: b.bar_time)
    all_bars = filter_trade_date_bars(data, all_bars)
    if len(all_bars) < 5:
        return []

    rows: list[MovementProfileRow] = []
    movement_id = 1

    # PREMARKET: export only interpretable candidates:
    # 1. full premarket value map,
    # 2. optional core value after an extreme early liquidity shock,
    # 3. first meaningful volume campaign.
    premarket_bars = bars_for_session(all_bars, "premarket")
    premarket_candidates: list[dict[str, Any]] = []
    if len(premarket_bars) >= MIN_SEGMENT_BARS:
        full_pre = make_fixed_segment(
            session_bars=premarket_bars,
            session_type="premarket",
            start_index=0,
            end_index=len(premarket_bars) - 1,
            role="premarket_full",
        )
        if full_pre is not None:
            premarket_candidates.append(full_pre)

        core_after_spike = find_premarket_core_after_early_spike(premarket_bars)
        if core_after_spike is not None:
            premarket_candidates.append(core_after_spike)

        for seg in first_n_campaign_segments(premarket_bars, "premarket", limit=1):
            seg = dict(seg)
            seg["profile_role"] = "premarket_first_volume_campaign"
            premarket_candidates.append(seg)

    # RTH: export first and second meaningful campaigns only. The first one is
    # usually the source profile for later market-FRVP entries; the second helps
    # debug continuation/rebuild examples without flooding the CSV.
    rth_bars = bars_for_session(all_bars, "rth")
    rth_candidates: list[dict[str, Any]] = []
    for idx, seg in enumerate(first_n_campaign_segments(rth_bars, "rth", limit=2), start=1):
        seg = dict(seg)
        seg["profile_role"] = f"rth_volume_campaign_{idx}"
        rth_candidates.append(seg)

    candidates = premarket_candidates + rth_candidates

    # De-dupe identical ranges while preserving role order.
    seen_ranges: set[tuple[str, int, int]] = set()
    for segment in candidates:
        key = (segment["session_type"], segment["start_index"], segment["end_index"])
        if key in seen_ranges:
            continue
        seen_ranges.add(key)
        session_bars = premarket_bars if segment["session_type"] == "premarket" else rth_bars
        row = build_movement_row(
            data=data,
            all_bars=all_bars,
            session_bars=session_bars,
            segment=segment,
            movement_id=movement_id,
            profile_role=segment.get("profile_role", "volume_campaign"),
        )
        if row is not None:
            rows.append(row)
            movement_id += 1

    return rows


def _training_file_symbol_date_key(file_path: str) -> tuple[str, str]:
    stem = os.path.splitext(os.path.basename(file_path))[0]
    parts = stem.split("-", 1)
    if len(parts) != 2:
        return (stem.upper(), "")
    symbol = parts[0].upper()
    trade_date = parts[1][:10]
    if len(trade_date) == 10 and trade_date[4] == "-" and trade_date[7] == "-":
        return (symbol, trade_date)
    return (stem.upper(), "")


def distinct_training_files(file_paths: list[str]) -> list[str]:
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


def dedupe_rows(rows: list[MovementProfileRow]) -> list[MovementProfileRow]:
    seen: set[tuple[str, str, str, datetime.datetime, datetime.datetime]] = set()
    result: list[MovementProfileRow] = []
    for row in rows:
        key = (
            row.symbol,
            row.trade_date,
            row.session_type,
            row.movement_start_time,
            row.movement_end_time,
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result



def _role_priority(profile_role: str) -> float:
    """Manual-review priority for selecting the primary source profile.

    The raw candidates are still useful for debugging, but the default output
    should show the one profile that best represents the previous meaningful
    movement for the later value-breakout setup.
    """
    role = profile_role or ""
    if role == "premarket_core_after_early_spike":
        return 95.0
    if role == "premarket_full":
        return 90.0
    if role == "premarket_first_volume_campaign":
        return 82.0
    if role == "rth_volume_campaign_1":
        return 74.0
    if role == "rth_volume_campaign_2":
        return 62.0
    return 50.0


def _row_has_market_confirmed_breakout(row: MovementProfileRow) -> bool:
    confirmed_time = row.first_confirmed_breakout_time
    return bool(confirmed_time is not None and confirmed_time.time() >= MARKET_OPEN)


def _primary_profile_score(row: MovementProfileRow) -> float:
    """Score candidates for the compact validation CSV.

    Prefer profiles that produce a market-hours confirmed breakout, then prefer
    stable source-profile roles. This avoids the confusing raw output where a
    noisy local RTH profile can sit next to the real premarket/first-movement
    source profile.
    """
    score = _role_priority(row.profile_role)

    if getattr(row, "movement_is_valid", True):
        score += 35.0
    else:
        score -= 80.0

    if _row_has_market_confirmed_breakout(row):
        score += 100.0
    elif row.first_confirmed_breakout_time is not None:
        # Premarket-only confirmations are useful as debug, but should usually
        # not beat a market-hours source profile for this workflow.
        score += 20.0
    else:
        score -= 35.0

    volume_strength = safe_float(row.first_confirmed_breakout_volume_vs_recent_avg, None)
    if volume_strength is not None:
        score += min(10.0, volume_strength)

    # Prefer profiles whose fight zone is not unrealistically huge relative to VAH,
    # but do not over-penalize real high shelves.
    if row.upper_fight_zone_high is not None and row.frvp_vah and row.frvp_vah > 0:
        fight_extension_pct = (row.upper_fight_zone_high - row.frvp_vah) / row.frvp_vah
        if fight_extension_pct > 0.45:
            score -= 25.0
        elif fight_extension_pct > 0.25:
            score -= 10.0

    return score


def select_primary_rows(rows: list[MovementProfileRow]) -> list[MovementProfileRow]:
    """Return one primary FRVP source profile per symbol/day.

    v3 improved the fight-zone values, but the CSV still looked the same because
    it exported every candidate profile. v5 keeps all raw candidates in a
    separate debug file and writes this compact selected set to the main output. It also adds
    movement-quality diagnostics so thin/choppy profiles can be reviewed before filtering.
    """
    grouped: dict[tuple[str, str], list[MovementProfileRow]] = {}
    for row in rows:
        grouped.setdefault((row.symbol, row.trade_date), []).append(row)

    selected: list[MovementProfileRow] = []
    for key in sorted(grouped):
        group = grouped[key]
        # Tie-breaker: higher score first, then earlier confirmed breakout, then
        # earlier movement start for stable reproducibility.
        def _sort_key(row: MovementProfileRow) -> tuple[float, float, float]:
            confirmed_time = row.first_confirmed_breakout_time or datetime.datetime.max
            movement_start = row.movement_start_time or datetime.datetime.max
            return (
                -_primary_profile_score(row),
                confirmed_time.timestamp(),
                movement_start.timestamp(),
            )

        selected.append(sorted(group, key=_sort_key)[0])

    return selected

def write_rows_to_csv(rows: list[MovementProfileRow], output_file_path: str) -> None:
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    rows = dedupe_rows(rows)
    fieldnames = list(MovementProfileRow.__dataclass_fields__.keys())
    with open(output_file_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
    print(f"Wrote {len(rows)} movement-profile rows to {output_file_path}")


def main() -> None:
    raw_files = glob.glob(INPUT_FILES_GLOB)
    files = distinct_training_files(raw_files)
    print(f"Found {len(raw_files)} files, processing {len(files)} distinct files")

    all_rows: list[MovementProfileRow] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_file = {executor.submit(process_training_file, file_path): file_path for file_path in files}
        completed = 0
        for future in concurrent.futures.as_completed(future_to_file):
            file_path = future_to_file[future]
            completed += 1
            try:
                all_rows.extend(future.result())
            except Exception as exc:
                print(f"Failed processing {file_path}: {exc}")
            if completed % 50 == 0:
                print(f"Completed {completed}/{len(files)} files. Rows so far: {len(all_rows)}")

    # Write all raw candidates for debugging, then write the compact primary
    # profile set as the main review file.
    write_rows_to_csv(all_rows, OUTPUT_CANDIDATES_FILE)
    selected_rows = select_primary_rows(dedupe_rows(all_rows))
    write_rows_to_csv(selected_rows, OUTPUT_COMBINED_FILE)

    valid_selected_rows = [
        row for row in selected_rows
        if bool(getattr(row, "movement_is_valid", False))
    ]
    write_rows_to_csv(valid_selected_rows, OUTPUT_VALID_FILE)

    print("Done.")
    print(f"Total movement-profile rows before dedupe: {len(all_rows)}")
    print(f"Selected primary movement-profile rows: {len(selected_rows)}")
    print(f"Valid selected movement-profile rows: {len(valid_selected_rows)}")


if __name__ == "__main__":
    main()
