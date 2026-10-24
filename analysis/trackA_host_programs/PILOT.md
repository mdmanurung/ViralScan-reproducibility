# Real-data fitting pilot — 2026-10-19

Completed through Snakemake in existing allocation 25833654; no new scheduler
jobs. EBV GSM4796271 (2,647 frozen called cells) and HSV-1 GSM3511335
(5,361) were prepared read only. All eight source inputs rehashed unchanged.
Fitting used 100 label-blind sampled cells per library and 80 shared variable
host genes, seed 1, requested rank 3, GBCD/EBCD maxiter 100, DIVAS nsim 40.
Every engine had a 900-second process-group timeout; none timed out.

| Engine | Fit wall time | Peak R RSS | Current technical gate |
| --- | ---: | ---: | --- |
| GBCD | 37.37 s | 421.3 MiB | Rejected: iteration-limit warnings |
| EBCD | 8.79 s | 364.2 MiB | Eligible; upstream stopping rule |
| DIVAS | 489.93 s | 406.8 MiB | Eligible finite basis; rejected joint search and angle NaN warnings retained |

Times include R startup and fit input/output; memory is peak R child-process
RSS, excluding the Python parent and preparation. The 16 GB workflow resource
declaration is not a hard memory limit or a measured cohort requirement.
GBCD and DIVAS can return ranks different from the requested rank.

## Qualification repair

The pilot exposed a bug: GBCD's iteration warnings were retained but its
finite basis was still marked usable. `fit_rejection()` now checks warnings
on fresh fits and cache reads. The first repair had 25 passing focused tests, including
scalar/list warning serialization and old cached receipts marked `ok`.
Rechecking the nine saved synthetic fits rejects two GBCD cases (null and
overlapping); seven remain eligible under the corrected gate.

Original pilot artifacts remain unchanged in `outputs/pilot-20261019-v1/`.
Their historical `qualified_basis`/`status` flags predate the fix. Use
[validation/pilot_receipt.json](validation/pilot_receipt.json) for that checkpoint's
gate assessment, recorded diagnostics/signature hashes, test evidence and
source identities. `source_snapshot/` preserves the pilot's pre-fix analysis
code and driver; matching frozen hashes were checked before recording results.
The original [validation/receipt.json](validation/receipt.json) is a historical
software checkpoint, not qualification of the subsequent gate change.

## Default-iteration retry

The isolated GBCD retry at 500 iterations reported iteration warnings and
was rejected by the blanket warning gate. It took 65.68 seconds with 419.7 MiB peak
R RSS. Its matrix, genes, cell identities, adapter and runtime match the first
fit exactly; only the iteration budget changed. All eight source inputs were
rehashed unchanged. Results are in `outputs/pilot-convergence-20261019-v1/`;
the retained summary is
[validation/convergence_receipt.json](validation/convergence_receipt.json).
This second checkpoint includes the 25-test result and current driver hashes;
the first receipt retains the original pilot driver hashes. These are historical
checkpoints: the subsequent diagnosis located both 500-iteration-run warnings
in fixed 25-iteration initialization steps. The fresh `v2` retry passes the
phase-aware technical gate with byte-identical signatures and memberships.
See [GBCD_DIAGNOSIS.md](GBCD_DIAGNOSIS.md) for the current evidence.

## Next action

Increase genes/cells in measured stages, and test DIVAS at the
intended simulation count before sizing a cohort allocation. Retain failed
fits; do not reduce scientific settings to obtain a passing result. The current
80-gene benchmark cannot establish resource requirements for 3,000 genes or
the full rank/seed grid.

No shared-signature, stability or predictive-performance conclusions were
drawn. One library per study leaves viral exposure entangled with lineage and
study. Mixed-population author annotations and the previously documented
biological-unit limitations remain unresolved. Full cohort fitting is unrun.

## 300-gene scaling checkpoint

The user-requested continuation completed the next stage in the existing
allocation, through `pilot.smk pilot_scaling`, with one CPU and the same
900-second worker caps. Output is `outputs/pilot-scaling-300genes-20261019-v1/`.
The 200 fitting cells are byte-identical to the prior default-iteration
pilot, and all 80 original gene columns are exactly preserved within the
300-gene matrix. All eight source inputs rehashed unchanged. Rank 3, seed 1,
500 iterations and DIVAS nsim 40 were retained. The source snapshot and failed
native outputs are preserved.

| Engine | Fit wall time | Peak R child RSS | Technical outcome |
| --- | ---: | ---: | --- |
| GBCD | 363.66 s | 423.3 MiB | Rejected: non-initialization iteration limit at 500 |
| EBCD | 42.52 s | 365.1 MiB | Eligible finite basis |
| DIVAS | Worker capped at 900 s | Not measured for killed child | Timeout; no qualified basis |

SLURM placed the initial overlapping one-core stages on CPU 0, so the wall
times include contention and cannot be interpreted as isolated scaling
ratios. DIVAS's timeout does not distinguish intrinsic resource requirements
from the execution conditions. Its settings were not reduced to obtain a
passing result. GBCD's warning differs from the exempt fixed 25-iteration
initializations and remains a genuine qualification failure under the
recorded rule.

Evidence: `validation/scaling_receipt.json` and
`validation/scaling_input_checks.json`; current focused suite: 33 passed.
The full cohort grid remains unqualified and unrun. A separate immutable
cohort-preparation root has completed for all 65 GEX libraries (332,907 cells)
through inventory/prepare rules only. A second check verified every matrix's
dimensions and finite, nonnegative counts; it did not repeat input hashing.
This does not launch models or support biological claims.

The bounded follow-up on CPU 3 finished with unchanged inputs: GBCD at
maxiter 1000 returned five finite programs in 107.279 seconds, with only its
two recorded 25-iteration initialization warnings. DIVAS at unchanged nsim
40 returned 18 finite programs in 760.064 seconds, with five native
`NaNs produced` warnings. Both pass the existing mechanical rejection rule;
the warning trace identifies post-optimization `projAngleMJ` angle
diagnostics. Gene signatures and projected scores are byte-identical on
the logging-only replay. Source inspection shows those angles do not enter
reconstruction. No warning was suppressed or upstream code changed.
Neither result qualifies the full
3000-gene, nsim-400 production grid. See the report recovery folder's
`scaling_recovery_verified.json` and `cohort_preparation_verified.json`.
The recovery folder also records `divas_warning_diagnosis.json`. A separate
800-cell, 3000-gene probe now tests rank 10, seed 1, maxiter 500 and DIVAS
nsim 400, with 900-second engine caps on one CPU. It represents two libraries,
not the production cohort or full rank/seed grid.
