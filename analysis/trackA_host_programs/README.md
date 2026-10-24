# Track A host programs

Implementation evidence: [VALIDATION.md](VALIDATION.md).

Discover shared and context associated host programs with GBCD, EBCD and
gene-aligned DIVAS, then test host-only prediction of viral transcriptional
activity in held out biological units and studies. This is a separate,
exploratory analysis of saved `combined_off` matrices. It does not change
ViralScan's detection results or establish virus specificity.

## Inputs and scientific contract

The 71 available libraries cover HSV-1 (19), HHV-6B (13), EBV (3), HPV16 rafts
(2) and HNSCC (34). Six HHV-6B TCR-enriched libraries are excluded, leaving
65 GEX libraries. Tonsil is excluded. Inputs come from `config.json`:
`adata_multimap.h5ad`, `virus_identity.tsv`, frozen called barcodes, the Track A
manifest/library titles, evidence tiers, and the independently sourced labels
in the existing Track A report. Neither FASTQs nor BUS files are needed.

- Host expression is integer `counts_original`, restricted to `is_viral=False`.
  Ensembl version suffixes are removed and duplicate host IDs summed; gene
  symbols remain annotations. All frozen barcodes must match exactly once.
- Viral burden sums **exact** expected-virus names in
  `counts_multimap_host_conservative`. EBV types are combined within HHV-4;
  HPV160, HSV-2, HHV-6A, vector HIV and artefact viruses cannot enter these
  target labels. `counts_unique_viral` supplies a separate sensitivity analysis.
- A relative activity label reproduces the pinned hostresponse convention:
  select the highest viral-per-host-UMI cells, retaining the number of positives
  defined by >=10 viral molecules. Thus a labelled cell need not itself have
  10 molecules. This is a cohort-relative transcriptional endpoint, not an
  infected/uninfected label or a deployable diagnostic cutoff.
- Library evidence must support the expected target before a nonzero signal
  contributes to target-resolved inference. Absence of a library-level positive
  call is not evidence that every cell is uninfected.
- Repeated HNSCC patients, HHV-6B donors, EBV donors and HSV-1 culture replicate
  identifiers stay together. Missing donor identity stays unknown. The two
  HPV16 rafts do not supply replicated positive/control conditions.

Author cell types can be supplied in `cell_types.tsv`: `library`, `barcode`,
`cell_type`, `source`. Empty annotations use source-defined broad labels for
NHDF fibroblasts, LCLs and NIKS keratinocytes. Mixed HHV-6B/HNSCC populations
remain `unannotated`; sorting fractions are recorded as source populations,
not invented cell types. Associations in those mixed populations remain
descriptive until author annotations are available. Unknown annotation libraries,
duplicate barcodes, missing genes/layers, or changed input identity are errors.

## Method implementations

`upstream.json` freezes upstream source identities. `setup_runtime.py` installs
only into `.runtime/library` and retains original sources/licenses and file
hashes. It never installs into the shared R library. R4_51 and the existing
Python analysis environment are used. Package installation is a separate step;
the analysis never downloads or installs packages automatically.

| Method | Qualified interface and orientation |
| --- | --- |
| GBCD | `gbcd::fit_gbcd(Y)` on cells x genes, generalized-binary prior with scale 0.04; convert native `F$lfc` from log2 to natural-log units. Final rank can exceed initialization `Kmax`. |
| EBCD | `ebcd::ebcd(C=t(Y), N=ncol(Y))`, generalized-binary cell memberships and signed orthogonal gene factors. Supplying the uncompressed target avoids upstream automatic covariance compression and preserves the gene-space map. |
| DIVAS | Install the upstream `pkg/` package with the recorded two-line rank-one shape correction; `DIVASmain(..., ReturnDetail=TRUE)`. Each study is cells x matched genes, so native `Scores` rows are genes. Use CVXR **1.0-15**, not the incompatible 1.9.2 API. |

DIVAS's root-level scripts and installable package expose different APIs; this
workflow uses the inspected package API. DIVAS requires >=2 study blocks, so
its within-single-study fits are explicitly unevaluable. Its gene-aligned
bootstrap/subspace inference has not been calibrated for correlated genes and
must not be interpreted as nominal statistical significance.

The original DIVAS signal extractor drops matrix dimensions when retained rank
is one. The null smoke test exposed the resulting `non-numeric matrix extent`
error. `upstream.json` records the exact two `drop=FALSE` source corrections;
setup checks their anchors, applies them only in the private source copy, and
records the corrected source/installed hashes. The upstream commit plus these
declared corrections identify this build; it is not claimed to be pristine
upstream parity.

All methods expose canonical signed, unit-norm gene signatures for comparison.
Scores for all called cells use a common ridge projection with coefficient
1e-6. These are **projected program activities**, not native nonnegative
memberships or calibrated posterior estimates. Native fits, native fitting-cell
scores, original column names and the exact signature source remain available.
GBCD does not expose a complete convergence certificate; EBCD objective
decreases and iteration limits make a candidate unqualified. Warnings are kept.
GBCD's two pinned 25-iteration initialization steps are distinguished from
refinement by recording active function frames and iteration budgets. Only
fully recorded initialization limits are nonterminal. Terminal or unclassified
iteration warnings still reject a fit, including cached fits.

## Workflow and outputs

Run commands from the repository root. First prepare the private method runtime:

```bash
PY=/exports/archive/hg-funcgenom-research/mdmanurung/conda/envs/viralscan_test_full/bin/python
SNAKE=/exports/archive/hg-funcgenom-research/mdmanurung/venvs/snakemake_slurm/bin/snakemake
$PY analysis/trackA_host_programs/setup_runtime.py --fetch
$PY -m pytest tests/test_tracka_host_programs.py -m research -q
$PY analysis/trackA_host_programs/qualify_methods.py
XDG_CACHE_HOME=/tmp/tracka-host-programs-cache $SNAKE \
  --snakefile analysis/trackA_host_programs/Snakefile --cores 1 --dry-run
```

`--source-cache` can reuse previously downloaded commit-verified sources.
`--rebuild` reinstalls only this analysis's private library while retaining its
old receipt. Small real-engine qualification checks overlapping shared/specific
truth, a null expression dataset and a study-confounded dataset. These checks
qualify software mechanics and the synthetic oracle, not scientific calibration.

The Snakemake graph prepares libraries independently, fits each method to each
study and a balanced pooled sample, predicts five study holdouts plus grouped
three-fold within-study holdouts where >=3 known units exist, then reports all
results and failures. Preparation hashes actual source matrices. The controller
uses its own Snakemake environment and obtains the design from the configured
analysis Python environment, so it needs no analysis-package installations.

Fitting uses deterministic, label-blind caps of 400 cells/library
and 1,000 cells/study. Held-out evaluation retains every called cell with an
eligible target label, projecting in bounded batches. All called cells receive
discovery projections. Selection
uses up to 3,000 genes expressed in every training study, selected by training
variance. GBCD/EBCD test ranks 10/20/30 and seeds 1–5; DIVAS estimates rank and
tests seeds 1–5. Validation holds out biological units and reconstructs an
unseen 20% of genes using the other 80%. The training-selected rank/seed is
refitted on all outer-training cells, retaining all final seeds for stability.
No outer-test expression influences gene/rank/seed selection. A failed selected
seed is not silently replaced.

Classifier penalties 0.01/0.1/1/10 are selected by inner-validation log loss,
using the **inner-training** gene basis. If inner validation has one class,
the predeclared penalty is 1. Fit standardization on training cells only.
Retain host-program-only, programs+QC, QC-only and within-library/cell-type/depth
scrambled-label controls. QC comprises log host depth, mitochondrial fraction,
and log detected host genes. Report AUROC, AUPRC, Brier score, log loss,
calibration bins, depth-matched and cell-type-stratified metrics. Test-unit
cluster bootstrap intervals and paired AUC differences require >=3 known units;
otherwise uncertainty is explicitly unavailable. Serialized classifiers accompany
their training feature basis and predictions; they are research artifacts.

Associations use adjusted within-library/cell-type correlations with viral
CPM, then average repeated libraries within biological units. Sign-flip tests
and bootstrap intervals use units, not cells. Eligible inference requires >=3
known units and author/source cell types. Global BH correction spans all
reported method/scope/context/program/sensitivity tests. Candidate sharing
requires concordant significant associations in >=2 studies, stability in >=80%
of requested seeds, and concordant unique-count and depth-matched sensitivities.
Few units can make significance unattainable; a valid outcome is no shared
program meeting these requirements. A single-context result does not establish
virus specificity. Gene programs are also matched across methods and between
pooled and separate-study fits by absolute cosine and Hungarian assignment.

The current known unit-ID counts are HSV-1 5, HHV-6B 5, EBV 2, HPV16 rafts 2
and HNSCC 15. Even with perfectly concordant effects, the smallest two-sided
sign-flip p-value with five units is 0.0625. Thus only HNSCC can theoretically
reach raw p<=0.05, and formal shared support in two studies is unattainable
with this input set under the declared tests. `inference_power.tsv` records
these optimistic bounds; actual eligible contrast counts may be smaller.

To support the agreed exploratory goal, `sharing.tsv` also labels
`descriptive_cross_context` programs: stable, concordant adjusted associations
and unique-count/depth-matched sensitivities in >=2 studies, each with >=2
known contributing unit IDs. Missing cell types remain flagged, and
`passes_unit_inference_gates` stays false for these descriptive patterns.
They are candidates for biological interpretation and held-out prediction;
they do not establish replicated infection signatures or virus specificity.

Independent HSV-1 source labels also supply paired mock-versus-1/3/5-hour and
time-trend contrasts within culture replicates, adjusted for host QC. These
comparisons do not depend on a ViralScan-positive call and enter the same FDR
family. Sign-flip inference assumes symmetric unit effects under the null.
Other studies lack this replicated paired mock design and are explicitly
unevaluable for that particular endpoint; EBV activity, HPV patient status and
HHV-6B reactivation must not be substituted for randomized infection exposure.

Principal outputs under the configured versioned root:

- `inventory.json`, `libraries.tsv`, per-library counts/cells/genes and input hashes.
- Discovery signatures, all-cell projected scores, native fits, warnings,
  rank/seed validation, stability and adjusted association tables.
- Held-out predictions, classifier files, calibration and replicate uncertainty;
  every failed or unevaluable design has a status and reason.
- `REPORT.md`, `report.json`, `task_status.tsv`, `sharing.tsv`,
  `associations.tsv`, `program_matches.tsv`, `inference_power.tsv` and
  `prediction_metrics.tsv`.

The report records method failures as incomplete even though Snakemake can
finish assembling the report. Workflow completion never establishes scientific
validity. `run_identity.json` freezes code/config and metadata hashes; changed
inputs require a new output root. Existing Track A run directories are read only.

## Execution boundary

The full graph has 65 preparation tasks, 18 discovery tasks, 48 prediction
tasks, inventory and report: **133 tasks** before Snakemake's final collector.
Many prediction/design tasks are correctly unevaluable; the graph retains them
in the denominator. Each discovery/prediction task requests 1 CPU, 64 GB and
24 hours; preparation requests 16 GB and two hours. The default selection grid
can launch hundreds of serial native fits across these tasks. Benchmark a
bounded pilot before requesting a full scheduler allocation; no jobs are
submitted by the setup, design, qualification or dry-run commands above.

To change run configuration, copy `config.json`, set a new `output_root`, and
pass `--config analysis_config=/absolute/path/config.json` to Snakemake.
Paths within that configuration are relative to its directory. A production
scheduler invocation must be bounded by the reviewed pilot resources and the
project's scheduler authorization.

The bounded real-data benchmark is `pilot.smk` (run within an existing
allocation):

```bash
XDG_CACHE_HOME=/tmp/tracka-pilot-cache snakemake \
  --snakefile analysis/trackA_host_programs/pilot.smk --cores 1 \
  --resources mem_mb=16000 --printshellcmds
```

It prepares EBV GSM4796271 and HSV-1 GSM3511335, then samples 100 cells per
library without labels and selects 80 variable host genes. Each method uses
rank 3, seed 1, GBCD/EBCD maxiter 100 (DIVAS nsim 40) and a 900-second process-group
timeout. The 16 GB declaration is a workflow resource budget, not an enforced
memory limit. The existing allocation must accommodate the pilot. Per-engine
`benchmark.json` records elapsed fitting time and peak R child-process RSS;
`outputs/pilot-20261019-v1/benchmark.json` records worker exit/timeout status.
An exit code of zero alone does not qualify a basis: inspect `status.json`
and `diagnostics.json`. This benchmark has one library per study and cannot
establish biological sharing, stability, predictive performance or cohort-scale
resource requirements. Its output root is immutable after completion.
DIVAS uses its upstream iteration controls; the process-group timeout bounds
its runtime. The first pilot exposed a GBCD warning-gate bug: historical
`qualified_basis`/`status` fields must be rechecked against native diagnostics.
The phase-aware gate rejects terminal or unclassified iteration warnings on
fresh fits and cache reads; documented initialization limits are retained.
The GBCD convergence retry uses the same data and sampling with 500 iterations
and a separate root, `outputs/pilot-convergence-20261019-v2/`:

```bash
XDG_CACHE_HOME=/tmp/tracka-pilot-cache snakemake \
  --snakefile analysis/trackA_host_programs/pilot.smk pilot_convergence \
  --cores 1 --resources mem_mb=16000 --printshellcmds
```

The historical `v1` retry used the blanket warning gate. The `v2` run records
warning phases and is assessed under the current gate. Diagnostic replays and
their evidence are described in [GBCD_DIAGNOSIS.md](GBCD_DIAGNOSIS.md).

Virus identity remains entangled with study, lineage, transformation and time;
host normalization measures relative expression and cannot establish absolute
host shutoff. The five datasets cover four distinct target viruses, all DNA
viruses. Independent cohorts and
RNA-virus generalization are outside this first analysis.

## Attribution

- [GBCD source](https://github.com/stephenslab/gbcd) and
  [HNSCC workflow](https://stephenslab.github.io/gbcd-workflow/gbcd_hnscc_intro.html):
  Liu, Carbonetto, Willwerscheid and colleagues, Nature Genetics (2025).
- [EBCD source](https://github.com/joonsukkang/ebcd), Kang and colleagues;
  [the linked comparison](https://xxie6.github.io/EBCD_GBCD_comparison/) informed
  orientation, but its older custom fitting code is not used.
- [DIVAS source](https://github.com/ByronSyun/DIVAS), Prothero and colleagues'
  methodology and Sun/Mao's R implementation;
  [workshop materials](https://github.com/jiadongm/EBNMF-workshop).
- [CVXR](https://cvxr.rbind.io/), Fu, Narasimhan and Boyd; the archived source
  checksum is retained in `upstream.json`.

Original licenses stay with private upstream sources. No upstream implementation
is copied into ViralScan's public package or redistributed by this analysis.
