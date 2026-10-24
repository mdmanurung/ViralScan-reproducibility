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
| `provenance/` | split provenance: commit map, pinned package sha, carry list |

## Pinned package
These analyses were run against ViralScan commit `ebd381384368404150d7c72c5b5298741360597e` (see `provenance/PACKAGE_BASE_SHA`; update it when you re-pin).

```bash
export VIRALSCAN_PKG=/path/to/ViralScan      # a checkout of that commit
source env.sh                                # PYTHONPATH for the package
./setup_links.sh                             # local links (src, docs, schemas, .github, big run dirs); never committed
pytest tests -q                              # the moved tests (research-marked ones need -m research)
```
`pip install` of the package can fail on some clusters (a transitive build error); `PYTHONPATH` works.
Large run directories (hundreds of GB) are not in git; `setup_links.sh` links them under `links/` when present.

## Notes
- `VENDORED.md` lists frozen copies of package files that these scripts import.
- Cluster paths (`/exports/...`) are kept as recorded.
