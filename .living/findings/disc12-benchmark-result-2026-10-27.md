# F-029 — DISC-12 discovery benchmark: no `k` for `prioritized`, defaults not assessed

**Date:** 2026-10-27 · **Status:** confirmed under the frozen protocol (`docs/plans/2026-10-22-discovery-benchmark.md`,
frozen 2026-10-23) · **Receipts:** `results/discovery_benchmark/2026-10-27/` (`freeze_manifest.json` with sha256 of every
file, 182 arms, `metrics.tsv`, `decisions.json`, `DEVIATIONS.txt`, `slurm_jobs.txt`).

## Result (frozen rules, §5)
- **182/182 arms** scored by the blind `scripts/disc12_metrics.py`; truth = each positive's primary per-cell unique
  molecules (`counts_unique`, see `docs/plans/disc12/truth/truth_provenance.json`).
- **Rule 2 (`k` for `prioritized`): none**, for every database and configuration. The covid positive LUM-SJ-x213-g is
  capture-only (0 unique SARS-CoV-2 molecules in the primary run, as §2 foresaw) and its panel virus is never reached, so
  no `k` lets the panel virus reach `prioritized` in every positive. Per §5.2, `prioritized` is left unbuilt; the package
  removed the state before release (package PLAN `DISC-19`).
- **Rule 1 (Kraken2 defaults): not_assessed** (it needs the rule-2 `k`). Per §5.5 this is not a "keep"; the 0.05 / 4
  CLI defaults stay as documented uncalibrated defaults.
- **Rule 3:** not_assessed (spike-in only). **Rule 4:** both DBs reported side by side; viral-only stays capped (G15).
- At the shipped default (0.05 / 4, PlusPF) the three herpesvirus positives reach species: truth-cell fraction 0.98 (EBV),
  1.00 (HHV-6B), 0.69 (HSV-1); Spearman with truth 0.47 / 0.95 / 0.91.

## Exploratory, NOT a decision input (post-hoc, user grilling Q4)
Re-scoring rules 1-2 without the capture-only positive, on PlusPF: `k` = max eligible non-truth groups in the negatives + 1
= **1648 at 0.05 / 4** (3886 at 0.0 / 4, 288 at 0.1 / 4, 67 at 0.2 / 4); every herpesvirus positive reaches it. Rule 1 would
still keep 0.05 / 4: stricter settings cut negative false-positive taxa (108 → 32 at 0.1 / 4) but lose recovery in at
least one positive. This was computed after seeing results; it changes no default and is input to a future protocol round.

## Limits
- Panel-positive truth is ViralScan itself (§7): agreement, not accuracy.
- Three negative libraries show whether false positives occur, not their rate.
- The removed `k = 3` would have flagged many negative taxa: the negatives carry non-truth taxa with up to 1647 eligible
  groups at the default.
