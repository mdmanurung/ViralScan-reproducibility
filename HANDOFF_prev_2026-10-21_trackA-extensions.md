# Handoff — finish software extensions + Track A (parallel workstreams)

**Date:** 2026-10-20 · **Root:** shared dirty checkout `codex/drop-py39` @ `5e551c9` (103 entries; never edit/stage/stash/reset it) · **Main:** `origin/main` @ `f4965d0` · **Status:** 5 rebased branches await user push; CLI-unify agent running; HHV-6B deletion waiting on a Slurm job.
Old root handoff (reviewed-roadmap) copied aside: `HANDOFF_prev_2026-10-20_reviewed-roadmap.md`. Full plan: `/home/mdmanurung/.claude/plans/thorouhgly-plan-for-all-dreamy-lamport.md`.

## Goal
Land every software extension and finish Track A without touching the shared root. Done = all PRs pushed/merged by the user, report finished, HHV-6B BUS deleted, cohort decision made.

## Next action
`gh pr list --repo mdmanurung/ViralScan --state open`; if the user has pushed the roadmap PR, check that the CLI-unify agent (`vs_work/cli-unify`, branch `codex/cli-unify`, WIP backup `codex/cli-unify-wip` @ `e7d83fe`) reported. Then `squeue -j 25854135`: when it runs, do T1 below.

## State
- Branches ready, NOT pushed (each has `pre-rebase-2026-10-20/*` tag): `codex/reviewed-roadmap` c85f290 (`/tmp/viralscan-reviewed-20261020`, seqid fix, 5924 passed), `codex/docs-revision` 30d16dd (`vs_work/docs-port`, scanpydoc untested), `codex/shifted-log-normalization` c133734 (`/tmp/viralscan-shifted-log-candidate`), `codex/tchem-second-opinion` 2d69f1e (`vs_work/tchem`), `codex/virus-taxonomy-rollup` cea6276 (`vs_work/taxonomy`). Push/PR commands are in the agents' reports in the transcript; user order: roadmap, docs, shifted-log, tchem, taxonomy.
- Merged: PR #85 (`f4965d0`, REF-11 panel script; 12 CI checks were still running).
- Running: CLI-unify agent (WS-9) rebasing onto roadmap c85f290; allocation 25833654 (EBCD cohort 3/22, ~2d9h of 4d used).
- Pending jobs: `tA_provenance_window` 25854135 (nodes DOWN/reserved reason), `tA_advance` 25851736 held by the window (3 passes left). `vr03_v3` cancelled.
- Track A report updated: `analysis/trackA_report_2026-10-18/REPORT_2026-10-19.md` (369 lines, `.bak_2026-10-20` copies beside edited files). Readiness 71/71 READY. Molecule replays 9/9 exact. Anello: 71/138 pairs classified; HHV-6B scoped NEGATIVE; HPV16 NOT TESTABLE; EBV 6/6 zero molecules, no verdict issued.
- Orphan `snakemake` PID 2408964 (old pytest dir) — user may kill; not ours.

## Locked decisions (user 2026-10-20, `.living/decisions.md` rounds 1–3)
- Claude rebases/tests in worktrees, user pushes. Docs: keep scanpydoc + api pages. Coverage map strips `VIRUS|` for viral refs only. Roadmap lands before CLI-unify. Research trees: commit text <1 MB, gitignore bulk. G3 signing after rc1. Perf G02/AA-02/04 deferred. flashier/cellprograms split dropped. Quickstart vignette run once on Slurm after docs merges. Prune merged branches after WS-6 (done: PR #85).
- hsv1 anello wave 2 deliberately stopped; 17 zero-mapping tasks not rerun; no hnscc wave.
- HHV-6B derived-intermediate deletion authorised (130 paths, 1072.5 GB).

## Dead ends — do not redo
- Fighting the provenance job with partition edits — it goes back to "nodes DOWN/reserved"; just wait.
- GBCD at maxiter 500 — rejected (200-cell run and 800-cell probe both hit the iteration limit). Grill Q9 approval is void (correction logged).
- `scontrol show job` on finished jobs — purged; use `sacct` (verifier fixed).
- Adopting the shared-root `if not config.scautoqc:` filter skip — contradicts the keep-legacy-filter decision.

## Read first
- `.living/decisions.md` tail (2026-10-20 rounds, Q9 correction) and `.living/learnings.md` (scontrol note).
- `analysis/trackA_report_2026-10-18/REPORT_2026-10-19.md:344` — open-decisions section.
- `$R/scripts/{deletion_window.sh,delete_bus.py}` with `R=/exports/archive/hg-funcgenom-research/mdmanurung/viralscan_work/trackA_round1`.
- `.mycelium/last-session.md`, `HANDOFF_trackA_2026-10-20.md`.

## Open items
- T1 HHV-6B BUS deletion: when 25854135 finishes -> confirm no running `tA_evidence_finish|summaries|provenance|advance|off_*` -> `delete_bus.py hhv6b` dry run (expect 130 paths / 1072.5 GB, no refusal) -> `--yes` -> only then `deletion_window.sh --release`.
- User decisions: EBCD continuation allocation (~39 h left vs ~60 h), GBCD maxiter or skip, cancel `tA_advance` after deletion, EBV scoped verdict, CLI-UNIFY-02 `--run-dir` meaning, per-dataset deletion OKs (hsv1, hnscc, ebv, tonsil), tchem install (tonsil chemistry).
- Wave 2 after merges: scAutoQC rebase on shifted-log+tchem (keep legacy filter; add mypy/ruff entry), research-tree commit PRs, vignette Slurm run, prune stale worktrees, one final inventory re-pin, list shared-root-only content for user OK.
- Pins (`analysis/v3_artifact_inventory.tsv`, PLAN.md) go stale on every rebase — redo once, last.
