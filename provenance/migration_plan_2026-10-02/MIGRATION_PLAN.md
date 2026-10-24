# Migration plan

Authoritative plan for splitting `ViralScan` into a package repo plus the
`viralscan-analysis` project. `TRACKER.md` holds live status, `REVIEW.md`
records fact-check results. This file holds the design.

All sizes were re-measured on 2026-10-02; see `REVIEW.md` for what changed and
why. **Apparent size is the planning number** — it is what crosses the wire.

## 0. Governing rule

The source is never modified. No `rm`, no `mv`, no `git rm`, no rename, no
in-place edit of any source path. Every operation is additive: copy out,
checksum, verify, report. Deletion is Phase F and begins only on explicit
approval.

This rule is scoped to the **source** trees. Work inside the new analysis
project — authoring `paths.py`, creating the skeleton, recreating symlinks at
their new locations — is additive by definition and is not gated.

Two narrow exceptions live inside the package repo, both gated: **Phase C**
relocates one tracked file via `git mv` (byte-identical, history preserved,
accepted only when gates 2–4 pass), and **Phase F / §8** performs the approved
deletions and config edits with one confirmation per stage. See `README.md`
for the full scoping.

Consequences that shape the rest of the plan:

- Source stays byte-identical and functional, so existing paths and Slurm
  scripts keep working throughout. The compatibility-symlink layer an earlier
  draft required is unnecessary.
- The verified copy is the only thing that makes deletion recoverable. Isilon
  has no trash, so no stage advances without a checksum verdict.

**The repository is being modified concurrently.** HEAD has moved 28 commits
since first drafting (`8bfd136` → `d2845f6`) with active jobs writing hundreds
of GB into in-scope trees. Every baseline in `TRACKER.md` and `CHECKSUMS.md`
must be re-captured at Phase A execution time, never read from prose.

## 1. Target state

**Package repo** — `/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan`

Keeps `src/viralscan/`, `tests/`, `docs/` (public), `schemas/`, `config/`,
`claims/`, `extras/`, `scripts/`, `data/`, `provenance/`, `PLAN.md`, `.living/`,
`todo/`, `audits/`, `CLAUDE.md`, `CONTEXT.md`, `migration_plan/`. Contains no
analyses, no results, no references, no run outputs.

This list is normative. `INVENTORY.md` repeats it for convenience; the two must
not drift.

**Analysis project** — `/exports/para-lipg-hpc/mdmanurung/viralscan-analysis`

```
viralscan-analysis/
├── README.md
├── ANALYSIS_MANIFEST.md           # <- ViralScan/analysis/ANALYSIS_MANIFEST.md
├── DATA_MANIFEST.md               # created in Phase B, populated from Phase D
├── viralscan_analysis/            # importable helpers (created, not copied)
│   ├── paths.py                   # single source of truth for data locations
│   └── manifest.py
├── analyses/                      # <- ViralScan/analysis/* (less the two files above)
│   ├── hostresponse_ebv_matched/  legacy_v2_v3/     multimap_profiling/
│   ├── reference_strategy_benchmark/               truth_panel/
│   ├── dedicated_tool_comparison/                  ideas/
│   ├── v3_ebv_baseline/           v3_validation/
├── studies/covid/                 # <- ViralScan/covid_viralscan/
├── campaigns/
│   ├── showcase/                  # <- viralscan_showcase/viralscan_showcase/  1.4 TB
│   ├── work/                      # <- viralscan_work/                        226 GB
│   │   ├── hpv16_gse189670/  f005_readorigin/  parity_mechA/
│   │   ├── strand_test/  dataset_scoping_2026-09-30/
│   ├── benchmark_runs/            # <- ViralScan/benchmark_runs/              1.2 TB
│   ├── reference_strategy/        # <- references/, starsolo_p22_6/, starsolo_p22_6b/
│   ├── ebv_latest_ref/            # <- ebv_latest_ref_2026-09-27/
│   └── panel_max/                 # <- viral_panel_max_2026-09-28/
├── references/                    # reference-PANEL builds (lineage)
│   ├── panel_ref_july/            # <- _misc/viralscan_panel_ref{,_genomic}/
│   ├── panel_final/               # <- viral_ref_final/
│   └── panel_cat42/               # <- viral_ref_cat42/
│   └── panel_cat42b/              # <- viral_ref_cat42b/
├── probes/                        # <- viral_scan_probe/
├── prose/                         # <- 5 root-level files + 2 docs/ files
├── envs/
│   └── viralscan_env_pinned.lock.yml   # export only, NOT the 4.2 GB tree
├── results/                       # <- ViralScan/results/
└── check_analysis_split.py         # gate 6
```

`v3_artifact_inventory.tsv` does **not** appear in this tree. It stays in the
package repo at `provenance/` — see Phase C.

## 2. Phases

### Phase A — Freeze and baseline

1. Add `.gitignore` entries **before any commit**, for every
   untracked-but-not-ignored path (six at last count — re-enumerate; see
   `RISKS.md` R11). Committing first is
   the exact `git add .` sweep that risk describes.
2. Commit the modified governance files — **only after step 1**, or the
   commit is the `git add .` sweep R11 describes — so the starting point is
   unambiguous.
3. Re-capture and record: HEAD SHA, `git ls-files | wc -l`,
   `git status --porcelain` counts, and a full file-level inventory
   (path, size, mtime, sha256) into `migration_plan/manifests/`.
4. Summarise into `INVENTORY.md`.

That inventory is the rollback reference.

### Phase B — Scaffold the analysis project

The target currently holds a zero-byte `README.md`, a `.git` with no commits,
and a self-referential symlink `viralscan-analysis -> viralscan-analysis` that
resolves to nothing.

1. **Remove** that broken symlink. It lives in the *destination* project, not
   the source, so Rule 0 does not bind it. (An earlier draft said "fix", which
   implied preserving something; there is nothing to preserve — it is a
   self-loop.)
2. Create the tree from §1.
3. Write the project `README.md` and the `DATA_MANIFEST.md` schema. The schema
   is written here but **populated from Phase D onward** — gate 6 is evaluated
   only after D stages complete.
4. Copy `ANALYSIS_MANIFEST.md` in — this is a copy, part of stage D2, not a
   move. `TRACKER.md` previously listed it under Phase B, which would have
   required the file to exist at the destination before anything was copied.
5. Export `viralscan_env_pinned` to `envs/viralscan_env_pinned.lock.yml`
   (`conda env export`, read-only on the source tree) per `DECISIONS.md` S5.
6. `git init` has already run; make the first commit.

### Phase C — Re-root the artifact inventory

`analysis/v3_artifact_inventory.tsv` is the only analysis-side file inside the
shipped package. Six things reference it:

- `scripts/validate_artifact_inventory.py:36` — `DEFAULT_INVENTORY` hardcodes
  `REPO_ROOT / "analysis" / "v3_artifact_inventory.tsv"`
- `scripts/validate_claim_registry.py:40` — same default
- `tests/test_artifact_inventory.py:182` — the only test that reads the real
  file. `tests/test_claim_registry.py` imports just `INVENTORY_COLUMNS` and
  builds every fixture under `tmp_path`, so it is not a consumer of the file
- `MANIFEST.in:11`
- the `config/public_ship_scope.json` `sdist.members` entry
- `schemas/v3/artifact_inventory.schema.json`

**Two constraints the first draft of this plan got wrong.**

*The column name is taken.* `scope` is already a **required** field:
`schemas/v3/artifact_inventory.schema.json:38` lists it in `required`, `:71`
constrains it to `{"enum": ["public", "private"]}`, and
`scripts/validate_artifact_inventory.py:45` already carries it in
`INVENTORY_COLUMNS`. The TSV has 30 rows, 24 `public` and 6 `private`. Adding a
`scope` column would collide with shipped data and a CI-validated schema.

*The file cannot move and stay shipped.* `MANIFEST.in` lives inside the package
repo, and setuptools cannot add a file from a different repository to an sdist.
"Move it out and repoint the ship-scope member" is not implementable.

**Design.** Follow `DECISIONS.md` S3:

1. The TSV **stays physically in the package repo**, relocated
   `analysis/` → `provenance/`. One file, one copy, no generation step, no
   staleness risk on a claim-bearing artifact.
2. Add a **`location`** column, enum `package` | `analysis`. `scope` is left
   untouched.
   - `location=package` rows keep repo-relative paths and keep validating
     against the ViralScan checkout. Behaviour unchanged for all 30 existing
     rows.
   - `location=analysis` rows resolve against an `ANALYSIS_ROOT` environment
     variable, defaulting to the sibling checkout.
3. Backfill all 30 rows to `location=package`; add rows for analysis-side
   artifacts as each D stage verifies.
4. Update both validators to read the repo path and to consult `ANALYSIS_ROOT`
   for `location=analysis` rows, with a clear error when it is unset.
5. Extend the schema with the `location` enum and add it to `required`.
6. Repoint `MANIFEST.in:11` and the ship-scope sdist member to
   `provenance/v3_artifact_inventory.tsv`.
7. Update `tests/test_artifact_inventory.py`, and add a test that a
   `location=analysis` row resolves when `ANALYSIS_ROOT` is set and raises when
   it is not.

Because the sdist member count does not change, gate 2's expectation stays at
102.

### Phase D — Copy, small to large

Each stage: rsync, then verify, then stop and report. Never proceed past a
partial verify. `Apparent` is the wire volume; `du` is what the filesystem
reports.

**Symlink remediation happens inside Phase D, not after it.** 112 absolute
symlinks in `parity_mechA` point into `ebv_latest_ref_2026-09-27/`, which moves
as D6, so they break during D6 and must be re-pointed as part of D6 and D8.
Recreating them later would mean writing links whose targets no longer exist.

| Stage | Source | Apparent | `du` | Destination |
|---|---|---|---|---|
| D1 | *new files* — `viralscan_analysis/`, `check_analysis_split.py` | 0 | 0 | `viralscan_analysis/`, project root |
| D2 | `ViralScan/analysis/*` less the two top-level files | **4.5 GB** | 1.5 GB | `analyses/*` |
| D3 | `ViralScan/covid_viralscan/` | **495 GB** | 333 GB | `studies/covid/` |
| D4 | `ViralScan/results/` + 7 prose files | **84 MB** | 40 MiB | `results/`, `prose/` |
| D5 | `viral_scan_probe/`, `viral_ref_final/`, `viral_ref_cat42/`, `viral_ref_cat42b/`, `_misc/viralscan_panel_ref{,_genomic}/` | **64.5 GB** | 26 GB | `probes/`, `references/panel_*` |
| D6 | `ebv_latest_ref_2026-09-27/`, `viral_panel_max_2026-09-28/` | **111 GB** | 58 GB | `campaigns/ebv_latest_ref/`, `campaigns/panel_max/` |
| D7 | `references/`, `starsolo_p22_6/`, `starsolo_p22_6b/` | **128 GB** | 137 GB | `campaigns/reference_strategy/` |
| D8 | `viralscan_work/` | 261 GB | 155 GB | `campaigns/work/` |
| D9 | `viralscan_showcase/viralscan_showcase/` | **1.4 TB** | 533 GB | `campaigns/showcase/` |
| D10 | `ViralScan/benchmark_runs/` | **1.2 TB** | 633 GB | `campaigns/benchmark_runs/` |

Per-stage symlink work, all inside Phase D:

| Stage | Symlink work |
|---|---|
| D6 | the 112 `parity_mechA` links lose their targets as this stage moves the tree they point into. Record the break. |
| D8 | recreate all 112 against `campaigns/ebv_latest_ref/`, relative to the new parent. Verify all 112 resolve. |
| D9 | recreate the 8 `fullrun/sub/` links, correcting the off-by-one `viralscan_showcase/` component. Verify all 8 resolve. |
| D10 | 3,000 symlinks copy as-is with `-a`; confirm the count and that the 25 pre-existing broken links are still exactly 25 — no more, no fewer. |

- D1–D6: **675 GB apparent** — the full-sha256 tier.
- D7–D10: **2.99 TB apparent** — the bulk tier.
- Total: **~3.7 TB**.

D1 is a *creation* stage, not a copy. It has no source tree to hash, so its
criterion is "module imports and `--help` exits 0", recorded in `TRACKER.md`.
Its `CHECKSUMS.md` row carries `n/a` or `0` in every measured column, never a
verdict.

The two top-level files of `analysis/` are routed by D2 but land outside
`analyses/`: `ANALYSIS_MANIFEST.md` to the project root, and
`v3_artifact_inventory.tsv` **not copied at all** — it stays in the package repo
per Phase C.

One deliberate exception: `viralscan_env_pinned` (4.2 GB). Its `bin/` holds 89
shebanged files pointing at their own absolute path (39 `python3.8`, 30 `perl`,
20 `python`). Of the tools named earlier as affected, only `kb` and `snakemake`
are actually broken by a copy — both are Python scripts with that shebang.
`kallisto` and `bustools` are ELF binaries with no shebang and would survive.
The decision to export rather than copy stands on `kb` and `snakemake`. Export
to `envs/viralscan_env_pinned.lock.yml` and document that the showcase results
came from the newer `test_viralscan` stack (kallisto 0.51.1, bustools 0.45.1,
Python 3.12), not this Python 3.8 environment.

### Phase E — Verification report

Per-stage results into `CHECKSUMS.md`. Blockers and anomalies into `RISKS.md`.

### Phase F — Stop, await approval

Present the verification report and the exact deletion manifest. Delete
nothing until explicitly approved. On approval, deletion proceeds
**stage-by-stage with a per-stage confirmation** — ten separate rows, not one.

## 3. Copy mechanics

```
rsync -aH --sparse --info=progress2 --partial --append-verify \
      --exclude='__pycache__/' --exclude='.snakemake/' \
      SRC/ DST/
```

No `-e ssh`. Source and destination are NFS4 mounts on the same host and `DST`
is a local path; the earlier draft's `ssh` option was spurious.

- `-H` is **mandatory**. `benchmark_runs/legacy_v2_v3/conda_pkgs:` holds 43,599
  hardlinked files; without `-H` they expand and the structure is lost.
- `--partial --append-verify` makes an interrupted multi-hour run resumable and
  self-verifying.
- `--sparse` guards any genuinely sparse file.
- No `-z`. These are FASTQ, `.bus`, and `.idx`; compression would cost hours of
  CPU for no gain.
- **No `--delete`, ever.** Not in any invocation, not in any variant.
- Both filesystems are NFS4 on Isilon — no reflinks, no atomic
  snapshot-then-branch.
- Ownership may warn (non-root, mixed pools). Add `--no-group --no-owner` only
  if it does; content checksums are unaffected.
- Run under `nohup` with a per-stage log. D9 and D10 take hours.

**The excludes must be mirrored in every verification command.** They are not
optional bookkeeping: the showcase holds 763 files under 8 `.snakemake/`
directories plus 1 `__pycache__` file, so its expected destination count is
**5,702**, not 6,466. See `CHECKSUMS.md`.

## 4. Budget correction

`du` under-reports these trees, so apparent size, not `du`, is the capacity
number.

| Path | `du` | Apparent | Ratio |
|---|---|---|---|
| `benchmark_runs/` | 633 GB | **1.2 TB** | 1.84x |
| `viralscan_showcase/` | 533 GB | **1.4 TB** | 2.63x |
| `ViralScan/covid_viralscan/` | 333 GB | 495 GB | 1.49x |
| `viralscan_work/` | 155 GB | 261 GB | 1.68x |
| `ViralScan/analysis/` | 1.5 GB | 4.5 GB | 3.09x |
| `ebv_latest_ref_2026-09-27/` | 44 GB | 77 GB | 1.75x |
| `viral_panel_max_2026-09-28/` | 14 GB | 34 GB | 2.41x |
| `viral_ref_cat42/` | 12 GB | 29 GB | 2.42x |
| `viral_ref_cat42b/` | 7.9 GB | 20 GB | 2.53x |
| `references/` | 64 GB | 62 GB | **0.97x** |

Ratios are computed on unrounded byte counts, so they will not always
reproduce from the rounded figures printed here.

Two causes, both verified, and one exception:

- **Hardlinks** (`benchmark_runs` only, among trees being copied):
  114,806 of 131,906 files have `nlink > 1`. `conda_pkgs:` is the largest
  cluster — 48,941 files, 43,599 of them hardlinked.
  (`viralscan_env_pinned/` holds a further 51,001 hardlinked files, but it is
  exported rather than copied.)
- **Storage-level compression** (showcase):
  `SRR24971475_2.fastq` is 187 GB apparent / 57 GB allocated. Probing 400
  offsets found zero all-zero blocks, so the data is genuinely present and
  Isilon is compressing underneath. Not corruption, not truncation.
- **The exception:** `references/` and the STARsolo indices are *less* apparent
  than `du`, because their index files barely compress. Nothing is wrong; it
  just means those trees are the cheapest per byte to move.

Revised budget: **~3.7 TB apparent.** Target filesystem has 14 TB free.

## 5. Checksum strategy

Verifying 3.7 TB means reading ~7.3 TB in total (both sides: ~1.35 TB for
D1–D6 plus ~6.0 TB for D7–D10). Tiered:

- **D1–D6 (675 GB): full sha256 on both sides**, computed in parallel,
  compared line by line, exclude-aware.
- **D7–D10 (2.99 TB):** `rsync -c -aH --dry-run` (checksum comparison without
  transfer) with matching excludes, plus full sha256 on a 5% random sample and
  on **every** `.tsv`, `.json`, `.md`, `.yaml`, `.py`, `.sh`, `.sbatch`, and on
  every file with the executable bit set. All code, manifests, scripts, and
  result tables get full verification regardless of bulk.

This is the recommended option for `DECISIONS.md` Q1 and is stated as
operative here; Q1 must be answered before Phase D begins.

Manifests go to `migration_plan/manifests/`, git-ignored: the whole-migration
inventory is ~172,000 files, so a full sha256 manifest runs to roughly 19 MB
and pre-commit enforces `--maxkb=500`. Summaries and verdicts go into the
tracked `CHECKSUMS.md`.

## 6. Verification gates

| # | Gate | Expected |
|---|---|---|
| 1 | `PYTHONPATH=src python -m pytest tests/ -v` | all green, incl. `test_ship_scope.py`, `test_artifact_inventory.py`, `test_claim_registry.py`, `test_docs_consistency.py` |
| 2 | `python scripts/check_ship_scope.py` | 63 wheel / 107 sdist / 53 docker / 13 public_docs / 3 claim_bearing — unchanged in structure, since the inventory's sdist slot is retained (re-verify counts at Phase C) |
| 3 | `validate_artifact_inventory.py` + `validate_claim_registry.py` | all rows resolve; `location=analysis` rows resolve iff `ANALYSIS_ROOT` is set |
| 4 | `python -m build`, diff members vs `ship_scope.wheel` | no diff |
| 5 | `ruff check .` + `ruff format --check .` | **no new findings** — the repo has pre-existing `ruff check` errors and format deviations (re-count at Phase A; 30 and 22 as of the last measurement), none in `migration_plan/` |
| 6 | `check_analysis_split.py` | no analysis path leaks into the package; every `DATA_MANIFEST.md` entry resolves. Evaluated **after** Phase D, not at Phase B |
| 7 | end-to-end `viralscan` re-run from the new layout | completes |

## 7. What stays in the package repo

`src/`, `tests/`, `schemas/`, `config/`, `claims/`, `extras/`, `data/`,
`scripts/`, public `docs/`, `provenance/`, `PLAN.md`, `.living/`, `todo/`,
`audits/`, `CLAUDE.md`, `CONTEXT.md`, `migration_plan/`.

Verified against `config/public_ship_scope.json`: of everything moving,
**exactly one** path is a ship-scope member —
`analysis/v3_artifact_inventory.tsv`, sdist only. Everything else is already
unshipped.

## 8. Cleanup, after approval only

**Not to be started until Phase F is approved, and then only with a per-item
confirmation.** Listed here so the end state is unambiguous.

- `git rm -r` the moved tracked paths.
- Drop the obsolete `.gitignore` blocks and the corresponding `pyproject.toml`
  `ruff.extend-exclude` entries.
- Recreate the 112 `parity_mechA` symlinks and the 8 showcase symlinks against
  their new parents, or re-root them via `paths.py` — the answer to
  `DECISIONS.md` Q3. This is listed here only as a fallback: the real work is
  scheduled in D8 and D9 above, before the trees they point into are deleted.
- Update `CLAUDE.md`. Its layout block is already stale: it describes six
  Snakemake rules (v3 added gene programmes, evidence, host filter, cell
  calling) and "195 bundled viral reference annotations" (now fetched from
  Zenodo).
- Update the `docs/` index.
- Update `PLAN.md` in the same commit, per the CLAUDE.md contract.

Every item above is an in-place change to a tracked file — `analysis/`,
`results/`, `.gitignore`, `pyproject.toml`, `CLAUDE.md`, `docs/`, and `PLAN.md` —
which Rule 0 forbids absolutely. They are legitimate **only** because this
section is gated on approval, which is exactly why the gate exists. None of them
may be started on the strength of a Phase E report alone.

Deliberately **not** done: `git filter-repo --path analysis --invert-paths` to
scrub history. It would rewrite every commit SHA and invalidate the `git_sha`
pins in the artifact inventory, the claim registry, and the `.living` re-pins.
Plain `git rm`, after approval only, keeps history intact.
