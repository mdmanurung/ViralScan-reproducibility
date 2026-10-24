# Handoff — reviewed ViralScan roadmap implementation

**Date:** 2026-10-20 · **Candidate:** `codex/reviewed-roadmap` @ `6bf4c62` · **Status:** local implementation verified; real-data map qualification and CI pending.

## Goal
Deliver WP-1–5 and WP-9 from the reviewed roadmap without changing primary counts or detection; keep WP-6/8 deferred and WP-7 closed.

## Next action
Run `git -C /tmp/viralscan-reviewed-20261020 status --short`, then read `tmp/reviewed-roadmap-2026-10-20/RESULTS.md:1` and its remaining qualification section.
If the temporary clone is gone, use that document's bundle-recovery commands; do not apply patches directly to this stale dirty root.

## State
- Shared root: `codex/drop-py39` @ `5e551c9`, with extensive unrelated dirty/untracked work; never reset, clean, stash or stage wholesale.
- Candidate: `/tmp/viralscan-reviewed-20261020`, clean at `6bf4c62`, based on GitHub-confirmed main `9151da9` at implementation start.
- Commits A–F: `32b654f`, `0bb5e23`, `e1ab5e3`, `2f9b537`, `ecee46c`, `6bf4c62`; local only, no push/PR/merge.
- Final frozen-code suite: 5,921 passed, 15 skipped, 163 deselected; selected integration 15 passed; focused tests 292 passed.
- Ruff, mypy, Sphinx HTML, artifact inventory, data governance, wheel/sdist and ship-scope checks passed.
- Independent fixture runs preserved exact primary TSV/H5AD bytes, detected values and coverage TSVs; corrected derived percentage is 4.0% → 0.2%.
- Durable packet: `tmp/reviewed-roadmap-2026-10-20/`; six patches, combined patch, verified prerequisite bundle, dist artifacts, receipts and SHA256 manifest.
- No work/jobs were launched by this thread beyond local tests, synthetic fixtures and builds; other threads' scheduler state was not refreshed.

## Locked decisions
- Implement eligible software locally; no remote publication or scientific execution authorized by this task (user, 2026-10-20).
- Preserve X, allocation layers, corrected molecules, detected, thresholds, dependencies and default DAG; figures use the authoritative called mask and host-only null.
- No `samtools depth -a`; only bounded viral zero filling; missing evidence abstains instead of becoming zero.
- WP-6/8 remain deferred; protocol stays draft with training/holdout execution false; claims registry is unchanged.
- Parallel CLI work retains its user-approved hard break (`viralscan run`, no aliases, follow-ups inside runs); reconcile overlapping parser/config/docs changes before integration.
- Carried-over boundaries: anello work stopped, no hnscc wave/reference expansion; deletion, scheduler submissions and external BLAST need their separate authorizations; rebase-only merges.

## Dead ends — do not redo
- Editing the shared stale root: it lacks the baseline implementation and contains unrelated work; use the isolated candidate or bundle.
- System `python3` is 3.6; use `viralscan_test_full/bin/python` with `PYTHONPATH=src` and writable NUMBA/MPL caches as documented in RESULTS.
- Viral-positive called barcodes are not the complete denominator; default summary must resolve called_cells.tsv or fail.
- Transcript references must not receive incompatible genome tracks; a nonvarying collision null must not produce a plausible p-value.
- Inventory commit pins go stale on rebase; refresh the output-reference pin after any rewritten source commit.

## Read first
- `tmp/reviewed-roadmap-2026-10-20/RESULTS.md:1` — delivery, exact commands, recovery and qualification limits.
- `tmp/reviewed-roadmap-2026-10-20/ACCEPTANCE.md:1` — A1–G2 ledger and resolved specification discrepancies.
- `docs/reviews/VIRALSCAN_REVISED_ROADMAP.md:1` and `docs/reviews/VIRALSCAN_IMPLEMENTATION_HANDOFF.md:1` — scope and implementation contracts.
- `HANDOFF_prev_2026-10-20_cli-unify-before-review.md:1` — preserved parallel CLI/Track A handoff; its status/job claims were not reverified.
- [Mycelium session memory](.mycelium/last-session.md) — separate Mycelium continuation state; not edited here.
- [.living/learnings.md](.living/learnings.md), heading beginning “2026-10-20 — STAR 2.7.11b segfaults in Solo” — preserved parallel-work dead end.

## Open items
- WP-3: qualify against a permitted existing real evidence BAM directory; bounded searches found none. C1–C8 and CLI pass on native synthetic fixtures.
- Insert/start–end confirmation remains unimplemented and explicitly not_assessed, including when BAMs exist; do not claim definitive swapping.
- CI and independent pre-merge review are pending; local test success is not scientific validation or release approval.
- Reconcile overlap with `../vs_work/cli-unify` before landing; do not adopt its older handoff's CI/e2e assertions as current evidence.
- Other Track A, performance and approval work stays with its existing handoffs/owners; do not resume jobs, deletion or anello experiments from this handoff.
