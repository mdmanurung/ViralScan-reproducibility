# CAT-40: kallisto inspect on the shipped and earlier panel indexes (2026-11-02)

Result: all four indexes give **max EC size 9,921 and 0 ECs discarded**. The shipped WP5 index matches the `viral_ref_final` baseline.

Package pin: `de55424`. Binary: kb's own kallisto 0.52.0 (the conda kallisto aborts on kb indexes, REL-16).
Command: `PKG=<pin worktree> ENV=<viralscan_test_full> scripts/cat40_inspect_indexes.sh data/runs/round_2026-11-02/cat08_cat40/cat40`
Records, raw text and index sha256: `data/runs/round_2026-11-02/cat08_cat40/cat40/` (`*.json`, `*.inspect.txt`, `index_sha256.txt`).

| Index (under `data/references/panel_builds/`) | targets | k-mers | D-list k-mers | unitigs | max EC size | ECs discarded |
|---|---|---|---|---|---|---|
| `viral_ref_wp5/build_7e5a2ce` (shipped tier) | 472,480 | 85,522,354 | 3,094,848 | 525,122 | 9,921 | 0 |
| `viral_ref_wp5/build_7e5a2ce_hostdlist` | 472,480 | 85,522,354 | 3,079,390 | 525,122 | 9,921 | 0 |
| `viral_ref_cat42d/build` | 471,944 | 84,860,192 | 3,094,720 | 519,971 | 9,921 | 0 |
| `viral_ref_final/build` (CAT-40 baseline) | 471,948 | 84,861,133 | 632,265 | 519,982 | 9,921 | 0 |

The WP5 records agree with the `index_inspect.json` the build wrote itself. No regression against the baseline. Whether 9,921 is acceptable stays the user's decision (PLAN, CAT-40).
