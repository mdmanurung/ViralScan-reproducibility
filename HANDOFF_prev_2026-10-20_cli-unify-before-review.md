# Handoff — CLI unify (PR A in flight), Track A remaining tasks

**Date:** 2026-10-20 · **Branch:** worktree `../vs_work/cli-unify` on `codex/cli-unify` @ `9151da9` (39 uncommitted entries; `origin/main` = `9151da9`, CI green) · **Status:** PR A code, docs and tests written but not committed; anello work stopped; Track A waits on Codex controllers and your OKs.
Shared root stays on `codex/drop-py39` @ `5e551c9` (dirty; never reset/clean/stash/stage wholesale; local `main` is stale at `253f033`). `R=/exports/archive/hg-funcgenom-research/mdmanurung/viralscan_work/trackA_round1`. Previous handoff: `HANDOFF_prev_2026-10-20_trackA-anello.md` (root `HANDOFF.md` is shared with the Codex perf thread; copy it aside before overwriting).

## Goal
Unify the CLI (PR A, `CLI-UNIFY-01`) and put follow-up outputs inside the run (PR B, `CLI-UNIFY-02`); finish the Track A report and deletions.

## Next action
In `../vs_work/cli-unify`, read the end-to-end result: `tail -3 /tmp/claude-149488/-exports-archive-hg-funcgenom-research-mdmanurung-ViralScan/4cf4bab0-2c4c-454d-a2b9-01f0a2628095/scratchpad/e2e.log`. If the file is gone, rerun it: `PATH=<env>/bin:$PATH PYTHONPATH=src python -m pytest tests/integration/test_tiny_end_to_end.py tests/integration/test_truth_panel_exact.py -m "integration and not network"`. Env is `viralscan_test_full`. `python` must be on PATH, or the release-static tests fail with 127.

## State
- **Last full run:** 2 failed, 48 errors. All 48 errors are in `test_tiny_end_to_end.py`, and one failure is `test_truth_panel_exact`. Both integration files were edited after that run started collecting, so these results are stale; the e2e rerun is the check.
- **Inventory failure:** `test_artifact_inventory` fails as expected. Its three rows (README, `docs/faq.md`, `docs/output_reference.md`) need re-pinning after the commit.
- **Clean:** ruff, ruff format, mypy, `gen_cli_reference.py --check` and `validate_claim_registry.py` all pass. `tests/test_cli_unify.py` passes (36 tests).
- **Queue:** `stablr2` 25833654 is running Codex's EBCD cohort (never cancel it). `tA_advance` 25851736 and `vr03_v3` 25772516 are pending. All `tA_anello_*` jobs are cancelled.

## PR A remaining (`CLI-UNIFY-01`, PLAN.md row already written, still `[ ]`)
1. Get the e2e and truth-panel tests green, then rerun the full suite.
2. Re-execute the 6 CI vignettes.
3. Make commit 1: `feat(cli)`, with PLAN `[x]` in the same commit.
4. Make commit 2: re-pin the 3 inventory rows to commit 1, following the pattern in `9151da9`.
5. Before merge, check that `tA_advance`, `vr03_v3` and the `$R/scripts` jobs import `vs_pinned`, not main. You push and merge. A re-pin PR follows the rebase-merge.

## PR B remaining (`CLI-UNIFY-02`, not started, about half a day)
1. Read the writers for `evidence`, `rerun-multimap` and `hostresponse`.
2. Choose defaults. `evidence` writes to `results/evidence/<target>/`; check for a clash with auto-evidence's `results/evidence/<genus>/` and its reuse receipt. `rerun-multimap`: check whether its output nests a sample tree. `hostresponse -o` becomes `--run-dir`.
3. **Your call:** does `--run-dir` mean the run root (which can hold several samples) or a sample dir?
4. Make `-o` optional, set `layout_version` to 2, and update `output_reference.md`. Run `validate-run` on a run that has the new outputs.

## Track A remaining tasks
| # | Task | Owner | State | Blocked on |
|---|---|---|---|---|
| 1 | Zero-mapping recovery (29 Drop-seq searches) | Codex | Stopped: 52 `verify_zero` errors, 3/29 receipts; late retry added none (26 missing) | Diagnosis |
| 2 | EBCD cohort, 22 targets | Codex | Running in 25833654 (24 h controller cap) | — |
| 3 | GBCD, then DIVAS capped probes | Codex | Waiting | #2 |
| 4 | Production-shape probes | Codex | 5/5 steps done (EBCD pass, DIVAS timed out at 900 s) | — |
| 5 | `reconcile_tables.py` refresh, dataset verdicts, report | Claude | Not started | — |
| 6 | HHV-6B deletion dry-run | Claude | Unblocked: 9/9 replays `exact_sparse_arrays_match_saved_baseline` | **Your OK** (dry-run; delete is a second OK) |
| 7 | Deletion for hsv1, hpv16, hnscc, ebv | Claude | 71/71 READY; 218 folders, 2.3 TB; disk 93% | **Your OK** per dataset after its dry-run |
| 8 | Remote BLAST of candidates | Claude | Not started | Candidate counts, then **your approval** |
| 9 | TRACKA-HOST-02 scaling pilot | Codex | Not started | **Your call**: new SLURM job or 25833654 |
| 10 | Tonsil atlas missing from `status/deletion_readiness.tsv` | Claude | Not checked | — |
| 11 | Anello evidence | — | Stopped by you; 8 hsv1 pairs: STAR 0 aligned (99.97% "too short") | Paused |
| 12 | One Track A git commit (report, scripts, `.living`, PLAN rows) | Claude → you | Waiting | #5; you review and push |

## Locked decisions
- CLI: a hard break with no aliases. `viralscan run` is the quantification command, and a bare `viralscan` warns and runs it. Follow-up outputs go inside the run, and `dest` names are unchanged. (user, 2026-10-20)
- The PR A rename table is approved as written in `docs/migration.md` of the worktree. (user, 2026-10-20)
- Anello work stopped because still nothing is found; no hnscc wave. (user, 2026-10-20)
- Carried over: merges are rebase-merge only. Deletion follows the approved protocol (`trackA-deletion-protocol` memory). HHV-6B deletion waits for the replays and needs an explicit OK. The anello reference is not expanded.

## Dead ends — do not redo
- STAR exit 139 is not fixed by `--soloMultiMappers Unique`/`Gene`, and it is not OOM. Only no-Solo or a dummy whitelist exits 0.
- `run_fresh_control.py` drives frozen pinned binaries; do not port it to the new CLI.
- Inventory pins on PR commits go stale on rebase-merge; re-pin after the merge.

## Read first
- `../vs_work/cli-unify/src/viralscan/cli/parsers.py` (`REMOVED_OPTIONS`, `parse_args`, `_build_run_parser`).
- `../vs_work/cli-unify/PLAN.md`, row `CLI-UNIFY-01` (decisions and what was left untouched).
- `HANDOFF_trackA_2026-10-20.md` for Track A controllers; `analysis/trackA_report_2026-10-18/recovery_2026-10-19/` for receipts and logs.
- `.mycelium/last-session.md`; `.living/learnings.md`, heading "2026-10-20 — STAR 2.7.11b segfaults in Solo ...".

## Open items
- NORM-SHIFT-01 PR, scAutoQC decisions, g3-signing, `tchem`/`virus-taxonomy` PRs: see `HANDOFF_pending_approvals_2026-10-19.md`.
- Doc nit: `docs/reference_panel.md` repeats `viralscan data fetch`; `docs/write-docs-prompt.md` still shows the old flags (left on purpose).
