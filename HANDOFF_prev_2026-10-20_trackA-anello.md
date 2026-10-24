# Handoff — Track A anello reruns, merged layout/docs PRs, Codex threads

**Date:** 2026-10-20 · **Branch:** shared root `codex/drop-py39` @ `5e551c9` (dirty, 83 entries; never reset/clean/stash/stage wholesale); `main` @ `9151da9` · **Status:** all PRs merged; 29 hsv1 anello pairs queued; CI on `main` not yet seen green.
`R=/exports/archive/hg-funcgenom-research/mdmanurung/viralscan_work/trackA_round1`. Previous handoff kept at `HANDOFF_prev_2026-10-19_perf-and-queues.md` (the root `HANDOFF.md` is shared with the Codex perf thread; do not clobber it again without copying it aside).

## Goal
Finish Track A anello evidence on real libraries (hsv1 now, hnscc second wave), keep `main` green, then land the remaining branches.

## Next action
`gh run list -R mdmanurung/ViralScan --branch main --limit 3`: check CI on `9151da9`. If a job fails, read it with `gh api repos/mdmanurung/ViralScan/actions/jobs/<id>/logs`. Then `squeue -u mdmanurung | grep anello` for the 29 hsv1 pairs (`$R/anello_settle_2026-10-19/resubmit_hsv1_wave2_2026-10-20.txt`).

## State
- Merged 2026-10-20 (rebase): #77 cpu-budget (`253f033`, user accepted the 55-byte raw-index exception), #78 orig-api-docs, #81 inventory re-pin `c76c3e7`, #82 STAR139 fix `6934f25`, #80 pertpy docs `09563c1`/`af8bb44`, #79 layout `8933a65`/`6410598`, #83 re-pin `9151da9`.
- CI on `main`: runs for `af8bb44`, `6934f25` cancelled (superseded); `9151da9` pending. Full suite and `tests/integration/test_tiny_end_to_end.py` (now expects `results/count_audit.tsv`) NOT run on merged `main`.
- Queue: 29 `tA_anello_aln` + 29 `tA_anello_cls` (hsv1: 18 shipped, 11 relaxed), `stablr2` = allocation 25833654 running Codex's EBCD cohort (do not touch), `tA_advance`, `vr03_v3`.
- mycelium-extra: `docs-restyle-rest` (`a53c926`) pushed; the user fast-forwards `main`.
- Local worktrees under `../vs_work/` are stale: `output-layout`, `docs-pertpy`, `anello-star139`, `cpu-budget`, `orig-api`, `main` (on `codex/repin-output-reference`). `scautoqc` (`ef2bb40`) and `notes` (`9b06bdb`) are unpushed, waiting on decisions.

## Locked decisions (user, 2026-10-20)
- STAR path: wrapper fix plus Codex per-task receipts as a cross-check; the product fix is merged.
- hsv1 reruns cover both settings (29 pairs); hnscc follows as a second wave after the hsv1 results are read; compare Codex receipts 25842262/282/302 and report only disagreements.
- Layout: evonk's files stay; `count_audit.tsv` under `results/`; `layout_version` in the manifest; `combined_summary.tsv` at the run root; manifest stays at the root (pinned test); banner untouched; `summary.txt` opens with evonk's block.
- Codex-owned: GBCD then DIVAS capped probes after the EBCD cohort finishes; HHV-6B deletion waits for all 9 molecule replays, dry-run hhv6b only, explicit OK first.
- No minimap2 vs minibwa benchmark; the anello reference is not expanded (ours 2,040 genomes vs Kojima 3,333; all 1,407 extras hit ours, 728 at >=85% identity).
- Merge policy: rebase-merge only; the user asked for "merge all, CI afterwards".

## Dead ends — do not redo
- STAR crash is not fixed by `--soloMultiMappers Unique` or `Gene` (still 139); not OOM (RSS 1.7 GB of 48 GB); only no-Solo or a dummy whitelist exit 0.
- Inventory rows pinned to PR commits (`ab47b5a`, `04562cf`, `4c352b7`, `10c9b32`) go stale on rebase-merge; re-pin to the merged commit in a follow-up.
- ASM and Nature pages block fetch (403 / cookie redirect); use Europe PMC (`PMC11735405` for the Nature Genetics paper).
- `scancel -n` by name is safe for `tA_anello_*`; never cancel allocation 25833654.

## Read first
- `$R/scripts/trackA_anello_align.py` (`STAR_139_FALLBACK` block) and `src/viralscan/scripts/anello_align.py` (`_run_star`).
- `.living/learnings.md`, heading "2026-10-20 — STAR 2.7.11b segfaults in Solo ...".
- `analysis/trackA_report_2026-10-18/recovery_2026-10-19/` — Codex recovery receipts (`zero_recovery_receipts/`, `late_zero_retry_plan.json`, `ebcd_cohort_launch.json`).
- `HANDOFF_trackA_2026-10-19.md`, `HANDOFF_pending_approvals_2026-10-19.md`.

## Open items
- No anello evidence yet: hhv6b/ebv/hnscc libraries align 0 reads; hsv1 relaxed has 22 low-complexity reads and 0 candidates. v3 plant gates: STAR exact@100 fails (best 0.846), candidates pass — return when the hsv1 reruns finish.
- hnscc second wave (about 49 pairs) — after hsv1 results.
- Codex thread: 5 of 9 molecule replays still to pass; EBCD cohort running; STAR zero-only receipts 3 of 29.
- From the earlier handoff: NORM-SHIFT-01 PR (user pushes), scAutoQC decisions (legacy filter, scoring before cell calling), g3-signing (user signs), `tchem` and `virus-taxonomy` rebase+PR, vignettes on real data, old remote branches to delete, production CPU-budget qualification.
- Doc nits not fixed: `docs/reference_panel.md` repeats `viralscan data fetch` and says `--anellovirus` where `build-ref` uses `--reference-panel anellovirus`; mycelium-extra "Python 3.9" mentions may be stale.
