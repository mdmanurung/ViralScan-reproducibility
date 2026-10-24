# Software validation — 2026-10-19

**Implementation and local checks complete. Full cohort fitting has not run.**
The operational entrypoint and scientific contract are in [README.md](README.md).
The original software checkpoint is [validation/receipt.json](validation/receipt.json).
It predates the pilot's stricter iteration-warning gate; its code hashes and
nine-check acceptance count describe that historical checkpoint.

| Check | Observed result |
| --- | --- |
| Focused software tests | 32 passed, zero skips; explicitly select `-m research`. Includes phase-aware fresh/cached warning handling and isolated retry configuration. |
| Native method checks | Nine completed; seven eligible under the corrected warning gate. GBCD null and overlapping cases reached iteration limits and are now rejected. |
| Independent overlapping-signal oracle | Every executed method recovered >99.7% of both known signal subspaces; GBCD's result is convergence-unqualified. Shuffled-gene recovery was <6.6%. |
| Track A inventory | 71 libraries present; 65 GEX included, six HHV-6B TCR libraries excluded; no missing included inputs. |
| Read-only real input probe | Three frozen EBV barcodes matched the source matrix. |
| Real preparation | GSM4796271: 2,647 frozen called cells x 41,145 canonical host genes; raw/source hashes recorded. |
| Workflow dry-run | 65 preparation, 18 discovery, 48 prediction, inventory, report and collector: 134 jobs; 16 prediction designs. |
| Static checks | Scoped Ruff lint/format, text-file checks and tracked diff whitespace passed. |

The focused tests cover barcode identity, integer raw counts, label semantics,
training-only gene selection, repeated-unit split protection, held-out gene
reconstruction, signed/permuted seed matching, native factor index preservation,
biological replication, depth confounding, study confounding, single-class
designs, partial report denominators, independent HSV-1 mock/time contrasts,
the exact upstream shape correction, full held-out cell coverage and batched
projection. One orchestration test uses a fixed basis to audit the Python
dataflow; real fitting engines have separate synthetic oracle checks.
Tests also distinguish descriptive sharing from formal support and check the
exact sign-flip power bound before a shared-signature claim is possible.

## Source and runtime qualification

The final native run is `.runtime/qualification-v3/qualification.json`; each
case/method directory retains its request, log, native fit, gene signatures,
native scores, diagnostics and input/output identities. Installation, source
and dependency hashes are in `.runtime/receipt.json`. Old unsuccessful
qualification attempts are retained. Rechecking the nine final diagnostics
under `fit_rejection` rejects GBCD's null and overlapping fits because their
warnings report iteration limits. The historical qualification JSON is retained
unchanged; it must not be used to override the corrected gate.

- GBCD: `stephenslab/gbcd@670e3afb50236303ddf99db33a3394abd4a711bd`.
- EBCD: `joonsukkang/ebcd@54cadb62b8d8d173d5bde1d3ec75290b84d67baa`.
- DIVAS: `ByronSyun/DIVAS@294986fac88bdeea1071902aa360b19e820c85de`,
  installable `pkg/` API, with the two explicit `drop=FALSE` corrections in
  `upstream.json`. The unmodified source failed the rank-one null case.
- CVXR 1.0-15: archived source SHA-256
  `c13b192a3793103880b43fb4d213a7928b0fc24db3a8df7b3f5cb587f92b838c`.
  The installed shared CVXR 1.9.2 API was incompatible with this DIVAS source.

Only the private analysis R library was installed/rebuilt. Shared packages,
frozen Track A matrices, other analysis outputs and the public ViralScan CLI
were not edited. The real preparation receipt is
`outputs/preparation-smoke-20261019/prepared/GSM4796271/receipt.json`.
That smoke output records its original code/metadata identity; use a new
output root for later runs after code or metadata changes.

## Limits and next action

The native checks use small synthetic matrices (100 cells x 80 genes), one
seed, 40 DIVAS simulations and 100 GBCD/EBCD iterations. They establish API,
orientation, finite-output and synthetic subspace-recovery evidence. Null and
study-confounded cases check execution; they do not estimate false-positive
rates or establish specificity. DIVAS retains angle-diagnostic NaN warnings
and rejected nonconverging search directions; only accepted finite bases are
used. Gene-aligned DIVAS significance remains uncalibrated.

No real-data program fitting, cohort prediction, full-resource benchmark,
scheduler dispatch, publication or scientific promotion has occurred.
Mixed-population author cell types remain absent. The code keeps those
associations descriptive. Rare activity can also make a training fold
unevaluable under the default fitting caps; held-out evaluation retains all
eligible frozen cells. These five datasets cover four distinct DNA viruses.

Known source-derived unit-ID counts are HSV-1 5, HHV-6B 5, EBV 2, HPV16 rafts 2
and HNSCC 15. Their best-case two-sided sign-flip p-values are 0.0625, 0.0625,
0.5, 0.5 and 0.0000610 respectively, before multiplicity correction. Actual
eligible unit counts can be smaller, and independence of every named
experimental replicate has not been established. The current set cannot
support formal shared inference in two studies under these tests.
`descriptive_cross_context` patterns remain available for exploration, with
unit/annotation limitations and `passes_unit_inference_gates=False` recorded.

**Real-data pilot completed:** see [PILOT.md](PILOT.md) and
[validation/pilot_receipt.json](validation/pilot_receipt.json). GBCD took
37.37 seconds but is rejected for iteration warnings; EBCD took 8.79 seconds,
DIVAS 489.93 seconds. No new scheduler jobs or cohort fits were submitted.
The first default-500-iteration GBCD retry took 65.68 seconds and was rejected
by the blanket warning gate; [validation/convergence_receipt.json](validation/convergence_receipt.json)
preserves that historical assessment. The diagnosis located both warnings in
fixed 25-iteration initialization steps. The fresh `v2` fit took 73.16 seconds,
passes the phase-aware technical gate, and has byte-identical signatures and
memberships. See [GBCD_DIAGNOSIS.md](GBCD_DIAGNOSIS.md).
Next: measured engine scaling before choosing a
cohort allocation. The full graph's declared 64 GB / 24-hour fitting resources
are requests, not measured requirements.
