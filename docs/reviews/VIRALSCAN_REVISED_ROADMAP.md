# ViralScan — Revised Roadmap (Independent Review, Round 3)

**Date:** 20 October 2026
**Supersedes:** R0–R7 in `ViralScan_refined_roadmap_round2.md` (supplied with the review request; not committed to this repository)
**Baseline:** `origin/main` = `9151da9`; audited defect state = `78660933`
**Implementation tree rule:** start from `origin/main` or the audit worktree at `78660933`. The local checkout `5e551c9` is 238 commits behind and lacks `scripts/super_expressors.py`.

**What changed from round 2.** R0 is retained but reduced to two small code changes; R1 is split into a bug fix and a feature; R2 is reduced to one new evidence source and one summary file; R3 is reduced to tier-2 only; R5 is deferred out of the release path; R6 is reclassified from a work package to a governance gate; R7 is reduced to wording. Nothing was removed without recording where it went (§9).

---

## 1. Governing contracts (unchanged from round 2, restated for implementers)

1. **Primary count immutability.** `adata.X`, corrected CB–UMI accounting, selected allocation layers, `detected`, and canonical denominators do not change. Derived display statistics may change when demonstrably wrong; every such change is led in release notes and tests.
2. **Evidence vs inference.** Sequence detection, unique-molecule evidence, cell-associated signal, transcription support, and productive infection are separate. No promotion across axes.
3. **No pseudo-independence.** Competitive realignment of the same read is specificity evidence, not an independent replicate.
4. **Library namespace.** Every barcode comparison is within a declared sample/GEM-well/pool namespace.
5. **Missing means not assessed.** Missing host depth, BUS, GTF, or pool manifest yields `not_estimable` / `not_assessed`, never zero or a plausible number. A missing `called_cells.tsv` is a **hard error** for the summary script (it cannot report prevalence over the virus-positive subset); the plot path uses the run's in-memory mask (contract 13).
6. **One origin, multiple evidence streams.** Kallisto molecules, STAR reads, raw reads and representatives are reported side by side, never summed.
7. **Preserve zero-viral cells.** Percentages, ranks and nulls are computed over the complete called-cell set, then left-joined to sparse virus-positive counts with true zeros.
8. **No assay overreach.** Droplet 3′/5′ human scRNA-seq only. Flex/spatial/nuclei/bulk/long-read are out of scope.
9. **Reproducible additions.** No new mandatory dependency; no default DAG change; opt-in plots and diagnostics.
10. **Respect the freeze.** `analysis/v3_validation/protocol.yaml` governs authorisation. No training or holdout execution without the freeze conditions.

**New in this revision:**

11. **No `samtools depth -a`.** The absence of `-a` is a deliberate OOM fix locked by `tests/test_evidence.py:34-49`. Zero-filling must be per plotted viral reference from `@SQ` lengths.
12. **Output-layout integration.** New run-directory outputs are added to the layout introduced by OUT-LAYOUT-01 (`combined_summary.tsv`, `layout_version`) and documented in `docs/output_reference.md`.
13. **Called-cell provenance.** The SuperExpressor plot uses the in-memory `called_mask` that `main()` already passes to `compute_stats()`, after `results/called_cells.tsv` has been written (`detection.py:2185`). It must **not** call `load_called_mask()`: that helper recomputes cells when the file is absent, so the figure's universe could silently differ from the run's detection denominator. `load_called_mask()` remains the resolver for `gene_programs.py`, which runs as a separate step.
14. **Line numbers refer to `78660933`.** Resolve cited symbols by name (`rg`) on `origin/main`; the `detection.py` lines cited here are unchanged at `9151da9`, but that is not a general guarantee.

---

## 2. Goals and non-goals

### Goals

- G1. Any reported SuperExpressor percentage is computed over the complete called-cell set, or the tool refuses to report it.
- G2. The SuperExpressor null uses host-only depth, matched to the same barcodes and the declared cell universe; when host depth is unavailable, the null is `not_estimable`.
- G3. Coverage plots show true zeros across uncovered viral bases, including the existing `coverage.raw_vs_deduplicated.png`.
- G4. A researcher can produce an accession-matched coverage-and-gene figure from existing evidence BAMs, with no new aligner and no new heavy dependency.
- G5. A candidate discovered by STAR rescue or below the kallisto gate can receive read-level review, labelled by evidence source.
- G6. Cross-library leakage can be probed at the molecule level in declared pools, without changing any count.
- G7. Missing inputs are visible as statuses, not as clean negatives or plausible fractions.
- G8. The v3 validation gate remains closed and unaccelerated.

### Non-goals (explicit)

- N1. General-purpose ambient viral RNA subtraction; CellSweep.
- N2. A new universal viral quantifier or aligner.
- N3. Changing `detected`, allocation weights, or thresholds.
- N4. Quantifying or validating assay types outside droplet scRNA-seq.
- N5. Whole-genome or transcriptome assembly; de novo virus discovery.
- N6. Productive-infection or reactivation claims from expression alone.
- N7. A curated viral splice-junction reference in this release.
- N8. pyGenomeTracks/bigWig rendering or any new mandatory plotting dependency.
- N9. Any training or holdout execution against the v3 protocol.
- N10. Rewriting the Snakemake core into new pipelines; all additions are opt-in scripts or subcommands.

---

## 3. Final prioritised work packages

| WP | Title | Class | Ship order | Gate |
|---|---|---|---|---|
| **WP-1** | SuperExpressor denominator, host-depth null, and figure provenance | **Release-critical correctness** | 1 | Parity with `detected`; 0.2 % fixture |
| **WP-2** | Coverage-plot zero gaps (bug fix) | **Release-critical truthfulness** | 1 (parallel to WP-1) | OOM test still passes |
| **WP-3** | Accession coverage map with gene track | Opt-in feature | 2 | Coordinate/length validation |
| **WP-4** | Candidate-complete evidence review (one new source, one summary) | Opt-in diagnostic | 3 | No promotion of `detected` |
| **WP-5** | Tier-2 molecule fingerprint across declared pools | Opt-in diagnostic | 3 | Empirical null; counts immutable |
| **WP-6** | Anellovirus capturability / STAR calibration | Deferred HPC experiment | after freeze | Pre-registered grid; training only |
| **WP-7** | v3 scientific validation | **Governance gate (not code)** | blocked | Signed freeze + authorisation |
| **WP-8** | Junction/transcription evidence | Deferred research | not in release | Curated annotations required |
| **WP-9** | Documentation, wording, stale-status reconciliation | Routine | with each PR | Docs tests |

### Dependency graph

```
WP-2 ──> WP-3                    (WP-3 reuses the zero-fill helper)
WP-1, WP-2, WP-4, WP-5 ──> WP-9  (docs land with/after each PR)
WP-7 ──> WP-6                    (freeze authorisation precedes calibration)
WP-7 ──> blocks any performance claim
WP-8                             (needs curated junction annotations; not present)
```

WP-1 and WP-2 may ship in either order and in parallel. WP-3 depends only on the WP-2 helper. WP-4 and WP-5 are independent of everything except the base tree. WP-6 cannot start without the freeze. WP-8 is not scheduled.

---

## 4. Work package specifications

### WP-1 — SuperExpressor denominator, null, and provenance

**Affected files**

| File | Function | Change |
|---|---|---|
| `scripts/super_expressors.py` | `summarise()` (30–67), `main()` (70–94) | Denominator resolution; fail-closed; legacy flag; provenance column; zero-virus behaviour |
| `src/viralscan/scripts/detection.py` | `super_expressor()` (331–455) | Host-only depth; called-cell universe; zeros preserved; truncation annotated; sidecar TSV/JSON |
| `src/viralscan/scripts/detection.py` | `preprocessing()` (201–262) / `main()` (2110–2415) | Pass identity + the in-memory called mask into `super_expressor()`; move the plot loop after `write_called_cells()` (`:2185`) |
| `tests/test_super_expressors.py` | existing | Replace the defect-encoding assertion |
| `tests/test_detection_audit_s2.py` | `TestSuperExpressorInputs` (`:82-101`) | Existing plot tests must keep passing: zero-cell error, no adata mutation, docstring rule |
| `tests/test_super_expressor_plot.py` | new | Plot-path unit tests |
| `docs/output_reference.md` | SuperExpressor section | Document TSV/JSON/provenance |

**WP-1.1 — Summary denominator (`scripts/super_expressors.py`)**

Resolution order in `main()`:
1. `--cells PATH` if supplied (highest precedence).
2. Else derive the run directory from `--per-cell-viral`: if the path is `<run>/results/per_cell_viral.tsv` and `<run>/results/called_cells.tsv` exists, use it.
3. Else **raise** `SystemExit` with an actionable message naming both files and stating that the virus-positive subset is not a prevalence denominator.

Add `--denominator {called_cells,viral_positive_called}` defaulting to `called_cells`.
`viral_positive_called` reproduces the old behaviour, prints one WARNING, and writes `denominator_kind=viral_positive_called` into every row so a table cannot be mistaken for prevalence.

Add `denominator_kind` as the **last** column; `n_cells` already exists and keeps its meaning (the denominator size). Replace the `rows[0]`-derived header with a module-level ordered `SUMMARY_FIELDS` constant so the header is identical for zero, one, or many viruses. The current order is `dataset, sample, virus, n_cells, n_cells_viral_umi, min_umi, n_super_expressors, pct_cells_super, viral_molecules, viral_molecules_in_super, share_molecules_in_super, max_viral_per_10k, n_ge_3, n_ge_5, n_ge_10, n_ge_50`, then `denominator_kind`.

Zero-virus behaviour: when `by_virus` is empty, write that full header and exit 0; do not index `rows[0]`. (At the audited commit this path exits 0 but emits only `dataset`/`sample` — BUG-7 in the review.)

Fractional allocations: `n_super_expressors` counts `>= min_umi` on the stored float; do not round. Document this.

**WP-1.2 — PNG host-depth null and universe (`detection.py::super_expressor`)**

Signature becomes:

```python
def super_expressor(adata, virus, viral_gene_ids, outputpath,
                    viral_count_matrix=None, *, host_gene_mask=None, called_mask=None):
```

- `host_gene_mask`: boolean over `adata.var_names` selecting host features. Computed by the caller from `identity.viral_gene_ids()` (`~adata.var_names.isin(all_viral_ids)`), **all** viral genes, not only this virus's. In the legacy `identity is None` path, flatten `index_groups` values (`{g for genes in index_groups.values() for g in genes}`); `set(index_groups)` is a set of **virus names**, not gene IDs.
- `called_mask`: boolean over `adata.obs_names`, the mask `main()` computes for cell calling and passes to `compute_stats()` (`compute_stats()` at `detection.py:871`; mask assigned in `main()` around `:2167`). Move the `if config.visual:` plot loop from `:2124-2132` to immediately after `write_called_cells(adata.obs_names, called_mask, outputpath)` (`:2185`), so the mask is in memory and `results/called_cells.tsv` is already written. Do **not** call `load_called_mask()` here (contract 13); it is not imported by `detection.py` and would recompute cells when the file is absent.
- `n_count_rna = _sum_axis(adata.X[:, host_gene_mask], 1)`.
- **Subset before summing.** Apply the universe to both vectors before computing totals: `viral_umi = viral_umi[universe]`, `n_count_rna = n_count_rna[universe]`; then `total_viral = viral_umi.sum()`, `total_rna = n_count_rna.sum()`, and `null_model = total_viral * (n_count_rna / total_rna)`. Filtering only at plot time would leave empty droplets in the null.
- `n_high_burden = int((viral_umi >= se_threshold).sum())` is computed over the universe; the title reports `n=<n_universe>` and that count, not `adata.n_obs`.
- If `host_gene_mask is None` or `total_rna == 0` (two-step host-depleted matrix), set `null_status = "not_estimable"`, do not draw the null, and print the status in the figure subtitle.
- Restrict the plotted/ranked universe to `called_mask`. Report `n_universe`, `n_plotted`, `n_high_burden`, `n_zero`.
- Keep `viral_umi` unchanged in definition (selected count layer).
- Write `plots/SuperExpressor_<virus>.tsv` with columns `barcode, viral_molecules, host_molecules, is_called, null_expected, rank_observed, rank_null`. True zeros are written as zeros.
- Write `plots/SuperExpressor_<virus>.json` with: sample, virus, count layer, `se_threshold`, `null_status`, `denominator_kind`, `n_universe`, `n_plotted`, `n_zero`, `n_high_burden`, `display_floor`, `max_rank_display` (or `null` if untruncated), git SHA, host-gene source (`identity` vs legacy `index_groups`), called-cells source and SHA-256.
- Figure: keep the filename `plots/SuperExpressor_<virus>.png`. A display floor (e.g. `0.5`) applies **only** to the figure and must never modify the TSV. Because `clip(lower=0.5)` also maps legitimate fractional values (e.g. 0.3) to 0.5, label it `"values ≤ 0.5 drawn at 0.5 (log scale); exact values in the TSV"` — not "0 values shown at 0.5". If `n_universe > 50 000`, truncate the ranked tail at rank 50 000 **in the figure only** (the TSV keeps every cell in the universe; do not randomly subsample ranks), annotate `"showing ranks 1–50000 of N"`, and record `n_plotted` vs `n_universe`; never silently slice.
- Title/labels: `"Viral molecule concentration across called cells"`, `"≥ X allocated molecules (exploratory high-burden cutoff)"`. No "infected"/"reactivated".
- Optional `--superexpressor-lareau` parity mode is out of scope for this WP.

**Tests**

1. 1,000 called cells, 50 virus-positive, 2 ≥ 10 → `pct_cells_super == 0.2`.
2. Zero-virus library → full header (all `SUMMARY_FIELDS`), no data rows, exit 0, no traceback.
3. Unresolvable called-cell file → non-zero exit with a message naming `results/called_cells.tsv`.
4. `--denominator viral_positive_called` → reproduces 4.0 % and warns; `denominator_kind` present.
5. Fractional 9.6 does not count as ≥ 10; 10.0 does.
6. Plot path: host-only sum excludes viral features (construct a matrix where host and viral totals differ and assert the null uses host).
7. Plot path: two-step (zero host depth) → `null_status == "not_estimable"`.
8. Plot path: non-called barcode with massive viral counts is excluded from prevalence.
9. Plot path: zeros present in TSV; `n_zero` correct.
10. Plot path: 60,000 called cells → `n_universe=60000`, `n_plotted=50000`, `max_rank_display=50000`, figure annotation present, TSV has 60,000 rows.
11. **Parity:** `viral_summary.tsv` and `detected` are byte-identical before/after for a fixture run.

**Acceptance:** all tests pass; a reader of the PNG + JSON can state the denominator, the null provenance and the truncation; no core count field changes.

---

### WP-2 — Coverage-plot zero gaps (bug fix)

**Affected files**

| File | Function | Change |
|---|---|---|
| `src/viralscan/evidence.py` | new `reference_lengths(bam)` | Parse `samtools view -H` `@SQ SN:… LN:…` |
| `src/viralscan/evidence.py` | `plot_coverage_comparison()` (1527–1575) | Reindex each viral reference onto `1..L` with zeros; NaN breaks for unknown lengths |
| `tests/test_evidence.py` | existing | Add gap fixtures; keep the OOM test unchanged |

**Rules**

- Do **not** modify `coverage_depth_points()` and do **not** add `-a` to `_SAMTOOLS_DEPTH_POLICY`.
- Materialise the full domain only for **viral** references, decided per reference. The existing filter is a **global** OR (`explicit_classes or reference.startswith("VIRUS|")`, `evidence.py:1538-1549`): as soon as any target/same-reporting-group/related/decoy reference exists, every reference — including host contigs — enters the plot. Do not reuse that boolean as the densification predicate. Define `is_viral_reference(ref)` (prefix `VIRUS|`, or an explicit competitor class) and use it per reference. `reference_class()` defaults to `"virus"` for unprefixed ids (`:830-833`), so it cannot be the predicate either.
- If a reference length exceeds 5,000,000 bp, use NaN breakpoints instead of a dense array.
- Keep output filename `coverage.raw_vs_deduplicated.png`.
- Do not change `coverage.raw.tsv` / `coverage.deduplicated.tsv`.

**Tests**

1. Synthetic BAM: `@SQ LN:1000`, **1 nt (`1M`)** reads — two at position 5 (depth 2) and one at 900 (depth 1). `samtools depth` then emits only 5 and 900, so the plot array must have zeros at 6–899. State the read length in the fixture: with `10M` reads the first read covers 5–14 and the uncovered interval is 15–899, which is a different assertion.
2. Mixed BAM: one target-classified viral reference plus a host contig → only the viral reference is densified, and the host contig yields no dense array (`is_viral_reference`, not the global `explicit_classes` boolean).
3. Existing `test_coverage_depth_points_does_not_scan_every_host_position` still passes.
4. Empty BAM → `"No aligned coverage"` text unchanged.

**Acceptance:** a 1 kb gap is visibly zero, not a ramp; memory bounded by viral genome lengths.

---

### WP-3 — Accession coverage map with gene track (opt-in)

**Affected files**

| File | Change |
|---|---|
| `src/viralscan/evidence.py` | New `coverage_map_figure(...)` beside `plot_coverage_comparison` |
| `src/viralscan/evidence.py` | New `resolve_reference_annotation(...)` (contig match, length check, strand) |
| `src/viralscan/cli/parsers.py` | `evidence-plot` gains `--coverage-map`, `--target`, `--annotation` |
| `src/viralscan/scripts/evidence_run.py` | Optional post-alignment invocation; no default DAG change |
| `docs/output_reference.md` | New file block |
| `tests/test_coverage_map.py` | New |

**Inputs**

- Existing `competitive_reads.raw.bam`, `competitive_reads.<mode>_dedup.bam`.
- Optional GTF: either a user file or `anellovirus.gtf_text_for()` output; `--annotation` may be omitted.
- Target: exactly one accession or gene ID; if omitted and exactly one viral reference exists in the BAM, select it; otherwise require `--target`.

**Validation**

- `@SQ` SN must equal the target exactly and `LN` must equal the annotation span; a mismatch raises `CoverageMapError` with both values.
- Transcript-reference detection: if the reference name matches a transcript accession, or the GTF has a single whole-genome placeholder, label the figure `reference-transcript coverage` and **do not** overlay accession-level gene models whose span exceeds the reference length.
- Strand: draw `+`/`-` arrows; overlapping ORFs are drawn on separate rows.
- Circular genomes: do not fabricate wrap-around features. If a feature crosses the origin, split it into two blocks and annotate `origin-spanning`.

**Outputs**

```text
results/evidence/<target>/
    coverage_map.<accession>.png
    coverage_map.<accession>.pdf
    coverage_map.<accession>.tsv.gz     # position or binned depth, zeros included
    coverage_map.<accession>.json       # provenance, lengths, annotation digest, status
```

Statuses: `ok`, `no_coverage`, `annotation_missing`, `annotation_mismatch`, `target_not_in_bam`, `transcript_reference`.

**Tests**

1. Gap fixture → zeros in `coverage_map.<accession>.tsv.gz` between covered blocks.
2. Annotation span > reference length → `CoverageMapError` naming both values; status `annotation_mismatch`.
3. No GTF → status `annotation_missing`; depth panel still drawn; no gene track.
4. Target absent from the BAM → status `target_not_in_bam`, message lists the available references.
5. Two viral accessions and no `--target` → error asking for one (no silent pick).
6. Coordinate parity: TSV depths equal `samtools depth` output on the same fixture.
7. Transcript reference with a genome GTF → status `transcript_reference`, label applied, no gene overlay.
8. Reference present with zero depth → status `no_coverage`, zeros (not missing rows) in the TSV.

**Acceptance:** the figure reconciles exactly with `samtools depth` on a fixture (C6); C1–C8 pass; no detection field changes.

---

### WP-4 — Candidate-complete evidence review (opt-in diagnostic)

**Affected files**

| File | Change |
|---|---|
| `src/viralscan/scripts/auto_evidence.py` | `anello_genera()` gains candidate enumeration; new `review_candidates` config flag |
| `src/viralscan/scripts/evidence_run.py` | New `source="alignment"` path reading the STAR BAM |
| `src/viralscan/cli/parsers.py` | `evidence --review-candidates` |
| `docs/output_reference.md` | `results/evidence_review.tsv` |
| `tests/test_auto_evidence.py` | Extend |

**Candidate enumeration**

For each Anelloviridae genus in `viral_summary.tsv`, include every row where any of:
- `detected == True` (existing behaviour), **or**
- `detection_source == "alignment_only"` (STAR candidate), **or**
- the row is below the called-cell gate (`detected == False`).

**Evidence source**

- Kallisto-eligible rows: unchanged replay.
- `alignment_only` rows: read `anello_align/Aligned.sortedByCoord.out.bam`, filter by target and barcode tag, and emit the fields that are computable (aligned reads, unique CB–UMI, query coverage, complex-body fraction, reagent fraction).
- Fields that require kallisto ECs are `not_assessed`.

**Output**

One file: `results/evidence_review.tsv`, one row per sample × taxon:

`virus_name, detection_source, detected, evidence_source (kallisto_replay|star_bam|none), n_reads, n_unique_cb_umi, complex_body_fraction, reagent_fraction, status (reviewed|not_assessed|unsupported_source), reason_codes`

No per-cell ledger, no junction TSV, no new schema family.

**Tests**

1. STAR-only candidate (0 kallisto UMI, present in the STAR BAM) → `evidence_source=star_bam`, `status=reviewed` (D1).
2. Below-gate candidate (`detected=False`) → appears with its weak evidence unchanged (D2).
3. No STAR BAM for an `alignment_only` row → `evidence_source=none`, `status=not_assessed`, reason `alignment_bam_missing` (D3).
4. Parity: `detected` and `viral_summary.tsv` byte-identical before/after (D4).

**Acceptance:** a 0-kallisto-UMI/STAR-positive simulation appears with `evidence_source=star_bam`; a below-gate candidate appears with its weak evidence unchanged; no `detected` value changes.

---

### WP-5 — Tier-2 molecule fingerprint (opt-in diagnostic)

**Affected files**

| File | Change |
|---|---|
| `scripts/swap_check.py` | New `--tier2` mode comparing corrected (CB, UMI) keys |
| `tests/test_swap_check.py` | Extend |

**Rules**

- Compare only pairs already admitted by the pool/whitelist rule.
- Read the corrected BUS from `kb_outputs.corrected_bus` = `kb-python/output.corrected.bus` (`kb_outputs.py:68-70`) — **not** under `counts_unfiltered/`. That file exists only for corrected runs, so prefer `kb_outputs.resolved_bus` = `kb-python/output.resolved.sorted.bus` (`:58-61`), the CB–UMI-sorted artifact v3 counting actually uses; fall back to `corrected_bus`, and if neither exists → `not_assessed`.
- Build the empirical collision null from within-library shuffled distribution; report `observed_shared_keys`, `expected_shared_keys`, `p_value`.
- Same CB+UMI with different viral target does not count as a match.
- Insert/start–end confirmation only when evidence BAMs exist; otherwise `insert_confirmation=not_assessed`.
- Never write or alter counts.

**Tests**

1. Planted shared CB+UMI in two libraries of the same pool → detected with a null p-value (E1).
2. Two libraries with different `pool_id` or `whitelist` → not compared (E2).
3. Same CB+UMI, different viral target → not a definitive match (E3).
4. Neither BUS artifact present → `not_assessed` (E4).

**Acceptance:** planted shared CB+UMI in the same pool is detected; two unrelated pools are not compared; same CB+UMI/different virus is not a definitive match; absent BUS → `not_assessed`; `detected` unchanged.

---

### WP-6 — Anellovirus capturability / STAR calibration (deferred experiment)

**Affected files**

| File | Change |
|---|---|
| `scripts/plant_anello_10x.py` | Add missing strata only |
| `scripts/anello_acceptance_report.py` | Add stratum table |
| `docs/plans/` | New pre-registration document **before** running |
| `src/viralscan/anello_align.py` | No change until the frozen decision says so |

**Rules**

- Pre-register the STAR filter grid and stop rule in a dated document before any run.
- Training-only. Never touch holdout.
- Report per stratum: sample-level recall, molecule-level recall, false positives, abstentions.
- No default change without the freeze decision.

**Acceptance:** a pre-registration document exists before results; every stratum is reported including failures; no default is changed by this WP.

---

### WP-7 — v3 scientific validation (governance gate, not code)

- No implementation work. No execution.
- Any proposed new outcome requires a protocol amendment before opening data.
- Claims in `claims/registry.json` must remain consistent with the draft status.

**Acceptance:** the gate file still says `status: draft`, `training_execution_allowed: false`, `holdout_execution_allowed: false`; no performance claim is added to docs.

---

### WP-8 — Junction/transcription evidence (deferred research)

Not scheduled. `Alignment.spliced()` remains a diagnostic count. A future proposal must supply: curated junction coordinates with provenance, a negative-control repeat set, and per-cell molecule linkage. No junction-based claim may appear in the release.

---

### WP-9 — Documentation, wording, stale-status reconciliation

- `docs/plans/ambient-and-barcode-swapping-controls.md`: replace "design only / no code" with the implemented status and point to `soup_screen()`, `scripts/swap_check.py`, and tests.
- `docs/output_reference.md`: add SuperExpressor TSV/JSON, `evidence_review.tsv`, coverage-map files; align with OUT-LAYOUT-01.
- Terminology: "candidate evidence", "high viral burden", "not proof of infection", "reference-transcript coverage".
- `README.md` / report template: no "infected" badge for a one-molecule event.

**Acceptance:** `rg "design only" docs/plans/ambient-and-barcode-swapping-controls.md` returns nothing; docs build passes; no claim language contradicts WP-7.

---

## 5. PR sequence and dependencies

| PR | Contents | Depends on | Touches counts? | Review focus |
|---|---|---|---|---|
| **PR-A** | WP-1 (summary + PNG + tests) | — | No | Denominator proof; parity test |
| **PR-B** | WP-2 (coverage zeros) | — | No | OOM test still green; gap fixture |
| **PR-C** | WP-3 (coverage map) | PR-B | No | Coordinate/length validation; statuses |
| **PR-D** | WP-4 (candidate review) | — | No | `alignment_only` source labelling |
| **PR-E** | WP-5 (tier-2) | — | No | Empirical null; pool scoping |
| **PR-F** | WP-9 (docs/wording) | PR-A..E | No | Docs build; no stale claims |
| **EXP-1** | WP-6 pre-registration + run | WP-7 authorisation | No | Training-only; strata |
| **GATE-1** | WP-7 | signed freeze | No | No code |

**First merge:** PR-A and PR-B in parallel. **Do not** combine WP-1 and WP-2 in one PR; they have different reviewers and different failure modes.

---

## 6. Test and benchmark requirements

### Unit/integration (must pass in CI)

- WP-1: the 11 tests listed in §4 WP-1 (A1–A11).
- WP-2: the 4 tests listed in §4 WP-2 (B1–B4).
- WP-3: the 8 tests listed in §4 WP-3 (C1–C8).
- WP-4: the 4 tests listed in §4 WP-4 (D1–D4).
- WP-5: the 4 tests listed in §4 WP-5 (E1–E4).
- WP-9: docs link check (F1–F2).

### Existing tests that must keep passing

- `tests/test_super_expressors.py` — rewritten to assert the corrected denominator, not deleted.
- `tests/test_detection_audit_s2.py::TestSuperExpressorInputs` (3 tests: zero-cell error, no `adata` mutation, docstring rule).
- `tests/test_detection.py` (38 tests) and `tests/test_evidence.py` (69 tests) at the audited commit.
- `tests/test_swap_check.py` + `tests/test_ambient_screen.py` (26 tests) before WP-5 touches `swap_check.py`.

### Regression (must be explicitly asserted, not assumed)

- `viral_summary.tsv`, `per_cell_viral.tsv`, `detected`, and `adata.X` checksums unchanged on a fixture run for PR-A..E.
- `coverage.raw.tsv` / `coverage.deduplicated.tsv` unchanged by PR-B.
- `tests/test_evidence.py::test_coverage_depth_points_does_not_scan_every_host_position` **unchanged and passing**.

### Benchmarks (no performance promise)

- PR-B: peak RSS on a fixture with one 8 kb viral reference and 10⁶ host positions must not exceed the pre-fix value by more than 10 %.
- PR-C: figure generation for one 3 kb accession under 10 s on a laptop-class core.

### Not in scope

- Any sensitivity/specificity estimate. Those belong to WP-7 and are blocked.

---

## 7. Falsifiable acceptance criteria (consolidated)

| ID | Fixture | Pass condition |
|---|---|---|
| A1 | 1,000 called, 50 viral-positive, 2 ≥ 10 | `pct_cells_super == 0.2` |
| A2 | Zero viral-positive called library | Full header (all `SUMMARY_FIELDS`, incl. `denominator_kind`), exit 0, no traceback |
| A3 | Missing `called_cells.tsv` | Non-zero exit naming the expected path |
| A4 | `--denominator viral_positive_called` | Warns; 4.0 %; `denominator_kind` set |
| A5 | Fractional 9.6 vs 10.0 | 9.6 not high-burden; 10.0 high-burden |
| A6 | Combined matrix with viral features | Null uses host-only sum |
| A7 | Two-step host-depleted matrix | `null_status == "not_estimable"` |
| A8 | Non-called barcode with 10⁵ viral molecules | Excluded from prevalence |
| A9 | Called cell with zero viral molecules | TSV value 0 (not 0.1); `n_zero` correct |
| A10 | 60,000 called cells | Figure shows ranks 1–50 000 with the annotation; TSV has 60,000 rows; `n_plotted`/`max_rank_display` recorded |
| A11 | Any PR-A fixture | `detected` and count files byte-identical |
| B1 | Two 1 nt (`1M`) reads at pos 5 (depth 2) and one at 900 of a 1,000 nt reference | `samtools depth` emits 5 and 900 only; plotted positions 6–899 are depth 0 |
| B2 | Mixed BAM: target-classified viral ref + host contig | Only the viral reference densified; host contig not materialised |
| B3 | Existing OOM test | Unchanged and passing |
| B4 | Empty BAM | `"No aligned coverage"` text unchanged |
| C1 | Gap fixture | Zeros in `coverage_map.<accession>.tsv.gz` between covered blocks |
| C2 | GTF span > reference length | `CoverageMapError` with both lengths; `annotation_mismatch` |
| C3 | No GTF | Depth-only figure, `annotation_missing` |
| C4 | Target absent from BAM | `target_not_in_bam`, lists available refs |
| C5 | Two accessions, no `--target` | Error asking for one; no silent pick |
| C6 | Fixture with known depths | TSV depths == `samtools depth` |
| C7 | Transcript reference with genome GTF | Labelled `reference-transcript coverage`; no genome overlay |
| C8 | Reference present, zero depth | `no_coverage`; zeros (not missing rows) in the TSV |
| D1 | 0-kallisto-UMI / STAR-positive | `evidence_source=star_bam`, no fabricated kallisto counts |
| D2 | Below-gate candidate | Included, weak evidence unchanged |
| D3 | `alignment_only` row with no STAR BAM | `evidence_source=none`, `status=not_assessed` |
| D4 | Any PR-D fixture | `detected` unchanged |
| E1 | Planted shared CB+UMI, same pool | Detected with null p-value |
| E2 | Unrelated pools | Not compared |
| E3 | Same CB+UMI, different virus | Not a definitive match |
| E4 | BUS absent | `not_assessed` |
| F1 | Docs build | Passes |
| F2 | Stale status text | Absent |
| G1 | `protocol.yaml` | Still draft; both flags false |
| G2 | Claims registry | No performance/superiority claim |

---

## 8. Scientific-validation safeguards

1. **Count immutability is a merge condition, not a guideline.** PR-A..E include a parity test.
2. **No threshold is touched.** `se_threshold=10`, `detection_threshold=1`, `infected_min_molecules=1.0`, `detection_min_cells=1` remain literal defaults.
3. **No new biological label.** "High burden" is descriptive; no "infected", "reactivated", "replicating".
4. **Evidence source is always named.** `kallisto_replay` vs `star_bam` vs `none`.
5. **Missing data is explicit.** `not_assessed`, `not_estimable`, `unsupported_source`.
6. **The freeze is untouched.** No training/holdout execution, no protocol edit, no claim promotion. WP-6 requires a pre-registration document and authorisation first.
7. **No assay claim.** Droplet scRNA-seq only; Flex/spatial/nuclei remain explicitly unsupported.
8. **No pseudo-replication.** Host-response wording must state donor/library grouping when available (existing `hostresponse.py` already computes it).

---

## 9. Scope exclusions and disposition of round-2 items

| Round-2 item | Disposition | Where it went |
|---|---|---|
| R0 SE-01/02/03/05 | **Kept**, simplified | WP-1 |
| R0 SE-04 (Poisson envelope) | **Removed** | Not scheduled; optional future |
| R0 "shared pure calculation layer" | **Simplified** | Two helpers only (denominator resolution, host-depth mask) |
| R1 VIS-COV-01..05 | **Split** | WP-2 (bug fix) + WP-3 (feature) |
| R1 pyGenomeTracks phase 2 | **Removed** | Not scheduled |
| R2 M4/GW-03 | **Simplified** | WP-4 (one source, one TSV) |
| R2 per-cell ledger | **Deferred** | Not scheduled |
| R2 junction TSV | **Moved** | WP-8 (deferred) |
| R3 M2/GW-04 | **Simplified** | WP-5 (tier-2 only) + WP-9 docs |
| R4 M1/GW-02 | **Kept, deferred** | WP-6 |
| R5 M3 | **Deferred out of release** | WP-8 |
| R6 M5/GW-06 | **Reclassified** | WP-7 gate |
| R7 GW-05 | **Reduced to wording** | WP-9 |
| Ambient subtraction / CellSweep | **Rejected** | Non-goal N1 |
| Alternative quantifier | **Rejected** | Non-goal N2 |
| Threshold changes | **Rejected** | Non-goal N3 |
| Holdout execution | **Blocked** | WP-7 |

---

## 10. Definition of done

**WP-1 done when:** A1–A11 pass in CI; the corrected PNG and TSV/JSON exist for a fixture run; `detected` parity test passes; release notes contain a before/after ledger for the corrected derived percentages; `docs/output_reference.md` documents the new files.

**WP-2 done when:** B1–B4 pass; the OOM test is untouched; the existing PNG filename is retained; peak RSS benchmark within 10 %.

**WP-3 done when:** C1–C8 pass; PNG+PDF+TSV+JSON exist for one real evidence directory; `docs/output_reference.md` documents the block; no default DAG rule was added.

**WP-4 done when:** D1–D4 pass; `results/evidence_review.tsv` is produced for a fixture with one kallisto and one STAR candidate; no schema beyond the one table exists.

**WP-5 done when:** E1–E4 pass; the script still refuses to compare undeclared pools; no count output changed.

**WP-6 done when:** a dated pre-registration exists **before** execution; the stratum table reports every stratum including failures; no default changed.

**WP-7 done when:** G1–G2 pass; the gate file is unchanged and no claim exceeds the draft status.

**WP-9 done when:** F1–F2 pass; the stale status paragraph is corrected, docs build passes, and no "infected" label appears in the SuperExpressor docs or template.

---

## 11. What this roadmap deliberately does not fix

- The two SuperExpressor code paths remain separate. Unifying them into one engine is not justified by the two callers' different inputs and outputs.
- `scripts/super_expressors.py` remains a repo script, not a package module and not a Snakemake rule. Moving it is a packaging decision with no scientific benefit in this cycle.
- The `rho = 1` soup model remains conservative rather than calibrated. Calibration needs matched controls that are not in scope.
- No estimate of sensitivity, specificity, or prevalence is produced. Those are WP-7 outputs.
- No junction, transcript, or productive-infection claim is made.
