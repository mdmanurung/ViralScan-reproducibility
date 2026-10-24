"""Bounded production-feature resource check on two existing libraries."""
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.io import mmwrite

HERE = Path(__file__).resolve().parent
A = HERE.parents[1] / "trackA_host_programs"
sys.path.insert(0, str(A))
from setup_runtime import verify_runtime  # noqa: E402
from tracka_analysis import (  # noqa: E402
    fit_rejection,
    normalize_signatures,
    read_libraries,
    training_genes,
)

OUT = HERE.parent / "outputs/production-shape-probe-20261020"
CFG = json.loads((A / "cohort_preparation_20261019.json").read_text())
LIBRARIES = ["GSM3511335", "GSM4796271"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare():
    verify_runtime(CFG)
    OUT.mkdir(parents=True, exist_ok=True)
    assert not any(p.is_file() for p in OUT.rglob("*")), "Preserve any previous probe outputs"
    X, cells, genes = read_libraries(CFG, LIBRARIES)
    selected = training_genes(X, cells, CFG)
    Y = X[:, selected].toarray()
    assert Y.shape == (800, 3000) and np.isfinite(Y).all()
    assert cells.groupby("dataset").size().tolist() == [400, 400]
    inputs = [A / "outputs/cohort-preparation-20261019-v1/prepared" / library / artifact for library in LIBRARIES for artifact in ("receipt.json", "host_counts.npz", "cells.tsv.gz", "genes.tsv")]
    mmwrite(OUT / "expression.mtx", sparse.coo_matrix(Y))
    (OUT / "genes.txt").write_text("\n".join(genes[selected]) + "\n")
    cells.to_csv(OUT / "cells.tsv", sep="\t", index=False)
    for method in CFG["methods"]:
        directory = OUT / method
        directory.mkdir(exist_ok=True)
        request = {"matrix": str(OUT / "expression.mtx"), "genes": str(OUT / "genes.txt"), "cells": str(OUT / "cells.tsv"), "method": method, "rank": 10, "seed": 1, "maxiter": CFG["maxiter"], "nsim": CFG["divas_nsim"]}
        (directory / "request.json").write_text(json.dumps(request, indent=2) + "\n")
    receipt = {"scope": "two-library production-feature resource probe; not full-cohort qualification", "libraries": LIBRARIES, "shape": list(Y.shape), "rank": 10, "seed": 1, "maxiter": CFG["maxiter"], "divas_nsim": CFG["divas_nsim"], "engine_cap_seconds": 900, "prepared_inputs_sha256": {str(p): sha(p) for p in inputs}, "production_config_sha256": sha(A / "config.json"), "adapter_sha256": sha(A / "methods.R")}
    (OUT / "input_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


def fit(method):
    directory = OUT / method
    request = directory / "request.json"
    started = time.monotonic()
    command = ["timeout", "--signal=TERM", "--kill-after=10s", "900s", CFG["rscript"], "--vanilla", str(A / "methods.R"), "fit", str(request), str(directory)]
    with (directory / "fit.log").open("w") as log:
        process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    result = {"method": method, "command": command, "returncode": process.returncode, "elapsed_seconds": time.monotonic() - started, "peak_child_rss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss, "status": "timeout_900s" if process.returncode == 124 else "method_failed", "production_cohort_qualified": False}
    if process.returncode == 0:
        table = pd.read_csv(directory / "signatures.tsv", sep="\t")
        assert table.gene_id.tolist() == (OUT / "genes.txt").read_text().splitlines()
        F = table.iloc[:, 1:].to_numpy()
        assert np.isfinite(F).all() and np.isfinite(normalize_signatures(F)).all()
        diagnostics = json.loads((directory / "diagnostics.json").read_text())
        rejection = fit_rejection(diagnostics)
        result.update(status="method_unqualified" if rejection else "finite_bounded_basis", rejection=rejection, final_rank=F.shape[1], warnings=diagnostics.get("warnings", []))
    (directory / "probe_status.json").write_text(json.dumps(result, indent=2) + "\n")
    print(result, flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "prepare":
        prepare()
    else:
        assert sys.argv[1] in CFG["methods"]
        fit(sys.argv[1])
