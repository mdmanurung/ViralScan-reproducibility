# Tracker

Live status of the package/analysis split. Update after any work, and add a row
to `CHECKSUMS.md` whenever a verification runs.

Statuses: `pending` · `in_progress` · `verified` · `blocked`

**Rule 0 applies.** The source is never modified — no `rm`, no `mv`, no
`git rm`, no rename. Deletion is Phase F and requires explicit approval. See
`README.md`.

**Baselines must be re-captured at execution time.** The repo is being modified
concurrently (see `RISKS.md` R15). Never read a baseline from prose.

## Phases

| Phase | Description | Status | Date | Evidence |
|---|---|---|---|---|
| A | Freeze and baseline | pending | — | — |
| B | Scaffold the analysis project | pending | — | — |
| C | Re-root the artifact inventory (`location` column) | pending | — | — |
| D1 | create `viralscan_analysis/` + `check_analysis_split.py` | pending | — | — |
| D2 | `ViralScan/analysis/*` → `analyses/*` | pending | — | — |
| D3 | `ViralScan/covid_viralscan/` → `studies/covid/` | pending | — | — |
| D4 | `ViralScan/results/` + 7 prose files | pending | — | — |
| D5 | probes + 4 reference-panel builds (incl. `viral_ref_cat42b/`) | pending | — | — |
| D6 | `ebv_latest_ref_2026-09-27/` + `viral_panel_max_2026-09-28/` | pending | — | — |
| D7 | `references/` + `starsolo_p22_6{,b}/` | pending | — | — |
| D8 | `viralscan_work/` | pending | — | — |
| D9 | `viralscan_showcase/viralscan_showcase/` | pending | — | — |
| D10 | `ViralScan/benchmark_runs/` | pending | — | — |
| E | Verification report | pending | — | — |
| F | Deletion | **blocked** | — | user approval required, per stage |

Symlink work inside Phase D: D6 records the 112 `parity_mechA` links breaking,
D8 recreates all 112, D9 recreates the 8 showcase links, D10 confirms its 3,000
links and 25 pre-existing broken links survived unchanged. See
`MIGRATION_PLAN.md` §2 Phase D.

Open decisions Q1–Q5 in `DECISIONS.md`; Q1 blocks Phase D, Q5 blocks Phase C,
Q2 blocks D7 and D10, Q3 blocks Phase F cleanup.

## Phase A — Freeze and baseline

| Step | Expected | Status |
|---|---|---|
| `.gitignore` for `ebv_latest_ref_2026-09-27/` | ignored | pending |
| `.gitignore` for `viral_panel_max_2026-09-28/` | ignored | pending |
| `.gitignore` for `sources/` | ignored | pending |
| `.gitignore` for `covid_viralscan/results_v3_exploratory/` | ignored | pending |
| `.gitignore` for `covid_viralscan/results_v3_strand_reverse/` | ignored | pending |
| `.gitignore` for `covid_viralscan/results_v3_strand_unstranded/` | ignored | pending |
| Commit modified governance files | clean porcelain for tracked files | pending |
| Record HEAD, tracked count, porcelain counts | in `CHECKSUMS.md` baseline | pending |
| Baseline inventory to `manifests/` | path, size, mtime, sha256 | pending |

The six `.gitignore` steps come **first**, before any commit. Re-enumerate
untracked-not-ignored paths at execution time — the count changes as new runs
land (see `RISKS.md` R11).

## Phase B — Scaffold

| Step | Expected | Status |
|---|---|---|
| Remove broken self-symlink `viralscan-analysis -> viralscan-analysis` | gone | pending |
| Create target skeleton per `MIGRATION_PLAN.md` §1 | all dirs exist | pending |
| Write project `README.md` | non-empty | pending |
| Write `DATA_MANIFEST.md` schema | schema only; populated from D onward | pending |
| First commit in the analysis repo | 1 commit | pending |

`ANALYSIS_MANIFEST.md` is copied at **D2**, not here — see the stage list.

## Phase C — Re-root the artifact inventory

| Step | Expected | Status |
|---|---|---|
| Relocate TSV `analysis/` → `provenance/` | file in place | pending |
| Add `location` column, enum `package`\|`analysis` | column present | pending |
| Backfill all 30 rows to `location=package` | 30 rows | pending |
| Add rows for analysis-side artifacts as each D stage verifies | ≥1 `location=analysis` row | pending |
| Extend `schemas/v3/artifact_inventory.schema.json` | enum + `required` | pending |
| `scripts/validate_artifact_inventory.py:36` | reads repo path; `ANALYSIS_ROOT` for analysis rows | pending |
| `scripts/validate_claim_registry.py:40` | same | pending |
| `tests/test_artifact_inventory.py` | updated | pending |
| New test: `location=analysis` resolves with `ANALYSIS_ROOT`, raises without | added | pending |
| `MANIFEST.in:11` repointed to `provenance/…` | line updated | pending |
| `config/public_ship_scope.json` sdist member repointed | 107 members unchanged in count | pending |

Do **not** touch the existing `scope` column — it is required, constrained to
`public`|`private`, and populated in all 30 rows.

## Gates

| # | Command | Expected | Status |
|---|---|---|---|
| 1 | `PYTHONPATH=src python -m pytest tests/ -v` | all green | pending |
| 2 | `python scripts/check_ship_scope.py` | 63 / 107 / 53 / 13 / 3 (re-verify) | pending |
| 3 | `python scripts/validate_artifact_inventory.py` | all rows resolve | pending |
| 4 | `python scripts/validate_claim_registry.py` | all rows resolve | pending |
| 5 | `python -m build` + member diff | no diff | pending |
| 6 | `ruff check .` | no **new** findings (30 pre-existing at last count) | pending |
| 7 | `ruff format --check .` | no **new** deviations (22 pre-existing at last count) | pending |
| 8 | `check_analysis_split.py` | no leakage | pending |
| 9 | end-to-end `viralscan` re-run | completes | pending |

## Baseline — last measured 2026-10-02 ~15:20

Stale by construction; re-capture at Phase A.

| Item | Value |
|---|---|
| HEAD | `d2845f6` (was `8bfd136`; `bb52a3d`, `5456a15`, `b9274c9` in between; re-capture at Phase A) |
| Branch | `codex/viralscan-v3` |
| Tracked files | 606 |
| Working tree | 31 lines: 3 modified, 28 untracked |
| `migration_plan/` | 12 `.md` files, untracked |

## Progress log

| Date | Phase | What happened | Next |
|---|---|---|---|
| 2026-10-02 | — | Surveyed both repos and 8 sibling directories; measured sizes, hardlinks, sparseness; drafted plan; created `migration_plan/`. Nothing copied, modified, or deleted outside it. | — |
| 2026-10-02 | — | **Pass-1 fact-check.** Four parallel read-only agents; every material finding re-verified directly. Found 3 critical defects (the `scope` column collision; the cross-repo sdist impossibility; unmirrored rsync excludes making D1–D6 unverifiable), 19 wrong numbers, 9 wrong facts, 7 undocumented conditions, 29 consistency defects. All corrected; recorded in `REVIEW.md`. `.gitignore` gained a `migration_plan/` block. | Answer Q1–Q5, then start Phase A. |
| 2026-10-02 | — | **Pass-2 consistency review + pass-3 drift review.** Independent re-read found 6 cross-doc defects and 5 unguarded instructions; all fixed. Active jobs then wrote ~230 GB into in-scope trees during review (`covid/` 266→495 GB apparent across the day); new sibling `viral_ref_cat42b/` (20 GB) added to D5; tiers now 675 GB / 2.99 TB / ~3.7 TB total. Baselines re-stamped. Both recorded in `REVIEW.md`. | Answer Q1–Q5 (plus freeze-vs-accept in new `RISKS.md` R20), then start Phase A with a full re-measure. |
| 2026-10-02 | — | **Pass-4 drift + residual cleanup.** HEAD `d2845f6`, 606 tracked, ship-scope 63/107, ruff 31 errors. Six `.gitignore` rows, Rule 0 scope clarified for Phase C, D1–D6 labels standardized, REVIEW pass-1 values annotated as historical. | Answer Q1–Q5 (plus R20 freeze-vs-accept), then Phase A with full re-measure. |
