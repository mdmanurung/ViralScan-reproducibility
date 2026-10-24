# Inventory

Every path in scope, with measured sizes and destinations. All values
re-measured 2026-10-02; see `REVIEW.md`.

**Two size columns matter.** `du` deduplicates hardlinks within a tree and
reports allocated blocks. *Apparent* is the raw byte total — what actually
crosses the wire. Capacity planning uses apparent. They differ by up to 3x in
either direction; see `MIGRATION_PLAN.md` §4.

## Deletion is gated

This file enumerates every path that Phase F would delete. **Nothing here may be
deleted, moved, or renamed without explicit user approval.** Phase F issues one
confirmation per stage. See `README.md` Rule 0.

## Package repo, moving out

Every row below is a deletion candidate at Phase F, gated on explicit approval.
Stage **D1** has no row: it creates new files and deletes nothing.

**These sizes are a snapshot, and they are already drifting fast.** The repo is
being worked on while this plan exists: within a single day `covid_viralscan/`
grew from 266 GB to 495 GB apparent (877 to 1,077 files) as strand-rerun
outputs landed, `viralscan_work/` grew 226 G → 261 G, `viral_ref_cat42/`
grew 19 G → 29 G, and the tracked-file count went 589 → 604. Re-measure every
row at Phase A, and see `RISKS.md` R15 on freezing new runs.

Source root: `/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan`

| Source path | `du` | Apparent | Files | Sym | Hard | Tracked | Ignored | Destination | Stage |
|---|---|---|---|---|---|---|---|---|---|
| `analysis/*` | 1.5 G | **4.5 G** | 101 | 0 | 0 | 89 | no | `analyses/*` | D2 |
| `analysis/ANALYSIS_MANIFEST.md` | 32 K | 7.1 K | 1 | 0 | 0 | 1 | no | project root | D2 |
| `analysis/v3_artifact_inventory.tsv` | 32 K | 15 K | 1 | 0 | 0 | 1 | no | **stays** — `provenance/` | C |
| `covid_viralscan/` | 333 G | 495 G | 1,077 | 0 | 0 | 14 | no | `studies/covid/` | D3 |
| └ `covid_viralscan/results_v3_exploratory/` | 6.6 G | 14 G | 126 | 0 | 0 | 0 | **no** | (included above) | D3 |
| └ `covid_viralscan/results_v3_strand_reverse/` | 53 G | 109 G | 96 | 0 | 0 | 0 | **no** | (included above) | D3 |
| └ `covid_viralscan/results_v3_strand_unstranded/` | 59 G | 121 G | 104 | 0 | 0 | 0 | **no** | (included above) | D3 |
| `results/` | 40 MiB | 80 MiB | 21 | 0 | 0 | 19 | no | `results/` | D4 |
| `benchmark_runs/` | 633 G | **1.2 T** | 131,906 | 3,000 | 114,806 | 0 | yes | `campaigns/benchmark_runs/` | D10 |
| `references/` | 64 G | 62 G | 52 | 0 | 0 | 0 | yes | `campaigns/reference_strategy/` | D7 |
| `starsolo_p22_6/` | 59 G | 54 G | 37 | 0 | 0 | 0 | yes | `campaigns/reference_strategy/` | D7 |
| `starsolo_p22_6b/` | 14 G | 12 G | 15 | 0 | 0 | 0 | yes | `campaigns/reference_strategy/` | D7 |
| `ebv_latest_ref_2026-09-27/` | 44 G | 77 G | 27,398 | 0 | 0 | 0 | no | `campaigns/ebv_latest_ref/` | D6 |
| `viral_panel_max_2026-09-28/` | 14 G | **34 G** | 348 | 0 | 0 | 0 | no | `campaigns/panel_max/` | D6 |

`analysis/*` contains 9 subdirectories plus the 2 top-level files above:

| Subdir | `du` | Apparent | Files | Tracked |
|---|---|---|---|---|
| `dedicated_tool_comparison/` | 72 K | 1.6 K | 1 | 1 |
| `hostresponse_ebv_matched/` | 2.6 M | 523 K | 24 | 20 |
| `ideas/` | 336 K | 30 K | 8 | 8 |
| `legacy_v2_v3/` | 880 K | 671 K | 15 | 15 |
| `multimap_profiling/` | 664 K | 154 K | 11 | 11 |
| `reference_strategy_benchmark/` | 808 K | 139 K | 15 | 15 |
| `truth_panel/` | 72 K | 1.7 K | 1 | 1 |
| `v3_ebv_baseline/` | 1.5 G | **4.5 G** | 10 | 2 |
| `v3_validation/` | 1.3 M | 430 K | 14 | 14 |

99 + 2 = 101 files; 87 + 2 = 89 tracked. `v3_ebv_baseline/` is the only
subdirectory not fully tracked: the two `.bus*` files are ignored by
`.gitignore:71-72` and account for 99.96% of the apparent size.

### Loose prose

Seven files, 86,916 B apparent total. Stage **D4**.

| Source path | Apparent | Tracked | Destination |
|---|---|---|---|
| `BENCHMARK_COMPARISON.md` | 24,606 B | yes | `prose/` |
| `docs/showcase_runbook.md` | 28,582 B | yes | `prose/` |
| `SESSION_RESUME.md` | 11,671 B | **no** | `prose/` |
| `reference_manifest.json` | 8,118 B | yes | `prose/` |
| `PROGRESS.md` | 6,437 B | yes | `prose/` |
| `reference_audit.tsv` | 4,626 B | yes | `prose/` |
| `docs/manuscript_draft.md` | 2,876 B | yes | `prose/` |

Five of these are at the repo root and two are under `docs/`.

`reference_manifest.json` and `reference_audit.tsv` embed absolute paths in
three families, only one of which is a moving target:

- `/exports/para-lipg-hpc/mdmanurung/ViralScan/references/starsolo/...` —
  10 and 7 occurrences. **Moves** to `campaigns/reference_strategy/`. Re-root.
- `/exports/para-lipg-hpc/mdmanurung/viralscan_showcase/...` — **moves** to
  `campaigns/showcase/`. Re-root.
- `/exports/archive/hg-funcgenom-research/evonk/old/intern/human_reference/...`
  and `.../conda/envs/starsolo/bin/STAR` — external, **stays**. Leave alone.

Re-rooting only the `starsolo/` values would leave the other two stale.

## Sibling directories, moving in

Source root: `/exports/archive/hg-funcgenom-research/mdmanurung`

| Source path | `du` | Apparent | Files | Sym | Hard | Destination | Stage |
|---|---|---|---|---|---|---|---|
| `viralscan_showcase/viralscan_showcase/` | 533 G | **1.4 T** | 6,466 | 8 | 0 | `campaigns/showcase/` | D9 |
| `viralscan_work/` | 155 G | 261 G | 2,805 | 112 | 0 | `campaigns/work/` | D8 |
| `viral_ref_final/` | 1.7 G | 3.7 G | 2,004 | 0 | 0 | `references/panel_final/` | D5 |
| `viral_ref_cat42/` | **12 G** | 29 G | **209** | 0 | 0 | `references/panel_cat42/` | D5 |
| `viral_ref_cat42b/` | 7.9 G | 20 G | 168 | 0 | 0 | `references/panel_cat42b/` | D5 |
| `_misc/viralscan_panel_ref/` | 2.0 G | 7.9 G | 15 | 0 | 0 | `references/panel_ref_july/` | D5 |
| `_misc/viralscan_panel_ref_genomic/` | 1.6 G | 3.7 G | 10 | 0 | 0 | `references/panel_ref_july/` | D5 |
| `viral_scan_probe/` | 272 M | 237 M | 34 | 0 | 0 | `probes/` | D5 |
| `viralscan_env_pinned/` | 4.2 G | 2.1 G | 71,616 | 1,761 | 51,001 | `envs/` **lock only** | — |

11,711 files total across the copied sibling trees.

Note the showcase path is nested one level deeper than its parent directory name
suggests: the source is `viralscan_showcase/viralscan_showcase/`.

### `viralscan_showcase/viralscan_showcase/` sub-areas

| Subdir | `du` | Apparent | Class |
|---|---|---|---|
| `fullrun/` | 446 G | 1.3 T | output + sbatch + refs; `sub/` is 284 GB of SRA scratch |
| `fullrun_evonk/` | 45 G | 84 G | output; runs evonk's installed v2.2.0 |
| `data/` | 30 G | 25 G | 6 FASTQ.gz + `GSE158275_RAW.tar` |
| `out_full_depth/` | 7.5 G | 14 G | output |
| `out_full_depth_wl/` | 4.1 G | 8.4 G | output |
| `dryrun/` | 610 M | 745 M | code + output |
| `emtest/` | 69 M | 130 M | code + output + BAM |
| `twostep/` | 263 M | 386 M | code + output |

8 symlinks under `fullrun/sub/` point at
`/exports/para-lipg-hpc/mdmanurung/viralscan_showcase/...`. **All 8 are
already broken** — each target is off by exactly one `viralscan_showcase/`
path component, because the `/exports/para-lipg-hpc` alias is itself a symlink
to the archive outer directory. Recreate at D9 with correct targets.

### `viralscan_work/` sub-projects

| Subdir | `du` | Apparent | Sym | Purpose |
|---|---|---|---|---|
| `hpv16_gse189670/` | **98 G** | 149 G | 0 | HPV16 control on GSE189670; calls the `viralscan` CLI |
| `f005_readorigin/` | 23 G | 31 G | 0 | read-origin forensics; stdlib-only script + minimap2 |
| `parity_mechA/` | 19 G | 45 G | **112** | legacy-v2 vs v3 parity; 6 frozen `src/viralscan` trees |
| `strand_test/` | 1.8 G | 2.0 G | 0 | `-N` / `--fr-unstranded` comparison; no scripts survive |
| `dataset_scoping_2026-09-30/` | 136 K | 15 K | 0 | 3 scoping markdown files |

Sub-row figures are `du -sh` of each subdirectory and do not sum exactly to
the tree total, which is `du -sh` of the whole. Both are as measured.

**The 112 symlinks in `parity_mechA/` are all absolute and point into**
`/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan/ebv_latest_ref_2026-09-27/runs/combined_corrected_5p/...`.
They resolve today. They break when `ebv_latest_ref_2026-09-27/` moves as
**D6** — so remediation belongs to D6 and D8, not only D9.

### `viral_ref_final/` note

`gtf/` and `logs/` are **empty** (0 files). Evidence that the reference build
is incomplete, worth recording before the tree is archived as lineage.

## Environments — exported, not copied

| Path | Size | Action |
|---|---|---|
| `viralscan_env_pinned/` | 4.2 G | export to `envs/viralscan_env_pinned.lock.yml` |

Python 3.8.20, **309** conda packages, `kb-python 0.28.2`, `snakemake 7.32.4`,
`kallisto 0.50.1`, `bustools 0.43.2`. No `viralscan` installed — the package
always came from the repo via `PYTHONPATH`.

89 files in `bin/` carry an absolute shebang into the env's own path: 39
`python3.8`, 30 `perl`, 20 `python`. Only `kb` and `snakemake` are the tools
that matter here, and both are Python scripts that would break. `kallisto` and
`bustools` are ELF binaries with no shebang and would survive a copy.

Stale relative to the `test_viralscan` stack (kallisto 0.51.1, bustools 0.45.1,
Python 3.12) that actually produced the showcase results.

## Staying in the package repo

`src/`, `tests/`, `schemas/`, `config/`, `claims/`, `extras/`, `data/`,
`scripts/`, public `docs/`, `provenance/`, `PLAN.md`, `.living/`, `todo/`,
`audits/`, `CLAUDE.md`, `CONTEXT.md`, `migration_plan/`.

Normative list: `MIGRATION_PLAN.md` §1 and §7. This list is a convenience copy
and must not drift from them.

Ship-scope member counts (re-verify at Phase C): wheel 63, sdist 107, docker 53, public_docs 13,
claim_bearing 3. Of everything moving, **exactly one** path is a member —
`analysis/v3_artifact_inventory.tsv`, sdist only.

## Measurement notes

### Hardlinks

114,806 of 131,906 files in `benchmark_runs/` have `nlink > 1`.

`legacy_v2_v3/conda_pkgs:` is the largest cluster: **48,941 files, 43,599 of
them hardlinked**, 5.2 GB apparent / 5.3 GB allocated. The trailing colon in
the directory name is a botched link target from a past run. Internally it
mirrors absolute `conda/pkgs/` paths.

Its hardlink partner is **`legacy_v2_v3/env_full/`**, not `conda/pkgs/` — the
inode is shared with `env_full/lib/R/library/...`, while the `conda/pkgs/`
counterpart is an independent copy with `nlink=1`. So the mirror is a hardlink
clone of the environment that produced the v2 baseline, which is
provenance-relevant rather than junk.

`viralscan_env_pinned/` holds a further 51,001 hardlinked files and 1,761
symlinks; it is exported rather than copied, so they do not affect the transfer.

### Symlinks

| Tree | Count | Broken | Absolute |
|---|---|---|---|
| `viralscan_showcase/` | 8 | **8** | 8 |
| `viralscan_work/` | 112 | 0 | 112 |
| `benchmark_runs/` | 3,000 | **25** | 1 |
| `viralscan_env_pinned/` | 1,761 | — | — |

`benchmark_runs/`'s single absolute link is
`legacy_v2_v3/env_bus/bin/python` → the shared `conda/envs/viralscan_bench`.
Its 25 pre-existing broken links are dangling `.so` references inside
`conda_pkgs:`. Both need a baseline so move-induced breakage is
distinguishable from what was already there.

### Storage-level compression

`fullrun/sub/hhv6_carT_ref/SRR24971475/SRR24971475_2.fastq`:
`stat` gives 199,851,204,802 B apparent and 119,285,040 × 512 B allocated —
187 GB / 57 GB. Probing 400 offsets at 64 KB found zero all-zero blocks, so the
data is genuinely present and Isilon is compressing underneath. Not corruption,
not truncation.

### rsync excludes affect expected counts

The copy excludes `__pycache__/` and `.snakemake/`. The showcase contains **763
files under 8 `.snakemake/` directories** plus **1 `__pycache__` file**, so its
expected destination count is **5,702**, not 6,466. All verification commands in
`CHECKSUMS.md` must apply the same exclusions.

## Generated artefacts

Phase A writes:

- `manifests/baseline_inventory.tsv` — path, size, mtime, sha256 per source path
- `manifests/stage_<ID>_source.sha256`, `stage_<ID>_dest.sha256`

Git-ignored: the whole-migration inventory is ~172,000 files, so a full sha256
manifest is roughly 19 MB, far past pre-commit's `--maxkb=500`.
