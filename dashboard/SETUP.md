# Smart Energy — Dashboard setup

## 1. What you must install separately (one thing)

**Mushroom** — the only extra dependency for this dashboard.
HACS → *Frontend* → search **Mushroom** → Install → reload the browser (Ctrl/Cmd-Shift-R).

Everything else the card uses (`markdown`, `vertical-stack`) is built into
Home Assistant. No `card-mod`, no ApexCharts required for this layout.

> Optional later: **ApexCharts Card** (HACS → Frontend) if you want a proper
> graph on top. Not needed for the minimalist card.

## 2. Add the card

1. Open the dashboard → top-right pencil (Edit) → **＋ Add card** → scroll to
   **Manual**.
2. Paste the contents of `smart_energy_card.yaml`.
3. Save. It renders as a single stacked card.

(Or use ⋮ → *Edit in YAML / Raw configuration editor* and drop it under `cards:`.)

## 3. Entity name

The card assumes the main sensor is `sensor.smart_energy`. If HA created it as
`sensor.smart_energy_2` (e.g. re-added), either rename it under
*Settings → Devices & Services → Entities*, or find/replace the entity id in
the YAML.

## 4. Notes on the heatmap

- Colours come straight from the engine's `level` (0 cheapest … 4 dearest), so
  the dashboard does **no** maths — matches the "engine does the thinking" design.
- The number of rows = the `heatmap_hours` you set on the integration (default 12).
- Bars scale to the most expensive hour shown.
