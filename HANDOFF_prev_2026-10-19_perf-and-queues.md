> **Performance update — 2026-10-20:** [PR #77](https://github.com/mdmanurung/ViralScan/pull/77) is **rebase-merged** as `253f0339` after all 12 CI checks passed on `0408639`. The user accepted the documented 55-byte raw-index compatibility exception by requesting merge after the explicit approval question. Its cause remains unexplained; failed evidence and strict comparators are preserved. Remote main and clean local main are verified at `253f0339`. The original CPU-budget branch is retained for source-provenance references. [Receipts](analysis/computational_bottlenecks_2026-10-17/followups/20261019-performance-monitor/REPORT.md). No production benchmark or SLURM submission was run.
>
> The 2026-10-19 handoff below is preserved as a historical snapshot for the other work queues; those queues were not re-audited in this performance session.

# Handoff — branch cleanup, CPU budget, original-API docs, scautoqc

**Date:** 2026-10-19 · **Branch:** shared root `codex/drop-py39` @ `5e551c9` (dirty, 80 entries; never reset/clean/stash/stage wholesale) · **Status:** two workflows running; nothing pushed except two snapshot branches.

## Goal
Land, in order, via rebase-only PRs: `cpu-budget` → `orig-api-docs` → `tchem` → `virus-taxonomy` → `shifted-log` → `g3-signing` (last, user signs). Leave local and remote branches clean.

## Next action
Check both workflows (`/workflows`; runs `wf_dd16b6d1-a75` cpu-budget requalify, `wf_44ab4bbb-3b5` scautoqc+notes builds). When `cpu-budget` reports: read its result, run its tests in `../vs_work/cpu-budget`, then push `codex/cpu-budget` and `codex/orig-api-docs`, open PRs, merge in that order after CI is green.

## State
- Worktrees (all under `../vs_work/`): `cpu-budget` @ `67b4e0f` (2 uncommitted test edits from the requalify fix), `orig-api` @ `f2f9462` clean, `scautoqc` (branch `codex/scautoqc`, 15 uncommitted), `notes` (branch `codex/shared-root-notes`, 34 uncommitted). `main` worktree `vs_work/main` @ `6bd1652`.
- Remote branches: `main`, `codex/drop-py39` (kept: root tracks it), `codex/g3-signing-r2`, `codex/scautoqc-wip` `92dd88e` and `codex/shared-root-snapshot-2026-10-19` `728cc76` (old backups, delete after the rebuilt branches land).
- Deleted: 128 local + 56 remote merged branches, 5 landed local branches, 14 agent worktrees. Local tag `archive/perf-wave1-prerebase` → `dec9885` (not pushed; the remote wave-1 tag points at the rebased commits only).
- `orig-api-docs` carries: original-style CLI flags (`-reference True`, value booleans), README + Sphinx on the upstream skeleton, Clarity theme, `pixi.toml`, `Singularity.pixi.def`, DOC-API-01 fix. Full suite 5829 passed / 15 skipped before the theme/pixi edits; docs/governance tests pass after.
- SIF built and tested 2026-10-19 (apptainer 1.3.6 via `/share/software/apptainer/1.3.6/bin`, unprivileged): doctor ok, tool pins match. SIF at the session scratchpad only.
- Docs site served on `127.0.0.1:8765` of `res-hpc-exe049` (dies with the node); built HTML in the scratchpad `site/`.
- Pending SLURM jobs (Track A, user's) run from the shared root; do not disturb it.

## Locked decisions
- `--cores` is the total CPU budget; bound workers/scheduler reservations (user, 2026-10-19). Changed bytes need a separate compatibility decision; never normalize.
- Merge order above; separate PR per finished branch; fold `plan-doc-api-enrichment` into `orig-api-docs` (done) (user, 2026-10-19).
- `shifted-log` merges after native CLI check + full PR CI only, no before/after benchmark; no TP10K flag (user, 2026-10-19).
- `g3-signing-r2` untouched until the user decides to sign; rebase just before signing (user, 2026-10-19).
- scAutoQC only flags, never removes cells; legacy UMAP count/gene filter stays unchanged (user, 2026-10-19).
- Rebase-only PR delivery; never push to `main` directly. Preserve tags `provenance/perf-*`.

## Dead ends — do not redo
- `pixi lock`/`pixi install` solves ALL environments: install `-e default`; docs env needs `beautifulsoup4==4.13.3` (Clarity dep pin). `pixi lock` failed on a uv cache lock held by another process (`~/.cache/rattler/.../uv-cache`); retry once idle. No `pixi.lock` committed.
- `pkill -f "pixi lock"` kills your own shell (command line matches).
- SRR20710641 (HHV-6B CAR-T) ENA FASTQ is real 10xv2 5' with barcodes in R1 (88.2% on-list, `viralscan check-chemistry`); stream a slice over HTTPS, no sra-tools needed. Vignette real-data swap NOT done yet.

## Read first
- `../vs_work/orig-api/PLAN.md` rows `DOCS-ORIG-01`, `CLI-ORIG-01` — what was verified vs not.
- `../vs_work/cpu-budget/docs/plans/2026-10-19-performance-resource-policy.md` — budget semantics.
- `HANDOFF_scautoqc_2026-10-19.md` (in `codex/scautoqc-wip`) — open scautoqc gates.
- Branch triage verdicts: tchem, virus-taxonomy → rebase+PR; shifted-log, g3 → need user sign-off.

## Open items
- Vignettes → real data (SRR20710641 slice for quickstart/reference notebooks; CI notebooks stay synthetic) — user asked 2026-10-19, not started.
- scautoqc real FASTQ→UMAP validation (SRR8315713) — needs kb env + reference; user decision.
- Untracked bulk in shared root (15 GB `analysis/translated_search`, 1.3 GB bottlenecks, `tmp/`, `.living/archive`) — decide gitignore/move.
- Delete old `codex/scautoqc-wip`, `codex/shared-root-snapshot-2026-10-19`, `codex/plan-doc-api-enrichment` after replacements land.
- Production CPU-budget qualification and G02 timing remain unmeasured; no SLURM without approval.
