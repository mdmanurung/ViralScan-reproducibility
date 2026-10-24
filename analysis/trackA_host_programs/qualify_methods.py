"""Small real-engine checks with independently specified shared/specific truth."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from setup_runtime import verify_runtime
from tracka_analysis import fit_method, project
from tracka_data import HERE, load_config, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(HERE / "config.json"))
    parser.add_argument("--output", type=Path, default=HERE / ".runtime/qualification")
    args = parser.parse_args()
    cfg = load_config(args.config)
    verify_runtime(cfg)
    cfg.update(maxiter=100, divas_nsim=40)
    rng = np.random.default_rng(20)
    n, p = 100, 80
    studies = np.repeat(["study_a", "study_b"], n // 2)
    cells = pd.DataFrame({"cell_id": [f"cell_{i}" for i in range(n)], "dataset": studies})
    genes = np.array([f"gene_{j}" for j in range(p)])
    true_shared = np.r_[np.ones(12), -np.ones(12), np.zeros(p - 24)]
    true_specific = np.r_[np.zeros(30), np.ones(12), -np.ones(12), np.zeros(p - 54)]
    shared_score = np.tile(np.r_[np.zeros(25), np.ones(25)], 2)
    specific_score = shared_score * (studies == "study_a")
    Y = (
        3
        + 1.5 * np.outer(shared_score, true_shared)
        + 1.5 * np.outer(specific_score, true_specific)
        + rng.normal(0, 0.1, (n, p))
    )
    cases = {
        "overlapping": Y,
        "null": 3 + rng.normal(0, 0.1, (n, p)),
        "study_confounded": 3
        + np.outer((studies == "study_a").astype(float), true_specific)
        + rng.normal(0, 0.1, (n, p)),
    }
    results = []
    args.output.mkdir(parents=True, exist_ok=True)
    for case, expression in cases.items():
        for method in cfg["methods"]:
            directory = (args.output / case / method).resolve()
            F = fit_method(cfg, method, expression, cells, genes, 4, 1, directory)
            result = {
                "case": case,
                "method": method,
                "status": "method_failed_or_unqualified" if F is None else "engine_executed",
            }
            if F is not None:
                scores = project(expression, F)
                result["reconstruction_relative_mse"] = float(
                    np.mean((expression - scores @ F.T) ** 2) / np.mean(expression**2)
                )
                if case == "overlapping":
                    truth = np.vstack([true_shared, true_specific])
                    residual = truth - project(truth, F) @ F.T
                    recovered = 1 - np.sum(residual**2, axis=1) / np.sum(truth**2, axis=1)
                    result["truth_subspace_recovery"] = recovered.tolist()
                    shuffled = F[rng.permutation(p)]
                    random_residual = truth - project(truth, shuffled) @ shuffled.T
                    result["shuffled_gene_recovery"] = (
                        1 - np.sum(random_residual**2, axis=1) / np.sum(truth**2, axis=1)
                    ).tolist()
                    result["oracle_pass"] = bool(
                        np.all(recovered > 0.75)
                        and np.all(recovered > np.array(result["shuffled_gene_recovery"]) + 0.25)
                    )
                else:
                    result["interpretation"] = (
                        "execution_check_only_no_calibrated_false_positive_or_specificity_claim"
                    )
            results.append(result)
            write_json(
                args.output / "qualification.json",
                {
                    "results": results,
                    "full_cohort_run": False,
                    "scope": "small_synthetic_native_engine_checks_not_scientific_calibration",
                    "upstream": json.loads((HERE / "upstream.json").read_text()),
                },
            )
            print(json.dumps(result), flush=True)
    if any(
        r["status"] != "engine_executed" or (r["case"] == "overlapping" and not r["oracle_pass"])
        for r in results
    ):
        raise SystemExit(
            "Method qualification incomplete; inspect qualification.json and native logs"
        )


if __name__ == "__main__":
    main()
