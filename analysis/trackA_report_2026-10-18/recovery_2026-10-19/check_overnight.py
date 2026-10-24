"""Check completed preparation and bounded fits without changing their outputs."""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

HERE = Path(__file__).resolve().parent
A = HERE.parents[1] / "trackA_host_programs"
sys.path.insert(0, str(A))
from tracka_analysis import fit_rejection, normalize_signatures  # noqa: E402

root = A / "outputs/cohort-preparation-20261019-v1"
with (root / "libraries.tsv").open() as handle:
    libraries = [r["library"] for r in csv.DictReader(handle, delimiter="\t") if r["included"] == "True"]
assert len(libraries) == 65
cells = 0
for library in libraries:
    directory = root / "prepared" / library
    receipt = json.loads((directory / "receipt.json").read_text())
    matrix = sparse.load_npz(directory / "host_counts.npz")
    genes = pd.read_csv(directory / "genes.tsv", sep="\t")
    table = pd.read_csv(directory / "cells.tsv.gz", sep="\t")
    assert receipt["library"] == library
    assert matrix.shape == (receipt["cells"], receipt["host_genes"])
    assert len(genes) == matrix.shape[1] and len(table) == matrix.shape[0]
    assert np.isfinite(matrix.data).all() and (matrix.data >= 0).all()
    cells += matrix.shape[0]
result = {"prepared_libraries": len(libraries), "prepared_cells": cells, "dimensions_and_finite_nonnegative_counts_checked": True, "source_files_rehashed_again": False, "full_cohort_models_run": False}
(HERE / "cohort_preparation_verified.json").write_text(json.dumps(result, indent=2) + "\n")
print(result, flush=True)

result = {}
for method in ("gbcd", "divas"):
    directory = A / "outputs/pilot-scaling-recovery-300genes-20261019-v1" / method
    request = json.loads((directory / "request.json").read_text())
    diagnostics = json.loads((directory / "diagnostics.json").read_text())
    table = pd.read_csv(directory / "signatures.tsv", sep="\t")
    genes = Path(request["genes"]).read_text().splitlines()
    assert table.gene_id.tolist() == genes
    values = table.iloc[:, 1:].to_numpy()
    assert np.isfinite(values).all()
    basis = normalize_signatures(values)
    assert np.isfinite(basis).all()
    rejection = fit_rejection(diagnostics)
    result[method] = {"technical_rejection": rejection, "finite_basis": True, "genes": len(genes), "final_rank": basis.shape[1], "elapsed_seconds": diagnostics["elapsed_seconds"], "warnings": diagnostics.get("warnings", []), "native_diagnostics": diagnostics["diagnostics"], "request": request, "production_scaling_qualified": False}
(HERE / "scaling_recovery_verified.json").write_text(json.dumps(result, indent=2) + "\n")
print({k: {p: v[p] for p in ("technical_rejection", "final_rank", "elapsed_seconds", "warnings")} for k, v in result.items()}, flush=True)
