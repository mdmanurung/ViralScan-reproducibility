# KSHV + EBV GSE154900 (RUN-05, PROG-18), round 2026-11-02

Status 2026-11-02: jobs submitted, not finished. de55424 numbers pending; round-2 numbers (e7c1b08) are the labelled baseline. Exploratory, unscored.

## Setup

- Package pin `v3.0.0rc1-164-gde55424`, env `viralscan_test_full`, cat42d reference, same arms and flags as `kshv_gse190558.md`.
- Inputs (read only): source SRR12287751-754 present under `data/inputs/benchmark_inputs/dsr_2026-10-05/GSE154900/`. Runs use the lane-concatenated `data/runs/work/dsr_round1/inputs/GSM4682311/GSM4682311_R{1,2}.fastq.gz` (660,519,688 pairs, full depth, no read cap; the runbook's "75M spots/SRR" subsample is not applied), as in round 2.
- GSM4682311 chemistry: frozen JSON says 10xv2 with `check-chemistry` unresolved (barcodes 94.9 % on the v2 list, R1 28 bp implies 12 bp UMI, not 10). Run with `-x 10xv2 --force-technology --strand forward`, as in round 2 (user 2026-10-06).
- GSM4682312 (BC-1 rep 2): `n/a: public FASTQ has no barcode read`. `check-chemistry` calls it bulk (barcode repeat 0.24, continuation 0.85, on-list 0.2 %, R1 101 bp). Evidence: `data/runs/round_2026-11-02/_kshv/chem/GSM4682312.json`. Not run in any arm.
- No explore-ledger append (no `scripts/explore_ledger.py` at de55424).
- Outputs: `data/runs/round_2026-11-02/GSE154900/GSM4682311/<arm>/`.

## Jobs

| Job | Arm | Row | Resources |
|---|---|---|---|
| 25941228 | combined_off | 4 | 4 cpu, 64G, 24 h |
| 25941231 | combined_artefact | 4 | 4 cpu, 64G, 96 h |
| 25941254 | twostep | 4 (array task 4) | 8 cpu, 64G, 24 h |
| 25941255 | dsr02 chain | after all arrays | 1 cpu |

## Outcome per arm (de55424)

| GSM | combined_off | combined_artefact | twostep | DSR-02 |
|---|---|---|---|---|
| GSM4682311 | pending (25941228_4) | pending (25941231_4) | pending (25941254_4) | pending |
| GSM4682312 | n/a: no barcode read | n/a | n/a | n/a |

Collect: same two commands as in `kshv_gse190558.md` (add 25941228,25941231 to the `sacct -j` list).

## Baseline: round 2 (e7c1b08), GSM4682311

Source: `data/runs/work/dsr_round2/runs/kshv_ebv_gse154900/<arm>/GSM4682311/GSM4682311/results/viral_summary.tsv`.

| arm | virus | molecules | called cells | infected called | % called infected |
|---|---|---|---|---|---|
| combined_off | KSHV (Human herpesvirus 8) | 555,654 | 3,428 | 3,280 | 95.7 |
| combined_off | EBV | 1,652 | 3,428 | 942 | 27.5 |
| combined_off | EBV type 2 | 117 | 3,428 | 18 | 0.5 |
| combined_artefact | KSHV | 555,806 | 3,438 | 3,286 | 95.6 |
| combined_artefact | EBV | 1,653 | 3,438 | 943 | 27.4 |
| twostep | KSHV | 658,087 | 11,487 | 2,979 | 25.9 |
| twostep | EBV | 2,034 | 11,487 | 1,103 | 9.6 |

Caveats: the called-cell set differs by arm (3.4 k combined, 11.5 k twostep, which calls cells on the STARsolo host matrix), so percentages do not compare across the two; molecule counts do. Per-cell co-infection (a cell with both KSHV and EBV) is not in `viral_summary.tsv`; it needs `per_cell_viral.tsv` and is not reported here.

## What this says for PROG-18 (KSHV latent validation)

Detection part met on round 2: KSHV and EBV are both detected in the BC-1 library in all three arms. Not yet shown: "mostly latent, lytic minority". Round 2 wrote no programme table; the `rerun-programs` table gives latent/productive/mixed cell counts for both viruses. One library (n = 1; the second replicate cannot run) limits the claim. EBV is 0.3 % of KSHV molecules, so EBV latency calls may sit near the detection floor.

## Interim 2026-11-03 (de55424)

`combined_off` GSM4682311 COMPLETED (25941228_4, 3 h 17, 64G). `combined_artefact` (25941231_4) running (13 h 44 at last check). `twostep` row 4 (25941254_4) pending. No OOM here.
Gene programmes were off in the run; added with `rerun-programs` (job 25949108).

| arm | virus | molecules | called cells | scored | latent | productive | mixed | indeterminate |
|---|---|---|---|---|---|---|---|---|
| combined_off | KSHV | 555,654 | 3,426 | 3,205 | 3,172 | 0 | 5 | 28 |
| combined_off | EBV | 1,652 | 3,426 | 44 | 1 | 0 | 0 | 43 |

Counts reproduce round 2 (555,654 and 1,652.25). PROG-18 reading: KSHV is mostly latent (3,172 of 3,205 scored cells, 99 %), with a small mixed minority (5) and no productive cell. That matches the "mostly latent" expectation, with the caveat from `kshv_gse190558.md` that the productive rule gave 0 even in induced libraries. EBV: only 44 cells scored and 43 indeterminate, so the EBV programme is not informative here. Per-cell co-infection is still not computed.
