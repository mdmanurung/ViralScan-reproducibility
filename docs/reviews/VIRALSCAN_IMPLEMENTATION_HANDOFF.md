# ViralScan — Implementation Handoff

**For:** a separate coding agent
**Baseline:** `origin/main` (`9151da9`) or the audit worktree at `78660933`
**Read first:** `VIRALSCAN_REVISED_ROADMAP.md` §1 contracts and §4 work packages
**Do not read as instructions:** the original `ViralScan_refined_roadmap_round2.md` (supplied with the review request; not in the repository) where it conflicts with this file

**Hard rules for every task**

1. Do not change `adata.X`, `detected`, allocation weights, or default thresholds.
2. Do not add a dependency. Matplotlib, scipy, samtools, pandas, numpy, anndata are already present.
3. Do not add a default Snakemake rule. New outputs are opt-in.
4. Do not run training or holdout analyses.
5. Do not use `samtools depth -a`.
6. Do not label any cell "infected", "reactivated", or "replicating".
7. Work from `origin/main`; the local `5e551c9` tree is 238 commits stale and lacks `scripts/super_expressors.py`.
8. Run `GIT_EDITOR=true git rebase …` for any interactive rebase in a non-interactive shell.

**Line numbers** in this file refer to the audited tree `78660933`. They are unchanged for `detection.py` at `origin/main` (`9151da9`), but resolve symbols with `rg` before editing; do not trust a number blindly.

**Verification environment.** The repo `.venv` is Python 3.14.5 with **no** pytest; system `python3` is 3.6.8. Two working options:

```bash
# Option A: a system pytest that already has the project dependencies.
# Verified in this environment: pytest 9.1.1 on a conda Python 3.10 with scanpy 1.11.5.
PYTHONPATH=src pytest tests/test_super_expressors.py -x -q

# Option B: fresh env from pyproject (there is no `test` extra: use `dev` + `full`).
cd <tree>
uv venv .venv --python 3.12
uv pip install -e '.[dev,full]'
.venv/bin/python -m pytest tests/test_super_expressors.py -x -q
```

`full` is required for anything importing `detection.py` (it imports `scanpy` at module level); `dev` supplies pytest. If an extras name does not exist, read `pyproject.toml` and use the real one. Do not invent a test command.

**samtools.** Tasks 3 and 4 need `samtools` on `PATH`. On this HPC it comes from Lmod: `module load genomics/ngs/samtools/1.16.1/gcc-8.5.0` (samtools 1.16.1, htslib 1.16). No install is required. The repo `environment.yml` pins `samtools=1.23.1` for conda-based environments; either satisfies the tests. Verify with `samtools --version` before claiming a coverage test ran.

---

## Task 1 — WP-1.1: Summary denominator (PR-A)

**Start at:** `scripts/super_expressors.py`

**Before:** `summarise()` (`:30-42`) falls back to a `called` set built only from `per_cell_viral.tsv`, i.e. virus-positive called barcodes. `main()` (`:70-94`) has no denominator flag and no provenance column.

**After:** the denominator is `--cells`, or `results/called_cells.tsv` resolved from the run directory, or a hard error. `--denominator viral_positive_called` reproduces the old behaviour with a warning and a provenance column.

**Minimum change**

```python
# scripts/super_expressors.py
def resolve_denominator(per_cell_viral, cells):
    if cells is not None:
        return set(cells), "called_cells"
    run_dir = Path(per_cell_viral).resolve().parent.parent
    called = run_dir / "results" / "called_cells.tsv"
    if called.is_file():
        return read_cells(called), "called_cells"
    raise SystemExit(
        f"No complete called-cell denominator. Pass --cells, or point --per-cell-viral at "
        f"<run>/results/per_cell_viral.tsv with <run>/results/called_cells.tsv present. "
        f"Refusing to compute prevalence over the virus-positive subset."
    )
```

- Add `--denominator {called_cells,viral_positive_called}` (default `called_cells`).
- In `viral_positive_called` mode, use the old `called` set, emit one `log.warning`, and set `denominator_kind="viral_positive_called"` on every row.
- Add `denominator_kind` as the **last** column; keep existing column names and order. Define one ordered `SUMMARY_FIELDS` constant and use it for every write:
  `dataset, sample, virus, n_cells, n_cells_viral_umi, min_umi, n_super_expressors, pct_cells_super, viral_molecules, viral_molecules_in_super, share_molecules_in_super, max_viral_per_10k, n_ge_3, n_ge_5, n_ge_10, n_ge_50, denominator_kind`.
- When `by_virus` is empty, write that full header and return 0. Do not index `rows[0]`; at the audited commit this path writes only `dataset`/`sample` (BUG-7).

**Reuse**

- `read_cells()` (`:24-27`) already skips a `barcode` header and handles one-column files; `results/called_cells.tsv` is written with a `barcode` header (`cellcalling.py:688-695`), so it is directly compatible.
- Do not import `cellcalling`; keep the script dependency-free.

**New/updated tests** (`tests/test_super_expressors.py`)

Replace the assertion at `:24-38` that expects `pct_cells_super == 50.0` from a 2-cell denominator. Add:

1. 1,000 called / 50 viral-positive / 2 ≥ 10 → `0.2`.
2. Header-only `per_cell_viral.tsv` → header-only output, exit 0.
3. `per_cell_viral.tsv` in a temp run dir **without** `called_cells.tsv` → `SystemExit`.
4. `per_cell_viral.tsv` in `<run>/results/` **with** `called_cells.tsv` → resolved automatically.
5. `--denominator viral_positive_called` → 4.0 %, warning, `denominator_kind` set.
6. 9.6 does not reach a 10 threshold; 10.0 does.

**Edge cases**

- Duplicate barcodes in the cells file: set semantics already deduplicate; keep.
- GEM suffix mismatch between the cells file and `per_cell_viral.tsv`: do not silently intersect; if the resolved universe has zero intersection with the per-cell barcodes, raise.
- Barcode column with extra tab columns: `read_cells` takes the first column; keep.

**Prohibited**

- Do not change `--min-umi` default (10).
- Do not remove `is_called_cell` from `per_cell_viral.tsv`.
- Do not add a new dependency or a new schema.

**Verify**

```bash
.venv/bin/python -m pytest tests/test_super_expressors.py -x -q
.venv/bin/python scripts/super_expressors.py --per-cell-viral <fixture>/results/per_cell_viral.tsv --min-umi 10
# expect: non-zero exit naming results/called_cells.tsv
```

**Stop conditions**

- Stop if `tests/test_super_expressors.py` cannot be run (report the missing environment; do not claim success).
- Stop if any change would alter `per_cell_viral.tsv`.

---

## Task 2 — WP-1.2: PNG host-depth null and declared universe (PR-A)

**Start at:** `src/viralscan/scripts/detection.py::super_expressor()` (`:331-455`) and the `if config.visual:` loop in `main()` (`:2124-2132`), which must move to just after `write_called_cells(...)` (`:2185`).

**Before**

- `:351` `n_count_rna = _sum_axis(adata.X, 1)` (includes viral features).
- `:389` `clip(lower=1e-1)`.
- `:397-398` `max_rank_display = 15000`; silent slice.
- The universe is `adata.n_obs` (all droplets; `:348` and `:395`).
- The plot is generated at `:2126`, **before** `called_mask` is assigned (~`:2167`), so the mask is not available there.

**After**

- `n_count_rna` is host-only.
- The universe is the in-memory `called_mask` that `main()` passes to `compute_stats()`; the plot loop runs after `results/called_cells.tsv` is written.
- A TSV and JSON sidecar carry the true zeros and provenance.
- Truncation is explicit.

**Minimum change**

```python
def super_expressor(adata, virus, viral_gene_ids, outputpath,
                    viral_count_matrix=None, *, host_gene_mask=None, called_mask=None):
    ...
    if adata.n_obs == 0:
        raise ValueError("super_expressor: the dataset has no cells, nothing to plot.")
    universe = (
        np.ones(adata.n_obs, dtype=bool) if called_mask is None
        else np.asarray(called_mask, dtype=bool)
    )
    denominator_kind = "all_barcodes" if called_mask is None else "called_cells"
    host = None if host_gene_mask is None else np.asarray(host_gene_mask, dtype=bool)
    n_count_rna = None if host is None else pd.Series(
        _sum_axis(adata.X[:, host], 1), index=adata.obs_names
    )
    ...
    # after viral_umi is built (:365-368) and BEFORE the null totals (:371-373):
    viral_umi = viral_umi[universe]
    n_count_rna = None if n_count_rna is None else n_count_rna[universe]
    total_viral = viral_umi.sum()
    total_rna = 0.0 if n_count_rna is None else n_count_rna.sum()
    null_model = None if n_count_rna is None or total_rna == 0 else total_viral * (n_count_rna / total_rna)
    n_high_burden = int((viral_umi >= config.se_threshold).sum())
```

Call site (`main()`). The plot loop currently sits at `:2124-2132`, **before** `called_mask` is assigned (~`:2167`). Move it to immediately after `write_called_cells(adata.obs_names, called_mask, outputpath)` (`:2185`) and before `compute_stats(...)`:

```python
all_viral = set(identity.viral_gene_ids()) if identity is not None else {
    g for genes in index_groups.values() for g in genes
}
host_mask = ~adata.var_names.isin(all_viral)
if config.visual:
    for virus in group_by_virus:
        super_expressor(
            adata, virus, group_by_virus[virus], outputpath,
            viral_count_matrix=detection_matrix,
            host_gene_mask=host_mask,
            called_mask=called_mask,
        )
```

Do **not** call `load_called_mask()` here: `detection.py` does not import it, `outputpath` is already the run directory (so `dirname()` would point at its parent), and the helper recomputes cells when `called_cells.tsv` is missing. The in-memory mask is authoritative and was just written to disk.

Note the flattening: `group_genes()` returns `(dict[str, list[str]], set[str])`, so `set(index_groups)` is a set of **virus names**, not gene IDs. Using it would make `host_mask` all-`True` and quietly put viral features back into the null.

**Null status rules**

- `host_gene_mask is None` → `null_status="not_estimable"`, no grey line.
- `total_rna == 0` over the universe → `not_estimable` (two-step host-depleted matrix).
- Otherwise → `ok`.
- When the null is `not_estimable`, skip the `null` dataframe column, the rolling smooth (`:384-386`), and the grey line; keep the observed curve and put the status in the subtitle. `n_high_burden` replaces `n_SE` at `:393`.

**Figure/data rules**

- Write `plots/SuperExpressor_<virus>.tsv`: `barcode, viral_molecules, host_molecules, is_called, null_expected, rank_observed, rank_null`. True zeros stay zero.
- Write `plots/SuperExpressor_<virus>.json`: `sample, virus, count_layer, se_threshold, null_status, denominator_kind, n_universe, n_plotted, n_zero, n_high_burden, display_floor, max_rank_display, git_sha, host_gene_source, called_cells_source, called_cells_sha256`.
- Figure display floor: `observed_plot = observed.clip(lower=0.5)` **only** in the plotting frame; label it `"values ≤ 0.5 drawn at 0.5 (log scale); exact values in the TSV"`. The old label "0 values shown at 0.5" is wrong: fractional allocations such as 0.3 are legitimate values, not zeros.
- Truncation: if `n_universe > 50_000`, take `max_rank_display = 50_000` and annotate `"showing ranks 1–50000 of N"`; otherwise plot all. The TSV keeps **all** `n_universe` rows; the cap applies to the figure only. Record both counts in JSON.
- Keep `plots/SuperExpressor_<virus>.png`.

**Reuse**

- `identity.viral_gene_ids()` is the same partition `multimap.py` used.
- `resolve_count_matrix()` / `matrix_for_genes()` already handle the count layer.
- `load_called_mask()` (`cellcalling.py:698`) is **not** used in this path; it remains the resolver for `gene_programs.py`.

**New tests** (`tests/test_super_expressor_plot.py`)

1. Synthetic AnnData: 3 host genes, 1 viral gene; host totals differ from `sum(X)`; assert the null uses the host sum.
2. `host_gene_mask=None` → `null_status=="not_estimable"`.
3. All-zero host column → `not_estimable`.
4. Called mask excludes a non-called high-viral barcode; assert `n_high_burden` excludes it.
5. Zero viral counts appear as `0` in the TSV, not `0.1`.
6. 60,000 **called** barcodes → JSON `n_universe==60000`, `n_plotted==50000`, `max_rank_display==50000`, annotation present, TSV row count 60,000.
7. `viral_summary.tsv` and `per_cell_viral.tsv` checksums unchanged (parity).
8. A non-called barcode with a large viral count must not change the null totals either (subset before summing).

**Existing tests that must keep passing**

- `tests/test_detection_audit_s2.py::TestSuperExpressorInputs` (3 tests): zero-cell `ValueError`, caller `adata` not mutated, and the docstring states the `>= config.se_threshold` rule. The new keyword args must stay optional so the existing call `D.super_expressor(a, "V", ["v1"], str(tmp_path))` still works.

**Edge cases**

- `adata.X` sparse: `_sum_axis` already handles it; keep.
- Duplicate var names: `preprocessing()` already raises; do not add a second check.
- No viral genes matched: existing `ValueError` at `:357-360` (not `:338-340`, which is docstring); keep.
- `config.visual` false: the loop is never executed; do not change the gate.

**Prohibited**

- Do not use `sum(adata.X)` anywhere in the null.
- Do not change `se_threshold` (10) or its config wiring.
- Do not rename the PNG.
- Do not write into `adata.obs`/`adata.var`.
- Do not change `compute_stats()` or any `detected` logic.

**Verify**

```bash
.venv/bin/python -m pytest tests/test_super_expressor_plot.py tests/test_super_expressors.py tests/test_detection_audit_s2.py -x -q
.venv/bin/python -m pytest tests/test_detection.py -q
```

**Stop conditions**

- Stop if the parity test cannot be made byte-identical; report the diff instead of editing the fixture.

---

## Task 3 — WP-2: Coverage zero gaps (PR-B)

**Start at:** `src/viralscan/evidence.py::plot_coverage_comparison()` (`:1527-1575`).

**Before:** `axis.plot` over sparse covered positions; gaps are bridged.

**After:** each viral reference is plotted on `1..L` with explicit zeros; unknown lengths use NaN breaks.

**Minimum change**

```python
def reference_lengths(bam: str) -> dict[str, int]:
    text = _run(["samtools", "view", "-H", bam], capture=True).decode(errors="replace")
    out = {}
    for line in text.splitlines():
        if line.startswith("@SQ"):
            fields = dict(kv.split(":", 1) for kv in line.split("\t")[1:] if ":" in kv)
            if "SN" in fields and "LN" in fields:
                out[fields["SN"]] = int(fields["LN"])
    return out
```

In `plot_coverage_comparison`, for each `reference`:

```python
if is_viral_reference(reference) and (length := lengths.get(reference)) is not None and length <= 5_000_000:
    xs = np.arange(1, length + 1)
    ys = np.zeros(length, dtype=float)
    ys[xs_from_rows - 1] = depths
    axis.plot(xs, ys, ...)
else:
    axis.plot(xs_from_rows, depths, ...)  # leave breaks (NaN insertion optional)
```

Define the predicate per reference; do **not** reuse the existing `explicit_classes` boolean at `:1538`, which is a global OR: when any target/same-reporting-group/related/decoy reference exists it admits every reference, host contigs included. `reference_class()` alone is also insufficient — it returns `"virus"` for any unprefixed id (`:830-833`).

**Reuse**

- `to_int` already exists in the module.
- Keep `_SAMTOOLS_DEPTH_POLICY` (`:1762`) exactly as is.

**Tests** (`tests/test_evidence.py`, extend)

1. Fake BAM header `@SQ SN:VIRUS|X LN:1000`; **1 nt (`1M`)** reads: two at 5 (depth 2) and one at 900 (depth 1) → `samtools depth` emits only 5 and 900; assert the plotted array has depth 0 at 6–899. (With `10M` reads the uncovered interval starts at 15.)
2. Mixed BAM with a target-classified viral reference and a host contig → only the viral reference is densified; the host contig yields no dense array.
3. The existing OOM test is untouched and passes.
4. Empty BAM → `"No aligned coverage"` text unchanged.

**Prohibited**

- Do not add `-a`.
- Do not change `coverage_depth_points()`.
- Do not change `coverage.raw.tsv` / `coverage.deduplicated.tsv`.
- Do not rename `coverage.raw_vs_deduplicated.png`.

**Verify**

```bash
.venv/bin/python -m pytest tests/test_evidence.py -x -q
```

---

## Task 4 — WP-3: Coverage map (PR-C)

**Depends on:** Task 3 (reuse `reference_lengths`).

**Start at:** `src/viralscan/evidence.py`, `src/viralscan/cli/parsers.py::_build_evidence_plot_parser` (`:386`).

**Before:** `evidence-plot` draws read-by-read competitive figures only; the coverage comparison PNG has no gene track.

**After:** `viralscan evidence-plot --coverage-map --target <accession> --evidence-dir <dir> [--annotation file.gtf]` writes PNG, PDF, TSV and JSON.

**Minimum change**

1. `coverage_map_figure(evidence_dir, target, annotation_path, out_dir)` in `evidence.py`:
   - Read lengths from both BAMs; require `target` present.
   - Read depth via `coverage_depth_points` for raw and dedup; densify with the Task-3 helper.
   - Parse annotation: GTF rows whose `seqid == target`; validate `max(end) <= length`; on mismatch raise `CoverageMapError(f"annotation span {max_end} > reference length {length}")`.
   - If no annotation: one panel, `status="annotation_missing"`.
   - If the target is a transcript accession (no `gene` rows, or a single whole-genome exon spanning `1..length`): subtitle `reference-transcript coverage`.
   - Draw genes on separate rows by strand; arrows for direction; split origin-spanning features into two blocks and label them.
   - Write PNG (dpi 200), PDF, TSV (position, raw_depth, dedup_depth, zeros included), JSON (target, length, annotation digest, status, source BAMs, git SHA).
2. CLI flags: `--coverage-map`, `--target`, `--annotation`. When `--coverage-map` is set, `--target` is required unless exactly one viral reference exists.
3. No Snakemake rule.

**Reuse**

- `anellovirus.gtf_text_for()` or a user GTF; `reference_class`; `evidence_run.py` BAM names.

**New tests** (`tests/test_coverage_map.py`)

1. Gap fixture → zeros in TSV.
2. GTF span > reference → `CoverageMapError`.
3. No GTF → `annotation_missing`.
4. Target absent → `target_not_in_bam` listing available refs.
5. Two accessions with no `--target` → error asking for one.
6. Coordinate parity: TSV depths equal `samtools depth` output on the fixture.
7. Transcript reference with a genome GTF → `transcript_reference`, no gene overlay.
8. Reference present with zero depth → `no_coverage`, zeros (not missing rows) in the TSV.

**Prohibited**

- Do not add pyGenomeTracks, deepTools or bigWig.
- Do not replay FASTQs.
- Do not merge STAR and kallisto BAMs in one figure.
- Do not overlay a genome GTF on a transcript reference.

---

## Task 5 — WP-4: Candidate-complete evidence review (PR-D)

**Start at:** `src/viralscan/scripts/auto_evidence.py::anello_genera()` (`:28-42`), `evidence_run.py`.

**Before:** below-gate and `alignment_only` rows are skipped; the docstring explains why (EC replay cannot see STAR-only reads).

**After:** candidates from all origins are enumerated; `alignment_only` rows get direct BAM evidence; one `results/evidence_review.tsv` is written.

**Minimum change**

1. `anello_genera()` → `candidate_genera(summary_tsv, identity, include_below_gate=False, include_alignment_only=False)`, preserving the current default return.
2. New config flag `review_candidates` (default false). When true, include both classes.
3. For `alignment_only`, call a new `star_evidence(target, bam_path, barcodes=None)` in `evidence_run.py` that reads `Aligned.sortedByCoord.out.bam` and returns the computable fields; EC-dependent fields are `not_assessed`.
4. Write `results/evidence_review.tsv` with the columns in the roadmap §4 WP-4.

**Reuse**

- `detected_summary_rows()` (`virus_grouping.py:65`) for legacy semantics.
- `extract_virus_reads()` for the kallisto path.

**Tests** (`tests/test_auto_evidence.py`, extend)

1. Summary with one detected, one below-gate, one `alignment_only` → three candidates when the flag is true; one when false.
2. STAR BAM fixture with a viral record → `evidence_source=star_bam`, nonzero read count.
3. No STAR BAM → `not_assessed`, not a crash.
4. `detected` column unchanged.

**Prohibited**

- Do not pass `alignment_only` targets to the kallisto EC replay.
- Do not create the per-cell ledger or junction TSV.
- Do not change `detected`.

---

## Task 6 — WP-5: Tier-2 fingerprint (PR-E)

**Start at:** `scripts/swap_check.py`.

**Before:** tier-1 barcode overlap only; docstring says tier 2 is not implemented (`:34`).

**After:** `--tier2` compares corrected `(CB, UMI)` keys across already-admitted pool pairs, with an empirical null.

**Minimum change**

1. Read the BUS from `KbCountOutputs.resolved_bus` = `kb-python/output.resolved.sorted.bus` (`kb_outputs.py:58-61`), the CB–UMI-sorted artifact v3 counting uses. Fall back to `corrected_bus` = `kb-python/output.corrected.bus` (`:68-70`; corrected runs only). If neither exists → `status="not_assessed"`. Neither file is under `counts_unfiltered/`.
2. Build `{(cb, umi): set(targets)}` per library.
3. Observed = keys shared with a donor library **for the same target**.
4. Null: shuffle barcode labels within the recipient library (or sample from the within-library key distribution), 1,000 permutations, fixed seed recorded in the manifest.
5. Emit `observed_shared_keys, expected_shared_keys, p_value, insert_confirmation (not_assessed unless BAMs), status`.
6. Do not compare undeclared pools.

**Tests** (`tests/test_swap_check.py`, extend)

1. Planted shared CB+UMI, same pool → observed ≥ 1, `p_value` recorded.
2. Two pools with different `pool_id` → no comparison rows.
3. Same CB+UMI, different target → not counted as a match.
4. No BUS → `not_assessed`.

**Prohibited**

- Do not modify counts or `detected`.
- Do not report a definitive "swapped" label.

---

## Task 7 — WP-9: Docs and wording (PR-F)

**Start at:** `docs/plans/ambient-and-barcode-swapping-controls.md:3-5`, `docs/output_reference.md`.

**Before:** the plan says "design only ... No code, no tests, nothing run" although `soup_screen()`, `swap_check.py`, and both test files exist.

**After:** status reflects implementation; new WP-1/3/4/5 outputs are documented; no "infected" label for a one-molecule event.

**Minimum change**

1. Replace the status paragraph with: implemented tier-1 (`soup_screen`, `swap_check.py`), pending tier-2 (CB+UMI), with file and test pointers.
2. Add `SuperExpressor_<virus>.tsv/.json`, `evidence_review.tsv`, `coverage_map.*` to `docs/output_reference.md`, aligned with OUT-LAYOUT-01.
3. Terminology sweep: `rg -n "infected" docs/ src/viralscan/templates/` and fix only SuperExpressor/host-response contexts, not the detection contract.

**Prohibited**

- Do not rename `detected` semantics.
- Do not claim validated performance.

**Verify**

```bash
rg "design only" docs/plans/ambient-and-barcode-swapping-controls.md   # no output
.venv/bin/python -m pytest tests/ -k "docs or inventory" -q   # only if such a test exists; otherwise report that none exists
```

---

## Task 8 — WP-6: Anellovirus calibration (EXP-1; do not start without authorisation)

**Start at:** `scripts/plant_anello_10x.py`, `scripts/anello_acceptance_report.py`, `docs/plans/`.

**Before:** simulation machinery exists; STAR rescue is opt-in; no pre-registered grid.

**After:** a dated pre-registration document exists **before** any run; strata are reported.

**Minimum change**

1. Write the pre-registration (grid values, stop rule, strata, success criteria) as `docs/plans/<date>-anello-star-calibration.md`.
2. Only after authorisation, run and report every stratum including failures.
3. Do not change `anello_align.py` defaults.

**Prohibited**

- No holdout.
- No default change.
- No threshold selection after seeing outcomes.

**Stop condition:** if `protocol.yaml` still has `training_execution_allowed: false`, stop and report; do not invent authorisation.

---

## Task 9 — WP-7: Gate (no code)

**Do:** verify `analysis/v3_validation/protocol.yaml` still says `status: draft`, `training_execution_allowed: false`, `holdout_execution_allowed: false`.

**Do not:** run anything, edit the protocol, add a performance claim, or alter `claims/registry.json`.

---

## Cross-task checklist before opening a PR

- [ ] `git diff --stat` touches only the files listed for the task.
- [ ] No change to `adata.X`, `detected`, `viral_summary.tsv`, `per_cell_viral.tsv` on a fixture (parity test or checksum).
- [ ] No new dependency in `pyproject.toml` / `environment.yml`.
- [ ] No new default Snakemake rule.
- [ ] New outputs documented in `docs/output_reference.md`.
- [ ] Tests added and run; the exact command and result are in the PR body.
- [ ] PR-A: `tests/test_detection_audit_s2.py::TestSuperExpressorInputs` and `tests/test_detection.py` still pass.
- [ ] PR-E: `tests/test_swap_check.py` and `tests/test_ambient_screen.py` still pass.
- [ ] `rg "samtools.*-a" src/` returns nothing new.
- [ ] `rg -n "infected|reactivated|replicating"` in new plot/docs text returns nothing.

## What not to do (repeated because it is the most likely failure)

1. Do not "fix" the denominator by dropping the fallback and silently using all barcodes. Use `called_cells.tsv` or fail.
2. Do not re-add `samtools depth -a`.
3. Do not merge STAR and kallisto evidence into one count.
4. Do not create a new schema family for R2.
5. Do not claim a scientific result from passing tests.
6. Do not start WP-6 without authorisation.
