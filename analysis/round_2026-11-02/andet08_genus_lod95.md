# ANDET-08: genus-level LOD95 for held-out anelloviruses (2026-11-02, exploratory, pre-G3, one library)

Status: measured, but the row's gate is not met, so `ANDET-08` stays `[~]`.
- The unplanted background is not call-free: the twin run reports one Gammatorquevirus molecule in one cell (`detected = True`, `low_complexity`, `screening_only`).
  Real anellovirus is plausible in healthy blood; the scorer subtracts the twin, but the row says "no reported call".
- Hetorquevirus has no held-out genome below 95 % identity; the genus-less `Anelloviridae` bucket is mostly undetectable (see below).
- One library, 12 M read pairs, not VAL-04 (the VAL-04 holdout H01 is untouched, `block_study_use`). No VAL-01 or G3 claim.

## Result (primary: pooled probit per genus, genome = resampling unit, response = net >= 1 molecule vs unplanted twin)

LOD95 is in planted molecules per condition (spread over 5 cells). `bracket` is the model-free fallback of `v3_lod.lod_bracket`.
BCa interval: 2000 replicates, seed 20261102; "not estimable" follows v3_lod's rules (a failed bootstrap fit anywhere blocks the interval).

| genus group | n genomes (<95 % identity) | status | LOD95 (molecules) | BCa 95 % | bracket |
|---|---|---|---|---|---|
| Alphatorquevirus | 15 | ok | 9.9 | 5.4-19.5 | |
| Betatorquevirus | 15 | ok | 20.7 | not estimable (failed-fit) | 20-50 |
| Gammatorquevirus | 15 | ok | 694 | not estimable (lod-not-reached) | above 3000 |
| Gyrovirus | 5 | not_reached | | not estimable | above 3000 |
| Samektorquevirus | 4 | ok | 46.1 | not estimable (failed-fit) | 20-50 |
| Hetorquevirus | 0 | no held-out genome below 95 % | | | |
| Memtorquevirus | 6 | ok | 42.8 | not estimable (failed-fit) | 20-50 |
| Anelloviridae (genus-less bucket) | 5 | not_reached | | not estimable | above 3000 |

Levels: 1, 2, 5, 10, 20, 50, 100, 300, 1000, 3000 molecules (10 levels, bracketing the knee for Alpha, Beta, Mem, Samek). Gamma, Gyro and the bucket never reach 95 %
because some held-out genomes are never detected, not because the knee is high.

Why the plateau: capture is a property of each genome's distance to the panel. Genomes with no alignment to the panel (identity under about 80 %) recover 0 to 14 % at 3000 molecules
(4 of 5 genus-less genomes and 2 of 5 Gyrovirus genomes recover none). Pooling them with well-captured genomes caps the detected fraction below 95 %.
`per_genome.tsv` lists each genome's capture (levels 1000 and 3000 pooled) and Poisson LOD95 (3 / capture).

Secondary strata (post hoc, exploratory, labelled as such in `lod95_by_genus.tsv`):
- Genomes detected at the top level only (`identity<95_detectable_only`): Gamma 99 molecules (BCa 41-277, n = 14), Gyro 308 (bracket 50-100 by level; n = 3), the other genera unchanged.
  This conditions on the outcome, so it is a description, not an LOD for the genus.
- Held-out genomes at >= 95 % nearest identity (set H, 5 per genus, all genera but Mem): Alpha 22.8, Beta 7.8, Gamma 36.6, genus-less 3.0, Hetor bracket 1-2 (quasi-separation), Gyro and Samek no variation (detected at 1 molecule); no BCa interval for any.
- Secondary response `net_genus` (counts only in the planted genus's own gene group) and a stricter threshold of 3 molecules are in `lod95_by_genus.tsv`; genus-correct assignment is clearly worse than family-level detection
  (e.g. the genus-less bucket gets no genus-correct molecule at all, as expected since that bucket has no taxon).

Median per-genome capture at 1000-3000 molecules and detectable genomes (<95 % identity; set H in the second column):

| genus group | n, detectable | median capture | median Poisson LOD95 | set H: n, median capture |
|---|---|---|---|---|
| Alphatorquevirus | 15, 15 | 0.56 | 5.3 | 5, 0.55 |
| Betatorquevirus | 15, 15 | 0.34 | 9.0 | 5, 0.61 |
| Gammatorquevirus | 15, 14 | 0.10 | 30.6 | 5, 0.09 |
| Gyrovirus | 5, 3 | 0.03 | 3.9 | 5, 0.95 |
| Samektorquevirus | 4, 4 | 0.31 | 101.7 | 2, 0.95 |
| Hetorquevirus | 0 | | | 5, 1.00 |
| Memtorquevirus | 6, 6 | 0.04 | 71.9 | 0 |
| Anelloviridae bucket | 5, 1 | 0.00 | | 5, 0.61 |

Gamma is low even at >= 95 % identity (median capture 0.09), which the nearest-identity number does not predict; see `fig_capture_vs_identity.png`.
Memtorquevirus and Samektorquevirus have the lowest capture at a given identity too. A coverage-weighted identity (the planter's `identity x coverage` rule) is used for the nearest hit, so a partial alignment can read as a high identity.

Figures (each backs one conclusion):
- `andet08_genus_lod95/fig_detection_curves.png`: detected fraction per planted level by genus, the probit fit and the LOD95 marker (blue < 95 %, orange >= 95 %).
- `andet08_genus_lod95/fig_capture_vs_identity.png`: per-genome capture against nearest-panel identity with the exact DP curve (divergence = 1 - identity). Held-out genomes scatter around the DP, with Gamma/Mem below it and no-alignment genomes at the floor.

## Design

- Index: cat42d panel + host (`panel.idx`, 2,040 Anelloviridae accessions; 1,994 live in the identity table). Package code de55424.
- Background: CAL-08 `10k_PBMC_3p_nextgem_Chromium_X` (10x public 3' v3.1, Chromium X, healthy PBMC), lane L001, first 12,000,000 read pairs,
  streamed from the pinned tar (sha256 `3c4fdead...1867a`) into `data/runs/round_2026-11-02/sens/background/local_R{1,2}.fastq.gz` (R1 28 nt, R2 90 nt; sha256 in `background/SHA256SUMS`).
  Substitution: the row names a VAL-04 background, but VAL-04 H01 (`pbmc_10x_healthy_v3`) is a `block_study_use` external-evaluation holdout and is not downloaded.
  CAL-08 is the registered calibration background (conditional eligibility: donor independence unresolved). Governance: this adds an outcome-generating run on a CAL-08 library
  (anellovirus molecule counts); the protocol's `pre_freeze_runs` inventory needs a line for it (the user's call; not edited here).
- Held-out genomes (`scripts/andet08_heldout_set.py`, seed 20261102): not in the panel by accession and by minimap2 identity band (`asm20`, panel = the 2,040 Anelloviridae sequences of cat42d `viral.fa`).
  Sources: Modha et al. TPA genomes (829, BK068993-BK069821; genus from the record's SOURCE line, an alpha/beta/gamma/samek/mem/he assignment, not an ICTV re-call) plus NCBI nuccore complete genomes
  (1500-4500 nt) for Gyrovirus (60 sampled of 863), Hetor-, Samektor-, Memtorquevirus (all), SEN virus and `Anelloviridae sp.` (80 sampled; the genus-less bucket). NCBI fetch by the package's `ncbi_fetch` code, generic contact string.
  Primary sets A, B, C: nearest-panel identity < 95 % (VAL-RA-DECISION-01's ANI cut; includes "no alignment"), disjoint random draws of up to 5 per genus per set.
  Contrast set H: >= 95 %, up to 5 per genus.
- "Eight genera" = the eight `virus_key` groups of the panel's identity table: seven named genera plus `genus:Anelloviridae` (the genus-unresolved bucket, which also holds SEN virus).
  This matches "8 anellovirus groups" in the cat42b probe note. The bucket has no taxon to hold out, so its held-out set is NCBI records NCBI itself leaves without a genus; read it as "unclassified Anelloviridae".
- Planting: `sens07 plant`, held-out mode, 5 cells per condition, levels above, sense CDS transcripts of the held-out genome (`heldout_cdna.fa`, from the record's CDS features, own strand), library strand forward,
  per-run seeds 20261102 + {0,1,2,3} for A, B, C, H, 12 M background pairs, top-count barcodes as cells. Unplanted twin = the background itself (`runs_v3/twin`), byte-identical to every planted run's twin.
- viralscan: `viralscan run --cell-calling emptydrops --anellovirus-gene-ids --strand forward`, 10xv3; scoring layer `adata_multimap.h5ad` X.
- Scoring: `scripts/andet08_genus_lod95.py`: per condition, molecules in the block's cells on Anelloviridae genes, net of the twin; detected = net >= 1. Probit = `scripts/v3_lod.py` (SCI-03 method), one fit per genus, genome as unit.
- Choices where the row left room (conservative option taken): background = CAL-08 not VAL-04; held-out below 95 % identity for the primary result; identity measured against the whole Anelloviridae panel;
  CDS-only reads (what the index holds, so UTR-only reads are not tested); one library, so E8's "several libraries" is not met.

## Not done / limits

- The row's "unplanted background must yield no reported call" fails (1 Gamma molecule). 3' poly-A end reads are not planted (internal CDS fragments only).
- No probit across libraries; n = 1 background. Hetorquevirus below 95 % and a real genus-less held-out taxon do not exist in the pools used (Het: 11 NCBI + 1 Modha genomes, all >= 95 %).
- Cell-calling is not part of detection (unfiltered counts); a viralscan "called" status would be stricter. Per-genome results are Poisson-noisy at low levels (one replicate per genome-level).

## Reproduce

    PYTHONPATH=<pkg>/src python scripts/andet08_heldout_set.py --out-dir <sens>/heldout_sets      # needs network; seed 20261102
    bash scripts/slurm_andet08_run.sh    # SET=twin|A|B|C|H SEEDOFF=0|0|1|2|3 ; plant + viralscan; 4 h, 8 cpus, 64 G (cluster 'all' partition; medium is capped at 4 cpus per user)
    PYTHONPATH=<pkg>/src python scripts/andet08_genus_lod95.py --root <sens> --out-dir <new dir>

Job IDs: B 25941595, C 25941596, H 25941597 (cluster, `andet08v3_*`, ~55 min plant + ~20 min run). A and the twin ran locally (4 threads). All calibration runs were local.
Earlier submissions 25941286, 25941304-8, 25941319-28, 25941540-45 used flags that no longer exist (`-s1`, `-w` list mismatch) and only exit at their mkdir; placeholders sit in `runs/`, `runs_v2/`, `calibration/runs*/`.
Data: `data/runs/round_2026-11-02/sens/{background,heldout_sets,runs_v3,calibration}`; logs `logs/`.
Package SHA: de55424. Seeds: held-out draw and NCBI subsample 20261102; plant 20261102..20261105; bootstrap 20261102.
