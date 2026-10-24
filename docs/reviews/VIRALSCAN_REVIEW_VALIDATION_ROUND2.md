# ViralScan — Validation of the independent review, revised roadmap and handoff (round 2)

**Date:** 20 October 2026
**Validates:** `VIRALSCAN_INDEPENDENT_REVIEW.md`, `VIRALSCAN_REVISED_ROADMAP.md`, `VIRALSCAN_IMPLEMENTATION_HANDOFF.md`
**Audited tree:** `78660933e2f8b35b8c20a490f4d36c93db4e692b` (clean worktree)
**Reconciled against:** `origin/main` = `9151da9` (7 commits ahead)

**Purpose.** A second, adversarial pass over the three artifacts themselves: re-check every claim that carries a `file:line`, re-check the internal ID graph, and execute the claims that can be executed instead of only reading them. Corrections were applied in place to all three files; this memo records what changed and why.

---

## 1. Method

1. Re-read all three artifacts end to end.
2. Re-ran every git-provenance check (`rev-list --count`, commit dates, adding commit, layout commit).
3. Re-read every cited symbol in the audit tree (`sed`, `grep -n`, `git show 9151da9:<path>`).
4. Executed the claim-relevant tests (5 files, 137 passed).
5. Executed two behavioural reproductions rather than asserting them.
6. Checked the ID graph across §4 (tests), §6 (counts), §7 (acceptance table) and §10 (DoD).

---

## 2. Verified as stated (no correction needed)

| Claim | Evidence |
|---|---|
| Audit tree `78660933`; `origin/main` `9151da9` is 7 commits ahead; local `5e551c9` is 238 behind | `git rev-list --count` |
| `scripts/super_expressors.py` added by `0f0d27e` on 2026-10-15; absent at `5e551c9` | `git log --diff-filter=A`; `git cat-file -e` |
| `8933a65` is OUT-LAYOUT-01 (`combined_summary.tsv`, `layout_version`) | `git log`; `docs/output_reference.md:68,114,116` at `origin/main` |
| R0 defect lines unchanged at `origin/main`: `detection.py:331,351,389,397,1104,2126` | `git show 9151da9:…` piped to `grep -n`; diff touches only `main()` after `:2341` |
| Defaults `se_threshold=10`, `detection_threshold=1`, `infected_min_molecules=1.0`, `detection_min_cells=1` | `defaults.py:38,39,43,45` |
| `n_count_rna = _sum_axis(adata.X, 1)` includes viral features | `detection.py:351,362-363` |
| `preprocessing()` returns the full matrix, no called-cell subset | `detection.py:201-262`, `:242` |
| PNG uses `adata.n_obs` (all droplets) | `detection.py:348,395` |
| Coverage OOM guard is deliberate and locked | `_SAMTOOLS_DEPTH_POLICY` `evidence.py:1762`; `tests/test_evidence.py:34-49`; 69 passed |
| Tier-2 fingerprint is documented as not implemented | `scripts/swap_check.py:34`; tests exist and 26 passed |
| `protocol.yaml` still draft / both flags false / frozen harmonisation | `:6`, `:10-11`, `:59` |
| Ambient/swapping plan is "design only" | `docs/plans/ambient-and-barcode-swapping-controls.md:3-5` |
| `coverage.raw.tsv` / `coverage.deduplicated.tsv` documented | `docs/output_reference.md:964` |
| SE-01 closed with `--per-cell-viral F --cells ANCHOR` | `PLAN.md:6504-6512` |
| `spliced()` is `"N" in cigar` | `src/viralscan/anello_align.py:438-439` |
| `anellovirus.gtf_text_for()` emits CDS or a whole-genome placeholder | `anellovirus.py:16-17,37-44,190` |
| Anello rule gated by `if _ANELLO_ALIGN:` | `Snakefile:109` |

---

## 3. Corrections applied

### 3.1 Review

| # | Finding | Severity | Correction |
|---|---|---|---|
| 1 | **BUG-7 as written was wrong.** The zero-virus path does not crash: it exits 0 and writes `dataset\tsample\n`. The real defect is the truncated header (field list derived from `rows[0]`). | Material: the crash claim was false | Row rewritten as header degradation; the `rows[0]` guard is acknowledged; the old note removed |
| 2 | Bug IDs `B1`–`B8` collided with the roadmap's `B1`–`B4` acceptance fixtures | Material for cross-document use | Renamed to `BUG-1`–`BUG-8`; collision called out explicitly |
| 3 | Evidence standard said no tests were executed; a working pytest exists | Material: understated evidence | Rewritten with the five executed files and results |
| 4 | `hostresponse.py` has no `src/viralscan/hostresponse.py`; the file is `src/viralscan/scripts/hostresponse.py`; depth-alone AUC is implemented at `:787`, not in the `:23-29` docstring | Moderate | Path and lines corrected in §4, §5 and §8 |
| 5 | `detection.py` "`:331` uses `adata.n_obs`" — `:331` is the `def`; uses are `:348,395` | Minor | Corrected |
| 6 | `preprocessing()` cited as `:201-265`; it ends at `:262` | Minor | Corrected |
| 7 | Two-step flow cited as `Snakefile:35-96`; `kb_count` is at `:137`, well outside that range | Minor | Now cites `:85` (`host_filter`) and `:137` (`kb_count`) |
| 8 | `anello_align.py` is ambiguous: both `src/viralscan/anello_align.py` (module) and `src/viralscan/scripts/anello_align.py` (Snakemake driver) exist, and `origin/main` changed the latter | Minor | Both citations now name the module path explicitly |
| 9 | The coverage-filter trap (global `explicit_classes` OR) was not recorded | Material for WP-2 | Added to §2.3 with `:1538`/`:1549` |
| 10 | BUS-path precision: `corrected_bus` is `kb-python/output.corrected.bus` (corrected runs only); `resolved_bus` is the canonical artifact | Moderate | Recorded in §8 and §10.6 |

### 3.2 Revised roadmap

| # | Finding | Severity | Correction |
|---|---|---|---|
| 1 | §10 demanded `A1–A11` and `B1–B4` but §7 defined only `A1–A10` and `B1–B3` | Material: DoD unverifiable | Added `A11` and `B4`; rows now mirror the §4 tests 1:1 |
| 2 | WP-3 had no test list; §7 `C1–C4` did not match the six tests in §4, and the `no_coverage`/`transcript_reference` states were untested | Material | Added the 8-test list `C1–C8` (gap, span, no GTF, target absent, multi-accession, samtools parity, transcript reference, no coverage) |
| 3 | WP-4 listed a no-BAM case in the handoff but no `D` criterion | Minor | Added `D3`; parity moved to `D4` |
| 4 | `A9` used 20,000 cells, below the 50,000 cap, so it could not demonstrate truncation | Material | Fixture is now 60,000; pass condition asserts `n_universe=60000`, `n_plotted=50000`, TSV keeps 60,000 rows |
| 5 | WP-5 read `kb-python/counts_unfiltered/output.corrected.bus`; the file is `kb-python/output.corrected.bus` | Material: wrong path | Path fixed; `resolved_bus` preferred with `corrected_bus` fallback |
| 6 | WP-2 said "references that pass the existing viral selection" — that selection is a global OR and admits host contigs whenever any target class exists | Material: would densify host genomes | Rule now requires a per-reference `is_viral_reference()`; `reference_class()` default `"virus"` called out as insufficient |
| 7 | WP-1.2 said the mask is `load_called_mask(...)`, "the same mask `compute_stats()` already uses" — `detection.py` never calls it and `compute_stats()` receives the mask as a parameter | Material: wrong mechanism | Contract 13 added: use the in-memory mask after `write_called_cells()`; `load_called_mask()` explicitly forbidden here |
| 8 | The null totals were not explicitly restricted to the universe; only plot-time filtering was described | Material: empty droplets would remain in the null | "Subset before summing" step added |
| 9 | Display floor labelled "0 values shown at 0.5", but `clip(0.5)` also moves legitimate fractional values (e.g. 0.3) | Moderate: misleading figure label | Label now "values ≤ 0.5 drawn at 0.5"; TSV retains exact values |
| 10 | "Subsample ranks" above 50,000 would discard data and break rank semantics | Moderate | Now "truncate the tail **in the figure only**"; TSV keeps every row |
| 11 | `n_called` (roadmap) vs `n_universe` (handoff) | Minor | Harmonised to `n_universe` |
| 12 | WP-1 affected-files said `main()` 2090–2140 (starts at 2110) and `preprocessing()` 201–265 (ends at 262) | Minor | Corrected to `2110–2415` and `201–262`; call site `:2126`; insertion point `:2185` |
| 13 | `super_expressor()` range 331–420; function ends at 455 | Minor | Corrected |
| 14 | Zero-virus acceptance said "header-only TSV"; it must be the **full** header | Moderate | `A2` now requires all `SUMMARY_FIELDS` including `denominator_kind` |
| 15 | Existing plot tests were absent from the plan | Moderate: implementer would break them | Added `tests/test_detection_audit_s2.py::TestSuperExpressorInputs` to affected files and §6 |
| 16 | Dependency graph contained a draft artefact (`WP-4 ──> WP-5?  no`) | Cosmetic | Rewritten |

### 3.3 Implementation handoff

| # | Finding | Severity | Correction |
|---|---|---|---|
| 1 | `uv pip install -e '.[dev,test]'` — there is **no `test` extra** (only `dev`, `full`, `enrichment`); `detection.py` imports scanpy, so `dev` alone is insufficient | Material: command fails | Now `.[dev,full]`, plus the verified system-pytest route |
| 2 | Snippet called `load_called_mask(adata, config, os.path.dirname(outputpath.rstrip("/")))` at `:2126`. Three defects: the mask does not exist there (assigned ~`:2167`), `detection.py` does not import the helper, and `outputpath` is already the run dir so `dirname()` points at its parent | Material: `NameError` or a re-call that disagrees with detection | Loop moved to after `write_called_cells()` (`:2185`); in-memory mask passed; helper call removed with explanation |
| 3 | `all_viral = … else set(index_groups)` — `group_genes()` returns `(dict[str, list[str]], set[str])`, so `set(index_groups)` is a set of **virus names**; `host_mask` would be all-`True` and viral features would stay in the null | Material: silent correctness bug | Flattened to `{g for genes in index_groups.values() for g in genes}` |
| 4 | `ValueError` cited at `:338-340`; that is docstring. The raise is `:357-360` | Minor | Corrected |
| 5 | Header-only case said "the known field list" without defining it | Moderate: not implementable as written | Full ordered `SUMMARY_FIELDS` enumerated |
| 6 | BUS path wrong (same as roadmap) | Material | Fixed with `resolved_bus` preference |
| 7 | Figure label "0 values shown at 0.5" | Moderate | Corrected wording |
| 8 | No mention of the existing `TestSuperExpressorInputs` suite | Moderate | Added to tests and checklist |
| 9 | Line numbers are `78660933`-specific while agents are told to start from `origin/main` | Minor | Preamble added: resolve by symbol; `detection.py` verified unchanged at `9151da9` |

---

## 4. Executed evidence

Interpreter: pytest 9.1.1 on the system conda Python 3.10 with scanpy 1.11.5. The repo `.venv` (Python 3.14.5) has no pytest; system `python3` is 3.6.8.

```text
PYTHONPATH=src pytest tests/test_super_expressors.py -q
  1 passed
PYTHONPATH=src pytest tests/test_evidence.py -q
  69 passed
PYTHONPATH=src pytest tests/test_swap_check.py tests/test_ambient_screen.py -q
  26 passed
PYTHONPATH=src pytest tests/test_detection.py -q
  38 passed
PYTHONPATH=src pytest tests/test_detection_audit_s2.py -k SuperExpressor -q
  3 passed, 8 deselected
```

Total: **137 passed, 0 failed**.

Behavioural reproductions:

```text
legacy (is_called_cell)        : 50 2 4.0
complete called-cell universe  : 1000 2 0.2
```

```text
zero-virus summarise → exit 0; output is exactly:
dataset\tsample\n
```

The first confirms BUG-1's arithmetic. The second confirms that BUG-7 is a header degradation, not a crash — the earlier hypothesis is retracted.

### 4.1 Coverage-plot execution (addendum)

`samtools` is available through Lmod (`module load genomics/ngs/samtools/1.16.1/gcc-8.5.0` → samtools 1.16.1, htslib 1.16). `plot_coverage_comparison` was executed on synthetic BAMs, capturing every `axis.plot` call:

- `VIRUS|TEST` (`LN:1000`), 10 nt reads at 5 and 900: `samtools depth` emits 5–14 and 900–909 only; no plotted point exists in 15–899, so the line jumps 14→900 and bridges an 885 bp gap — **BUG-6 executed**.
- `VIRUS|A`, `TARGET|B`, `chr1`: all three are plotted, including the host contig — the global `explicit_classes` OR admits it whenever a `TARGET|` reference exists — **WP-2 hazard executed**.
- Header-only BAM: `"No aligned coverage"` text unchanged.

`tests/test_evidence.py` re-run with samtools present: **69 passed**.

The execution also exposed a defect in the review's own acceptance fixture: a "10 nt read at pos 5" covers 5–14, so asserting zeros at 6–899 is wrong for that read length. The fixture now specifies `1M` reads in `B1`, WP-2 test 1, and handoff Task 3 test 1. A `1M` fixture was re-run to confirm the corrected assertion: depth rows are exactly `5 → 2` and `900 → 1`.

### 4.2 Full suite and Sphinx build

Full suite at `78660933` with samtools loaded: **5787 passed, 70 failed, 41 skipped, 163 deselected** in 14 min 41 s. The 70 failures are environmental and outside the review's subject files:

| Files | Count | Cause |
|---|---|---|
| `tests/test_hostresponse*.py` | 59 | `ValueError: unknown attr 'nocapture'` — numba/llvmlite version mismatch in the shared conda env |
| `tests/test_umap.py` | 5 | Same numba/llvmlite error |
| `tests/test_release_static.py` | 6 | Test subprocess cannot find `python` on `PATH` (exit 127) |

Sphinx HTML build of the local tree with the `reviews/**` exclusion applied (sphinx 8.1.3, myst 4.0.1, `nbsphinx`/`sphinx-rtd-theme` installed to a throwaway target): **27 pages built**, no `docs/reviews` page emitted, so `"reviews/**"` in `exclude_patterns` works. The only warning is the pre-existing `notices/CAT-30_retraction_DRAFT.md` toctree warning. `nbsphinx` also warns that the system pandoc (2.0.6) is below its supported minimum (2.9.2–4.0.0); this does not affect the exclusion check. The build was on the local `5e551c9` docs, so page count is not a statement about `origin/main`.

---

## 5. Residual limitations

1. `plot_coverage_comparison()` was executed with samtools 1.16.1 via Lmod (§4.1). The **coverage-map feature (WP-3)** does not exist yet, so its acceptance criteria remain unexecuted.
2. Full suite and Sphinx build were run (§4.2) and their failures triaged as environmental; no end-to-end workflow run and no real-data run.
3. The two-step host-depletion behaviour is derived from the code path, not measured on a two-step run.
4. Tier-2 feasibility still assumes BUS artifacts survive in completed run directories; only the path definitions were verified.
5. The review's severity ordering and the roadmap's scope choices remain judgement calls, not measurements.

---

## 6. Consistency check after the edits

- Acceptance IDs now map 1:1 to the test lists: `A1–A11` (11 tests), `B1–B4` (4), `C1–C8` (8), `D1–D4` (4), `E1–E4` (4), `F1–F2`, `G1–G2`.
- §6 counts, §7 table rows and §10 DoD ranges agree.
- Review bug IDs (`BUG-n`) no longer collide with roadmap acceptance IDs (`A`–`G`).
- No absolute institutional paths were introduced; files are cited repo-relative.
