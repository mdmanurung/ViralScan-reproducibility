# HOST-05: sensitivity cost of `--host-filter starsolo` (round 2026-11-02)

Status: **Part A measured; Part B submitted (Slurm 25941194, array 0-7, partition `all`), still PENDING on Priority when this note was written**. Package pin: `de55424`
(`v3.0.0rc1-164-gde55424`, worktree `ViralScan/.claude/worktrees/pin-host05`). Env `viralscan_test_full`.
Exploratory, n = 2 background libraries (Part A) and n = 1 library (Part B). No pass/fail threshold.

## Design

HOST-05 asks how many true viral fragments and molecules the STAR host filter removes. Two parts.

**Part A, already computed (DISC-12-HH, Slurm 25874010 and 25874011, 2026-10-24).** Real HHV-6B and EBV read
pairs (drawn from alignment BAMs of their source libraries) are spiked into two other real 10x libraries
(D03 = SRR29320037, 10xv2; R01 = R01_SOC4, 10xv3). Only the product's filter runs on the result
(`host_filter._starsolo_filter`, both `pinned` and `star-default`), then `lost_truth_counts` (D15 fragments, D16
molecules) against `fragment_lineage.tsv.gz`. Two pools: `default` (ordinary pool, 30 conditions) and
`outside_truth` (the host-homologous / EVE-like reads that also align to HOST or another virus, `--max-nh 20`).
Source code at the run: repro `vs_work/disc12-hosthomolog` at package `720b466`. Between `720b466` and the
`de55424` pin, `host_filter.py` changed only by an import rename (`_open_maybe_gzip` to `open_maybe_gzip`); the
filter and `lost_truth_counts` are unchanged, so the numbers transfer to the pin.

**Part B, new (this round).** Native `viralscan` end to end on the real EBV library SRR12682296 (10xv2, forward,
first 50 M read pairs) with the round-2c SENS-07 plant (7,770 exact planted reads, 21 conditions; 3 levels x 7 genomes;
read-only reuse of `data/runs/work/dsr_round2c/runs/ebv/sens07/SRR12682296/plant`) and its unplanted twin. Three arms on
each: `--host-filter none`, and `--host-filter starsolo` with `--host-filter-star-params pinned` and `star-default`,
all on the same virus-only kb index (`viral_ref_cat42d/build_virus_only`), same flags, so arms differ only by the
filter. Host index: `references/starsolo/ebv_latest_ref_2026-09-27/star_host_2.7.11b` (the same index Part A used).
Outputs: `viralscan host-loss` on the planted starsolo runs (truth read ids against the run's own lineage),
and SENS-07 `score` (planted minus twin) per arm. HHV-6B SRR20710641 (R1 150 nt, not plantable without a trim,
a user decision) runs unplanted, `none` vs `pinned`, to compare endogenous viral molecules.

## Part A results (DISC-12-HH, collected 2026-11-02)

Script: `scripts/host05_hh_aggregate.py`; Wilson 95% intervals. Fragments/molecules are summed over
5 levels x 3 seeds, each condition drawing from the same source pool, so draws repeat across conditions
(the interval treats them as independent, which is optimistic).

| pool | background (source) | STAR params | conditions | fragments | removed | molecules | lost | not in lineage | fragment loss (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| default | D03 (HHV-6B) | pinned | 15 | 1329 | 0 | 1329 | 0 | 0 | 0 [0, 0.29%] |
| default | D03 (HHV-6B) | star-default | 15 | 1329 | 0 | 1329 | 0 | 0 | 0 [0, 0.29%] |
| default | R01 (EBV) | pinned | 15 | 1329 | 0 | 1329 | 0 | 0 | 0 [0, 0.29%] |
| default | R01 (EBV) | star-default | 15 | 1329 | 0 | 1329 | 0 | 0 | 0 [0, 0.29%] |
| outside_truth | D03 (HHV-6B) | pinned | 8 of 15 | 99 | 0 | 99 | 0 | 0 | 0 [0, 3.7%] |
| outside_truth | D03 (HHV-6B) | star-default | 8 of 15 | 99 | 0 | 99 | 0 | 0 | 0 [0, 3.7%] |
| outside_truth | R01 (EBV) | both | not submitted | n/a | n/a | n/a | n/a | n/a | not estimable (pool empty) |

- `outside_truth` rows 8 and 10-15 (HHV-6B levels 30 seed 2 and 100/300) failed in `spikein.py spike`: the host-homologous
  pool holds 22-31 reads, too few to draw 30+ distinct fragments. Recorded as n/a, not retried (loud failure is the design).
  The EBV `outside_truth` pool is empty (no host-competing EBV reads in the raw realignment, PLAN DISC-12-HH, 25872923).
- Both source BAMs hold host-unmapped reads only, so every number here is a **lower bound** on the loss.

## Part B jobs and collect command

Slurm array 25941194 (`scripts/host05_run_arm.sh`, `-p all -c 8 --mem=64G -t 12:00:00 --array=0-7`), logs in
`data/runs/round_2026-11-02/host05/logs/`. Task to arm: 0 ebv_planted_none, 1 ebv_planted_pinned, 2 ebv_planted_star-default,
3-5 the same on ebv_unplanted, 6 hhv6b_none, 7 hhv6b_pinned. Run dirs `data/runs/round_2026-11-02/host05/<arm>/{run,meta}`.
Expected 1.5-2.5 h per task (round-1 twostep: 1h21 EBV, 2h08 HHV-6B at 4 cores).

After tasks 0-5 finish, from the repro checkout:

    PYTHONPATH=<ViralScan>/.claude/worktrees/pin-host05/src \
      <conda>/envs/viralscan_test_full/bin/python scripts/host05_collect.py

It writes `host05/summary/host_loss.tsv` (D15/D16 with Wilson CIs, `not_in_lineage`) and `host05/score_{none,pinned,star-default}/`
(SENS-07 capture per family). Endogenous molecules for EBV (unplanted arms) and HHV-6B (tasks 6-7) come from each run's
`<run>/<sample>/results/viral_summary.tsv`. Part B results are **not yet measured**.

## Reading so far

Across 2,658 real viral fragments per STAR parameter set (two backgrounds) the filter removed none; upper 95% bound 0.29%.
On the 99 host-homologous HHV-6B fragments it removed none; upper bound 3.7%. This is a lower bound on the cost (source
reads are host-unmapped by construction) and does not close HOST-05, which also needs the Part B end-to-end arms, the
phase-6 EBV acceptance and CMP-01..03.

## Recommendation for the package side (not done here)

Do not change `docs/cli_reference.md` or `docs/output_reference.md` yet: those "unmeasured" lines are on the DOC-10
allow-list and need a registered claim first. Once Part B lands, register D15/D16 in `claims/` and then reword both docs
and the package PLAN HOST-05 row in one change.
