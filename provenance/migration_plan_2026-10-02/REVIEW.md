# Review log

Fact-check passes over this folder. Each pass re-measures the filesystem rather
than trusting earlier prose.

## Pass 1 — 2026-10-02, comprehensive

Four parallel read-only agents, partitioned by scope: package-repo numbers,
sibling-directory numbers, code references and gate safety, and internal
consistency across all eleven files then present in the folder. Every material claim was then re-verified
directly before being accepted as a correction.

**Result: 3 critical defects, 19 wrong numbers, 9 wrong or under-specified
facts, 7 undocumented conditions, 29 internal-consistency defects.** All
corrected in this pass, with a handful of second-pass residuals recorded below.

### Critical — design was unimplementable as written

**C1. The `scope` column already exists.** Phase C proposed "add a `scope`
column (`package` | `analysis`)". It is already a required field:

- `schemas/v3/artifact_inventory.schema.json:38` lists `scope` in `required`
- `:71` constrains it to `{"enum": ["public", "private"]}`
- `scripts/validate_artifact_inventory.py:45` already has it in
  `INVENTORY_COLUMNS`
- `analysis/v3_artifact_inventory.tsv` has **30 rows**, 24 `public` and 6
  `private`

Phase C would have collided with shipped data and a CI-validated schema.
Corrected: the new column is `location` (`package` | `analysis`), leaving
`scope` alone.

**C2. The ship-scope TSV cannot be shipped from the analysis project.** The
plan said to move `v3_artifact_inventory.tsv` into the analysis repo *and* keep
it in the sdist, by "repointing `MANIFEST.in` and the ship-scope sdist member to
the new location". `MANIFEST.in` lives inside the package repo; setuptools
cannot add a file from a different repository to an sdist. Those two
instructions are mutually exclusive.

Corrected to settled decision S3's mechanism: the TSV **stays physically in the
package repo**, relocated to `provenance/` because it is no longer part of an
`analyses/` tree. A new `location` column says which repo each row resolves
against; `ANALYSIS_ROOT` supplies the analysis one. Single file, no build step,
no cross-repo packaging.

### Critical — verification could never pass

**C3. The rsync excludes were absent from the verification commands.** The copy
excludes `__pycache__/` and `.snakemake/`; the `find … | sha256sum` and
`find … | wc -l` checks did not. The diff could therefore never be empty and
the file counts could never match, so D1–D6 were unverifiable as specified.
Concrete: the showcase holds **763 files under 8 `.snakemake/` directories**
plus 1 `__pycache__` file, so its expected destination count is **5,702**, not
the 6,466 the docs compared against. All verification commands are now
exclude-aware.

### Wrong numbers, all re-measured

| # | Was | Now | Where |
|---|---|---|---|
| 1 | D1–D6 tier "425 GB" | **411 GB** (the doc's own rows summed to 365 GB) | `MIGRATION_PLAN.md`, `CHECKSUMS.md`, `DECISIONS.md` |
| 2 | D7 = 62 GB | **128 GB** — the row named `starsolo_p22_6{,b}/` but priced only `references/` | `MIGRATION_PLAN.md`, `INVENTORY.md`, `DECISIONS.md` |
| 3 | D7–D10 tier "2.8 TB" | **2.95 TB** (rows summed to 2.89 TB) | `CHECKSUMS.md` |
| 4 | total "3.2 TB" | **~3.4 TB** | `MIGRATION_PLAN.md`, `RISKS.md`, `DECISIONS.md` |
| 5 | `analysis/` 1.5 GB apparent | **4.5 GB** — `du` value in an "Apparent" column | `MIGRATION_PLAN.md`, `INVENTORY.md` |
| 6 | `viral_panel_max` 14 GB | **34 GB apparent** (14 GB `du`) | `INVENTORY.md` |
| 7 | `viralscan_work/` 127 GB, 2,667 files | **141 GB, 2,677 files** | `INVENTORY.md` |
| 8 | `hpv16_gse189670/` 84 GB | **98 GB** | `INVENTORY.md` |
| 9 | `viral_ref_cat42/` 1017 MB, 14 files | **7.4 GB, 141 files** | `INVENTORY.md` |
| 10 | tracked files 583 | **589** | `CHECKSUMS.md` |
| 11 | "7 modified, ~35 untracked" | **3 modified, 26 untracked** (29 lines) | 3 docs |
| 12 | `starsolo_p22_6` 59 G / `6b` 14 G apparent left blank | **54 G / 12 G apparent** (apparent is *lower* than `du` here) | `INVENTORY.md` |
| 13 | `conda_pkgs:` "5.3 GB apparent" | **5.2 GB apparent**, 5.3 GB allocated | `INVENTORY.md` |
| 14 | 48,941 counted as hardlinks | **48,941 files, 43,599 hardlinked** | `HANDOFFS/2026-10-02-survey.md` |
| 15 | "~24 scripts" hardcode old paths | **29** (excluding 5 Snakemake-generated temp scripts) | `DECISIONS.md` |
| 16 | `test_docs_consistency.py` described as a "7-file allowlist" | **6 files** | `README.md`, `DECISIONS.md` |
| 17 | "310 conda packages" | **309** package records | `INVENTORY.md` |
| 18 | manifest "176,000 rows" scoped to two trees | those two trees hold **138,372**; the whole-migration total is **172,025** | `manifests/README.md` |
| 19 | D4 = 40 MB | **84 MB** (`results/` 83.5 MB apparent + prose 87 KB) | `MIGRATION_PLAN.md` |

### Wrong or under-specified facts

**F1. `conda_pkgs:` is hardlinked to `env_full/`, not `conda/pkgs/`.** Inode
36710641793 is shared with
`benchmark_runs/legacy_v2_v3/env_full/lib/R/library/Biobase/Code/DESCRIPTION`;
the `conda/pkgs/` counterpart is inode 38207369746 with `nlink=1`. The `-H`
requirement stands — 43,599 hardlinked files are real — but the *narrative* was
wrong, and the corrected reading is better for provenance: the mirror is a
hardlink clone of the environment that produced the v2 baseline results.

**F2. All 8 showcase symlinks are already broken.** Each target is off by
exactly one `viralscan_showcase/` path component, because
`/exports/para-lipg-hpc/mdmanurung/viralscan_showcase` is itself a symlink to
the archive outer directory. `RISKS.md` R9 claimed "the old location resolves
meanwhile, because the source is untouched" — false. Nothing currently depends
on those links resolving.

**F3. `kallisto` and `bustools` have no shebang.** They are ELF 64-bit
dynamically linked executables. Of the 89 shebanged files in
`viralscan_env_pinned/bin/`, 39 are `python3.8`, 30 `perl`, 20 `python`. Only
`kb` and `snakemake` (both Python scripts) are actually broken by a copy. The
conclusion — export, do not copy — still holds on those two.

**F4. `tmp/` does not exist.** `.tmp/` exists and is already ignored
(`.gitignore:23`). No action needed for either.

**F5. `ruff format` does process these `.md` files.** Verified:
`ruff format --check migration_plan/` reports "12 files already formatted".
The claim that the folder is inert to the lint gate was wrong in both halves —
`ruff.check` produces no diagnostics for `.md`, but `ruff format` formats them,
and `ruff.extend-exclude` is a deny-list, not a `src/`+`tests/` allowlist.

**F6. Gate 5's "clean" expectation is false today.** At the time,
`ruff check .` reported 29 errors and `ruff format --check .` would reformat 20
files. Both have since drifted (30 and 22 at last count). All are
pre-existing, in `ebv_latest_ref_2026-09-27/`,
`viral_panel_max_2026-09-28/`, `extras/vendor_sources/`, and `tests/`. Zero in
`migration_plan/`. The gate now expects "no new findings" rather than "clean".

**F7. An untracked-but-not-ignored path the earlier draft had missed.**
`covid_viralscan/results_v3_exploratory/` — 6.6 GB `du`, 14 GB apparent, 126
files, untracked, and `.gitignore:77-82` omits it. A `git add .` would stage
14 GB.

**F8. "five consumers" of the inventory listed seven files.** And
`tests/test_claim_registry.py` is not one of them: it imports only
`INVENTORY_COLUMNS` and builds every fixture under `tmp_path`. Only
`tests/test_artifact_inventory.py:182` reads the real file.

**F9. `-e 'ssh -o ServerAliveInterval=60'` is spurious.** Source and destination
are NFS4 mounts on the same host, and the destination is a local path.

### Undocumented conditions, now recorded

- **112 absolute symlinks** in `viralscan_work/parity_mechA/`, all pointing into
  `/exports/archive/.../ViralScan/ebv_latest_ref_2026-09-27/runs/combined_corrected_5p/...`.
  They resolve today and will break once `ebv_latest_ref_2026-09-27/` moves as
  D6 — so the remediation belongs to **D6 and D8**, not only D9.
- **3,000 symlinks** in `benchmark_runs/`, of which **25 are already broken**
  (dangling `.so` links inside `conda_pkgs:`) and 1 is absolute. D10 needed a
  symlink acceptance criterion and a pre-existing baseline.
- `viral_ref_final/gtf/` and `viral_ref_final/logs/` are **empty** — evidence
  that reference build is incomplete.
- `viralscan_env_pinned/` holds **51,001 hardlinked files** and 1,761
  symlinks, so "hardlinks (`benchmark_runs` only)" was imprecise.
- `covid_viralscan/results_v3_exploratory/` (F7) brings the untracked-not-ignored
  count to **four**; the earlier `tmp/` entry was the phantom fifth.
- `starsolo_p22_6{,_b}` in the target tree expands to a non-existent
  `starsolo_p22_6_b`.
- The repo is **being modified concurrently**. HEAD moved `8bfd136` →
  `bb52a3d` at 15:15, after these docs were first written, which is why the
  dirty-tree and tracked-file baselines drifted mid-review. Baselines must be
  captured at Phase A execution time, not baked into prose.

### Internal-consistency defects, all corrected

29 more, including: `DECISIONS.md` used `D1`–`D4` for open questions while
every other file used `D1`–`D10` for copy stages (renamed to `Q1`–`Q4`);
`INVENTORY.md` double-counted 1.5 GB inside D2; `INVENTORY.md` put
`viral_panel_max_2026-09-28/` in D6 while the plan and tracker did not; three
different "what stays in the package repo" lists; Phase B said "move in
`ANALYSIS_MANIFEST.md`" before any copy existed; Phase B said "fix" the broken
symlink where `TRACKER.md` said "remove" it; `RISKS.md` required `.gitignore`
hardening *before* any commit while `MIGRATION_PLAN.md` said commit *first*;
`INVENTORY.md` — the file enumerating everything Phase F will delete — never
mentioned that deletion needs approval; the deletion sign-off table had one row
for ten stages; `manifests/README.md` and `runlogs/README.md` assigned the same
two log filenames; `HANDOFFS/2026-10-02-survey.md` called Phase F `pending` when
`TRACKER.md` marks it `blocked`; and a truncated sentence in `RISKS.md` R3.

### Confirmed correct, kept as written

Every `du` figure in `INVENTORY.md`. Every file count that was stated. The
`benchmark_runs` hardlink census (114,806 of 131,906). The 8-symlink count and
target prefix. `SRR24971475_2.fastq` at 187 GB apparent / 57 GB allocated. The
89-file shebang count. All four `viralscan_env_pinned` version pins, its Python
3.8.20, and the absence of any `viralscan` install in it. The 6 frozen
`src/viralscan` trees in `parity_mechA`. `strand_test/` having no scripts. The
showcase's zero hardlinks. All code line references
(`validate_artifact_inventory.py:36`, `validate_claim_registry.py:40`,
`MANIFEST.in:11`, `.gitignore:66`, `:71-72`, `:77-82`, `pyproject.toml:92-101`).
The claim that exactly one moving path is a ship-scope member, with all five
member counts exact. Both CLAUDE.md quotes. And the `.gitignore` work done in
the first session, including the `runlogs` rename forced by the bare `logs/`
rule.

## Pass 2

Re-ran after the corrections: all tables programmatically checked clean,
arithmetic re-derived independently, gates re-verified. Residuals above were
either fixed or explicitly recorded as acceptable. See `HANDOFFS/` for the
session record.

## Pass 3 — drift review, 2026-10-02 evening

Three parallel read-only agents plus direct re-measurement. The repo kept
moving: HEAD advanced to `b9274c9` (25 commits past the first reading), tracked
files 600 → 604, and active jobs wrote ~230 GB of new apparent bytes into
in-scope trees — `covid_viralscan/` 266 GB → 495 GB, `viralscan_work/` 226 G →
261 G, `viral_ref_cat42/` 19 G → 29 G. A whole new sibling tree appeared:
`viral_ref_cat42b/` (7.9 GB `du` / 20 GB apparent / 168 files), a second CAT-42
build with its own `build.sbatch`, `quant_gse189670.sbatch`, and `regression.sbatch`.

Changes applied:

- D3 → 495 GB apparent (200 new files since first measurement); D5 → 64.5 GB (added cat42b);
  D6 → 111 GB; D8 → 261 GB. Tiers: **D1–D6 675 GB, D7–D10 2.99 TB, total
  ~3.7 TB.** Read amplification ~7.3 TB.
- `viral_ref_cat42b/` added to `INVENTORY.md`, the D5 row, and the §1 target
  tree (`references/panel_cat42b/`).
- `RISKS.md` R11 sizes refreshed; new **R20** for active compute writing into
  in-scope trees, with freeze-vs-accept options.
- Baselines re-stamped (`CHECKSUMS.md`, `TRACKER.md`).
- The "four untracked-not-ignored paths" wording that survived in
  `MIGRATION_PLAN.md:89` corrected to "every … (six at last count —
  re-enumerate)".
- `REVIEW.md` ruff figures annotated as drifted (29/20 → 30/22).

Standing note, now proven three times: **no number in these documents survives
contact with an active cluster.** Phase A must re-measure everything, and
Phase E must re-verify before any deletion.

## Pass 4 — drift + residual cleanup, 2026-10-02 evening

Two parallel agents (fresh consistency audit; live re-measurement) plus direct
verification. HEAD advanced to `d2845f6` (28 commits past first reading),
tracked files 604 → 606, `ruff check` errors 30 → 31, and ship-scope counts
moved wheel 59→63 / sdist 102→107 (cat42b became the shipped panel).

Changes applied:

- Ship-scope counts updated to 63/107 with "re-verify at Phase C" annotations
  in all gate tables (`README.md`, `MIGRATION_PLAN.md`, `TRACKER.md`,
  `CHECKSUMS.md`, `INVENTORY.md`, `RISKS.md`).
- `TRACKER.md` Phase A table gained the two `results_v3_strand_*` `.gitignore`
  rows (six total); `CHECKSUMS.md` Phase A criterion updated to match.
- `REVIEW.md` pass-1 "Now" column values annotated as historical snapshots
  (correct at pass-1 time; since drifted — see `INVENTORY.md` for current).
- Rule 0 scope clarified for Phase C's intra-repo `git mv` and Phase F edits
  (`README.md`, `MIGRATION_PLAN.md` §0).
- `DECISIONS.md` identifier convention fixed to allow stage references in
  `Blocks.` lines; tier labels standardized on D1–D6.
- Baselines re-stamped to `d2845f6` / 606 tracked / 31-line porcelain.

Note on pass-1 history: the wrong-numbers table below records what each value
**was corrected from and to at pass-1 time**. Those "Now" values were accurate
then and have since drifted further. Do not read current state from this
section — read `INVENTORY.md`.
