# data/ — where the data lives

All bulk data for the ViralScan experiments lives here, on the archive filesystem (mirrored). Nothing under `runs/`, `inputs/`,
`references/`, `backups/` or `pinned_snapshots/` is tracked by git; the manifests (`DATA_MANIFEST.md`, `metadata/`, `raw/*.md`) are.
Every directory was moved here whole (renamed, not copied), so the paths recorded inside run outputs stay relative-valid.
`source env.sh` sets `VIRALSCAN_DATA=data` and `VIRALSCAN_CACHE=data/references/gtf`.

| Kind | Where | Notes |
|---|---|---|
| Viral GTF annotations (393) | `references/gtf/data/*.gtf` | the package reads them through `VIRALSCAN_CACHE` (`<cache>/data/*.gtf`) |
| kraken2 databases | `references/kraken2_db/` | |
| Reference-panel builds | `references/panel_builds/` | `viral_ref_*`, `viralscan_panel_ref*` |
| STARsolo / kallisto reference runs | `references/starsolo/` | `references`, `starsolo_p22_6{,b}`, `ebv_latest_ref_2026-09-27`, `viral_panel_max_2026-09-28` |
| Probes | `references/probes/` | `viral_scan_probe`, `virtus2_probe` |
| Input FASTQs / benchmark inputs | `inputs/benchmark_inputs/`, plus per-study `data/` dirs inside `runs/` | find with `find data -name '*.fastq*'` |
| Run outputs incl. BAMs, count matrices | `runs/` | `benchmark_runs`, `covid_viralscan`, `viralscan_showcase`, `work` (Track A/B/C, discovery, dsr*, disc12), `vs_work`, `cost01`, `logs`, `sources` |
| Package snapshots (git worktrees) | `pinned_snapshots/vs_pinned*`, `runs/vs_work/*` | registered in the package checkout; `git worktree repair` if you move them |
| Backups | `backups/` | old-checkout leftovers, pruned branches, split backups, branch bundles |

Index of an area: `find data/<area> -maxdepth 2 | head`. Per-tree manifests (path, size, sha256 of key files) are written to
`data/metadata/` as trees are documented.
