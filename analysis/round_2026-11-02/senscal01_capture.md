# SENS-CAL-01: measured capture versus iid divergence (2026-11-02, exploratory, training only)

Status: iid-substitution arm done; clustered arm and held-out natural-divergence transfer not done. Row stays `[~]`.
One background library, one index (cat42d), no pass/fail threshold, not scored on any holdout.

## Result

Measured capture follows the exact substitution DP (`fragment_capture_exact`, k = 31) to within about 1 point at every divergence.
One effective-length parameter fits at L_eff = 88 (planted R2 is 90 nt). The DP at L = 90 is already close; the fit trims 2 nt.
Capture at 0 % divergence is 1.000, so the DP's blind spot (panel/host competition) did not show for unique viral sequence.
The Luebbert et al. 2025 reading (about 55 % at 4.4 % divergence, EBOV) is not reproduced: here the curve gives about 0.76 at 4.4 %.

| divergence | planted | recovered | capture | Wilson 95 % | DP L=90 | DP L=88 |
|---|---|---|---|---|---|---|
| 0 | 12000 | 12000 | 1.0000 | 0.9997-1.0000 | 1.0000 | 1.0000 |
| 0.01 | 12000 | 11885 | 0.9904 | 0.9885-0.9920 | 0.9939 | 0.9929 |
| 0.02 | 12000 | 11501 | 0.9584 | 0.9547-0.9618 | 0.9621 | 0.9582 |
| 0.03 | 12000 | 10719 | 0.8933 | 0.8876-0.8986 | 0.8989 | 0.8919 |
| 0.05 | 12000 | 8477 | 0.7064 | 0.6982-0.7145 | 0.7079 | 0.6972 |
| 0.075 | 12000 | 5319 | 0.4432 | 0.4344-0.4522 | 0.4503 | 0.4405 |
| 0.10 | 12000 | 2975 | 0.2479 | 0.2403-0.2557 | 0.2537 | 0.2471 |
| 0.125 | 12000 | 1486 | 0.1238 | 0.1181-0.1298 | 0.1310 | 0.1273 |
| 0.15 | 12000 | 750 | 0.0625 | 0.0583-0.0670 | 0.0634 | 0.0615 |

Fit (`senscal01_capture2/fit.json`): binomial likelihood over the nine pooled points, integer L from 31 to 150. Best L_eff = 88.
Log-likelihood at L = 90 is 11.9 lower (LRT 23.7), so the 2-nt trim is statistically detectable.
The 95 % profile interval collapses to the single grid value 88. It is too narrow: it treats 108,000 molecules as independent
and ignores genome-to-genome spread (3 genomes per family; per-family curves overlap within about 3 points).
A two-parameter variant (free ceiling c0) returns c0 = 1.0, L_eff = 88: no ceiling below 1.

Figure: `senscal01_capture2/fig_capture_vs_divergence.png` (pooled points, per-family lines, both DP curves, the Luebbert reading).

## Design

- Fragments: R2 reads (90 nt) drawn uniformly from the indexed CDS transcripts of exact panel genomes (`--transcripts-fasta cdna.fa`, sense strand,
  library strand forward), then iid substitutions at rate d on the read (`sens07 plant --error-rate d`, the planter's `mutate`).
- Genomes: 3 per family from Papillomaviridae, Polyomaviridae, Orthoherpesviridae, Anelloviridae (selection seed 20261102, same seed for every d,
  so the same genomes), 1000 molecules each, 20 cells per condition. Families list: genomes of `viral.fa` that have a transcript in `cdna.fa`.
- Background: first 3,000,000 read pairs of the CAL-08 10k PBMC 3' library (see ANDET-08 note for provenance), unplanted twin run once.
- Run: `viralscan run` at package de55424 against the cat42d panel + host index, `--cell-calling emptydrops --anellovirus-gene-ids --strand forward`,
  10xv3 chemistry check passed (95.2 % on the list). Scoring: `sens07` `score` logic, molecules of the planted family in the condition's cells,
  `adata_multimap.h5ad` layer X, minus the twin, detection threshold 1.
- Grid: 0, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.125, 0.15.
- Choices where the row left room: held-out = panel genomes of families outside any VAL holdout (no protocol holdout virus list exists yet; the VAL-04
  holdout H01 is a PBMC library, untouched); the effective-length fit uses integer L with the DP as written (no interpolation).

## Not done

- Clustered substitutions (the row's second step): the planter's `mutate` is iid only. Needs a clustered mutator; deferred.
- Real held-out viruses at natural divergence: the ANDET-08 plants give this. Measured capture against nearest-panel identity is in
  `andet08_genus_lod95.md` (identity is a proxy for divergence; divergence there is not iid). Spread around the DP is large.
- Not the frozen WP5 index (cat42d); indels and sequencing error are not modelled; one library.

## Reproduce

Package code `de55424` (worktree `ViralScan/.claude/worktrees/pin-sens`), env `conda/envs/viralscan_test_full`.

    bash scripts/slurm_senscal01_run.sh          # SET=twin, then SET=d<DIV> DIV=<DIV> per grid value; local, 4 threads, ~15 min each
    PYTHONPATH=<pkg>/src python scripts/senscal01_capture.py --root <sens dir> --out-dir <new dir>

Outputs: `data/runs/round_2026-11-02/sens/calibration/runs_v3/{twin,d0,...,d0.15}` (plants, kb counts, viralscan results).
Seeds: plant 20261102 for every divergence run. No other random step.
Run notes: the calibration jobs were run locally (login node, 4 threads) because the queue held the cluster jobs for over an hour.
Cluster copies (25941319-25941328) were submitted first with a removed CLI flag (`-s1`/`-s2`), so they exit at once; their output dir
names (`calibration/runs/`, `calibration/runs_v2/`) hold only empty placeholders and one stray plant (`runs/d0`). The results are in `runs_v3`.
