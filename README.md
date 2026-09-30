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

## CRT highs & lows (Candle Range Theory)

A per-row state machine. Nothing is drawn on candle 1 — the levels only appear once the range has been
**swept and reclaimed**, which is the whole point of CRT.

| Step | What happens | On the chart |
| --- | --- | --- |
| the candle before the current one closes | it becomes **candle 1**, the range | a `1` badge inside the body |
| a later candle *closes outside* candle 1's range | candle 1 is invalidated, the `1` **moves to that candle** | badge moves, old CRT levels and the `2` disappear |
| a later candle **sweeps** candle 1's high or low **and closes back inside** its range | that candle becomes **candle 2** | a `2` badge, and **now** `CRT-H` / `CRT-L` are drawn at candle 1's extremes |
| a candle closes inside the range without sweeping | nothing changes | still waiting on candle 1 |

- **Per row**: `CRT-H/L` sits on the right of each of the six `HTF n` rows (all on by default).
- **Timeframe**: `Only for` in the CRT group defaults to `1H and up` — your H1 / H4 / D / W / M workflow.
  Set it to `Any timeframe` if you also want the 5m / 15m rows to run the engine.
- **Lines**: `Line runs` = `Whole row` (reaches the newest candle of the row, as in the sketch) or
  `Range candle` (stops just past candle 1). `Line padding` adds bars at each end — never `extend.right`.
- **Tags**: `CRT tag` = `Right of line` (text sits at the end of the level) or `Above and below candle`.
- **Candle numbers**: the `1` / `2` badges, with colour and size, can be switched off if you only want levels.
- Every state change is driven by candle *closes* on the HTF, so it behaves identically on history and live.

## Fixed after the Pine compiles

| Problem | Fix |
| --- | --- |
| `CE10137 — Unable to determine the object for the field assignment` on `array.get(candleSet.candles, 1).crt_num := 1` | Pine v6 cannot assign a field on the result of a call. The candle is taken into a variable first (`Candle firstRange = array.get(...)`), then its field is assigned. |
| `CW10003 — The function 'smcModule' should be called on each calculation for consistency` | The SMC module contains `ta.*` state (`ta.highest`, `ta.lowest`, `ta.change`, `ta.crossover`, `ta.cum`, `timeframe.change`) and was called from inside `if theme.show_smc`. **The module now calculates on every bar, unconditionally.** The master switch and the display inputs moved into the draw functions, so they still control exactly what reaches the chart — and what alerts (the per-bar alert state is cleared while the module is off). |

| `CE10088 — Cannot modify global variable "currentAlerts" in function` | A function may mutate a *field* of a global object (`currentAlerts.equalLows := true` — which the LuxAlgo code does throughout) but never the global variable itself. The line that reset the alert object inside `smcModule()` is gone; the alert carriers are now gated at global scope with `theme.show_smc and currentAlerts.x`. |

Behaviour consequence worth knowing: turning the SMC module off no longer freezes its internal state. Structures,
order blocks and gaps keep being tracked in the background (that is what keeps the `ta.*` series identical to
running the module alone), so switching it back on shows a chart that is already up to date. Its alerts stay
silent while it is off, because the carriers are gated by the master switch.

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

Eight checks, each one added after a real failure in this repo (and each one tested by re-injecting its bug):

| Check | Why it exists |
| --- | --- |
| indentation / tabs | Pine is whitespace sensitive and the editor's error points at the wrong line when it drifts |
| value-vs-void `if/else` | `CE10235`: one branch ending with a label, the other with `label.set_xy()` — this is what the first compile failed on |
| forward references | a user function may not read a global or call a function declared further down (`Reorder()` → `DrawCrt()` was caught here) |
| unknown UDT fields | `settings.foo` regexes used to also match `htfSettings.foo`; the matcher is anchored now |
| in-place field assignment | `CE10137`: `array.get(a, i).field := x` cannot compile |
| global writes in a function | `CE10088`: a function reassigning a global variable (fields are fine) |
| stateful calls from a branch | `CW10003`: a `ta.*`-carrying function called inside an `if`, which the editor warns about |
| trailing whitespace / parens | cheap noise that sometimes hides a real problem |

TradingView remains the only authority — this just catches the classes of mistake it has already reported once.

## Disclaimer

Research/visualisation tooling. Nothing here is financial advice, and the originals' logic is preserved as-is —
verify anything you trade on.
