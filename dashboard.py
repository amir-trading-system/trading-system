#!/usr/bin/env python3
"""Interactive trading-calendar dashboard.

Place this script beside ``Trades_with_PL_Last_Month.csv`` and run:

    python3 trade_scheduler.py

The app uses only Python's standard library. It reads the CSV when the browser
loads the data and whenever the Reload CSV button is pressed.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import threading
import webbrowser
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse

from ibkr_flex import FlexSyncError, FlexSyncManager


DEFAULT_CSV_NAME = "Trades_with_PL_Last_Month.csv"
FLOAT_CACHE_NAME = "yahoo_symbol_cache.json"
FLOAT_CACHE_VERSION = 3
FLOAT_CACHE_MAX_AGE = timedelta(days=7)
FLOAT_MISSING_MAX_AGE = timedelta(hours=12)
MAX_FLOAT_SYMBOLS_PER_REQUEST = 20

DATE_COLUMN_ALIASES = (
    "TradeDate",
    "Trade Date",
    "Date",
    "Date/Time",
    "DateTime",
    "TradeDateTime",
    "ExecutionDate",
    "ExecDate",
    "OrderDate",
    "ActivityDate",
)
SYMBOL_COLUMN_ALIASES = ("Symbol", "Ticker", "UnderlyingSymbol")
PNL_COLUMN_ALIASES = (
    "FifoPnlRealized",
    "Fifo PnL Realized",
    "Realized P&L",
    "Realized P/L",
    "RealizedPnL",
    "RealizedPL",
    "Realized Profit Loss",
    "Profit/Loss",
    "Net P&L",
    "P&L",
    "PnL",
)
TIME_COLUMN_ALIASES = (
    "DateTime",
    "ExecutionDateTime",
    "TradeDateTime",
    "TransactionDateTime",
    "ExecutionTime",
    "TradeTime",
    "TransactionTime",
    "OrderTime",
    "Time",
)


class TradeDataError(ValueError):
    """Raised when the input file cannot be interpreted as a trades export."""


class YahooMetadataError(RuntimeError):
    """Raised when Yahoo Finance cannot provide symbol metadata."""


def yahoo_symbol(symbol: str) -> str:
    """Convert common broker share-class notation to Yahoo's notation."""
    return symbol.strip().upper().replace(" ", "-").replace(".", "-")


class YahooFinanceMetadataClient:
    """Read current company statistics through yfinance."""

    def __init__(self) -> None:
        try:
            import yfinance as yf  # type: ignore[import-not-found]
        except ImportError:
            self.yf = None
        else:
            self.yf = yf

    @staticmethod
    def numeric_value(value: Any) -> int | float | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(number):
            return None
        return int(number) if number.is_integer() else number

    @staticmethod
    def text_value(value: Any) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    def fetch_metadata(self, symbol: str) -> dict[str, Any]:
        if self.yf is None:
            raise YahooMetadataError(
                "Yahoo analysis requires yfinance. Install it with: "
                "python3 -m pip install yfinance"
            )
        try:
            information = self.yf.Ticker(yahoo_symbol(symbol)).get_info()
        except YahooMetadataError:
            raise
        except Exception as exc:
            raise YahooMetadataError(
                "yfinance could not retrieve this symbol from Yahoo Finance."
            ) from exc
        if not isinstance(information, dict) or not information:
            raise YahooMetadataError(
                "Yahoo Finance does not publish company data for this symbol."
            )
        average_volume_10d = information.get("averageVolume10days")
        if average_volume_10d is None:
            average_volume_10d = information.get("averageDailyVolume10Day")
        current_price = information.get("currentPrice")
        if current_price is None:
            current_price = information.get("regularMarketPrice")
        return {
            "float_shares": self.numeric_value(information.get("floatShares")),
            "shares_outstanding": self.numeric_value(
                information.get("sharesOutstanding")
            ),
            "market_cap": self.numeric_value(information.get("marketCap")),
            "average_volume": self.numeric_value(information.get("averageVolume")),
            "average_volume_10d": self.numeric_value(average_volume_10d),
            "short_percent_float": self.numeric_value(
                information.get("shortPercentOfFloat")
            ),
            "short_ratio": self.numeric_value(information.get("shortRatio")),
            "held_percent_insiders": self.numeric_value(
                information.get("heldPercentInsiders")
            ),
            "held_percent_institutions": self.numeric_value(
                information.get("heldPercentInstitutions")
            ),
            "beta": self.numeric_value(information.get("beta")),
            "current_price": self.numeric_value(current_price),
            "sector": self.text_value(information.get("sector")),
            "industry": self.text_value(information.get("industry")),
            "country": self.text_value(information.get("country")),
            "exchange": self.text_value(information.get("exchange")),
        }


class YahooMetadataStore:
    """Cache Yahoo company metadata so the dashboard makes few requests."""

    def __init__(self, cache_path: Path) -> None:
        self.cache_path = cache_path
        self.lock = threading.RLock()
        self.fetch_lock = threading.Lock()
        self.entries: dict[str, dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
            if payload.get("version") != FLOAT_CACHE_VERSION:
                self.entries = {}
                return
            entries = payload.get("symbols", {})
            if isinstance(entries, dict):
                self.entries = {
                    str(symbol).upper(): entry
                    for symbol, entry in entries.items()
                    if isinstance(entry, dict)
                }
        except (OSError, ValueError, TypeError):
            self.entries = {}

    def save(self) -> None:
        payload = {
            "version": FLOAT_CACHE_VERSION,
            "source": "Yahoo Finance",
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "symbols": self.entries,
        }
        temporary_path = self.cache_path.with_suffix(".tmp")
        try:
            temporary_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
            )
            temporary_path.replace(self.cache_path)
        except OSError:
            # Yahoo data can still be shown for this session if the cache folder
            # is read-only or temporarily unavailable.
            pass

    @staticmethod
    def is_fresh(entry: dict[str, Any]) -> bool:
        try:
            fetched_at = datetime.fromisoformat(str(entry["fetched_at"]))
            if fetched_at.tzinfo is None:
                fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        except (KeyError, TypeError, ValueError):
            return False
        maximum_age = FLOAT_CACHE_MAX_AGE if not entry.get("error") else FLOAT_MISSING_MAX_AGE
        return datetime.now(timezone.utc) - fetched_at <= maximum_age

    def get_many(
        self, symbols: Iterable[str], *, force_refresh: bool = False
    ) -> dict[str, Any]:
        requested: list[str] = []
        for symbol in symbols:
            cleaned = symbol.strip().upper()
            if (
                cleaned
                and len(cleaned) <= 32
                and re.fullmatch(r"[A-Z0-9.^=\-]+", cleaned)
                and cleaned not in requested
            ):
                requested.append(cleaned)
        requested = requested[:MAX_FLOAT_SYMBOLS_PER_REQUEST]

        with self.lock:
            missing = [
                symbol
                for symbol in requested
                if force_refresh
                or symbol not in self.entries
                or not self.is_fresh(self.entries[symbol])
            ]

        if missing:
            with self.fetch_lock:
                # Another request may have filled the cache while this one waited.
                with self.lock:
                    missing = [
                        symbol
                        for symbol in missing
                        if force_refresh
                        or symbol not in self.entries
                        or not self.is_fresh(self.entries[symbol])
                    ]
                client = YahooFinanceMetadataClient()
                session_error: str | None = None
                for symbol in missing:
                    fetched_at = datetime.now(timezone.utc).isoformat(
                        timespec="seconds"
                    )
                    if session_error:
                        entry = {
                            "fetched_at": fetched_at,
                            "error": session_error,
                        }
                    else:
                        try:
                            entry = client.fetch_metadata(symbol)
                            entry.update(
                                {"fetched_at": fetched_at, "error": None}
                            )
                        except YahooMetadataError as exc:
                            message = str(exc)
                            entry = {
                                "fetched_at": fetched_at,
                                "error": message,
                            }
                            if "requires yfinance" in message:
                                session_error = message
                    with self.lock:
                        self.entries[symbol] = entry
                with self.lock:
                    self.save()

        with self.lock:
            results = {
                symbol: self.entries.get(
                    symbol,
                    {
                        "fetched_at": None,
                        "error": "Yahoo company data is unavailable.",
                    },
                )
                for symbol in requested
            }
        return {
            "source": "Yahoo Finance",
            "cache_max_age_days": FLOAT_CACHE_MAX_AGE.days,
            "symbols": results,
        }


def normalized_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def resolve_header(
    headers: Iterable[str], aliases: Iterable[str], *, required: bool = False
) -> str | None:
    available = {normalized_header(header): header for header in headers}
    for alias in aliases:
        match = available.get(normalized_header(alias))
        if match is not None:
            return match
    if required:
        raise TradeDataError(
            "Missing required column. Expected one of: " + ", ".join(aliases)
        )
    return None


def parse_trade_date(value: str, row_number: int) -> datetime:
    cleaned = value.strip()
    formats = (
        "%Y%m%d",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%Y-%m-%d %H:%M:%S",
    )
    for date_format in formats:
        try:
            return datetime.strptime(cleaned, date_format)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TradeDataError(
            f"Row {row_number}: unsupported TradeDate value {value!r}."
        ) from exc


def parse_execution_datetime(
    value: str, fallback_date: datetime, row_number: int
) -> datetime | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    date_time_formats = (
        "%Y%m%d;%H%M%S",
        "%Y%m%d;%H%M",
        "%Y%m%d %H%M%S",
        "%Y%m%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
    )
    for date_time_format in date_time_formats:
        try:
            return datetime.strptime(cleaned, date_time_format)
        except ValueError:
            continue
    for time_format in ("%H:%M:%S", "%H:%M", "%H%M%S", "%H%M"):
        try:
            parsed_time = datetime.strptime(cleaned, time_format).time()
            return datetime.combine(fallback_date.date(), parsed_time)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(cleaned.replace("Z", "+00:00")).replace(
            tzinfo=None
        )
    except ValueError as exc:
        raise TradeDataError(
            f"Row {row_number}: unsupported execution time value {value!r}."
        ) from exc


def parse_decimal(value: str | None, *, row_number: int, field: str) -> Decimal:
    cleaned = (value or "").strip()
    if not cleaned:
        return Decimal("0")
    negative_parentheses = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()")
    cleaned = re.sub(r"[$€£]", "", cleaned)
    # Accept both US decimals (1,234.56) and common semicolon-CSV decimals
    # (1234,56). A single comma followed by 1-6 digits is treated as decimal.
    if "," in cleaned and "." not in cleaned and re.fullmatch(
        r"[+-]?\d+,\d{1,6}", cleaned
    ):
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    try:
        result = Decimal(cleaned)
    except InvalidOperation as exc:
        raise TradeDataError(
            f"Row {row_number}: invalid {field} value {value!r}."
        ) from exc
    return -result if negative_parentheses else result


def as_number(value: Decimal, places: int = 6) -> float:
    quantizer = Decimal("1").scaleb(-places)
    return float(value.quantize(quantizer))


def get_value(row: dict[str, str], column: str | None) -> str:
    return (row.get(column, "") if column else "") or ""


def decimal_ratio(
    numerator: Decimal, denominator: Decimal | int, places: int = 6
) -> float | None:
    decimal_denominator = (
        denominator if isinstance(denominator, Decimal) else Decimal(denominator)
    )
    if decimal_denominator == 0:
        return None
    return as_number(numerator / decimal_denominator, places)


def build_trade_analysis(records: list[dict[str, Any]]) -> dict[str, Any]:
    realized = [
        record
        for record in records
        if record["pnl_decimal"] != 0 and record["quantity_decimal"] != 0
    ]
    winners = [record for record in realized if record["pnl_decimal"] > 0]
    losers = [record for record in realized if record["pnl_decimal"] < 0]

    gross_profit = sum(
        (record["pnl_decimal"] for record in winners), Decimal("0")
    )
    gross_loss = abs(
        sum((record["pnl_decimal"] for record in losers), Decimal("0"))
    )
    net_pnl = gross_profit - gross_loss
    winning_shares = sum(
        (abs(record["quantity_decimal"]) for record in winners), Decimal("0")
    )
    losing_shares = sum(
        (abs(record["quantity_decimal"]) for record in losers), Decimal("0")
    )
    realized_shares = winning_shares + losing_shares
    average_winner = decimal_ratio(gross_profit, len(winners))
    average_loser = (
        -decimal_ratio(gross_loss, len(losers)) if losers else None
    )
    payoff_ratio = (
        decimal_ratio(
            Decimal(str(average_winner)),
            Decimal(str(abs(average_loser))),
        )
        if average_winner is not None and average_loser not in (None, 0)
        else None
    )

    daily_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        daily_groups[record["date"]].append(record)
    daily_rows: list[dict[str, Any]] = []
    cumulative_pnl = Decimal("0")
    for date_key, matching_records in sorted(daily_groups.items()):
        day_pnl = sum(
            (record["pnl_decimal"] for record in matching_records), Decimal("0")
        )
        cumulative_pnl += day_pnl
        daily_rows.append(
            {
                "date": date_key,
                "pnl": as_number(day_pnl),
                "trade_count": len(matching_records),
                "cumulative_pnl": as_number(cumulative_pnl),
            }
        )

    positive_days = [day for day in daily_rows if day["pnl"] > 0]
    negative_days = [day for day in daily_rows if day["pnl"] < 0]
    best_day = max(daily_rows, key=lambda day: day["pnl"]) if daily_rows else None
    worst_day = min(daily_rows, key=lambda day: day["pnl"]) if daily_rows else None

    hourly_groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in realized:
        if record["hour"] is not None:
            hourly_groups[record["hour"]].append(record)
    hourly_rows: list[dict[str, Any]] = []
    for hour, matching_records in sorted(hourly_groups.items()):
        hour_pnl = sum(
            (record["pnl_decimal"] for record in matching_records), Decimal("0")
        )
        hour_shares = sum(
            (abs(record["quantity_decimal"]) for record in matching_records),
            Decimal("0"),
        )
        hour_winners = sum(
            1 for record in matching_records if record["pnl_decimal"] > 0
        )
        hourly_rows.append(
            {
                "hour": hour,
                "label": f"{hour:02d}:00–{hour:02d}:59",
                "closed_execution_count": len(matching_records),
                "total_pnl": as_number(hour_pnl),
                "average_pnl": decimal_ratio(hour_pnl, len(matching_records)),
                "pnl_per_share": decimal_ratio(hour_pnl, hour_shares),
                "win_rate": hour_winners / len(matching_records),
            }
        )
    minimum_hour_sample = 3
    eligible_hours = [
        row
        for row in hourly_rows
        if row["closed_execution_count"] >= minimum_hour_sample
    ]
    best_hour = (
        max(eligible_hours, key=lambda row: row["average_pnl"])
        if eligible_hours
        else None
    )

    weekday_names = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    weekday_groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for day in daily_rows:
        weekday_groups[datetime.fromisoformat(day["date"]).weekday()].append(day)
    weekday_rows: list[dict[str, Any]] = []
    for weekday in range(7):
        matching_days = weekday_groups.get(weekday, [])
        if not matching_days:
            continue
        weekday_total = sum(
            (Decimal(str(day["pnl"])) for day in matching_days), Decimal("0")
        )
        weekday_positive = sum(1 for day in matching_days if day["pnl"] > 0)
        weekday_rows.append(
            {
                "weekday": weekday,
                "label": weekday_names[weekday],
                "trading_days": len(matching_days),
                "total_pnl": as_number(weekday_total),
                "average_daily_pnl": decimal_ratio(
                    weekday_total, len(matching_days)
                ),
                "profitable_day_rate": weekday_positive / len(matching_days),
            }
        )

    symbol_all_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    symbol_realized_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        symbol_all_groups[record["symbol"]].append(record)
    for record in realized:
        symbol_realized_groups[record["symbol"]].append(record)
    symbol_rows: list[dict[str, Any]] = []
    for symbol, all_records in symbol_all_groups.items():
        matching_realized = symbol_realized_groups.get(symbol, [])
        symbol_pnl = sum(
            (record["pnl_decimal"] for record in all_records), Decimal("0")
        )
        symbol_shares = sum(
            (abs(record["quantity_decimal"]) for record in matching_realized),
            Decimal("0"),
        )
        symbol_gross_profit = sum(
            (
                record["pnl_decimal"]
                for record in matching_realized
                if record["pnl_decimal"] > 0
            ),
            Decimal("0"),
        )
        symbol_gross_loss = abs(
            sum(
                (
                    record["pnl_decimal"]
                    for record in matching_realized
                    if record["pnl_decimal"] < 0
                ),
                Decimal("0"),
            )
        )
        symbol_winners = sum(
            1 for record in matching_realized if record["pnl_decimal"] > 0
        )
        symbol_rows.append(
            {
                "symbol": symbol,
                "trade_row_count": len(all_records),
                "closed_execution_count": len(matching_realized),
                "winning_execution_count": symbol_winners,
                "losing_execution_count": len(matching_realized) - symbol_winners,
                "closed_shares": as_number(symbol_shares),
                "gross_profit": as_number(symbol_gross_profit),
                "gross_loss": as_number(symbol_gross_loss),
                "total_pnl": as_number(symbol_pnl),
                "average_closed_pnl": decimal_ratio(
                    symbol_pnl, len(matching_realized)
                ),
                "pnl_per_share": decimal_ratio(symbol_pnl, symbol_shares),
                "win_rate": (
                    symbol_winners / len(matching_realized)
                    if matching_realized
                    else None
                ),
            }
        )
    symbol_rows.sort(key=lambda row: row["total_pnl"], reverse=True)

    month_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        month_groups[record["date"][:7]].append(record)
    month_rows: list[dict[str, Any]] = []
    for month, matching_records in sorted(month_groups.items()):
        month_pnl = sum(
            (record["pnl_decimal"] for record in matching_records), Decimal("0")
        )
        month_realized = [
            record
            for record in matching_records
            if record["pnl_decimal"] != 0 and record["quantity_decimal"] != 0
        ]
        month_winners = sum(
            1 for record in month_realized if record["pnl_decimal"] > 0
        )
        month_rows.append(
            {
                "month": month,
                "total_pnl": as_number(month_pnl),
                "trade_row_count": len(matching_records),
                "closed_execution_count": len(month_realized),
                "win_rate": (
                    month_winners / len(month_realized)
                    if month_realized
                    else None
                ),
            }
        )

    commission_paid = abs(
        sum(
            (
                Decimal(str(record["commission"]))
                for record in records
                if record["commission"] < 0
            ),
            Decimal("0"),
        )
    )
    return {
        "overview": {
            "closed_execution_count": len(realized),
            "winning_execution_count": len(winners),
            "losing_execution_count": len(losers),
            "win_rate": len(winners) / len(realized) if realized else None,
            "gross_profit": as_number(gross_profit),
            "gross_loss": -as_number(gross_loss),
            "net_pnl": as_number(net_pnl),
            "average_winner": average_winner,
            "average_loser": average_loser,
            "payoff_ratio": payoff_ratio,
            "profit_factor": decimal_ratio(gross_profit, gross_loss),
            "expectancy_per_closed_execution": decimal_ratio(
                net_pnl, len(realized)
            ),
            "average_profit_per_share_good_trades": decimal_ratio(
                gross_profit, winning_shares
            ),
            "average_loss_per_share_bad_trades": (
                -decimal_ratio(gross_loss, losing_shares) if losing_shares else None
            ),
            "net_pnl_per_closed_share": decimal_ratio(net_pnl, realized_shares),
            "trading_day_count": len(daily_rows),
            "profitable_day_rate": (
                len(positive_days) / len(daily_rows) if daily_rows else None
            ),
            "average_daily_pnl": decimal_ratio(net_pnl, len(daily_rows)),
            "best_day": best_day,
            "worst_day": worst_day,
            "commission_paid": as_number(commission_paid),
            "timed_closed_execution_count": sum(
                1 for record in realized if record["hour"] is not None
            ),
        },
        "best_hour": best_hour,
        "minimum_hour_sample": minimum_hour_sample,
        "hourly": hourly_rows,
        "weekdays": weekday_rows,
        "symbols": symbol_rows,
        "months": month_rows,
        "equity_curve": daily_rows,
        "definitions": {
            "good_trade": "A closing execution with positive FifoPnlRealized.",
            "profit_per_share": "Total positive realized P&L divided by shares closed by profitable executions.",
            "hour": "The execution hour from DateTime; OrderTime is used only when DateTime is unavailable.",
        },
    }


def find_csv(script_directory: Path, explicit_file: str | None) -> Path:
    if explicit_file:
        candidate = Path(explicit_file).expanduser()
        if not candidate.is_absolute():
            candidate = script_directory / candidate
        return candidate.resolve()

    preferred = script_directory / DEFAULT_CSV_NAME
    # Always use the documented default instead of guessing from unrelated CSV
    # files in the application folder. main() and /api/data can bootstrap this
    # exact path from the configured IBKR Activity Flex query when it is absent.
    return preferred.resolve()


def decode_csv_text(csv_path: Path) -> tuple[str, str]:
    raw = csv_path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16"), "utf-16"
    try:
        return raw.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        try:
            return raw.decode("cp1252"), "cp1252"
        except UnicodeDecodeError as exc:
            raise TradeDataError(
                f"Could not decode {csv_path.name}. Save it as UTF-8 CSV."
            ) from exc


def detect_csv_layout(text: str) -> tuple[int, str, list[str]]:
    lines = text.splitlines()
    candidates: list[tuple[int, int, int, str, list[str]]] = []
    required_alias_groups = (
        DATE_COLUMN_ALIASES,
        SYMBOL_COLUMN_ALIASES,
        PNL_COLUMN_ALIASES,
    )
    for line_index, line in enumerate(lines[:30]):
        if not line.strip():
            continue
        for delimiter in (",", ";", "\t", "|"):
            cells = next(csv.reader([line], delimiter=delimiter))
            normalized_cells = {normalized_header(cell) for cell in cells}
            required_matches = sum(
                any(normalized_header(alias) in normalized_cells for alias in aliases)
                for aliases in required_alias_groups
            )
            candidates.append(
                (required_matches, len(cells), -line_index, delimiter, cells)
            )

    if not candidates:
        raise TradeDataError("The CSV is empty or does not contain a header row.")

    required_matches, _, negative_line_index, delimiter, cells = max(candidates)
    if required_matches < 3:
        # Return the most plausible row so the caller can report what it found.
        return -negative_line_index, delimiter, [cell.strip() for cell in cells]
    return -negative_line_index, delimiter, [cell.strip() for cell in cells]


def load_trade_payload(csv_path: Path) -> dict[str, Any]:
    text, encoding = decode_csv_text(csv_path)
    header_line_index, delimiter, detected_headers = detect_csv_layout(text)
    source_lines = text.splitlines(keepends=True)
    csv_body = "".join(source_lines[header_line_index:])
    reader = csv.DictReader(io.StringIO(csv_body), delimiter=delimiter)
    headers = [(header or "").strip() for header in (reader.fieldnames or [])]
    if not headers:
        raise TradeDataError(
            f"{csv_path.name} is empty or does not contain a header row."
        )
    reader.fieldnames = headers

    columns = {
        "date": resolve_header(headers, DATE_COLUMN_ALIASES),
        "symbol": resolve_header(headers, SYMBOL_COLUMN_ALIASES),
        "pnl": resolve_header(headers, PNL_COLUMN_ALIASES),
        "quantity": resolve_header(headers, ("Quantity", "Qty")),
        "price": resolve_header(headers, ("TradePrice", "Trade Price", "Price")),
        "side": resolve_header(headers, ("Buy/Sell", "Side", "Action")),
        "commission": resolve_header(
            headers, ("IBCommission", "Commission", "Fees")
        ),
        "currency": resolve_header(headers, ("CurrencyPrimary", "Currency")),
        "account": resolve_header(
            headers, ("ClientAccountID", "Account", "Account ID")
        ),
        "description": resolve_header(
            headers, ("Description", "Security Description")
        ),
        "datetime": resolve_header(headers, TIME_COLUMN_ALIASES),
    }

    required_columns = {
        "trade date": columns["date"],
        "symbol": columns["symbol"],
        "realized P&L": columns["pnl"],
    }
    missing = [label for label, column in required_columns.items() if column is None]
    if missing:
        printable_delimiter = "TAB" if delimiter == "\t" else repr(delimiter)
        raise TradeDataError(
            f"Could not read the required columns from {csv_path.name}.\n"
            f"Missing: {', '.join(missing)}.\n"
            f"Detected header row: {header_line_index + 1}; delimiter: "
            f"{printable_delimiter}.\n"
            f"Detected headers: {', '.join(detected_headers) or '(none)'}.\n"
            "Make sure this is the trades CSV, or run with "
            "--file /full/path/to/the/correct.csv"
        )

    records: list[dict[str, Any]] = []
    for row_number, row in enumerate(reader, start=header_line_index + 2):
        if not any(str(value or "").strip() for value in row.values()):
            continue
        trade_date = parse_trade_date(get_value(row, columns["date"]), row_number)
        execution_datetime = parse_execution_datetime(
            get_value(row, columns["datetime"]), trade_date, row_number
        )
        symbol = get_value(row, columns["symbol"]).strip().upper()
        if not symbol:
            symbol = "UNKNOWN"
        pnl = parse_decimal(
            get_value(row, columns["pnl"]),
            row_number=row_number,
            field=columns["pnl"] or "P&L",
        )
        quantity = parse_decimal(
            get_value(row, columns["quantity"]),
            row_number=row_number,
            field=columns["quantity"] or "Quantity",
        )
        price = parse_decimal(
            get_value(row, columns["price"]),
            row_number=row_number,
            field=columns["price"] or "TradePrice",
        )
        commission = parse_decimal(
            get_value(row, columns["commission"]),
            row_number=row_number,
            field=columns["commission"] or "Commission",
        )
        records.append(
            {
                "source_row": row_number,
                "date": trade_date.date().isoformat(),
                "symbol": symbol,
                "pnl_decimal": pnl,
                "quantity_decimal": quantity,
                "pnl": as_number(pnl),
                "quantity": as_number(quantity),
                "price": as_number(price),
                "datetime": (
                    execution_datetime.isoformat(timespec="seconds")
                    if execution_datetime
                    else None
                ),
                "time": (
                    execution_datetime.strftime("%H:%M:%S")
                    if execution_datetime
                    else None
                ),
                "hour": execution_datetime.hour if execution_datetime else None,
                "side": get_value(row, columns["side"]).strip().upper(),
                "commission": as_number(commission),
                "currency": get_value(row, columns["currency"]).strip().upper()
                or "USD",
                "account": get_value(row, columns["account"]).strip(),
                "description": get_value(row, columns["description"]).strip(),
            }
        )

    if not records:
        raise TradeDataError("The CSV does not contain any trade rows.")

    records.sort(
        key=lambda item: (
            item["date"],
            item["time"] or "99:99:99",
            item["source_row"],
        )
    )
    grouped_days: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped_days[record["date"]].append(record)

    days: dict[str, dict[str, Any]] = {}
    for date_key, day_records in sorted(grouped_days.items()):
        symbol_records: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in day_records:
            symbol_records[record["symbol"]].append(record)

        symbols: list[dict[str, Any]] = []
        for symbol, matching_records in sorted(symbol_records.items()):
            symbol_pnl = sum(
                (item["pnl_decimal"] for item in matching_records), Decimal("0")
            )
            symbols.append(
                {
                    "symbol": symbol,
                    "trade_count": len(matching_records),
                    "pnl": as_number(symbol_pnl),
                }
            )

        day_pnl = sum(
            (item["pnl_decimal"] for item in day_records), Decimal("0")
        )
        public_records = [
            {
                key: value
                for key, value in item.items()
                if key not in ("pnl_decimal", "quantity_decimal")
            }
            for item in day_records
        ]
        days[date_key] = {
            "date": date_key,
            "trade_count": len(day_records),
            "pnl": as_number(day_pnl),
            "symbols": symbols,
            "trades": public_records,
        }

    day_values = list(days.values())
    total_pnl = sum(
        (record["pnl_decimal"] for record in records), Decimal("0")
    )
    best_day = max(day_values, key=lambda item: item["pnl"])
    worst_day = min(day_values, key=lambda item: item["pnl"])
    currencies = sorted({record["currency"] for record in records})
    months = sorted({record["date"][:7] for record in records})
    analysis_by_month = {
        month: build_trade_analysis(
            [record for record in records if record["date"].startswith(month)]
        )
        for month in months
    }
    analysis = {
        "all": build_trade_analysis(records),
        "months": analysis_by_month,
    }

    return {
        "metadata": {
            "file_name": csv_path.name,
            "file_path": str(csv_path),
            "loaded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "pnl_column": columns["pnl"],
            "time_column": columns["datetime"],
            "csv_encoding": encoding,
            "csv_delimiter": "TAB" if delimiter == "\t" else delimiter,
            "csv_header_row": header_line_index + 1,
            "count_definition": "Each CSV trade row counts as one trade.",
            "currencies": currencies,
        },
        "summary": {
            "trade_count": len(records),
            "pnl": as_number(total_pnl),
            "trading_days": len(days),
            "positive_days": sum(1 for item in day_values if item["pnl"] > 0),
            "negative_days": sum(1 for item in day_values if item["pnl"] < 0),
            "unique_symbols": len({record["symbol"] for record in records}),
            "best_day": {"date": best_day["date"], "pnl": best_day["pnl"]},
            "worst_day": {"date": worst_day["date"], "pnl": worst_day["pnl"]},
        },
        "months": months,
        "days": days,
        "analysis": analysis,
    }


HTML_PAGE = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WTC - World Trade Center</title>
  <style>
    :root {
      color-scheme: dark;
      --background: #071018;
      --panel: #0d1822;
      --panel-strong: #122230;
      --line: #203342;
      --text: #f4f7fa;
      --muted: #8fa5b5;
      --green: #33d69f;
      --green-soft: rgba(51, 214, 159, .12);
      --red: #ff6b7a;
      --red-soft: rgba(255, 107, 122, .12);
      --amber: #f6c760;
      --blue: #6eb8ff;
      --shadow: 0 18px 50px rgba(0, 0, 0, .24);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-width: 880px;
      background:
        radial-gradient(circle at top left, rgba(36, 107, 156, .18), transparent 32rem),
        var(--background);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
    }

    button, select { font: inherit; }
    button { cursor: pointer; }

    .shell { width: min(1720px, calc(100% - 32px)); margin: 0 auto; padding: 30px 0 48px; }
    .topbar {
      position: relative;
      display: flex;
      min-height: 286px;
      align-items: flex-end;
      justify-content: space-between;
      gap: 24px;
      overflow: hidden;
      padding: 30px;
      border: 1px solid rgba(143, 165, 181, .28);
      border-radius: 24px;
      background: #09141d;
      box-shadow: var(--shadow);
      isolation: isolate;
    }
    .hero-image {
      position: absolute;
      z-index: -2;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center 44%;
      filter: saturate(.78) contrast(1.08);
    }
    .hero-scrim {
      position: absolute;
      z-index: -1;
      inset: 0;
      background:
        linear-gradient(90deg, rgba(4, 12, 18, .94) 0%, rgba(4, 12, 18, .65) 48%, rgba(4, 12, 18, .24) 100%),
        linear-gradient(0deg, rgba(4, 12, 18, .88) 0%, transparent 68%);
    }
    .brand-block { max-width: 740px; }
    .header-actions { display: flex; align-self: flex-start; align-items: center; gap: 10px; }
    .view-tabs { display: inline-flex; gap: 4px; padding: 4px; border: 1px solid rgba(143, 165, 181, .38); border-radius: 14px; background: rgba(7, 16, 24, .78); backdrop-filter: blur(10px); }
    .view-tab { border: 0; border-radius: 10px; padding: 8px 13px; background: transparent; color: var(--muted); font-weight: 780; }
    .view-tab:hover { color: var(--text); }
    .view-tab.active { background: var(--panel-strong); color: var(--text); box-shadow: 0 4px 14px rgba(0,0,0,.22); }
    .eyebrow { margin: 0 0 8px; color: var(--blue); font-size: 12px; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; }
    h1 { margin: 0; font-size: clamp(34px, 4.5vw, 60px); line-height: .98; letter-spacing: -.05em; text-shadow: 0 3px 20px rgba(0,0,0,.58); }
    .subtitle { margin: 12px 0 0; color: #d6e0e7; font-size: 15px; text-shadow: 0 2px 12px rgba(0,0,0,.75); }
    .image-credit {
      position: absolute;
      right: 18px;
      bottom: 12px;
      z-index: 2;
      color: rgba(235, 242, 246, .72);
      font-size: 10px;
      text-decoration: none;
      text-shadow: 0 1px 8px rgba(0,0,0,.9);
    }
    .image-credit:hover { color: #fff; text-decoration: underline; }

    .button {
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px 14px;
      background: var(--panel-strong);
      color: var(--text);
      transition: transform .15s ease, border-color .15s ease, background .15s ease;
    }
    .button:hover { transform: translateY(-1px); border-color: #3c5c72; background: #172b3a; }
    .button.primary { border-color: rgba(110, 184, 255, .4); background: rgba(110, 184, 255, .13); }
    .button:disabled { cursor: not-allowed; opacity: .48; transform: none; }

    .status { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin: 24px 0 14px; color: var(--muted); font-size: 12px; }
    .status-dot { display: inline-block; width: 8px; height: 8px; margin-right: 7px; border-radius: 50%; background: var(--green); box-shadow: 0 0 14px rgba(51, 214, 159, .7); }
    .status-dot.warning { background: var(--amber); box-shadow: 0 0 14px rgba(246, 199, 96, .55); }
    .status-dot.error-dot { background: var(--red); box-shadow: 0 0 14px rgba(255, 107, 122, .55); }
    .note { color: var(--muted); }

    .summary-grid { display: grid; grid-template-columns: repeat(5, minmax(145px, 1fr)); gap: 12px; margin-bottom: 18px; }
    .summary-card { min-height: 106px; padding: 17px 18px; border: 1px solid var(--line); border-radius: 16px; background: linear-gradient(150deg, rgba(255,255,255,.025), transparent), var(--panel); box-shadow: var(--shadow); }
    .summary-label { color: var(--muted); font-size: 11px; font-weight: 800; letter-spacing: .09em; text-transform: uppercase; }
    .summary-value { margin-top: 8px; font-size: 27px; font-weight: 850; letter-spacing: -.035em; }
    .summary-detail { margin-top: 5px; color: var(--muted); font-size: 12px; }

    .calendar-balance-panel {
      margin: 0 0 18px;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 18px;
      background:
        linear-gradient(145deg, rgba(110, 184, 255, .075), transparent 55%),
        var(--panel);
      box-shadow: var(--shadow);
    }
    .calendar-balance-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 20px;
      padding: 17px 20px 5px;
    }
    .calendar-balance-title { margin: 0; font-size: 14px; font-weight: 850; }
    .calendar-balance-subtitle { margin: 4px 0 0; color: var(--muted); font-size: 11px; }
    .calendar-balance-current { text-align: right; }
    .calendar-balance-current-label { color: var(--muted); font-size: 10px; font-weight: 800; letter-spacing: .09em; text-transform: uppercase; }
    .calendar-balance-current-value { margin-top: 3px; font-size: 22px; font-weight: 850; font-variant-numeric: tabular-nums; }
    .calendar-balance-chart { min-height: 190px; overflow-x: auto; padding: 0 10px 8px; }
    .calendar-balance-svg { display: block; width: 100%; min-width: 720px; height: 190px; }
    .balance-grid { stroke: rgba(143, 165, 181, .13); stroke-width: 1; }
    .balance-zero { stroke: rgba(246, 199, 96, .42); stroke-width: 1; stroke-dasharray: 5 5; }
    .balance-line { fill: none; stroke: var(--blue); stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
    .balance-area { fill: url(#calendar-balance-gradient); }
    .balance-axis { fill: var(--muted); font-size: 10px; }
    .balance-point { stroke: #071018; stroke-width: 2; transition: r .12s ease; }
    .balance-point:hover { r: 6; }
    .balance-point.positive { fill: var(--green); }
    .balance-point.negative { fill: var(--red); }
    .balance-point.flat { fill: var(--amber); }

    .toolbar { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin: 22px 0 12px; }
    .month-controls { display: flex; align-items: center; gap: 8px; }
    .icon-button { width: 40px; height: 40px; border: 1px solid var(--line); border-radius: 12px; background: var(--panel); color: var(--text); font-size: 20px; }
    select { height: 40px; min-width: 178px; border: 1px solid var(--line); border-radius: 12px; padding: 0 12px; background: var(--panel); color: var(--text); }
    .month-pnl { font-size: 14px; font-weight: 750; }

    .calendar-wrap { overflow-x: auto; padding-bottom: 10px; }
    .calendar { min-width: 1240px; }
    .calendar-head, .week-row { display: grid; grid-template-columns: repeat(5, minmax(195px, 1fr)) minmax(180px, .88fr); gap: 10px; }
    .calendar-head { position: sticky; top: 0; z-index: 4; padding: 7px 0 10px; background: rgba(7, 16, 24, .94); backdrop-filter: blur(10px); }
    .column-title { padding: 0 10px; color: var(--muted); font-size: 11px; font-weight: 850; letter-spacing: .12em; text-transform: uppercase; }
    .column-title.week-total-title { color: var(--amber); }
    .week-row { margin-bottom: 10px; align-items: stretch; }

    .day-card, .week-total {
      min-height: 208px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: var(--panel);
      color: inherit;
      text-align: left;
      box-shadow: var(--shadow);
    }
    .day-card { width: 100%; padding: 14px; transition: transform .15s ease, border-color .15s ease; }
    .day-card.has-trades:hover { transform: translateY(-2px); border-color: #42637a; }
    .day-card.positive { background: linear-gradient(145deg, var(--green-soft), transparent 60%), var(--panel); }
    .day-card.negative { background: linear-gradient(145deg, var(--red-soft), transparent 60%), var(--panel); }
    .day-card.outside-month { opacity: .48; }
    .day-card.empty { cursor: default; box-shadow: none; }
    .day-card-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding-bottom: 10px; border-bottom: 1px solid rgba(143, 165, 181, .14); }
    .day-number { font-size: 21px; font-weight: 850; }
    .day-month { color: var(--muted); font-size: 11px; font-weight: 750; text-transform: uppercase; }
    .trade-pill { padding: 4px 7px; border: 1px solid var(--line); border-radius: 999px; color: var(--muted); font-size: 10px; font-weight: 750; }
    .empty-copy { margin-top: 22px; color: #566b79; font-size: 13px; }

    .symbols { display: grid; gap: 7px; margin-top: 11px; }
    .symbol-line { display: grid; grid-template-columns: minmax(52px, auto) 1fr auto; gap: 7px; align-items: baseline; }
    .ticker { font-weight: 850; letter-spacing: .025em; }
    .symbol-count { color: var(--muted); font-size: 11px; }
    .money { font-variant-numeric: tabular-nums; font-weight: 800; }
    .positive-text { color: var(--green); }
    .negative-text { color: var(--red); }
    .neutral-text { color: var(--text); }
    .more-symbols { color: var(--muted); font-size: 11px; }
    .day-total { display: flex; align-items: flex-end; justify-content: space-between; gap: 10px; margin-top: 13px; padding-top: 11px; border-top: 1px solid rgba(143, 165, 181, .14); }
    .day-total-label { color: var(--muted); font-size: 10px; font-weight: 800; letter-spacing: .09em; text-transform: uppercase; }
    .day-total-value { font-size: 22px; }

    .week-total { display: flex; flex-direction: column; justify-content: space-between; padding: 17px; border-color: rgba(246, 199, 96, .3); background: linear-gradient(145deg, rgba(246, 199, 96, .09), transparent 65%), #111b21; }
    .week-label { color: var(--amber); font-size: 11px; font-weight: 850; letter-spacing: .11em; text-transform: uppercase; }
    .week-range { margin-top: 5px; color: var(--muted); font-size: 12px; }
    .week-stats { display: grid; gap: 17px; }
    .week-stat-label { color: var(--muted); font-size: 10px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
    .week-count { margin-top: 4px; font-size: 22px; font-weight: 850; }
    .week-pnl { margin-top: 4px; font-size: 28px; font-weight: 900; letter-spacing: -.035em; }

    .analysis-toolbar { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; margin: 23px 0 16px; }
    .analysis-heading h2 { margin: 0; font-size: 30px; letter-spacing: -.035em; }
    .analysis-heading p { margin: 7px 0 0; color: var(--muted); font-size: 13px; }
    .analysis-kpis { display: grid; grid-template-columns: repeat(6, minmax(150px, 1fr)); gap: 12px; margin-bottom: 14px; }
    .analysis-kpi { min-height: 128px; padding: 17px 18px; border: 1px solid var(--line); border-radius: 16px; background: linear-gradient(150deg, rgba(255,255,255,.025), transparent), var(--panel); box-shadow: var(--shadow); }
    .analysis-kpi.featured { border-color: rgba(110, 184, 255, .32); background: linear-gradient(145deg, rgba(110,184,255,.11), transparent 70%), var(--panel); }
    .kpi-label { color: var(--muted); font-size: 10px; font-weight: 850; letter-spacing: .09em; line-height: 1.45; text-transform: uppercase; }
    .kpi-value { margin-top: 9px; font-size: 25px; font-weight: 900; letter-spacing: -.035em; font-variant-numeric: tabular-nums; }
    .kpi-detail { margin-top: 7px; color: var(--muted); font-size: 11px; line-height: 1.4; }
    .insight-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 0 0 14px; }
    .insight-card { padding: 16px 18px; border: 1px solid var(--line); border-radius: 16px; background: var(--panel); }
    .insight-title { color: var(--blue); font-size: 10px; font-weight: 850; letter-spacing: .1em; text-transform: uppercase; }
    .insight-copy { margin-top: 7px; color: #dbe6ed; font-size: 13px; line-height: 1.55; }
    .symbol-odds-panel { margin-bottom: 14px; padding: 20px; border: 1px solid rgba(110,184,255,.32); border-radius: 18px; background: linear-gradient(145deg, rgba(110,184,255,.09), transparent 46%), var(--panel); box-shadow: var(--shadow); }
    .odds-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 22px; }
    .odds-header h3 { margin: 0; font-size: 21px; letter-spacing: -.025em; }
    .odds-header p { margin: 6px 0 0; color: var(--muted); font-size: 11px; line-height: 1.5; }
    .odds-form { display: flex; gap: 8px; min-width: min(100%, 360px); }
    .odds-input { width: 210px; height: 42px; border: 1px solid var(--line); border-radius: 12px; padding: 0 13px; background: #09141d; color: var(--text); font: inherit; font-weight: 800; letter-spacing: .04em; text-transform: uppercase; }
    .odds-input:focus { border-color: var(--blue); outline: 2px solid rgba(110,184,255,.14); }
    .odds-result { margin-top: 17px; }
    .odds-result-header { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin-bottom: 12px; }
    .odds-symbol { display: flex; align-items: baseline; gap: 10px; font-size: 22px; font-weight: 900; }
    .evidence-badge { padding: 4px 8px; border: 1px solid var(--line); border-radius: 999px; color: var(--muted); font-size: 9px; font-weight: 850; letter-spacing: .08em; text-transform: uppercase; }
    .odds-grid { display: grid; grid-template-columns: repeat(6, minmax(130px, 1fr)); gap: 9px; }
    .odds-card { min-height: 96px; padding: 13px 14px; border: 1px solid rgba(143,165,181,.15); border-radius: 13px; background: rgba(7,16,24,.46); }
    .odds-label { color: var(--muted); font-size: 9px; font-weight: 850; letter-spacing: .08em; text-transform: uppercase; }
    .odds-value { margin-top: 7px; font-size: 20px; font-weight: 900; letter-spacing: -.025em; }
    .odds-detail { margin-top: 4px; color: var(--muted); font-size: 10px; line-height: 1.35; }
    .confidence-wrap { margin: 13px 0; padding: 12px 14px; border: 1px solid rgba(143,165,181,.14); border-radius: 12px; background: rgba(7,16,24,.34); }
    .confidence-copy { display: flex; justify-content: space-between; gap: 15px; color: var(--muted); font-size: 10px; }
    .confidence-track { position: relative; height: 8px; margin-top: 9px; border-radius: 999px; background: #172632; }
    .confidence-range { position: absolute; top: 0; height: 100%; border-radius: inherit; background: rgba(110,184,255,.42); }
    .confidence-marker { position: absolute; top: -4px; width: 3px; height: 16px; border-radius: 2px; background: var(--blue); transform: translateX(-50%); }
    .odds-empty { padding: 17px; border: 1px dashed var(--line); border-radius: 12px; color: var(--muted); font-size: 12px; line-height: 1.55; text-align: center; }
    .analysis-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
    .analysis-panel { min-width: 0; padding: 18px; border: 1px solid var(--line); border-radius: 18px; background: var(--panel); box-shadow: var(--shadow); }
    .analysis-panel.span-2 { grid-column: span 2; }
    .panel-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
    .panel-title { margin: 0; font-size: 17px; letter-spacing: -.015em; }
    .panel-subtitle { margin: 5px 0 0; color: var(--muted); font-size: 11px; line-height: 1.45; }
    .mini-button { border: 1px solid var(--line); border-radius: 10px; padding: 7px 10px; background: var(--panel-strong); color: var(--muted); font-size: 10px; font-weight: 800; white-space: nowrap; }
    .mini-button:hover { border-color: #3c5c72; color: var(--text); }
    .mini-button:disabled { cursor: wait; opacity: .58; }
    .bar-chart { display: grid; gap: 9px; }
    .bar-row { display: grid; grid-template-columns: minmax(80px, 112px) minmax(100px, 1fr) minmax(80px, auto); gap: 10px; align-items: center; }
    .bar-label { overflow: hidden; color: #dfe8ee; font-size: 11px; font-weight: 750; text-overflow: ellipsis; white-space: nowrap; }
    .bar-track { position: relative; height: 10px; overflow: hidden; border-radius: 999px; background: #172632; }
    .bar-fill { height: 100%; min-width: 2px; border-radius: inherit; }
    .bar-fill.positive { background: linear-gradient(90deg, #1ca97e, var(--green)); }
    .bar-fill.negative { background: linear-gradient(90deg, var(--red), #c64959); }
    .bar-value { font-size: 11px; font-weight: 820; font-variant-numeric: tabular-nums; text-align: right; }
    .bar-detail { grid-column: 2 / -1; margin-top: -6px; color: var(--muted); font-size: 10px; }
    .metric-table-wrap { max-height: 410px; overflow: auto; border: 1px solid rgba(143,165,181,.12); border-radius: 12px; }
    .metric-table th { top: 0; }
    .metric-table td { font-size: 12px; }
    .metric-table tbody tr:last-child td { border-bottom: 0; }
    .symbol-link { color: var(--text); font-weight: 850; text-decoration: none; text-underline-offset: 3px; }
    .symbol-link:hover { color: var(--blue); text-decoration: underline; }
    .symbol-link::after { content: " ↗"; color: var(--muted); font-size: 10px; font-weight: 700; }
    .float-value { color: #dce8ef; font-variant-numeric: tabular-nums; font-weight: 760; }
    .float-unavailable { color: var(--muted); }
    .float-status { margin: -3px 0 12px; padding: 9px 11px; border: 1px solid rgba(246,199,96,.28); border-radius: 10px; background: rgba(246,199,96,.07); color: #ead9a6; font-size: 11px; line-height: 1.45; }
    .metadata-status { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin: 0 0 14px; padding: 11px 14px; border: 1px solid rgba(110,184,255,.26); border-radius: 13px; background: rgba(110,184,255,.07); color: #c8def0; font-size: 11px; }
    .metadata-progress { color: var(--muted); white-space: nowrap; }
    .bucket-note { margin-top: 11px; color: var(--muted); font-size: 10px; line-height: 1.45; }
    .scatter-wrap { overflow-x: auto; }
    .scatter-svg { display: block; width: 100%; min-width: 590px; height: 310px; }
    .scatter-grid { stroke: rgba(143,165,181,.13); stroke-width: 1; }
    .scatter-zero { stroke: rgba(246,199,96,.44); stroke-width: 1; stroke-dasharray: 5 5; }
    .scatter-point { fill: rgba(110,184,255,.72); stroke: #b9dbfb; stroke-width: 1; }
    .scatter-point.positive { fill: rgba(51,214,159,.74); stroke: #91efd0; }
    .scatter-point.negative { fill: rgba(255,107,122,.72); stroke: #ffb3bc; }
    .scatter-axis { fill: var(--muted); font-size: 10px; }
    .equity-wrap { min-height: 260px; }
    .equity-svg { display: block; width: 100%; min-width: 560px; height: 260px; }
    .equity-grid { stroke: rgba(143,165,181,.14); stroke-width: 1; }
    .equity-zero { stroke: rgba(246,199,96,.42); stroke-width: 1; stroke-dasharray: 5 5; }
    .equity-line { fill: none; stroke: var(--blue); stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
    .equity-area { fill: url(#equity-gradient); }
    .equity-axis { fill: var(--muted); font-size: 10px; }
    .chart-empty { display: grid; place-items: center; min-height: 180px; padding: 25px; border: 1px dashed var(--line); border-radius: 12px; color: var(--muted); font-size: 12px; line-height: 1.5; text-align: center; }
    .definition-list { display: grid; gap: 14px; }
    .definition-list dt { color: var(--text); font-size: 12px; font-weight: 820; }
    .definition-list dd { margin: 4px 0 0; color: var(--muted); font-size: 11px; line-height: 1.55; }

    dialog { width: min(1060px, calc(100% - 38px)); max-height: min(760px, calc(100vh - 50px)); padding: 0; border: 1px solid #345064; border-radius: 20px; background: #0b151e; color: var(--text); box-shadow: 0 34px 100px rgba(0,0,0,.65); }
    dialog::backdrop { background: rgba(0, 6, 10, .78); backdrop-filter: blur(5px); }
    .modal-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; padding: 22px 24px 18px; border-bottom: 1px solid var(--line); }
    .modal-title { margin: 0; font-size: 24px; }
    .modal-summary { margin-top: 6px; color: var(--muted); font-size: 13px; }
    .close-button { width: 38px; height: 38px; border: 1px solid var(--line); border-radius: 11px; background: var(--panel-strong); color: var(--text); font-size: 21px; }
    .modal-body { max-height: 620px; overflow: auto; padding: 18px 24px 24px; }
    table { width: 100%; border-collapse: collapse; }
    th { position: sticky; top: 0; z-index: 2; padding: 10px 9px; background: #101d27; color: var(--muted); font-size: 10px; letter-spacing: .09em; text-align: left; text-transform: uppercase; }
    td { padding: 11px 9px; border-bottom: 1px solid rgba(143,165,181,.12); font-size: 13px; }
    td.number, th.number { text-align: right; font-variant-numeric: tabular-nums; }
    .side-buy { color: var(--green); font-weight: 800; }
    .side-sell { color: var(--red); font-weight: 800; }

    .error { margin-top: 20px; padding: 16px; border: 1px solid rgba(255,107,122,.45); border-radius: 14px; background: var(--red-soft); color: #ffd8dd; white-space: pre-wrap; }
    .hidden { display: none !important; }

    @media (max-width: 1100px) {
      .summary-grid { grid-template-columns: repeat(3, 1fr); }
      .analysis-kpis { grid-template-columns: repeat(3, 1fr); }
      .odds-grid { grid-template-columns: repeat(3, 1fr); }
      .odds-header { align-items: stretch; flex-direction: column; }
      .analysis-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .analysis-panel.span-2 { grid-column: span 2; }
      .header-actions { align-items: flex-end; flex-direction: column-reverse; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <div class="topbar">
      <img
        class="hero-image"
        src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/World_Trade_Center_towers%2C_New_York%2C_LCCN2015645969.jpg/1280px-World_Trade_Center_towers%2C_New_York%2C_LCCN2015645969.jpg"
        alt="The original World Trade Center Twin Towers in the Manhattan skyline in July 2001"
        loading="eager"
        fetchpriority="high"
      >
      <div class="hero-scrim" aria-hidden="true"></div>
      <div class="brand-block">
        <p class="eyebrow">Trading performance command center</p>
        <h1>WTC - World Trade Center</h1>
        <p class="subtitle">Your calendar, analysis, and symbol intelligence in one place.</p>
      </div>
      <div class="header-actions">
        <nav class="view-tabs" aria-label="Dashboard pages">
          <button class="view-tab active" id="calendar-tab" type="button">Calendar</button>
          <button class="view-tab" id="analysis-tab" type="button">Analysis</button>
        </nav>
        <button class="button" id="ibkr-sync-button" type="button">Sync IBKR</button>
        <button class="button primary" id="reload-button" type="button">Reload CSV</button>
      </div>
      <a
        class="image-credit"
        href="https://commons.wikimedia.org/wiki/File:World_Trade_Center_towers,_New_York,_LCCN2015645969.jpg"
        target="_blank"
        rel="noopener noreferrer"
      >Photo: Carol M. Highsmith / Library of Congress</a>
    </div>

    <div class="status">
      <span id="file-status"><span class="status-dot"></span>Loading trades…</span>
      <span id="ibkr-status"><span class="status-dot warning"></span>Checking IBKR sync…</span>
      <span class="note" id="data-note"></span>
    </div>

    <section class="page-view" id="calendar-page">
      <section class="summary-grid" id="summary-grid" aria-label="Monthly summary"></section>

      <article class="calendar-balance-panel" aria-labelledby="calendar-balance-title">
        <div class="calendar-balance-header">
          <div>
            <h2 class="calendar-balance-title" id="calendar-balance-title">Daily balance</h2>
            <p class="calendar-balance-subtitle">Cumulative realized P&amp;L from the first trade in the loaded file.</p>
          </div>
          <div class="calendar-balance-current">
            <div class="calendar-balance-current-label">Current balance</div>
            <div class="calendar-balance-current-value" id="calendar-balance-value">—</div>
          </div>
        </div>
        <div class="calendar-balance-chart" id="calendar-balance-chart"></div>
      </article>

      <div class="toolbar">
        <div class="month-controls">
          <button class="icon-button" id="previous-month" type="button" aria-label="Previous month">‹</button>
          <select id="month-select" aria-label="Displayed month"></select>
          <button class="icon-button" id="next-month" type="button" aria-label="Next month">›</button>
        </div>
        <div class="month-pnl" id="month-pnl"></div>
      </div>

      <div class="calendar-wrap">
        <section class="calendar" id="calendar" aria-label="Trade calendar">
          <div class="calendar-head">
            <div class="column-title">Monday</div>
            <div class="column-title">Tuesday</div>
            <div class="column-title">Wednesday</div>
            <div class="column-title">Thursday</div>
            <div class="column-title">Friday</div>
            <div class="column-title week-total-title">Week total</div>
          </div>
          <div id="week-rows"></div>
        </section>
      </div>
    </section>

    <section class="page-view hidden" id="analysis-page">
      <div class="analysis-toolbar">
        <div class="analysis-heading">
          <h2>Trade Analysis</h2>
          <p>Understand where your edge is strongest—and where losses are concentrated.</p>
        </div>
        <select id="analysis-period-select" aria-label="Analysis period"></select>
      </div>

      <section class="analysis-kpis" id="analysis-kpis" aria-label="Performance metrics"></section>
      <section class="insight-grid" id="analysis-insights" aria-label="Key observations"></section>
      <article class="symbol-odds-panel">
        <div class="odds-header">
          <div>
            <h3>New Symbol Rank</h3>
            <p>Enter any ticker. Its current Yahoo profile will be ranked against similar stocks from your own trading history.</p>
          </div>
          <form class="odds-form" id="symbol-odds-form">
            <input class="odds-input" id="symbol-odds-input" list="trade-symbols" placeholder="Enter symbol" autocomplete="off" aria-label="Symbol to analyze">
            <datalist id="trade-symbols"></datalist>
            <button class="button primary" type="submit">Analyze</button>
          </form>
        </div>
        <div class="odds-result" id="symbol-odds-result">
          <div class="odds-empty">Enter a symbol—even one you have never traded—to calculate its historical-fit rank.</div>
        </div>
      </article>
      <div class="metadata-status" id="metadata-status">
        <span>Yahoo company-profile analysis uses current values and will load when this page opens.</span>
        <span class="metadata-progress" id="metadata-progress">Not loaded</span>
      </div>

      <div class="analysis-grid">
        <article class="analysis-panel span-2">
          <div class="panel-header"><div><h3 class="panel-title">Performance by current float</h3><p class="panel-subtitle">Win rate, profit efficiency, and total results grouped by Yahoo’s latest float.</p></div></div>
          <div id="float-bucket-table"></div>
        </article>
        <article class="analysis-panel">
          <div class="panel-header"><div><h3 class="panel-title">Market-cap performance</h3><p class="panel-subtitle">Average P&amp;L/share across current market-cap groups.</p></div></div>
          <div id="market-cap-chart"></div>
        </article>
        <article class="analysis-panel span-2">
          <div class="panel-header"><div><h3 class="panel-title">Float versus P&amp;L/share</h3><p class="panel-subtitle">Each point is a traded symbol. Float uses a logarithmic scale; point size reflects closed executions.</p></div></div>
          <div class="scatter-wrap" id="float-scatter"></div>
        </article>
        <article class="analysis-panel">
          <div class="panel-header"><div><h3 class="panel-title">Float turnover</h3><p class="panel-subtitle">10-day average volume divided by current float.</p></div></div>
          <div id="turnover-chart"></div>
        </article>
        <article class="analysis-panel span-2">
          <div class="panel-header"><div><h3 class="panel-title">Sector performance</h3><p class="panel-subtitle">Current Yahoo sector, ranked by average P&amp;L/share.</p></div></div>
          <div id="sector-table"></div>
        </article>
        <article class="analysis-panel">
          <div class="panel-header"><div><h3 class="panel-title">Yahoo profile coverage</h3><p class="panel-subtitle">Availability of current properties for symbols in this period.</p></div></div>
          <div id="metadata-coverage"></div>
        </article>
        <article class="analysis-panel span-2">
          <div class="panel-header"><div><h3 class="panel-title">Performance by exit hour</h3><p class="panel-subtitle">Average realized P&amp;L per closing execution. Hour is based on its closing execution time.</p></div></div>
          <div id="hourly-chart"></div>
        </article>
        <article class="analysis-panel">
          <div class="panel-header"><div><h3 class="panel-title">Weekday performance</h3><p class="panel-subtitle">Average daily P&amp;L for each weekday.</p></div></div>
          <div id="weekday-chart"></div>
        </article>
        <article class="analysis-panel span-2">
          <div class="panel-header"><div><h3 class="panel-title">Cumulative realized P&amp;L</h3><p class="panel-subtitle">Daily equity curve for the selected period.</p></div></div>
          <div class="equity-wrap" id="equity-chart"></div>
        </article>
        <article class="analysis-panel">
          <div class="panel-header"><div><h3 class="panel-title">How metrics are calculated</h3><p class="panel-subtitle">A concise guide to the numbers shown here.</p></div></div>
          <dl class="definition-list" id="analysis-definitions"></dl>
        </article>
        <article class="analysis-panel span-2">
          <div class="panel-header">
            <div><h3 class="panel-title">Symbol performance</h3><p class="panel-subtitle">Best-performing symbols with current Yahoo profile data.</p></div>
            <button class="mini-button" id="refresh-floats" type="button">Refresh Yahoo data</button>
          </div>
          <div class="float-status hidden" id="float-status"></div>
          <div id="symbol-table"></div>
        </article>
        <article class="analysis-panel">
          <div class="panel-header"><div><h3 class="panel-title">Monthly results</h3><p class="panel-subtitle">A compact view of consistency over time.</p></div></div>
          <div id="monthly-table"></div>
        </article>
      </div>
    </section>

    <div class="error hidden" id="error-box"></div>
  </main>

  <dialog id="trade-dialog">
    <div class="modal-header">
      <div>
        <h2 class="modal-title" id="modal-title"></h2>
        <div class="modal-summary" id="modal-summary"></div>
      </div>
      <button class="close-button" id="modal-close" type="button" aria-label="Close">×</button>
    </div>
    <div class="modal-body" id="modal-body"></div>
  </dialog>

  <script>window.__TRADE_PAYLOAD__ = null;</script>
  <script>
    const initialAnalysisView = location.pathname === '/analysis' || location.hash === '#analysis';
    const state = {
      payload: null,
      selectedMonth: null,
      selectedView: initialAnalysisView ? 'analysis' : 'calendar',
      analysisScope: 'all',
      symbolMetadata: {},
      visibleSymbols: [],
      metadataLoading: false,
      selectedRankSymbol: null,
      lastActivitySync: null
    };
    const monthSelect = document.getElementById('month-select');
    const analysisPeriodSelect = document.getElementById('analysis-period-select');
    const weekRows = document.getElementById('week-rows');
    const errorBox = document.getElementById('error-box');
    const dialog = document.getElementById('trade-dialog');
    const ibkrSyncButton = document.getElementById('ibkr-sync-button');

    const escapeHtml = (value) => String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');

    function toneClass(value) {
      if (value > 0.0000001) return 'positive-text';
      if (value < -0.0000001) return 'negative-text';
      return 'neutral-text';
    }

    function cardTone(value) {
      if (value > 0.0000001) return 'positive';
      if (value < -0.0000001) return 'negative';
      return 'neutral';
    }

    function formatMoney(value) {
      const currencies = state.payload?.metadata?.currencies ?? ['USD'];
      const currency = currencies.length === 1 ? currencies[0] : 'USD';
      try {
        return new Intl.NumberFormat('en-US', {
          style: 'currency', currency, minimumFractionDigits: 2,
          maximumFractionDigits: 2, signDisplay: 'auto'
        }).format(value || 0);
      } catch (_) {
        return `${Number(value || 0).toFixed(2)} ${currency}`;
      }
    }

    function formatPercent(value) {
      return value == null ? '—' : `${(Number(value) * 100).toFixed(1)}%`;
    }

    function formatPerShare(value) {
      return value == null ? '—' : `${formatMoney(value)}/share`;
    }

    function formatMaybeMoney(value) {
      return value == null ? '—' : formatMoney(value);
    }

    function formatRatio(value) {
      return value == null ? '—' : `${Number(value).toFixed(2)}×`;
    }

    function formatShares(value) {
      if (value == null) return 'N/A';
      return new Intl.NumberFormat('en-US', {
        notation: 'compact', maximumFractionDigits: 2
      }).format(Number(value));
    }

    function formatCompactMoney(value) {
      if (value == null) return 'N/A';
      return `$${new Intl.NumberFormat('en-US', {
        notation: 'compact', maximumFractionDigits: 2
      }).format(Number(value))}`;
    }

    function yahooFinanceUrl(symbol) {
      return `https://finance.yahoo.com/quote/${encodeURIComponent(symbol)}`;
    }

    function setView(view, updateUrl = true) {
      state.selectedView = view;
      const showingAnalysis = view === 'analysis';
      document.getElementById('calendar-page').classList.toggle('hidden', showingAnalysis);
      document.getElementById('analysis-page').classList.toggle('hidden', !showingAnalysis);
      document.getElementById('calendar-tab').classList.toggle('active', !showingAnalysis);
      document.getElementById('analysis-tab').classList.toggle('active', showingAnalysis);
      document.title = showingAnalysis
        ? 'WTC - Analysis'
        : 'WTC - World Trade Center';
      if (showingAnalysis && state.payload) {
        loadYahooMetadata(currentAnalysis().symbols.map(row => row.symbol));
      }
      if (!updateUrl) return;
      if (location.protocol === 'file:') {
        location.hash = showingAnalysis ? 'analysis' : '';
      } else {
        history.pushState({ view }, '', showingAnalysis ? '/analysis' : '/');
      }
    }

    function parseIsoDate(isoDate) {
      const [year, month, day] = isoDate.split('-').map(Number);
      return new Date(Date.UTC(year, month - 1, day));
    }

    function isoDate(date) {
      return date.toISOString().slice(0, 10);
    }

    function addDays(date, days) {
      const result = new Date(date);
      result.setUTCDate(result.getUTCDate() + days);
      return result;
    }

    function monthName(monthKey) {
      const [year, month] = monthKey.split('-').map(Number);
      return new Intl.DateTimeFormat('en-US', {
        month: 'long', year: 'numeric', timeZone: 'UTC'
      }).format(new Date(Date.UTC(year, month - 1, 1)));
    }

    function shortDate(iso) {
      return new Intl.DateTimeFormat('en-US', {
        month: 'short', day: 'numeric', timeZone: 'UTC'
      }).format(parseIsoDate(iso));
    }

    function longDate(iso) {
      return new Intl.DateTimeFormat('en-US', {
        weekday: 'long', month: 'long', day: 'numeric', year: 'numeric',
        timeZone: 'UTC'
      }).format(parseIsoDate(iso));
    }

    function monthWeeks(monthKey) {
      const [year, month] = monthKey.split('-').map(Number);
      const first = new Date(Date.UTC(year, month - 1, 1));
      const last = new Date(Date.UTC(year, month, 0));
      const mondayIndex = (first.getUTCDay() + 6) % 7;
      const start = addDays(first, -mondayIndex);
      const lastMondayIndex = (last.getUTCDay() + 6) % 7;
      const end = addDays(last, (4 - lastMondayIndex + 7) % 7);
      const weeks = [];
      for (let monday = start; monday <= end; monday = addDays(monday, 7)) {
        weeks.push(Array.from({ length: 5 }, (_, index) => addDays(monday, index)));
      }
      return weeks;
    }

    function monthDayData() {
      return Object.values(state.payload.days)
        .filter(day => day.date.startsWith(state.selectedMonth));
    }

    function renderSummary() {
      const days = monthDayData();
      const pnl = days.reduce((sum, day) => sum + day.pnl, 0);
      const trades = days.reduce((sum, day) => sum + day.trade_count, 0);
      const symbols = new Set();
      days.forEach(day => day.symbols.forEach(item => symbols.add(item.symbol)));
      const positiveDays = days.filter(day => day.pnl > 0).length;
      const negativeDays = days.filter(day => day.pnl < 0).length;
      const flatDays = days.length - positiveDays - negativeDays;
      const decidedDays = positiveDays + negativeDays;
      const positiveRate = decidedDays ? positiveDays / decidedDays : null;
      const bestDay = days.length
        ? days.reduce((best, day) => day.pnl > best.pnl ? day : best, days[0])
        : null;
      const cards = [
        ['Monthly P&L', `<span class="${toneClass(pnl)}">${formatMoney(pnl)}</span>`, monthName(state.selectedMonth)],
        ['Trade count', String(trades), 'CSV trade rows'],
        ['Positive / Negative days', `<span class="positive-text">${positiveDays}</span> / <span class="negative-text">${negativeDays}</span>`, positiveRate == null ? 'No completed days' : `${formatPercent(positiveRate)} positive${flatDays ? ` · ${flatDays} flat` : ''}`],
        ['Symbols', String(symbols.size), 'Unique tickers'],
        ['Best day', bestDay ? formatMoney(bestDay.pnl) : '—', bestDay ? longDate(bestDay.date) : 'No trades']
      ];
      document.getElementById('summary-grid').innerHTML = cards.map(([label, value, detail]) => `
        <article class="summary-card">
          <div class="summary-label">${escapeHtml(label)}</div>
          <div class="summary-value">${value}</div>
          <div class="summary-detail">${escapeHtml(detail)}</div>
        </article>`).join('');
      document.getElementById('month-pnl').innerHTML =
        `${escapeHtml(monthName(state.selectedMonth))}: <span class="${toneClass(pnl)}">${formatMoney(pnl)}</span>`;
    }

    function renderCalendarBalanceChart() {
      const target = document.getElementById('calendar-balance-chart');
      const currentValue = document.getElementById('calendar-balance-value');
      const rows = state.payload.analysis.all.equity_curve
        .filter(row => row.date.startsWith(state.selectedMonth));
      if (!rows.length) {
        currentValue.textContent = '—';
        currentValue.className = 'calendar-balance-current-value';
        target.innerHTML = '<div class="chart-empty">No daily P&amp;L is available for this month.</div>';
        return;
      }

      const finalBalance = Number(rows[rows.length - 1].cumulative_pnl || 0);
      currentValue.textContent = formatMoney(finalBalance);
      currentValue.className = `calendar-balance-current-value ${toneClass(finalBalance)}`;

      const width = 1400, height = 190, left = 62, right = 18, top = 15, bottom = 30;
      const chartWidth = width - left - right, chartHeight = height - top - bottom;
      const values = rows.map(row => Number(row.cumulative_pnl || 0));
      let minimum = Math.min(...values), maximum = Math.max(...values);
      if (minimum === maximum) {
        const spread = Math.max(Math.abs(minimum) * .04, 1);
        minimum -= spread;
        maximum += spread;
      } else {
        const padding = Math.max((maximum - minimum) * .12, .5);
        minimum -= padding;
        maximum += padding;
      }
      const x = index => left + (rows.length === 1 ? chartWidth / 2 : index / (rows.length - 1) * chartWidth);
      const y = value => top + (maximum - value) / (maximum - minimum) * chartHeight;
      const points = values.map((value, index) => `${x(index).toFixed(2)},${y(value).toFixed(2)}`).join(' ');
      const showsZero = minimum <= 0 && maximum >= 0;
      const baseY = showsZero ? y(0) : top + chartHeight;
      const areaPoints = `${x(0).toFixed(2)},${baseY.toFixed(2)} ${points} ${x(rows.length - 1).toFixed(2)},${baseY.toFixed(2)}`;
      const midpoint = Math.floor((rows.length - 1) / 2);
      const pointMarkup = rows.map((row, index) => {
        const dailyPnl = Number(row.pnl || 0);
        const pointClass = dailyPnl > 0 ? 'positive' : dailyPnl < 0 ? 'negative' : 'flat';
        const tooltip = `${longDate(row.date)} · Day ${formatMoney(dailyPnl)} · Balance ${formatMoney(row.cumulative_pnl)}`;
        return `<circle class="balance-point ${pointClass}" cx="${x(index).toFixed(2)}" cy="${y(values[index]).toFixed(2)}" r="4" tabindex="0"><title>${escapeHtml(tooltip)}</title></circle>`;
      }).join('');
      target.innerHTML = `<svg class="calendar-balance-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Daily cumulative realized profit and loss balance for ${escapeHtml(monthName(state.selectedMonth))}">
        <defs><linearGradient id="calendar-balance-gradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6eb8ff" stop-opacity=".30"/><stop offset="1" stop-color="#6eb8ff" stop-opacity=".02"/></linearGradient></defs>
        <line class="balance-grid" x1="${left}" y1="${top}" x2="${width - right}" y2="${top}"/>
        <line class="balance-grid" x1="${left}" y1="${top + chartHeight}" x2="${width - right}" y2="${top + chartHeight}"/>
        ${showsZero ? `<line class="balance-zero" x1="${left}" y1="${y(0).toFixed(2)}" x2="${width - right}" y2="${y(0).toFixed(2)}"/>` : ''}
        <polygon class="balance-area" points="${areaPoints}"/>
        <polyline class="balance-line" points="${points}"/>
        ${pointMarkup}
        <text class="balance-axis" x="4" y="${top + 4}">${escapeHtml(formatMoney(maximum))}</text>
        <text class="balance-axis" x="4" y="${top + chartHeight}">${escapeHtml(formatMoney(minimum))}</text>
        <text class="balance-axis" x="${x(0)}" y="${height - 7}">${escapeHtml(shortDate(rows[0].date))}</text>
        <text class="balance-axis" x="${x(midpoint)}" y="${height - 7}" text-anchor="middle">${escapeHtml(shortDate(rows[midpoint].date))}</text>
        <text class="balance-axis" x="${x(rows.length - 1)}" y="${height - 7}" text-anchor="end">${escapeHtml(shortDate(rows[rows.length - 1].date))}</text>
      </svg>`;
    }

    function dayCard(date) {
      const dateKey = isoDate(date);
      const day = state.payload.days[dateKey];
      const outsideMonth = !dateKey.startsWith(state.selectedMonth);
      const dayNumber = date.getUTCDate();
      const month = new Intl.DateTimeFormat('en-US', { month: 'short', timeZone: 'UTC' }).format(date);
      if (!day) {
        return `<button class="day-card empty ${outsideMonth ? 'outside-month' : ''}" type="button" disabled>
          <div class="day-card-header"><div><span class="day-number">${dayNumber}</span> <span class="day-month">${month}</span></div></div>
          <div class="empty-copy">No trades</div>
        </button>`;
      }

      const visibleSymbols = day.symbols.slice(0, 5);
      const symbolLines = visibleSymbols.map(item => `
        <div class="symbol-line">
          <span class="ticker">${escapeHtml(item.symbol)}</span>
          <span class="symbol-count">${item.trade_count} trade${item.trade_count === 1 ? '' : 's'}</span>
          <span class="money ${toneClass(item.pnl)}">${formatMoney(item.pnl)}</span>
        </div>`).join('');
      const remainder = day.symbols.length - visibleSymbols.length;
      return `<button class="day-card has-trades ${cardTone(day.pnl)} ${outsideMonth ? 'outside-month' : ''}" type="button" data-date="${dateKey}">
        <div class="day-card-header">
          <div><span class="day-number">${dayNumber}</span> <span class="day-month">${month}</span></div>
          <span class="trade-pill">${day.trade_count} trade${day.trade_count === 1 ? '' : 's'}</span>
        </div>
        <div class="symbols">${symbolLines}${remainder > 0 ? `<div class="more-symbols">+${remainder} more symbols</div>` : ''}</div>
        <div class="day-total">
          <span class="day-total-label">Day total</span>
          <span class="day-total-value money ${toneClass(day.pnl)}">${formatMoney(day.pnl)}</span>
        </div>
      </button>`;
    }

    function weekTotal(week) {
      const dates = week.map(isoDate);
      const matching = dates.map(date => state.payload.days[date]).filter(Boolean);
      const count = matching.reduce((sum, day) => sum + day.trade_count, 0);
      const pnl = matching.reduce((sum, day) => sum + day.pnl, 0);
      return `<aside class="week-total">
        <div>
          <div class="week-label">Week total</div>
          <div class="week-range">${shortDate(dates[0])} – ${shortDate(dates[4])}</div>
        </div>
        <div class="week-stats">
          <div><div class="week-stat-label">Trades</div><div class="week-count">${count}</div></div>
          <div><div class="week-stat-label">P&L</div><div class="week-pnl ${toneClass(pnl)}">${formatMoney(pnl)}</div></div>
        </div>
      </aside>`;
    }

    function renderCalendar() {
      weekRows.innerHTML = monthWeeks(state.selectedMonth).map(week => `
        <div class="week-row">
          ${week.map(dayCard).join('')}
          ${weekTotal(week)}
        </div>`).join('');
      document.querySelectorAll('[data-date]').forEach(button => {
        button.addEventListener('click', () => openDay(button.dataset.date));
      });
    }

    function openDay(dateKey) {
      const day = state.payload.days[dateKey];
      if (!day) return;
      document.getElementById('modal-title').textContent = longDate(dateKey);
      document.getElementById('modal-summary').innerHTML =
        `${day.trade_count} trade${day.trade_count === 1 ? '' : 's'} · ` +
        `<span class="${toneClass(day.pnl)}">${formatMoney(day.pnl)}</span>`;
      const rows = day.trades.map(trade => `
        <tr>
          <td><strong>${escapeHtml(trade.symbol)}</strong></td>
          <td>${escapeHtml(trade.time ? trade.time.slice(0, 5) : '—')}</td>
          <td class="${trade.side === 'BUY' ? 'side-buy' : trade.side === 'SELL' ? 'side-sell' : ''}">${escapeHtml(trade.side || '—')}</td>
          <td class="number">${Number(trade.quantity).toLocaleString('en-US', { maximumFractionDigits: 6 })}</td>
          <td class="number">${formatMoney(trade.price)}</td>
          <td class="number money ${toneClass(trade.pnl)}">${formatMoney(trade.pnl)}</td>
          <td class="number">${formatMoney(trade.commission)}</td>
          <td>${escapeHtml(trade.description || '')}</td>
        </tr>`).join('');
      document.getElementById('modal-body').innerHTML = `
        <table>
          <thead><tr><th>Symbol</th><th>Time</th><th>Side</th><th class="number">Quantity</th><th class="number">Price</th><th class="number">Realized P&L</th><th class="number">Commission</th><th>Description</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>`;
      dialog.showModal();
    }

    function renderMonthSelector() {
      monthSelect.innerHTML = state.payload.months.map(month =>
        `<option value="${month}" ${month === state.selectedMonth ? 'selected' : ''}>${escapeHtml(monthName(month))}</option>`
      ).join('');
      const index = state.payload.months.indexOf(state.selectedMonth);
      document.getElementById('previous-month').disabled = index <= 0;
      document.getElementById('next-month').disabled = index >= state.payload.months.length - 1;
    }

    function currentAnalysis() {
      return state.analysisScope === 'all'
        ? state.payload.analysis.all
        : state.payload.analysis.months[state.analysisScope];
    }

    function renderAnalysisPeriodSelector() {
      const options = [
        `<option value="all" ${state.analysisScope === 'all' ? 'selected' : ''}>Entire file</option>`,
        ...state.payload.months.slice().reverse().map(month =>
          `<option value="${month}" ${state.analysisScope === month ? 'selected' : ''}>${escapeHtml(monthName(month))}</option>`
        )
      ];
      analysisPeriodSelect.innerHTML = options.join('');
    }

    function renderSymbolRankSelector() {
      const symbols = state.payload.analysis.all.symbols
        .filter(row => row.closed_execution_count > 0)
        .map(row => row.symbol)
        .sort();
      document.getElementById('trade-symbols').innerHTML = symbols
        .map(symbol => `<option value="${escapeHtml(symbol)}"></option>`).join('');
    }

    const rankFeatures = [
      { key: 'float', value: metadata => metadata?.float_shares > 0 ? Math.log10(metadata.float_shares) : null },
      { key: 'marketCap', value: metadata => metadata?.market_cap > 0 ? Math.log10(metadata.market_cap) : null },
      { key: 'volume10d', value: metadata => metadata?.average_volume_10d > 0 ? Math.log10(metadata.average_volume_10d) : null },
      { key: 'turnover', value: metadata => metadata?.float_shares > 0 && metadata?.average_volume_10d > 0 ? Math.log10(metadata.average_volume_10d / metadata.float_shares) : null },
      { key: 'price', value: metadata => metadata?.current_price > 0 ? Math.log10(metadata.current_price) : null },
      { key: 'beta', value: metadata => metadata?.beta != null && Number.isFinite(Number(metadata.beta)) ? Number(metadata.beta) : null },
      { key: 'shortFloat', value: metadata => metadata?.short_percent_float != null && Number.isFinite(Number(metadata.short_percent_float)) ? Number(metadata.short_percent_float) : null },
      { key: 'insiderOwnership', value: metadata => metadata?.held_percent_insiders != null && Number.isFinite(Number(metadata.held_percent_insiders)) ? Number(metadata.held_percent_insiders) : null },
      { key: 'institutionalOwnership', value: metadata => metadata?.held_percent_institutions != null && Number.isFinite(Number(metadata.held_percent_institutions)) ? Number(metadata.held_percent_institutions) : null }
    ];

    function percentileRank(value, values) {
      const valid = values.filter(item => item != null && Number.isFinite(Number(item))).map(Number).sort((a, b) => a - b);
      if (value == null || !valid.length || !Number.isFinite(Number(value))) return .5;
      const below = valid.filter(item => item < value).length;
      const equal = valid.filter(item => item === value).length;
      return (below + equal * .5) / valid.length;
    }

    function rankLabel(score) {
      if (score >= 70) return 'Strong historical fit';
      if (score >= 58) return 'Above-average fit';
      if (score >= 43) return 'Neutral fit';
      if (score >= 30) return 'Below-average fit';
      return 'Weak historical fit';
    }

    function rankConfidence(featureCoverage, neighborCount, neighborExits, averageSimilarity) {
      if (featureCoverage >= .75 && neighborCount >= 8 && neighborExits >= 40 && averageSimilarity >= .4) return 'High confidence';
      if (featureCoverage >= .5 && neighborCount >= 5 && neighborExits >= 20 && averageSimilarity >= .25) return 'Moderate confidence';
      return 'Low confidence';
    }

    function renderSymbolRank(symbol, requestMetadata = true) {
      const cleaned = String(symbol || '').trim().toUpperCase();
      const target = document.getElementById('symbol-odds-result');
      const input = document.getElementById('symbol-odds-input');
      if (!cleaned) {
        state.selectedRankSymbol = null;
        target.innerHTML = '<div class="odds-empty">Enter a symbol—even one you have never traded—to calculate its historical-fit rank.</div>';
        return;
      }
      if (!/^[A-Z0-9.^=\-]{1,32}$/.test(cleaned)) {
        target.innerHTML = `<div class="odds-empty"><strong>${escapeHtml(cleaned)}</strong> is not a supported Yahoo ticker format.</div>`;
        return;
      }
      input.value = cleaned;
      state.selectedRankSymbol = cleaned;
      const allRows = state.payload.analysis.all.symbols
        .filter(row => row.closed_execution_count > 0);
      const desiredSymbols = [...new Set([cleaned, ...allRows.map(row => row.symbol)])];
      const pending = desiredSymbols
        .filter(symbolName => !state.symbolMetadata[symbolName]);
      if (pending.length) {
        const loaded = desiredSymbols.length - pending.length;
        target.innerHTML = `<div class="odds-empty">Loading Yahoo profiles for ranking <strong>${escapeHtml(cleaned)}</strong>… ${Math.max(0, loaded)}/${desiredSymbols.length} available.</div>`;
        if (requestMetadata) loadYahooMetadata(desiredSymbols);
        return;
      }
      const targetMetadata = state.symbolMetadata[cleaned];
      if (!targetMetadata || targetMetadata.error) {
        target.innerHTML = `<div class="odds-empty">Yahoo profile data is unavailable for <strong>${escapeHtml(cleaned)}</strong>. ${escapeHtml(targetMetadata?.error || 'Try Refresh Yahoo data.')}</div>`;
        return;
      }
      const candidates = allRows
        .filter(row => row.symbol !== cleaned)
        .filter(row => {
          const metadata = state.symbolMetadata[row.symbol];
          return metadata && !metadata.error;
        });
      const featureStats = rankFeatures.map(feature => {
        const values = candidates.map(row => feature.value(state.symbolMetadata[row.symbol]))
          .filter(value => value != null && Number.isFinite(Number(value))).map(Number);
        const mean = values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
        const variance = mean == null || values.length < 2
          ? 0
          : values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length;
        return { feature, mean, deviation: Math.sqrt(variance) };
      });
      const comparisons = candidates.map(row => {
        const metadata = state.symbolMetadata[row.symbol];
        let squaredDistance = 0;
        let sharedFeatures = 0;
        featureStats.forEach(({ feature, deviation }) => {
          const targetValue = feature.value(targetMetadata);
          const candidateValue = feature.value(metadata);
          if (
            targetValue != null && candidateValue != null &&
            Number.isFinite(Number(targetValue)) &&
            Number.isFinite(Number(candidateValue)) &&
            deviation > .000001
          ) {
            const difference = (Number(targetValue) - Number(candidateValue)) / deviation;
            squaredDistance += Math.min(9, difference * difference);
            sharedFeatures += 1;
          }
        });
        if (sharedFeatures < 3) return null;
        const distance = Math.sqrt(squaredDistance / sharedFeatures);
        let similarity = Math.exp(-distance);
        if (targetMetadata.sector && targetMetadata.sector === metadata.sector) similarity *= 1.15;
        if (targetMetadata.industry && targetMetadata.industry === metadata.industry) similarity *= 1.1;
        similarity = Math.min(1, similarity);
        return { row, metadata, similarity, sharedFeatures };
      }).filter(Boolean).sort((left, right) => right.similarity - left.similarity).slice(0, 12);

      if (comparisons.length < 3) {
        target.innerHTML = `<div class="odds-empty">Not enough comparable Yahoo profiles are available to rank <strong>${escapeHtml(cleaned)}</strong>. At least three comparable traded symbols are required.</div>`;
        return;
      }
      let weightTotal = 0, winTotal = 0, pnlTotal = 0, profitFactorTotal = 0;
      comparisons.forEach(comparison => {
        const row = comparison.row;
        const weight = comparison.similarity * Math.min(3, Math.sqrt(row.closed_execution_count));
        const profitFactor = row.gross_loss > 0
          ? Math.min(5, row.gross_profit / row.gross_loss)
          : row.gross_profit > 0 ? 5 : 0;
        comparison.weight = weight;
        comparison.profit_factor = profitFactor;
        weightTotal += weight;
        winTotal += weight * Number(row.win_rate || 0);
        pnlTotal += weight * Number(row.pnl_per_share || 0);
        profitFactorTotal += weight * profitFactor;
      });
      const neighborWinRate = weightTotal ? winTotal / weightTotal : 0;
      const weightedPnlPerShare = weightTotal ? pnlTotal / weightTotal : 0;
      const weightedProfitFactor = weightTotal ? profitFactorTotal / weightTotal : 0;
      const overallRate = Number(state.payload.analysis.all.overview.win_rate || .5);
      const priorWeight = 5;
      const estimatedSuccess = (neighborWinRate * weightTotal + overallRate * priorWeight) / (weightTotal + priorWeight);
      const pnlPercentile = percentileRank(
        weightedPnlPerShare,
        candidates.map(row => row.pnl_per_share)
      );
      const profitFactorPercentile = percentileRank(
        weightedProfitFactor,
        candidates.map(row => row.gross_loss > 0 ? Math.min(5, row.gross_profit / row.gross_loss) : 5)
      );
      const score = Math.max(0, Math.min(100,
        100 * (.55 * estimatedSuccess + .30 * pnlPercentile + .15 * profitFactorPercentile)
      ));
      const availableFeatures = rankFeatures
        .filter(feature => {
          const value = feature.value(targetMetadata);
          return value != null && Number.isFinite(Number(value));
        }).length;
      const featureCoverage = availableFeatures / rankFeatures.length;
      const neighborExits = comparisons.reduce((sum, comparison) =>
        sum + comparison.row.closed_execution_count, 0);
      const averageSimilarity = comparisons.reduce((sum, comparison) =>
        sum + comparison.similarity, 0) / comparisons.length;
      const confidence = rankConfidence(
        featureCoverage, comparisons.length, neighborExits, averageSimilarity
      );
      const ownHistory = allRows.find(row => row.symbol === cleaned);
      const profile = [
        targetMetadata.float_shares ? `Float ${formatShares(targetMetadata.float_shares)}` : null,
        targetMetadata.market_cap ? `Market cap ${formatCompactMoney(targetMetadata.market_cap)}` : null,
        targetMetadata.average_volume_10d ? `10-day volume ${formatShares(targetMetadata.average_volume_10d)}` : null,
        targetMetadata.sector || null,
        targetMetadata.industry || null
      ].filter(Boolean).join(' · ');
      const cards = [
        ['Historical-fit rank', `${score.toFixed(0)}/100`, rankLabel(score), score - 50],
        ['Estimated success', formatPercent(estimatedSuccess), `Overall baseline ${formatPercent(overallRate)}`, estimatedSuccess - overallRate],
        ['Comparable symbols', String(comparisons.length), `${neighborExits} combined exits`, comparisons.length - 5],
        ['Neighbor P&L/share', formatPerShare(weightedPnlPerShare), `${Math.round(pnlPercentile * 100)}th percentile`, weightedPnlPerShare],
        ['Neighbor profit factor', formatRatio(weightedProfitFactor), `${Math.round(profitFactorPercentile * 100)}th percentile`, weightedProfitFactor - 1],
        ['Profile coverage', formatPercent(featureCoverage), `${availableFeatures}/${rankFeatures.length} numeric properties`, featureCoverage - .5]
      ];
      target.innerHTML = `
        <div class="odds-result-header">
          <div class="odds-symbol"><a class="symbol-link" href="${yahooFinanceUrl(cleaned)}" target="_blank" rel="noopener noreferrer">${escapeHtml(cleaned)}</a><span class="evidence-badge">${escapeHtml(confidence)}</span></div>
          <div class="panel-subtitle">${escapeHtml(profile)}</div>
        </div>
        <div class="odds-grid">${cards.map(([label, value, detail, tone]) => `<div class="odds-card">
          <div class="odds-label">${escapeHtml(label)}</div>
          <div class="odds-value ${toneClass(Number(tone || 0))}">${escapeHtml(value)}</div>
          <div class="odds-detail">${escapeHtml(detail)}</div>
        </div>`).join('')}</div>
        <div class="confidence-wrap">
          <div class="confidence-copy"><span>Historical-fit score combines estimated success (55%), P&amp;L/share percentile (30%), and profit-factor percentile (15%).</span><span>${score.toFixed(0)}/100</span></div>
          <div class="confidence-track"><div class="confidence-range" style="left:0;width:${score.toFixed(2)}%"></div><div class="confidence-marker" style="left:${score.toFixed(2)}%"></div></div>
        </div>
        <div class="panel-subtitle">The closest matches are based on normalized float, market cap, 10-day volume, float turnover, price, beta, short interest, and ownership. Sector and industry matches receive a small similarity boost.${ownHistory ? ` ${escapeHtml(cleaned)}'s own ${ownHistory.closed_execution_count} exits were excluded from the model.` : ''}</div>
        <div class="metric-table-wrap" style="margin-top:13px"><table class="metric-table">
          <thead><tr><th>Comparable symbol</th><th class="number">Similarity</th><th class="number">Float</th><th>Sector</th><th class="number">Exits</th><th class="number">Win rate</th><th class="number">P&amp;L/share</th><th class="number">Total P&amp;L</th></tr></thead>
          <tbody>${comparisons.map(comparison => `<tr>
            <td><a class="symbol-link" href="${yahooFinanceUrl(comparison.row.symbol)}" target="_blank" rel="noopener noreferrer">${escapeHtml(comparison.row.symbol)}</a></td>
            <td class="number">${formatPercent(comparison.similarity)}</td>
            <td class="number">${formatShares(comparison.metadata.float_shares)}</td>
            <td>${escapeHtml(comparison.metadata.sector || 'N/A')}</td>
            <td class="number">${comparison.row.closed_execution_count}</td>
            <td class="number">${formatPercent(comparison.row.win_rate)}</td>
            <td class="number ${toneClass(comparison.row.pnl_per_share)}">${formatPerShare(comparison.row.pnl_per_share)}</td>
            <td class="number money ${toneClass(comparison.row.total_pnl)}">${formatMoney(comparison.row.total_pnl)}</td>
          </tr>`).join('')}</tbody>
        </table></div>`;
    }

    function renderBarChart(elementId, rows, valueKey, valueFormatter, detailFormatter) {
      const target = document.getElementById(elementId);
      if (!rows.length) {
        target.innerHTML = '<div class="chart-empty">No matching realized executions are available for this period.</div>';
        return;
      }
      const maximum = Math.max(...rows.map(row => Math.abs(Number(row[valueKey] || 0))), 0.01);
      target.innerHTML = `<div class="bar-chart">${rows.map(row => {
        const value = Number(row[valueKey] || 0);
        const width = Math.max(2, Math.abs(value) / maximum * 100);
        return `<div class="bar-row">
          <div class="bar-label" title="${escapeHtml(row.label)}">${escapeHtml(row.label)}</div>
          <div class="bar-track"><div class="bar-fill ${value >= 0 ? 'positive' : 'negative'}" style="width:${width.toFixed(2)}%"></div></div>
          <div class="bar-value ${toneClass(value)}">${valueFormatter(value)}</div>
          <div class="bar-detail">${escapeHtml(detailFormatter(row))}</div>
        </div>`;
      }).join('')}</div>`;
    }

    function renderEquityCurve(rows) {
      const target = document.getElementById('equity-chart');
      if (!rows.length) {
        target.innerHTML = '<div class="chart-empty">No daily P&amp;L is available for this period.</div>';
        return;
      }
      const width = 900, height = 260, left = 58, right = 16, top = 18, bottom = 32;
      const chartWidth = width - left - right, chartHeight = height - top - bottom;
      const values = rows.map(row => Number(row.cumulative_pnl || 0));
      let minimum = Math.min(0, ...values), maximum = Math.max(0, ...values);
      if (minimum === maximum) { minimum -= 1; maximum += 1; }
      const x = index => left + (rows.length === 1 ? chartWidth / 2 : index / (rows.length - 1) * chartWidth);
      const y = value => top + (maximum - value) / (maximum - minimum) * chartHeight;
      const points = values.map((value, index) => `${x(index).toFixed(2)},${y(value).toFixed(2)}`).join(' ');
      const baseY = y(0);
      const areaPoints = `${left},${baseY.toFixed(2)} ${points} ${x(rows.length - 1).toFixed(2)},${baseY.toFixed(2)}`;
      const midpoint = Math.floor((rows.length - 1) / 2);
      target.innerHTML = `<svg class="equity-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Cumulative P and L curve">
        <defs><linearGradient id="equity-gradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6eb8ff" stop-opacity=".28"/><stop offset="1" stop-color="#6eb8ff" stop-opacity=".02"/></linearGradient></defs>
        <line class="equity-grid" x1="${left}" y1="${top}" x2="${width - right}" y2="${top}"/>
        <line class="equity-grid" x1="${left}" y1="${top + chartHeight}" x2="${width - right}" y2="${top + chartHeight}"/>
        <line class="equity-zero" x1="${left}" y1="${baseY}" x2="${width - right}" y2="${baseY}"/>
        <polygon class="equity-area" points="${areaPoints}"/>
        <polyline class="equity-line" points="${points}"/>
        <text class="equity-axis" x="4" y="${top + 4}">${escapeHtml(formatMoney(maximum))}</text>
        <text class="equity-axis" x="4" y="${top + chartHeight}">${escapeHtml(formatMoney(minimum))}</text>
        <text class="equity-axis" x="${left}" y="${height - 8}">${escapeHtml(shortDate(rows[0].date))}</text>
        <text class="equity-axis" x="${x(midpoint)}" y="${height - 8}" text-anchor="middle">${escapeHtml(shortDate(rows[midpoint].date))}</text>
        <text class="equity-axis" x="${width - right}" y="${height - 8}" text-anchor="end">${escapeHtml(shortDate(rows[rows.length - 1].date))}</text>
      </svg>`;
    }

    function emptyMetadataGroup(label, order = 0) {
      return {
        label, order, symbol_count: 0, closed_execution_count: 0,
        winning_execution_count: 0, total_pnl: 0, gross_profit: 0,
        gross_loss: 0, closed_shares: 0
      };
    }

    function addSymbolToMetadataGroup(group, row) {
      group.symbol_count += 1;
      group.closed_execution_count += Number(row.closed_execution_count || 0);
      group.winning_execution_count += Number(row.winning_execution_count || 0);
      group.total_pnl += Number(row.total_pnl || 0);
      group.gross_profit += Number(row.gross_profit || 0);
      group.gross_loss += Number(row.gross_loss || 0);
      group.closed_shares += Number(row.closed_shares || 0);
    }

    function finalizeMetadataGroup(group) {
      return {
        ...group,
        win_rate: group.closed_execution_count
          ? group.winning_execution_count / group.closed_execution_count : null,
        pnl_per_share: group.closed_shares
          ? group.total_pnl / group.closed_shares : null,
        average_pnl: group.closed_execution_count
          ? group.total_pnl / group.closed_execution_count : null,
        profit_factor: group.gross_loss
          ? group.gross_profit / group.gross_loss : null
      };
    }

    function aggregateByBuckets(rows, buckets, valueGetter) {
      const groups = buckets.map((bucket, index) => emptyMetadataGroup(bucket.label, index));
      rows.forEach(row => {
        if (!row.closed_execution_count) return;
        const metadata = state.symbolMetadata[row.symbol];
        const value = valueGetter(metadata, row);
        if (value == null || !Number.isFinite(Number(value))) return;
        const index = buckets.findIndex(bucket =>
          Number(value) >= bucket.minimum && Number(value) < bucket.maximum);
        if (index >= 0) addSymbolToMetadataGroup(groups[index], row);
      });
      return groups.filter(group => group.symbol_count).map(finalizeMetadataGroup);
    }

    function aggregateByCategory(rows, categoryGetter) {
      const groups = new Map();
      rows.forEach(row => {
        if (!row.closed_execution_count) return;
        const category = categoryGetter(state.symbolMetadata[row.symbol], row);
        if (!category) return;
        if (!groups.has(category)) groups.set(category, emptyMetadataGroup(category));
        addSymbolToMetadataGroup(groups.get(category), row);
      });
      return [...groups.values()].map(finalizeMetadataGroup);
    }

    function renderMetadataBucketTable(elementId, rows, note) {
      const target = document.getElementById(elementId);
      if (!rows.length) {
        target.innerHTML = '<div class="chart-empty">Yahoo profile data is loading or unavailable for this period.</div>';
        return;
      }
      target.innerHTML = `<div class="metric-table-wrap"><table class="metric-table">
        <thead><tr><th>Range</th><th class="number">Symbols</th><th class="number">Exits</th><th class="number">Win rate</th><th class="number">P&amp;L/share</th><th class="number">Profit factor</th><th class="number">Total P&amp;L</th></tr></thead>
        <tbody>${rows.map(row => `<tr>
          <td><strong>${escapeHtml(row.label)}</strong></td>
          <td class="number">${row.symbol_count}</td>
          <td class="number">${row.closed_execution_count}</td>
          <td class="number">${formatPercent(row.win_rate)}</td>
          <td class="number ${toneClass(row.pnl_per_share)}">${formatPerShare(row.pnl_per_share)}</td>
          <td class="number">${formatRatio(row.profit_factor)}</td>
          <td class="number money ${toneClass(row.total_pnl)}">${formatMoney(row.total_pnl)}</td>
        </tr>`).join('')}</tbody>
      </table></div><div class="bucket-note">${escapeHtml(note)}</div>`;
    }

    function renderSectorTable(rows) {
      const target = document.getElementById('sector-table');
      const visible = rows.slice().sort((a, b) =>
        (b.pnl_per_share ?? -Infinity) - (a.pnl_per_share ?? -Infinity)).slice(0, 12);
      if (!visible.length) {
        target.innerHTML = '<div class="chart-empty">Sector data is loading or unavailable.</div>';
        return;
      }
      target.innerHTML = `<div class="metric-table-wrap"><table class="metric-table">
        <thead><tr><th>Sector</th><th class="number">Symbols</th><th class="number">Exits</th><th class="number">Win rate</th><th class="number">P&amp;L/share</th><th class="number">Total P&amp;L</th></tr></thead>
        <tbody>${visible.map(row => `<tr>
          <td><strong>${escapeHtml(row.label)}</strong></td>
          <td class="number">${row.symbol_count}</td>
          <td class="number">${row.closed_execution_count}</td>
          <td class="number">${formatPercent(row.win_rate)}</td>
          <td class="number ${toneClass(row.pnl_per_share)}">${formatPerShare(row.pnl_per_share)}</td>
          <td class="number money ${toneClass(row.total_pnl)}">${formatMoney(row.total_pnl)}</td>
        </tr>`).join('')}</tbody>
      </table></div>`;
    }

    function renderFloatScatter(rows) {
      const target = document.getElementById('float-scatter');
      const points = rows.filter(row => {
        const metadata = state.symbolMetadata[row.symbol];
        return metadata?.float_shares > 0 && row.pnl_per_share != null;
      });
      if (points.length < 2) {
        target.innerHTML = '<div class="chart-empty">At least two symbols with float data are needed for this view.</div>';
        return;
      }
      const width = 900, height = 310, left = 66, right = 22, top = 18, bottom = 42;
      const chartWidth = width - left - right, chartHeight = height - top - bottom;
      const logs = points.map(row => Math.log10(state.symbolMetadata[row.symbol].float_shares));
      const pnlValues = points.map(row => Number(row.pnl_per_share));
      let minX = Math.floor(Math.min(...logs)), maxX = Math.ceil(Math.max(...logs));
      if (minX === maxX) maxX += 1;
      let minY = Math.min(0, ...pnlValues), maxY = Math.max(0, ...pnlValues);
      if (minY === maxY) { minY -= .01; maxY += .01; }
      const x = value => left + (Math.log10(value) - minX) / (maxX - minX) * chartWidth;
      const y = value => top + (maxY - value) / (maxY - minY) * chartHeight;
      const xTicks = [];
      for (let exponent = minX; exponent <= maxX; exponent += 1) xTicks.push(exponent);
      const zeroY = y(0);
      target.innerHTML = `<svg class="scatter-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Float versus profit and loss per share">
        ${xTicks.map(exponent => `<line class="scatter-grid" x1="${x(10 ** exponent)}" y1="${top}" x2="${x(10 ** exponent)}" y2="${height - bottom}"/>`).join('')}
        <line class="scatter-zero" x1="${left}" y1="${zeroY}" x2="${width - right}" y2="${zeroY}"/>
        ${points.map(row => {
          const metadata = state.symbolMetadata[row.symbol];
          const radius = Math.min(9, 3.5 + Math.sqrt(row.closed_execution_count || 1));
          return `<circle class="scatter-point ${row.pnl_per_share >= 0 ? 'positive' : 'negative'}" cx="${x(metadata.float_shares)}" cy="${y(row.pnl_per_share)}" r="${radius}"><title>${escapeHtml(`${row.symbol} · Float ${formatShares(metadata.float_shares)} · ${formatPerShare(row.pnl_per_share)} · ${row.closed_execution_count} exits`)}</title></circle>`;
        }).join('')}
        ${xTicks.map(exponent => `<text class="scatter-axis" x="${x(10 ** exponent)}" y="${height - 15}" text-anchor="middle">${escapeHtml(formatShares(10 ** exponent))}</text>`).join('')}
        <text class="scatter-axis" x="${left}" y="12">${escapeHtml(formatPerShare(maxY))}</text>
        <text class="scatter-axis" x="${left}" y="${height - bottom + 14}">${escapeHtml(formatPerShare(minY))}</text>
        <text class="scatter-axis" x="${width / 2}" y="${height - 2}" text-anchor="middle">Current float</text>
      </svg>`;
    }

    function renderMetadataAnalysis(analysis) {
      if (!analysis) return;
      const rows = analysis.symbols.filter(row => row.closed_execution_count > 0);
      const loaded = rows.filter(row => state.symbolMetadata[row.symbol]);
      const successful = loaded.filter(row => !state.symbolMetadata[row.symbol].error);
      const withFloat = rows.filter(row => state.symbolMetadata[row.symbol]?.float_shares > 0);
      const withMarketCap = rows.filter(row => state.symbolMetadata[row.symbol]?.market_cap > 0);
      const withSector = rows.filter(row => state.symbolMetadata[row.symbol]?.sector);
      const withTurnover = rows.filter(row => {
        const metadata = state.symbolMetadata[row.symbol];
        return metadata?.float_shares > 0 && metadata?.average_volume_10d > 0;
      });

      const floatBuckets = [
        { label: 'Under 1M', minimum: 0, maximum: 1e6 },
        { label: '1M–5M', minimum: 1e6, maximum: 5e6 },
        { label: '5M–10M', minimum: 5e6, maximum: 10e6 },
        { label: '10M–20M', minimum: 10e6, maximum: 20e6 },
        { label: '20M–50M', minimum: 20e6, maximum: 50e6 },
        { label: '50M–100M', minimum: 50e6, maximum: 100e6 },
        { label: '100M+', minimum: 100e6, maximum: Infinity }
      ];
      const marketCapBuckets = [
        { label: 'Under $50M', minimum: 0, maximum: 50e6 },
        { label: '$50M–$300M', minimum: 50e6, maximum: 300e6 },
        { label: '$300M–$2B', minimum: 300e6, maximum: 2e9 },
        { label: '$2B–$10B', minimum: 2e9, maximum: 10e9 },
        { label: '$10B+', minimum: 10e9, maximum: Infinity }
      ];
      const turnoverBuckets = [
        { label: 'Under 0.10×', minimum: 0, maximum: .1 },
        { label: '0.10×–0.25×', minimum: .1, maximum: .25 },
        { label: '0.25×–0.50×', minimum: .25, maximum: .5 },
        { label: '0.50×–1.00×', minimum: .5, maximum: 1 },
        { label: '1.00×–2.00×', minimum: 1, maximum: 2 },
        { label: '2.00×+', minimum: 2, maximum: Infinity }
      ];
      const floatRows = aggregateByBuckets(rows, floatBuckets,
        metadata => metadata?.float_shares);
      const marketCapRows = aggregateByBuckets(rows, marketCapBuckets,
        metadata => metadata?.market_cap);
      const turnoverRows = aggregateByBuckets(rows, turnoverBuckets,
        metadata => metadata?.float_shares > 0 && metadata?.average_volume_10d > 0
          ? metadata.average_volume_10d / metadata.float_shares : null);
      const sectorRows = aggregateByCategory(rows, metadata => metadata?.sector);

      renderMetadataBucketTable('float-bucket-table', floatRows,
        'A float range needs at least five closed executions before it is considered a qualified result.');
      renderBarChart('market-cap-chart', marketCapRows, 'pnl_per_share', formatPerShare,
        row => `${row.symbol_count} symbols · ${row.closed_execution_count} exits · ${formatPercent(row.win_rate)} wins`);
      renderBarChart('turnover-chart', turnoverRows, 'pnl_per_share', formatPerShare,
        row => `${row.symbol_count} symbols · ${row.closed_execution_count} exits · ${formatPercent(row.win_rate)} wins`);
      renderSectorTable(sectorRows);
      renderFloatScatter(rows);

      const coverageRows = [
        { label: 'Profile loaded', value: rows.length ? successful.length / rows.length : 0 },
        { label: 'Float', value: rows.length ? withFloat.length / rows.length : 0 },
        { label: 'Market cap', value: rows.length ? withMarketCap.length / rows.length : 0 },
        { label: 'Sector', value: rows.length ? withSector.length / rows.length : 0 },
        { label: 'Turnover', value: rows.length ? withTurnover.length / rows.length : 0 }
      ];
      renderBarChart('metadata-coverage', coverageRows, 'value', formatPercent,
        () => 'Current Yahoo coverage');

      const qualified = floatRows.filter(row => row.closed_execution_count >= 5 && row.pnl_per_share != null);
      const best = qualified.length
        ? qualified.reduce((winner, row) => row.pnl_per_share > winner.pnl_per_share ? row : winner, qualified[0])
        : null;
      const status = document.getElementById('metadata-status');
      const statusCopy = status.querySelector('span');
      statusCopy.textContent = best
        ? `Best qualified current-float range: ${best.label}, averaging ${formatPerShare(best.pnl_per_share)} across ${best.closed_execution_count} exits.`
        : 'Yahoo company-profile analysis uses current values—not historical values from each trade date.';
      document.getElementById('metadata-progress').textContent = state.metadataLoading
        ? `Loaded ${loaded.length}/${rows.length} profiles`
        : `${successful.length}/${rows.length} profiles available`;
    }

    function floatCell(symbol) {
      const entry = state.symbolMetadata[symbol];
      if (!entry) {
        return '<span class="float-unavailable">Loading…</span>';
      }
      if (entry.float_shares == null) {
        return `<span class="float-unavailable" title="${escapeHtml(entry.error || 'Yahoo Finance does not have a float value for this symbol.')}\">N/A</span>`;
      }
      const exact = Number(entry.float_shares).toLocaleString('en-US');
      const fetched = entry.fetched_at
        ? new Date(entry.fetched_at).toLocaleString()
        : 'unknown time';
      return `<span class="float-value" title="${escapeHtml(`${exact} shares · Yahoo Finance · updated ${fetched}`)}">${escapeHtml(formatShares(entry.float_shares))}</span>`;
    }

    function marketCapCell(symbol) {
      const entry = state.symbolMetadata[symbol];
      return entry?.market_cap == null
        ? '<span class="float-unavailable">N/A</span>'
        : `<span class="float-value">${escapeHtml(formatCompactMoney(entry.market_cap))}</span>`;
    }

    function sectorCell(symbol) {
      const entry = state.symbolMetadata[symbol];
      return `<span title="${escapeHtml(entry?.industry || '')}">${escapeHtml(entry?.sector || 'N/A')}</span>`;
    }

    async function loadYahooMetadata(symbols, forceRefresh = false) {
      const requested = [...new Set(symbols)]
        .filter(symbol => forceRefresh || !state.symbolMetadata[symbol]);
      if (!requested.length || state.metadataLoading) {
        renderMetadataAnalysis(currentAnalysis());
        return;
      }
      state.metadataLoading = true;
      const refreshButton = document.getElementById('refresh-floats');
      const floatStatus = document.getElementById('float-status');
      const progress = document.getElementById('metadata-progress');
      refreshButton.disabled = true;
      refreshButton.textContent = 'Loading Yahoo data…';
      floatStatus.classList.add('hidden');
      let processed = 0;
      try {
        if (window.__TRADE_PAYLOAD__) {
          requested.forEach(symbol => {
            state.symbolMetadata[symbol] = {
              fetched_at: null,
              error: 'Yahoo enrichment is available in the live Python dashboard.'
            };
          });
        } else {
          const batchSize = 10;
          for (let offset = 0; offset < requested.length; offset += batchSize) {
            const batch = requested.slice(offset, offset + batchSize);
            progress.textContent = `Loading ${processed}/${requested.length} symbols`;
            const parameters = new URLSearchParams({ symbols: batch.join(',') });
            if (forceRefresh) parameters.set('refresh', '1');
            const response = await fetch(`/api/symbol-metadata?${parameters.toString()}`, { cache: 'no-store' });
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.error || 'Unable to load Yahoo company data.');
            Object.assign(state.symbolMetadata, payload.symbols || {});
            processed += batch.length;
            const entries = Object.values(payload.symbols || {});
            const dependencyError = entries.find(entry =>
              String(entry.error || '').includes('requires yfinance'));
            renderMetadataAnalysis(currentAnalysis());
            renderSymbolTable(currentAnalysis().symbols, false);
            if (dependencyError) {
              requested.slice(processed).forEach(symbol => {
                state.symbolMetadata[symbol] = { ...dependencyError };
              });
              throw new Error(dependencyError.error);
            }
          }
        }
      } catch (error) {
        requested.filter(symbol => !state.symbolMetadata[symbol]).forEach(symbol => {
          state.symbolMetadata[symbol] = {
            fetched_at: null,
            error: error.message || 'Yahoo Finance is temporarily unavailable.'
          };
        });
        floatStatus.textContent = error.message || 'Yahoo Finance is temporarily unavailable.';
        floatStatus.classList.remove('hidden');
      } finally {
        state.metadataLoading = false;
        refreshButton.disabled = false;
        refreshButton.textContent = 'Refresh Yahoo data';
        renderMetadataAnalysis(currentAnalysis());
        renderSymbolTable(currentAnalysis().symbols, false);
        if (state.selectedRankSymbol) {
          renderSymbolRank(state.selectedRankSymbol, false);
        }
        const remaining = [
          ...currentAnalysis().symbols.map(row => row.symbol),
          ...(state.selectedRankSymbol ? [state.selectedRankSymbol] : [])
        ]
          .filter(symbol => !state.symbolMetadata[symbol]);
        if (remaining.length && state.selectedView === 'analysis') {
          setTimeout(() => loadYahooMetadata(remaining), 0);
        }
      }
    }

    function renderSymbolTable(rows, requestMetadata = true) {
      const target = document.getElementById('symbol-table');
      const visible = rows.filter(row => row.closed_execution_count > 0).slice(0, 20);
      state.visibleSymbols = visible.map(row => row.symbol);
      if (!visible.length) {
        target.innerHTML = '<div class="chart-empty">No realized symbol results are available.</div>';
        return;
      }
      target.innerHTML = `<div class="metric-table-wrap"><table class="metric-table">
        <thead><tr><th>Symbol</th><th class="number">Float</th><th class="number">Market cap</th><th>Sector</th><th class="number">Closed exits</th><th class="number">Win rate</th><th class="number">P&amp;L/share</th><th class="number">Total P&amp;L</th></tr></thead>
        <tbody>${visible.map(row => `<tr>
          <td><a class="symbol-link" href="${yahooFinanceUrl(row.symbol)}" target="_blank" rel="noopener noreferrer" aria-label="Open ${escapeHtml(row.symbol)} on Yahoo Finance">${escapeHtml(row.symbol)}</a></td>
          <td class="number">${floatCell(row.symbol)}</td>
          <td class="number">${marketCapCell(row.symbol)}</td>
          <td>${sectorCell(row.symbol)}</td>
          <td class="number">${row.closed_execution_count}</td>
          <td class="number">${formatPercent(row.win_rate)}</td>
          <td class="number ${toneClass(row.pnl_per_share)}">${row.pnl_per_share == null ? '—' : formatMoney(row.pnl_per_share)}</td>
          <td class="number money ${toneClass(row.total_pnl)}">${formatMoney(row.total_pnl)}</td>
        </tr>`).join('')}</tbody>
      </table></div>`;
      if (requestMetadata && state.selectedView === 'analysis') {
        loadYahooMetadata(rows.map(row => row.symbol));
      }
    }

    function renderMonthlyTable(rows) {
      const target = document.getElementById('monthly-table');
      if (!rows.length) {
        target.innerHTML = '<div class="chart-empty">No monthly results are available.</div>';
        return;
      }
      target.innerHTML = `<div class="metric-table-wrap"><table class="metric-table">
        <thead><tr><th>Month</th><th class="number">Exits</th><th class="number">Win rate</th><th class="number">P&amp;L</th></tr></thead>
        <tbody>${rows.slice().reverse().map(row => `<tr>
          <td>${escapeHtml(monthName(row.month))}</td>
          <td class="number">${row.closed_execution_count}</td>
          <td class="number">${formatPercent(row.win_rate)}</td>
          <td class="number money ${toneClass(row.total_pnl)}">${formatMoney(row.total_pnl)}</td>
        </tr>`).join('')}</tbody>
      </table></div>`;
    }

    function renderAnalysis() {
      const analysis = currentAnalysis();
      if (!analysis) return;
      const overview = analysis.overview;
      const bestHour = analysis.best_hour;
      const strongestWeekday = analysis.weekdays.length
        ? analysis.weekdays.reduce((best, row) => row.average_daily_pnl > best.average_daily_pnl ? row : best, analysis.weekdays[0])
        : null;
      const kpis = [
        ['Avg profit/share — good trades', formatPerShare(overview.average_profit_per_share_good_trades), `${overview.winning_execution_count} profitable closing executions`, true, overview.average_profit_per_share_good_trades],
        ['Best average exit hour', bestHour ? bestHour.label : '—', bestHour ? `${formatMoney(bestHour.average_pnl)} avg · ${bestHour.closed_execution_count} exits` : `Requires at least ${analysis.minimum_hour_sample} timed exits`, false, bestHour?.average_pnl],
        ['Exit win rate', formatPercent(overview.win_rate), `${overview.winning_execution_count} wins · ${overview.losing_execution_count} losses`, false, overview.win_rate == null ? 0 : overview.win_rate - .5],
        ['Profit factor', formatRatio(overview.profit_factor), `${formatMoney(overview.gross_profit)} gross profit`, false, overview.profit_factor == null ? 0 : overview.profit_factor - 1],
        ['Average winner / loser', `${formatMaybeMoney(overview.average_winner)} / ${formatMaybeMoney(overview.average_loser)}`, `Payoff ${formatRatio(overview.payoff_ratio)}`, false, (overview.average_winner || 0) + (overview.average_loser || 0)],
        ['Expectancy per exit', formatMaybeMoney(overview.expectancy_per_closed_execution), `${overview.closed_execution_count} closing executions`, false, overview.expectancy_per_closed_execution]
      ];
      document.getElementById('analysis-kpis').innerHTML = kpis.map(([label, value, detail, featured, tone]) => `<article class="analysis-kpi ${featured ? 'featured' : ''}">
        <div class="kpi-label">${escapeHtml(label)}</div>
        <div class="kpi-value ${toneClass(Number(tone || 0))}">${escapeHtml(value)}</div>
        <div class="kpi-detail">${escapeHtml(detail)}</div>
      </article>`).join('');

      const bestDay = overview.best_day;
      document.getElementById('analysis-insights').innerHTML = [
        ['Good-trade efficiency', `Each share closed profitably earned ${formatMaybeMoney(overview.average_profit_per_share_good_trades)} on average. Losing exits averaged ${formatMaybeMoney(overview.average_loss_per_share_bad_trades)} per share.`],
        ['Timing edge', bestHour ? `${bestHour.label} has the strongest average result at ${formatMoney(bestHour.average_pnl)} per exit, with a ${formatPercent(bestHour.win_rate)} win rate.` : 'No hourly ranking is available for this period.'],
        ['Consistency', strongestWeekday ? `${strongestWeekday.label} is the strongest weekday at ${formatMoney(strongestWeekday.average_daily_pnl)} per trading day. Best day: ${bestDay ? `${longDate(bestDay.date)} (${formatMoney(bestDay.pnl)})` : '—'}.` : 'No weekday results are available.']
      ].map(([title, copy]) => `<article class="insight-card"><div class="insight-title">${escapeHtml(title)}</div><div class="insight-copy">${escapeHtml(copy)}</div></article>`).join('');

      renderBarChart('hourly-chart', analysis.hourly, 'average_pnl', formatMoney,
        row => `${row.closed_execution_count} exits · ${formatPercent(row.win_rate)} wins · ${formatPerShare(row.pnl_per_share)}`);
      renderBarChart('weekday-chart', analysis.weekdays, 'average_daily_pnl', formatMoney,
        row => `${row.trading_days} days · ${formatPercent(row.profitable_day_rate)} profitable`);
      renderEquityCurve(analysis.equity_curve);
      renderMetadataAnalysis(analysis);
      renderSymbolTable(analysis.symbols);
      renderMonthlyTable(analysis.months);
      document.getElementById('analysis-definitions').innerHTML = `
        <div><dt>Good trade</dt><dd>${escapeHtml(analysis.definitions.good_trade)}</dd></div>
        <div><dt>Profit per share</dt><dd>${escapeHtml(analysis.definitions.profit_per_share)}</dd></div>
        <div><dt>Most profitable hour</dt><dd>Ranked by average realized P&amp;L and requires at least ${analysis.minimum_hour_sample} closing executions. ${escapeHtml(analysis.definitions.hour)}</dd></div>
        <div><dt>Yahoo company profile</dt><dd>Float, market cap, average volume, and sector are current cached values. They may differ from the values that existed on a historical trade date.</dd></div>
        <div><dt>Trade count</dt><dd>Calendar counts every CSV execution row. Analysis focuses on rows with non-zero realized P&amp;L and quantity.</dd></div>`;
    }

    function renderAll() {
      renderMonthSelector();
      renderSummary();
      renderCalendarBalanceChart();
      renderCalendar();
      renderAnalysisPeriodSelector();
      renderSymbolRankSelector();
      renderAnalysis();
      if (state.selectedRankSymbol) renderSymbolRank(state.selectedRankSymbol);
      setView(state.selectedView, false);
    }

    function formatSyncTime(value) {
      if (!value) return null;
      const parsed = new Date(value);
      return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
    }

    function renderIbkrStatus(status) {
      const statusElement = document.getElementById('ibkr-status');
      const snapshot = Boolean(window.__TRADE_PAYLOAD__);
      if (snapshot) {
        ibkrSyncButton.disabled = true;
        ibkrSyncButton.title = 'IBKR sync is available in the live WTC server.';
        statusElement.innerHTML = '<span class="status-dot warning"></span>Offline snapshot';
        return;
      }
      if (!status?.configured) {
        ibkrSyncButton.disabled = true;
        ibkrSyncButton.title = 'Add the Flex token and query ID to ibkr_flex.env.';
        statusElement.innerHTML = '<span class="status-dot warning"></span>IBKR sync not configured';
        return;
      }
      if (!status.activity_configured) {
        ibkrSyncButton.disabled = true;
        ibkrSyncButton.title = 'Add an Activity Flex Query ID to download finalized P&L.';
        statusElement.innerHTML = '<span class="status-dot warning"></span>IBKR Activity report not configured';
        return;
      }
      ibkrSyncButton.disabled = Boolean(status.running);
      ibkrSyncButton.title = status.running ? 'IBKR synchronization is running.' : 'Download the latest finalized Activity report now.';
      const finalSync = formatSyncTime(status.last_activity_success);
      const tradeSync = formatSyncTime(status.last_trade_success);
      const parts = [];
      if (finalSync) parts.push(`final P&L ${finalSync}`);
      if (tradeSync) {
        const count = status.confirmation_rows == null ? '' : ` · ${status.confirmation_rows} executions`;
        parts.push(`confirmations ${tradeSync}${count}`);
      }
      if (status.running) parts.unshift('syncing now');
      if (status.configuration_warning) parts.push(status.configuration_warning);
      const dotClass = status.error ? 'status-dot error-dot' : 'status-dot';
      const copy = status.error
        ? `IBKR: ${status.error}`
        : `IBKR ${parts.length ? parts.join(' · ') : 'ready'}`;
      statusElement.innerHTML = `<span class="${dotClass}"></span>${escapeHtml(copy)}`;
      state.lastActivitySync = status.last_activity_success || state.lastActivitySync;
    }

    async function syncIbkr() {
      ibkrSyncButton.disabled = true;
      ibkrSyncButton.textContent = 'Syncing…';
      errorBox.classList.add('hidden');
      try {
        const response = await fetch('/api/ibkr/sync', { method: 'POST', cache: 'no-store' });
        const result = await response.json();
        renderIbkrStatus(result.status || result);
        if (!response.ok) throw new Error(result.error || 'IBKR synchronization failed.');
        await loadData();
      } catch (error) {
        errorBox.textContent = error.message;
        errorBox.classList.remove('hidden');
      } finally {
        ibkrSyncButton.textContent = 'Sync IBKR';
        if (state.payload?.ibkr) renderIbkrStatus(state.payload.ibkr);
      }
    }

    async function pollIbkrStatus() {
      if (window.__TRADE_PAYLOAD__) return;
      try {
        const response = await fetch(`/api/ibkr/status?refresh=${Date.now()}`, { cache: 'no-store' });
        const result = await response.json();
        if (!response.ok) return;
        const previousActivitySync = state.lastActivitySync;
        renderIbkrStatus(result);
        if (previousActivitySync && result.last_activity_success && result.last_activity_success !== previousActivitySync) {
          await loadData();
        }
      } catch (_) {
        // A temporary status-poll failure should not interrupt the dashboard.
      }
    }

    async function loadData({ preserveMonth = true } = {}) {
      const reloadButton = document.getElementById('reload-button');
      reloadButton.disabled = true;
      reloadButton.textContent = 'Loading…';
      errorBox.classList.add('hidden');
      try {
        let result;
        if (window.__TRADE_PAYLOAD__) {
          result = window.__TRADE_PAYLOAD__;
        } else {
          const response = await fetch(`/api/data?refresh=${Date.now()}`, { cache: 'no-store' });
          result = await response.json();
          if (!response.ok) throw new Error(result.error || 'Unable to load the CSV.');
        }
        const previousMonth = preserveMonth ? state.selectedMonth : null;
        const previousScope = preserveMonth ? state.analysisScope : 'all';
        state.payload = result;
        state.selectedMonth = result.months.includes(previousMonth)
          ? previousMonth
          : result.months[result.months.length - 1];
        state.analysisScope = previousScope === 'all' || result.months.includes(previousScope)
          ? previousScope
          : 'all';
        const loaded = new Date(result.metadata.loaded_at).toLocaleString();
        document.getElementById('file-status').innerHTML =
          `<span class="status-dot"></span>${escapeHtml(result.metadata.file_name)} · refreshed ${escapeHtml(loaded)}`;
        document.getElementById('data-note').textContent =
          `P&L: ${result.metadata.pnl_column} · Time: ${result.metadata.time_column || 'not available'} · ${result.metadata.count_definition}`;
        renderIbkrStatus(result.ibkr);
        renderAll();
      } catch (error) {
        errorBox.textContent = error.message;
        errorBox.classList.remove('hidden');
      } finally {
        reloadButton.disabled = false;
        reloadButton.textContent = 'Reload CSV';
      }
    }

    monthSelect.addEventListener('change', () => {
      state.selectedMonth = monthSelect.value;
      renderAll();
    });
    analysisPeriodSelect.addEventListener('change', () => {
      state.analysisScope = analysisPeriodSelect.value;
      renderAnalysis();
    });
    document.getElementById('symbol-odds-form').addEventListener('submit', event => {
      event.preventDefault();
      renderSymbolRank(document.getElementById('symbol-odds-input').value);
    });
    document.getElementById('calendar-tab').addEventListener('click', () => setView('calendar'));
    document.getElementById('analysis-tab').addEventListener('click', () => setView('analysis'));
    document.getElementById('refresh-floats').addEventListener('click', () => {
      loadYahooMetadata(currentAnalysis().symbols.map(row => row.symbol), true);
    });
    document.getElementById('previous-month').addEventListener('click', () => {
      const index = state.payload.months.indexOf(state.selectedMonth);
      if (index > 0) { state.selectedMonth = state.payload.months[index - 1]; renderAll(); }
    });
    document.getElementById('next-month').addEventListener('click', () => {
      const index = state.payload.months.indexOf(state.selectedMonth);
      if (index < state.payload.months.length - 1) { state.selectedMonth = state.payload.months[index + 1]; renderAll(); }
    });
    document.getElementById('reload-button').addEventListener('click', () => loadData());
    ibkrSyncButton.addEventListener('click', syncIbkr);
    document.getElementById('modal-close').addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => {
      if (event.target === dialog) dialog.close();
    });
    addEventListener('popstate', () => {
      setView(location.pathname === '/analysis' ? 'analysis' : 'calendar', false);
    });

    loadData({ preserveMonth: false });
    if (!window.__TRADE_PAYLOAD__) setInterval(pollIbkrStatus, 60000);
  </script>
</body>
</html>
'''


def make_handler(
    csv_path: Path, ibkr_sync: FlexSyncManager
) -> type[BaseHTTPRequestHandler]:
    metadata_store = YahooMetadataStore(csv_path.parent / FLOAT_CACHE_NAME)

    class TradeCalendarHandler(BaseHTTPRequestHandler):
        server_version = "TradeCalendar/1.0"

        def log_message(self, format_string: str, *args: Any) -> None:
            # Keep the terminal readable while still reporting errors.
            if args and str(args[1]).startswith(("4", "5")):
                super().log_message(format_string, *args)

        def send_bytes(
            self, body: bytes, content_type: str, status: HTTPStatus = HTTPStatus.OK
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            if path in ("/", "/analysis"):
                self.send_bytes(HTML_PAGE.encode("utf-8"), "text/html; charset=utf-8")
                return
            if path == "/api/data":
                try:
                    ibkr_sync.ensure_activity_file()
                    payload = load_trade_payload(csv_path)
                    payload["ibkr"] = ibkr_sync.status()
                    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
                    self.send_bytes(body, "application/json; charset=utf-8")
                except FlexSyncError as exc:
                    body = json.dumps(
                        {"error": str(exc), "status": ibkr_sync.status()},
                        separators=(",", ":"),
                    ).encode("utf-8")
                    self.send_bytes(
                        body,
                        "application/json; charset=utf-8",
                        HTTPStatus.BAD_GATEWAY,
                    )
                except (OSError, TradeDataError) as exc:
                    body = json.dumps({"error": str(exc)}).encode("utf-8")
                    self.send_bytes(
                        body,
                        "application/json; charset=utf-8",
                        HTTPStatus.UNPROCESSABLE_ENTITY,
                    )
                return
            if path == "/api/ibkr/status":
                body = json.dumps(
                    ibkr_sync.status(), separators=(",", ":")
                ).encode("utf-8")
                self.send_bytes(body, "application/json; charset=utf-8")
                return
            if path in ("/api/symbol-metadata", "/api/floats"):
                query = parse_qs(parsed_url.query)
                symbols = [
                    symbol
                    for value in query.get("symbols", [])
                    for symbol in value.split(",")
                ]
                force_refresh = query.get("refresh", ["0"])[0] == "1"
                if not symbols:
                    body = json.dumps(
                        {"error": "No symbols were requested."}
                    ).encode("utf-8")
                    self.send_bytes(
                        body,
                        "application/json; charset=utf-8",
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                payload = metadata_store.get_many(
                    symbols, force_refresh=force_refresh
                )
                body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
                self.send_bytes(body, "application/json; charset=utf-8")
                return
            if path == "/health":
                self.send_bytes(b'{"status":"ok"}', "application/json")
                return
            if path == "/favicon.ico":
                self.send_bytes(b"", "image/x-icon", HTTPStatus.NO_CONTENT)
                return
            self.send_bytes(b"Not found", "text/plain", HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
            path = urlparse(self.path).path
            if path != "/api/ibkr/sync":
                self.send_bytes(b"Not found", "text/plain", HTTPStatus.NOT_FOUND)
                return
            try:
                # The dashboard reads the Activity report. Fetching the separate
                # confirmation report here only delays the visible refresh.
                status = ibkr_sync.refresh_activity()
                body = json.dumps({"status": status}, separators=(",", ":")).encode(
                    "utf-8"
                )
                self.send_bytes(body, "application/json; charset=utf-8")
            except FlexSyncError as exc:
                body = json.dumps(
                    {"error": str(exc), "status": ibkr_sync.status()},
                    separators=(",", ":"),
                ).encode("utf-8")
                self.send_bytes(
                    body,
                    "application/json; charset=utf-8",
                    HTTPStatus.BAD_GATEWAY,
                )

    return TradeCalendarHandler


def print_check(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    metadata = payload["metadata"]
    analysis = payload["analysis"]["all"]
    overview = analysis["overview"]
    print(f"File: {metadata['file_path']}")
    print(f"Months: {', '.join(payload['months'])}")
    print(f"Trade rows: {summary['trade_count']}")
    print(f"Trading days: {summary['trading_days']}")
    print(f"Unique symbols: {summary['unique_symbols']}")
    print(f"Total realized P&L: {summary['pnl']:.2f}")
    print(
        f"Best day: {summary['best_day']['date']} "
        f"({summary['best_day']['pnl']:.2f})"
    )
    print(
        f"Worst day: {summary['worst_day']['date']} "
        f"({summary['worst_day']['pnl']:.2f})"
    )
    print(f"Closed executions analyzed: {overview['closed_execution_count']}")
    if overview["win_rate"] is not None:
        print(f"Closed-execution win rate: {overview['win_rate']:.2%}")
    if overview["average_profit_per_share_good_trades"] is not None:
        print(
            "Average profit/share on good trades: "
            f"{overview['average_profit_per_share_good_trades']:.4f}"
        )
    if analysis["best_hour"]:
        print(
            "Best average hour: "
            f"{analysis['best_hour']['label']} "
            f"({analysis['best_hour']['average_pnl']:.2f} average P&L)"
        )
    elif metadata["time_column"] is None:
        print("Best average hour: unavailable (no execution-time column)")


def export_snapshot(payload: dict[str, Any], output_path: Path) -> None:
    embedded_json = json.dumps(payload, separators=(",", ":")).replace(
        "</", "<\\/"
    )
    snapshot = HTML_PAGE.replace(
        "window.__TRADE_PAYLOAD__ = null;",
        f"window.__TRADE_PAYLOAD__ = {embedded_json};",
        1,
    )
    output_path.write_text(snapshot, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Open WTC - World Trade Center, an interactive trade-performance dashboard."
    )
    parser.add_argument(
        "--file",
        help=(
            "CSV filename or path. By default, the script reads "
            f"{DEFAULT_CSV_NAME!r} from its own folder."
        ),
    )
    parser.add_argument("--host", default="127.0.0.1", help=argparse.SUPPRESS)
    parser.add_argument("--port", type=int, default=8765, help="Local web port.")
    parser.add_argument(
        "--no-browser", action="store_true", help="Do not open the browser automatically."
    )
    parser.add_argument(
        "--check", action="store_true", help="Validate the CSV and print its totals."
    )
    parser.add_argument(
        "--export-html",
        nargs="?",
        const="trade_calendar_snapshot.html",
        metavar="FILE",
        help="Write a self-contained interactive HTML snapshot instead of starting the server.",
    )
    args = parser.parse_args()

    script_directory = Path(__file__).resolve().parent
    try:
        csv_path = find_csv(script_directory, args.file)
        ibkr_sync = FlexSyncManager(csv_path, load_trade_payload)
        if not csv_path.is_file():
            print(
                f"Local trade history not found. Downloading {csv_path.name} "
                "from the IBKR Activity Flex query..."
            )
            ibkr_sync.ensure_activity_file()
        payload = load_trade_payload(csv_path)
    except (OSError, TradeDataError, FlexSyncError) as exc:
        parser.error(str(exc))

    if args.check:
        print_check(payload)
        return 0

    if args.export_html:
        snapshot_path = Path(args.export_html).expanduser()
        if not snapshot_path.is_absolute():
            snapshot_path = script_directory / snapshot_path
        export_snapshot(payload, snapshot_path)
        print(f"Interactive snapshot written to: {snapshot_path}")
        if not args.no_browser:
            webbrowser.open(snapshot_path.resolve().as_uri())
        return 0

    handler = make_handler(csv_path, ibkr_sync)
    try:
        server = ThreadingHTTPServer((args.host, args.port), handler)
    except OSError as exc:
        parser.error(f"Could not start the local dashboard on port {args.port}: {exc}")
    actual_port = server.server_address[1]
    url = f"http://{args.host}:{actual_port}/"
    print(f"WTC - World Trade Center is running at {url}")
    print(f"Reading: {csv_path}")
    if ibkr_sync.config.configured:
        configured_reports = []
        if ibkr_sync.config.activity_configured:
            configured_reports.append("final Activity report")
        if ibkr_sync.config.trade_configured:
            configured_reports.append("intraday Trade Confirmations")
        print(f"IBKR automatic sync: {', '.join(configured_reports)}")
    else:
        print("IBKR automatic sync: not configured (see README.md)")
    print("Press Ctrl+C to stop.")

    if not args.no_browser:
        threading.Timer(0.45, lambda: webbrowser.open(url)).start()

    ibkr_sync.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nWTC - World Trade Center stopped.")
    finally:
        ibkr_sync.stop()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
