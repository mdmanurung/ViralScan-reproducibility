# Handoff — Track B exploratory pilot done; Track A + software extensions continue

**Date:** 2026-10-21 · **Root:** shared dirty checkout `codex/drop-py39` @ `5e551c9` (104 entries; never edit/stage/stash/reset it) · **Status:** Track B pilot finished (no virus); 7 local branches unpushed (user pushes); HHV-6B deletion HELD.
Previous handoff copied aside: `HANDOFF_prev_2026-10-21_trackA-extensions.md`.

## Goal
Finish Track A (HHV-6B/EBV verdicts, report), land the software branches, and decide next Track B cohorts. Done = branches merged, report final, verdicts settled, deletion decision made.

## Next action
Ask the user the 4 pilot decisions (below). Then `git -C /exports/archive/hg-funcgenom-research/mdmanurung/ViralScan fetch origin` and re-check which of the 7 branches are pushed.

## State
- Track B pilot report: `viralscan_work/trackB_explore_2026-10/REPORT_trackB_explore_pilot.md` (guard + decisions: `GUARD.md` same dir). D03 (2 libs) + R01 (2 libs): STAR 0-21 viral reads each; flank-index UMIs (10-43) are anello genes with zero STAR reads = not calls.
- Flank index v2: `viralscan_work/trackB_explore_2026-10/ref_flank_v2/panel_flank.idx` (passes gate: 2,809/2,849 vs 19; CAL-08 0→3 UMI). Extension script `scripts/extend_gtf.py` (gene-only rows extended; v1 buggy, kept as `extend_gtf_v1.py`).
- HHV-6B flank audit (GSM6416022): 28.27 M viral reads, 8.9% (2.5 M) in 3' flank; peak 125 kb = U84/U85 3' UTR. Table: `viralscan_work/star_hostvirus/flank_audit/GSM6416022_classes.tsv`. Verdict stays "scoped NEGATIVE" + caveat until user says otherwise.
- Unpushed branches (user pushes, order): `codex/shifted-log-normalization`, `codex/tchem-second-opinion`, `codex/virus-taxonomy-rollup`, `codex/cli-unify-02-hostresponse`, `codex/cli-unify-02-layout` (4d2ac67, stacked on hostresponse), `codex/spq-coverage-map-star` (db75432), `codex/hhv6b-3utr-strand-finding` (no commits yet; worktree `vs_work/hhv6b-finding`, write F-027 there).
- Jobs: `stablr2` 25833654 running; `ebcd_cont` 25854873 queued afterany it (no new allocation request needed); `tA_advance` 25851736 held. Arm P masked-index pilot (25856080-82) was queued by an agent; fix = plain nucleotide mask + kallisto >= 0.51.1.
- tchem installed (`tools/tchem_0.1.0`, env vars in `~/.bashrc`). Disk 93% (cap 95%).

## Locked decisions (user 2026-10-21)
- HHV-6B BUS deletion (130 paths, 1072.5 GB, dry run OK) HELD until Track A analysis done (audit + flank results in, verdict settled, report final); deletion for hsv1/hnscc/ebv/tonsil also held; keep `tA_advance` held.
- Exploratory override of discovery Q21/LOCK-01 A2 for D03/R01 (user must add the one-line note to ViralScan-discovery themselves; read-only repo). Those sets now count as "seen".
- No EBV scoped verdict until the flank audit runs on GSM4796271; EBV shared-contig signal (72% of NC_007605.1 records also map another VIRUS| contig) after the pilot.
- Skip GBCD; CLI-UNIFY-02 `--run-dir` = input, post-hoc outputs under `<run-dir>/posthoc/`; Kraken2 discovery deferred (DISC-07..14 unbuilt, no DB); Track A tonsil analysis was dropped 2026-10-18 (FASTQs deleted).

## Dead ends — do not redo
- Workflow agents as Slurm monitors: they end their turn instead of waiting (wf_38c85550 returned "not evaluated"). Use Monitor from the main session.
- Scripts reading the login node's `/tmp` scratchpad from sbatch jobs (compute nodes cannot see it; peak125 cross-contig output lost). Keep job inputs on shared storage.
- Compute-node `python3` is 3.6: use `conda/envs/viralscan_test_full/bin/python`.
- First flank index (extension of exon/transcript rows only) — HHV-6B genes are gene-only rows; do not reuse `ref_flank/` or `ref_flank_fast/`.

## Read first
- `viralscan_work/trackB_explore_2026-10/REPORT_trackB_explore_pilot.md` — pilot results and limits.
- `analysis/trackA_report_2026-10-18/REPORT_2026-10-19.md:344` — open Track A decisions.
- `.living/decisions.md` tail; `.mycelium/last-session.md`.

## Open items
- Pilot decisions for the user: (1) expand D03/R01 anyway? (rec: no); (2) next cohorts D02 / D04 or an autoimmune cohort (rec: D02, D04); (3) flank index as discovery default or retire; (4) read-check the HHV-7/HSV-1/HHV-5 reads?
- Run the flank audit on EBV GSM4796271; then F-027 finding note + Lareau comparison (his HHV-6B reference is CDS-only, `hhv6-reference/HHV6b_only.index.txt`, 103 `_cds_` entries).
- User tasks: push branches; add override note in ViralScan-discovery; `kill 2408964` (orphan snakemake); check `identity_sign` git key warning.
- Wave 2: scAutoQC rebase on shifted-log + tchem; research-tree PRs; quickstart vignette on Slurm; prune worktrees; re-pin inventory last.
