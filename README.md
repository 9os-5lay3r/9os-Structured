# 9os-Structured

Straight up compilation — two published Pine Script indicators, fused into **one** v6 indicator named **`9os.XLR8`**.

| File | What it is |
| --- | --- |
| `9os.XLR8.pine` | The merged indicator: `ICT HTF Candles (fadi)` + `Smart Money Concepts [LuxAlgo]` |
| `tools/pine_lint.py` | Offline checks for the Pine v6 gotchas this repo has already hit (see below) |

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
2. Paste the whole content of `9os.XLR8.pine`.
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

## CRT highs & lows (new)

Every HTF candle row can stamp **CRT-H** and **CRT-L** on the high and the low of its **newest closed candle** —
the range candle of Candle Range Theory, which is where the liquidity sits.

- **Per-row switch**: `CRT-H/L` sits on the right of each of the six `HTF n` rows, so you can run it on the
  Daily row only, on everything, or on nothing. All six are **on** by default; turn off the ones you don't want.
- **The levels ride along**: when a new HTF candle opens, the range candle rolls forward and the CRT lines and
  tags move with it. `candles[0]` is the candle still forming, so the range candle is always `candles[1]`;
  a row that has not closed a candle yet shows nothing.
- **Fixed length, never extended right**: the line spans the range candle plus `Line padding` bars at each end
  (default 3, so roughly an 8-bar level) — long enough to read as a level, short enough not to reach the next
  row. It deliberately does **not** use `extend.right`.
- **Tags**: `CRT-H` above the line and `CRT-L` below it, centred on the range candle, so nothing sits on top of
  the newest candle of the row.
- **Style group** `CRT Highs & Lows`: high / low colour, line style, width, padding and label size.
- Each row's CRT drawing costs 2 lines + 2 labels. The legend appends `· CRT` to every row that has it on.

## Fixed after the first Pine compile

| Problem | Fix |
| --- | --- |
| `CE10235 — Return type of one of the "if" or "switch" blocks is not compatible… (series label; void)`, raised on the HTF label block in `Reorder()` | Pine v6 rejects an `if/else` whose one branch ends with a value (e.g. `x := label.new(...)`) and the other with a `void` call (e.g. `label.set_xy(...)`). All fourteen occurrences (HTF labels, remaining-time labels, interval stamps, trace lines and price labels, legend) now use a **create if missing, then always move it** shape, so every branch is `void`. |
| `SHORT TITLE TOO LONG (15 characters)` | The script is now called `9os.XLR8` (8 characters), used as both the title and the short title. |

Bugs of the same family were swept in one pass, so the second compile should not surface more of them.

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

## Offline lint

```bash
python3 tools/pine_lint.py 9os.XLR8.pine
```

Five checks, each one added after a real failure in this repo:

| Check | Why it exists |
| --- | --- |
| indentation / tabs | Pine is whitespace sensitive and the editor's error points at the wrong line when it drifts |
| value-vs-void `if/else` | `CE10235`: one branch ending with a label, the other with `label.set_xy()` — this is what the first compile failed on |
| forward references | a user function may not read a global or call a function declared further down (`Reorder()` → `DrawCrt()` was caught here) |
| unknown UDT fields | `settings.foo` regexes used to also match `htfSettings.foo`; the matcher is anchored now |
| trailing whitespace / parens | cheap noise that sometimes hides a real problem |

TradingView remains the only authority — this just catches the classes of mistake it has already reported once.

## Disclaimer

Research/visualisation tooling. Nothing here is financial advice, and the originals' logic is preserved as-is —
verify anything you trade on.
