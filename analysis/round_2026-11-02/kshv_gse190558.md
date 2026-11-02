# KSHV GSE190558 (RUN-04, PROG-16), round 2026-11-02

Status 2026-11-02: jobs submitted, not finished. de55424 numbers are pending; the round-2 numbers
below (pin e7c1b08, 2026-10-13/14) are the baseline and are labelled as such. Exploratory, unscored.

## Setup

- Package pin: `v3.0.0rc1-164-gde55424` (worktree `ViralScan/.claude/worktrees/pin-kshv`, clean). Env `viralscan_test_full`.
- Reference: cat42d (`data/references/panel_builds/viral_ref_cat42d/build`, virus-only `build_virus_only`), STAR host `data/references/starsolo/ebv_latest_ref_2026-09-27/star_host_2.7.11b`.
- Inputs (read only): lane-concatenated GSM FASTQs `data/runs/work/dsr_round1/inputs/<GSM>/<GSM>_R{1,2}.fastq.gz`, the round-1/2 inputs, so the arms compare with round 2. Source SRRs under `data/inputs/benchmark_inputs/dsr_2026-10-05/GSE190558/SRR17180386-401` all present with `DONE`. Lane map (runbook 12a): GSM5725695 latent = SRR17180398-401; GSM5725696 lytic = 394-397; GSM5725697 lytic + casp-i = 390-393; GSM5725698 lytic + casp-i + anti-IFN = 386-389.
- Chemistry: frozen round-1 `check-chemistry` JSONs, copied to `data/runs/round_2026-11-02/_kshv/chem/`: 10xv3 (95.7-96.4 % on-list), strand forward. Not re-measured.
- Arms per library: `combined_off`, `combined_artefact` (`--read-filter artefact`), `twostep` (`--host-filter starsolo`, virus-only index). All with `--cell-calling emptydrops --anellovirus-gene-ids`. Gene programmes are on by default at this pin (`gene_program_summary.tsv`).
- DSR-02 read validation: chained job, see below.
- Outputs: `data/runs/round_2026-11-02/GSE190558/<GSM>/<arm>/` (run metadata and `time.txt` in `meta_<arm>/`). Logs `data/runs/round_2026-11-02/_kshv/logs/`.

## Commands and jobs

Scripts: `scripts/slurm_kshv_round_2026-11-02.sh` (ARM=...), `scripts/slurm_kshv_dsr02_chain.sh`, `scripts/slurm_kshv_dsr02_row.sh`. Manifest `config/kshv_round_2026-11-02.manifest.tsv` (rows 0-3 are this dataset).

| Job | Arm | Rows | Resources |
|---|---|---|---|
| 25941227 | combined_off | 0-3 %3 | 4 cpu, 32G, 12 h |
| 25941230 | combined_artefact | 0-3 %3 | 4 cpu, 32G, 24 h |
| 25941254 | twostep | 0-4 %3 (0-3 here) | 8 cpu, 64G, 24 h |
| 25941255 | dsr02 chain (afterany of all arrays) | enumerates calls, submits the evidence array | 1 cpu |

Smoke tests (500 k pairs of GSM5725695, output under `_kshv/smoke/`, not results): jobs 25941195 (combined, artefact) and 25941226 (twostep). They passed CLI parsing, chemistry check, read filter, STARsolo and kb count; the artefact smoke ended at emptyDrops ("insufficient unique points"), expected on 500 k reads.
No explore-ledger append this round: de55424 has no `scripts/explore_ledger.py`.

## Outcome per library and arm (de55424)

| GSM | condition | combined_off | combined_artefact | twostep | DSR-02 |
|---|---|---|---|---|---|
| GSM5725695 | latent | pending (25941227_0) | pending (25941230_0) | pending (25941254_0) | pending |
| GSM5725696 | lytic | pending (_1) | pending (_1) | pending (_1) | pending |
| GSM5725697 | lytic + casp-i | pending (_2) | pending (_2) | pending (_2) | pending |
| GSM5725698 | lytic + casp-i + anti-IFN | pending (_3) | pending (_3) | pending (_3) | pending |

Collect (after the jobs end):

    sacct -j 25941227,25941230,25941254,25941255 -P -o JobID,JobName,State,Elapsed,MaxRSS,ExitCode
    python3 -I scripts/kshv_round_collect.py new data/runs/round_2026-11-02 > analysis/round_2026-11-02/kshv_summary.tsv

## Baseline: round 2 (e7c1b08), KSHV rows

Source: `data/runs/work/dsr_round2/runs/kshv_gse190558/<arm>/<GSM>/<GSM>/results/viral_summary.tsv` via `scripts/kshv_round_collect.py round2`.

| GSM | arm | KSHV molecules | called cells | infected called | % called infected |
|---|---|---|---|---|---|
| GSM5725695 latent | combined_off | 59,365 | 5,687 | 3,085 | 54.2 |
| GSM5725695 latent | combined_artefact | 59,361 | 5,690 | 3,085 | 54.2 |
| GSM5725695 latent | twostep | 59,506 | 5,587 | 3,021 | 54.1 |
| GSM5725696 lytic | combined_off | 23,671,063 | 8,220 | 8,219 | 99.99 |
| GSM5725696 lytic | combined_artefact | 23,670,509 | 8,224 | 8,223 | 99.99 |
| GSM5725696 lytic | twostep | 23,717,600 | 7,748 | 7,638 | 98.6 |
| GSM5725697 lytic + casp-i | combined_off | 23,545,060 | 6,925 | 6,921 | 99.9 |
| GSM5725697 lytic + casp-i | twostep | 23,600,287 | 6,597 | 6,485 | 98.3 |
| GSM5725698 lytic + casp-i + anti-IFN | combined_off | 31,763,568 | 9,463 | 9,463 | 100 |
| GSM5725698 lytic + casp-i + anti-IFN | twostep | 31,822,240 | 8,940 | 8,813 | 98.6 |

Read: KSHV molecules are about 400x higher in the induced libraries than in the latent one, and all three arms agree to within 1 % on molecules. EBV shows 1 molecule in GSM5725697 (noise). Round 2 wrote no gene programme file, so the latent-gene half of the acceptance test (LANA/ORF73, vFLIP/ORF71, vCyclin/ORF72 in both conditions) is not yet shown; the de55424 runs add `gene_program_summary.tsv`.

## What this says for PROG-16 (lytic acceptance)

Partly met on round 2: induced > uninduced by molecule count, in every arm. Not yet shown: latent genes present in both conditions, and the programme-level (productive vs latent cell counts) contrast. The de55424 gene-programme tables settle this. GSE190558 is iSLK.219, a cell line with a high latent fraction, so "54 % of called cells infected" in the latent library needs the programme table before it is read as latent.
