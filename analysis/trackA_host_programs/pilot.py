"""Bounded real-data engine benchmark; no model selection or inference."""

import argparse
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from setup_runtime import verify_runtime
from tracka_analysis import fit_method, read_libraries, training_genes
from tracka_data import HERE, load_config, prepare, run_root, sha256, write_json

LIBRARIES = ["GSM3511335", "GSM4796271"]
METHODS = ["gbcd", "ebcd", "divas"]
ROOT = HERE / "outputs/pilot-20261019-v1"


def config(convergence_check=False, scaling_check=False):
    cfg = load_config(HERE / "config.json")
    cfg.update(
        output_root=str(
            HERE / "outputs/pilot-convergence-20261019-v2" if convergence_check else ROOT
        ),
        max_cells_per_library=100,
        max_cells_per_study=100,
        n_genes=80,
        min_detected_cells=5,
        ranks=[3],
        seeds=[1],
        maxiter=500 if convergence_check else 100,
        divas_nsim=40,
    )
    if scaling_check:
        cfg.update(
            output_root=str(HERE / "outputs/pilot-scaling-300genes-20261019-v1"),
            n_genes=300,
            maxiter=500,
        )
    return cfg


def worker(cfg, method):
    root = Path(cfg["output_root"])
    X, cells, genes = read_libraries(cfg, LIBRARIES)
    selected = training_genes(X, cells, cfg)
    Y = X[:, selected].toarray()
    assert Y.shape == (200, cfg["n_genes"]) and np.isfinite(Y).all()
    assert cells.groupby("dataset").size().tolist() == [100, 100]
    started = time.monotonic()
    F = fit_method(cfg, method, Y, cells, genes[selected], 3, 1, root / method)
    if F is not None:
        assert F.shape[0] == cfg["n_genes"] and np.isfinite(F).all()
    write_json(
        root / method / "benchmark.json",
        {
            "method": method,
            "elapsed_seconds": time.monotonic() - started,
            "peak_child_rss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
            "qualified_basis": F is not None,
            "matrix_shape": list(Y.shape),
            "studies": cells.groupby("dataset").size().to_dict(),
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=METHODS)
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument("--convergence-check", action="store_true")
    stage.add_argument("--scaling-check", action="store_true")
    args = parser.parse_args()
    cfg = config(args.convergence_check, args.scaling_check)
    root = Path(cfg["output_root"])
    run_root(cfg)
    verify_runtime(cfg)
    if args.method:
        worker(cfg, args.method)
        return
    if (root / "benchmark.json").exists():
        raise ValueError("Pilot already recorded; retain its immutable receipt")
    write_json(root / "pilot_config.json", cfg)
    for library in LIBRARIES:
        prepare(cfg, library)
    outcomes = {}
    for method in ["gbcd"] if args.convergence_check else METHODS:
        command = [sys.executable, str(Path(__file__).resolve()), "--method", method]
        if args.convergence_check:
            command.append("--convergence-check")
        if args.scaling_check:
            command.append("--scaling-check")
        with (root / f"{method}.log").open("w") as log:
            process = subprocess.Popen(
                command,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                outcomes[method] = {"returncode": process.wait(timeout=900)}
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                outcomes[method] = {"status": "timeout", "limit_seconds": 900}
    write_json(
        root / "benchmark.json",
        {
            "purpose": "technical real-data pilot; no biological inference",
            "libraries": LIBRARIES,
            "convergence_check": args.convergence_check,
            "scaling_check": args.scaling_check,
            "script_sha256": sha256(__file__),
            "workflow_sha256": sha256(HERE / "pilot.smk"),
            "method_outcomes": outcomes,
            "new_scheduler_jobs": 0,
        },
    )


if __name__ == "__main__":
    main()
