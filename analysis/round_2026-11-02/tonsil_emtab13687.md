# DSR-07 E-MTAB-13687 tonsil atlas negative-control subset, round 2026-11-02

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
| ERR13027010 | combined_off | 25941210 | COMPLETED | `data/runs/round_2026-11-02/tonsil_atlas/ERR13027010/combined_off/` |
| ERR13027010 | combined_artefact | 25941211 | COMPLETED | `data/runs/round_2026-11-02/tonsil_atlas/ERR13027010/combined_artefact/` |
| ERR13027010 | twostep | 25941212 | COMPLETED | `data/runs/round_2026-11-02/tonsil_atlas/ERR13027010/twostep/` |
| ERR13027027 | combined_off | 25941213 | COMPLETED | `data/runs/round_2026-11-02/tonsil_atlas/ERR13027027/combined_off/` |
| ERR13027027 | combined_artefact | 25941214 | COMPLETED | `data/runs/round_2026-11-02/tonsil_atlas/ERR13027027/combined_artefact/` |
| ERR13027027 | twostep | 25941215 | FAILED (node, see Results) | `data/runs/round_2026-11-02/tonsil_atlas/ERR13027027/twostep/` |

Inputs under `data/inputs/benchmark_inputs/dsr_2026-10-05/E-MTAB-13687/<ERR>/`. ERR13027010: R1 = `_1`, R2 = `_2`. ERR13027027: R1 = `_2` (7.8 GB, barcode), R2 = `_1` (17 GB, cDNA), the frozen round-1 orientation. `-x 10xv3 --strand forward` for both (on-list 96.2 % and 95.3 %).
- ERR13027122: **n/a, not run.** Round-1 check-chemistry gives strand pilot 0.1 / 0.0 / 0.2 % (forward / reverse / unstranded): not a GEX library (probably HTO/ADT, 28.2 M reads). Sample choice was made from metadata before any viral output (run plan section 10).
Accept (run plan section 10): no probable/strong call beyond rare EBV; every call goes to DSR-02.
Expected duration from round 2 (e7c1b08): ERR13027027 combined_off 2 h 12 min, twostep 3 h 30 min, combined_artefact 11 h 17 min (single-threaded filter).

## Results
Source: `<run dir>/<library>/results/viral_summary.tsv`. Eleven of twelve jobs COMPLETED. Elapsed: ERR13027010 off 18 min, artefact 1 h 33 min, twostep 38 min; ERR13027027 off 2 h 07 min, artefact 10 h 51 min.

| library | arm | detected rows (molecules) |
|---|---|---|
| ERR13027010 | combined_off | none |
| ERR13027010 | combined_artefact | none |
| ERR13027010 | twostep | Molluscum contagiosum virus 1 |
| ERR13027027 | combined_off | HHV-1 29 (8 / 19709 called cells); HHV-8 2; HHV-6A 1; Cercopithecine herpesvirus 1; Samektorquevirus 1 |
| ERR13027027 | combined_artefact | identical to combined_off |
| ERR13027027 | twostep | **job 25941215 FAILED**, see below |

No EBV row is detected in any completed arm. Accept check: partly met. Nothing probable/strong on EBV, but ERR13027027 carries HSV-1 at 29 molecules in 8 of 19.7 k called cells (unique fraction 1.0, background 2). That is an off-target call at >= 3 molecules and goes to DSR-02 below. It is not read as a finding until DSR-02 returns.

### ERR13027027 twostep failure (job 25941215)
Exit 1 after 53 min on `res-hpc-mem02`. The log shows `STAR ... Illegal instruction (core dumped)` in the STARsolo host filter, then `CalledProcessError` in `host_filter.py` (line 441, `subprocess.run(cmd, check=True)`). Cause: the conda STAR binary uses a CPU instruction missing on the old Xeon E5-2690 v3 in `res-hpc-mem02`. All other twostep jobs ran on `res-hpc-exe*` nodes. It is a node problem, not a package bug and not a script or memory problem.
Resubmitted as job 25949107 with `--exclude=res-hpc-mem02` into a new dir `tonsil_atlas/ERR13027027/twostep_retry1/` (script `ARM_DIR=twostep_retry1`); the failed dir is untouched.

## Pending
- Collect step, then DSR-02 per call with `scripts/dsr02_validate_call.py --run-dir <library run dir> --virus <name> --panel-fasta data/references/panel_builds/viral_ref_cat42d/build/viral.fa --host-fasta <GRCh38 genome.fa> --out <dir>`.
  `scripts/dsr02_enumerate_calls.py` cannot be used as is: it globs `runs/<dataset>/<arm>/<sample>/` and this round uses `<dataset>/<library>/<arm>/`.
