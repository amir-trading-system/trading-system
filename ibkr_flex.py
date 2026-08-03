"""Safe background synchronization for Interactive Brokers Flex reports."""

from __future__ import annotations

import csv
import io
import json
import os
import shutil
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree


FLEX_BASE_URL = (
    "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"
)
FLEX_VERSION = "3"
USER_AGENT = "WTC-Trade-Center/1.0"
RETRYABLE_REPORT_CODES = {"1001", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1019", "1021"}
MIN_REQUEST_GAP_SECONDS = 1.10
# IBKR permits ten Flex requests per minute. Stay below the ceiling so a retry
# or another process using the token does not immediately trip error 1018.
MAX_REQUESTS_PER_MINUTE = 8


class FlexSyncError(RuntimeError):
    """Raised when IBKR configuration or report retrieval fails."""


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _clean_secret(value: str | None) -> str | None:
    cleaned = str(value or "").strip().strip('"').strip("'")
    return cleaned or None


def read_local_environment(path: Path) -> dict[str, str]:
    """Read a tiny KEY=VALUE file without adding a dotenv dependency."""
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return values
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key.replace("_", "").isalnum():
            values[key] = value.strip().strip('"').strip("'")
    return values


def _positive_number(value: str | None, default: float, minimum: float) -> float:
    try:
        parsed = float(value or "")
    except (TypeError, ValueError):
        return default
    return max(minimum, parsed)


@dataclass(frozen=True)
class FlexConfig:
    token: str | None
    activity_query_id: str | None
    trade_query_id: str | None
    trade_sync_minutes: float = 15.0
    activity_sync_hour: int = 3
    request_timeout_seconds: float = 30.0

    @classmethod
    def load(cls, directory: Path) -> "FlexConfig":
        local = read_local_environment(directory / "ibkr_flex.env")

        def setting(name: str) -> str | None:
            return os.environ.get(name) or local.get(name)

        try:
            activity_hour = int(setting("IBKR_ACTIVITY_SYNC_HOUR") or "3")
        except ValueError:
            activity_hour = 3
        return cls(
            token=_clean_secret(setting("IBKR_FLEX_TOKEN")),
            activity_query_id=_clean_secret(setting("IBKR_ACTIVITY_QUERY_ID")),
            trade_query_id=_clean_secret(setting("IBKR_TRADE_QUERY_ID")),
            trade_sync_minutes=_positive_number(
                setting("IBKR_TRADE_SYNC_MINUTES"), 15.0, 5.0
            ),
            activity_sync_hour=min(23, max(0, activity_hour)),
            request_timeout_seconds=_positive_number(
                setting("IBKR_REQUEST_TIMEOUT_SECONDS"), 30.0, 5.0
            ),
        )

    @property
    def configured(self) -> bool:
        return bool(self.token and (self.activity_query_id or self.trade_query_id))

    @property
    def activity_configured(self) -> bool:
        return bool(self.token and self.activity_query_id)

    @property
    def trade_configured(self) -> bool:
        return bool(self.token and self.trade_query_id)

    def missing(self) -> list[str]:
        missing: list[str] = []
        if not self.token:
            missing.append("IBKR_FLEX_TOKEN")
        if not self.activity_query_id and not self.trade_query_id:
            missing.append("IBKR_ACTIVITY_QUERY_ID or IBKR_TRADE_QUERY_ID")
        return missing


def parse_generation_response(payload: bytes) -> str:
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise FlexSyncError("IBKR returned an unreadable report-generation response.") from exc
    values = {_local_name(child.tag): (child.text or "").strip() for child in root}
    if values.get("Status", "").lower() != "success":
        message = values.get("ErrorMessage") or "IBKR could not generate the Flex report."
        code = values.get("ErrorCode")
        raise FlexSyncError(f"{message}{f' (IBKR {code})' if code else ''}")
    reference = values.get("ReferenceCode")
    if not reference:
        raise FlexSyncError("IBKR generated the report without returning a reference code.")
    return reference


def report_error(payload: bytes) -> tuple[str | None, str | None]:
    stripped = payload.lstrip()
    if not stripped.startswith(b"<"):
        return None, None
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError:
        return None, None
    if _local_name(root.tag) != "FlexStatementResponse":
        return None, None
    values = {_local_name(child.tag): (child.text or "").strip() for child in root}
    if values.get("Status", "").lower() == "success":
        return None, None
    return values.get("ErrorCode"), values.get("ErrorMessage") or "IBKR report retrieval failed."


def xml_trade_rows(payload: bytes) -> list[dict[str, str]]:
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise FlexSyncError("IBKR returned an unreadable XML report.") from exc
    rows: list[dict[str, str]] = []
    for element in root.iter():
        if _local_name(element.tag).lower() not in {"trade", "tradeconfirm"}:
            continue
        if element.attrib and any(key.lower() == "symbol" for key in element.attrib):
            rows.append({str(key): str(value) for key, value in element.attrib.items()})
    return rows


def csv_from_xml_activity(payload: bytes) -> bytes:
    rows = xml_trade_rows(payload)
    if not rows:
        raise FlexSyncError("The Activity Flex report did not contain any trade rows.")
    preferred = [
        "ClientAccountID", "Symbol", "TradeDate", "DateTime", "Quantity",
        "TradePrice", "Buy/Sell", "FifoPnlRealized", "MtmPnl", "Proceeds",
        "CostBasis", "IBCommission", "CurrencyPrimary", "AssetClass",
        "Description", "ExecID", "TradeID",
    ]
    available = {key for row in rows for key in row}
    normalized = {key.lower(): key for key in available}
    fieldnames: list[str] = []
    for desired in preferred:
        actual = normalized.get(desired.lower())
        if actual and actual not in fieldnames:
            fieldnames.append(actual)
    fieldnames.extend(sorted(available.difference(fieldnames), key=str.lower))
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def activity_report_bytes(payload: bytes) -> bytes:
    code, message = report_error(payload)
    if message:
        raise FlexSyncError(f"{message}{f' (IBKR {code})' if code else ''}")
    if payload.lstrip().startswith(b"<"):
        return csv_from_xml_activity(payload)
    return payload


def count_confirmation_rows(payload: bytes) -> int:
    code, message = report_error(payload)
    if message:
        raise FlexSyncError(f"{message}{f' (IBKR {code})' if code else ''}")
    if payload.lstrip().startswith(b"<"):
        return len(xml_trade_rows(payload))
    text = payload.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    for index, line in enumerate(lines[:30]):
        for delimiter in (",", "\t", "|"):
            headers = [cell.strip().lower() for cell in next(csv.reader([line], delimiter=delimiter))]
            if "symbol" in headers and any(name in headers for name in ("execid", "tradeid", "date/time", "tradedate")):
                reader = csv.reader(lines[index + 1 :], delimiter=delimiter)
                return sum(1 for row in reader if row and any(cell.strip() for cell in row))
    raise FlexSyncError("The Trade Confirmation report did not contain a recognizable header row.")


class FlexSyncManager:
    """Download Flex reports without exposing credentials to the browser."""

    def __init__(
        self,
        csv_path: Path,
        validator: Callable[[Path], Any],
        config: FlexConfig | None = None,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.csv_path = csv_path
        self.validator = validator
        self.config = config or FlexConfig.load(csv_path.parent)
        self.opener = opener
        self.trade_report_path = csv_path.parent / "ibkr_trade_confirmations_latest.dat"
        self.backup_path = csv_path.parent / "Trades_before_last_IBKR_sync.csv"
        self._sync_lock = threading.Lock()
        self._state_lock = threading.RLock()
        self._request_pacing_lock = threading.Lock()
        self._request_times: deque[float] = deque()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_trade_attempt: datetime | None = None
        self._last_activity_attempt: datetime | None = None
        self._activity_success_date: str | None = None
        self._state: dict[str, Any] = {
            "running": False,
            "last_attempt": None,
            "last_success": None,
            "last_activity_success": None,
            "last_trade_success": None,
            "confirmation_rows": None,
            "error": None,
        }

    def status(self) -> dict[str, Any]:
        with self._state_lock:
            state = dict(self._state)
        state.update(
            {
                "configured": self.config.configured,
                "activity_configured": self.config.activity_configured,
                "trade_configured": self.config.trade_configured,
                "trade_sync_minutes": self.config.trade_sync_minutes,
                "missing": self.config.missing(),
            }
        )
        return state

    @staticmethod
    def _iso_now() -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def _set_state(self, **updates: Any) -> None:
        with self._state_lock:
            self._state.update(updates)

    def start(self) -> None:
        if not self.config.configured or self._thread:
            return
        self._thread = threading.Thread(
            target=self._background_loop, name="ibkr-flex-sync", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def _background_loop(self) -> None:
        while not self._stop.is_set():
            now = datetime.now().astimezone()
            sync_trade = self.config.trade_configured and (
                self._last_trade_attempt is None
                or now - self._last_trade_attempt
                >= timedelta(minutes=self.config.trade_sync_minutes)
            )
            sync_activity = self.config.activity_configured and (
                now.hour >= self.config.activity_sync_hour
                and self._activity_success_date != now.date().isoformat()
                and (
                    self._last_activity_attempt is None
                    or now - self._last_activity_attempt >= timedelta(hours=1)
                )
            )
            if sync_trade or sync_activity:
                try:
                    self.sync(
                        include_activity=bool(sync_activity),
                        include_trade=bool(sync_trade),
                        wait_for_lock=False,
                    )
                except FlexSyncError:
                    # The status object retains the error and the loop retries later.
                    pass
            self._stop.wait(30)

    def _wait_for_request_slot(self) -> None:
        with self._request_pacing_lock:
            while True:
                now = time.monotonic()
                while self._request_times and now - self._request_times[0] >= 60.0:
                    self._request_times.popleft()
                delay = 0.0
                if self._request_times:
                    delay = max(
                        delay,
                        MIN_REQUEST_GAP_SECONDS - (now - self._request_times[-1]),
                    )
                if len(self._request_times) >= MAX_REQUESTS_PER_MINUTE:
                    delay = max(delay, 60.25 - (now - self._request_times[0]))
                if delay <= 0:
                    self._request_times.append(now)
                    return
                if self._stop.wait(delay):
                    raise FlexSyncError("IBKR synchronization was stopped.")

    def _request(self, endpoint: str, params: dict[str, str]) -> bytes:
        self._wait_for_request_slot()
        url = f"{FLEX_BASE_URL}/{endpoint}?{urlencode(params)}"
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
        try:
            with self.opener(request, timeout=self.config.request_timeout_seconds) as response:
                return response.read()
        except HTTPError as exc:
            raise FlexSyncError(f"IBKR returned HTTP {exc.code} while retrieving the report.") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise FlexSyncError("IBKR could not be reached. Check the internet connection and try again.") from exc

    def _download_report(self, query_id: str) -> bytes:
        token = self.config.token
        if not token:
            raise FlexSyncError("IBKR_FLEX_TOKEN is not configured.")
        generation = self._request(
            "SendRequest", {"t": token, "q": query_id, "v": FLEX_VERSION}
        )
        reference = parse_generation_response(generation)
        # IBKR generates the report asynchronously and its own example waits
        # before the first GetStatement call. Two patient retrieval attempts use
        # fewer requests than frequent short polling and stay below error 1018.
        waits = (20, 20)
        last_message = "IBKR is still preparing the Flex report."
        for wait_seconds in waits:
            if wait_seconds and self._stop.wait(wait_seconds):
                raise FlexSyncError("IBKR synchronization was stopped.")
            payload = self._request(
                "GetStatement", {"t": token, "q": reference, "v": FLEX_VERSION}
            )
            code, message = report_error(payload)
            if not message:
                return payload
            last_message = f"{message}{f' (IBKR {code})' if code else ''}"
            if code not in RETRYABLE_REPORT_CODES:
                raise FlexSyncError(last_message)
        raise FlexSyncError(last_message)

    @staticmethod
    def _atomic_write(path: Path, payload: bytes) -> None:
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_bytes(payload)
        temporary.replace(path)

    def _sync_activity(self) -> None:
        query_id = self.config.activity_query_id
        if not query_id:
            return
        self._last_activity_attempt = datetime.now().astimezone()
        payload = activity_report_bytes(self._download_report(query_id))
        candidate = self.csv_path.with_name(f".{self.csv_path.name}.ibkr-candidate")
        try:
            candidate.write_bytes(payload)
            try:
                self.validator(candidate)
            except Exception as exc:
                raise FlexSyncError(
                    "The downloaded Activity report is missing fields required by WTC. "
                    "Confirm that its Trades section includes Symbol, TradeDate, Quantity, "
                    "TradePrice, Buy/Sell, FifoPnlRealized, IBCommission, and CurrencyPrimary."
                ) from exc
            if self.csv_path.exists():
                shutil.copy2(self.csv_path, self.backup_path)
            candidate.replace(self.csv_path)
        except OSError as exc:
            raise FlexSyncError("WTC could not save the downloaded Activity report.") from exc
        finally:
            try:
                candidate.unlink()
            except FileNotFoundError:
                pass
        completed = self._iso_now()
        self._activity_success_date = datetime.now().astimezone().date().isoformat()
        self._set_state(last_activity_success=completed)

    def _sync_trade_confirmations(self) -> None:
        query_id = self.config.trade_query_id
        if not query_id:
            return
        self._last_trade_attempt = datetime.now().astimezone()
        payload = self._download_report(query_id)
        count = count_confirmation_rows(payload)
        try:
            self._atomic_write(self.trade_report_path, payload)
        except OSError as exc:
            raise FlexSyncError("WTC could not save the Trade Confirmation report.") from exc
        self._set_state(last_trade_success=self._iso_now(), confirmation_rows=count)

    def sync(
        self,
        *,
        include_activity: bool = True,
        include_trade: bool = True,
        wait_for_lock: bool = True,
    ) -> dict[str, Any]:
        if not self.config.configured:
            missing = ", ".join(self.config.missing())
            raise FlexSyncError(f"IBKR synchronization is not configured. Missing: {missing}.")
        acquired = self._sync_lock.acquire(blocking=wait_for_lock)
        if not acquired:
            return self.status()
        attempted = self._iso_now()
        self._set_state(running=True, last_attempt=attempted, error=None)
        errors: list[str] = []
        successes = 0
        try:
            if include_activity and self.config.activity_configured:
                try:
                    self._sync_activity()
                    successes += 1
                except FlexSyncError as exc:
                    errors.append(f"Activity report: {exc}")
            if include_trade and self.config.trade_configured:
                try:
                    self._sync_trade_confirmations()
                    successes += 1
                except FlexSyncError as exc:
                    errors.append(f"Trade confirmations: {exc}")
            if successes:
                self._set_state(last_success=self._iso_now())
            self._set_state(error=" ".join(errors) or None)
            if errors and not successes:
                raise FlexSyncError(" ".join(errors))
            return self.status()
        finally:
            self._set_state(running=False)
            self._sync_lock.release()

    def write_status_file(self) -> None:
        """Optional diagnostic snapshot that never includes the Flex token."""
        payload = json.dumps(self.status(), indent=2, sort_keys=True).encode("utf-8")
        self._atomic_write(self.csv_path.parent / "ibkr_sync_status.json", payload)
