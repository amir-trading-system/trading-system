import argparse
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd


FIXTURE_DIR = Path(__file__).with_name("fixtures") / "frvp"


def fixture(name: str) -> str:
    """Return an immutable, date-scoped regression fixture path."""
    path = FIXTURE_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"Missing frozen FRVP fixture: {path}. "
            "Run freeze_frvp_validation_fixtures.py only after reviewing "
            "the replacement source export."
        )
    return str(path)


# PARITY_DETECTION_START
VALIDATION_BUILD_ID = 2026100402
POST_ENTRY_MATURE_TREND_TIERS = 2
POST_ENTRY_REQUIRED_CONFIRMATION_SCORE = 5
FAILED_EXPANSION_COMPRESSION_BARS = 20
FAILED_EXPANSION_REJECTION_WINDOW_BARS = 3
MINIMUM_FAILED_EXPANSION_OVERLAP_PCT = 70.0
MINIMUM_FAILED_COMPRESSION_VOLUME_RATIO = 1.50
MINIMUM_FAILED_BREAKOUT_VOLUME_RATIO = 2.0
MAXIMUM_FAILED_BREAKOUT_CLOSE_LOCATION_PCT = 65.0
MINIMUM_FAILED_BREAKOUT_UPPER_WICK_PCT = 30.0
MINIMUM_FAILED_REJECTION_BODY_PCT = 60.0
MAXIMUM_FAILED_REJECTION_CLOSE_LOCATION_PCT = 25.0
MINIMUM_FAILED_REJECTION_VOLUME_RATIO = 0.60


def mature_post_entry_veto(
    confirmed_tiers: int,
    last_accepted_entry_tiers: int | None,
    entry_confirmation_score: int,
) -> bool:
    """Reject weak continuation signals after two newer trend tiers."""
    return (
        last_accepted_entry_tiers is not None
        and confirmed_tiers - last_accepted_entry_tiers
        >= POST_ENTRY_MATURE_TREND_TIERS
        and entry_confirmation_score
        < POST_ENTRY_REQUIRED_CONFIRMATION_SCORE
    )


# PARITY_RULE: state_model
@dataclass
class Candidate:
    break_index: int
    support_start: int
    support_end: int
    support_low: float
    support_high: float
    support_touches: int
    prior_advance_pct: float
    source: str
    support_buyer_defense: bool = True
    rejection_indices: list[int] = field(default_factory=list)
    rejection_volume: float = 0.0
    rejection_body_pct: float = 0.0
    rejection_high: float = np.nan
    wick_confirmed_rejections: int = 0
    accepted_bullish_closes_above_support: int = 0
    accepted_closes_above_resistance_contact: int = 0
    failed_expansion_origin: bool = False
    failed_expansion_high: float = np.nan
    expired: bool = False


def detect(
    path: str,
    date: str,
    debug_clocks: set[str] | None = None,
    resistance_acceptance_guard: bool = True,
    data_override: pd.DataFrame | None = None,
):
    data = (
        data_override.copy()
        if data_override is not None
        else pd.read_csv(path)
    )
    data["time"] = pd.to_datetime(data["time"])
    data = data[data.time.dt.strftime("%Y-%m-%d") == date].sort_values("time").reset_index(drop=True)
    if data.empty:
        return pd.DataFrame()

    time = data.time.to_numpy()
    open_ = data.open.to_numpy(float)
    high = data.high.to_numpy(float)
    low = data.low.to_numpy(float)
    close = data.close.to_numpy(float)
    volume = data.Volume.to_numpy(float)
    volume_ma = data["Volume MA"].to_numpy(float)
    long_volume_ma = pd.Series(volume).rolling(60, min_periods=60).mean().to_numpy()
    prior_three_volume = pd.Series(volume).shift(1).rolling(3, min_periods=3).mean().to_numpy()
    candle_range = high - low
    prior_three_range = pd.Series(candle_range).shift(1).rolling(3, min_periods=3).mean().to_numpy()
    ema9 = pd.Series(close).ewm(span=9, adjust=False).mean().to_numpy()
    ema20 = pd.Series(close).ewm(span=20, adjust=False).mean().to_numpy()
    vwap = pd.to_numeric(data["VWAP"], errors="coerce").to_numpy(float)
    body_floor = np.minimum(open_, close)

    support_lookback = 120
    prior_advance_lookback = 120
    support_tolerance = 0.035
    signal_clear_tolerance = 0.04
    break_pct = 0.0
    resistance_touch_tolerance = 0.04
    min_prior_advance = 8.0
    max_resistance_gap = 720
    maximum_setup_bars = 720
    min_breakout_pct = 0.0
    min_close_location = 50.0
    min_volume_expansion = 1.15
    min_body_expansion = 2.0
    min_quiet_resistance_bars = 2
    support_trend_touch_tolerance = 0.001
    entry_ema_alignment_tolerance = 0.0015

    active: list[Candidate] = []
    known_levels: list[Candidate] = []
    signals = []
    setup_records = []
    failed_expansion_records = []
    last_signal_index = None
    last_signal_resistance = None
    last_signal_support_low = None
    last_signal_support_high = None
    last_signal_resistance_stage_bars = None
    last_accepted_signal_index = None
    last_accepted_signal_support_high = None
    last_accepted_signal_resistance_stage_bars = None
    accepted_signal_support_lows: list[float] = []
    lowest_since_signal = np.inf
    last_nested_evidence_index = None
    last_nested_cleared_resistance = np.nan
    last_nested_blocking_resistance = np.nan
    last_nested_evidence_score = np.nan
    last_nested_direct_entry_index = None
    last_nested_direct_entry_lower = np.nan
    last_nested_direct_entry_ceiling = np.nan

    # Track distinct session-high tiers. A tier is confirmed only after an
    # 8% pullback; a new tier must then clear the prior peak by at least 5%.
    # This clusters nearby highs such as 10:19/10:30/10:33/10:48 into one
    # structural high instead of treating every marginal print as a new leg.
    trend_tier_peak = np.nan
    trend_tier_peak_volume_ratio = np.nan
    trend_tier_pullback_armed = False
    confirmed_trend_tiers = 0
    declining_trend_tiers = 0
    previous_confirmed_tier_volume_ratio = np.nan
    last_accepted_entry_trend_tiers = None

    def confidence_metrics(
        support_start: int,
        support_end: int,
        entry_index: int,
        resistance_volume_expansion: float,
        entry_volume_vs_prior_three: float,
        entry_body_range_pct: float,
        entry_close_location_pct: float,
    ) -> dict[str, float | int | bool | pd.Timestamp]:
        """Mirror the Pine confidence model without changing eligibility."""
        expansion_start = support_start
        oldest = max(0, support_start - prior_advance_lookback)
        for boundary_index in range(support_start - 1, oldest - 1, -1):
            if np.isnan(ema20[boundary_index]) or close[boundary_index] <= ema20[boundary_index]:
                expansion_start = boundary_index + 1
                break
            expansion_start = boundary_index

        leg = np.arange(expansion_start, support_start + 1)
        start_price = open_[expansion_start]
        end_price = close[support_start]
        gain_pct = (
            (end_price / start_price - 1.0) * 100.0
            if start_price > 0.0 else np.nan
        )
        path = abs(close[expansion_start] - start_price)
        if len(leg) > 1:
            path += float(np.abs(np.diff(close[leg])).sum())
        efficiency_pct = (
            abs(end_price - start_price) / path * 100.0
            if path > 0.0 else 0.0
        )

        running_high = -np.inf
        maximum_drawdown_pct = 0.0
        for leg_index in leg:
            running_high = max(running_high, high[leg_index])
            if running_high > 0.0:
                maximum_drawdown_pct = max(
                    maximum_drawdown_pct,
                    (1.0 - low[leg_index] / running_high) * 100.0,
                )

        high_volume_bull = (
            (close[leg] > open_[leg])
            & ~np.isnan(volume_ma[leg])
            & (volume_ma[leg] > 0.0)
            & (volume[leg] >= volume_ma[leg])
        )
        bull_volume = float(volume[leg][high_volume_bull].sum())
        bull_average_volume = float(volume_ma[leg][high_volume_bull].sum())
        total_volume = float(volume[leg].sum())
        bull_volume_ratio = (
            bull_volume / bull_average_volume
            if bull_average_volume > 0.0 else 0.0
        )
        bull_volume_share_pct = (
            bull_volume / total_volume * 100.0
            if total_volume > 0.0 else 0.0
        )
        expansion_strength_score = sum((
            not np.isnan(gain_pct) and gain_pct >= 10.0,
            bull_volume_ratio >= 2.0,
            bull_volume_share_pct >= 50.0,
            efficiency_pct >= 40.0,
            maximum_drawdown_pct <= 25.0,
        ))

        entry_volume_vs_previous = (
            volume[entry_index] / volume[entry_index - 1]
            if entry_index > 0 and volume[entry_index - 1] > 0.0
            else np.nan
        )
        entry_range_vs_prior_three = (
            candle_range[entry_index] / prior_three_range[entry_index]
            if not np.isnan(prior_three_range[entry_index])
            and prior_three_range[entry_index] > 0.0
            else np.nan
        )
        entry_confirmation_score = sum((
            not np.isnan(entry_volume_vs_previous)
            and entry_volume_vs_previous >= 1.20,
            not np.isnan(entry_volume_vs_prior_three)
            and entry_volume_vs_prior_three >= 1.50,
            not np.isnan(resistance_volume_expansion)
            and resistance_volume_expansion >= 1.50,
            not np.isnan(entry_range_vs_prior_three)
            and entry_range_vs_prior_three >= 1.20,
            entry_body_range_pct >= 60.0
            and entry_close_location_pct >= 75.0,
        ))
        support_to_entry_bars = max(0, entry_index - support_end)
        close_to_expansion = support_to_entry_bars <= 20
        combined_score = (
            expansion_strength_score
            + entry_confirmation_score
            + int(close_to_expansion)
        )
        return {
            "expansion_start": pd.Timestamp(time[expansion_start]),
            "expansion_bars": int(len(leg)),
            "expansion_gain_pct": float(gain_pct),
            "expansion_efficiency_pct": float(efficiency_pct),
            "expansion_drawdown_pct": float(maximum_drawdown_pct),
            "expansion_bull_volume_ratio": float(bull_volume_ratio),
            "expansion_bull_volume_share_pct": float(bull_volume_share_pct),
            "expansion_strength_score": int(expansion_strength_score),
            "support_to_entry_bars": int(support_to_entry_bars),
            "close_to_expansion": bool(close_to_expansion),
            "entry_volume_vs_previous": float(entry_volume_vs_previous),
            "entry_range_vs_prior_three": float(entry_range_vs_prior_three),
            "entry_confirmation_score": int(entry_confirmation_score),
            "combined_confidence_score": int(combined_score),
        }

    def refined_support_bounds(candidate: Candidate) -> tuple[int, int]:
        """Return the compact defended shelf used to start the chart line.

        Candidate discovery intentionally keeps a wider context window, but
        the visible support must start with the actual defended shelf, not the
        bullish expansion candle immediately before it, and must end before a
        later no-wick continuation candle.
        """
        if candidate.support_start >= candidate.support_end:
            return candidate.support_start, candidate.support_end
        first_range = max(candle_range[candidate.support_start], 1e-12)
        first_bullish_share = max(
            close[candidate.support_start] - open_[candidate.support_start],
            0.0,
        ) / first_range
        if first_bullish_share < 0.60:
            return candidate.support_start, candidate.support_end
        support_indices = np.arange(
            candidate.support_start, candidate.support_end + 1,
        )
        ranges = np.maximum(candle_range[support_indices], 1e-12)
        lower_wicks = (
            np.minimum(open_[support_indices], close[support_indices])
            - low[support_indices]
        )
        bullish_body_share = (
            np.maximum(close[support_indices] - open_[support_indices], 0.0)
            / ranges
        )
        defended = (
            (lower_wicks / ranges >= 0.20)
            & (bullish_body_share < 0.60)
        )
        if not np.any(defended):
            return candidate.support_start, candidate.support_end

        refined_end = int(support_indices[defended].max())
        refined_start = refined_end
        for prior_index in range(refined_end - 1, candidate.support_start - 1, -1):
            prior_range = max(candle_range[prior_index], 1e-12)
            prior_bullish_share = max(
                close[prior_index] - open_[prior_index], 0.0,
            ) / prior_range
            close_to_shelf = abs(
                low[prior_index] / candidate.support_low - 1.0
            ) <= 0.01
            if prior_bullish_share >= 0.60 or not close_to_shelf:
                break
            refined_start = prior_index
        return refined_start, refined_end

    def refined_pivot_shelf(
        candidate: Candidate,
        entry_index: int,
    ) -> tuple[int, int, int, int, float] | None:
        """Recover the two-bar defended shelf hidden below a later pivot.

        A one-bar pivot may borrow buyer-defense evidence from the preceding
        bars. When those bars form the actual compact shelf, freeze their low,
        find the first later close below it, and use the strongest wick-confirmed
        retest from underneath as resistance.
        """
        if "pivot" not in candidate.source:
            return None
        pivot_index = candidate.support_start
        best_refinement = None
        for newer_support in range(
            pivot_index - 1,
            max(0, pivot_index - 5),
            -1,
        ):
            older_support = newer_support - 1
            if older_support < 0:
                continue
            support_indices = np.array([older_support, newer_support])
            support_ranges = np.maximum(candle_range[support_indices], 1e-12)
            support_lower_wicks = (
                np.minimum(open_[support_indices], close[support_indices])
                - low[support_indices]
            )
            if np.any(support_lower_wicks / support_ranges * 100.0 < 20.0):
                continue
            shelf_low = float(low[support_indices].min())
            shelf_high = float(low[support_indices].max())
            if (shelf_high / shelf_low - 1.0) * 100.0 > 1.0:
                continue
            if not (
                high[newer_support] >= ema9[newer_support]
                and high[newer_support] >= ema20[newer_support]
                and not np.isnan(vwap[newer_support])
                and high[newer_support] >= vwap[newer_support]
            ):
                continue

            refined_break = None
            for breakdown_index in range(
                newer_support + 1,
                min(entry_index, newer_support + 5),
            ):
                if (
                    close[breakdown_index] < shelf_low
                    and close[breakdown_index] < open_[breakdown_index]
                ):
                    refined_break = breakdown_index
                    break
            if refined_break is None:
                continue

            strongest_rejection = None
            strongest_wick_pct = -np.inf
            for rejection_index in range(refined_break + 1, entry_index):
                rejection_range = max(
                    high[rejection_index] - low[rejection_index], 1e-12
                )
                upper_wick_pct = (
                    high[rejection_index]
                    - max(open_[rejection_index], close[rejection_index])
                ) / rejection_range * 100.0
                resistance_contact = (
                    high[rejection_index] >= shelf_low * 0.96
                    and close[rejection_index] <= shelf_low * 1.005
                    and close[rejection_index] >= shelf_low * 0.92
                )
                if resistance_contact and upper_wick_pct >= 15.0:
                    if upper_wick_pct > strongest_wick_pct:
                        strongest_wick_pct = upper_wick_pct
                        strongest_rejection = rejection_index
            if strongest_rejection is None:
                continue
            if close[entry_index] <= high[strongest_rejection]:
                continue
            candidate_refinement = (
                older_support,
                newer_support,
                refined_break,
                strongest_rejection,
                shelf_low,
            )
            if (
                best_refinement is None
                or shelf_low > best_refinement[-1]
            ):
                best_refinement = candidate_refinement
        return best_refinement

    def mature_lower_high_ceiling(entry_index: int) -> tuple[bool, tuple[float, ...]]:
        """Detect a persistent 30-bar staircase of lower overhead highs."""
        window_bars = 30
        window_highs: list[float] = []
        for window_number in range(4):
            window_end = entry_index - window_number * window_bars
            window_start = max(0, window_end - window_bars)
            if window_end <= window_start:
                return False, tuple(window_highs)
            window_highs.append(float(np.max(high[window_start:window_end])))

        descending = all(
            window_highs[newer + 1] > window_highs[newer] * 1.01
            for newer in range(3)
        )
        full_decline_pct = (
            (window_highs[3] / window_highs[0] - 1.0) * 100.0
            if window_highs[0] > 0.0 else 0.0
        )
        uncleared_prior_ceiling = close[entry_index] <= window_highs[1] * 1.002
        return (
            descending and full_decline_pct >= 5.0 and uncleared_prior_ceiling,
            tuple(window_highs),
        )

    for i in range(len(data)):
        current_clock = pd.Timestamp(time[i]).strftime("%H:%M")
        current_volume_ratio = (
            volume[i] / volume_ma[i]
            if not np.isnan(volume_ma[i]) and volume_ma[i] > 0.0
            else np.nan
        )
        if np.isnan(trend_tier_peak):
            trend_tier_peak = high[i]
            trend_tier_peak_volume_ratio = current_volume_ratio
        elif not trend_tier_pullback_armed:
            if high[i] > trend_tier_peak:
                trend_tier_peak = high[i]
                trend_tier_peak_volume_ratio = current_volume_ratio
            if low[i] <= trend_tier_peak * 0.92:
                confirmed_trend_tiers += 1
                if (
                    not np.isnan(previous_confirmed_tier_volume_ratio)
                    and not np.isnan(trend_tier_peak_volume_ratio)
                    and trend_tier_peak_volume_ratio
                    <= previous_confirmed_tier_volume_ratio * 0.90
                ):
                    declining_trend_tiers += 1
                previous_confirmed_tier_volume_ratio = (
                    trend_tier_peak_volume_ratio
                )
                trend_tier_pullback_armed = True
        elif high[i] >= trend_tier_peak * 1.05:
            trend_tier_peak = high[i]
            trend_tier_peak_volume_ratio = current_volume_ratio
            trend_tier_pullback_armed = False
        if last_nested_evidence_index is not None and i - last_nested_evidence_index > 10:
            last_nested_evidence_index = None
            last_nested_cleared_resistance = np.nan
            last_nested_blocking_resistance = np.nan
            last_nested_evidence_score = np.nan
        if last_signal_index is not None and i > last_signal_index:
            lowest_since_signal = min(lowest_since_signal, low[i])

        failed_expansion_detected_now = False
        failed_expansion_breakout_index_now = None
        failed_expansion_high_now = np.nan

        # A high-volume balance that breaks upward without accepting the new
        # prices, then falls back into the balance on a decisive bearish bar,
        # leaves trapped supply at the failed high. Do not treat the rebound
        # from that rejection as a fresh long entry until the failed high is
        # reclaimed with participation and a strong close.
        if close[i] < open_[i]:
            rejection_range = max(high[i] - low[i], 1e-12)
            rejection_body_pct = (open_[i] - close[i]) / rejection_range * 100.0
            rejection_close_location_pct = (
                (close[i] - low[i]) / rejection_range * 100.0
            )
            for rejection_lag in range(
                1, FAILED_EXPANSION_REJECTION_WINDOW_BARS + 1
            ):
                expansion_index = i - rejection_lag
                baseline_start = (
                    expansion_index - FAILED_EXPANSION_COMPRESSION_BARS * 2
                )
                compression_start = (
                    expansion_index - FAILED_EXPANSION_COMPRESSION_BARS
                )
                if baseline_start < 0:
                    continue
                compression_indices = np.arange(
                    compression_start, expansion_index
                )
                baseline_indices = np.arange(
                    baseline_start, compression_start
                )
                overlap_count = sum(
                    low[j] <= high[j - 1] and high[j] >= low[j - 1]
                    for j in compression_indices[1:]
                )
                overlap_pct = (
                    overlap_count / max(len(compression_indices) - 1, 1)
                    * 100.0
                )
                compression_volume = float(
                    np.mean(volume[compression_indices])
                )
                baseline_volume = float(np.mean(volume[baseline_indices]))
                compression_high = float(np.max(high[compression_indices]))
                expansion_range = max(
                    high[expansion_index] - low[expansion_index], 1e-12
                )
                expansion_close_location_pct = (
                    (close[expansion_index] - low[expansion_index])
                    / expansion_range * 100.0
                )
                expansion_upper_wick_pct = (
                    high[expansion_index]
                    - max(open_[expansion_index], close[expansion_index])
                ) / expansion_range * 100.0
                failed_expansion = (
                    close[expansion_index] > open_[expansion_index]
                    and close[expansion_index] > compression_high
                    and overlap_pct >= MINIMUM_FAILED_EXPANSION_OVERLAP_PCT
                    and baseline_volume > 0.0
                    and compression_volume / baseline_volume
                    >= MINIMUM_FAILED_COMPRESSION_VOLUME_RATIO
                    and compression_volume > 0.0
                    and volume[expansion_index] / compression_volume
                    >= MINIMUM_FAILED_BREAKOUT_VOLUME_RATIO
                    and (
                        expansion_close_location_pct
                        <= MAXIMUM_FAILED_BREAKOUT_CLOSE_LOCATION_PCT
                        or expansion_upper_wick_pct
                        >= MINIMUM_FAILED_BREAKOUT_UPPER_WICK_PCT
                    )
                    and rejection_body_pct
                    >= MINIMUM_FAILED_REJECTION_BODY_PCT
                    and rejection_close_location_pct
                    <= MAXIMUM_FAILED_REJECTION_CLOSE_LOCATION_PCT
                    and volume[i] / max(volume[expansion_index], 1.0)
                    >= MINIMUM_FAILED_REJECTION_VOLUME_RATIO
                    and close[i] <= compression_high
                )
                if failed_expansion:
                    failed_expansion_detected_now = True
                    failed_expansion_breakout_index_now = expansion_index
                    failed_expansion_high_now = high[expansion_index]
                    failed_expansion_records.append({
                        "breakout": pd.Timestamp(time[expansion_index]),
                        "rejection": pd.Timestamp(time[i]),
                        "high": float(high[expansion_index]),
                    })
                    break
        survivors: list[Candidate] = []
        qualifying = []

        # PARITY_RULE: candidate_evaluation
        for c in active:
            if c.expired:
                continue
            age = i - c.break_index
            if age <= 0:
                survivors.append(c)
                continue
            if age > maximum_setup_bars:
                continue
            support_upper = c.support_high
            reused_level = c.source.startswith("known-")
            support_line = c.support_low
            if c.rejection_indices and i - c.rejection_indices[-1] > max_resistance_gap:
                c.rejection_indices.clear()
                c.rejection_volume = 0.0
                c.rejection_body_pct = 0.0
                c.rejection_high = np.nan
                c.wick_confirmed_rejections = 0
                c.accepted_closes_above_resistance_contact = 0

            rejection_now = (
                high[i] >= support_line * (1.0 - resistance_touch_tolerance)
                and close[i] <= support_upper
                and close[i] >= c.support_low * (1.0 - resistance_touch_tolerance * 2.0)
            )

            # A failed breakdown that closes back above the support zone before
            # support proves itself as resistance is not a flip setup.
            if not c.rejection_indices and close[i] > support_upper:
                continue

            prior_rejection_high = c.rejection_high
            prior_resistance_contact = (
                float(np.mean(high[c.rejection_indices]))
                if c.rejection_indices else np.nan
            )
            closes_above_resistance_contact = (
                len(c.rejection_indices) >= 2
                and not np.isnan(prior_resistance_contact)
                and close[i] > prior_resistance_contact
            )
            if closes_above_resistance_contact:
                c.accepted_closes_above_resistance_contact += 1
            else:
                c.accepted_closes_above_resistance_contact = 0

            same_level_resistance_high = max(
                (
                    other.rejection_high
                    for other in active
                    if other is not c
                    and other.rejection_indices
                    and not np.isnan(other.rejection_high)
                    and abs(other.support_low / c.support_low - 1.0) <= support_tolerance
                ),
                default=np.nan,
            )
            clears_same_level_resistance = (
                np.isnan(same_level_resistance_high)
                or close[i] > same_level_resistance_high * (1.0 + min_breakout_pct)
            )
            breakout_now = (
                c.rejection_indices
                and c.wick_confirmed_rejections >= 1
                and not np.isnan(prior_rejection_high)
                and close[i] > prior_rejection_high * (1.0 + min_breakout_pct)
                and (
                    (
                        reused_level
                        and clears_same_level_resistance
                    )
                    or (
                        not reused_level
                        and (
                            close[i] > c.support_high
                            or (
                                c.source == "near-ema-low"
                                and
                                len(c.rejection_indices) >= 3
                                and len(c.rejection_indices) <= 10
                                and (open_[c.break_index] - close[c.break_index])
                                    / max(high[c.break_index] - low[c.break_index], 1e-12)
                                    * 100.0 >= 80.0
                                and close[i] >= c.support_high * 0.97
                                and (close[i] / c.support_low - 1.0) * 100.0 <= 5.0
                                and c.prior_advance_pct >= 30.0
                            )
                        )
                    )
                )
            )

            if debug_clocks and current_clock in debug_clocks:
                print(
                    "DEBUG_ACTIVE", current_clock,
                    "support", pd.Timestamp(time[c.support_start]).strftime("%H:%M"),
                    pd.Timestamp(time[c.support_end]).strftime("%H:%M"),
                    round(c.support_low, 4), round(c.support_high, 4),
                    "break", pd.Timestamp(time[c.break_index]).strftime("%H:%M"),
                    "source", c.source,
                    "rejects", [pd.Timestamp(time[j]).strftime("%H:%M") for j in c.rejection_indices],
                    "rhigh", None if np.isnan(c.rejection_high) else round(c.rejection_high, 4),
                    "breakout", bool(breakout_now),
                )

            # A close through resistance is an entry only when the reclaim bar
            # also has the required price/volume quality. Once a bar closes
            # cleanly above both the frozen support zone and the established
            # contact price, resistance has already been crossed. If that first
            # cross is not qualified, consume the sequence; a later momentum
            # candle is continuation, not a delayed reclaim entry.
            if breakout_now:
                if not c.support_buyer_defense:
                    # Keep the provisional level through this bar so it can
                    # still block a same-bar shortcut, then expire it before
                    # any later reclaim can reuse false support evidence.
                    c.expired = True
                    survivors.append(c)
                    continue
                avg_rejection_volume = c.rejection_volume / len(c.rejection_indices)
                avg_rejection_body = c.rejection_body_pct / len(c.rejection_indices)
                bullish_body_pct = max(0.0, (close[i] - open_[i]) / close[i] * 100.0)
                volume_expansion = volume[i] / avg_rejection_volume if avg_rejection_volume else 0.0
                body_expansion = bullish_body_pct / avg_rejection_body if avg_rejection_body else 0.0
                quiet_count = sum(volume[j] < volume_ma[j] for j in c.rejection_indices)
                direct_volume = volume_expansion >= min_volume_expansion
                quiet_expansion = (
                    quiet_count >= min_quiet_resistance_bars
                    and i > 0
                    and volume[i] >= volume_ma[i - 1]
                    and body_expansion >= min_body_expansion
                )
                close_location = (close[i] - low[i]) / max(high[i] - low[i], 1e-12) * 100.0
                entry_range_pct = (high[i] - low[i]) / max(close[i], 1e-12) * 100.0
                entry_body_range_pct = (close[i] - open_[i]) / max(high[i] - low[i], 1e-12) * 100.0
                recent_high = high[max(0, i - 30):i].max() if i > 0 else high[i]
                gap_to_recent_high_pct = (recent_high / close[i] - 1.0) * 100.0
                break_range_for_quality = max(high[c.break_index] - low[c.break_index], 1e-12)
                breakdown_body_range_for_quality = (open_[c.break_index] - close[c.break_index]) / break_range_for_quality * 100.0
                stage_bars_for_quality = max(0, i - c.break_index - 1)
                if stage_bars_for_quality > 0:
                    stage_indices_for_quality = np.arange(c.break_index + 1, i)
                    stage_quiet_pct_for_quality = float(np.mean(volume[stage_indices_for_quality] < volume_ma[stage_indices_for_quality]) * 100.0)
                else:
                    stage_quiet_pct_for_quality = 0.0
                support_zone_width_pct = (c.support_high / c.support_low - 1.0) * 100.0
                entry_distance_from_support_pct = (close[i] / c.support_low - 1.0) * 100.0
                resistance_bullish_count = sum(close[j] > open_[j] for j in c.rejection_indices)
                resistance_bullish_pct = resistance_bullish_count / len(c.rejection_indices) * 100.0
                clean_resistance_build = (
                    len(c.rejection_indices) >= 2
                    and resistance_bullish_count == len(c.rejection_indices)
                )
                far_reclaim_quality = (
                    entry_distance_from_support_pct <= 7.0
                    or (c.support_touches >= 2 and entry_distance_from_support_pct <= 15.0)
                    or (stage_bars_for_quality <= 10 and entry_distance_from_support_pct <= 15.0)
                    or c.prior_advance_pct >= 90.0
                    or clean_resistance_build
                )
                long_volume_expansion = (
                    volume[i] / long_volume_ma[i]
                    if not np.isnan(long_volume_ma[i]) and long_volume_ma[i] > 0.0
                    else np.nan
                )
                ema20_gap_pct = (close[i] / ema20[i] - 1.0) * 100.0 if ema20[i] > 0.0 else np.nan
                rising_ema_context = (
                    i >= 5
                    and ema20[i] > ema20[i - 5]
                    and ema20_gap_pct >= 5.0
                )
                sustained_participation = (
                    (not np.isnan(long_volume_expansion) and long_volume_expansion >= 1.5)
                    or rising_ema_context
                )
                resistance_attempts = 0
                previous_rejection = None
                for rejection_index in c.rejection_indices:
                    if previous_rejection is None or rejection_index - previous_rejection > 1:
                        resistance_attempts += 1
                    previous_rejection = rejection_index
                stage_bull_bear_volume_ratio = np.nan
                if stage_bars_for_quality > 0:
                    stage_rel_volume = np.divide(
                        volume[stage_indices_for_quality],
                        volume_ma[stage_indices_for_quality],
                        out=np.full(stage_bars_for_quality, np.nan),
                        where=volume_ma[stage_indices_for_quality] > 0,
                    )
                    stage_bullish = close[stage_indices_for_quality] > open_[stage_indices_for_quality]
                    stage_bearish = close[stage_indices_for_quality] < open_[stage_indices_for_quality]
                    bullish_rel_volume = stage_rel_volume[stage_bullish]
                    bearish_rel_volume = stage_rel_volume[stage_bearish]
                    if len(bullish_rel_volume) and len(bearish_rel_volume):
                        bullish_average = np.nanmean(bullish_rel_volume)
                        bearish_average = np.nanmean(bearish_rel_volume)
                        if bearish_average > 0.0:
                            stage_bull_bear_volume_ratio = bullish_average / bearish_average
                entry_volume_vs_prior_three = (
                    volume[i] / prior_three_volume[i]
                    if not np.isnan(prior_three_volume[i]) and prior_three_volume[i] > 0.0
                    else np.nan
                )
                behavior_quality_score = 0
                if resistance_attempts == 2:
                    behavior_quality_score += 2
                if not np.isnan(volume_expansion) and volume_expansion <= 3.0:
                    behavior_quality_score += 1
                if not np.isnan(entry_volume_vs_prior_three) and entry_volume_vs_prior_three <= 3.0:
                    behavior_quality_score += 1
                if not np.isnan(stage_bull_bear_volume_ratio) and stage_bull_bear_volume_ratio >= 1.0:
                    behavior_quality_score += 1
                precise_long_stage = (
                    stage_bars_for_quality <= 30
                    or (support_zone_width_pct <= 4.0 and c.prior_advance_pct >= 30.0)
                )
                trend_aligned = (
                    ema9[i] > ema20[i]
                    and close[i] >= ema9[i]
                    and close[i] >= ema20[i]
                    and not np.isnan(vwap[i])
                    and close[i] >= vwap[i]
                )
                near_ema_reclaim_exception = (
                    not reused_level
                    and c.source == "near-ema-low"
                    and len(c.rejection_indices) >= 3
                    and len(c.rejection_indices) <= 10
                    and breakdown_body_range_for_quality >= 80.0
                    and close[i] >= c.support_high * 0.97
                    and entry_distance_from_support_pct <= 5.0
                    and c.prior_advance_pct >= 30.0
                    and entry_body_range_pct >= 50.0
                    and entry_range_pct >= 5.0
                    and volume_expansion >= 1.30
                    and ema9[i] >= ema20[i] * (1.0 - entry_ema_alignment_tolerance)
                    and close[i] >= ema9[i]
                    and close[i] >= ema20[i]
                    and not np.isnan(vwap[i])
                    and close[i] >= vwap[i]
                )
                entry_trend_aligned = trend_aligned or near_ema_reclaim_exception
                vwap_gap_pct = (
                    (close[i] / vwap[i] - 1.0) * 100.0
                    if not np.isnan(vwap[i]) and vwap[i] > 0.0
                    else np.nan
                )
                controlled_extension = (
                    not np.isnan(vwap_gap_pct)
                    and (entry_range_pct <= 15.0 or vwap_gap_pct <= 25.0)
                    and (vwap_gap_pct <= 40.0 or breakdown_body_range_for_quality >= 60.0)
                )
                qualified = (
                    close[i] > open_[i]
                    and c.support_buyer_defense
                    and close_location >= min_close_location
                    and entry_body_range_pct >= 35.0
                    and (
                        entry_range_pct >= 3.0
                        or (entry_range_pct >= 2.0 and stage_quiet_pct_for_quality >= 80.0 and body_expansion >= 2.0)
                    )
                    and (gap_to_recent_high_pct <= 15.0 or entry_trend_aligned)
                    and breakdown_body_range_for_quality >= 30.0
                    and far_reclaim_quality
                    and sustained_participation
                    and precise_long_stage
                    and (direct_volume or quiet_expansion)
                    and entry_trend_aligned
                    and controlled_extension
                )
                lower_high_veto, lower_high_windows = mature_lower_high_ceiling(i)
                # Once price has already closed above the frozen resistance
                # contact on two consecutive bars, the market has accepted
                # the level.  A later high-volume candle is continuation, not
                # the first support-to-resistance reclaim entry.
                stale_mature_reclaim = (
                    lower_high_veto
                    and c.accepted_closes_above_resistance_contact >= 2
                )
                qualified = qualified and not stale_mature_reclaim
                if debug_clocks and current_clock in debug_clocks:
                    print(
                        "DEBUG_QUALITY", current_clock,
                        "qualified", bool(qualified),
                        "close_bull", bool(close[i] > open_[i]),
                        "close_loc", round(close_location, 2),
                        "body_range", round(entry_body_range_pct, 2),
                        "range", round(entry_range_pct, 2),
                        "gap_high", round(gap_to_recent_high_pct, 2),
                        "break_body", round(breakdown_body_range_for_quality, 2),
                        "far", bool(far_reclaim_quality),
                        "participation", bool(sustained_participation),
                        "precise_long", bool(precise_long_stage),
                        "volume", bool(direct_volume),
                        "quiet", bool(quiet_expansion),
                        "volume_x", round(volume_expansion, 2),
                        "stage", stage_bars_for_quality,
                        "lower_high_veto", bool(lower_high_veto),
                        "prior_acceptance", c.accepted_closes_above_resistance_contact,
                        "stale_mature_reclaim", bool(stale_mature_reclaim),
                        "lower_high_windows", [round(x, 4) for x in lower_high_windows],
                    )
                # PARITY_RULE: qualified_entry_acceptance
                if qualified:
                    confidence = confidence_metrics(
                        c.support_start,
                        c.support_end,
                        i,
                        volume_expansion,
                        entry_volume_vs_prior_three,
                        entry_body_range_pct,
                        close_location,
                    )
                    mature_weak_reset = (
                        confirmed_trend_tiers >= 4
                        and declining_trend_tiers >= 2
                        and confidence["expansion_strength_score"] <= 1
                        and confidence["support_to_entry_bars"] > 20
                    )
                    if mature_weak_reset:
                        # The session has already completed several distinct
                        # high/pullback tiers on weakening participation, while
                        # this candidate is only a distant micro-reset. Keep it
                        # out of the actionable set without weakening fresh
                        # high-quality structures in mature trends.
                        survivors.append(c)
                        continue
                    stage = data.iloc[c.break_index + 1:i]
                    stage_bars = len(stage)
                    stage_quiet_bars = int((stage["Volume"] < stage["Volume MA"]).sum())
                    stage_quiet_pct = stage_quiet_bars / stage_bars * 100.0 if stage_bars else 0.0
                    break_range = max(high[c.break_index] - low[c.break_index], 1e-12)
                    breakdown_volume_x = (
                        volume[c.break_index] / volume_ma[c.break_index]
                        if volume_ma[c.break_index] > 0 else np.nan
                    )
                    breakdown_body_range_pct = (
                        (open_[c.break_index] - close[c.break_index]) / break_range * 100.0
                    )
                    breakdown_close_from_low_pct = (
                        (close[c.break_index] - low[c.break_index]) / break_range * 100.0
                    )
                    qualifying.append((
                        c.support_high, c, volume_expansion, body_expansion,
                        close_location, stage_bars, stage_quiet_bars,
                        stage_quiet_pct, breakdown_volume_x,
                        breakdown_body_range_pct, breakdown_close_from_low_pct,
                        resistance_bullish_pct, long_volume_expansion,
                        ema20_gap_pct, rising_ema_context,
                        behavior_quality_score, resistance_attempts,
                        stage_bull_bear_volume_ratio,
                        entry_volume_vs_prior_three,
                        confidence,
                    ))
                    survivors.append(c)
                    continue
                unqualified_resistance_cross = (
                    not np.isnan(prior_rejection_high)
                    and close[i] > max(
                        c.support_high,
                        prior_rejection_high,
                    )
                    and c.accepted_bullish_closes_above_support >= 1
                )
                if unqualified_resistance_cross:
                    continue
                if close[i] > c.support_high and close[i] > open_[i]:
                    c.accepted_bullish_closes_above_support += 1
                else:
                    c.accepted_bullish_closes_above_support = 0
                c.rejection_indices.append(i)
                c.rejection_volume += volume[i]
                c.rejection_body_pct += abs(close[i] - open_[i]) / close[i] * 100.0
                c.rejection_high = max(c.rejection_high, high[i])
                upper_wick_pct = (
                    (high[i] - max(open_[i], close[i]))
                    / max(high[i] - low[i], 1e-12)
                    * 100.0
                )
                if upper_wick_pct >= 15.0:
                    c.wick_confirmed_rejections += 1
                survivors.append(c)
                continue

            if rejection_now:
                c.accepted_bullish_closes_above_support = 0
                c.rejection_indices.append(i)
                c.rejection_volume += volume[i]
                c.rejection_body_pct += abs(close[i] - open_[i]) / close[i] * 100.0
                c.rejection_high = high[i] if np.isnan(c.rejection_high) else max(c.rejection_high, high[i])
                upper_wick_pct = (
                    (high[i] - max(open_[i], close[i]))
                    / max(high[i] - low[i], 1e-12)
                    * 100.0
                )
                if upper_wick_pct >= 15.0:
                    c.wick_confirmed_rejections += 1
                survivors.append(c)
            elif close[i] > c.support_high and close[i] > open_[i]:
                c.accepted_bullish_closes_above_support += 1
                survivors.append(c)
            else:
                c.accepted_bullish_closes_above_support = 0
                survivors.append(c)

        if qualifying:
            selected = max(
                qualifying,
                key=lambda x: (
                    x[1].rejection_indices[-1],
                    x[0],
                    x[2] >= 3.0,
                    x[1].support_end,
                ),
            )
            if selected[-1]["expansion_strength_score"] <= 1:
                structural_alternatives = [
                    candidate for candidate in qualifying
                    if candidate[1].rejection_indices[-1]
                    == selected[1].rejection_indices[-1]
                    and candidate[-1]["expansion_strength_score"] >= 4
                ]
                if structural_alternatives:
                    selected = max(
                        structural_alternatives,
                        key=lambda x: (
                            x[-1]["expansion_strength_score"],
                            x[0],
                            x[2] >= 3.0,
                            x[1].support_end,
                        ),
                    )
            (
                _, c, volume_expansion, body_expansion, close_location,
                stage_bars, stage_quiet_bars, stage_quiet_pct,
                breakdown_volume_x, breakdown_body_range_pct,
                breakdown_close_from_low_pct,
                resistance_bullish_pct, long_volume_expansion,
                ema20_gap_pct, rising_ema_context,
                behavior_quality_score, resistance_attempts,
                stage_bull_bear_volume_ratio,
                entry_volume_vs_prior_three,
                confidence,
            ) = selected
            # A breakout bar cannot create the resistance used to block
            # itself.  Evaluate only overhead rejection evidence that was
            # already proven before this bar, and expire it after ten bars.
            blockers = []
            for other in survivors:
                prior_rejections = [j for j in other.rejection_indices if j < i]
                if not prior_rejections:
                    continue
                prior_blocker_high = max(high[j] for j in prior_rejections)
                prior_blocker_bar = prior_rejections[-1]
                if (
                    other is not c
                    and other.support_high > c.support_high
                    and (other.support_high / c.support_high - 1.0) <= 0.15
                    and i - prior_blocker_bar <= 10
                    and close[i] <= prior_blocker_high
                ):
                    blockers.append((other, prior_blocker_high, prior_blocker_bar))
            previously_proven_blocker = bool(blockers)
            immediate_proven_blocker = any(
                i - prior_blocker_bar <= 3
                for _, _, prior_blocker_bar in blockers
            )
            stacked_same_bar_blockers = False
            same_bar_blocker_count = 0
            entry_distance_from_support_pct = (close[i] / c.support_low - 1.0) * 100.0
            known_overhead_distances = [
                (level.support_low / close[i] - 1.0) * 100.0
                for level in known_levels
                if level.support_low > c.support_low * (1.0 + support_tolerance)
                and level.support_low > close[i]
            ]
            nearest_known_overhead_pct = min(known_overhead_distances) if known_overhead_distances else np.nan
            nearest_known = None
            if known_overhead_distances:
                eligible_known = [level for level in known_levels if level.support_low > c.support_low * (1.0 + support_tolerance) and level.support_low > close[i]]
                nearest_known = min(eligible_known, key=lambda level: level.support_low)
            # The Pine runtime still has the previously proven support shelf
            # live when price closes immediately underneath it.  The compact
            # Python level model can merge that shelf into the known-level
            # list one bar earlier, so mirror the same hard blocker here: a
            # candle that has not actually cleared a former-support edge is
            # not the reclaim entry.  BOXL 14:39 closes only 0.07% beneath the
            # old shelf; 14:40 clears it and remains eligible.
            immediate_uncleared_known_overhead = (
                not np.isnan(nearest_known_overhead_pct)
                and nearest_known_overhead_pct <= 0.25
            )
            stacked_known_overhead_count = sum(
                level.support_low > c.support_low * (1.0 + support_tolerance)
                and level.support_low > close[i]
                and (level.support_low / close[i] - 1.0) * 100.0 <= 15.0
                for level in known_levels
            )
            high_conviction_reclaim = (
                volume_expansion >= 3.0
                and not np.isnan(long_volume_expansion)
                and long_volume_expansion >= 4.0
            ) or (
                ema9[i] > ema20[i]
                and close[i] >= ema9[i]
                and close[i] >= ema20[i]
                and not np.isnan(vwap[i])
                and close[i] >= vwap[i]
            ) or (
                c.source == "near-ema-low"
                and
                len(c.rejection_indices) >= 3
                and len(c.rejection_indices) <= 10
                and close[i] >= c.support_high * 0.97
                and (close[i] / c.support_low - 1.0) * 100.0 <= 5.0
                and c.prior_advance_pct >= 30.0
                and ema9[i] >= ema20[i] * (1.0 - entry_ema_alignment_tolerance)
                and close[i] >= ema9[i]
                and close[i] >= ema20[i]
                and not np.isnan(vwap[i])
                and close[i] >= vwap[i]
            )
            same_unreset_price_regime = (
                last_signal_index is not None
                and last_signal_support_low is not None
                and last_signal_support_high is not None
                and c.support_start > last_signal_index
                and c.support_low > last_signal_support_low
                and (c.support_low / last_signal_support_low - 1.0) * 100.0 <= 15.0
                and lowest_since_signal > last_signal_support_high
            )
            distinct_higher_support_tier = (
                last_signal_support_low is not None
                and (c.support_low / last_signal_support_low - 1.0) * 100.0
                >= 10.0
                and confidence["entry_confirmation_score"] >= 4
            )
            same_unreset_price_regime = (
                same_unreset_price_regime and not distinct_higher_support_tier
            )
            prior_setup_age = (
                i - setup_records[-1]["time_index"]
                if setup_records else None
            )
            setup_confirms_new_regime = (
                prior_setup_age is not None
                and 2 <= prior_setup_age <= 20
            )
            premature_after_setup = (
                prior_setup_age is not None and prior_setup_age < 2
            )
            previously_accepted_same_support = any(
                abs(c.support_low / accepted_support_low - 1.0) <= 0.002
                for accepted_support_low in accepted_signal_support_lows
                if accepted_support_low > 0.0
            )
            accepted_higher_support_tier = any(
                accepted_support_low
                > c.support_low * (1.0 + support_tolerance)
                for accepted_support_low in accepted_signal_support_lows
            )
            stale_reactivated_lower_support = (
                previously_accepted_same_support
                and accepted_higher_support_tier
            )
            if debug_clocks and current_clock in debug_clocks:
                print(
                    "DEBUG_BLOCKERS", current_clock,
                    "selected_support", round(c.support_low, 4), round(c.support_high, 4),
                    "selected_resistance", round(c.rejection_high, 4),
                    "setup_age", prior_setup_age,
                    "blockers", [
                        {
                            "support": (round(x.support_low, 4), round(x.support_high, 4)),
                            "resistance": round(prior_high, 4),
                            "break": pd.Timestamp(time[x.break_index]).strftime("%H:%M"),
                            "last_reject": pd.Timestamp(time[prior_bar]).strftime("%H:%M"),
                        }
                        for x, prior_high, prior_bar in blockers
                    ],
                )
            original_support_blockers = [
                other for other in survivors
                if other is not c
                and other.rejection_indices
                and other.support_high > c.support_high
                and (other.support_high / c.support_high - 1.0) <= 0.15
                and close[i] <= other.support_high
            ]
            blocked = (
                immediate_proven_blocker
                and confidence["expansion_strength_score"] < 4
                and c.prior_advance_pct < 15.0
            ) or (
                bool(original_support_blockers) and not high_conviction_reclaim
            ) or (
                # Three separate former-support shelves overhead describe a
                # stacked supply regime, not a clean reclaim.  Strong volume
                # through the lowest shelf cannot waive the two higher ones.
                stacked_known_overhead_count >= 3
            )
            blocked = blocked or (
                same_unreset_price_regime and not setup_confirms_new_regime
            )
            blocked = blocked or immediate_uncleared_known_overhead
            blocked = blocked or stale_reactivated_lower_support
            duplicate = (
                last_signal_index is not None
                and i - last_signal_index <= 0
                and last_signal_resistance is not None
                and abs(c.rejection_high / last_signal_resistance - 1.0) <= support_tolerance
            )
            signaled_now = not blocked and not duplicate
            continuation_instead_of_fresh_reclaim = (
                stage_bars > 10
                and (
                    (
                        resistance_attempts == 1
                        and c.accepted_bullish_closes_above_support >= 2
                    )
                    or (
                        resistance_acceptance_guard
                        and c.accepted_closes_above_resistance_contact >= 3
                        and (
                            confidence["entry_confirmation_score"] < 5
                            or (
                                stage_bars > 30
                                and resistance_attempts >= 3
                            )
                        )
                    )
                )
            )
            if continuation_instead_of_fresh_reclaim:
                signaled_now = False
            rapid_higher_continuation = (
                last_accepted_signal_index is not None
                and pd.Timedelta(0)
                < pd.Timestamp(time[i])
                - pd.Timestamp(time[last_accepted_signal_index])
                <= pd.Timedelta(minutes=35)
                and last_accepted_signal_resistance_stage_bars is not None
                and last_accepted_signal_resistance_stage_bars >= 5
                and c.source != "near-ema-low"
                and "pivot" not in c.source
                and volume_expansion < 4.0
                and last_accepted_signal_support_high is not None
                and c.support_low > last_accepted_signal_support_high
            )
            if rapid_higher_continuation:
                signaled_now = False
            excessively_retested_resistance = resistance_attempts > 4
            previous_bar_already_cleared_resistance = (
                i > 0
                and not np.isnan(c.rejection_high)
                and close[i - 1] >= c.rejection_high - 1e-9
                and close[i - 1] > c.support_high
                and not np.isnan(volume_ma[i - 1])
                and volume[i - 1] >= volume_ma[i - 1]
            )
            fresh_structure_veto = (
                c.source == "low"
                and (
                    body_expansion < 1.50
                    or (stage_bars > 30 and resistance_attempts < 3)
                )
            ) or excessively_retested_resistance \
                or previous_bar_already_cleared_resistance
            weak_marginal_breakout = (
                stage_bars > 10
                and close_location <= 55.0
                and entry_body_range_pct < 45.0
            )
            mature_post_entry_continuation = (
                mature_post_entry_veto(
                    confirmed_trend_tiers,
                    last_accepted_entry_trend_tiers,
                    confidence["entry_confirmation_score"],
                )
            )
            blocked_by_failed_expansion = (
                c.failed_expansion_origin
                and not np.isnan(c.failed_expansion_high)
                and close[i] <= c.failed_expansion_high
            )
            # A strong bullish impulse that is immediately erased leaves
            # supply at its high. A compact shelf formed inside that failed
            # move is not a fresh reclaim until the entry clears that high.
            failed_impulse_overhead = False
            impulse_scan_start = max(0, c.support_start - 4)
            for impulse_i in range(impulse_scan_start, c.support_end + 1):
                if (
                    last_accepted_signal_index is not None
                    and impulse_i <= last_accepted_signal_index
                ):
                    continue
                impulse_range = max(
                    high[impulse_i] - low[impulse_i], 1e-12
                )
                impulse_body_pct = (
                    max(close[impulse_i] - open_[impulse_i], 0.0)
                    / impulse_range * 100.0
                )
                impulse_close_location = (
                    (close[impulse_i] - low[impulse_i])
                    / impulse_range * 100.0
                )
                impulse_volume_ratio = (
                    volume[impulse_i] / volume_ma[impulse_i]
                    if volume_ma[impulse_i] > 0.0 else np.nan
                )
                if not (
                    impulse_body_pct >= 60.0
                    and impulse_close_location >= 75.0
                    and not np.isnan(impulse_volume_ratio)
                    and impulse_volume_ratio >= 1.50
                ):
                    continue
                impulse_end_i = impulse_i
                continuation_i = impulse_i + 1
                if continuation_i < c.break_index:
                    continuation_range = max(
                        high[continuation_i] - low[continuation_i], 1e-12
                    )
                    continuation_body_pct = (
                        max(close[continuation_i] - open_[continuation_i], 0.0)
                        / continuation_range * 100.0
                    )
                    continuation_close_location = (
                        (close[continuation_i] - low[continuation_i])
                        / continuation_range * 100.0
                    )
                    continuation_volume_ratio = (
                        volume[continuation_i] / volume_ma[continuation_i]
                        if volume_ma[continuation_i] > 0.0 else np.nan
                    )
                    if (
                        continuation_body_pct >= 40.0
                        and continuation_close_location >= 65.0
                        and not np.isnan(continuation_volume_ratio)
                        and continuation_volume_ratio >= 1.0
                    ):
                        impulse_end_i = continuation_i
                rejection_i = impulse_end_i + 1
                if rejection_i < c.break_index:
                    rejection_range = max(
                        high[rejection_i] - low[rejection_i], 1e-12
                    )
                    rejection_body_pct = (
                        max(open_[rejection_i] - close[rejection_i], 0.0)
                        / rejection_range * 100.0
                    )
                    rejection_close_location = (
                        (close[rejection_i] - low[rejection_i])
                        / rejection_range * 100.0
                    )
                    rejection_volume_ratio = (
                        volume[rejection_i] / volume_ma[rejection_i]
                        if volume_ma[rejection_i] > 0.0 else np.nan
                    )
                    if (
                        rejection_body_pct >= 60.0
                        and rejection_close_location <= 25.0
                        and not np.isnan(rejection_volume_ratio)
                        and rejection_volume_ratio >= 1.0
                        and close[i] <= max(high[impulse_i:impulse_end_i + 1])
                    ):
                        failed_impulse_overhead = True
                if failed_impulse_overhead:
                    break
            failed_impulse_overhead = (
                failed_impulse_overhead
                and confidence["expansion_strength_score"] < 5
            )
            fresh_structure_veto = (
                fresh_structure_veto
                or mature_post_entry_continuation
                or rapid_higher_continuation
                or blocked_by_failed_expansion
                or failed_impulse_overhead
                or premature_after_setup
                or weak_marginal_breakout
            )
            if debug_clocks and current_clock in debug_clocks:
                print(
                    "DEBUG_FINAL_GUARDS", current_clock,
                    "fresh", bool(fresh_structure_veto),
                    "rapid", bool(rapid_higher_continuation),
                    "body_x", round(body_expansion, 3),
                    "accepted_age", None if last_accepted_signal_index is None
                    else i - last_accepted_signal_index,
                    "accepted_stage", last_accepted_signal_resistance_stage_bars,
                    "mature", bool(mature_post_entry_continuation),
                    "failed_expansion", bool(blocked_by_failed_expansion),
                    "failed_impulse", bool(failed_impulse_overhead),
                    "expansion_score", confidence["expansion_strength_score"],
                    "confirmation_score", confidence["entry_confirmation_score"],
                    "prior_advance", round(c.prior_advance_pct, 3),
                )
            if fresh_structure_veto:
                signaled_now = False
                # Consume this exact pattern and remember its price regime.
                # A later bar may not substitute for the rejected breakout
                # without first forming a genuinely new structure.
                if not rapid_higher_continuation:
                    last_signal_index = i
                    last_signal_resistance = c.rejection_high
                    last_signal_support_low = c.support_low
                    last_signal_support_high = c.support_high
                    last_signal_resistance_stage_bars = stage_bars
                    lowest_since_signal = np.inf
                survivors = [
                    other for other in survivors
                    if abs(other.support_low / c.support_low - 1.0) > signal_clear_tolerance
                ]
            if signaled_now:
                recent_nested_evidence = (
                    last_nested_evidence_index is not None
                    and i > last_nested_evidence_index
                    and i - last_nested_evidence_index <= 10
                    and not np.isnan(last_nested_blocking_resistance)
                    and close[i] > last_nested_blocking_resistance
                )
                display_support_start, display_support_end = (
                    refined_support_bounds(c)
                )
                latest_rejection = c.rejection_indices[-1]
                final_resistance_tests_frozen_support = (
                    high[latest_rejection] >= c.support_low
                    and close[latest_rejection] <= c.support_low
                )
                flip_level = (
                    c.support_low
                    if final_resistance_tests_frozen_support
                    else float(np.mean(high[c.rejection_indices]))
                )
                display_break = c.break_index
                display_rejections = list(c.rejection_indices)
                display_resistance = c.rejection_high
                display_support_low = c.support_low
                display_support_high = c.support_high
                pivot_refinement = refined_pivot_shelf(c, i)
                if pivot_refinement is not None:
                    (
                        display_support_start,
                        display_support_end,
                        display_break,
                        strongest_rejection,
                        display_support_low,
                    ) = pivot_refinement
                    display_support_high = max(
                        display_support_low,
                        float(np.mean(body_floor[[
                            display_support_start,
                            display_support_end,
                        ]])),
                    )
                    display_rejections = [strongest_rejection]
                    display_resistance = high[strongest_rejection]
                    flip_level = display_support_low
                signals.append({
                    "time": pd.Timestamp(time[i]),
                    "support_low": display_support_low,
                    "support_high": display_support_high,
                    "flip_level": flip_level,
                    "support_start": pd.Timestamp(time[display_support_start]),
                    "support_end": pd.Timestamp(time[display_support_end]),
                    "break": pd.Timestamp(time[display_break]),
                    "resistance": display_resistance,
                    "rejections": ",".join(
                        pd.Timestamp(time[j]).strftime("%H:%M")
                        for j in display_rejections
                    ),
                    "touches": c.support_touches,
                    "advance_pct": c.prior_advance_pct,
                    "volume_x": volume_expansion,
                    "body_x": body_expansion,
                    "close_location": close_location,
                    "stage_bars": stage_bars,
                    "stage_quiet_bars": stage_quiet_bars,
                    "stage_quiet_pct": stage_quiet_pct,
                    "breakdown_volume_x": breakdown_volume_x,
                    "breakdown_body_range_pct": breakdown_body_range_pct,
                    "breakdown_close_from_low_pct": breakdown_close_from_low_pct,
                    "source": c.source,
                    "same_bar_blockers": same_bar_blocker_count,
                    "entry_distance_from_support_pct": entry_distance_from_support_pct,
                    "resistance_bullish_pct": resistance_bullish_pct,
                    "long_volume_x": long_volume_expansion,
                    "ema20_gap_pct": ema20_gap_pct,
                    "rising_ema_context": rising_ema_context,
                    "behavior_quality_score": behavior_quality_score,
                    "resistance_attempts": resistance_attempts,
                    "stage_bull_bear_volume_ratio": stage_bull_bear_volume_ratio,
                    "entry_volume_vs_prior_three": entry_volume_vs_prior_three,
                    **confidence,
                    "prior_accepted_bullish_closes": c.accepted_bullish_closes_above_support,
                    "nearest_known_overhead_pct": nearest_known_overhead_pct,
                    "known_overhead_low": nearest_known.support_low if nearest_known else np.nan,
                    "known_overhead_high": nearest_known.support_high if nearest_known else np.nan,
                    "known_overhead_touches": nearest_known.support_touches if nearest_known else 0,
                    "known_overhead_advance": nearest_known.prior_advance_pct if nearest_known else np.nan,
                    "known_overhead_start": pd.Timestamp(time[nearest_known.support_start]) if nearest_known else pd.NaT,
                    "known_overhead_levels": ",".join(f"{level.support_low:.4f}" for level in known_levels if level.support_low > c.support_low * (1.0 + support_tolerance) and (level.support_low / close[i] - 1.0) * 100.0 <= 15.0),
                    "nested_context": recent_nested_evidence,
                    "nested_evidence_time": pd.Timestamp(time[last_nested_evidence_index]) if recent_nested_evidence else pd.NaT,
                    "nested_evidence_age": i - last_nested_evidence_index if recent_nested_evidence else np.nan,
                    "nested_cleared_resistance": last_nested_cleared_resistance if recent_nested_evidence else np.nan,
                    "nested_blocking_resistance": last_nested_blocking_resistance if recent_nested_evidence else np.nan,
                })
                last_signal_index = i
                last_signal_resistance = c.rejection_high
                last_signal_support_low = c.support_low
                last_signal_support_high = c.support_high
                last_signal_resistance_stage_bars = stage_bars
                last_accepted_signal_index = i
                last_accepted_signal_support_high = c.support_high
                last_accepted_signal_resistance_stage_bars = stage_bars
                last_accepted_entry_trend_tiers = confirmed_trend_tiers
                accepted_signal_support_lows.append(c.support_low)
                lowest_since_signal = np.inf
                last_nested_evidence_index = None
                last_nested_cleared_resistance = np.nan
                last_nested_blocking_resistance = np.nan
                last_nested_evidence_score = np.nan
            if signaled_now:
                survivors = [
                    other for other in survivors
                    if abs(other.support_low / c.support_low - 1.0) > signal_clear_tolerance
                ]
            elif duplicate:
                survivors = [other for other in survivors if other is not c]

        active = survivors

        # PARITY_RULE: nested_reclaim
        nested_volume_ratio = (
            volume[i] / prior_three_volume[i]
            if not np.isnan(prior_three_volume[i]) and prior_three_volume[i] > 0
            else np.nan
        )
        nested_range_ratio = (
            candle_range[i] / prior_three_range[i]
            if not np.isnan(prior_three_range[i]) and prior_three_range[i] > 0
            else np.nan
        )
        nested_body_range_pct = (
            max(close[i] - open_[i], 0.0) / max(candle_range[i], 1e-12) * 100.0
        )
        nested_close_location = (
            (close[i] - low[i]) / max(candle_range[i], 1e-12) * 100.0
        )
        nested_entry_range_pct = candle_range[i] / max(close[i], 1e-12) * 100.0
        nested_vwap_gap_pct = (
            (close[i] / vwap[i] - 1.0) * 100.0
            if not np.isnan(vwap[i]) and vwap[i] > 0.0
            else np.nan
        )
        nested_trend_aligned = (
            ema9[i] > ema20[i]
            and close[i] >= ema9[i]
            and close[i] >= ema20[i]
            and not np.isnan(vwap[i])
            and close[i] >= vwap[i]
        )
        nested_bar_quality = (
            close[i] > open_[i]
            and nested_close_location >= 70.0
            and nested_body_range_pct >= 50.0
            and not np.isnan(nested_volume_ratio)
            and nested_volume_ratio >= 1.15
            and not np.isnan(nested_range_ratio)
            and nested_range_ratio >= 1.15
            and nested_trend_aligned
        )
        if nested_bar_quality:
            # Compact sequences use the same forward market story as the
            # main detector.  Freeze a price from defended support first,
            # then require a bearish close through that exact price, a
            # wick-confirmed retest from below, and finally a close above all
            # of those rejection highs.  Never manufacture support from the
            # later resistance candles themselves.
            best_nested = None
            for d in range(i - 2, max(-1, i - 7), -1):
                if d < 1 or close[d] >= open_[d]:
                    continue
                nested_break_range = max(high[d] - low[d], 1e-12)
                nested_break_body_range_pct = max(open_[d] - close[d], 0.0) / nested_break_range * 100.0
                nested_controlled_extension = (
                    not np.isnan(nested_vwap_gap_pct)
                    and (nested_entry_range_pct <= 15.0 or nested_vwap_gap_pct <= 25.0)
                    and (nested_vwap_gap_pct <= 40.0 or nested_break_body_range_pct >= 60.0)
                )
                if not nested_controlled_extension:
                    continue

                resistance_stage = np.arange(d + 1, i)
                if len(resistance_stage) == 0:
                    continue

                for anchor_i in range(d - 1, max(-1, d - 11), -1):
                    frozen_support = low[anchor_i]
                    if frozen_support <= 0.0:
                        continue

                    support_start = max(0, d - 10)
                    for boundary_i in range(d - 1, support_start - 1, -1):
                        if close[boundary_i] < frozen_support:
                            support_start = boundary_i + 1
                            break
                    support_window = np.arange(support_start, d)
                    if len(support_window) == 0:
                        continue
                    support_mask = (
                        (np.abs(low[support_window] / frozen_support - 1.0) <= 0.035)
                        & (close[support_window] >= frozen_support * 0.97)
                    )
                    support_touch_indices = support_window[support_mask]
                    if len(support_touch_indices) < 2:
                        continue

                    # The line belongs to the selected support bar.  Do not
                    # slide it down to the lowest candle in a loose cluster:
                    # that recreates the same hindsight error with different
                    # data.  The most recent touch must defend this exact
                    # frozen price, within a tight compact-shelf tolerance.
                    newest_support = int(support_touch_indices.max())
                    newest_support_distance_pct = abs(
                        low[newest_support] / frozen_support - 1.0
                    ) * 100.0
                    if not (
                        close[d - 1] >= frozen_support
                        and close[d] < frozen_support
                        and newest_support_distance_pct <= 1.5
                    ):
                        continue

                    support_ranges = np.maximum(
                        high[support_touch_indices] - low[support_touch_indices],
                        1e-12,
                    )
                    support_bodies = np.maximum(
                        np.abs(
                            close[support_touch_indices]
                            - open_[support_touch_indices]
                        ),
                        1e-12,
                    )
                    support_lower_wicks = (
                        np.minimum(
                            open_[support_touch_indices],
                            close[support_touch_indices],
                        )
                        - low[support_touch_indices]
                    )
                    support_close_locations = (
                        (close[support_touch_indices] - low[support_touch_indices])
                        / support_ranges
                        * 100.0
                    )
                    support_range_ratios = np.array([
                        support_ranges[pos] / prior_three_range[index]
                        if not np.isnan(prior_three_range[index])
                        and prior_three_range[index] > 0.0
                        else np.nan
                        for pos, index in enumerate(support_touch_indices)
                    ])
                    defended_support = (
                        (support_lower_wicks / support_ranges * 100.0 >= 10.0)
                        & (
                            (support_lower_wicks / support_bodies * 100.0 >= 50.0)
                            | (support_close_locations >= 75.0)
                        )
                        & (support_range_ratios <= 1.25)
                    )
                    # A distant wick elsewhere in a long loose cluster cannot
                    # validate the price that actually broke.  Defense must
                    # appear among the last three touches before breakdown.
                    newest_support_position = int(
                        np.where(support_touch_indices == newest_support)[0][-1]
                    )
                    nested_support_has_buyer_defense = bool(
                        defended_support[newest_support_position]
                    )
                    if not nested_support_has_buyer_defense:
                        continue

                    support_bar_reaches_trend = (
                        high[newest_support] >= ema9[newest_support]
                        and high[newest_support] >= ema20[newest_support]
                        and not np.isnan(vwap[newest_support])
                        and high[newest_support] >= vwap[newest_support]
                    )
                    if not support_bar_reaches_trend:
                        continue

                    # This is the newest defended price that the breakdown
                    # actually crossed. It is authoritative for this sequence;
                    # do not fall back to an older, lower line merely because
                    # the current candle failed to reclaim the real one.

                    contact_mask = (
                        (high[resistance_stage] >= frozen_support * 0.96)
                        & (close[resistance_stage] <= frozen_support * 1.005)
                        & (close[resistance_stage] >= frozen_support * 0.92)
                    )
                    resistance_touch_indices = resistance_stage[contact_mask]
                    if len(resistance_touch_indices) < 1:
                        break
                    resistance_ranges = np.maximum(
                        high[resistance_touch_indices]
                        - low[resistance_touch_indices],
                        1e-12,
                    )
                    resistance_upper_wicks = (
                        high[resistance_touch_indices]
                        - np.maximum(
                            open_[resistance_touch_indices],
                            close[resistance_touch_indices],
                        )
                    )
                    if not np.any(
                        resistance_upper_wicks / resistance_ranges * 100.0
                        >= 15.0
                    ):
                        break
                    resistance_high = float(high[resistance_touch_indices].max())
                    if close[i] <= max(resistance_high, frozen_support):
                        break

                    oldest_support = int(support_touch_indices.min())
                    nested_has_nearby_expansion_anchor = False
                    for expansion_i in range(
                        max(0, oldest_support - 3), oldest_support
                    ):
                        expansion_range = max(
                            high[expansion_i] - low[expansion_i], 1e-12
                        )
                        expansion_body_pct = (
                            max(close[expansion_i] - open_[expansion_i], 0.0)
                            / expansion_range
                            * 100.0
                        )
                        expansion_close_location = (
                            (close[expansion_i] - low[expansion_i])
                            / expansion_range
                            * 100.0
                        )
                        expansion_volume_ratio = (
                            volume[expansion_i] / volume_ma[expansion_i]
                            if not np.isnan(volume_ma[expansion_i])
                            and volume_ma[expansion_i] > 0.0
                            else np.nan
                        )
                        if (
                            expansion_body_pct >= 60.0
                            and expansion_close_location >= 75.0
                            and not np.isnan(expansion_volume_ratio)
                            and expansion_volume_ratio >= 1.15
                        ):
                            nested_has_nearby_expansion_anchor = True
                            break

                    higher = [
                        candidate.rejection_high for candidate in active
                        if candidate.rejection_indices
                        and not np.isnan(candidate.rejection_high)
                        and candidate.support_high > frozen_support
                        and candidate.rejection_high > close[i]
                        and (candidate.rejection_high / frozen_support - 1.0) * 100.0 >= 1.0
                        and (candidate.rejection_high / frozen_support - 1.0) * 100.0 <= 15.0
                    ]
                    nearest_higher = min(higher) if higher else np.nan
                    blocker_gap_pct = (
                        (nearest_higher / close[i] - 1.0) * 100.0
                        if not np.isnan(nearest_higher) and close[i] > 0.0
                        else np.nan
                    )
                    if (
                        (higher and not nested_has_nearby_expansion_anchor)
                        or (higher and blocker_gap_pct > 1.0)
                    ):
                        break

                    candidate_record = (
                        len(resistance_touch_indices),
                        len(support_touch_indices),
                        frozen_support,
                        nearest_higher,
                        d,
                        tuple(int(x) for x in support_touch_indices),
                        tuple(int(x) for x in resistance_touch_indices),
                    )
                    if best_nested is None or candidate_record[:2] > best_nested[:2]:
                        best_nested = candidate_record
                    break

            if best_nested is not None:
                _, _, lower_resistance, higher_resistance, nested_break_i, nested_support_indices, nested_resistance_indices = best_nested
                if debug_clocks and current_clock in debug_clocks:
                    print(
                        "DEBUG_NESTED", current_clock,
                        "lower", round(lower_resistance, 4),
                        "higher", round(higher_resistance, 4),
                        "break", pd.Timestamp(time[nested_break_i]).strftime("%H:%M"),
                        "supports", [pd.Timestamp(time[x]).strftime("%H:%M") for x in nested_support_indices],
                        "resistance", [pd.Timestamp(time[x]).strftime("%H:%M") for x in nested_resistance_indices],
                    )
                evidence_score = nested_volume_ratio * nested_range_ratio
                same_blocker = (
                    not np.isnan(last_nested_blocking_resistance)
                    and not np.isnan(higher_resistance)
                    and abs(higher_resistance / last_nested_blocking_resistance - 1.0) <= 0.035
                )
                prior_setup_age = (
                    i - setup_records[-1]["time_index"]
                    if setup_records else None
                )
                direct_nested_entry_condition = (
                    (
                        np.isnan(higher_resistance)
                        and prior_setup_age is not None
                        and 2 <= prior_setup_age <= 20
                    )
                    or (
                        not np.isnan(higher_resistance)
                        and high[i] >= higher_resistance
                        and close[i] >= higher_resistance * 0.995
                        and nested_volume_ratio >= 2.0
                        and nested_body_range_pct >= 75.0
                        and nested_close_location >= 85.0
                    )
                )
                resolved_nested_ceiling = (
                    higher_resistance
                    if not np.isnan(higher_resistance)
                    else lower_resistance
                )
                repeats_resolved_nested_layer = (
                    direct_nested_entry_condition
                    and last_nested_direct_entry_index is not None
                    and i - last_nested_direct_entry_index <= 1
                    and not np.isnan(last_nested_direct_entry_lower)
                    and not np.isnan(last_nested_direct_entry_ceiling)
                    and lower_resistance
                    >= last_nested_direct_entry_lower * (1.0 - support_tolerance)
                    and lower_resistance
                    <= last_nested_direct_entry_ceiling * (1.0 + support_tolerance)
                )
                direct_nested_entry = (
                    direct_nested_entry_condition
                    and not repeats_resolved_nested_layer
                )
                if direct_nested_entry:
                    support_defense_scores = {
                        support_i: (
                            min(open_[support_i], close[support_i])
                            - low[support_i]
                        ) / max(high[support_i] - low[support_i], 1e-12)
                        for support_i in nested_support_indices
                    }
                    strongest_support_i = max(
                        nested_support_indices,
                        key=lambda support_i: support_defense_scores[support_i],
                    )
                    signals.append({
                        "time": pd.Timestamp(time[i]),
                        "support_low": lower_resistance,
                        "support_high": lower_resistance,
                        "flip_level": lower_resistance,
                        "support_start": pd.Timestamp(time[strongest_support_i]),
                        "support_end": pd.Timestamp(time[strongest_support_i]),
                        "break": pd.Timestamp(time[nested_break_i]),
                        "resistance": lower_resistance,
                        "rejections": ",".join(pd.Timestamp(time[j]).strftime("%H:%M") for j in nested_resistance_indices),
                        "touches": len(nested_support_indices),
                        "advance_pct": np.nan,
                        "volume_x": nested_volume_ratio,
                        "body_x": np.nan,
                        "close_location": nested_close_location,
                        "stage_bars": len(nested_resistance_indices),
                        "stage_quiet_bars": int(sum(volume[j] < volume_ma[j] for j in nested_resistance_indices)),
                        "stage_quiet_pct": float(np.mean([volume[j] < volume_ma[j] for j in nested_resistance_indices]) * 100.0),
                        "breakdown_volume_x": volume[nested_break_i] / volume_ma[nested_break_i] if volume_ma[nested_break_i] > 0 else np.nan,
                        "breakdown_body_range_pct": nested_break_body_range_pct,
                        "breakdown_close_from_low_pct": (close[nested_break_i] - low[nested_break_i]) / max(high[nested_break_i] - low[nested_break_i], 1e-12) * 100.0,
                        "source": "nested-direct",
                        "same_bar_blockers": 0,
                        "entry_distance_from_support_pct": (close[i] / lower_resistance - 1.0) * 100.0,
                        "resistance_bullish_pct": float(np.mean([close[j] > open_[j] for j in nested_resistance_indices]) * 100.0),
                        "long_volume_x": volume[i] / long_volume_ma[i] if not np.isnan(long_volume_ma[i]) and long_volume_ma[i] > 0 else np.nan,
                        "ema20_gap_pct": (close[i] / ema20[i] - 1.0) * 100.0,
                        "rising_ema_context": bool(i >= 5 and ema20[i] > ema20[i - 5]),
                        "behavior_quality_score": 0,
                        "resistance_attempts": 1,
                        "stage_bull_bear_volume_ratio": np.nan,
                        "entry_volume_vs_prior_three": nested_volume_ratio,
                        "nearest_known_overhead_pct": np.nan,
                        "known_overhead_low": np.nan,
                        "known_overhead_high": np.nan,
                        "known_overhead_touches": 0,
                        "known_overhead_advance": np.nan,
                        "known_overhead_start": pd.NaT,
                        "known_overhead_levels": "",
                        "nested_context": True,
                        "nested_evidence_time": (
                            setup_records[-1]["time"]
                            if prior_setup_age is not None
                            else pd.Timestamp(time[i])
                        ),
                        "nested_evidence_age": (
                            prior_setup_age if prior_setup_age is not None else 0
                        ),
                        "nested_cleared_resistance": lower_resistance,
                        "nested_blocking_resistance": np.nan,
                    })
                    last_signal_index = i
                    last_signal_resistance = lower_resistance
                    last_signal_support_low = lower_resistance
                    last_signal_support_high = lower_resistance
                    last_signal_resistance_stage_bars = len(nested_resistance_indices)
                    last_accepted_signal_index = i
                    last_accepted_signal_support_high = lower_resistance
                    last_accepted_signal_resistance_stage_bars = len(nested_resistance_indices)
                    last_accepted_entry_trend_tiers = confirmed_trend_tiers
                    accepted_signal_support_lows.append(lower_resistance)
                    lowest_since_signal = np.inf
                    last_nested_evidence_index = None
                    last_nested_cleared_resistance = np.nan
                    last_nested_blocking_resistance = np.nan
                    last_nested_evidence_score = np.nan
                    last_nested_direct_entry_index = i
                    last_nested_direct_entry_lower = lower_resistance
                    last_nested_direct_entry_ceiling = resolved_nested_ceiling
                    active = [
                        candidate
                        for candidate in active
                        if not (
                            candidate.support_high
                            >= lower_resistance * (1.0 - support_tolerance)
                            and candidate.support_low
                            <= resolved_nested_ceiling
                            * (1.0 + support_tolerance)
                        )
                    ]
                elif (
                    not np.isnan(higher_resistance)
                    and not repeats_resolved_nested_layer
                    and (
                        last_nested_evidence_index is None
                        or not same_blocker
                        or np.isnan(last_nested_evidence_score)
                        or evidence_score > last_nested_evidence_score
                    )
                ) and (
                    nested_support_indices[-1]
                    - nested_support_indices[0] + 1 <= 6
                ):
                    setup_records.append({
                        "time": pd.Timestamp(time[i]),
                        "time_index": i,
                        "lower_resistance": lower_resistance,
                        "higher_resistance": higher_resistance,
                    })
                    last_nested_evidence_index = i
                    last_nested_cleared_resistance = lower_resistance
                    last_nested_blocking_resistance = higher_resistance
                    last_nested_evidence_score = evidence_score

        # PARITY_RULE: candidate_creation
        # A breakdown bar must be bearish and must cross below a support shelf
        # that belongs to the uninterrupted episode immediately before it.
        if i < 2 or close[i] >= open_[i]:
            continue

        best = None
        for anchor_i in range(max(0, i - support_lookback), i):
            for anchor, source in ((low[anchor_i], "low"),):
                if anchor <= 0:
                    continue
                boundary = anchor * (1.0 - break_pct)
                if close[i - 1] < boundary or close[i] >= boundary:
                    continue

                # Keep only the current support episode. An older close below
                # the level ends all prior support evidence.
                episode_start = max(0, i - support_lookback)
                for j in range(i - 1, episode_start - 1, -1):
                    if close[j] < boundary:
                        episode_start = j + 1
                        break
                idx = np.arange(episode_start, i)
                if len(idx) == 0:
                    continue
                low_dist = np.abs(low[idx] / anchor - 1.0)
                dist = low_dist
                touch_ranges = np.maximum(high[idx] - low[idx], 1e-12)
                touch_bull_body_share = np.maximum(close[idx] - open_[idx], 0.0) / touch_ranges
                touch_range_pct = touch_ranges / np.maximum(close[idx], 1e-12)
                expansion_pass_through = (touch_bull_body_share >= 0.60) & (touch_range_pct >= 0.03)
                touch_mask = (
                    (dist <= support_tolerance)
                    & (close[idx] >= boundary)
                    & ~expansion_pass_through
                )
                touches = idx[touch_mask]
                if len(touches) < 2 or len(touches) > 30:
                    continue
                latest_support_i = int(touches.max())
                support_bar_reaches_trend = (
                    high[latest_support_i] >= ema9[latest_support_i]
                    and high[latest_support_i] >= ema20[latest_support_i]
                    and not np.isnan(vwap[latest_support_i])
                    and high[latest_support_i] >= vwap[latest_support_i]
                )
                if not support_bar_reaches_trend:
                    near_trend_mask = (
                        (high[touches] >= ema9[touches] * (1.0 - support_trend_touch_tolerance))
                        & (high[touches] >= ema20[touches] * (1.0 - support_trend_touch_tolerance))
                        & ~np.isnan(vwap[touches])
                        & (high[touches] >= vwap[touches] * (1.0 - support_trend_touch_tolerance))
                    )
                    touches = touches[near_trend_mask]
                    if len(touches) < 2:
                        continue
                    source = "near-ema-low"

                # Support must be current, not a distant cluster followed by a
                # separate price structure.
                if touches.max() < i - 120:
                    continue

                prior_start = max(0, int(touches.min()) - prior_advance_lookback)
                older = np.arange(prior_start, int(touches.min()))
                if len(older) < 5:
                    continue
                prior_low = low[older].min()
                advance_pct = (anchor / prior_low - 1.0) * 100.0
                if advance_pct < min_prior_advance:
                    continue

                touch_lows = low[touches]
                touch_bodies = body_floor[touches]
                lower_wicks = touch_bodies - touch_lows
                touch_body_sizes = np.maximum(np.abs(close[touches] - open_[touches]), 1e-12)
                defended_body_floor = float(np.min(touch_bodies))
                body_floor_spread_pct = (
                    (float(np.max(touch_bodies)) / defended_body_floor - 1.0) * 100.0
                    if defended_body_floor > 0 else np.inf
                )
                strong_wick_defenses = (
                    lower_wicks >= touch_body_sizes * 0.50
                )
                touch_ranges = np.maximum(candle_range[touches], 1e-12)
                touch_close_locations = (
                    (close[touches] - low[touches]) / touch_ranges * 100.0
                )
                touch_range_ratios = np.array([
                    touch_ranges[pos] / prior_three_range[index]
                    if not np.isnan(prior_three_range[index])
                    and prior_three_range[index] > 0.0
                    else np.nan
                    for pos, index in enumerate(touches)
                ])
                qualified_buyer_defense = (
                    (lower_wicks / touch_ranges * 100.0 >= 10.0)
                    & (
                        (lower_wicks / touch_body_sizes * 100.0 >= 50.0)
                        | (touch_close_locations >= 75.0)
                    )
                    & (touch_range_ratios <= 1.25)
                )
                meaningful_lower_wick_defense = bool(
                    np.any(qualified_buyer_defense)
                )
                decisive_buyer_defense = bool(np.any(
                    qualified_buyer_defense
                    & (
                        (lower_wicks / touch_ranges * 100.0 >= 20.0)
                        | (touch_close_locations >= 75.0)
                    )
                ))
                buyer_defense_count = int(np.sum(qualified_buyer_defense))
                # A repeatedly accepted closing/body floor is the actionable
                # support line when at least two candles probe below it and
                # recover with meaningful lower wicks. Absolute wick lows are
                # then failed auctions, not accepted support prices.
                body_floor_is_defended = (
                    len(touches) >= 3
                    and int(strong_wick_defenses.sum()) >= 2
                    and body_floor_spread_pct <= 0.65
                )
                support_low = float(defended_body_floor if body_floor_is_defended else np.min(touch_lows))
                support_high = float(np.mean(touch_bodies))
                if support_high < support_low:
                    support_high = support_low
                # The breakdown must clear the lower edge of the defended
                # zone. A close merely below candle bodies remains support.
                if close[i] >= support_low * (1.0 - break_pct):
                    continue

                widest = float(np.abs(low[touches] / anchor - 1.0).max())
                span = int(touches.max() - touches.min() + 1)
                near_ema_fallback = source == "near-ema-low"
                if near_ema_fallback and not (
                    len(touches) <= 3
                    and span <= 3
                    and i - int(touches.max()) <= 2
                    and advance_pct >= 30.0
                    and (open_[i] - close[i]) / max(high[i] - low[i], 1e-12) * 100.0 >= 80.0
                    and buyer_defense_count >= 2
                ):
                    continue
                if not meaningful_lower_wick_defense:
                    continue
                score = len(touches) * 1_000_000 - span * 10_000 - widest * 10_000_000 + support_high
                candidate = Candidate(
                    i, int(touches.min()), int(touches.max()), support_low,
                    support_high, len(touches), advance_pct, source,
                    support_buyer_defense=decisive_buyer_defense,
                )
                if best is None or score > best[0]:
                    best = (score, candidate)

        # A compact one-bar support pivot can break a few bars later.  It must
        # be a bullish higher-low pivot inside an established advance, and no
        # intervening close may already have broken its low.
        if i >= 2:
            pivot_i = i - 1
            anchor = low[pivot_i]
            pivot_range = max(high[pivot_i] - low[pivot_i], 1e-12)
            pivot_body_size = max(abs(close[pivot_i] - open_[pivot_i]), 1e-12)
            pivot_lower_wick = min(open_[pivot_i], close[pivot_i]) - low[pivot_i]
            pivot_lower_wick_pct = pivot_lower_wick / pivot_range * 100.0
            pivot_lower_wick_to_body_pct = pivot_lower_wick / pivot_body_size * 100.0
            pivot_close_location_pct = (
                (close[pivot_i] - low[pivot_i]) / pivot_range * 100.0
            )
            pivot_has_own_defense = (
                pivot_lower_wick_pct >= 10.0
                and pivot_lower_wick_to_body_pct >= 50.0
            )
            pivot_body_range_pct = pivot_body_size / pivot_range * 100.0
            compact_bearish_buyer_defense = (
                close[pivot_i] <= open_[pivot_i]
                and pivot_close_location_pct < 25.0
                and pivot_body_range_pct <= 25.0
                and pivot_has_own_defense
            )
            nearby_lower_wick_defense = False
            for defense_i in range(max(0, pivot_i - 2), pivot_i):
                defense_range = max(high[defense_i] - low[defense_i], 1e-12)
                defense_body_size = max(abs(close[defense_i] - open_[defense_i]), 1e-12)
                defense_lower_wick = min(open_[defense_i], close[defense_i]) - low[defense_i]
                defense_lower_wick_pct = defense_lower_wick / defense_range * 100.0
                defense_lower_wick_to_body_pct = (
                    defense_lower_wick / defense_body_size * 100.0
                )
                if (
                    abs(low[defense_i] / anchor - 1.0) <= support_tolerance
                    and abs(body_floor[defense_i] / body_floor[pivot_i] - 1.0)
                    <= 0.0065
                    and close[defense_i] >= anchor
                    and defense_lower_wick_pct >= 10.0
                    and defense_lower_wick_to_body_pct >= 50.0
                    and volume[pivot_i] >= volume[defense_i]
                ):
                    nearby_lower_wick_defense = True
                    break
            older = np.arange(max(0, pivot_i - prior_advance_lookback), pivot_i)
            if len(older) >= 5:
                advance_pct = (anchor / low[older].min() - 1.0) * 100.0
                pivot = (
                    (close[pivot_i] > open_[pivot_i]
                     or compact_bearish_buyer_defense)
                    and high[pivot_i] > high[pivot_i - 1]
                    and low[pivot_i] > low[pivot_i - 1]
                    # A candle closing near its low is rejection from above,
                    # not a defended support pivot, even when a tiny body makes
                    # its lower-wick/body ratio look artificially large.
                    and pd.Timestamp(time[i]) - pd.Timestamp(time[pivot_i]) <= pd.Timedelta(minutes=2)
                    and high[pivot_i] >= ema9[pivot_i] * (1.0 - support_trend_touch_tolerance)
                    and high[pivot_i] >= ema20[pivot_i] * (1.0 - support_trend_touch_tolerance)
                    and not np.isnan(vwap[pivot_i])
                    and high[pivot_i] >= vwap[pivot_i] * (1.0 - support_trend_touch_tolerance)
                    and close[i] < anchor
                    and advance_pct >= min_prior_advance
                )
                if pivot:
                    pivot_is_expansion_pass_through = (
                        pivot_body_size / pivot_range * 100.0 >= 75.0
                    )
                    pivot_buyer_defense_accepted = (
                        (
                            pivot_close_location_pct >= 25.0
                            and (
                                pivot_has_own_defense
                                or (
                                    nearby_lower_wick_defense
                                    and not pivot_is_expansion_pass_through
                                )
                            )
                        )
                        or compact_bearish_buyer_defense
                    )
                    prefer_upper_defended_pivot = (
                        best is not None
                        and compact_bearish_buyer_defense
                        and anchor > best[1].support_high
                    )
                    if best is None or prefer_upper_defended_pivot:
                        best = (
                            0.0,
                            Candidate(
                                i, pivot_i, pivot_i, anchor,
                                body_floor[pivot_i], 1, advance_pct,
                                "pivot-low",
                                support_buyer_defense=(
                                    pivot_buyer_defense_accepted
                                ),
                            ),
                        )

        for level in known_levels:
            crossed_known = close[i - 1] >= level.support_low and close[i] < level.support_low
            if crossed_known:
                reused = Candidate(
                    i, level.support_start, level.support_end,
                    level.support_low, level.support_high,
                    level.support_touches, level.prior_advance_pct,
                    "known-" + level.source,
                    support_buyer_defense=level.support_buyer_defense,
                )
                # Prefer a fresh defended structure from the current episode.
                # An old known level is only a fallback when no current support
                # shelf was found; otherwise it can replace the true nearby
                # support merely because its price is a few cents higher.
                recent_known_level = i - level.support_end <= support_lookback
                if best is None or (
                    recent_known_level
                    and reused.support_low > best[1].support_low
                ):
                    best = (10_000_000_000 + reused.support_low, reused)

        if best is not None:
            c = best[1]
            if (
                failed_expansion_detected_now
                and failed_expansion_breakout_index_now is not None
                and c.support_start >= failed_expansion_breakout_index_now
                and c.support_start <= i
            ):
                c.failed_expansion_origin = True
                c.failed_expansion_high = failed_expansion_high_now
            if not c.source.startswith("known-") and not any(
                abs(level.support_low / c.support_low - 1.0)
                <= support_tolerance
                for level in known_levels
            ):
                known_levels.append(Candidate(
                    c.break_index, c.support_start, c.support_end,
                    c.support_low, c.support_high, c.support_touches,
                    c.prior_advance_pct, c.source,
                    support_buyer_defense=c.support_buyer_defense,
                ))
                while len(known_levels) > 60:
                    known_levels.pop(0)
            # Each breakdown owns its own sequence. A later micro-break may not
            # erase an older unresolved support-to-resistance transition.
            while len(active) >= 60:
                active.pop(0)
            active.append(c)

    result = pd.DataFrame(signals)
    entry_times = {
        pd.Timestamp(x["time"]) for x in signals
    }
    result.attrs["setups"] = [
        x for x in setup_records if x["time"] not in entry_times
    ]
    result.attrs["failed_expansions"] = failed_expansion_records
    return result


# PARITY_DETECTION_END


def evaluate_corpus(directory: str) -> dict[str, object]:
    """Compare the corrected detector with its immediate prior behavior."""
    root = Path(directory)
    paths = sorted(root.glob("*1_*.csv"))
    required = {"time", "open", "high", "low", "close", "Volume", "Volume MA", "VWAP"}
    baseline_raw = 0
    corrected_raw = 0
    baseline_unique: set[tuple[str, pd.Timestamp]] = set()
    corrected_unique: set[tuple[str, pd.Timestamp]] = set()
    changed_dates: list[dict[str, object]] = []
    usable_files = 0
    file_dates = 0
    source_rows = 0

    for path in paths:
        try:
            data = pd.read_csv(path)
        except Exception:
            continue
        if not required.issubset(data.columns):
            continue
        data["time"] = (
            pd.to_datetime(
                data["time"], errors="coerce", format="mixed", utc=True,
            )
            .dt.tz_convert("America/New_York")
        )
        data = data.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
        if data.empty:
            continue
        usable_files += 1
        source_rows += len(data)
        symbol = path.name.split(",", 1)[0].split("_")[-1]
        dates = sorted(data.time.dt.strftime("%Y-%m-%d").unique())
        file_dates += len(dates)
        for date in dates:
            baseline = detect(
                str(path), date,
                resistance_acceptance_guard=False,
                data_override=data,
            )
            corrected = detect(
                str(path), date,
                resistance_acceptance_guard=True,
                data_override=data,
            )
            baseline_raw += len(baseline)
            corrected_raw += len(corrected)
            baseline_times = set(baseline.time) if len(baseline) else set()
            corrected_times = set(corrected.time) if len(corrected) else set()
            baseline_unique.update((symbol, pd.Timestamp(ts)) for ts in baseline_times)
            corrected_unique.update((symbol, pd.Timestamp(ts)) for ts in corrected_times)
            removed = sorted(baseline_times - corrected_times)
            added = sorted(corrected_times - baseline_times)
            if removed or added:
                changed_dates.append({
                    "file": path.name,
                    "symbol": symbol,
                    "date": date,
                    "removed": [pd.Timestamp(ts).strftime("%H:%M") for ts in removed],
                    "added": [pd.Timestamp(ts).strftime("%H:%M") for ts in added],
                })

    return {
        "files": usable_files,
        "file_dates": file_dates,
        "rows": source_rows,
        "baseline_raw": baseline_raw,
        "corrected_raw": corrected_raw,
        "raw_removed": baseline_raw - corrected_raw,
        "baseline_unique": len(baseline_unique),
        "corrected_unique": len(corrected_unique),
        "unique_removed": len(baseline_unique - corrected_unique),
        "unique_added": len(corrected_unique - baseline_unique),
        "changed_dates": changed_dates,
    }


# Curated behavioral regression matrix. Every user-labeled positive or false
# positive belongs here so later refinements cannot silently regress a case.
# These labels intentionally test semantic markers, not only whether the
# detector emitted some signal on the same day.
REGRESSION_CASES = [
    (
        "AMOD",
        fixture("amod_2026-10-02_11a4e.csv"),
        "2026-10-02",
        ["08:45", "08:53", "09:15"],
        ["07:32", "08:35", "16:04"],
    ),
    (
        "NXL",
        fixture("nxl_2026-10-01_840ce.csv"),
        "2026-10-01",
        ["09:24", "09:44"],
        ["10:51", "11:43", "11:55", "12:06"],
    ),
    ("CMCT", fixture("cmct_2026-09-30_69205.csv"), "2026-09-30", ["10:25"], ["10:19", "10:24"]),
    ("LGHL", fixture("lghl_2026-09-30_504a7.csv"), "2026-09-30", ["06:11", "06:43"], ["06:29"]),
    ("KNRX", fixture("knrx_2026-09-28_d348a.csv"), "2026-09-28", ["09:48"], ["11:45"]),
    ("WETO", fixture("weto_2026-08-17_ec6ab.csv"), "2026-08-17", ["10:12"], []),
    ("WFF", fixture("wff_2026-08-17_05f96.csv"), "2026-08-17", ["11:46"], []),
    ("ELPW", fixture("elpw_2026-09-25_de341.csv"), "2026-09-25", ["12:19"], []),
    ("APUS", fixture("apus_2026-09-25_a4f2d.csv"), "2026-09-25", ["08:53", "09:11"], []),
    ("APUS", fixture("apus_2026-09-24_47305.csv"), "2026-09-24", ["08:56", "09:22"], []),
    ("VEEE", fixture("veee_2026-07-13_dc82b.csv"), "2026-07-13", ["10:14", "10:54"], ["09:20", "10:39", "11:59", "16:27"]),
    ("SDOT", fixture("sdot_2026-06-26_45c94.csv"), "2026-06-26", ["11:54", "13:38", "14:16"], ["06:42", "06:51", "07:38", "08:47", "10:59", "14:25"]),
    ("BOXL", fixture("boxl_2026-08-12_fe518.csv"), "2026-08-12", ["14:40"], ["14:38", "14:39"]),
    ("SDEV", fixture("sdev_2026-09-29_51b3f.csv"), "2026-09-29", ["09:44"], ["09:58", "10:17"]),
    # Full 09/29 tape: preserve the three accepted entries and permanently lock
    # all four user-identified false entry markers out of the detector.
    ("SDEV", fixture("sdev_2026-09-29_138e9.csv"), "2026-09-29", ["09:44", "10:58", "12:08"], ["12:35", "12:45", "14:11", "14:57"]),
    ("SDEV", fixture("sdev_2026-10-02_138e9.csv"), "2026-10-02", [], ["12:31"]),
]

SETUP_REGRESSION_CASES = [
    # AMOD 08:45 is the completed reclaim, not merely nested evidence. 07:24
    # is a stale lower structure and must not survive as a setup marker.
    (
        "AMOD",
        fixture("amod_2026-10-02_11a4e.csv"),
        "2026-10-02",
        [],
        ["07:24", "08:45"],
    ),
    # These are nested reclaims without a fresh expansion-backed support
    # structure. They must not be rendered as SETUP markers.
    ("SDEV", fixture("sdev_2026-09-29_138e9.csv"), "2026-09-29", [], ["12:41", "15:05"]),
    # 11:03 used to be built backwards from the 10:58-11:02 highs.
    # The actual defended support was 10:54 near 3.06 and price never
    # reclaimed that frozen level, so no SETUP is allowed.
    ("SDEV", fixture("sdev_2026-09-30_a770d.csv"), "2026-09-30", [], ["11:03"]),
]

# These dates were explicitly labeled as complete: no unlisted entry is
# allowed. This is stricter than the required/forbidden matrix above and stops
# an unknown extra marker from hiding behind a green regression summary.
EXACT_ENTRY_CASES = [
    (
        "AMOD",
        fixture("amod_2026-10-02_11a4e.csv"),
        "2026-10-02",
        ["08:45", "08:53", "09:15"],
    ),
    (
        "NXL",
        fixture("nxl_2026-10-01_840ce.csv"),
        "2026-10-01",
        ["09:24", "09:44"],
    ),
    (
        "SDEV",
        fixture("sdev_2026-09-29_138e9.csv"),
        "2026-09-29",
        ["09:44", "10:58", "12:08"],
    ),
]

# Full 09/30 tape: 10:42 was produced only after the original level had
# already been accepted for several bars.  It is continuation, not a fresh
# support-to-resistance reclaim.
REGRESSION_CASES.append(
    ("SDEV", fixture("sdev_2026-09-30_7a5bd.csv"), "2026-09-30", [], ["10:42"])
)

# Full 10/02 tape: preserve the three user-confirmed entries, reject the
# exhausted/noisy levels, and lock the corrected upper support prices.
REGRESSION_CASES.append(
    (
        "SDEV",
        fixture("sdev_2026-10-02_7a5bd.csv"),
        "2026-10-02",
        ["09:42", "10:26", "16:11"],
        ["14:24", "14:33", "15:56"],
    )
)
SETUP_REGRESSION_CASES.append(
    (
        "SDEV",
        fixture("sdev_2026-10-02_7a5bd.csv"),
        "2026-10-02",
        ["15:32"],
        [],
    )
)


def test_curated_entry_regressions():
    report = []
    for symbol, path, date, positives, negatives in REGRESSION_CASES:
        result = detect(path, date)
        actual = set(result.time.dt.strftime("%H:%M")) if len(result) else set()
        assert set(positives) <= actual, (symbol, date, "missing", set(positives) - actual)
        assert not (set(negatives) & actual), (symbol, date, "unexpected", set(negatives) & actual)
        report.append({
            "symbol": symbol,
            "date": date,
            "fixture": Path(path).name,
            "required": positives,
            "forbidden": negatives,
            "actual": sorted(actual),
            "status": "PASS",
        })
    return report


def test_curated_setup_regressions():
    report = []
    for symbol, path, date, positives, negatives in SETUP_REGRESSION_CASES:
        result = detect(path, date)
        actual = {
            record["time"].strftime("%H:%M")
            for record in result.attrs.get("setups", [])
        }
        assert set(positives) <= actual, (
            symbol, date, "missing setup", set(positives) - actual
        )
        assert not (set(negatives) & actual), (
            symbol, date, "unexpected setup", set(negatives) & actual
        )
        report.append({
            "symbol": symbol,
            "date": date,
            "fixture": Path(path).name,
            "required": positives,
            "forbidden": negatives,
            "actual": sorted(actual),
            "status": "PASS",
        })
    return report


def test_exact_entry_regressions():
    report = []
    failures = []
    for symbol, path, date, expected in EXACT_ENTRY_CASES:
        result = detect(path, date)
        actual = set(result.time.dt.strftime("%H:%M")) if len(result) else set()
        missing = sorted(set(expected) - actual)
        unexpected = sorted(actual - set(expected))
        record = {
            "symbol": symbol,
            "date": date,
            "fixture": Path(path).name,
            "expected": expected,
            "actual": sorted(actual),
            "missing": missing,
            "unexpected": unexpected,
            "status": "PASS" if not missing and not unexpected else "FAIL",
        }
        report.append(record)
        if record["status"] == "FAIL":
            failures.append(record)
    assert not failures, ("exact marker mismatches", failures)
    return report


def test_ssm_exact_marker_regression():
    result = detect(
        fixture("ssm_2026-10-01_7b6c2.csv"),
        "2026-10-01",
    )
    entries = set(result.time.dt.strftime("%H:%M")) if len(result) else set()
    setups = {record["time"].strftime("%H:%M") for record in result.attrs.get("setups", [])}
    assert entries == {"15:45"}
    assert setups == {"15:31"}


def test_sdev_current_fresh_reclaim_guard():
    """09:42 is fresh; 09:32 is a delayed continuation marker."""
    path = fixture("sdev_2026-10-02_9f6d3.csv")
    data = pd.read_csv(path)
    data["time"] = pd.to_datetime(data["time"])
    data = data[
        data.time.dt.strftime("%Y-%m-%d") == "2026-10-02"
    ].sort_values("time").reset_index(drop=True)

    def passes_guard(clock: str) -> bool:
        matches = data.index[data.time.dt.strftime("%H:%M") == clock]
        assert len(matches) == 1, (clock, "missing fixture bar")
        index = int(matches[0])
        row = data.iloc[index]
        assert row["Strong Reclaim Entry"] == 1, (clock, "missing exported marker")
        support_high = float(row["Support Zone High"])
        accepted_bullish_closes = 0
        cursor = index - 1
        while cursor >= 0:
            prior = data.iloc[cursor]
            if prior.close > support_high and prior.close > prior.open:
                accepted_bullish_closes += 1
                cursor -= 1
            else:
                break
        resistance_attempts = int(row["Distinct Resistance Attempts"])
        return not (
            resistance_attempts == 1 and accepted_bullish_closes >= 2
        )

    assert passes_guard("09:42")
    assert not passes_guard("09:32")


def test_post_entry_maturity_guard():
    """Keep 12:08 and reject SDEV's three late weak continuations."""
    path = fixture("sdev_2026-09-29_138e9.csv")
    data = pd.read_csv(path)
    data["time"] = pd.to_datetime(data["time"])
    data = data[
        data.time.dt.strftime("%Y-%m-%d") == "2026-09-29"
    ].sort_values("time").reset_index(drop=True)

    confirmed_tiers = 0
    tier_peak = np.nan
    pullback_armed = False
    tiers_by_clock: dict[str, int] = {}
    for row in data.itertuples():
        if np.isnan(tier_peak):
            tier_peak = row.high
        elif not pullback_armed:
            tier_peak = max(tier_peak, row.high)
            if row.low <= tier_peak * 0.92:
                confirmed_tiers += 1
                pullback_armed = True
        elif row.high >= tier_peak * 1.05:
            tier_peak = row.high
            pullback_armed = False
        tiers_by_clock[row.time.strftime("%H:%M")] = confirmed_tiers

    accepted_tiers = tiers_by_clock["12:08"]
    assert not mature_post_entry_veto(accepted_tiers, accepted_tiers, 4)
    for clock, score in (("12:35", 0), ("12:45", 3), ("14:57", 4)):
        assert mature_post_entry_veto(
            tiers_by_clock[clock], accepted_tiers, score
        ), (clock, tiers_by_clock[clock], accepted_tiers, score)

    # VEEE's later valid continuation also forms two newer tiers, but its
    # complete 5/5 entry confirmation must remain eligible.
    assert not mature_post_entry_veto(9, 7, 5)


def test_expansion_and_entry_confidence_metrics():
    """Lock the full-leg WETO model and accepted SDEV support price."""
    weto = detect(
        fixture("weto_2026-08-17_ec6ab.csv"),
        "2026-08-17",
    )
    weto_entry = weto[weto.time.dt.strftime("%H:%M") == "10:12"]
    assert len(weto_entry) == 1
    weto_row = weto_entry.iloc[0]
    assert weto_row.expansion_start.strftime("%H:%M") == "09:33"
    assert weto_row.support_start.strftime("%H:%M") == "09:58"
    assert int(weto_row.expansion_strength_score) == 5
    assert int(weto_row.entry_confirmation_score) == 5
    assert int(weto_row.combined_confidence_score) == 11
    assert weto_row.entry_volume_vs_previous > 3.7
    assert weto_row.entry_volume_vs_prior_three > 2.8
    assert weto_row.volume_x > 3.9

    sdev = detect(
        fixture("sdev_2026-09-29_51b3f.csv"),
        "2026-09-29",
    )
    sdev_entry = sdev[sdev.time.dt.strftime("%H:%M") == "09:44"]
    assert len(sdev_entry) == 1
    sdev_row = sdev_entry.iloc[0]
    assert abs(float(sdev_row.support_low) - 1.79) < 1e-9
    assert abs(float(sdev_row.support_high) - 1.792725) < 1e-6


def test_sdev_full_dataset_support_selection_and_line_price():
    """Lock accepted SDEV flips and reject the unsupported 10:47 pivot."""
    sdev = detect(
        fixture("sdev_2026-09-29_6c7b8.csv"),
        "2026-09-29",
    )

    first = sdev[sdev.time.dt.strftime("%H:%M") == "09:44"]
    assert len(first) == 1
    first_row = first.iloc[0]
    assert abs(float(first_row.support_low) - 1.79) < 1e-9
    assert abs(float(first_row.flip_level) - 1.79) < 1e-9

    second = sdev[sdev.time.dt.strftime("%H:%M") == "10:58"]
    assert len(second) == 1
    second_row = second.iloc[0]
    assert second_row.support_start.strftime("%H:%M") == "10:48"
    assert second_row.support_end.strftime("%H:%M") == "10:49"
    assert abs(float(second_row.support_low) - 2.23) < 1e-9
    assert int(second_row.entry_confirmation_score) == 5
    assert abs(float(second_row.flip_level) - 2.18) <= 0.01

    assert "10:47" not in set(sdev.time.dt.strftime("%H:%M"))


def test_sdev_october_first_exact_sequence():
    """Only 09:33 qualifies; its shelf is 09:07-09:08."""
    result = detect(
        fixture("sdev_2026-10-01_7a5bd.csv"),
        "2026-10-01",
    )
    entries = set(result.time.dt.strftime("%H:%M")) if len(result) else set()
    assert entries == {"09:33"}
    row = result.iloc[0]
    assert row.support_start.strftime("%H:%M") == "09:07"
    assert row.support_end.strftime("%H:%M") == "09:08"
    assert row["break"].strftime("%H:%M") == "09:10"
    assert abs(float(row.support_low) - 3.67) < 1e-9
    assert "09:30" in str(row.rejections).split(",")


def test_sdev_october_second_exact_sequences():
    """Lock the corrected upper support lines and exhausted-level vetoes."""
    result = detect(
        fixture("sdev_2026-10-02_7a5bd.csv"),
        "2026-10-02",
    )

    first = result[result.time.dt.strftime("%H:%M") == "10:26"]
    assert len(first) == 1
    first_row = first.iloc[0]
    assert first_row.support_start.strftime("%H:%M") == "10:04"
    assert first_row.support_end.strftime("%H:%M") == "10:04"
    assert first_row["break"].strftime("%H:%M") == "10:05"
    assert abs(float(first_row.support_low) - 6.55) < 1e-9
    assert abs(float(first_row.flip_level) - 6.55) < 1e-9
    assert str(first_row.rejections).split(",")[-4:] == [
        "10:22", "10:23", "10:24", "10:25",
    ]

    second = result[result.time.dt.strftime("%H:%M") == "16:11"]
    assert len(second) == 1
    second_row = second.iloc[0]
    assert second_row.support_start.strftime("%H:%M") == "16:02"
    assert second_row.support_end.strftime("%H:%M") == "16:03"
    assert abs(float(second_row.support_low) - 7.60) < 1e-9
    assert abs(float(second_row.flip_level) - 7.60) < 1e-9

    entries = set(result.time.dt.strftime("%H:%M"))
    assert "14:24" not in entries
    assert "14:33" not in entries
    assert "15:56" not in entries
    failed_expansions = result.attrs.get("failed_expansions", [])
    target_failure = [
        record for record in failed_expansions
        if record["breakout"].strftime("%H:%M") == "14:24"
        and record["rejection"].strftime("%H:%M") == "14:27"
    ]
    assert len(target_failure) == 1
    assert abs(float(target_failure[0]["high"]) - 7.50) < 1e-9
    setups = {
        record["time"].strftime("%H:%M")
        for record in result.attrs.get("setups", [])
    }
    assert "15:32" in setups


def test_amod_october_second_exact_sequences():
    """AMOD has exactly three completed entries and no setup-only marker."""
    result = detect(
        fixture("amod_2026-10-02_11a4e.csv"),
        "2026-10-02",
    )
    entries = set(result.time.dt.strftime("%H:%M")) if len(result) else set()
    assert entries == {"08:45", "08:53", "09:15"}
    setups = {
        record["time"].strftime("%H:%M")
        for record in result.attrs.get("setups", [])
    }
    assert setups == set()

    first = result[result.time.dt.strftime("%H:%M") == "08:45"].iloc[0]
    assert first.support_start.strftime("%H:%M") == "08:37"
    assert first["break"].strftime("%H:%M") == "08:40"
    assert "08:43" in str(first.rejections).split(",")

    second = result[result.time.dt.strftime("%H:%M") == "08:53"].iloc[0]
    assert second.support_start.strftime("%H:%M") == "08:47"
    assert second["break"].strftime("%H:%M") == "08:49"
    assert str(second.rejections).split(",") == [
        "08:50", "08:51", "08:52",
    ]

    third = result[result.time.dt.strftime("%H:%M") == "09:15"].iloc[0]
    assert third.support_start.strftime("%H:%M") == "09:03"
    assert third.support_end.strftime("%H:%M") == "09:04"
    assert third["break"].strftime("%H:%M") == "09:07"
    assert str(third.rejections) == "09:09"
    assert abs(float(third.flip_level) - 3.00) < 1e-9
    assert float(third.volume_x) >= 2.5
    assert float(third.entry_volume_vs_prior_three) >= 3.0
    assert int(third.entry_confirmation_score) >= 4


def run_regression_suite() -> dict[str, object]:
    """Run every frozen behavioral and structural check exactly once."""
    entry_report = test_curated_entry_regressions()
    setup_report = test_curated_setup_regressions()
    exact_entry_report = test_exact_entry_regressions()
    test_ssm_exact_marker_regression()
    test_sdev_current_fresh_reclaim_guard()
    test_post_entry_maturity_guard()
    test_expansion_and_entry_confidence_metrics()
    test_sdev_full_dataset_support_selection_and_line_price()
    test_sdev_october_first_exact_sequence()
    test_sdev_october_second_exact_sequences()
    test_amod_october_second_exact_sequences()

    return {
        "positive_entry_fixtures":
            sum(len(case[3]) for case in REGRESSION_CASES) + 3,
        "negative_entry_fixtures":
            sum(len(case[4]) for case in REGRESSION_CASES) + 3,
        "positive_setup_fixtures":
            sum(len(case[3]) for case in SETUP_REGRESSION_CASES) + 1,
        "negative_setup_fixtures":
            sum(len(case[4]) for case in SETUP_REGRESSION_CASES),
        "entry_cases": entry_report,
        "setup_cases": setup_report,
        "exact_entry_cases": exact_entry_report,
        "structural_checks": [
            "SSM exact 15:31 SETUP / 15:45 ENTRY",
            "SDEV fresh-reclaim guard",
            "post-entry maturity guard",
            "expansion and entry confidence metrics",
            "SDEV accepted support and flip prices",
            "SDEV 10/01 exact 09:33-only sequence",
            "SDEV 10/02 exact sequence and line prices",
            "AMOD 10/02 exact 08:45 / 08:53 / 09:15 sequence",
        ],
    }


def assert_current_release_attested() -> None:
    """Prevent the legacy regression command from blessing stale Pine code."""
    attestation_path = Path(__file__).with_name(
        "frvp_validation_attestation.json"
    )
    pine_path = Path(__file__).with_name("frvp_new_indicator.pine")
    if not attestation_path.exists():
        raise AssertionError(
            "FRVP source is not attested; run verify_frvp_release.py --record"
        )
    attested = json.loads(attestation_path.read_text()).get("source", {})
    fixture_digest = hashlib.sha256()
    for path in sorted(FIXTURE_DIR.glob("*.csv")):
        fixture_digest.update(path.name.encode())
        fixture_digest.update(b"\0")
        fixture_digest.update(path.read_bytes())
        fixture_digest.update(b"\0")
    current = {
        "pine_sha256": hashlib.sha256(pine_path.read_bytes()).hexdigest(),
        "python_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "fixture_tree_sha256": fixture_digest.hexdigest(),
        "validation_build_id": VALIDATION_BUILD_ID,
    }
    changed = [
        key for key, value in current.items()
        if attested.get(key) != value
    ]
    if changed:
        raise AssertionError(
            "Behavioral tests passed, but the Pine/Python release is stale "
            f"({', '.join(changed)} changed). Run the full validation gate."
        )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?")
    ap.add_argument("date", nargs="?")
    ap.add_argument("--regression", action="store_true")
    ap.add_argument("--corpus")
    args = ap.parse_args()
    if args.corpus:
        summary = evaluate_corpus(args.corpus)
        changed_dates = summary.pop("changed_dates")
        print(summary)
        for record in changed_dates:
            print(record)
    elif args.regression:
        report = run_regression_suite()
        assert_current_release_attested()
        print(
            f"PASS: {report['positive_entry_fixtures']} positive and "
            f"{report['negative_entry_fixtures']} negative entry fixtures; "
            f"{report['positive_setup_fixtures']} positive and "
            f"{report['negative_setup_fixtures']} negative setup fixtures; "
            "SSM exact 15:31 SETUP / 15:45 ENTRY; "
            "post-entry maturity guard; confidence metrics; and both "
            "full-SDEV flip lines; exact 10/01 09:33-only sequence; and "
            "the corrected SDEV and AMOD 10/02 sequences"
        )
    else:
        if not args.path or not args.date:
            ap.error("path and date are required unless --regression is used")
        out = detect(args.path, args.date)
        print(Path(args.path).name, args.date, "signals", len(out))
        if not out.empty:
            for col in ("time", "support_start", "support_end", "break"):
                out[col] = out[col].dt.strftime("%H:%M")
            print(out.to_string(index=False))
