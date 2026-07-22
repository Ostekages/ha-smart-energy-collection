# Smart Energy ⚡

A small Home Assistant **engine** (custom integration) that turns your
[Strømligning](https://github.com/MTrab/stromligning) spot-price sensors into
intelligent, dashboard-ready data.

> Philosophy: build the *engine* first, the dashboard is the easy part.
> Integration = data + calculations. Dashboard = presentation.

## What it does

Reads your two Strømligning sensors:

- `sensor.stromligning_spotprice_vat` (today, 15-minute `prices` array)
- `binary_sensor.stromligning_tomorrow_spotprice_vat` (tomorrow, `prices` array)

…and computes:

- ✅ 15-minute prices aggregated to **hourly averages**
- ✅ Cheapest **contiguous window** for any duration (2h / 3h / 4h … configurable)
- ✅ **"From now" logic** — past hours are ignored, so at 17:00 it won't suggest 13:00
- ✅ A **heatmap** of the next N hours (level 0 = cheapest … 4 = most expensive)
- ✅ Best window **today vs tomorrow** + a simple **trend**

## Entities

Few sensors, rich attributes (by design — no `sensor.smart_energy_1..50`).

| Entity | State | Key attributes |
| --- | --- | --- |
| `sensor.smart_energy` | current price (kr/kWh) | `current`, `next_hours` (heatmap), `best_2h`, `best_3h`, `best_4h`, `best_today`, `best_tomorrow`, `trend` |
| `sensor.smart_energy_best_today` | `13-16` | `start`, `end`, `average_price` |
| `sensor.smart_energy_trend` | `better_today` / `better_tomorrow` / `equal` | `best_today`, `best_tomorrow` |

Each window attribute looks like:

```yaml
best_3h:
  start: "2026-07-22T13:00:00+02:00"
  end:   "2026-07-22T16:00:00+02:00"
  label: "13-16"
  average_price: 0.0645
```

And `next_hours` is a ready-to-render heatmap:

```yaml
next_hours:
  - { start: "...T13:00...", hour: "13", time: "13:00", price: 0.0623, level: 0 }
  - { start: "...T16:00...", hour: "16", time: "16:00", price: 1.2750, level: 4 }
```

## Installation

### Option A — HACS (recommended)
1. Push this repo to GitHub.
2. HACS → ⋮ → *Custom repositories* → add the repo URL, category **Integration**.
3. Install **Smart Energy**, restart Home Assistant.

### Option B — Manual
Copy `custom_components/smart_energy/` into your HA `config/custom_components/`
and restart.

Then: **Settings → Devices & Services → Add Integration → Smart Energy**, and
confirm the two Strømligning entities (defaults are pre-filled). All durations,
heatmap length and the prices-attribute name are configurable, and can be
changed later via the integration's *Configure* button.

## Dashboard (next step)

The engine is complete — the dashboard reads everything from these entities.
Recommended free HACS cards: **Mushroom**, **card-mod**, and **ApexCharts Card**.
Because the heatmap and windows are pre-computed, the card only has to *show*
them, e.g. a template/Mushroom card iterating `next_hours` with a colour per
`level`, and a chip showing `sensor.smart_energy_best_today`.

## Verify the maths

```bash
python3 verify_engine.py
```

Runs the pure calculation helpers against sample Strømligning data (no HA needed).
