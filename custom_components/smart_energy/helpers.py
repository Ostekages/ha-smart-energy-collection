"""Pure calculation helpers for Smart Energy.

These functions contain no Home Assistant imports so they can be unit tested
in isolation. Everything the engine "knows" lives here.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from statistics import mean
from typing import Any


def _parse_dt(value: Any) -> datetime:
    """Parse an ISO 8601 string (or passthrough datetime)."""
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def parse_prices(raw: Any) -> list[dict]:
    """Normalise a raw ``prices`` attribute into sorted price intervals.

    Each raw item looks like ``{"price": 0.64, "start": "...", "end": "..."}``.
    Invalid items are skipped rather than raising.
    """
    result: list[dict] = []
    for item in raw or []:
        try:
            price = float(item["price"])
            start = _parse_dt(item["start"])
            end = _parse_dt(item["end"])
        except (KeyError, TypeError, ValueError):
            continue
        result.append({"price": price, "start": start, "end": end})
    result.sort(key=lambda x: x["start"])
    return result


def merge_prices(*price_lists: list[dict]) -> list[dict]:
    """Merge several interval lists, de-duplicating identical start times."""
    seen: dict[datetime, dict] = {}
    for prices in price_lists:
        for item in prices:
            seen[item["start"]] = item
    return sorted(seen.values(), key=lambda x: x["start"])


def aggregate_hourly(prices: list[dict]) -> list[dict]:
    """Aggregate (typically 15-minute) intervals into hourly averages."""
    buckets: dict[datetime, list[float]] = {}
    for item in prices:
        hour_start = item["start"].replace(minute=0, second=0, microsecond=0)
        buckets.setdefault(hour_start, []).append(item["price"])

    return [
        {
            "start": hour_start,
            "end": hour_start + timedelta(hours=1),
            "price": round(mean(values), 4),
        }
        for hour_start, values in sorted(buckets.items())
    ]


def filter_future(hourly: list[dict], now: datetime) -> list[dict]:
    """Keep only the current hour and hours that have not yet ended."""
    return [hour for hour in hourly if hour["end"] > now]


def _contiguous(window: list[dict]) -> bool:
    """True when the hours in ``window`` are back to back with no gaps."""
    return all(a["end"] == b["start"] for a, b in zip(window, window[1:]))


def find_best_window(hourly: list[dict], duration: int) -> dict | None:
    """Find the cheapest contiguous ``duration``-hour window.

    Returns ``{"start", "end", "average_price"}`` or ``None`` when there are
    not enough contiguous hours available.
    """
    if duration <= 0 or len(hourly) < duration:
        return None

    best: dict | None = None
    for i in range(len(hourly) - duration + 1):
        window = hourly[i : i + duration]
        if not _contiguous(window):
            continue
        avg = round(mean(hour["price"] for hour in window), 4)
        if best is None or avg < best["average_price"]:
            best = {
                "start": window[0]["start"],
                "end": window[-1]["end"],
                "average_price": avg,
            }
    return best


def current_price(prices: list[dict], now: datetime) -> float | None:
    """Return the price for the interval that contains ``now``."""
    for item in prices:
        if item["start"] <= now < item["end"]:
            return item["price"]
    return None


def build_levels(hourly: list[dict], levels: int = 5) -> list[dict]:
    """Turn hourly prices into a heatmap the dashboard can render directly.

    ``level`` is 0 (cheapest) .. ``levels - 1`` (most expensive), scaled
    against the min/max of the supplied hours.
    """
    if not hourly:
        return []

    values = [hour["price"] for hour in hourly]
    low, high = min(values), max(values)
    span = high - low

    result: list[dict] = []
    for hour in hourly:
        if span == 0:
            level = 0
        else:
            level = int((hour["price"] - low) / span * (levels - 1) + 0.5)
        result.append(
            {
                "start": hour["start"].isoformat(),
                "hour": hour["start"].strftime("%H"),
                "time": hour["start"].strftime("%H:%M"),
                "price": hour["price"],
                "level": level,
            }
        )
    return result


def window_label(window: dict | None) -> str | None:
    """Human friendly ``13-16`` style label for a window."""
    if not window:
        return None
    return f"{window['start'].strftime('%H')}-{window['end'].strftime('%H')}"
