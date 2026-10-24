# GBCD warning diagnosis — 2026-10-19

**The 500-iteration real-data fit passes the phase-aware technical gate.**
This corrects the blanket warning gate used by the historical pilot receipts.
It does not establish a full convergence certificate or biological validity.

## Source and replay evidence

Pinned `gbcd/R/fit_gbcd.R` contains two explicit `flash_backfit(maxiter = 25)`
initializations, followed by covariance refinements using `maxiter1/maxiter2`
and a final expression fit using `maxiter3`. Increasing those public budgets
does not change the two initialization budgets.

`diagnose_gbcd.R` replayed the exact saved 500-iteration request and captured
warning stacks without modifying the installed package or the adapter. Both
iteration warnings originated in the fixed 25-iteration initializations.
Neither originated in the covariance refinements or final expression fit.
Signatures and native memberships were byte-identical to the saved retry.

## Qualification correction and controls

The adapter now records `warning_details` from active function frames, including
the iteration budget and whether the warning occurred in initialization.
The gate exempts only GBCD initialization warnings with a recorded budget of
25 and exactly matching warning records. Terminal, missing, mismatched or
unclassified iteration limits remain disqualifying. All warnings are retained.
The pinned upstream source and installed runtime remain unchanged.

| Fresh real-data replay | Recorded iteration warnings | Current gate |
| --- | --- | --- |
| 100 iterations | Two initialization limits at 25; two covariance refinement limits at 100 | Rejected |
| 500 iterations | Two initialization limits at 25; no refinement/expression iteration warnings | Eligible |

Both replays retain byte-identical signatures and memberships relative to
their respective earlier runs. The 500-iteration fit took 73.16 seconds and
419.5 MiB peak R RSS. It retains five native factors despite requested rank 3.
No algorithm, prior, tolerance or iteration setting was changed to obtain a
passing result; only warning provenance and its interpretation changed.

The regression first failed under the blanket gate, then passed after the fix.
The full focused suite has **32 passing tests**, including fresh/cache reads,
terminal failures, scalar/list serialization, incomplete records, wrong-method
records and mismatched messages. Old fits without phase records remain
unqualified when their iteration warnings cannot be classified.

## Retained evidence and continuation

- Initial diagnostic replay: `outputs/pilot-diagnosis-20261019-v1/gbcd/`.
- Fresh eligible fit: `outputs/pilot-convergence-20261019-v2/gbcd/`.
- Real terminal-warning control: `outputs/pilot-warning-control-20261019-v1/gbcd/`.
- Frozen summary and hashes: [validation/diagnosis_receipt.json](validation/diagnosis_receipt.json).

The `diagnose_gbcd` and `gbcd_warning_control` targets in `pilot.smk` retain
the diagnostic replays; `pilot_convergence` retains the fresh 500-iteration
fit. Each uses one CPU and a 900-second cap within the existing allocation.
No new scheduler jobs were submitted. Historical receipts remain unchanged.

Next: increase cells/genes in bounded stages and evaluate DIVAS at its intended
simulation count before selecting cohort resources. The 200-cell x 80-gene
pilot does not qualify the full rank/seed grid, biological sharing or held-out
prediction. Mixed-population annotations and unit-count limitations remain.
