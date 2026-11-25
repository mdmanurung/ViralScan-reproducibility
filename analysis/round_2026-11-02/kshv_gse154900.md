# KSHV + EBV GSE154900 (RUN-05, PROG-18), round 2026-11-02

Status 2026-11-04: combined_off (25941228_4) and combined_artefact (25941231_4, 19 h 56) COMPLETED; twostep (25941254_4) PENDING on JobArrayTaskLimit with no task of its array running. Programme table at 5b419d4 exists for combined_off only. No DSR-02 job exists for this dataset: chain 25941255 would enumerate it and is PENDING behind 25941254_3-4. Round-2 numbers (e7c1b08) are the labelled baseline. Exploratory, unscored.

## Setup

- Package pin `v3.0.0rc1-164-gde55424`, env `viralscan_test_full`, cat42d reference, same arms and flags as `kshv_gse190558.md`.
- Inputs (read only): source SRR12287751-754 present under `data/inputs/benchmark_inputs/dsr_2026-10-05/GSE154900/`. Runs use the lane-concatenated `data/runs/work/dsr_round1/inputs/GSM4682311/GSM4682311_R{1,2}.fastq.gz` (660,519,688 pairs, full depth, no read cap; the runbook's "75M spots/SRR" subsample is not applied), as in round 2.
- GSM4682311 chemistry: frozen JSON says 10xv2 with `check-chemistry` unresolved (barcodes 94.9 % on the v2 list, R1 28 bp implies 12 bp UMI, not 10). Run with `-x 10xv2 --force-technology --strand forward`, as in round 2 (user 2026-10-06).
- GSM4682312 (BC-1 rep 2): `n/a: public FASTQ has no barcode read`. `check-chemistry` calls it bulk (barcode repeat 0.24, continuation 0.85, on-list 0.2 %, R1 101 bp). Evidence: `data/runs/round_2026-11-02/_kshv/chem/GSM4682312.json`. Not run in any arm.
- No explore-ledger append (no `scripts/explore_ledger.py` at de55424).
- Outputs: `data/runs/round_2026-11-02/GSE154900/GSM4682311/<arm>/`.

## Jobs

| Job | Arm | Row | Resources | State 2026-11-04 |
|---|---|---|---|---|
| 25941228 | combined_off | 4 | 4 cpu, 64G, 24 h | _4 COMPLETED (3 h 17) |
| 25941231 | combined_artefact | 4 | 4 cpu, 64G, 96 h | _4 COMPLETED (19 h 56) |
| 25941254 | twostep | 4 (array task 4) | 8 cpu, 64G, 24 h | _4 PENDING (JobArrayTaskLimit; no task of the array running) |
| 25941255 | dsr02 chain | after all arrays | 1 cpu | PENDING (Dependency) |
| 25949108, 25949495, 25950135 | \`rerun-programs\` | finished runs | 32-48G | COMPLETED; \`programs_5b419d4\` exists for combined_off only |

## Outcome per arm (de55424)
Source: \`data/runs/round_2026-11-02/GSE154900/GSM4682311/<arm>/GSM4682311/results/viral_summary.tsv\` (rows detected \`True\`); programmes from \`posthoc/programs_5b419d4/results/gene_program_summary.tsv\`.

| arm | virus | molecules | called cells | infected called (%) | programmes at 5b419d4: scored / productive / latent / mixed / indeterminate |
|---|---|---|---|---|---|
| combined_off | KSHV (Human herpesvirus 8) | 555,654 | 3,426 | 3,278 (95.68) | 3,265 / 0 / 2,889 / 288 / 88 |
| combined_off | EBV | 1,652.25 | 3,426 | 942 (27.50) | 44 / 0 / 1 / 0 / 43 |
| combined_off | EBV type 2 | 116.75 | 3,426 | 18 (0.53) | 0 scored |
| combined_artefact | KSHV | 555,806 | 3,421 | 3,277 (95.79) | programmes not run |
| combined_artefact | EBV | 1,653.25 | 3,421 | 943 (27.57) | programmes not run |
| combined_artefact | EBV type 2 | 116.75 | 3,421 | 18 (0.53) | programmes not run |
| twostep | | pending (25941254_4) | | | |

GSM4682312: n/a, no barcode read. Other calls with >= 3 molecules: Samektorquevirus 4 molecules in combined_off and combined_artefact (Gammatorquevirus 1). None has DSR-02 evidence submitted.

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

`combined_off` GSM4682311 COMPLETED (25941228_4, 3 h 17, 64G). `combined_artefact` (25941231_4) was running on 2026-11-03 (13 h 44) and COMPLETED on 2026-11-04 (19 h 56); its numbers are in the table above. `twostep` row 4 (25941254_4) is still pending. No OOM here.
Gene programmes were off in the run; added with `rerun-programs` (job 25949108).

| arm | virus | molecules | called cells | scored | latent | productive | mixed | indeterminate |
|---|---|---|---|---|---|---|---|---|
| combined_off | KSHV | 555,654 | 3,426 | 3,205 | 3,172 | 0 | 5 | 28 |
| combined_off | EBV | 1,652 | 3,426 | 44 | 1 | 0 | 0 | 43 |

Counts reproduce round 2 (555,654 and 1,652.25). PROG-18 reading: KSHV is mostly latent (3,172 of 3,205 scored cells, 99 %), with a small mixed minority (5) and no productive cell. That matches the "mostly latent" expectation, with the caveat from `kshv_gse190558.md` that the productive rule gave 0 even in induced libraries. EBV: only 44 cells scored and 43 indeterminate, so the EBV programme is not informative here. Per-cell co-infection is still not computed.

## Update 2026-11-03: package 5b419d4 catalogue and the "mixed" cells

Official `rerun-programs` at 5b419d4 on this round's `combined_off` run (`posthoc/programs_5b419d4/`, job 25949495): KSHV 3,265 scored, productive 0, latent 2,889, mixed 288, indeterminate 88. EBV unchanged (44 scored, 43 indeterminate). The coordinator's recompute on the round-2 twostep run of the same library (called-cell set 2,979) gives productive 0, latent 2,357, mixed 605. The two arms differ in the called-cell set and the mixed count, same pattern.

Diagnosis of the mixed cells (`scripts/kshv_mixed_diagnosis.py`, read-only; unique KSHV molecules in the called cells):

| | twostep (n = 605 mixed) | combined_off (n = 288 mixed) |
|---|---|---|
| marker pair PAN (gs01) + K4 (gp13) only | 516 (85 %) | 256 (89 %) |
| other 2-marker sets (PAN + K3, K4 + K3) | 34 | 14 |
| 3 or more productive markers | 36 (6 %) | 18 (6 %) |
| 4 or more | 7 | 7 |
| productive molecules per cell: median [q25, q75, q95] | 3 [2, 4, 10] | 3 [2, 3.2, 17.6] |
| cells with at most 2 productive molecules | 196 (32 %) | 140 (49 %) |
| any ORF50 (gp52) or ORF16 (gp19) | about 40 | about 13 |
| latent molecules per cell, median | 62 | 58 |

Same readout in the latent-called cells of this library: PAN alone in 1,516 of 2,357 (64 %), K4 alone in 164, no productive marker in 653. So PAN at 1-2 molecules is the baseline of this library, and the mixed state is mostly the cells where K4 (or K3) also reaches 1 molecule on top of PAN: a threshold on a continuum, not a separate population. Only about 6 % of the mixed cells (36 of 605) show three or more productive markers, and only 7 show the late/IE markers expected of true lysis.
Latent library GSM5725695 for comparison: 0 mixed, 1 productive; its cells carry few KSHV molecules overall (median latent molecules 5 vs 38-62 here), so the contrast is depth-confounded and is not evidence that BC-1 differs biologically.

Ambient: the soup is dominated by the latent gene ORF71/K13 (90 % of ambient marker molecules; ambient_viral_fraction 0.0037). PAN is 6.9 % of the soup's marker molecules against 14.3 % in the mixed cells, K4 1.0 % against 2.7 %: the mixed cells are enriched about 2-3x for PAN and K4 over the soup profile, so soup alone does not explain the profile. The count-level expectation does not settle it: ambient_viral_fraction x the cell's total molecules gives 0.04 expected ambient productive molecules per cell in the twostep matrix (598 of 605 cells above the Poisson 99th percentile) but 35 per cell in the combined matrix (9 of 288 above), because the denominator (viral-only versus host-plus-virus totals) differs between arms. The ambient fraction was measured on its own denominator, so I treat this count test as inconclusive.

Verdict on the 605 (and the 288): mostly a narrow, shallow PAN + K4 signal (median 3 molecules from two early genes), enriched over the soup but not broad; likely a mix of low-level lytic-gene leakage in latent cells and ambient/threshold effects. A spontaneous-lytic minority proper is at most the 6 % with three or more productive markers (36 cells, about 1 % of called cells), and the 7 with four or more are the best candidates. The "mostly latent, lytic minority" reading of PROG-18 stands, with the lytic minority small and not confirmed at read level.
