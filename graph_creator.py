import datetime
import pickle
import pandas as pd
import mplfinance as mpf

import common

TV_COLORS = {
    "bg": "#131722",
    "panel": "#131722",
    "grid": "#2a2e39",
    "text": "#d1d4dc",
    "bull": "#26a69a",
    "bear": "#ef5350",
    "ema_9": "#2196f3",
    "ema_20": "#ab47bc",
    "vwap": "#ffb74d",
    "macd": "#42a5f5",
    "signal": "#ff9800",
}

market_colors = mpf.make_marketcolors(
    up=TV_COLORS["bull"],
    down=TV_COLORS["bear"],
    edge="inherit",
    wick="inherit",
    volume="inherit",
)

tv_dark_style = mpf.make_mpf_style(
    base_mpf_style="nightclouds",
    marketcolors=market_colors,
    facecolor=TV_COLORS["bg"],
    figcolor=TV_COLORS["bg"],
    gridcolor=TV_COLORS["grid"],
    gridstyle="-",
    rc={
        "axes.labelcolor": TV_COLORS["text"],
        "xtick.color": TV_COLORS["text"],
        "ytick.color": TV_COLORS["text"],
        "text.color": TV_COLORS["text"],
        "axes.edgecolor": TV_COLORS["grid"],
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)

file_path = "model/training/data/ACXP-2026-03-10 14:43:00.json"

with open(file_path, "rb") as f:
    obj = pickle.load(f)

potential_bar: common.objects.BarData = obj["potential_confirmation_bar"]
all_bars: common.objects.BarData = obj["one_minute_timeframe_stock"].bars

potential_bar_04_am = datetime.datetime(
    year=potential_bar.bar_time.year,
    month=potential_bar.bar_time.month,
    day=potential_bar.bar_time.day,
    hour=4,
)

relevant_bars = sorted([
    bar_object
    for bar_object in all_bars
    if bar_object.bar_time >= potential_bar.bar_time
], key=lambda bar_obj: bar_obj.bar_time)

df = pd.DataFrame(bar_object.__dict__ for bar_object in relevant_bars)

# load your data
df.set_index("bar_time", inplace=True)

# mark the signal
df["signal"] = None
df["open"] = df["open_value"]

hist = df["histogram"]

hist_colors = []
for i in range(len(hist)):
    if i == 0:
        hist_colors.append("#787b86")
    elif hist.iloc[i] >= 0:
        hist_colors.append("#26a69a" if hist.iloc[i] > hist.iloc[i-1] else "#80cbc4")
    else:
        hist_colors.append("#ef5350" if hist.iloc[i] < hist.iloc[i-1] else "#ef9a9a")
# plot
apds = [
    mpf.make_addplot(df["ema_9"], panel=0, color="yellow", width=1),
    mpf.make_addplot(df["ema_20"], panel=0, color="purple", width=1),
    mpf.make_addplot(df["vwap"], panel=0, color="green", width=1.2),
    mpf.make_addplot(df["volume_average"], panel=1, color="yellow", width=1),
    mpf.make_addplot(df["macd"], panel=2, color="blue"),
    mpf.make_addplot(df["signal_line"], panel=2, color="orange"),
    mpf.make_addplot(df["histogram"], type="bar", panel=2, color=hist_colors),
]

fig, axes = mpf.plot(
    df,
    type='candle',
    volume=True,
    addplot=apds,
    style=tv_dark_style,
    panel_ratios=(4, 1.2, 1.8),
    figscale=1.4,
    figratio=(16, 9),
    title="TradingView-style Review Chart",
    ylabel="Price",
    ylabel_lower="Volume",
    returnfig=True,
)

axes[4].axhline(0, color="#787b86", linewidth=0.8, alpha=0.8)

# fig.show()
