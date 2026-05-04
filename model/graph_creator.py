import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import common

class GraphCreator:
    @staticmethod
    def create_interactive_chart(
        symbol: str,
        potential_confirmation_bar: common.objects.BarData,
        one_minute_timeframe_stock: common.objects.Stock,
        score: common.objects.Score = None,
    ):
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

        relevant_bars = sorted([
            bar_object
            for bar_object in one_minute_timeframe_stock.bars
            if same_day_market_open <= bar_object.bar_time <= same_day_market_close
        ], key=lambda bar_obj: bar_obj.bar_time)

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
                bgcolor="rgba(19,23,34,0.75)",  # semi-transparent
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

        fig.write_html(html_file_path)
