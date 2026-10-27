# ViralScan-reproducibility

Analyses, benchmarks, validation studies and manuscript evidence for [ViralScan](https://github.com/mdmanurung/ViralScan).
The software lives in the package repo; this repo holds everything that *uses* it. It was split out of the package repo with
per-file git history (`provenance/package_commit_map.tsv` maps old package commit ids to commits here).

| Where | What |
|---|---|
| `analysis/` | one folder per analysis (see `analysis/ANALYSIS_MANIFEST.md`), incl. `v3_validation/` (protocol, deviation ledger) |
| `results/`, `covid_viralscan/`, `benchmark_inputs/` | result tables, the COVID survey, benchmark inputs |
| `claims/`, `audits/`, `docs/plans/` | claim registry, audits, plans and design notes |
| `scripts/`, `extras/`, `tests/` | SLURM jobs, study scripts, helpers and their tests |
| `.living/`, `PLAN.md`, `HANDOFF*.md` | living-repo notes, tracker (experiment sections), session handoffs |
| `provenance/PLAN_archive_2026-10.md`, `docs/handoffs/`, `docs/superpowers/`, `skillpacks/`, `.github/prompts/` | frozen pre-4e package tracker (all done rows) and dev notes moved out of the package tree (REPO-SPLIT-01 batch 4e, 2026-10-27) |
| `provenance/` | split provenance: commit map, pinned package sha, carry list |

## Pinned package
These analyses were run against ViralScan commit `ebd381384368404150d7c72c5b5298741360597e` (see `provenance/PACKAGE_BASE_SHA`; update it when you re-pin).

```bash
git -C /path/to/ViralScan worktree add --detach pkg "$(head -1 provenance/PACKAGE_BASE_SHA)"   # the pinned package checkout, at ./pkg
echo /path/to/ViralScan/.git/objects >> .git/objects/info/alternates                          # ledger commits that live only in the package history
source env.sh                                # VIRALSCAN_PKG=pkg, VIRALSCAN_DATA=data, VIRALSCAN_CACHE=data/references/gtf, PYTHONPATH
pytest tests -q                              # the moved tests (research-marked ones need -m research)
```
`pip install` of the package can fail on some clusters (a transitive build error); `PYTHONPATH` works.
Bulk data (hundreds of GB to TB: FASTQ/BAM, GTFs, kraken2 databases, references, run outputs) lives in `data/` and is not in git; see `data/README.md` for the layout and where each kind of file is.

## Notes
- `VENDORED.md` lists frozen copies of package files that these scripts import.
- Cluster paths (`/exports/...`) are kept as recorded.
