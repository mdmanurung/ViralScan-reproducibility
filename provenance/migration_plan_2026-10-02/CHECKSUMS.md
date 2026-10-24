# Checksums

Verification method and the per-stage sign-off table. **No stage advances
without a passing row here.**

## The excludes must be mirrored

The copy excludes `__pycache__/` and `.snakemake/`
(`MIGRATION_PLAN.md` §3). Every verification command below applies the *same*
exclusions. Without them the sha256 diff can never be empty, the file counts can
never match, and `rsync --dry-run` is never silent — so the stage would be
unverifiable by construction.

The `find` predicate used throughout:

```
EXC = \( -path '*/__pycache__' -o -path '*/.snakemake' \) -prune -o -type f -print
```

Concrete effect: the showcase holds 763 files under 8 `.snakemake/` directories
plus 1 `__pycache__` file, so its expected destination count is **5,702**, not
6,466.

## Method

### Full verification — stages D1 to D6 (675 GB apparent)

Both sides hashed, in parallel, compared line by line.

```
find SRC \( -path '*/__pycache__' -o -path '*/.snakemake' \) -prune -o \
     -type f -print0 | xargs -0 -P 6 -n 200 sha256sum | sort -k2 > stage_src.sha256
find DST \( -path '*/__pycache__' -o -path '*/.snakemake' \) -prune -o \
     -type f -print0 | xargs -0 -P 6 -n 200 sha256sum | sort -k2 > stage_dst.sha256
diff stage_src.sha256 stage_dst.sha256
```

A stage passes only when `diff` is empty. An empty diff on both sides also
proves nothing was added or dropped, since a missing path would appear as a
removed line.

D1 is excluded from this method: it is a *creation* stage with no source. Its
criterion is "module imports and `--help` exits 0", recorded in `TRACKER.md`.

### Bulk verification — stages D7 to D10 (2.99 TB apparent)

Hashing both sides means reading ~5.9 TB. Three complementary checks:

1. `rsync -c -aH --dry-run --exclude='__pycache__/' --exclude='.snakemake/' SRC/ DST/`
   — checksum comparison without transfer. **Silence means every file matches
   by content.** Any output line is a failure.
2. Full sha256 on a **5% random sample**, both sides, exclude-aware.
3. Full sha256 on **every** `.tsv`, `.json`, `.md`, `.yaml`, `.py`, `.sh`,
   `.sbatch`, **and every file with the executable bit set** — so all code,
   manifests, scripts, and result tables get full verification regardless of
   bulk. This is where silent corruption in a result table would surface.

A stage passes only when all three pass.

### Per-stage structural checks

| Check | Applies to | Expected |
|---|---|---|
| File count | all | equal, exclude-aware |
| Byte total | all | equal, `du -sb` (which implies `--apparent-size`) |
| Hardlink count | D10 | `nlink > 1` count = **114,806** |
| Symlink count | D6, D8, D9, D10 | see baseline table below |
| Symlink targets | D6, D8, D9 | D8 and D9 recreate against the new parent; all resolve |
| Executable bit | D2–D10 | preserved for every file copied with a set bit |
| Ownership | all | note any `--no-group` / `--no-owner` fallback used |
| Pre-existing broken links | D9, D10 | **unchanged from baseline** — 8 and 25 respectively |

Symlink baselines, measured before any copy:

| Tree | Total | Broken before | Absolute |
|---|---|---|---|
| `viralscan_showcase/` | 8 | 8 | 8 |
| `viralscan_work/` | 112 | 0 | 112 |
| `benchmark_runs/` | 3,000 | 25 | 1 |

The showcase's 8 are *already* broken — each target is off by one
`viralscan_showcase/` path component. Do not count them as move-induced damage.

## Sign-off table — copy stages

| Stage | Files | Bytes | sha256 / `-c` | Counts | Symlinks | Hardlinks | Own | Verifier | Date | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 | n/a (created) | 0 | n/a | n/a | 0 | 0 | n/a | — | — | pending |
| D2 | — | — | — | — | — | — | — | — | — | pending |
| D3 | — | — | — | — | — | — | — | — | — | pending |
| D4 | — | — | — | — | — | — | — | — | — | pending |
| D5 | — | — | — | — | — | — | — | — | — | pending |
| D6 | — | — | — | — | 112 break | — | — | — | — | pending |
| D7 | — | — | — | — | — | — | — | — | — | pending |
| D8 | — | — | — | — | 112 recreated | — | — | — | — | pending |
| D9 | 5,702 | — | — | — | 8 recreated | — | — | — | — | pending |
| D10 | — | — | — | — | 3,000 / 25 broken | 114,806 | — | — | — | pending |

Verdicts: `pending` · `pass` · `fail` · `partial`

## Sign-off table — non-copy phases

Required by this file's own rule that no phase advances without a row.

| Phase | Criterion | Expected | Verdict |
|---|---|---|---|
| A | `.gitignore` hardening precedes any commit; baseline captured | 6 paths ignored (re-enumerate); inventory in `manifests/` | pending |
| B | symlink removed; tree created; `DATA_MANIFEST.md` schema written; first commit | all present | pending |
| C | `check_ship_scope.py`, both validators, **and `python -m build`** all pass; `location` backfilled to 30 rows | 30 rows, all resolve; wheel members unchanged | pending |
| E | every D row above is `pass`; no open blocker | 10/10 pass | pending |
| F | deletion approved per stage | see deletion table | blocked |

## Repository gates

| Gate | Command | Expected | Status |
|---|---|---|---|
| 1 | `PYTHONPATH=src python -m pytest tests/ -v` | all green | pending |
| 2 | `python scripts/check_ship_scope.py` | 63 wheel / 107 sdist / 53 docker / 13 public_docs / 3 claim_bearing (re-verify at Phase C — counts drift with the repo) | pending |
| 3 | `python scripts/validate_artifact_inventory.py` | all rows resolve; `location=analysis` rows resolve iff `ANALYSIS_ROOT` set | pending |
| 4 | `python scripts/validate_claim_registry.py` | all rows resolve | pending |
| 5 | `python -m build`, diff members vs `ship_scope.wheel` | no diff | pending |
| 6 | `ruff check .` | no **new** findings (30 pre-existing at last count; re-count at Phase A) | pending |
| 7 | `ruff format --check .` | no **new** deviations (22 pre-existing at last count; re-count at Phase A) | pending |
| 8 | `check_analysis_split.py` (analysis repo) | no analysis path in the package | pending |
| 9 | one end-to-end `viralscan` re-run | completes | pending |

These 9 rows map onto the plan's 7 gates (`MIGRATION_PLAN.md` §6) as
1→1, 2→2, 3→3+4, 4→5, 5→6+7, 6→8, 7→9. Because the numbering differs, cite the
**command**, never a gate number, when referring to a gate from another
document. `python -m build` (row 5) is the gate that catches a packaging
regression, and it belongs to Phase C's acceptance criteria.

## Baseline

**Must be re-captured at Phase A execution time.** The repo is being modified
concurrently and aggressively. HEAD moved `8bfd136` → `bb52a3d` → `5456a15`
→ `b9274c9` → `d2845f6` within three review passes, tracked files went 583 → 606, and
`covid_viralscan/` grew 266 GB → 495 GB apparent as strand-rerun outputs
landed. Never read a baseline from prose; measure it.

| Item | Last measured (2026-10-02, ~15:20) |
|---|---|
| Package repo | `/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan` |
| Branch | `codex/viralscan-v3` |
| HEAD | `d2845f6` (28 commits past the first reading; re-capture at Phase A) |
| Tracked files | 606 |
| Working tree | 31 porcelain lines: 3 modified, 28 untracked |
| Remote | `git@github.com:mdmanurung/ViralScan.git` |
| Source free space | 20 TB |
| Target project | `/exports/para-lipg-hpc/mdmanurung/viralscan-analysis` |
| Target free space | 14 TB |
| Target git | initialised, 0 commits, no remote, broken self-symlink |

## Deletion sign-off — Phase F

**Nothing in this section may be actioned without explicit user approval.**
One row per stage, confirmed individually. The plan requires per-stage
confirmation, so a single aggregate row would defeat it.

| Stage | Verified above | Approval given | Deleted on | Confirmed by |
|---|---|---|---|---|
| D1 | n/a | **no** | — | — |
| D2 | pending | **no** | — | — |
| D3 | pending | **no** | — | — |
| D4 | pending | **no** | — | — |
| D5 | pending | **no** | — | — |
| D6 | pending | **no** | — | — |
| D7 | pending | **no** | — | — |
| D8 | pending | **no** | — | — |
| D9 | pending | **no** | — | — |
| D10 | pending | **no** | — | — |
