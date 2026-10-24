# Vendored frozen copies

Copied from ViralScan at `4da467487fcd2e58253c5d774d5a866254f295a3` so moved scripts/tests keep working. Do not edit; re-vendor when the package copy changes.

- `scripts/governance_utils.py`
- `extras/build_gene_programs.py`
- `extras/build_virus_catalog.py`

`scripts/governance_utils.py` is modified here: `package_fallback()` (two-root governance, split decision D39) resolves package-owned artifacts via `VIRALSCAN_PKG`; `scripts/validate_claim_registry.py` and `scripts/validate_artifact_inventory.py` use it.
