# PROG-MIXED-VETO-01 held-out gate: pre-registration (2026-11-03)

Written and committed **before** any held-out run. Nothing below may change after the first held-out
output exists; a change needs a new dated note that says what changed and why.

## What is tested

The beta-binomial `mixed` veto of package PR #187 (`--programme-mixed-veto betabinomial`), with the KSHV fit
frozen in `src/viralscan/data/gene_program_vetoes.tsv`: mean **0.007365**, rho **0.006506**, alpha **0.01**
per cell. Package commit: the PR #187 head at the time of the runs, recorded per run in `code_sha.txt`; the
veto code and fit must be byte-identical to `13ec4ff`.

Fit and training check (training data, not evidence for the gate): `scripts/kshv_fit_veto_p0.py`
(`_kshv/veto_fit_betabinom_342c8db/`), `scripts/kshv_veto_training_gate.py` (`_kshv/veto_training_gate_13ec4ff/`, on the forced runs in `_kshv/veto_training_check_betabinom_13ec4ff/`; both byte-identical to the first runs made on an unpushed WIP commit):
on GSM5725696/-97 the mixed-share gap is -0.3 and -4.7 points under `betabinomial` against 68.5 and 48.5
under `any`. The earlier binomial test (p0 0.004167) failed that check; it is not tested here.

## Definitions (fixed now)

- **Load N:** a cell's KSHV molecules on the unique layer (`counts_unique_viral`) over every KSHV gene, as
  `run_one` computes it (user decision Q13a).
- **Bins:** low [15, 100), high [500, inf) unique KSHV molecules.
- **Cell set:** called cells of the run, KSHV rows of `gene_program_cells.tsv` in state `productive`,
  `mixed` or `latent`.
- **Mixed share:** mixed / (productive + mixed + latent) in that set, per bin, in percentage points.
- **Lytic programme:** `productive` or `mixed`.
- Runs: `viralscan run` with the standard arm set, `--gene-programs`, then `viralscan rerun-programs
  --programme-mixed-veto betabinomial` into a new `posthoc/` dir; the `any` result is the run's own layer 2.

## Datasets

1. **GSE184257** (Jung 2022, PRJNA763826), EpiOral tissue, mock and KSHV 3 dpi / 6 dpi. **Set 3** first (one
   run per condition, about 54 GB). Chemistry by `check-chemistry` per library; a library that fails it is
   recorded n/a with the reason, before any viral output is read. If criterion 1 has fewer than 200 cells at
   >= 500 unique KSHV molecules in Set 3, Set 2 is added before the gate is decided; Set 2 is added in any case
   before the gate counts as passed (user decision Q9).
2. **GSM5725698** (GSE190558 lytic + caspase-i + anti-IFN), early check: not used for the fit or the markers,
   but same series and protocol, so it cannot rule out overfitting on its own.
3. **GSM5725695** (GSE190558 latent): training library, regression only.
4. **HSV-1 SRR8315713**: regression only.

## Pass criteria (all must hold; user decision Q7, revised)

| # | Data | Criterion |
|---|---|---|
| 1 | GSE184257 KSHV-infected libraries | >= 90 % of called cells with >= 500 unique KSHV molecules are lytic programme |
| 2 | GSE184257 mock libraries | 0 called cells with >= 2 productive groups (`productive_breadth` >= 2) |
| 3 | GSE184257 KSHV-infected libraries | \|mixed share high - mixed share low\| <= 10 points, per library |
| 4 | GSM5725698 | criteria 1 and 3 |
| 5 | GSM5725695 | >= 95 % of scored KSHV cells latent and <= 1 % productive |
| 6 | HSV-1 SRR8315713 | productive calls identical to the `any` run. HSV-1 latency is unobservable, so `mixed` is unreachable and the veto cannot change it: this checks the plumbing, not the rule |

A criterion whose bin holds fewer than 30 cells is **not estimable** for that library and is reported so; it
neither passes nor fails. The gate passes only if every estimable criterion passes and criteria 1 and 3 are
estimable on at least one GSE184257 KSHV library.

## Known limitation, stated before the run

No held-out latent library exists, so the latent side (criterion 5) is checked only on training data. A pass
supports the veto for lytic and mixed calls, not a held-out latent claim.

## Outcome

If the gate passes, a package PR sets KSHV's `mixed_veto_rule` to `betabinomial`. If it fails, KSHV stays on
`any`, the result is recorded here as a new dated section, and the veto is not tuned on GSE184257.
