import datetime
import os
import pickle
from typing import Any, Optional

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import common


class GraphCreator:
    DEFAULT_FRVP_ROWS = 100
    DEFAULT_FRVP_VALUE_AREA_PCT = 0.70

    @staticmethod
    def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
        try:
            if value is None:
                return default
            value = float(value)
            if np.isnan(value):
                return default
            return value
        except Exception:
            return default

    @staticmethod
    def _parse_range_datetime(value: Any, base_date: datetime.date) -> datetime.datetime:
        """Accept datetime, time, or strings like '09:53' / '2026-05-15 09:53:00'."""
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.time):
            return datetime.datetime.combine(base_date, value)
        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()

        if isinstance(value, str):
            value = value.strip()
            for fmt in ("%H:%M", "%H:%M:%S"):
                try:
                    parsed_time = datetime.datetime.strptime(value, fmt).time()
                    return datetime.datetime.combine(base_date, parsed_time)
                except ValueError:
                    pass

            parsed = pd.Timestamp(value)
            if pd.isna(parsed):
                raise ValueError(f"Could not parse FRVP range datetime: {value}")
            return parsed.to_pydatetime()

        raise TypeError(f"Unsupported FRVP range datetime type: {type(value).__name__}")

    @staticmethod
    def _fixed_row_edges(low: float, high: float, row_count: int) -> np.ndarray:
        if row_count <= 0:
            raise ValueError("row_count must be positive")
        if high <= low:
            high = low + max(abs(low) * 0.001, 0.0001)
        return np.linspace(low, high, row_count + 1)

    @staticmethod
    def _add_weighted_volume_to_rows(
        volume_by_row: np.ndarray,
        row_edges: np.ndarray,
        segment_low: float,
        segment_high: float,
        segment_volume: float,
    ) -> None:
        """Distribute segment_volume across fixed price rows by overlap amount."""
        if segment_volume <= 0:
            return
        if segment_low > segment_high:
            segment_low, segment_high = segment_high, segment_low
        if segment_high <= segment_low:
            # Point-like bar/segment: assign to containing row.
            idx = int(np.searchsorted(row_edges, segment_low, side="right") - 1)
            idx = max(0, min(len(volume_by_row) - 1, idx))
            volume_by_row[idx] += segment_volume
            return

        total_overlap = 0.0
        overlaps: list[tuple[int, float]] = []
        for i in range(len(volume_by_row)):
            row_low = row_edges[i]
            row_high = row_edges[i + 1]
            overlap = max(0.0, min(segment_high, row_high) - max(segment_low, row_low))
            if overlap > 0:
                overlaps.append((i, overlap))
                total_overlap += overlap

        if total_overlap <= 0:
            idx = int(np.searchsorted(row_edges, (segment_low + segment_high) / 2.0, side="right") - 1)
            idx = max(0, min(len(volume_by_row) - 1, idx))
            volume_by_row[idx] += segment_volume
            return

        for idx, overlap in overlaps:
            volume_by_row[idx] += segment_volume * (overlap / total_overlap)

    @classmethod
    def _calculate_frvp(
        cls,
        bars: list[Any],
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        row_count: int = DEFAULT_FRVP_ROWS,
        value_area_pct: float = DEFAULT_FRVP_VALUE_AREA_PCT,
    ) -> Optional[dict[str, Any]]:
        """Approximate TradingView-style FRVP with fixed rows and body-weighted OHLCV.

        Since 1-minute OHLCV does not contain true volume-at-price, this approximation:
        - uses fixed row count, similar to TradingView's Number of Rows mode
        - weights 70% of each candle volume to the candle body
        - weights 15% to the upper wick and 15% to the lower wick
        """
        profile_bars = sorted(
            [bar_object for bar_object in bars if start_time <= bar_object.bar_time <= end_time],
            key=lambda bar_object: bar_object.bar_time,
        )
        if not profile_bars:
            return None

        lows = [cls._safe_float(getattr(bar_object, "low", None), None) for bar_object in profile_bars]
        highs = [cls._safe_float(getattr(bar_object, "high", None), None) for bar_object in profile_bars]
        lows = [x for x in lows if x is not None]
        highs = [x for x in highs if x is not None]
        if not lows or not highs:
            return None

        profile_low = min(lows)
        profile_high = max(highs)
        row_edges = cls._fixed_row_edges(profile_low, profile_high, row_count)
        volume_by_row = np.zeros(row_count, dtype=float)

        for bar_object in profile_bars:
            open_value = cls._safe_float(getattr(bar_object, "open_value", None), None)
            high = cls._safe_float(getattr(bar_object, "high", None), None)
            low = cls._safe_float(getattr(bar_object, "low", None), None)
            close = cls._safe_float(getattr(bar_object, "close", None), None)
            volume = cls._safe_float(getattr(bar_object, "volume", None), 0.0) or 0.0

            if open_value is None or high is None or low is None or close is None or volume <= 0:
                continue

            body_low = min(open_value, close)
            body_high = max(open_value, close)
            lower_wick_low = low
            lower_wick_high = body_low
            upper_wick_low = body_high
            upper_wick_high = high

            body_volume = volume * 0.70
            lower_wick_volume = volume * 0.15
            upper_wick_volume = volume * 0.15

            cls._add_weighted_volume_to_rows(volume_by_row, row_edges, body_low, body_high, body_volume)
            cls._add_weighted_volume_to_rows(volume_by_row, row_edges, lower_wick_low, lower_wick_high, lower_wick_volume)
            cls._add_weighted_volume_to_rows(volume_by_row, row_edges, upper_wick_low, upper_wick_high, upper_wick_volume)

        total_volume = float(volume_by_row.sum())
        if total_volume <= 0:
            return None

        row_lows = row_edges[:-1]
        row_highs = row_edges[1:]
        row_mids = (row_lows + row_highs) / 2.0

        poc_idx = int(np.argmax(volume_by_row))
        target_volume = total_volume * value_area_pct
        included = {poc_idx}
        included_volume = float(volume_by_row[poc_idx])
        lower_idx = poc_idx - 1
        upper_idx = poc_idx + 1

        while included_volume < target_volume and (lower_idx >= 0 or upper_idx < row_count):
            lower_vol = volume_by_row[lower_idx] if lower_idx >= 0 else -1.0
            upper_vol = volume_by_row[upper_idx] if upper_idx < row_count else -1.0
            if upper_vol >= lower_vol:
                included.add(upper_idx)
                included_volume += float(upper_vol)
                upper_idx += 1
            else:
                included.add(lower_idx)
                included_volume += float(lower_vol)
                lower_idx -= 1

        included_indexes = sorted(included)
        val = float(row_lows[included_indexes[0]])
        vah = float(row_highs[included_indexes[-1]])
        poc = float(row_mids[poc_idx])

        return {
            "start_time": start_time,
            "end_time": end_time,
            "profile_low": float(profile_low),
            "profile_high": float(profile_high),
            "total_volume": total_volume,
            "row_lows": row_lows,
            "row_highs": row_highs,
            "row_mids": row_mids,
            "volume_by_row": volume_by_row,
            "val": val,
            "poc": poc,
            "vah": vah,
            "value_area_pct": value_area_pct,
            "row_count": row_count,
        }

    @staticmethod
    def _normalize_frvp_ranges(
        frvp_ranges: Optional[list[dict[str, Any]]],
        base_date: datetime.date,
    ) -> list[dict[str, Any]]:
        if not frvp_ranges:
            return []

        normalized: list[dict[str, Any]] = []
        for i, range_config in enumerate(frvp_ranges, start=1):
            start_time = GraphCreator._parse_range_datetime(range_config["start"], base_date)
            end_time = GraphCreator._parse_range_datetime(range_config["end"], base_date)
            if end_time < start_time:
                raise ValueError(f"FRVP range end is before start: {range_config}")
            normalized.append({
                "name": range_config.get("name") or f"FRVP {i}",
                "start_time": start_time,
                "end_time": end_time,
                "rows": int(range_config.get("rows", GraphCreator.DEFAULT_FRVP_ROWS)),
                "value_area_pct": float(range_config.get("value_area_pct", GraphCreator.DEFAULT_FRVP_VALUE_AREA_PCT)),
                "side": range_config.get("side"),
            })
        return normalized

    @classmethod
    def _add_frvp_to_figure(
        cls,
        fig: go.Figure,
        df: pd.DataFrame,
        profile: dict[str, Any],
        name: str,
        profile_index: int,
        frvp_side: str = "left",
    ) -> None:
        if df.empty:
            return

        x_min = df.index.min().to_pydatetime() if isinstance(df.index.min(), pd.Timestamp) else df.index.min()
        x_max = df.index.max().to_pydatetime() if isinstance(df.index.max(), pd.Timestamp) else df.index.max()
        chart_seconds = max(60.0, (x_max - x_min).total_seconds())

        # Draw the FRVP histogram on the requested side of the visible candles.
        # left  = bars sit before the first candle and extend rightward.
        # right = bars sit after the last candle and extend leftward.
        frvp_side = (frvp_side or "left").lower().strip()
        if frvp_side not in {"left", "right"}:
            raise ValueError("frvp_side must be either 'left' or 'right'")

        max_width_seconds = chart_seconds * 0.14
        gap_seconds = chart_seconds * (0.025 + profile_index * 0.18)

        # IMPORTANT:
        # annotation_position only moves the VAL/POC/VAH text label.
        # The FRVP histogram location is controlled by the rectangle x0/x1 values below.
        # left  = the row's RIGHT edge is anchored before the first candle; rows extend LEFT.
        # right = the row's LEFT edge is anchored after the last candle; rows extend RIGHT.
        if frvp_side == "left":
            profile_anchor = x_min - datetime.timedelta(seconds=gap_seconds)
        else:
            profile_anchor = x_max + datetime.timedelta(seconds=gap_seconds)

        max_volume = float(np.max(profile["volume_by_row"])) if len(profile["volume_by_row"]) else 0.0
        if max_volume <= 0:
            return

        for row_low, row_high, volume in zip(
            profile["row_lows"],
            profile["row_highs"],
            profile["volume_by_row"],
        ):
            if volume <= 0:
                continue
            width_seconds = max_width_seconds * (float(volume) / max_volume)
            if frvp_side == "left":
                # Draw before the first candle. The histogram grows leftward.
                row_x0 = profile_anchor - datetime.timedelta(seconds=width_seconds)
                row_x1 = profile_anchor
            else:
                # Draw after the last candle. The histogram grows rightward.
                row_x0 = profile_anchor
                row_x1 = profile_anchor + datetime.timedelta(seconds=width_seconds)
            in_value_area = profile["val"] <= float((row_low + row_high) / 2.0) <= profile["vah"]
            fill_color = "rgba(80, 140, 255, 0.32)" if in_value_area else "rgba(120, 123, 134, 0.22)"
            line_color = "rgba(80, 140, 255, 0.12)" if in_value_area else "rgba(120, 123, 134, 0.10)"
            fig.add_shape(
                type="rect",
                xref="x",
                yref="y",
                x0=row_x0,
                x1=row_x1,
                y0=float(row_low),
                y1=float(row_high),
                fillcolor=fill_color,
                line=dict(color=line_color, width=0.4),
                layer="below",
                row=1,
                col=1,
            )

        # Source range markers.
        fig.add_vrect(
            x0=profile["start_time"],
            x1=profile["end_time"],
            fillcolor="rgba(255, 193, 7, 0.06)",
            line_width=0,
            row=1,
            col=1,
        )

        level_specs = [
            ("VAL", profile["val"], "rgba(38, 166, 154, 0.95)", "dot"),  # green
            ("POC", profile["poc"], "rgba(255, 193, 7, 0.95)", "solid"), # yellow
            ("VAH", profile["vah"], "rgba(239, 83, 80, 0.95)", "dot"),  # red
        ]
        annotation_position = "left" if frvp_side == "left" else "right"
        for label, price, color, dash in level_specs:
            fig.add_hline(
                y=price,
                line_width=1,
                line_dash=dash,
                line_color=color,
                annotation_text=f"{name} {label}: {price:.4f}",
                annotation_position=annotation_position,
                row=1,
                col=1,
            )

        # Legend placeholder for profile info.
        fig.add_trace(
            go.Scatter(
                x=[profile_anchor],
                y=[profile["poc"]],
                mode="markers",
                marker=dict(size=8, color="rgba(255, 193, 7, 0.95)"),
                name=(
                    f"{name}: VAL {profile['val']:.4f} | "
                    f"POC {profile['poc']:.4f} | VAH {profile['vah']:.4f}"
                ),
                hovertemplate=(
                    f"{name}<br>"
                    f"Start: {profile['start_time']}<br>"
                    f"End: {profile['end_time']}<br>"
                    f"VAL: {profile['val']:.4f}<br>"
                    f"POC: {profile['poc']:.4f}<br>"
                    f"VAH: {profile['vah']:.4f}<br>"
                    f"Total volume: {profile['total_volume']:,.0f}"
                    "<extra></extra>"
                ),
            ),
            row=1,
            col=1,
        )

        # Extend the shared x-axis so the outside FRVP bars are visible.
        side_padding = datetime.timedelta(seconds=chart_seconds * (0.18 + 0.18 * profile_index))
        if frvp_side == "left":
            fig.update_xaxes(
                range=[x_min - side_padding, x_max],
                row=1,
                col=1,
            )
        else:
            fig.update_xaxes(
                range=[x_min, x_max + side_padding],
                row=1,
                col=1,
            )

    @staticmethod
    def create_interactive_chart(
        symbol: str,
        potential_confirmation_bar: common.objects.BarData,
        one_minute_timeframe_stock: common.objects.Stock,
        score: common.objects.Score = None,
        include_extended_hours: bool = False,
        chart_start_time: Any = None,
        chart_end_time: Any = None,
        frvp_ranges: Optional[list[dict[str, Any]]] = None,
        frvp_rows: int = DEFAULT_FRVP_ROWS,
        frvp_value_area_pct: float = DEFAULT_FRVP_VALUE_AREA_PCT,
        frvp_side: str = "left",
    ) -> go.Figure:
        base_date = potential_confirmation_bar.bar_time.date()
        same_day_market_open = datetime.datetime(
            year=potential_confirmation_bar.bar_time.year,
            month=potential_confirmation_bar.bar_time.month,
            day=potential_confirmation_bar.bar_time.day,
            hour=9,
            minute=30,
        )

        same_day_market_close = datetime.datetime(
            year=potential_confirmation_bar.bar_time.year,
            month=potential_confirmation_bar.bar_time.month,
            day=potential_confirmation_bar.bar_time.day,
            hour=16,
        )

        if chart_start_time is not None:
            chart_start = GraphCreator._parse_range_datetime(chart_start_time, base_date)
        elif include_extended_hours:
            chart_start = datetime.datetime.combine(base_date, datetime.time(4, 0))
        else:
            chart_start = same_day_market_open

        if chart_end_time is not None:
            chart_end = GraphCreator._parse_range_datetime(chart_end_time, base_date)
        elif include_extended_hours:
            chart_end = datetime.datetime.combine(base_date, datetime.time(20, 0))
        else:
            chart_end = same_day_market_close

        # If FRVP ranges are outside the chart range, expand the chart so the source range is visible.
        normalized_frvp_ranges = GraphCreator._normalize_frvp_ranges(frvp_ranges, base_date)
        for range_config in normalized_frvp_ranges:
            chart_start = min(chart_start, range_config["start_time"])
            chart_end = max(chart_end, range_config["end_time"])

        relevant_bars = sorted([
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if (
                bar_object.bar_time.date() == base_date
                and chart_start <= bar_object.bar_time <= chart_end
            )
        ], key=lambda bar_obj: bar_obj.bar_time)

        if not relevant_bars:
            raise ValueError(f"No bars found for {symbol} between {chart_start} and {chart_end}")

        df = pd.DataFrame(bar_object.__dict__ for bar_object in relevant_bars)
        df.set_index("bar_time", inplace=True)

        hist = df["histogram"]
        hist_colors = []

        for i in range(len(hist)):
            if i == 0:
                hist_colors.append("#787b86")
            elif hist.iloc[i] >= 0:
                hist_colors.append("#26a69a" if hist.iloc[i] > hist.iloc[i - 1] else "#80cbc4")
            else:
                hist_colors.append("#ef5350" if hist.iloc[i] < hist.iloc[i - 1] else "#ef9a9a")

        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.62, 0.18, 0.20],
            subplot_titles=("Price", "Volume", "MACD"),
        )

        # Candles
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["open_value"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name="Candles",
                increasing_line_color="#26a69a",
                decreasing_line_color="#ef5350",
                customdata=np.stack([
                    df["volume"],
                    df["volume_average"],
                    df["ema_9"],
                    df["ema_20"],
                    df["vwap"],
                ], axis=-1),
                hovertemplate=(
                    "H: %{high:.2f}<br>"
                    "C: %{close:.2f}<br>"
                    "O: %{open:.2f}<br>"
                    "L: %{low:.2f}<br>"
                    "Volume: %{customdata[0]:,.0f}<br>"
                    "Vol Avg: %{customdata[1]:,.0f}<br>"
                    "EMA 9: %{customdata[2]:.2f}<br>"
                    "EMA 20: %{customdata[3]:.2f}<br>"
                    "VWAP: %{customdata[4]:.2f}"
                    "<extra></extra>"
                ),
            ),
            row=1,
            col=1,
        )

        # EMA / VWAP
        fig.add_trace(go.Scatter(x=df.index, y=df["ema_9"], name="EMA 9", line=dict(color="#edf40b", width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["ema_20"], name="EMA 20", line=dict(color="#ab47bc", width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(mode="markers", x=df.index, y=df["vwap"], name="VWAP", marker=dict(color="#18eb11", size=3)), row=1, col=1)

        # FRVP overlays.
        all_day_bars = sorted(
            [bar_object for bar_object in one_minute_timeframe_stock.bars if bar_object.bar_time.date() == base_date],
            key=lambda bar_object: bar_object.bar_time,
        )
        for i, range_config in enumerate(normalized_frvp_ranges):
            profile = GraphCreator._calculate_frvp(
                bars=all_day_bars,
                start_time=range_config["start_time"],
                end_time=range_config["end_time"],
                row_count=range_config.get("rows") or frvp_rows,
                value_area_pct=range_config.get("value_area_pct") or frvp_value_area_pct,
            )
            if profile is not None:
                GraphCreator._add_frvp_to_figure(
                    fig=fig,
                    df=df,
                    profile=profile,
                    name=range_config["name"],
                    profile_index=i,
                    frvp_side=range_config.get("side", frvp_side),
                )

        # Volume
        volume_colors = np.where(df["close"] >= df["open_value"], "#26a69a", "#ef5350")
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["volume"],
                name="Volume",
                marker_color=volume_colors,
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["volume_average"],
                name="Volume Avg",
                line=dict(color="#fbc02d", width=1),
            ),
            row=2,
            col=1,
        )

        # MACD
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["histogram"],
                name="Histogram",
                marker_color=hist_colors,
            ),
            row=3,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["macd"],
                name="MACD",
                line=dict(color="#42a5f5", width=1),
            ),
            row=3,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["signal_line"],
                name="Signal Line",
                line=dict(color="#ff9800", width=1),
            ),
            row=3,
            col=1,
        )

        signal_time = pd.Timestamp(str(potential_confirmation_bar.bar_time))
        if signal_time in df.index:
            signal_price = df.loc[signal_time, "close"]

            fig.add_vline(
                x=signal_time,
                line_width=1,
                line_dash="dash",
                line_color="yellow",
            )

            fig.add_trace(
                go.Scatter(
                    x=[signal_time],
                    y=[signal_price],
                    mode="markers",
                    name=f"Signal {score.score}" if score is not None else "Signal",
                    marker=dict(
                        size=14,
                        color="yellow",
                        symbol="triangle-up",
                        line=dict(color="black", width=1),
                    ),
                ),
                row=1,
                col=1,
            )

        title = f"{symbol} Trade Review. Bar Time: {signal_time}"
        if score is not None:
            title += f" | Score: {score.score}"

        fig.update_layout(
            title=title,
            template="plotly_dark",
            height=900,
            width=1500,
            xaxis_rangeslider_visible=False,
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="rgba(19,23,34,0.75)",
                font_size=12,
                font_color="#d1d4dc",
                bordercolor="#2a2e39",
            ),
            paper_bgcolor="#131722",
            plot_bgcolor="#131722",
            font=dict(color="#d1d4dc"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
            ),
            overwrite=True,
        )

        fig.update_xaxes(
            showgrid=True,
            gridcolor="#2a2e39",
            rangeslider_visible=False,
        )

        fig.update_yaxes(
            showgrid=True,
            gridcolor="#2a2e39",
        )

        html_file_path = f"model/training/data/charts/{symbol}-{str(potential_confirmation_bar.bar_time)}.html"
        os.makedirs(os.path.dirname(html_file_path), exist_ok=True)
        fig.write_html(html_file_path)

        return fig


if __name__ == '__main__':
    FILE_PATH = "model/training/data/PMAX-2026-05-06 10:18:00.json"
    with open(FILE_PATH, "rb") as f:
        obj = pickle.load(f)
        stock: common.objects.Stock = obj["day_timeframe_stock"]

        fig = GraphCreator.create_interactive_chart(
            symbol=stock.symbol_name,
            potential_confirmation_bar=obj["potential_confirmation_bar"],
            one_minute_timeframe_stock=obj["one_minute_timeframe_stock"],
            include_extended_hours=True,
            frvp_side="left",
            frvp_ranges=[
                {"name": "Main FRVP", "start": "04:00", "end": "09:29"},
            ],
        )
        fig.show()
