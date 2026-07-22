"""Quick self-check of the Smart Energy engine against real Strømligning data.

Run with:  python verify_engine.py
No Home Assistant required — it only exercises helpers.py.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "smart_energy"))

from helpers import (  # noqa: E402
    aggregate_hourly,
    build_levels,
    current_price,
    filter_future,
    find_best_window,
    parse_prices,
    window_label,
)

# A handful of 15-min intervals taken from the real attached data set.
RAW = [
    {"price": 0.062608, "start": "2026-07-22T13:30:00+02:00", "end": "2026-07-22T13:45:00+02:00"},
    {"price": 0.061954, "start": "2026-07-22T13:45:00+02:00", "end": "2026-07-22T14:00:00+02:00"},
    {"price": 0.059618, "start": "2026-07-22T14:00:00+02:00", "end": "2026-07-22T14:15:00+02:00"},
    {"price": 0.060179, "start": "2026-07-22T14:15:00+02:00", "end": "2026-07-22T14:30:00+02:00"},
    {"price": 0.065785, "start": "2026-07-22T14:30:00+02:00", "end": "2026-07-22T14:45:00+02:00"},
    {"price": 0.068028, "start": "2026-07-22T14:45:00+02:00", "end": "2026-07-22T15:00:00+02:00"},
    {"price": 0.06457, "start": "2026-07-22T15:00:00+02:00", "end": "2026-07-22T15:15:00+02:00"},
    {"price": 0.081671, "start": "2026-07-22T15:15:00+02:00", "end": "2026-07-22T15:30:00+02:00"},
    {"price": 0.061861, "start": "2026-07-22T15:30:00+02:00", "end": "2026-07-22T15:45:00+02:00"},
    {"price": 0.062608, "start": "2026-07-22T15:45:00+02:00", "end": "2026-07-22T16:00:00+02:00"},
    {"price": 1.20, "start": "2026-07-22T16:00:00+02:00", "end": "2026-07-22T16:15:00+02:00"},
    {"price": 1.25, "start": "2026-07-22T16:15:00+02:00", "end": "2026-07-22T16:30:00+02:00"},
    {"price": 1.30, "start": "2026-07-22T16:30:00+02:00", "end": "2026-07-22T16:45:00+02:00"},
    {"price": 1.35, "start": "2026-07-22T16:45:00+02:00", "end": "2026-07-22T17:00:00+02:00"},
]


def main() -> None:
    prices = parse_prices(RAW)
    now = datetime.fromisoformat("2026-07-22T13:40:00+02:00")

    hourly = aggregate_hourly(prices)
    print("Hourly averages:")
    for h in hourly:
        print(f"  {h['start']:%H:%M}  {h['price']:.4f}")

    future = filter_future(hourly, now)
    print(f"\nCurrent price at {now:%H:%M}: {current_price(prices, now):.4f}")

    for duration in (2, 3):
        best = find_best_window(future, duration)
        print(f"Best {duration}h window from now: {window_label(best)}  "
              f"avg={best['average_price'] if best else None}")

    print("\nHeatmap levels:")
    for entry in build_levels(future, 5):
        bar = "█" * (entry["level"] + 1)
        print(f"  {entry['time']}  {entry['price']:.4f}  L{entry['level']} {bar}")

    # Basic sanity assertions
    assert current_price(prices, now) == 0.062608
    best3 = find_best_window(future, 3)
    assert window_label(best3) == "13-16", window_label(best3)
    assert build_levels(future, 5)[0]["level"] == 0
    print("\nAll assertions passed ✅")


if __name__ == "__main__":
    main()
