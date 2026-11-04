# PROG-MIXED-VETO-01 held-out gate: scoring addendum (2026-11-04)

Written and committed **before** any GSE184257 `run` was submitted and before any viral output of it was
opened. It does not change `analysis/round_2026-11-02/prog_mixed_veto_prereg.md` (committed 2026-11-03,
`30d86ec`); it fixes what that note left open. The rule, alpha (0.01), fit (mean 0.007365, rho 0.006506),
bins, cell set and criteria 1-6 stand as written there.

## Package and arms

- Package: `13ea776` (main at the time), worktree `data/pkg_13ea776`. The veto code and the KSHV fit
  (`gene_program_vetoes.tsv`, `gene_programs.py`) are byte-identical to the `13ec4ff` the note names
  (`git diff 13ec4ff 13ea776 -- <both files>` is empty).
  The repro pin `provenance/PACKAGE_BASE_SHA` (9e31c65) predates the veto, so the pin is not used for this
  gate. No pin change is made here.
- Arms per library: `combined_off`, `combined_artefact` and `twostep` (`viralscan run --gene-programs`).
  The gate itself is scored on `twostep`, the arm of the training gate. The other two arms are reported
  as context and cannot change the verdict.
- Both rules are produced by `viralscan rerun-programs --programme-mixed-veto {any,betabinomial}` on the same
  completed run, into `posthoc/programs_veto_any/` and `posthoc/programs_veto_betabinomial/`. The run's own
  layer 2 (catalogue rule, which is `any`) is not used for scoring.
- GSM5725698, GSM5725695 (twostep) and HSV-1 SRR8315713 (`combined_off_r2`; no finished twostep exists) reuse
  the completed round 2026-11-02 runs and get the same two reruns.
- Chemistry: `check-chemistry` per library with no `-x`; its JSON gives `-x` and `--strand`. An unresolved
  library is recorded n/a with the reason.
- GSE184257 evidence outputs (`evidence/`) are not run and not opened: it is also an EVID-06 held-out set.

## Scoring (implemented in `scripts/prog_mixed_veto_heldout_gate.py`)

- N, bins, cell set and mixed share: as in the note (unique-layer KSHV molecules; [15,100) and [500,inf);
  called cells whose KSHV row is productive, mixed or latent).
- Criterion 1: lytic = productive or mixed under `betabinomial`; denominator = **called cells** with
  N >= 500 (a called cell with no KSHV row counts as not lytic). Bin with fewer than 30 called cells is
  not estimable.
- Criterion 3: mixed share per bin over the scored set; each bin needs >= 30 scored cells.
- Criterion 2: called cells of the mock libraries with `productive_breadth` >= 2 on the KSHV row, under
  `betabinomial`; a mock library with no KSHV row has 0.
- Criterion 5: scored cells exclude `indeterminate`.
- Criterion 6: per barcode, productive under `any` equals productive under `betabinomial`.
- Verdict: `PASS` only if no estimable criterion fails and criteria 1 and 3 are estimable on at least one
  GSE184257 KSHV library. A Set 3 pass is reported as "Set 3 passes"; the note still requires Set 2 before
  the gate counts as passed. A library whose bin is not estimable is never rescored by changing a bin.
