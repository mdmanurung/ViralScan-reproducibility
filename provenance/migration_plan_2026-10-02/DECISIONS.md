# Decisions

Open questions and settled decisions for the migration.

**Identifier convention.** Open questions are `Q1`–`Q5`. Settled decisions are
`S1`–`S8`. Copy stages are `D1`–`D10`; question IDs never use `D<n>`, but
`Blocks.` lines name the stages a question gates (e.g. "Stages D7, D10").
An earlier draft used `D1`–`D4` for questions, which collided with the
stage namespace across every other document.

An unanswered question blocks the phases named in "Blocks".

## Open — awaiting user decision

### Q1. Checksum strategy

**Question.** Verifying 3.7 TB means reading ~7.3 TB across both sides. Full
sha256 everywhere, or tiered?

**Options.**

1. Full sha256 everywhere. Strongest. ~10–20 h at NFS read speeds; 6 cores
   available.
2. **Tiered (recommended).** Full sha256 for D1–D6 (675 GB; D1 contributes 0 — creation stage, verified by import). For D7–D10,
   `rsync -c --dry-run` plus full sha256 on a 5% random sample, on every
   `.tsv`, `.json`, `.md`, `.yaml`, `.py`, `.sh`, `.sbatch`, and on every file
   with the executable bit set. All code, manifests, scripts, and result tables
   get full verification regardless of bulk.
3. Size + mtime only. Instant. Not recommended — mtime is not content.

**Note.** Option 2 is written into `MIGRATION_PLAN.md` §5 and `CHECKSUMS.md` as
the operative method so the documents are usable. If you prefer option 1, both
need editing; nothing has been copied yet, so nothing is wasted.

**Blocks.** Phase D.

**Decision.** _pending_

### Q2. Caches versus results

**Question.** `benchmark_runs/` (1.2 TB apparent) and the D7 STARsolo indices
(128 GB apparent) are caches, not results. Including them in the analysis
project forces a ~1.3 TB `.gitignore`. Keep them in the project, or leave them
in place with only a `DATA_MANIFEST.md` entry?

**Note.** Dropping D7 and D10 cuts the copy from ~3.7 TB to ~2.3 TB and saves
the most wall-clock time.

**Supersedes.** S2 partially — see that entry.

**Blocks.** Stages D7, D10.

**Decision.** _pending_

### Q3. Old paths after deletion

**Question.** Once deletion is approved and done, keep the old paths as
symlinks pointing at the new home, or rewrite the scripts that hardcode
`/exports/para-lipg-hpc/mdmanurung/{ViralScan,viralscan_showcase}` onto a
`paths.py` indirection?

**Measured.** **29** `.py` / `.sh` / `.sbatch` files across the showcase and
`viralscan_work` hardcode those paths, excluding 5 Snakemake-generated temp
scripts under `fullrun/.snakemake/scripts/` that the copy already skips. Note
`/exports/para-lipg-hpc/mdmanurung/viralscan_work` does not exist on disk — the
alias list contains `ViralScan`, `viralscan_showcase`, and the two
`viralscan_panel_ref*` entries only.

**Note.** During the copy this question is moot: the old paths stay valid,
because the source is untouched.

**Blocks.** Phase F cleanup.

**Decision.** _pending_

### Q4. `.living/` and `PLAN.md` placement

**Question.** `PLAN.md` and `.living/` stay in the package repo, so analysis
findings continue to be logged in the *package* repo's memory layer. Acceptable,
or split the layer?

**Note.** `CLAUDE.md:34-35` makes `PLAN.md` the mandatory in-flight tracker for
package work. Moving it breaks that contract unless the contract is rewritten
too.

**Blocks.** Nothing immediately.

**Decision.** _pending_

### Q5. Where `v3_artifact_inventory.tsv` physically lives

Raised by the pass-1 review. Settled decision S3 says "keep it shipped", but the
plan originally also said "move it to `analyses/`", and those are mutually
exclusive: `MANIFEST.in` lives in the package repo and setuptools cannot add a
file from a different repository to an sdist.

The plan now implements S3 literally — the file **stays in the package repo** at
`provenance/`, with a new `location` column for resolution. That needs no build
step and no vendored copy, which is why it is proposed rather than treated as
settled.

**Alternatives if you prefer the analysis project to own the master file:**

- (a) as planned: single file in the package repo, `location` column,
  `ANALYSIS_ROOT` for analysis rows.
- (b) master in the analysis project; the package repo holds a **generated**
  copy refreshed by a script and re-pinned by commit. Single source of truth,
  but adds a generation step and a staleness risk to a claim-bearing artifact
  that CI validates.
- (c) master in the analysis project; the package repo copy is refreshed
  manually each time. Worst of both.

**Recommendation.** (a). The file is small (15 KB), it is validated in CI, and
this repo already has a re-pin discipline for exactly this artifact. A
generation step would add a failure mode to a shipped provenance claim.

**Blocks.** Phase C.

**Decision.** _pending (proposed: a)

## Settled

### S1. The source is never modified

**Decision.** No `rm`, no `mv`, no `git rm`, no rename, no in-place edit of any
source path. Copy out, checksum, verify, report. Deletion is Phase F and
requires explicit approval, one stage at a time.

**Scope.** Source trees only. Additive work inside the new analysis project —
authoring `paths.py`, creating the skeleton, removing the broken self-symlink
that lives there, recreating symlinks at their new locations — is not gated.

**Rationale.** Isilon has no trash, so the verified copy is the only thing that
makes deletion recoverable. It also keeps the source functional throughout.

**Date.** 2026-10-02.

### S2. Move everything, by copy

**Decision.** All research content moves, including the multi-terabyte result
trees.

**Rationale.** The user chose full relocation. Feasible: the target filesystem
has 14 TB free against ~3.7 TB apparent.

**Partially superseded by Q2.** S2 settles the *policy* (move, don't leave
behind); Q2 asks whether the two cache trees are in scope for the move. The
earlier draft of this folder contradicted itself here — S2 declared full
relocation settled while Q2 (then numbered D2) reopened the same question.

**Date.** 2026-10-02.

### S3. The inventory keeps its ship-scope slot

**Decision.** `v3_artifact_inventory.tsv` remains a shipped, claim-bearing
artifact. It stays **physically in the package repo**, relocated
`analysis/` → `provenance/`, with paths re-rooted by a new `location` column.

**Corrected in pass 1.** The original wording said "re-root its `path` column",
while `MIGRATION_PLAN.md` Phase C said "add a `scope` column" — two different
mechanisms. Phase C now implements S3.

**Note.** The `location` column is required to be a *new* name: `scope` is
already a required field constrained to `public` | `private`, with 30 populated
rows.

**Date.** 2026-10-02.

### S4. Own git repo, no remote yet

**Decision.** `viralscan-analysis` gets its own git history. No remote is
configured for now.

**Rationale.** User's choice. Analysis is by definition not part of the
released package, so it should not share the package's version history. A
submodule was rejected: ~3.7 TB of results would make checkout painful.

**Date.** 2026-10-02.

### S5. `viralscan_env_pinned` is exported, not copied

**Decision.** Capture `envs/viralscan_env_pinned.lock.yml`; do not copy the
4.2 GB tree.

**Rationale.** 89 files in its `bin/` carry absolute shebangs into the env's
own path (39 `python3.8`, 30 `perl`, 20 `python`). Of the four tools originally
named as affected, only `kb` and `snakemake` are broken by a copy — both are
Python scripts with that shebang. `kallisto` and `bustools` are ELF binaries
with no shebang and would survive. The decision rests on `kb` and `snakemake`,
which is sufficient. The environment is also stale relative to what produced the
showcase results.

**Date.** 2026-10-02.

### S6. `migration_plan/` lives in the package repo

**Decision.** Track the plan in `ViralScan/migration_plan/`.

**Rationale.** Verified against every gate. `MANIFEST.in` is a positive
include-list (46 `include`, 5 `prune`, 10 `exclude`, 1 `global-exclude`, no
`graft` or
`recursive-include`) and `migration_plan` appears zero times in it, so the
folder is excluded from the sdist. `public_ship_scope.json` is a positive
allowlist; zero occurrences. `.dockerignore` opens with `**` followed by exact
`!` negations; zero occurrences. `check_data_governance.py` scans institutional
`/exports/` paths only inside ship-scope files — load-bearing, since 8 of the
12 documents here do contain `/exports/` and would fail if scanned.
`test_docs_consistency.py` uses a hard-coded 6-file list with no globbing.
`packages.find` is scoped `where = ["src"]`, so the folder is not a package.

**Two caveats recorded in `README.md`:** `ruff format` does process these `.md`
files, and `manifests/` + `runlogs/` are git-ignored because pre-commit enforces
`check-added-large-files --maxkb=500` — the log directory specifically because
`.gitignore:66` has a bare `logs/` rule that matches at any depth.

**Date.** 2026-10-02.

### S7. Git history is not rewritten

**Decision.** No `git filter-repo` to scrub `analysis/` from history.

**Rationale.** It would rewrite every commit SHA and invalidate the `git_sha`
pins in the artifact inventory, the claim registry, and the `.living` re-pins.
Plain `git rm` after approval keeps history intact.

**Date.** 2026-10-02.

### S8. The source is never rsynced with `--delete`

**Decision.** `--delete` appears in no invocation, in any variant, for the
whole migration. The destination is only ever written to, never reconciled
against the source.

**Rationale.** `--delete` combined with a mis-specified source path is the most
plausible route to losing the original data, and nothing in the plan needs it.
The source remains authoritative at its original path throughout, so there is
never a reason to propagate deletions.

**Date.** 2026-10-02 (added in pass 1).
