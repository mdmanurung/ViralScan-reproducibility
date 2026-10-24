# Risks

Risk register for the migration. Update when a risk materialises, is mitigated,
or is retired.

Figures are re-measured; see `REVIEW.md`.

## Critical

### R1. Accidental deletion of source data

**Risk.** ~3.7 TB of unique research artefacts destroyed by a stray `rm -rf`,
and unrecoverable — Isilon has no trash.

**Mitigation.** Rule 0 in `README.md`: no `rm`, no `mv`, no `git rm`, no
rename, no in-place edit of any source path. Every operation is additive.
`--delete` is never used in any rsync invocation (`DECISIONS.md` S8). No stage
advances without a checksum verdict in `CHECKSUMS.md`. Deletion is Phase F,
gated on explicit approval with one confirmation per stage.

**Residual.** Low. The main residual is human error outside this process.

### R2. Interrupted multi-hour copy leaves a partial destination

**Risk.** D9 and D10 run for hours; a network drop or a Slurm preemption leaves
a half-written tree that looks complete.

**Mitigation.** `rsync --partial --append-verify` makes the run resumable and
self-verifying. Per-stage `nohup` logs in `migration_plan/runlogs/`.
Verification runs after the transfer completes, never during. A stage is marked
`pass` in `CHECKSUMS.md` only when file count, byte total, and checksums all
agree.

**Residual.** Low.

### R3. Hardlink structure silently destroyed

**Risk.** `benchmark_runs/` contains 114,806 hardlinked files. A copy without
`-H` expands them into independent copies: `conda_pkgs:` alone would roughly
double from 5.2 GB, and the fact that those files are shared with the
environment that produced the v2 baseline results would be lost.

**Mitigation.** `-H` is mandatory in the rsync invocation. After D10, confirm
the `nlink > 1` count still equals **114,806** and that `conda_pkgs:` still
holds **43,599** hardlinked files.

**Residual.** Low.

### R4. Verification cannot pass because excludes are unmirrored

**Risk.** The copy excludes `__pycache__/` and `.snakemake/`. If a verification
command omits those exclusions, the sha256 `diff` can never be empty, the file
counts can never match, and `rsync --dry-run` is never silent — so D1–D6 would
be unverifiable by construction and could never legitimately be marked `pass`.

**Mitigation.** `CHECKSUMS.md` defines the exclude-aware `find` predicate once
and requires it in every command. Expected counts are stated per stage, so the
showcase is 5,702 rather than 6,466.

**Residual.** Low, provided the predicate is used verbatim. This is the one
check most easily transcribed wrong, so it is worth eyeballing the first
invocation of each tier.

## High

### R5. Capacity overrun from under-reported sizes

**Risk.** `du` reports 633 GB for `benchmark_runs/` against 1.2 TB apparent;
533 GB for the showcase against 1.4 TB; 1.5 GB for `analysis/` against 4.5 GB.
Planning on `du` understates the transfer by up to 3x, and in a few trees
apparent is *lower* than `du`.

**Mitigation.** The plan budgets **3.7 TB apparent**, itemised per stage in
`MIGRATION_PLAN.md` §2 and §4. Target filesystem has 14 TB free. Monitor free
space per stage.

**Residual.** Low.

### R6. The shipped provenance artifact breaks the release

**Risk.** `analysis/v3_artifact_inventory.tsv` is referenced by
`MANIFEST.in:11`, the `config/public_ship_scope.json` sdist member,
`schemas/v3/artifact_inventory.schema.json`, and two validators plus one test.
A naive move breaks all of them.

**Mitigation.** Phase C lands the `location`-column design before any copy, so
validators never see a half-built state. `check_ship_scope.py`, both validators, and `python -m build` catch any
regression before a release — cite the commands, not gate numbers, since the
three gate tables in this folder are numbered differently. The file stays in the package repo, so the sdist member count
is unchanged in count (107 at last measurement; re-verify at Phase C).

**Residual.** Low.

### R7. Two divergent code paths already produce different numbers

**Risk.** Pre-existing, not caused by this migration, but the migration makes it
more visible. The showcase used repo 2.3.0 via `PYTHONPATH`; `fullrun_evonk`
ran evonk's installed 2.2.0; `parity_mechA` froze 6 separate `src/` trees
specifically to compare revisions.

**Mitigation.** Every analysis manifest records which code version produced its
numbers. Worth doing regardless of the migration.

**Residual.** Medium — this is a scientific-integrity concern that outlives the
file move.

### R8. `conda_pkgs:` provenance misread as junk

**Risk.** `benchmark_runs/legacy_v2_v3/conda_pkgs:` — trailing colon, a botched
link target from a past run — looks like a mirrored path tree worth discarding.
Deleting or excluding it on that basis would destroy the hardlink evidence for
the v2 baseline environment.

**Mitigation.** Copy it faithfully; it is explicitly not to be dropped
(`RISKS.md`, this register's own instruction). Record it in the Phase E report
as a *candidate* for exclusion, and let the user decide. Its hardlink partner
is `legacy_v2_v3/env_full/`, verified by inode — not the shared `conda/pkgs/`
cache, as an earlier draft of this plan claimed.

**Residual.** Low.

## Medium

### R9. Showcase symlinks are already broken, so nothing signals the breakage

**Risk.** The 8 symlinks under `fullrun/sub/` point one `viralscan_showcase/`
path component short of their real targets. All 8 are dangling *now*, before
any migration step, because `/exports/para-lipg-hpc/mdmanurung/viralscan_showcase`
is itself a symlink to the archive outer directory. An earlier draft claimed
"the old location resolves meanwhile, because the source is untouched" — that
is false.

**Mitigation.** Record the pre-migration state (8 links, 8 broken) as the
baseline in `CHECKSUMS.md`. Recreate them at D9 against the correct new parent
and record the new targets explicitly — a destination-side write with an
unspecified target is how the original bug happened. Report the pre-existing
breakage in the Phase E report so it is not misattributed to the move.

**Residual.** Low.

### R10. 112 parity symlinks break when D6 moves

**Risk.** `viralscan_work/parity_mechA/` holds 112 absolute symlinks, all
pointing into
`.../ViralScan/ebv_latest_ref_2026-09-27/runs/combined_corrected_5p/...`. They
resolve today and break the moment `ebv_latest_ref_2026-09-27/` moves as D6 —
so remediation belongs to **D6 and D8**, not only D9. Undocumented in the
original plan.

**Mitigation.** D6 and D8 both carry symlink rows in the `CHECKSUMS.md` sign-off
table. Baseline is 112 links, 0 broken.

**Residual.** Low.

### R11. `git add .` sweeps in large untracked data

**Risk.** Several paths are untracked but *not* ignored. As of the last
measurement there were **six** — and the count keeps changing as new runs
land, so re-enumerate at Phase A:

| Path | `du` | Apparent | Files |
|---|---|---|---|
| `ebv_latest_ref_2026-09-27/` | 44 G | 77 G | 27,398 |
| `viral_panel_max_2026-09-28/` | 14 G | 34 G | 348 |
| `covid_viralscan/results_v3_exploratory/` | 6.6 G | 14 G | 126 |
| `covid_viralscan/results_v3_strand_reverse/` | 53 G | 109 G | 96 |
| `covid_viralscan/results_v3_strand_unstranded/` | 59 G | 121 G | 104 |
| `sources/` | — | — | — |

The last three `covid_viralscan/results_v3_*` directories were omitted by
`.gitignore:77-82` and **appeared while this plan was being written** — the
count is not stable. A casual `git add .` would stage ~150 GB.

**Correction.** An earlier draft listed `tmp/` — it does not exist. The real
candidate is `.tmp/`, and `.gitignore:23` already ignores it, so it needs
nothing.

**Mitigation.** `.gitignore` entries first, **before any commit**
(`MIGRATION_PLAN.md` Phase A, step 1). This ordering is deliberate: committing
first is precisely the hazard.

**Residual.** Low.

### R12. `viralscan_env_pinned` breaks if copied naively

**Risk.** 89 files in its `bin/` carry absolute shebangs into the env's own
path. A copy yields an environment whose `kb` and `snakemake` cannot start.

**Correction.** `kallisto` and `bustools` are ELF binaries with no shebang and
would survive. An earlier draft named all four tools as broken; only two are.

**Mitigation.** Do not copy. Export to `envs/viralscan_env_pinned.lock.yml` and
document the actual provenance of the showcase results.

**Residual.** Low.

### R13. Ownership preservation warns on copy

**Risk.** Files are group-owned by different pools (`para-lipg-hpc-rw`,
`Domain Users`). Running as non-root, rsync cannot always preserve group.

**Mitigation.** Add `--no-group --no-owner` only if warnings appear, and record
that content checksums are unaffected. The `CHECKSUMS.md` sign-off table has an
`Own` column for the fallback, and the per-stage structural checks require the
deviation to be noted.

**Residual.** Low.

### R14. Manifests exceed pre-commit size limits

**Risk.** The whole-migration inventory is ~172,000 files, so a full sha256
manifest runs to roughly 19 MB and pre-commit enforces
`check-added-large-files --maxkb=500`.

**Mitigation.** `migration_plan/manifests/` and `migration_plan/runlogs/` are
git-ignored. Only summaries and verdicts are tracked, in `CHECKSUMS.md`.

**Residual.** Low.

### R15. Concurrent modification of the repository

**Risk.** The repo is being worked on while this plan is written. HEAD moved
`8bfd136` → `bb52a3d` → `5456a15` → `b9274c9` → `d2845f6` across four review passes,
tracked files went 583 → 604, and active jobs wrote ~230 GB of new apparent
bytes into in-scope trees. A baseline captured now may be stale by the time
Phase A runs, and a stage verified against a stale baseline proves nothing.

**Mitigation.** Every baseline is re-captured at Phase A execution time and
recorded in `TRACKER.md` and `CHECKSUMS.md`. Never read a baseline from prose.

**Residual.** Medium — another session could in principle modify a source tree
mid-copy.

### R16. 29 scripts hardcode the old paths

**Risk.** Measured: 29 `.py` / `.sh` / `.sbatch` files across the showcase and
`viralscan_work` hardcode `/exports/para-lipg-hpc/mdmanurung/{ViralScan,viralscan_showcase}`.
If the old locations are removed after deletion without keeping symlinks, every
one of them breaks at once. Unregistered in the original plan.

**Mitigation.** Answer `DECISIONS.md` Q3 before Phase F. Keeping the old paths
as symlinks costs nothing; rewriting onto `paths.py` is an afternoon of edits
across 29 files.

**Residual.** Low once Q3 is answered; unbounded while it is open.

## Low

### R17. Analysis project spans two filesystems

**Risk.** Source is NFS4 on the `mirror-lts` pool, target is NFS4 on
`nomirror-scratch`. Cross-filesystem copies are plain reads and writes; no
reflinks, no atomic snapshot-then-branch.

**Mitigation.** Accepted by design. `paths.py` in the analysis project makes the
duality explicit rather than implicit. No `ssh` transport is used; both are
local mount points on the same host.

**Residual.** Low.

### R18. `CLAUDE.md` and `docs/` drift

**Risk.** `CLAUDE.md`'s layout block is already stale — it describes six Snakemake
rules (v3 added gene programmes, evidence, host filter, cell calling) and "195
bundled viral reference annotations" (now fetched from Zenodo). Migration work
adds more drift.

**Mitigation.** Phase F cleanup updates `CLAUDE.md` and the `docs/` index, and
updates `PLAN.md` in the same commit per the CLAUDE.md contract.

**Residual.** Low.

### R19. Empty reference-build directories archived as complete

**Risk.** `viral_ref_final/gtf/` and `viral_ref_final/logs/` are empty.
Archiving the tree as finished reference lineage would misrepresent it.

**Mitigation.** Recorded in `INVENTORY.md`. Noted in the Phase E report.

**Residual.** Low.

### R20. Active compute writes into the trees being moved

**Risk.** Jobs are running *now*. Within a single day `covid_viralscan/` grew
266 GB → 495 GB apparent (strand-rerun outputs landing mid-review),
`viralscan_work/` grew 226 G → 261 G, `viral_ref_cat42/` grew 19 G → 29 G, and
a whole new sibling tree (`viral_ref_cat42b/`, 20 GB) appeared. A file-level
inventory is stale within hours, and a stage verified in the morning can be
invalidated by an afternoon job writing into its source.

**Mitigation.** Two options, user's choice: (a) **freeze** — no new runs write
into in-scope trees from Phase A onward, so the baseline holds; (b) **accept
and re-verify** — treat the inventory as a lower bound and re-run verification
immediately before any deletion decision. Either way, re-measure every row at
Phase A and again at Phase E. Do not delete on the strength of a stale report.

**Residual.** Medium — this is the only risk that compounds with time.
