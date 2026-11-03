# DSR-06 GSE164690 HNSCC one-lane pilot (HN18 CD45- SRR13419165 vs HN01 SRR13418973), round 2026-11-02

Status 2026-11-03: runs finished (see Results); DSR-02 rows 0-3 done, rows 4-6 pending. Package pin: `de55424` (clean worktree
`ViralScan/.claude/worktrees/pin-dsr0607`). Reference: cat42d (`data/references/panel_builds/viral_ref_cat42d/{build,build_virus_only}`),
STAR host index `data/references/starsolo/ebv_latest_ref_2026-09-27/star_host_2.7.11b`. Env: `conda/envs/viralscan_test_full` + `R4_51`.
Script: `scripts/slurm_round_2026_11_02_dsr0607.sh` (same conventions as `slurm_round_2026_11_02_dsr0304.sh`).
Chemistry: frozen round-1 JSON (`data/runs/work/dsr_round1/chem/<library>.json`, copied to `<arm>.meta/check_chemistry.json`), not re-run.
Cell calling `emptydrops`, `--anellovirus-gene-ids`, no `--force-technology`. Outputs: `data/runs/round_2026-11-02/<dataset>/<library>/<arm>/`, metadata in `<arm>.meta/`.
Earlier runs of the same libraries exist (`dsr_round1`, `dsr_round2` on `e7c1b08`); this round is a rerun on `de55424` and does not replace them.

## Arms and flags
- combined_off: `-i panel.idx -t panel.t2g`
- combined_artefact: same plus `--read-filter artefact`
- twostep: `-i virus_panel.idx -t virus_panel.t2g --host-filter starsolo --host-index <STAR>`

## Jobs
| library | arm | job ID | state | run dir |
|---|---|---|---|---|
| SRR13419165 | combined_off | 25941204 | COMPLETED | `data/runs/round_2026-11-02/hnscc_gse164690/SRR13419165/combined_off/` |
| SRR13419165 | combined_artefact | 25941205 | COMPLETED | `data/runs/round_2026-11-02/hnscc_gse164690/SRR13419165/combined_artefact/` |
| SRR13419165 | twostep | 25941206 | COMPLETED | `data/runs/round_2026-11-02/hnscc_gse164690/SRR13419165/twostep/` |
| SRR13418973 | combined_off | 25941207 | COMPLETED | `data/runs/round_2026-11-02/hnscc_gse164690/SRR13418973/combined_off/` |
| SRR13418973 | combined_artefact | 25941208 | COMPLETED | `data/runs/round_2026-11-02/hnscc_gse164690/SRR13418973/combined_artefact/` |
| SRR13418973 | twostep | 25941209 | COMPLETED | `data/runs/round_2026-11-02/hnscc_gse164690/SRR13418973/twostep/` |

Inputs: R1 = `*_2.fastq.gz` (barcode), R2 = `*_3.fastq.gz` (cDNA) under `data/inputs/benchmark_inputs/dsr_2026-10-05/GSE164690/<SRR>/`; both libraries present. `-x 10xv2 --strand forward` (chem JSON: on-list 94.3 % HN18, 94.2 % HN01).
Accept (run plan section 9): HPV16 (or the clinically typed HPV) in HN18 tumour cells, about 0 in HN01. A full run only if the pilot passes.
DSR-02 read validation: not run yet; it follows the collect step for every call (see "Pending").

## Results
Source: `<run dir>/<library>/results/viral_summary.tsv`; all six jobs COMPLETED (elapsed: HN18 off 17 min, artefact 1 h 09 min, twostep 48 min; HN01 17 min, 1 h 14 min, 59 min). Collect: `scripts/collect_round_2026_11_02_dsr0607.sh`.

| library | arm | HPV16 molecules (called cells infected / called) | other detected virus rows |
|---|---|---|---|
| HN18 SRR13419165 | combined_off | 562 (151 / 940, 16.1 %) | HPV29 6 mol (5 cells) |
| HN18 | combined_artefact | 562 (151 / 937, 16.1 %) | HPV29 6 |
| HN18 | twostep | 587 (157 / 1172, 13.4 %) | HPV29 9, Samektorquevirus 3, Gammatorquevirus 1, HPV118 1 |
| HN01 SRR13418973 | combined_off | no HPV16 row | HPV29 6 mol (5 / 5251 cells), HPV118 1, HHV-8 1 |
| HN01 | combined_artefact | no HPV16 row | HPV29 6, HPV118 1, HHV-8 1 |
| HN01 | twostep | no HPV16 row | HPV29 4 (4 / 5219), HPV118 2, HHV-8 2, Gammatorquevirus 2, others 1 |

Accept check: met. HPV16 is called only in HN18 (562-587 molecules, 13-16 % of called cells, background 36-38 UMIs), and is absent from HN01 in all three arms. The read filter changes nothing for HPV16. Off-target rows with >= 3 molecules (HPV29 in both libraries, Samektorquevirus in HN18 twostep) go to DSR-02 below. HPV29 appears at 4-9 molecules in both a positive and a negative library, so it is probably a shared cross-map, not a finding; DSR-02 decides.

## DSR-02 read validation (array 25949116, rows of `analysis/round_2026-11-02/dsr0607_offtarget_calls.tsv`)
Script `scripts/slurm_round_2026_11_02_dsr0607_dsr02.sh`, package `de55424`, GRCh38 `data/references/grch38/refdata-gex-GRCh38-2024-A/genome.fa`. Output `data/runs/round_2026-11-02/_dsr0607/evidence/<dataset>__<library>__<arm>__<virus>/`. Molecules are the `counted` rows of `molecule_verdict_summary.tsv`; flags from `interpretation_flags.tsv`.

| Row | Library | Arm | Call | Molecules virus-best / host-best / tie / unaligned | Flags | Verdict |
|---|---|---|---|---|---|---|
| 0 | HN18 SRR13419165 | combined_off | HPV29 | 3 / 5 / 0 / 1 | host_homology, coverage and EVE-like hotspot | not supported: mostly host |
| 1 | HN18 | combined_artefact | HPV29 | 3 / 5 / 0 / 1 | same | not supported: mostly host |
| 2 | HN18 | twostep | Samektorquevirus | 2 / 1 / 0 / 0 | host_homology | inconclusive: 3 molecules, at the floor |
| 3 | HN18 | twostep | HPV29 | 3 / 6 / 1 / 1 | host_homology, coverage and EVE-like hotspot | not supported: mostly host |
| 4-6 | HN01 SRR13418973 | all three | HPV29 | pending (25949116_4-6) | | |

Reading: HPV29 in HN18 is the same host cross-map seen in the HPV16 rafts (DSR-03 note): more molecules align to human than to HPV29, with a single-locus hotspot. No BLAST read has a viral top hit. The Samektorquevirus call has 2 virus-best molecules; that is too few to call an anellovirus present or absent.
