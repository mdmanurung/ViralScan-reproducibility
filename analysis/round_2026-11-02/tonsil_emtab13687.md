# DSR-07 E-MTAB-13687 tonsil atlas negative-control subset, round 2026-11-02

Status 2026-11-04: all arm runs finished, including the ERR13027027 twostep retry (job 25949107). DSR-02 for the combined_off HSV-1 call (25949116_7) COMPLETED; the combined_artefact call (25949116_8) is PENDING; the twostep retry HSV-1 call has no DSR-02 job. Package pin: `de55424` (clean worktree
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
| ERR13027027 | twostep retry | 25949107 | COMPLETED (4 h 19 min, 96G) | `data/runs/round_2026-11-02/tonsil_atlas/ERR13027027/twostep_retry1/` |
| ERR13027027 | DSR-02 HSV-1, combined_off | 25949116_7 | COMPLETED (1 h 16 min) | `data/runs/round_2026-11-02/_dsr0607/evidence/tonsil_atlas__ERR13027027__combined_off__Human_herpesvirus_1/` |
| ERR13027027 | DSR-02 HSV-1, combined_artefact | 25949116_8 | PENDING (Priority) | not created |

Inputs under `data/inputs/benchmark_inputs/dsr_2026-10-05/E-MTAB-13687/<ERR>/`. ERR13027010: R1 = `_1`, R2 = `_2`. ERR13027027: R1 = `_2` (7.8 GB, barcode), R2 = `_1` (17 GB, cDNA), the frozen round-1 orientation. `-x 10xv3 --strand forward` for both (on-list 96.2 % and 95.3 %).
- ERR13027122: **n/a, not run.** Round-1 check-chemistry gives strand pilot 0.1 / 0.0 / 0.2 % (forward / reverse / unstranded): not a GEX library (probably HTO/ADT, 28.2 M reads). Sample choice was made from metadata before any viral output (run plan section 10).
Accept (run plan section 10): no probable/strong call beyond rare EBV; every call goes to DSR-02.
Expected duration from round 2 (e7c1b08): ERR13027027 combined_off 2 h 12 min, twostep 3 h 30 min, combined_artefact 11 h 17 min (single-threaded filter).

## Results
Source: `<run dir>/<library>/results/viral_summary.tsv`. Eleven of the first twelve jobs COMPLETED; the failed twostep job was rerun as 25949107 (COMPLETED). Elapsed: ERR13027010 off 18 min, artefact 1 h 33 min, twostep 38 min; ERR13027027 off 2 h 07 min, artefact 10 h 51 min.

| library | arm | detected rows (molecules) |
|---|---|---|
| ERR13027010 | combined_off | none |
| ERR13027010 | combined_artefact | none |
| ERR13027010 | twostep | Molluscum contagiosum virus 1 |
| ERR13027027 | combined_off | HHV-1 29 (8 / 19709 called cells); HHV-8 2; HHV-6A 1; Cercopithecine herpesvirus 1; Samektorquevirus 1 |
| ERR13027027 | combined_artefact | identical to combined_off |
| ERR13027027 | twostep | **job 25941215 FAILED**, see below |
| ERR13027027 | twostep_retry1 (job 25949107) | HHV-1 29 (7 / 12,455 called cells); Gammatorquevirus 1; Cercopithecine herpesvirus 1; Samektorquevirus 1; HPV77 1; Yaba-like disease virus 1 |

twostep_retry1 file: `data/runs/round_2026-11-02/tonsil_atlas/ERR13027027/twostep_retry1/ERR13027027/results/viral_summary.tsv` (rows with `detected True`; unique fraction 1.0, background 3 UMIs for HHV-1). The HSV-1 molecule count (29) equals the combined arms. HPV86, Cowpox virus and Coxsackievirus have 1 molecule and are not detected.

No EBV row is detected in any completed arm. Accept check: partly met. Nothing probable/strong on EBV, but ERR13027027 carries HSV-1 at 29 molecules in 8 of 19.7 k called cells (unique fraction 1.0, background 2). That is an off-target call at >= 3 molecules and goes to DSR-02 below. It is not read as a finding until DSR-02 returns.

### ERR13027027 twostep failure (job 25941215)
Exit 1 after 53 min on `res-hpc-mem02`. The log shows `STAR ... Illegal instruction (core dumped)` in the STARsolo host filter, then `CalledProcessError` in `host_filter.py` (line 441, `subprocess.run(cmd, check=True)`). Cause: the conda STAR binary uses a CPU instruction missing on the old Xeon E5-2690 v3 in `res-hpc-mem02`. All other twostep jobs ran on `res-hpc-exe*` nodes. It is a node problem, not a package bug and not a script or memory problem.
Resubmitted as job 25949107 with `--exclude=res-hpc-mem02` into a new dir `tonsil_atlas/ERR13027027/twostep_retry1/` (script `ARM_DIR=twostep_retry1`); the failed dir is untouched. The retry COMPLETED in 4 h 19 min.

## DSR-02 read validation (array 25949116, rows 7-8 of `analysis/round_2026-11-02/dsr0607_offtarget_calls.tsv`)
| Row | Library | Arm | Call | Job | State | Molecules virus-best / host-best / tie / unaligned | Verdict |
|---|---|---|---|---|---|---|---|
| 7 | ERR13027027 | combined_off | HSV-1 (29 molecules) | 25949116_7 | COMPLETED | 29 / 1 / 0 / 0 | virus-best in 29 of 30 counted molecules; host_homology, low_complexity, sibling_or_host_ambiguity, coverage_hotspot and eve_or_integration_like_hotspot all not flagged |
| 8 | ERR13027027 | combined_artefact | HSV-1 (29 molecules) | 25949116_8 | PENDING | pending | pending |

The twostep_retry1 HSV-1 call (29 molecules, 7 cells) has no row in `dsr0607_offtarget_calls.tsv` and no DSR-02 job.

## Pending
- Row 8 (25949116_8, combined_artefact), then the HSV-1 verdict for both arms. Row 7 numbers: `.../tonsil_atlas__ERR13027027__combined_off__Human_herpesvirus_1/molecule_verdict_summary.tsv` (`counted` rows) and `interpretation_flags.tsv`.
- A DSR-02 job for the twostep_retry1 HSV-1 call, or a note that rows 7-8 cover it.
