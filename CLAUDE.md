# CLAUDE.md (ViralScan-reproducibility)

Experiments and evidence for ViralScan; the package is a separate repo (`VIRALSCAN_PKG`, pinned in `provenance/PACKAGE_BASE_SHA`).

- Run experiments from here with `source env.sh && ./setup_links.sh`. Do not copy package code in; vendor frozen copies only via `VENDORED.md`.
- `PLAN.md` here tracks the experiment/validation work (the package keeps its own `PLAN.md`). Update it when you finish a step.
- Never commit the links created by `setup_links.sh` or large run outputs.
- Run tests against the **pinned** package, not the latest `main`: `git worktree add --detach <dir> $(head -1 provenance/PACKAGE_BASE_SHA)` in a package clone, then `VIRALSCAN_PKG=<dir> ./setup_links.sh` and `env -u VIRALSCAN_TCHEM -u VIRALSCAN_TCHEM_WHITELISTS VIRALSCAN_PKG=<dir> python -m pytest tests`. The governance ledgers pin package file hashes at that sha; against a newer `main` five tests fail by design (re-pin the ledgers deliberately to move the pin forward).
- Split provenance and decisions: `provenance/`; the full split tracker (decisions D1-D46, change log) is `SPLIT_TRACKER.md` here (written for the package-side agents; its absolute paths are local to the author's machine).
