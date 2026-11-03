# CAT-08: leave-fold-out confusability of the shipped panel (2026-11-02)

Result: held-out genomes mostly do not pseudoalign at all (31.4 % of 388,740 reads map), and the reads that do map land on the right genus far more often than on the wrong family. Row stays open: the native `build-ref` HPV-11 run failed (below).

Package pin `de55424`; kb kallisto 0.52.0; panel `viral_ref_wp5/build_7e5a2ce/viral.fa` (sha256 `38c67d4c...0b335`, 2,414 genomes).

## Method (job 25941238, COMPLETED in 7 min)

`scripts/cat08_loo_confusability.sbatch` runs `scripts/cat08_loo_confusability.py`. Genomes are held out in 20 folds stratified by family (seed 20261102). Each fold gets a virus-only index (`kallisto index -k 31`) without its held-out genomes. 90 bp error-free reads are tiled every 30 bp from the held-out genomes (random strand) and pseudoaligned with `kallisto quant --pseudobam`. A read is `same_species`, `same_genus`, `same_family` or `other_family` by the widest rank at which all its compatible targets agree with the source; otherwise `unmapped`.

Not a native `viralscan build-ref` build: that needs a host cDNA and `kb ref` per fold. The 7 min runtime is plausible: each index holds about 12 Mb of virus and each fold has about 19k reads.

Validation: all 20 folds present (117-124 genomes each), `per_genome.tsv` has 2,414 rows, `per_family.tsv` has 30 families, reads 388,740, unmapped 266,595.
Output: `data/runs/round_2026-11-02/cat08_cat40/loo/{per_genome,per_family,cross_family}.tsv`, `run_info.json`.

## Numbers (P(captured) = fraction of held-out reads that pseudoalign)

| Family | genomes | P(captured) | same species | same genus | same family | other family |
|---|---|---|---|---|---|---|
| Anelloviridae | 2041 | 0.368 | 0.238 | 0.029 | 0.101 | 0 |
| Papillomaviridae | 110 | 0.167 | 0 | 0.1665 | 0.0002 | 0.0001 |
| Orthoherpesviridae | 11 | 0.281 | 0 | 0.2805 | 0 | 0.0001 |
| Poxviridae | 7 | 0.473 | 0 | 0.471 | 0.002 | 0.0002 |
| Hepadnaviridae | 8 | 0.471 | 0 | 0.471 | 0 | 0 |
| Polyomaviridae | 15 | 0.145 | 0 | 0.142 | 0.003 | 0 |

Families with P(captured) = 0: Arenaviridae, Astroviridae, Caliciviridae, Filoviridae, Matonaviridae, Nairoviridae, Orthomyxoviridae, Peribunyaviridae, Retroviridae, Rhabdoviridae, Sedoreoviridae. Full table: `loo/per_family.tsv`.

- **Cross-family landing is rare**: 18 reads in total (`cross_family.tsv`): Poxviridae and Orthoherpesviridae reads onto Papillomaviridae (7 each), Papillomaviridae reads onto Orthoherpesviridae (3) and Poxviridae (1).
- **HPV (the valid HPV-11 test, in-panel)**: 0 of 110 types land on another family's genome beyond those few reads; reads land on other alpha/beta types. HPV-11 (`NC_075235.1`): 46 of 262 reads (17.6 %) map, all `same_genus`; top landing HPV-6b (`NC_001355.1`, 36 reads). HPV-type median P(captured) 0.148 (range 0 to 0.43).
- **Anello**: genus-level P(captured) is lowest for Gyrovirus (0.083, 6 genomes) and highest for Alphatorquevirus (0.499, 45 genomes). Betatorquevirus (1,368 genomes) 0.343. Many genomes carry blank catalogue genera (593 genus labels in the table), so a per-genus read-out needs the genus map fixed first.

Caveats: (1) 5 % of each family is held out at once, so a family with close pairs sees slightly fewer neighbours than true leave-one-out. (2) The single `Herpesviridae` genome lands 94.7 % `same_genus`, which means catalogue genus labels are shared across `Herpesviridae` and `Orthoherpesviridae`; a catalogue inconsistency, not a real result. (3) Error-free reads only; no host competition (the host-aware check is the failed run below). (4) HPV16 lineage variants are not covered (needs an NCBI fetch).

## HPV-11 native run (job 25941241, FAILED after 1.5 min)

`viralscan build-ref --host human --ensembl-release 116 --virus-accessions <109 HPV>` (package de55424) stopped before `kb ref` with:
`ERROR  Reference build failed: Exact duplicate sequences before index construction: ENST00000604066.1 and ENST00000630556.1`
Both IDs are Ensembl human transcripts. The exact-duplicate gate (`build_reference.py:_check_reference_structure`, called on the combined host+virus FASTA at the pre-index validation) rejects the unmodified Ensembl 116 cDNA. This is package behaviour, not the sbatch script. Log: `data/runs/round_2026-11-02/cat08_cat40/logs/cat08_hpv11_25941241.log`. Partial output (not reusable): `.../hpv11_native/`.
