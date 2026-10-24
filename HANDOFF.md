# Handoff — PAUSED for repo split; DISC-12 + host-loss jobs running

**Date:** 2026-10-22 (evening) · **Root:** shared dirty checkout `codex/drop-py39` @ `5e551c9` (never edit/stage/stash/reset it; a Codex session uses it) · Previous: `HANDOFF_prev_2026-10-22_merge-loop.md`.

## Goal
Land all open branches, record the spike-in flank verdict, finish package work → `3.0.0rc1`.

## Update (2026-10-24) — DEVELOPMENT PAUSED for the repo split (user)
- Running (leave alone): DISC-12 arrays 25873325/25873326 (code snapshot in `viralscan_work/disc12_run_2026-10-23/code`, OFFSET scheme, DEVIATIONS.txt); host-loss 25874010 (HH, HHV-6B rows 1-15) + 25874011 (default pool). The host-loss jobs read code from `vs_work/disc12-hosthomolog` — do NOT move/delete that worktree until they finish.
- rc1: #116 merged (4da4674), tag moved there, release run 40038144113 failed at grype scan (Ubuntu 20.04 base). Fix branch `codex/release-image-refresh` 8c463ec (LOCAL ONLY, `vs_work/release-fix`): base 26.7.2-0 + scan JSON on failure. Resume: user builds env `conda/envs/viralscan_lock_2026-10-24` from environment.yml (micromamba R4_51, --strict-channel-priority); then pip check, write_explicit_lock, audit_locks, PR, merge OK, tag OK.
- #117 DISC-12-HH ready for review (merge needs user OK). EBV HH pool empty even from raw (not estimable).
- DISC-12 metrics: `codex/disc12-metrics` c88a0fe (LOCAL ONLY, `vs_work/disc12-metrics`), written blind. Needs per-cell truth TSVs (barcode, molecules) per positive + user answers on 5 protocol ambiguities (script docstring / PLAN row DISC-12-METRICS).
- Open question to user: push the two local branches before the split?

## Update (2026-10-23 night)
- Merged since: #103 `81f2282` (DISC-12 FROZEN), #112 `6e4035e` (`discover --called-cells`), #114 `29adda1`, #113 `84944fe`, #115 `088a8d1` (STAR-GATE-01 = labels only; row STAR-FATE-01).
- rc1: tag v3.0.0rc1 moved to 84944fe; release run 40007587542 FAILED at Docker `pip check` (lock conflict: s-i-c 1.23.1 vs snakemake packaging<26; pyseq-align needs cython). Fix = **PR #116** (`vs_work/release-fix`, branch `codex/release-lock-pipcheck`). After merge + CI green: move tag to the merge commit again (needs user OK).
- DISC-12 run: `viralscan_work/disc12_run_2026-10-23/` (code pinned 84944fe, 182 conditions). Pilot 25872786 (row 83, x213 pluspf c0.05_h4) slow in `read_host_filtered` (pure-Python lineage count, per condition). After pilot: `sbatch --array=0-181%6 run.sbatch` from that dir; then metrics report (protocol §4/§5, G13: no numbers before receipts).
- DISC-12-HH: draft **PR #117** (`vs_work/disc12-hosthomolog`). Flaw: source BAMs align host_filtered reads -> EBV pool 0, HHV-6B lower bound. EBV raw FASTQs exist (`trackA_round1/inputs/GSM4796271/`), HHV-6B raw deleted. User decides: realign EBV raw / HHV-6B-only lower bound / drop arm. Nothing submitted.

## Update (2026-10-23 evening)
- Merged: #109 `61f1b06` (spike-in, flank retired, F-028), #110 `87591c4` (3.0.0rc1 on main; USER pushes tag v3.0.0rc1), #111 `3b5096d` (panel archive script).
- Open: #112 `discover --called-cells` (Q20a; CI running) and #103 DISC-12 protocol (ready, not draft; inputs pinned in `docs/plans/disc12/input_manifest.tsv`; HHV-6B GSM6416022, HSV-1 GSM3511335, EBV, covid x213; negatives GSM3511328/329 + GSM6416026). Merging #103 = the freeze (user). Both need user merge OK.
- Decisions recorded in `.living/decisions.md` (rounds 1-3 + Q20a). STAR-GATE-01 remains the user's; `fate_host` unusable (pruned BAM).
- After freeze: DISC-12 run = build host-homologous spike set (Q16) then the grid (12 configs x 2 DBs) per protocol.

## Update (2026-10-23 ~10:30)
- Merged: #106 `6527e94` (scautoqc tests now run in CI py3.11), #108 `8f834a8` (quickstart real run). Grid 25864985 66/66 done; post-hoc run: **flank index retired** (F-028). PR #109 (`codex/spikein-posthoc`, rebased onto main, receipts in `analysis/spikein_detection_limit/results_2026-10-23/`) needs user merge OK.
- k2_viral_20260626 downloaded + md5-verified; hashes and HHV-6B pick GSM6416022 written into #103 (`262e657`). DISC-12 freeze blocked on open questions Q3' (HSV-1 Drop-seq: my earlier "no called_cells" fact was wrong; twostep runs have them), Q16 host-homologous spike set (grid pool drops host-aligning reads), Q17 input = twostep host_filtered pairs (raw FASTQs of GSM6416022/26 deleted), Q18 negatives GSM3511328/329 + GSM6416026, Q19 covid x213 is in-house.
- Q14 done: 21 merged worktrees removed. Left: rc1-prep (untracked `scripts/make_panel_archive.py`), superseded cli02b-1022 / scautoqc / star-align-1022 / wave2-base-1022.
- Next after #109 merges: Q15 rc1 release-prep PR. STAR-GATE-01 is now the user's decision (SPIKE-01 done).

## Update (2026-10-23 early) — after grilling round (decisions in `.living/decisions.md`)
- Merged since: #88 `8b54485` (main CI+Docs green there), #105 `1c871d5` (STAR route i), #107 `0499fb0` (path scrub docs/scripts).
- Open: #106 CI scautoqc deps (moved to py3.11; sctk 0.2.0 won't build on 3.12) — user approved merge, merge when py3.11-ubuntu passes. #108 quickstart real run (VIG-RUN-01; Slurm 25867622 ok, validate-run ok) — needs user merge OK. #103 DISC-12 decisions written; freeze after user runs `kraken2_db/fetch_viral.sh` and Q4 truth check.
- Grid 25864985: 28/66 at 23:50 on 10-22. Q13: post-hoc through verdict + PR unasked unless recovery <80% of old or >10% rows missing/failed.
- Then Q14 worktree prune (merged + clean only) and Q15 rc1 release-prep PR (user merges + tags).

## Update (night 2026-10-22) — option A (local checks, CI once at end on main)
- Merged: #102 `f32ff7b`, #101 `2c543b6`, #104 `e2cc951`, #99 `95de5ab`, #100 `5b0e8f1`. #88 updated (`codex/docs-revision`), local check passes; docs build dispatched (run 39828579132), merge after it.
- Then watch main's CI (`gh run list --branch main --workflow ci.yml`); fix forward if red.
- Helpers: `vs_work/notes/local_check.sh <branch>`, `vs_work/notes/merge_main.sh <worktree>`.

## Update (late 2026-10-22)
- #99 base switched to main by user; review fixes pushed (`efda8fe` reserved `posthoc` sample ID + cli_reference prose, `30647d2` PLAN note). Merge after CI green (needs user OK per PR).
- #100 mouse-globin fix pushed (`13157b8`). Merge #100 BEFORE #88 (#88 documents `--scautoqc`).
- Codex-bot "unreachable pin" comments on #88/#100 are stale: every pin on every open branch is an ancestor of its tip.
- #104 opened (DISC-13 route ii).

## Next action (original)
1. User switches #99's base: `gh api -X PATCH repos/mdmanurung/ViralScan/pulls/99 -f base=main` (classifier blocks Claude). CI triggers only on opened/synchronize/reopened, so after the switch push a commit (merge origin/main into `vs_work/cli02b-merge`, re-pin) to start CI. Merge only when `baseRefName == main` and 12/12 pass.
2. Ask user for merge approval of #88, #100, #101, #102 (not covered by "merge 92–99"). Each needs merge-main + re-pin after whichever lands first.

## State
- Merged (merge commits): #91 `ae887b1`, #92 `b0bba30`, #93 `2b4b833`, #94 `ad7f393`, #95 `46737c7`, #96 `206b25f`, #97 `0f7c2d2`, #98 `81619c1`.
- #99 `codex/cli-unify-02-layout` @ `8c6dc59` (worktree `vs_work/cli02b-merge`, NOT `cli02b-1022`): main merged in, validator + 184 tests pass; base still `codex/cli-unify-02-hostresponse`, so no CI.
- #88 docs-revision @ `ddc63b6`: main merged, reference_panel "Known limitations" kept, 12/12 CI earlier; strict sphinx build passed (dispatched run 39819678228; only Pages deploy failed, expected off-main).
- #100 scautoqc (rebased, `vs_work/scautoqc-1022`): test_scautoqc skipped in CI (leidenalg/sctk in no env file); 5 pass 5 skip under celloracle env.
- #101 STAR stack (`vs_work/star-confirm`, 13+2 commits): 302 pass, ruff/mypy clean. Merge with a MERGE COMMIT (pins name branch commits). 8 HPC-path lines remain in branch history (tip clean).
- #102 PATHS-01: PLAN.md paths → `$SITE_ROOT`/`$SITE_SCRATCH`/`$COLLAB_ROOT`. ~190 hits in `.living/`, ~300 elsewhere: scope is the user's call.
- #103 DISC-12 protocol DRAFT (`docs/plans/2026-10-22-discovery-benchmark.md`), UNDECIDED items for user.
- Grid array 25864985: 2/66 done at ~17:00, 6 concurrent, ~75 min/row → ~13 h. Watcher `bqm42hprw` (this session only).
- Helpers: `vs_work/notes/trial_merge.sh`, `repin.py <worktree> <path>...` (re-pins rows to HEAD; needs env python), `rebase_resolve.sh <worktree>` (keep-both CHANGELOG/PLAN/.living, main side for inventory/cli_reference, stops otherwise).
- Backups: `backup/scautoqc-rebased-pre-rebase2-2026-10-22`, `backup/star-confirm-pre-rebase2-2026-10-22` (+ earlier `backup/*-pre-rebase-2026-10-22`).

## Locked decisions
- Merge PR by PR with own check; merge commits only (never squash: inventory pins name branch commits).
- Conflict rule for inventory: rows only the branch changed → branch; others → main; then re-pin stale rows to the merge commit.
- All 2026-10-22 grilling entries in `.living/decisions.md` approved. Flank verdict rule unchanged.
- Deletions, Track A sign-off, STAR-GATE-01, D02/D04 start, research-tree commit, installs: user only.

## Dead ends — do not redo
- Merge-loop script / blanket merges: classifier needs per-batch user approval in-session.
- `gh api PATCH pulls/99 base` by Claude: classifier denied ("External System Writes").
- Local sphinx build: `sphinx_design` not installed; dispatch `docs.yml` on the branch instead.

## Open items (Claude)
- After #101 merges: DISC-13 STAR route (i) producer. Route (ii) producer DONE: #104 (`codex/disc13-read-support`, `build_read_support_evidence`, API only, stubbed-aligner tests; no real minimap2 test).
- Merges of #88/#100/#101/#102/#104 need explicit per-PR user approval in-session ("finish all tasks" was not accepted by the classifier).
- Grid done → `vs_work/spikein-posthoc`: `rescore.py`, `aggregate.py check --scores-name scores_v2.tsv`, report, `recovery_ratio.py`; verdict; rebase spikein branches; PR.
- After #88 merges: quickstart vignette on Slurm. Last: prune worktrees (keep `/tmp/vs_work_*`), re-pin inventory.

## Open items (user)
- #99 base switch; merge approval for #88/#100/#101/#102; DISC-12 decisions; repo-wide path scrub scope.
- Research-tree commit, orphan 2408964, report sign-off, HHV-6B gaps 3/4/7/8 then deletion.
