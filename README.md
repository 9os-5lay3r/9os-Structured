# 9os-Structured

Straight up compilation — two published Pine Script indicators, fused into **one** v6 indicator.

| File | What it is |
| --- | --- |
| `ICT_HTF_Candles_LuxAlgo.pine` | The merged indicator: `ICT HTF Candles (fadi)` + `Smart Money Concepts [LuxAlgo]` |

## Source material

| Module | Original script | Author | Licence |
| --- | --- | --- | --- |
| A | `ICT HTF Candles (fadi)` (v6) | fadizeidan | MPL 2.0 |
| B | `Smart Money Concepts [LuxAlgo]` (v5) | LuxAlgo | CC BY-NC-SA 4.0 |

Both works stay licensed as published. Anything derived from module B is bound by
CC BY-NC-SA 4.0 (attribution, non-commercial, share-alike); anything derived from module A carries MPL 2.0.
If you republish this file, keep this notice and both attributions.

## Install

1. TradingView → **Pine Editor** → *Open* → **New indicator**.
2. Paste the whole content of `ICT_HTF_Candles_LuxAlgo.pine`.
3. **Save**, then **Add to chart**.
4. Open the indicator settings. Everything from both originals is there, plus two new groups:

### New groups (the only settings that did not exist before)

- **Master** — `ICT HTF Candles` on/off and `Smart Money Concepts` on/off. Each module can be isolated.
- **Theme** — the SMC `Style` selector (was *Smart Money Concepts → Style*) with editable monochrome colours,
  plus two bridge switches: *Colour HTF candles with the SMC structure trend* and *Show legend*.

Every other input keeps the name, group, default and meaning it had in its original script.
Groups that come from the SMC module are prefixed with `SMC · ` so the input tree stays readable.

## What is in the merged file

- One `indicator()` declaration (`overlay = true`, 500 boxes / 500 lines / 500 labels, `max_bars_back = 5000`).
- **ICT HTF Candles**: up to 6 higher-timeframe candle sets drawn to the right of price, with HTF labels,
  remaining-time counters, interval stamps, price labels, FVG and volume-imbalance boxes.
- **Smart Money Concepts**: internal + swing structure, order blocks, EQH/EQL, fair value gaps,
  strong/weak high-low, MTF daily/weekly/monthly levels, premium/discount zones and all 16 alerts.
- A single legend label (bottom right) summarising what is currently drawn.

The header comment block inside the `.pine` file lists every deviation from the two originals, and every line
that differs from an original is tagged with `// [merge]` or `// [v6]` so the two can be diffed.

## Things worth knowing

- **Drawing budget is shared.** TradingView allows ~500 lines, 500 labels and 500 boxes per script.
  Both originals already asked for the maximum, so the merged script has one shared budget instead of two.
  With the shipped defaults the ICT rows use roughly 60 boxes / 120 lines, which leaves plenty for the SMC
  module. Turning on *SMC · Fair Value Gaps* on a very long chart grows boxes over time (they are only removed
  once price mitigates them) — that is original LuxAlgo behaviour.
- **v5 → v6.** The LuxAlgo half was ported to Pine v6 by hand: typed inputs, monochrome/equilibrium colour
  consistency, a default branch in the MTF level style switch, empty-slice guards in the order-block/level
  maths, and the 16 `alertcondition()` calls hoisted to the global scope (they cannot live inside the
  `if show_smc` block) with per-bar boolean carriers.
- **Two features are intentionally not merged:** the SMC fair value gaps stay chart-space (MTF, mitigated by
  price) while the ICT FVG/VI boxes stay per-HTF-row — different tools, both opt-in.
- The custom daily open (`Midnight / 8:30 / 9:30` New York) now compares New York calendar days instead of
  guessing from offsets, so the daily candle opens exactly once per day, on the first chart bar at or after the
  chosen hour, and it works on any chart timeframe.

## Disclaimer

Research/visualisation tooling. Nothing here is financial advice, and the originals' logic is preserved as-is —
verify anything you trade on.
