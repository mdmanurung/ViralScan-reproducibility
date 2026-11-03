# DSR-06 GSE164690 HNSCC one-lane pilot (HN18 CD45- SRR13419165 vs HN01 SRR13418973), round 2026-11-02

Status 2026-11-03: runs finished (see Results); DSR-02 read validation of off-target calls submitted. Package pin: `de55424` (clean worktree
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

## Pending
- Collect step, then DSR-02 per call with `scripts/dsr02_validate_call.py --run-dir <library run dir> --virus <name> --panel-fasta data/references/panel_builds/viral_ref_cat42d/build/viral.fa --host-fasta <GRCh38 genome.fa> --out <dir>`.
  `scripts/dsr02_enumerate_calls.py` cannot be used as is: it globs `runs/<dataset>/<arm>/<sample>/` and this round uses `<dataset>/<library>/<arm>/`.
