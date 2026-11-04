# KSHV GSE190558 (RUN-04, PROG-16), round 2026-11-02

Status 2026-11-04: 11 of 12 library-arm cells have a summary (the original OOM arms were rerun as `_r2`). GSM5725698 twostep (job 25941254_3) is PENDING on JobArrayTaskLimit with no task of its array running. DSR-02 (`_r2` array 25952505): rows 1-2 COMPLETED, rows 3-5 RUNNING, rows 6-16 PENDING, row 0 ran out of memory and was resubmitted (25953432_0, PENDING). Programme tables at 5b419d4 are missing for the three `combined_artefact_r2` runs. GSE184257 Set 3 download: 3 of 4 libraries done. The round-2 numbers below (pin e7c1b08, 2026-10-13/14) are the baseline and are labelled as such. Exploratory, unscored.

## Setup

- Package pin: `v3.0.0rc1-164-gde55424` (worktree `ViralScan/.claude/worktrees/pin-kshv`, clean). Env `viralscan_test_full`.
- Reference: cat42d (`data/references/panel_builds/viral_ref_cat42d/build`, virus-only `build_virus_only`), STAR host `data/references/starsolo/ebv_latest_ref_2026-09-27/star_host_2.7.11b`.
- Inputs (read only): lane-concatenated GSM FASTQs `data/runs/work/dsr_round1/inputs/<GSM>/<GSM>_R{1,2}.fastq.gz`, the round-1/2 inputs, so the arms compare with round 2. Source SRRs under `data/inputs/benchmark_inputs/dsr_2026-10-05/GSE190558/SRR17180386-401` all present with `DONE`. Lane map (runbook 12a): GSM5725695 latent = SRR17180398-401; GSM5725696 lytic = 394-397; GSM5725697 lytic + casp-i = 390-393; GSM5725698 lytic + casp-i + anti-IFN = 386-389.
- Chemistry: frozen round-1 `check-chemistry` JSONs, copied to `data/runs/round_2026-11-02/_kshv/chem/`: 10xv3 (95.7-96.4 % on-list), strand forward. Not re-measured.
- Arms per library: `combined_off`, `combined_artefact` (`--read-filter artefact`), `twostep` (`--host-filter starsolo`, virus-only index). All with `--cell-calling emptydrops --anellovirus-gene-ids`. Gene programmes were OFF in these runs (`config.yaml: gene_programs: false`, despite the help text); layer 2 is added afterwards with `viralscan rerun-programs` (`scripts/slurm_kshv_programs.sh`, job 25949108), which writes only `<run>/posthoc/programs/` and changes no counts.
- DSR-02 read validation: chained job, see below.
- Outputs: `data/runs/round_2026-11-02/GSE190558/<GSM>/<arm>/` (run metadata and `time.txt` in `meta_<arm>/`). Logs `data/runs/round_2026-11-02/_kshv/logs/`.

## Commands and jobs

Scripts: `scripts/slurm_kshv_round_2026-11-02.sh` (ARM=...), `scripts/slurm_kshv_dsr02_chain.sh`, `scripts/slurm_kshv_dsr02_row.sh`. Manifest `config/kshv_round_2026-11-02.manifest.tsv` (rows 0-3 are this dataset).

| Job | Arm | Rows | Resources | State 2026-11-04 |
|---|---|---|---|---|
| 25941227 | combined_off | 0-3 %3 | 4 cpu, 32G, 12 h | _0 COMPLETED; _1-3 OUT_OF_MEMORY (superseded by 25949104) |
| 25941230 | combined_artefact | 0-3 %3 | 4 cpu, 32G, 24 h | _0 COMPLETED; _1-2 OUT_OF_MEMORY; _3 CANCELLED by the user (superseded by 25949105) |
| 25941254 | twostep | 0-4 %3 (0-3 here) | 8 cpu, 64G, 24 h | _0-2 COMPLETED; _3-4 PENDING (JobArrayTaskLimit; no task of the array running) |
| 25941255 | dsr02 chain (afterany of all arrays) | enumerates calls, submits the evidence array | 1 cpu, 4G | PENDING (Dependency on 25941254_*) |
| 25949104 | combined_off_r2 | 1-3 | 96G | _1-3 COMPLETED (1 h 32 to 2 h 06) |
| 25949105 | combined_artefact_r2 | 1-3 | 128G | _1-3 COMPLETED (9 h 17 to 12 h 47) |
| 25949108, 25949495, 25950135 | `rerun-programs` (`de55424` catalogue, then 5b419d4 twice) | finished runs | 32-48G | COMPLETED |
| 25949110 | `_r2` DSR-02 chain | enumerates the 17 calls of the `_r2` arms | 4G | COMPLETED; submitted 25952505 |
| 25952505 | `_r2` DSR-02 evidence array (rows 0-16 %6) | see DSR-02 section | 24G | _0 OUT_OF_MEMORY; _1-2 COMPLETED; _3-5 RUNNING; _6-16 PENDING |
| 25953432 | DSR-02 row 0 resubmit | row 0 | 48G | _0 PENDING (Priority) |
| 25953402 | GSE184257 Set 3 download array (0-3) | see held-out data section | 2G | _0 FAILED (broken pipe); _1-3 COMPLETED |
| 25953433 | retry of 25953402_0 | task 0 | 2G | _0 RUNNING |

Smoke tests (500 k pairs of GSM5725695, output under `_kshv/smoke/`, not results): jobs 25941195 (combined, artefact) and 25941226 (twostep). They passed CLI parsing, chemistry check, read filter, STARsolo and kb count; the artefact smoke ended at emptyDrops ("insufficient unique points"), expected on 500 k reads.
No explore-ledger append this round: de55424 has no `scripts/explore_ledger.py`.

## Outcome per library and arm (de55424)
Source: `data/runs/round_2026-11-02/GSE190558/<GSM>/<arm>/<GSM>/results/viral_summary.tsv` (HHV-8 row), programmes from `<run>/posthoc/programs_5b419d4/results/gene_program_summary.tsv`, collected with `PROGRAMS_DIR=programs_5b419d4 python3 -I scripts/kshv_round_collect.py new data/runs/round_2026-11-02` on 2026-11-04. The original OOM rows have no summary; their `_r2` reruns are listed next to them. Table `kshv_summary_5b419d4.tsv` is refreshed from the same command.

| GSM | condition | arm | job | state | KSHV molecules | called cells | infected called (%) | programmes at 5b419d4: scored / productive / latent / mixed / indeterminate |
|---|---|---|---|---|---|---|---|---|
| GSM5725695 | latent | combined_off | 25941227_0 | COMPLETED | 59,365 | 5,690 | 3,086 (54.2) | 2,574 / 1 / 2,522 / 0 / 51 |
| GSM5725695 | latent | combined_artefact | 25941230_0 | COMPLETED | 59,361 | 5,690 | 3,085 (54.2) | 2,573 / 1 / 2,521 / 0 / 51 |
| GSM5725695 | latent | twostep | 25941254_0 | COMPLETED | 59,506 | 5,587 | 3,021 (54.1) | 2,527 / 1 / 2,478 / 0 / 48 |
| GSM5725696 | lytic | combined_off | 25941227_1 | OUT_OF_MEMORY at 32G | no summary | | | |
| GSM5725696 | lytic | combined_artefact | 25941230_1 | OUT_OF_MEMORY at 32G | no summary | | | |
| GSM5725696 | lytic | combined_off_r2 | 25949104_1 | COMPLETED (96G) | 23,671,063 | 7,942 | 7,941 (99.99) | 7,939 / 4,842 / 1,152 / 1,661 / 284 |
| GSM5725696 | lytic | combined_artefact_r2 | 25949105_1 | COMPLETED (128G) | 23,670,509 | 7,940 | 7,939 (99.99) | programmes not run |
| GSM5725696 | lytic | twostep | 25941254_1 | COMPLETED | 23,717,600 | 7,748 | 7,638 (98.6) | 7,638 / 4,709 / 1,043 / 1,699 / 187 |
| GSM5725697 | lytic + casp-i | combined_off | 25941227_2 | OUT_OF_MEMORY at 32G | no summary | | | |
| GSM5725697 | lytic + casp-i | combined_artefact | 25941230_2 | OUT_OF_MEMORY at 32G | no summary | | | |
| GSM5725697 | lytic + casp-i | combined_off_r2 | 25949104_2 | COMPLETED (96G) | 23,545,060 | 6,839 | 6,836 (99.99) | 6,835 / 3,095 / 1,414 / 1,986 / 340 |
| GSM5725697 | lytic + casp-i | combined_artefact_r2 | 25949105_2 | COMPLETED (128G) | 23,544,978 | 6,862 | 6,859 (99.99) | programmes not run |
| GSM5725697 | lytic + casp-i | twostep | 25941254_2 | COMPLETED | 23,600,287 | 6,597 | 6,485 (98.3) | 6,485 / 3,065 / 1,231 / 1,993 / 196 |
| GSM5725698 | lytic + casp-i + anti-IFN | combined_off | 25941227_3 | OUT_OF_MEMORY at 32G | no summary | | | |
| GSM5725698 | lytic + casp-i + anti-IFN | combined_artefact | 25941230_3 | CANCELLED by the user after 3 min 47 s | no summary | | | |
| GSM5725698 | lytic + casp-i + anti-IFN | combined_off_r2 | 25949104_3 | COMPLETED (96G) | 31,763,568 | 9,159 | 9,159 (100) | 9,159 / 5,444 / 1,230 / 2,269 / 216 |
| GSM5725698 | lytic + casp-i + anti-IFN | combined_artefact_r2 | 25949105_3 | COMPLETED (128G) | 31,761,926 | 9,151 | 9,151 (100) | programmes not run |
| GSM5725698 | lytic + casp-i + anti-IFN | twostep | 25941254_3 | PENDING (JobArrayTaskLimit) | pending | | | |

EBV: 1 molecule in GSM5725697 twostep, combined_off_r2 and combined_artefact_r2 (1 infected called cell each).

Collect (re-run when 25941254_3 and the programme reruns finish):

    PROGRAMS_DIR=programs_5b419d4 python3 -I scripts/kshv_round_collect.py new data/runs/round_2026-11-02

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

Read: KSHV molecules are about 400x higher in the induced libraries than in the latent one, and all three arms agree to within 1 % on molecules. EBV shows 1 molecule in GSM5725697 (noise). Round 2 wrote no gene programme file, so the latent-gene half of the acceptance test (LANA/ORF73, vFLIP/ORF71, vCyclin/ORF72 in both conditions) is not yet shown; the programme tables are added by `rerun-programs` (see Interim).

## What this says for PROG-16 (lytic acceptance)

Partly met on round 2: induced > uninduced by molecule count, in every arm. Not yet shown: latent genes present in both conditions, and the programme-level (productive vs latent cell counts) contrast. The de55424 gene-programme tables settle this. GSE190558 is iSLK.219, a cell line with a high latent fraction, so "54 % of called cells infected" in the latent library needs the programme table before it is read as latent.

## Interim 2026-11-03 (de55424)

Status of the jobs (sacct): `combined_off` GSM5725695 COMPLETED (25941227_0, 57 min, MaxRSS 17 GB); `combined_artefact` GSM5725695 COMPLETED (25941230_0, 3 h 57); `twostep` GSM5725695/-96/-97 COMPLETED (25941254_0-2, 1 h 54 to 5 h 15, MaxRSS 15 GB); `twostep` GSM5725698 (_3) pending.
OUT_OF_MEMORY at 32G (sacct MaxRSS is capped at the limit, 30.8-31.9 GB, so the true need is unknown): `combined_off` GSM5725696/-97/-98 (25941227_1-3, 1 h 10 to 1 h 26), `combined_artefact` GSM5725696/-97 (25941230_1-2, 6 h and 9 h). `combined_artefact` GSM5725698 (25941230_3) was still pending at 32G.
Reruns into NEW dirs `<arm>_r2` (`ARM_SUFFIX=_r2`, the OOM dirs are left as they are): `combined_off_r2` rows 1-3 at 96G (job 25949104), `combined_artefact_r2` rows 1-3 at 128G (job 25949105), DSR-02 for them via chain 25949110 (`TAG=_r2`).
The original DSR-02 chain 25941255 runs once the original arrays end; it sees only the arms that finished, and the OOM arms count as `n/a (no summary)` there. The `_r2` chain covers them, so 25941255 does not need re-running.

Finished cells (table: `analysis/round_2026-11-02/kshv_summary_partial.tsv`, from `scripts/kshv_round_collect.py new`):

| GSM | arm | KSHV molecules | called cells | scored for programme | latent | productive | mixed | indeterminate |
|---|---|---|---|---|---|---|---|---|
| GSM5725695 latent | combined_off | 59,365 | 5,690 | 2,556 | 2,523 | 0 | 0 | 33 |
| GSM5725695 latent | combined_artefact | 59,361 | 5,690 | 2,555 | 2,522 | 0 | 0 | 33 |
| GSM5725695 latent | twostep | 59,506 | 5,587 | 2,512 | 2,479 | 0 | 0 | 33 |
| GSM5725696 lytic | twostep | 23,717,600 | 7,748 | 7,534 | 6,116 | 0 | 1,230 | 188 |
| GSM5725697 lytic + casp-i | twostep | 23,600,287 | 6,597 | 6,345 | 5,295 | 1 | 914 | 135 |

Molecule counts reproduce round 2 within 0.1 % (latent, three arms) and 0.5 % (lytic, twostep).

PROG-16 reading: induced > uninduced holds on molecules (400x). The programme layer does not show it: in the two induced libraries almost no cell is called productive (0 and 1 of about 7,000), and most are called latent. Latent presence in the uninduced library is shown (2,523 latent cells). A productive call of 0 with 23.7 M KSHV molecules points at the productive-marker rule (uniquely placed molecules, at least 2 non-overlapping groups) failing on KSHV, not at absent lysis. Treat the acceptance test as not passed at the programme level until the marker rule is checked (open question, not diagnosed here).

## Update 2026-11-03: package 5b419d4 catalogue (PR #181: PAN, K4, K3, ORF52 productive; ORF37 dropped; `induced_in_lytic`)

Official numbers: `viralscan rerun-programs` from a detached worktree at 5b419d4 (`ViralScan/.claude/worktrees/pin-kshv-5b419d4`), into NEW `posthoc/programs_5b419d4/` of each run (job 25949495, `scripts/slurm_kshv_programs_5b419d4.sh`; the older `posthoc/programs/` is kept). Table: `analysis/round_2026-11-02/kshv_summary_5b419d4.tsv`. Read-only diagnosis script: `scripts/kshv_mixed_diagnosis.py` (log `_kshv/logs/kshv_diag_25949496.log`). Runs finished by then only; `_r2` and remaining twostep runs still to do: rerun `slurm_kshv_programs_5b419d4.sh` (it skips done dirs).

| GSM | arm | scored | productive | latent | mixed | indeterminate |
|---|---|---|---|---|---|---|
| GSM5725695 latent | combined_off | 2,574 | 1 | 2,522 | 0 | 51 |
| GSM5725695 latent | combined_artefact | 2,573 | 1 | 2,521 | 0 | 51 |
| GSM5725695 latent | twostep | 2,527 | 1 | 2,478 | 0 | 48 |
| GSM5725696 lytic | twostep | 7,638 | 4,709 | 1,043 | 1,699 | 187 |
| GSM5725697 lytic + casp-i | twostep | 6,485 | 3,065 | 1,231 | 1,993 | 196 |

PROG-16: with the new catalogue the induced libraries are mostly productive (62 % and 47 %) or mixed (22 % and 31 %); the latent library is 98 % latent with 1 productive and 0 mixed cell. This is the induced > uninduced contrast the earlier catalogue missed (it gave 0 and 1 productive). Productive cells in the induced libraries are broad: 2-7 markers, median 6-7 molecules; mixed cells there carry 2-8 markers (median 14-19 molecules). Latent genes in both conditions: the latent library is latent-called in 98 % of scored cells, and the induced libraries keep 1,043 and 1,231 latent-called cells. Caveat: ambient is large in the induced libraries (`ambient_viral_fraction` 0.068 and 0.118), and the marker profile of the soup matches the mixed cells (cosine 0.99), so cell-level productive counts there overlap with soup; the 4,709 / 3,065 productive cells are not all independent of it. Still open on 2026-11-03 (state on 2026-11-04 in the Outcome table above): combined_off_r2 programmes are done (next update); combined_artefact_r2 programmes are not run; GSM5725698 twostep is pending.

## Update 2026-11-03: combined_off_r2 programme calls, and states by load including non-called barcodes

**combined_off_r2 (job 25950135, `rerun-programs` at 5b419d4, `posthoc/programs_5b419d4/`).** KSHV scored / productive / latent / mixed / indeterminate:
GSM5725696 7,939 / 4,842 / 1,152 / 1,661 / 284 (61 % productive); GSM5725697 6,835 / 3,095 / 1,414 / 1,986 / 340 (45 %); GSM5725698 9,159 / 5,444 / 1,230 / 2,269 / 216 (59 %). Same pattern as twostep (62 % and 47 %).

**Why this check.** An adversarial review (2026-11-03) found that cell calling leaves 34 % (GSM5725696) and 16 % (GSM5725697) of KSHV molecules in non-called barcodes, 229 and 79 of them with >= 500 molecules, and that "98 % latent" in GSM5725695 may be depth-limited (latent cells median 15 molecules).
**Method.** `scripts/kshv_programmes_by_load.py` scores every called cell plus every non-called barcode with >= 100 KSHV molecules, using the package's own `run_one` at 5b419d4 and the run's parameters, on the twostep arm. It stops if its called-cell states differ from the official `gene_program_cells.tsv` (they match). Output `data/runs/round_2026-11-02/_kshv/programmes_by_load/` (`barcode_states.tsv`, `states_by_load.tsv`, `versions.txt`).

Barcodes with >= 500 KSHV molecules, called and non-called together:

| library | n | productive | mixed | latent | non-called share of n |
|---|---|---|---|---|---|
| GSM5725695 latent | 0 | | | | (no barcode reaches 500) |
| GSM5725696 lytic | 2,532 | 1,278 (50 %) | 1,237 (49 %) | 17 (1 %) | 229 |
| GSM5725697 lytic + casp-i | 2,346 | 920 (39 %) | 1,361 (58 %) | 64 (3 %) | 80 |

At matched load (twostep, called cells):

| load bin (KSHV molecules) | GSM5725695 latent: latent / productive / mixed | GSM5725696: latent / productive / mixed | GSM5725697: latent / productive / mixed |
|---|---|---|---|
| 15-100 | 1,252 / 1 / 0 | 357 / 319 / 21 | 449 / 354 / 21 |
| 100-500 | 27 / 0 / 0 | 660 / 3,183 / 594 | 713 / 1,832 / 645 |
| 500-2,000 | none | 13 / 853 / 408 | 56 / 639 / 679 |
| >= 2,000 | none | 1 / 352 / 676 | 4 / 240 / 648 |

Reading:
- Cell calling does not drive the contrast. Adding the non-called heavy barcodes moves the productive share by 2 points or less, and among heavy barcodes 97-99 % are productive or mixed.
- The latent library is latent at matched load too: at 15-100 molecules it has 1 productive cell in 1,253, the lytic libraries about half. At 100-500 it has 27 latent and 0 productive. Depth alone does not explain "98 % latent", though only 27 latent-library cells reach 100 molecules.
- The productive / mixed split is load-driven: the mixed share rises with load (13-20 % at 100-500, 66-73 % at >= 2,000), consistent with latent markers reaching one molecule in heavily lytic cells, which the latent-marker veto then calls mixed. Read productive + mixed together as "lytic programme present"; do not read the split as biology.
- Not addressed: the 5b419d4 markers were chosen with this dataset in view; the held-out test (PROG-16) is still open.

## Update 2026-11-03: mixed veto fit and training gate (PLAN PROG-MIXED-VETO-01)

Package PR #187 adds a load-aware `mixed` veto. Fit (`scripts/kshv_fit_veto_p0.py`, 135 called cells with >= 2,000
unique KSHV molecules in GSM5725696/-97 twostep): median latent-veto share 0.004167, IQR 0.0023-0.0086; the
counts are 57.5x overdispersed against a binomial, so the planned binomial veto flagged 42 of the 135 heavy
lytic cells and failed the training check (mixed share 2-7 % at 100-500 and 19-20 % at >= 2,000 allocated
molecules; `_kshv/veto_training_check/`). Beta-binomial MLE on the same cells: mean 0.007365, rho 0.006506
(`_kshv/veto_fit_betabinom_342c8db/`, byte-identical to the first fit run).

Training gate (`scripts/kshv_veto_training_gate.py`, unique-layer bins, `_kshv/veto_training_gate_13ec4ff/` on `_kshv/veto_training_check_betabinom_13ec4ff/`, package 13ec4ff; byte-identical to the first runs):

| library | rule | mixed % at [15,100) / [500,inf) | gap (points) |
|---|---|---|---|
| GSM5725696 | any | 26.0 / 94.5 | 68.5 |
| GSM5725696 | betabinomial | 1.9 / 1.6 | -0.3 |
| GSM5725697 | any | 41.2 / 89.8 | 48.5 |
| GSM5725697 | betabinomial | 7.5 / 2.8 | -4.7 |

Under the beta-binomial veto mixed cells fall from 1,699 to 99 (-96) and 1,993 to 311 (-97); productive + mixed
and latent calls are unchanged; GSM5725695 is unchanged (1 productive, 2,478 latent). Training data only: the
held-out gate is pre-registered in `prog_mixed_veto_prereg.md` (committed before any held-out run).

## DSR-02 read validation of the `_r2` arms (chain 25949110, array 25952505, state 2026-11-04)
Calls: `data/runs/round_2026-11-02/_kshv/evidence_r2/calls.tsv` (17 rows, run dirs under `_kshv/view_r2/`). Output: `_kshv/evidence_r2/<dataset>__<GSM>__<arm>__<virus>/`. The array runs at 24G.

| Row | Library | Arm | Call (molecules) | Job | State | virus-best / host-best / tie / unaligned (counted) | Flags | Verdict |
|---|---|---|---|---|---|---|---|---|
| 0 | GSM5725696 | combined_artefact_r2 | HHV-8 (23,670,509) | 25952505_0 | OUT_OF_MEMORY at 24G after 48 min; partial output moved to `evidence_r2/_failed/`. Resubmitted as 25953432_0 at 48G, PENDING | pending | | pending |
| 1 | GSM5725696 | combined_artefact_r2 | HPV77 (4) | 25952505_1 | COMPLETED (1 h 05) | 2 / 0 / 0 / 4 | host_homology flagged 0.333 | virus-best 2, host-best 0 of 6 counted |
| 2 | GSM5725697 | combined_artefact_r2 | Cercopithecine herpesvirus (5) | 25952505_2 | COMPLETED (0 h 57) | 0 / 0 / 3 / 2 | none flagged | no virus-best molecule; 3 ties, 2 unaligned |
| 3 | GSM5725697 | combined_artefact_r2 | HHV-8 (23,544,978) | 25952505_3 | RUNNING (1 h 00) | pending | | pending |
| 4 | GSM5725697 | combined_artefact_r2 | HPV77 (6) | 25952505_4 | RUNNING | pending | | pending |
| 5 | GSM5725698 | combined_artefact_r2 | HHV-8 (31,761,926) | 25952505_5 | RUNNING | pending | | pending |
| 6 | GSM5725698 | combined_artefact_r2 | HPV29 (3) | 25952505_6 | PENDING | pending | | pending |
| 7-16 | GSM5725696-98 | combined_off_r2 | Cercopithecine herpesvirus, HHV-8, HPV77, HPV29 (see `calls.tsv`) | 25952505_7-16 | PENDING (throttle %6) | pending | | pending |

Rows 1-2: `molecule_verdict_summary.tsv` (`counted` rows) and `interpretation_flags.tsv` in the row's evidence dir.
Risk: rows 3, 5, 8, 11 and 14 are HHV-8 calls with 23.5 to 31.8 M molecules, the same shape as row 0, which ran out of memory at 24G. `calls.tsv` marks HHV-8 `expected=false`, so the enumerator lists the target virus as an off-target call. The original arms (GSM5725695 all arms, GSM5725696/-97 twostep) are covered only by chain 25941255, which is blocked behind 25941254_3-4.

## Held-out data for the mixed-veto gate: GSE184257 Set 3 download
Script `scripts/slurm_gse184257_set3_download.sh` (array 0-3, user decision Q3, 2026-11-04), output `data/runs/work/gse184257_set3/raw/<GSM>/`, MD5-checked against ENA, `DONE` written last.

| Task | GSM | SRR | Condition | Job | State |
|---|---|---|---|---|---|
| 0 | GSM6249889 | SRR19685943 | Mock 3dpi Set 3 | 25953402_0 | FAILED (broken pipe after 14 min; a partial `SRR19685943_2.fastq.gz.tmp` was left) |
| 0 | GSM6249889 | SRR19685943 | Mock 3dpi Set 3 | 25953433_0 (retry) | RUNNING |
| 1 | GSM6249890 | SRR19685944 | Mock 6dpi Set 3 | 25953402_1 | COMPLETED, `DONE` present |
| 2 | GSM6249891 | SRR19685945 | KSHV 3dpi Set 3 | 25953402_2 | COMPLETED, `DONE` present |
| 3 | GSM6249892 | SRR19685946 | KSHV 6dpi Set 3 | 25953402_3 | COMPLETED, `DONE` present |

3 of 4 libraries are downloaded. The held-out gate runs (chemistry check, arms, `rerun-programs --programme-mixed-veto betabinomial`) are not scripted or submitted yet; the pre-registration is `prog_mixed_veto_prereg.md`.
