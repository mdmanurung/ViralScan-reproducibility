# CLAUDE.md (ViralScan-reproducibility)

Experiments and evidence for ViralScan; the package is a separate repo (`VIRALSCAN_PKG`, pinned in `provenance/PACKAGE_BASE_SHA`).

- Run experiments from here with `source env.sh && ./setup_links.sh`. Do not copy package code in; vendor frozen copies only via `VENDORED.md`.
- `PLAN.md` here tracks the experiment/validation work (the package keeps its own `PLAN.md`). Update it when you finish a step.
- Never commit the links created by `setup_links.sh` or large run outputs.
- Split provenance and decisions: `provenance/`; the original split tracker is in the package repo history / `provenance/migration_plan_2026-10-02/`.
