# Track A continuation — 2026-10-20

User authorized finishing every previously reported Track A task. Work is
in progress; do not claim the full list complete. Preserve the dirty shared
checkout and the frozen pinned source. No deletion, external candidate
BLAST, push or publication is authorized here.

Read `analysis/trackA_report_2026-10-18/REPORT_2026-10-19.md` and its
`recovery_2026-10-19/` receipts. They supersede the October 18 findings and
October 19 handoff's execution state. Root `HANDOFF.md` belongs to another
workflow and is untouched.

Completed: 213 structural run validations, 281 primary tier joins, ten
selected extra-arm evidence summaries, provenance concat recovery, both
cross-library hostresponse controls, all six v3 control pairs. All 65 host
matrices (332,907 cells) have dimension/finite/nonnegative checks. Bounded
GBCD/DIVAS follow-ups returned finite bases; DIVAS warnings are being traced.
Production cohort fitting is unqualified and unrun.

HHV-6B anellovirus checks are complete: 26 full-depth valid empty BAMs,
13 scoped preregistered NEGATIVE verdicts, five kallisto calls with no Q137
support. This does not establish a universal genus detection limit.
All 54 primary anellovirus kallisto calls across datasets have zero original
Q137-passing molecules. HPV16 remains NOT TESTABLE for the new search.

Controllers run within existing allocation 25833654:

1. `recovery_2026-10-19/molecule_assignments.smk`: two of nine exact native
   replays passed initially; now four of nine pass and five continue. Log
   `molecule_assignment_remaining_execution.log`. Failed cases must retain
   partial exports and must not weaken the matrix oracle. EBV lacks retained
   corrected BUS text and cannot be replayed.
2. `zero_mapping_recovery.smk`: 29 frozen failed Drop-seq searches, six
   native threads, original mapping filters/reference/geometry, separate
   output root. Tag-only mode bypasses a reproduced STARsolo all-unmapped
   counting crash. Accept ONLY successful full-depth runs with zero mapped
   BAM records and exact retained-audit input counts. Nonzero BAMs fail
   closed. Read `ZERO_MAPPING_RECOVERY.md`. Log `zero_recovery_execution.log`.
   No original completion markers are manufactured. Cancel each blocked
   classifier only after its zero proof and original classifier validate.
3. `production_shape_probe.smk`: 800 cells, 3000 genes, rank 10, seed 1,
   maxiter 500, DIVAS nsim 400, 900-second engine caps. EBCD passes in
   175.2 s / 1002.6 MiB peak child RSS with no warnings. DIVAS times out
   at 900 s / 1812.5 MiB; GBCD is running. Earlier orchestration/dense
   Matrix Market failures are archived; the coordinate retry has exact
   numerical input and identity parity. Log `production_shape_probe_execution.log`.
4. `run_qualified_ebcd_cohort.py`: waits for all three resource probes to
   finish, then runs ONLY 22 EBCD targets from the existing full workflow
   (six discovery scopes, sixteen prediction folds, unchanged rank/seed
   grid and production configuration). One CPU / 64 GB, 24-hour controller
   cap. Log `ebcd_cohort_execution.log`; launch/final receipts are written
   when the wait ends/execution finishes. Other engines stay separately gated.
5. `finish_late_zero_retries.py`: standby until the first retry controller
   and original alignments finish. It preserves `zero_recovery_tasks_initial29.json`,
   then appends only later failed no-whitelist Drop-seq tasks, without changing
   any original task identity. It runs only new receipt targets through the
   same zero-only verifier. No running/pending original job is duplicated.
   Check `late_zero_retry_execution.log` and its plan/final receipts.

The DIVAS warning trace completed: all five warnings arise in upstream
`projAngleMJ` post-optimization angle diagnostics. Gene signatures and
projected scores are byte-identical on the logging-only replay. Reconstruction
uses bases/block mappings rather than the diagnostic angles. No suppression
or upstream edits; see `divas_warning_diagnosis.json`.

CPU use: molecule replay CPU 2 (one thread), zero recovery CPUs
0,1,3,8,9,10 (six threads), probes then EBCD CPU 11 (one thread), within eight reserved
CPUs. These are allocation steps, not new sbatch submissions. Original real
anellovirus arrays continue independently. Refresh their state with squeue
and accounting; never duplicate running or pending alignments.

The existing recurring advance chain continues submitting its previously
approved metadata refreshes. At 08:49, provenance job 25851735 ran and next
advance job 25851736 was time-deferred. Evidence bytes were unchanged despite
new timestamps. Both HHV-6B deletion dry-runs refused stale windows and an
active evidence writer. After it finished, 71/71 complete provenance and
READY states reverified. All 168 eligible public ENA read-count checks match,
with the table byte-identical to its predecessor and no FASTQ download.
Fresh HHV-6B dry-runs still refuse the stale deletion window; the raw-store
plan is empty, derived intermediates total 130 paths / 1072.5 GB. See
`hhv6b_deletion_packet_20261020.json`. No windows opened and nothing deleted. BUS text and
host-filtered pairs remain needed until all exports/searches finish.

Next action: inspect the three controller logs and new receipts. Refresh
`reconcile_tables.py`, then finish remaining dataset verdicts and report.
Remote BLAST needs actual candidate counts and separate approval first.
Final local Track A commit belongs in a separate worktree only after the
report is finished; user reviews and pushes. Do not stage unrelated changes.
