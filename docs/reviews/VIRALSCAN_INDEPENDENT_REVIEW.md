# ViralScan — Independent Adversarial Review of the v3 Roadmap

**Review date:** 20 October 2026
**Input reviewed:** `ViralScan_refined_roadmap_round2.md` (R0–R7, Appendices A–E), supplied with the review request. It is **not** present in the repository, so there is no committed copy to diff against; §9 records the disposition of every round-2 item.
**Audit tree:** commit `78660933e2f8b35b8c20a490f4d36c93db4e692b` (2026-10-20 09:19 +0200), checked out in a clean worktree
**Also checked:** `origin/main` = `9151da9` (7 commits ahead of the audited tree) and the local checkout `5e551c9` (2026-10-13, **238 commits behind** the audited tree)
**External sources read:** Lareau `04_super_expressors.R` (raw file), scPathoQuant `spq/visualization/viz.py` (raw file)

**Evidence standard.** This review is source inspection plus execution of the claim-relevant unit tests and two direct reproductions. Tests were run from the audited tree with `PYTHONPATH=src pytest` (pytest 9.1.1 on the system conda Python 3.10, scanpy 1.11.5). The repo `.venv` (Python 3.14.5) has no `pytest`, and system `python3` is 3.6.8, so neither was used. Executed: `tests/test_super_expressors.py` (1 passed), `tests/test_evidence.py` (69 passed), `tests/test_swap_check.py` + `tests/test_ambient_screen.py` (26 passed), `tests/test_detection.py` (38 passed), and `tests/test_detection_audit_s2.py -k SuperExpressor` (3 passed). The denominator arithmetic was reproduced directly (4.0 % legacy vs 0.2 % over the complete universe), and the zero-virus path was executed (exit 0, two-column header — see BUG-7). The coverage-plot path was executed on synthetic BAMs with samtools 1.16.1 (Lmod module `genomics/ngs/samtools/1.16.1/gcc-8.5.0`): the uncovered interval is bridged exactly as BUG-6 describes, and a mixed BAM shows a host contig admitted by the global `explicit_classes` OR. No real-data benchmark was run, no holdout outcome was inspected, and no repository code was modified. Claims below are labelled **Verified** (read in the audited source, and executed where stated), **Partially verified** (read but dependent on runtime configuration), or **Unverified** (not independently reproduced).

---

## 1. Executive verdict

**The roadmap's central defect claim is correct and release-relevant. Its scope is roughly 40 % larger than the evidence justifies.**

The roadmap correctly identified a real, reproducible denominator defect in the SuperExpressor summary, a real host-depth mis-specification and two silent rendering choices in the SuperExpressor PNG, and a real visual-correctness defect in the coverage comparison plot (lines bridging uncovered viral bases). Every one of these was confirmed in source. The roadmap also correctly resisted the tempting-but-wrong changes: no ambient subtraction, no alternative aligner, no threshold changes, no promotion of STAR rescue to default, and no holdout inspection.

However, the roadmap retains four work items whose value is speculative relative to their cost: the R2 three-schema evidence expansion, the R5 junction programme, the R3 tier-2 fingerprinting as a release-track deliverable, and the R1 pyGenomeTracks "phase 2". It also over-credits some fixes: the SuperExpressor PNG receives the full **unfiltered** matrix (all droplets), not merely "every row of the provided AnnData", and the standalone script is a manual analysis tool that the project already invokes with `--cells`, not a pipeline stage. These corrections *strengthen* the case for a small, fail-closed fix and *weaken* the case for a shared "calculation layer" framework.

The single most important change to the roadmap is structural: **split R1 into (a) a tiny truthfulness bug fix to an existing plot, and (b) a genuinely new opt-in coverage-map feature.** The first is release-critical; the second is a usability feature. Merging them delays the fix and inflates the test surface.

The second most important change: **R6 is not implementation work.** It is a governance gate. Listing it alongside code packages invites an agent to "work on" a frozen protocol. It must be reclassified.

The third: **R5 should be explicitly deferred out of the release path.** Nothing in the current evidence model can support junction-level transcription claims without curated annotations that do not exist in the repo, and the roadmap's own text says so. A release must not wait for it.

**Verdict: accept the roadmap's diagnosis, reject roughly one third of its scope, and re-sequence.**

---

## 2. Most consequential findings

### 2.1 The SuperExpressor summary default denominator is wrong (confirmed, and worse than described)

`scripts/super_expressors.py:30-42`:

```python
by_virus = defaultdict(dict)
called = set()
with open(per_cell_viral, newline="") as fh:
    for row in csv.DictReader(fh, delimiter="\t"):
        bc = row["barcode"]
        if row.get("is_called_cell", "").lower() == "true":
            called.add(bc)
        ...
universe = set(cells) if cells is not None else called
```

`detection.compute_stats()` writes per-cell rows only for virus-positive barcodes (`src/viralscan/scripts/detection.py:1104`, comment literally `# Per-cell rows (only infected cells)`), including non-called ones with `is_called_cell=False`. Therefore the fallback `called` set is **virus-positive called cells only**. Virus-negative called cells — the overwhelming majority of every real library — never enter the denominator.

The existing test **encodes the defect as expected behaviour** (`tests/test_super_expressors.py:24-38`):

```python
(row,) = se.summarise(p, min_umi=10)  # denominator = is_called_cell (A, B)
assert (row["n_cells"], row["n_super_expressors"], row["pct_cells_super"]) == (2, 1, 50.0)
```

A library with 1,000 called cells, 50 virus-positive, 2 ≥10 would report **4 %**, not **0.2 %**. The roadmap's arithmetic is right.

**Two corrections to the roadmap's framing:**

1. The script is not a pipeline stage. `PLAN.md:6504-6512` records SE-01 closed with the documented invocation `scripts/super_expressors.py --per-cell-viral F --cells ANCHOR`. The project's own practice is already the safe route. The residual risk is the defective default and any reuse that omits `--cells`.
2. `scripts/super_expressors.py` is **absent from the local checkout** `5e551c9` (it was added 2026-10-15 and main has moved 238 commits since). Any implementation agent working in the local tree will not find the file. The handoff must pin the audited tree.

`--cells` is a correct, already-implemented solution. The smallest adequate fix is: **resolve the authoritative called-cell file automatically, and fail closed when it cannot be resolved** — not a new abstraction.

### 2.2 The SuperExpressor PNG's null is not host depth, and its cell universe is the whole unfiltered matrix

`src/viralscan/scripts/detection.py:351`:

```python
n_count_rna = pd.Series(_sum_axis(adata.X, 1), index=adata.obs_names)
```

In the combined primary workflow `adata.X` contains host **and** viral features, so `total_rna` includes the viral molecules the null is supposed to redistribute. Lareau's `nCount_RNA` is host-only because HHV-6 kite counts are stored in `so_filt@meta.data`, not the RNA assay — so ViralScan's "same algebra" is **not** the same denominator. In the two-step workflow (`host_filter` at `src/viralscan/Snakefile:85` → `kb_count` at `:137`) host reads are removed before quantification, so `sum(adata.X)` is host-depleted by construction and cannot serve as a host-depth null.

Additionally, `preprocessing()` reads `counts_unfiltered/adata.h5ad` (`kb_outputs.py:83`, `current_adata` at `:103`) and never subsets to called cells, so `super_expressor()` ranks **every droplet**, including empty ones. The roadmap says "every row of the provided AnnData"; the reality is broader and strengthens the case for a declared universe.

Two more verified rendering defects: `clip(lower=1e-1)` on observed counts (`:389`) manufactures pseudo-observations at 0.1, and `max_rank_display = 15000` (`:397`) silently truncates without annotation.

### 2.3 Coverage lines bridge uncovered viral bases — and the fix must not re-introduce an OOM

`src/viralscan/evidence.py:1512` docstring: *"Return covered depth points for plotting **without manufacturing zero depth**."* `plot_coverage_comparison()` (`:1527`) then calls `axis.plot` on those sparse positions, so a 1 kb uncovered interval between two islands is drawn as a continuous ramp.

**Critical constraint the roadmap missed.** `tests/test_evidence.py:34-49` deliberately locks the absence of `samtools depth -a`:

```python
# `samtools depth -a` printed every position of every host contig (~1-2 G lines,
# >230 GB RSS) for a plot that only draws covered points (DSR-02 evidence OOM).
assert "-a" not in seen[0]
```

The correct fix is therefore **not** to add `-a`. It is to materialise zeros only for the viral references being plotted, using `@SQ` lengths from `samtools view -H` (viral genomes are kilobases, not gigabases), or to insert explicit NaN breakpoints. The revised roadmap must state this explicitly; a careless implementer following "fill zeros across the true accession length" could regress the OOM fix.

The OOM guard was executed, not merely read: `tests/test_evidence.py` passed 69/69 at the audited commit, including `test_coverage_depth_points_does_not_scan_every_host_position`. Note also that `plot_coverage_comparison()`'s existing reference filter is a **global** OR (`explicit_classes` at `:1538`, filter at `:1549`): when any target/same-reporting-group/related/decoy reference exists, *every* reference — including host contigs — enters the plot. A per-reference viral predicate is therefore required before any densification in WP-2; reusing that boolean as-is would materialise host contigs.

### 2.4 `auto_evidence` excludes STAR-only and below-gate candidates — but the reason is structural, not an oversight

`src/viralscan/scripts/auto_evidence.py:28-42` skips `detected == False` rows and `alignment_only` rows. The docstring states the mechanism honestly: *"the evidence replay only sees reads in kallisto equivalence classes, so those rows would extract nothing."*

So R2 is not "remove an arbitrary filter". It is "add a second evidence path for a different data source". The roadmap is right that this is a genuine capability gap, but wrong to frame it as a small candidate-selection change. The smallest implementation is: keep the kallisto replay untouched, and for `alignment_only` candidates read the existing STAR anellovirus BAM directly, writing the same summary fields where computable and `not_assessed` elsewhere. No new schemas.

### 2.5 `soup_screen()` and `swap_check.py` already exist and are already honest

- `soup_screen()` (`detection.py:733`) implements the `rho = 1` Poisson upper bound, reports `soup_rejected_rho1` / `soup_sufficient`, and states in its own basis string that it *"does not show infection and a pass is not a clean result."*
- `scripts/swap_check.py` implements the pool-aware hypergeometric barcode-overlap test and its docstring already says `Tier 2 (a shared (CB, UMI) key in the BUS files) is not implemented.`

The roadmap's R3 recommendation is therefore correct in direction but should be **much smaller**: the only new mechanism justified is tier-2 (CB+UMI fingerprint) as an opt-in script extension, with an empirical collision null. Everything else is documentation.

### 2.6 `protocol.yaml` is still authorisation-closed (confirmed)

`analysis/v3_validation/protocol.yaml:6` `status: draft`; `:10-11` `training_execution_allowed: false`, `holdout_execution_allowed: false`. The `harmonization` block is separately `status: frozen` (`:59`) with a contract hash. The roadmap's R6 framing is correct; it must not be treated as an implementation package.

### 2.7 Documentation drift is real (confirmed)

`docs/plans/ambient-and-barcode-swapping-controls.md:3-5` still reads *"Status: design only ... No code, no tests, nothing run"* while `soup_screen()`, `scripts/swap_check.py`, `tests/test_ambient_screen.py` and `tests/test_swap_check.py` all exist in the same tree. This is a five-line doc fix, not a work package.

### 2.8 `origin/main` moved after the audit — the roadmap must acknowledge the new output layout

Seven commits sit on top of `78660933`, including **OUT-LAYOUT-01**: `combined_summary.tsv` at the run root, `layout_version` in `run_manifest.json`, and `count_audit.tsv` relocated into `results/`. Any new output (coverage map, review TSV) must be added to that layout and to `docs/output_reference.md`, and must not collide with `combined_summary.tsv` semantics. The roadmap as written predates this and is silent about it.

I verified that the material R0 defects are **unchanged** at `origin/main` (the `n_count_rna`, `clip`, and `max_rank_display` lines are untouched by the layout commit).

---

## 3. Confirmed bugs (source-verified)

| # | Bug | Evidence | Reproduces? | Severity |
|---|---|---|---|---|
| BUG-1 | Summary denominator excludes virus-negative called cells | `scripts/super_expressors.py:33-42`; `detection.py:1104`; test `tests/test_super_expressors.py:24-38` encodes 50 % over a 2-cell denominator | **Executed**: legacy path reports 4.0 % over 50, complete universe 0.2 % over 1,000 | **High** — a prevalence statement can be inflated by the ratio of called cells to virus-positive cells (up to 3 orders of magnitude in sparse libraries) |
| BUG-2 | PNG null uses `sum(adata.X)`, which includes viral features and is host-depleted in two-step runs | `detection.py:351`; two-step rules `Snakefile:85` (`host_filter`) and `:137` (`kb_count`) | Yes | **Moderate** — the grey null is mis-specified; conclusions about "concentration beyond depth" can be wrong in either direction |
| BUG-3 | PNG ranks every droplet in the unfiltered matrix | `kb_outputs.py:83,103`; `detection.py:201-262` returns full adata; `:348,395` use `adata.n_obs` | Yes | **Moderate** — an infection-prevalence-looking curve over droplets |
| BUG-4 | Zero viral counts clipped to 0.1 for plotting, unlabelled | `detection.py:389` | Yes | **Low** — visual; TSV absent, so no recoverable data |
| BUG-5 | 15,000-rank silent truncation | `detection.py:397-398` | Yes | **Low** — tail omitted without annotation |
| BUG-6 | Coverage lines bridge uncovered bases | `evidence.py:1527-1575` (`axis.plot` over sparse positions) | **Executed** (samtools 1.16.1): 10 nt reads at 5–14 and 900–909 leave no plotted point between 14 and 900; the line jumps straight across the 885 bp gap | **Moderate** — a reader can infer continuous coverage across a deletion/gap |
| BUG-7 | Header-only output loses the field list: `fields` is derived from `rows[0]`, so an empty result writes only `dataset`/`sample` | `scripts/super_expressors.py:86-88` | **Executed**: exit 0, output is exactly `dataset\tsample\n` | **Low** — a zero-virus run produces a two-column header that no consumer can parse as the summary schema |
| BUG-8 | `scripts/super_expressors.py` not in the local checkout | `5e551c9` tree; file added at `0f0d27e` (2026-10-15) | N/A | **Process** — agents must work from `origin/main` or the audit worktree |

Bug IDs are `BUG-n` deliberately: the roadmap reserves bare `B1`–`B4` for the WP-2 acceptance fixtures.

Note on BUG-7: the crash hypothesis was **wrong** and is retracted. `main()` guards the `rows[0]` lookup with `(rows[0] if rows else {})`, so a zero-virus library exits 0; the defect is that the header degrades to `dataset\tsample` instead of the full field list. The fix is the explicit field list already required by WP-1.1.

---

## 4. Misdiagnosed or imprecise recommendations

| Roadmap claim | Assessment | Correction |
|---|---|---|
| "Two distinct SuperExpressor implementations … their cell universes and metrics can disagree" | Correct, but the framing implies equal standing | The summary script is a **manual analysis tool** (`PLAN.md:6504`), not a pipeline stage. Fix the default; do not build a framework to unify them. |
| "Implement one shared pure calculation/data contract" | Over-engineered for two callers with different inputs and outputs | Share only **denominator resolution** and a **host-depth helper**. A shared "rank_viral_burden" layer is premature. |
| "The PNG uses every row of the provided AnnData" | Understated | It uses the **unfiltered** matrix (all droplets), because `preprocessing()` never subsets. |
| "Require `--cells` in methods-grade runs" | Correct but insufficient | Fail closed by default: resolve `results/called_cells.tsv` from the run directory; raise when unresolvable. |
| R2 "candidate-complete" implies removing an arbitrary restriction | Misdiagnosed mechanism | The restriction is structural: kallisto EC replay cannot see STAR-only reads. A **second evidence source** is required, not a wider selector. |
| R2 proposes three new TSV schemas | Not justified by a demonstrated consumer | One `evidence_review.tsv` (sample × taxon) reusing existing per-target artifacts; defer the per-cell ledger and junction TSV. |
| R1 proposes pyGenomeTracks as "phase 2" | Unnecessary in the roadmap | Remove from the roadmap entirely; record as a future option. Matplotlib + existing BAMs + accession-matched GTF is sufficient. |
| R1 "construct the complete `1..L` position domain" | Correct, but omits the OOM constraint | Must fill zeros **per plotted viral reference from `@SQ` lengths**, never with `samtools depth -a` (`tests/test_evidence.py:34-49`). |
| R3 tier-2 "conditional molecule fingerprints" | Feasible but under-specified | BUS files are retained in the run directory (`kb_outputs.py:47-70`), so CB+UMI comparison is feasible. Insert confirmation requires BAMs. State this. |
| R4 "search the three linked STAR filtering parameters as a joint grid" | Reasonable, but open-ended | Must be pre-registered with a fixed grid and a stop rule; the roadmap says this, but the acceptance criterion ("supports the specific filter/default decision") is not falsifiable as written. |
| R5 transcription/junction evidence | Correctly qualified in prose, but listed as a work package | **Defer out of the release path.** No curated junction reference exists in the repo; `spliced()` is `"N" in self.cigar` (`src/viralscan/anello_align.py:438-439`). |
| R7 host-response additions | Mostly already implemented | `src/viralscan/scripts/hostresponse.py` already has depth-alone AUC (`:787`, `_depth_alone_auc`) and donor-like detection (`:125-126`, `_DONOR_LIKE`); `src/viralscan/scripts/umap.py` already tests in host-only PCA (`:120` helper, `:328` call). Only wording remains. |
| "No numerical changes" is the invariant for core molecules | Correct and important | Retain. The corrected *derived percentage* may change and must be ledgered. |

---

## 5. Existing functionality the roadmap overlooks or under-credits

1. **`results/called_cells.tsv` already exists** (`cellcalling.py:685-695`) and `load_called_mask()` (`:698`) already resolves it with a fail-closed namespace check. R0's fix needs no new cell-universe machinery.
2. **`identity.viral_gene_ids()` already provides the viral/host partition** used by multimapping, so host-only depth is a one-line mask away.
3. **`tests/test_evidence.py` already locks the DSR-02 memory behaviour**, which constrains the R1 fix.
4. **`soup_screen()` already emits `ambient_basis` text** that says a pass is not clean; R3's "honest ambient uncertainty" is largely present.
5. **`swap_check.py` already has the pool/whitelist comparison and hypergeometric null**; only tier-2 is missing.
6. **`src/viralscan/scripts/hostresponse.py` already implements** depth-only AUC (`:787`), group-disjoint CV, and donor-like column detection (`:125-126`).
7. **`umap.py` already separates the test space from the display space** (host-only PCA for the enrichment test at `:328`).
8. **`docs/output_reference.md:964` already documents** `coverage.raw.tsv` / `coverage.deduplicated.tsv`, so the coverage-map provenance should extend that section rather than create a parallel documentation tree.
9. **`evidence_run.py:619` already writes** `coverage.raw_vs_deduplicated.png`; the bug fix belongs there, not in a new module.

---

## 6. Features to remove from the roadmap

| Feature | Why remove |
|---|---|
| R1 Phase 2 (pyGenomeTracks/bigWig backend) | Adds a heavy optional dependency for a visual style; no scientific capability. Record as a future option only. |
| R2 per-cell evidence ledger (`anellovirus_cell_evidence.tsv.gz`) | No current consumer; cell-level attribution is `not_assessed` for most sources anyway. Defer. |
| R2 junction TSV schema | Depends on annotations that do not exist in the repo. Belongs to the deferred R5 item. |
| R5 as a release work package | Cannot be validated with available data; `spliced()` is a raw CIGAR flag. Defer to research. |
| SE-04 Poisson envelope | Optional; the roadmap already says non-blocking. Keep out of the release PRs. |
| A shared "pure calculation layer" framework | Two callers with different inputs. Share two small helpers instead. |
| R6 as an implementation package | It is a governance gate, not code. Must not be scheduled as agent work. |

---

## 7. Recommendations: retain, simplify, deepen

**Retain (unchanged):**
- Count/detection immutability as an explicit contract.
- `--cells` as the authoritative denominator input, now with automatic run-directory resolution and fail-closed behaviour.
- Opt-in-only diagnostics; no default DAG change.
- No ambient subtraction, no alternative quantifier, no threshold changes.
- The evidence-versus-inference separation and the `not_assessed` vocabulary.
- The v3 freeze; no holdout inspection.

**Simplify:**
- R0 → two small code changes + tests, not a shared calculation framework.
- R1 → split into a bug fix (zeros/breaks in the existing plot) and a separate opt-in coverage-map feature.
- R2 → one summary TSV, one new evidence source (STAR BAM), no new schemas.
- R3 → tier-2 only, as an extension to the existing script; everything else is documentation.
- R7 → wording only.

**Deepen (where it changes scientific meaning):**
- Make the SuperExpressor PNG's universe, host-depth provenance, threshold semantics and truncation **visible in the figure and in a machine-readable sidecar**. This is the highest-value change in the whole roadmap because it prevents a confident but wrong prevalence claim.
- Make the coverage plot's zeros real, because a gap is biological information.
- Make missing inputs (`called_cells.tsv`, host depth, BUS files, GTF) produce explicit statuses, never plausible numbers.

---

## 8. Evidence matrix

Legend — **Severity**: Critical/High/Moderate/Low. **Confidence**: Verified / Partially verified / Hypothesis. No severity of Critical or High is assigned without a stated consequence.

| Proposal | Actual implementation | Evidence (file:line, audited tree `78660933`) | Severity | Scientific impact if unfixed | Existing solution | Decision | Smallest adequate change | Tests | Dependencies | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|
| R0: summary default denominator | `universe = called` where `called` = virus-positive called barcodes from `per_cell_viral.tsv` | `scripts/super_expressors.py:33-42`, `:56`; `detection.py:1104`; `tests/test_super_expressors.py:24-38` | **High** | Prevalence can be inflated by (called cells / virus-positive called cells); e.g. 4 % vs 0.2 % | `--cells` already correct | **Keep (simplify)** | Resolve `results/called_cells.tsv` from the run dir; raise if unresolvable; keep `--cells`; explicit legacy flag | 1000/50/2 → 0.2 %; zero-positive library; missing called file raises; legacy flag warns | none | Verified |
| R0: PNG host-depth null | `n_count_rna = sum(adata.X)` | `detection.py:351`; two-step rules `Snakefile:85,137`; Lareau stores HHV6 in metadata | **High** | A null that includes viral counts can make concentration look expected (or not) incorrectly | `identity.viral_gene_ids()` | **Keep** | Host-only mask; two-step → `null_not_estimable` | Host-only sum asserted; two-step → not_estimable | identity table | Verified |
| R0: PNG cell universe | Full unfiltered adata, all droplets | `kb_outputs.py:83,103`; `detection.py:201-262,348,395` | **High** | A prevalence-looking curve over empty droplets | `load_called_mask()` (resolver, not called from `detection.py`) | **Keep** | Pass the in-memory `called_mask` that `main()` computes (do not call `load_called_mask()` here — it would recompute); declare `n_universe`, `n_plotted` | Universe test; non-called barcodes excluded from prevalence | cellcalling | Verified |
| R0: zero clipping / truncation | `clip(1e-1)`; `max_rank_display=15000` | `detection.py:389,397-398` | **Low** | Visual ambiguity; unrecoverable data | none | **Keep (small)** | Plot-data TSV with true zeros; documented floor; annotate/remove truncation | 0-UMI cell in TSV; 60 000-cell run records `n_universe=60000`, `n_plotted=50000` | none | Verified |
| R1: coverage bridging | `samtools depth` covered positions; `axis.plot` | `evidence.py:1512,1527-1575`; deliberate OOM guard `tests/test_evidence.py:34-49` | **Moderate** | Reader infers continuous coverage across an uncovered interval | `@SQ` lengths | **Keep (split out)** | Fill zeros per viral reference from `@SQ`; NaN breaks; no `-a` | 1 nt reads at 5/900 of a 1,000 nt reference → plotted zeros at 6–899; OOM test still passes | none | Verified (executed) |
| R1: coverage map feature | Existing plot only; no genome/gene figure | `evidence.py`; `anellovirus.py:190-212`; `evidence_run.py:522,557-568,619`; CLI `parsers.py:386` | **Low** (feature) | No incorrect conclusion caused by absence; usability gap | matplotlib + existing BAMs | **Keep (opt-in, reduced)** | `evidence-plot --coverage-map`; raw/dedup/gene tracks; PNG+PDF+JSON; no pyGenomeTracks | Gap, mismatch, missing GTF, zero coverage, multi-accession | R1 bug fix | Verified |
| R1: transcript vs genome coordinates | `gtf_text_for()` emits CDS or whole-genome placeholder | `anellovirus.py:16-17,37-44,190-212` | **Moderate** | Misleading annotation overlay | existing identity/length metadata | **Keep** | Explicit label + length check; refuse mismatch | Length-mismatch raises; placeholder labelled | none | Verified |
| R2: candidate coverage | `anello_genera()` skips below-gate and `alignment_only` | `auto_evidence.py:28-42`; `reads.py:70` | **Moderate** | STAR-rescued candidates never get read-level review | existing STAR BAMs; `evidence_run.py` | **Simplify** | `--review-candidates`: include `alignment_only` via direct BAM evidence; one `evidence_review.tsv` | 0-kallisto/STAR-positive appears; no promotion of `detected` | R2 config flag | Verified |
| R2: three new schemas | not implemented | roadmap proposal | **Low** | Complexity without consumer | existing per-target artifacts | **Remove** | one summary TSV only | — | — | Verified |
| R3: soup | `soup_screen()` rho=1 bound, descriptive | `detection.py:733-780`; `tests/test_ambient_screen.py` | **Low** | Already honest; risk is over-reading | existing | **Keep as docs** | Report basis text in docs; no code | existing | none | Verified |
| R3: tier-2 fingerprint | Tier 2 explicitly not implemented | `scripts/swap_check.py:34`; BUS paths `kb_outputs.py:46-70` — note `corrected_bus` is `kb-python/output.corrected.bus` (corrected runs only); `resolved_bus` (`kb-python/output.resolved.sorted.bus`) is the canonical v3 artifact | **Moderate** | Cross-library leakage can go undetected beyond barcode overlap | existing tier-1 | **Simplify (opt-in)** | `--tier2` CB+UMI match + empirical null; NA without BUS | planted shared CB+UMI; unrelated pools excluded; no count change | retained BUS | Verified |
| R4: anellovirus calibration | plant/report machinery exists; STAR opt-in | `scripts/plant_anello_10x.py`, `scripts/anello_acceptance_report.py`, `Snakefile:109` | **Moderate** | Divergent-strain recall unquantified | existing fixtures | **Keep as deferred experiment** | Pre-registered grid; training-only; no default change | Pre-registration + stratum reporting | freeze authorisation | Verified |
| R5: junction evidence | `spliced()` = `"N" in cigar` | `src/viralscan/anello_align.py:438-439` (the module; `src/viralscan/scripts/anello_align.py` is the separate Snakemake driver) | **Low** (for release) | Premature transcription claims if shipped | none | **Defer** | No code; keep diagnostic flag as-is | — | curated annotations (absent) | Verified |
| R6: v3 validation | draft; training/holdout disabled | `protocol.yaml:6,10-11`; harmonization frozen `:59` | **Critical (claim gate)** | Any performance claim without it is unsupported | freeze process | **Reclassify as gate** | No code; claim registry wording only | — | authorisation | Verified |
| R7: host response | depth AUC, group CV, donor detection, host-only test space | `src/viralscan/scripts/hostresponse.py:787,125-126`; `src/viralscan/scripts/umap.py:120,328` | **Low** | Over-reading already guarded | existing | **Keep as wording** | Labels only | existing | none | Verified |
| Docs drift | "design only" while code exists | `docs/plans/ambient-and-barcode-swapping-controls.md:3-5` | **Low** | Duplicate work / false status | source | **Keep (5-line fix)** | Update status paragraph | docs check | none | Verified |
| Output layout | `origin/main` adds `combined_summary.tsv`, `layout_version` | `origin/main:8933a65` | **Low** | New outputs land outside the documented layout | existing docs | **Keep (integration)** | Add new files to layout + output_reference | docs/inventory test | origin/main | Verified |

### 8.1 Separating confirmed defects from potential improvements

**Confirmed defects (evidence above):** BUG-1, BUG-2, BUG-3, BUG-4, BUG-5, BUG-6, BUG-7, docs drift, output-layout omission.
**Potential improvements (not defects):** coverage-map figure, tier-2 fingerprint, candidate-complete review, anellovirus calibration, host-response wording.
**Rejected:** ambient subtraction, CellSweep, alternative quantifier, default STAR promotion, threshold changes, pyGenomeTracks, three-schema expansion.

---

## 9. Original versus revised scoring

Scores are 1–5; the revised column scores **the roadmap in this review's revised form**, not an implemented product.

| Criterion | Original | Revised | Reasoning |
|---|---|---|---|
| **Scientific validity** | 4.0 | **5.0** | Original correctly separates evidence from inference and refuses unsupported claims. Revised removes R5's unvalidatable junction promises and makes missing-input statuses explicit, closing the remaining over-reach. |
| **Source-code grounding** | 4.0 | **5.0** | Nearly every original claim verified. Deductions: the "every row of provided AnnData" understatement; the manual-script framing; the missing DSR-02 OOM constraint; silence on `origin/main`'s layout change. Revised pins file:line and states constraints. |
| **Architectural simplicity** | 3.0 | **4.5** | Original proposed a shared calculation layer, three new schemas and an optional heavy renderer. Revised shares two helpers, one summary TSV, zero new dependencies. Residual: two SuperExpressor code paths still exist; unification is deliberately not attempted. |
| **Scope discipline** | 2.5 | **5.0** | Original retained seven packages including a speculative transcript programme. Revised ships five, defers two, and reclassifies one as a gate. |
| **Implementation feasibility** | 3.5 | **4.5** | Original underestimated R2's evidence-source change and R3's BUS handling. Revised scopes each to a single file/function with bounded tests. Residual: WP-4 depends on the STAR BAM layout being stable; verified by reading, not execution. |
| **Regression safety** | 4.5 | **5.0** | Original's count-immutability contract is excellent and retained verbatim. Revised adds an explicit "no `samtools depth -a`" guard and parity tests for `detected`. |
| **Validation quality** | 3.5 | **4.5** | Original has strong falsifiable cases but several non-automatable criteria ("a correct scPathoQuant-like map"). Revised converts these to fixture-level assertions. Residual: no real-data benchmark is runnable inside this review. |
| **User experience** | 3.5 | **4.5** | Original improves honesty but adds decisions. Revised keeps a single default path that is safe, with opt-in extras; the figure itself carries provenance and the "candidate evidence" qualifier. |
| **Maintainability** | 3.5 | **4.5** | Fewer schemas, no new dependencies, existing helpers reused. Residual: two plot code paths remain by design. |
| **Prioritisation** | 4.0 | **5.0** | Original's R0-first is right; revised additionally promotes the coverage gap fix ahead of the feature, and removes R6 from the queue. |

**Aggregate:** original 3.60 / 5; revised 4.75 / 5. **Unresolved deficiencies are stated in §10.**

---

## 10. Remaining limitations and uncertainties

1. **Test coverage.** The five review files (137 tests) and the coverage path were executed. A full-suite run at `78660933` with samtools present gives **5787 passed, 70 failed, 41 skipped** (163 deselected). All 70 failures are environment defects, not review findings: 59 in `tests/test_hostresponse*.py` and 5 in `tests/test_umap.py` share `ValueError: unknown attr 'nocapture'` from a numba/llvmlite mismatch in the shared conda environment; 6 in `tests/test_release_static.py` fail because the test subprocess has no `python` on `PATH`. A Sphinx HTML build of the local tree with the `reviews/**` exclusion applied succeeds (27 pages) and emits **no** `docs/reviews` page; its only warning is the pre-existing `notices/CAT-30_retraction_DRAFT.md` toctree warning. No end-to-end workflow run and no real-data run were performed. The coverage-map feature (WP-3) does not exist yet, so its acceptance criteria remain unexecuted.
2. **No real-data validation** was performed. The denominator error's real-world magnitude depends on the called-cell/virus-positive ratio per library; the 4 % vs 0.2 % example is arithmetic, not a measured dataset.
3. **Two-step host-depth behaviour is derived, not measured.** I verified the architecture (`host_filter` → `kb_count`) and that host reads are removed before quantification; I did not run a two-step library to observe the host-depleted matrix.
4. **BUG-7 was executed and the crash hypothesis retracted.** A zero-virus library exits 0 and writes a two-column header; there is no traceback. Only the header degradation is real.
5. **The historical "held-out divergence condition failed"** claim in the roadmap is **Unverified**. It is plausible and consistent with `anello_align` being opt-in, but I did not find the run record in this inspection.
6. **R3 tier-2 feasibility** assumes BUS files remain in completed run directories (`kb_outputs.py:46-70` defines the paths). I verified the path definitions, not that a given production run retained the files. Prefer `resolved_bus` (`kb-python/output.resolved.sorted.bus`, written whenever v3 counting ran) over `corrected_bus` (`kb-python/output.corrected.bus`, corrected runs only): the revised roadmap originally named the latter with a wrong directory.
7. **The revised roadmap's WP-4** depends on the STAR anellovirus BAM (`Aligned.sortedByCoord.out.bam`) exposing barcode tags compatible with the evidence summary. The roadmap asserts this; I verified the rule exists (`Snakefile:109`) and the alignment module reads barcodes, not that every field the summary needs is populated.
8. **Scoring is judgement**, not measurement. The revised scores assume the work packages are implemented and tested as specified; they are not a claim that the current package already meets them.
9. **The local checkout is stale.** All implementation must start from `origin/main` (`9151da9`) or the audit worktree at `78660933`; the local `5e551c9` tree lacks `scripts/super_expressors.py` and 238 commits of main.
