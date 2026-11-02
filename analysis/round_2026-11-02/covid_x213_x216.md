# COVID x213 / x216 rerun (PLAN DSR-04), 2026-11-02

Status: **submitted, not started** (all 6 jobs PENDING on Priority at 2026-11-02). No numbers yet.

Package SHA: `de55424` (`v3.0.0rc1-164-gde55424`, clean worktree `ViralScan/.claude/worktrees/pin-dsr0304`). Env: `conda/envs/viralscan_test_full`. Reference: `cat42d` (`data/references/panel_builds/viral_ref_cat42d/build`, virus-only `build_virus_only` for twostep; STAR host `data/references/starsolo/ebv_latest_ref_2026-09-27/star_host_2.7.11b`). Script: `scripts/slurm_round_2026_11_02_dsr0304.sh` (arms differ only by flags, as `slurm_dsr_rerun_array.sh`). `-x` and `--strand` come from the frozen round-1 chem JSON (`data/runs/work/dsr_round1/chem/<lib>.json`, copied to each `<arm>.meta/check_chemistry.json`). Cells: `--cell-calling emptydrops`, `--anellovirus-gene-ids`. Run dirs: `data/runs/round_2026-11-02/<dataset>/<library>/<arm>/` (+ `<arm>.meta/` with `code_sha.txt`, `time.txt`).

Inputs (checked present): `data/runs/covid_viralscan/data/LUM-SJ-x2{13,16}-g/LUM-SJ-x2{13,16}-g_merged_R{1,2}.fastq.gz` (25 GB / 56 GB and 20 GB / 44 GB), whitelist `data/runs/covid_viralscan/viralscan_ref/cellranger_whitelist.txt`. Chemistry `-x 10xv3 --strand reverse` (strand pilot: 46.0 % reverse vs 4.3 % forward).

| Library | Arm | Job | Resources | State at write |
|---|---|---|---|---|
| LUM-SJ-x213-g | combined_off | 25941184 | 8 cpu, 32G, 1d | PENDING |
| LUM-SJ-x213-g | combined_artefact | 25941185 | 4 cpu, 32G, 4d | PENDING |
| LUM-SJ-x213-g | twostep | 25941186 | 8 cpu, 48G, 2d | PENDING |
| LUM-SJ-x216-g | combined_off | 25941187 | 8 cpu, 32G, 1d | PENDING |
| LUM-SJ-x216-g | combined_artefact | 25941188 | 4 cpu, 32G, 4d | PENDING |
| LUM-SJ-x216-g | twostep | 25941189 | 8 cpu, 48G, 2d | PENDING |

Expected cost from round 2 (x213): off 4.4 h, artefact 43.6 h (single-threaded filter), twostep 12.9 h wall.

## Reading anellovirus calls
The Alphatorquevirus magnitude from the old reference is retracted (CAT-30, `covid_viralscan/RETRACTION_NOTICE_CAT-30.md`: 99.999 % of the class reads carry a homopolymer >= 15 nt; no clean read had a viral best hit). Treat any anellovirus row here as unverified until read-validated; do not compare it as a replacement number. SARS-CoV-2 expected 0 (`NC_045512.2_gene1`). Accept: SARS-CoV-2 stays 0; anellovirus collapses on cat42d + artefact, or survivors go to DSR-02.

## Read validation (DSR-02) - still to do
Any surviving anellovirus call (always kept regardless of count, F-022) on `combined_off` and `combined_artefact`, same `--run-dir` command as in `hpv16_gse189670.md` (blocked on the GRCh38 FASTA path).

## Collect
```
sacct -X -j 25941184,25941185,25941186,25941187,25941188,25941189 -o JobID,JobName%26,State,Elapsed,MaxRSS
find data/runs/round_2026-11-02/covid -name viral_summary.tsv
```
