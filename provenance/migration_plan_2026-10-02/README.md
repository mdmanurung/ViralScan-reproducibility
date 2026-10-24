# Migration plan: split ViralScan into a package repo and an analysis project

This folder is the single auditable record of the package/analysis split. Start
here.

## What the migration does

`ViralScan` currently holds two things that should not live together: the
**shipped Python/Snakemake package**, and **~3.7 TB apparent of research
artefacts** — registered analyses, sub-studies, benchmark campaigns,
reference-panel builds, k-mer probes, run outputs, and indices.

The migration moves the research content to a separate project at
`/exports/para-lipg-hpc/mdmanurung/viralscan-analysis` and leaves the package
repo containing only package source, tests, and documentation.

**3.7 TB is apparent size, not `du`.** `du` under-reports these trees by up to
3x, and in a few it over-reports. See `MIGRATION_PLAN.md` §4.

## Rule 0 — the source is never modified

This constraint overrides everything else in this folder.

- No `rm`, no `mv`, no `git rm`, no rename, no in-place edit of any source path.
- `rsync --delete` is never used, in any variant.
- Every operation is **additive**: copy out, checksum, verify, report.
- **Deletion is a separate phase (F), gated on explicit approval, one
  confirmation per stage.**
- The source stays byte-identical and functional throughout, so every existing
  Slurm script and path keeps working.
- There is no trash on Isilon. The verified copy is the only thing that makes
  deletion recoverable, which is why no stage advances without a checksum
  verdict.

Rule 0 is scoped to the **source** trees. Additive work inside the new analysis
project — authoring `paths.py`, creating the skeleton, removing the broken
self-symlink that lives there, recreating symlinks at their new locations — is
not gated.

Two deliberate, narrow exceptions live inside the package repo itself, and both
are gated, not silent:

- **Phase C** relocates one tracked file (`analysis/v3_artifact_inventory.tsv`
  → `provenance/`) via `git mv`. Content is byte-identical, history is
  preserved, and the move is accepted only when gates 2–4 pass.
- **Phase F / §8** performs the approved deletions and config edits, one
  confirmation per stage.

Everything else in the repo — every FASTQ, BAM, index, and result — is never
renamed, moved, or edited under any phase.

## Documents

| File | Purpose |
|---|---|
| `MIGRATION_PLAN.md` | The authoritative plan: phases, gates, copy mechanics |
| `TRACKER.md` | Live per-phase status, updated every session |
| `DECISIONS.md` | Open questions (`Q1`–`Q5`) and settled decisions (`S1`–`S8`) |
| `INVENTORY.md` | Every source path, size, counts, destination, stage |
| `RISKS.md` | 19 risks with mitigations and residuals |
| `CHECKSUMS.md` | Verification method and per-stage sign-off tables |
| `REVIEW.md` | Fact-check log: what was verified, what was wrong |
| `HANDOFFS/` | Dated session handoffs |

Generated artefacts, git-ignored because a full sha256 manifest of ~172,000
files is roughly 19 MB and pre-commit caps tracked files at 500 KB:

- `manifests/` — file inventories and sha256 manifests
- `runlogs/` — rsync and verification stdout

(`runlogs` rather than `logs`, because `.gitignore:66` has a bare `logs/` rule
that matches at any depth and would swallow the directory whole.)

## Why this folder is safe inside the package repo

Verified against the actual gates:

| Gate | Effect of this folder |
|---|---|
| `MANIFEST.in` | 46 `include`, 5 `prune`, 10 `exclude`, 1 `global-exclude`; no `graft`, no `recursive-include`. Zero occurrences of `migration_plan` — excluded from the sdist |
| `config/public_ship_scope.json` | Positive allowlist; zero occurrences — not a wheel, sdist, or docker member |
| `scripts/check_ship_scope.py` | Validates only listed members; never walks the repo root |
| `scripts/check_data_governance.py` | Scans `/exports/` paths only inside ship-scope files. **Load-bearing** — 8 of these documents contain `/exports/` and would fail if scanned |
| `tests/test_docs_consistency.py` | Hard-coded 6-file list, no globbing — no effect |
| `pyproject.toml` | `packages.find where = ["src"]` — the folder is not a package; `include-package-data = false`; no `setuptools_scm`, so the sdist does not auto-include tracked files |
| `ruff check` | Produces no diagnostics for `.md` |
| `ruff format` | **Does process these `.md` files** (verified: "12 files already formatted"). `ruff.extend-exclude` is a deny-list, not a `src/`+`tests/` allowlist, so the folder must stay format-clean |
| `.pre-commit-config.yaml` | `check-added-large-files --maxkb=500` — hence the git-ignored generated dirs |
| `CLAUDE.md` | Plain markdown: final newlines present, no trailing whitespace, no tabs |

Ship-scope member counts, for reference (re-verify at Phase C): wheel 63, sdist 107, docker 53,
public_docs 13, claim_bearing 3.

## How to use

1. Read `MIGRATION_PLAN.md`.
2. Check `TRACKER.md` for the current phase.
3. Answer open questions in `DECISIONS.md` — Q1 blocks Phase D, Q5 blocks
   Phase C.
4. After any work, update `TRACKER.md` and add a row to `CHECKSUMS.md`.
5. Write a dated file in `HANDOFFS/` at the end of a session.
6. If a number looks wrong, re-measure it and record the result in `REVIEW.md`.
   Prose in this folder has already been wrong about 80 times across four review
   passes; the filesystem is the only authority. See `REVIEW.md`.

Per the repository `CLAUDE.md` contract, `PLAN.md` must also be updated in the
same commit as any phase change.
