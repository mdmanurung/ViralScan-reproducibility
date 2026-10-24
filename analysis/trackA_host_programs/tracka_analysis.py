"""Host program discovery and nested, biological-unit-held-out prediction."""

import argparse
import hashlib
import itertools
import json
import os
import pickle
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.io import mmwrite
from scipy.optimize import linear_sum_assignment
from setup_runtime import verify_runtime
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from tracka_data import HERE, library_metadata, load_config, run_root, sha256, write_json


class Unevaluable(ValueError):
    """A design limitation, distinguished from a failed method execution."""


def normalized_counts(X):
    depth = np.asarray(X.sum(axis=1)).ravel()
    if (depth <= 0).any():
        raise ValueError("Zero host library size")
    result = sparse.diags(1e4 / depth) @ X
    result = result.tocsr()
    result.data = np.log1p(result.data)
    return result


def read_libraries(cfg, libraries, balance=True):
    """Bound fitting with label-blind caps; retain every held-out called cell."""
    root = Path(cfg["output_root"]) / "prepared"
    matrices, tables, genes = [], [], None
    for library in sorted(libraries):
        directory = root / library
        current = pd.read_csv(directory / "genes.tsv", sep="\t").gene_id.to_numpy()
        if genes is not None and not np.array_equal(genes, current):
            raise ValueError(
                "Prepared host gene universes differ; an explicit intersection is required"
            )
        genes = current
        cells = pd.read_csv(directory / "cells.tsv.gz", sep="\t", dtype={"time": str})
        X = sparse.load_npz(directory / "host_counts.npz")
        if X.shape != (len(cells), len(genes)):
            raise ValueError("Count/metadata dimensions differ")
        rng = np.random.default_rng(0)
        idx = np.sort(
            rng.choice(len(cells), min(len(cells), cfg["max_cells_per_library"]), replace=False)
        )
        if not balance:
            idx = np.arange(len(cells))
        matrices.append(X[idx])
        tables.append(cells.iloc[idx])
    if not matrices:
        raise Unevaluable("No training libraries")
    cells = pd.concat(tables, ignore_index=True)
    if cells.empty:
        raise Unevaluable("Selected libraries contain no frozen called cells")
    X = sparse.vstack(matrices, format="csr")
    if not balance:
        return normalized_counts(X), cells, genes
    keep = []
    for _, part in cells.groupby("dataset", sort=True):
        rng = np.random.default_rng(0)
        keep.extend(
            rng.choice(part.index, min(len(part), cfg["max_cells_per_study"]), replace=False)
        )
    keep = np.sort(keep)
    return normalized_counts(X[keep]), cells.iloc[keep].reset_index(drop=True), genes


def training_genes(X, cells, cfg):
    eligible = np.asarray((X > 0).sum(axis=0)).ravel() >= cfg["min_detected_cells"]
    for study in cells.dataset.unique():
        eligible &= np.asarray((X[cells.dataset.eq(study).to_numpy()] > 0).sum(axis=0)).ravel() > 0
    mean = np.asarray(X.mean(axis=0)).ravel()
    variance = np.asarray(X.multiply(X).mean(axis=0)).ravel() - mean**2
    eligible &= variance > 1e-10
    positions = np.flatnonzero(eligible)
    if len(positions) < 3:
        raise Unevaluable("Fewer than three common expressed variable host genes")
    return positions[np.argsort(-variance[positions], kind="stable")[: cfg["n_genes"]]]


def inner_split(cells):
    """Hold out units within each study, retaining every training study block."""
    validation = np.zeros(len(cells), dtype=bool)
    for _, part in cells.groupby("dataset", sort=True):
        units = sorted(part.biological_unit.unique())
        if len(units) >= 2:
            rng = np.random.default_rng(1)
            picked = rng.choice(units, max(1, len(units) // 5), replace=False)
            validation[part.index] = part.biological_unit.isin(picked)
    if not validation.any() or validation.all():
        raise Unevaluable("No independent unit available for inner validation")
    train = np.flatnonzero(~validation)
    test = np.flatnonzero(validation)
    if set(cells.iloc[train].biological_unit) & set(cells.iloc[test].biological_unit):
        raise ValueError("Biological unit leaked across inner split")
    return train, test


def normalize_signatures(F):
    norms = np.linalg.norm(F, axis=0)
    nonzero = norms > 1e-10
    if not nonzero.any():
        raise Unevaluable("Method returned no nonzero gene programs")
    # Keep zero columns so displayed program indices retain their native mappings.
    F = F / np.where(nonzero, norms, 1)
    signs = np.sign(F[np.argmax(np.abs(F), axis=0), np.arange(F.shape[1])])
    signs[signs == 0] = 1
    return F * signs


def project(Y, F):
    return np.linalg.solve(F.T @ F + np.eye(F.shape[1]) * 1e-6, (Y @ F).T).T


def project_batches(X, selected, F):
    if X.shape[0] == 0:
        return np.empty((0, F.shape[1]))
    return np.vstack(
        [project(X[i : i + 2048, selected].toarray(), F) for i in range(0, X.shape[0], 2048)]
    )


def reconstruction_error(Y, F, seed=0):
    """Infer validation-cell scores from 80% of genes; score the other 20%."""
    rng = np.random.default_rng(seed)
    held = np.sort(rng.choice(Y.shape[1], max(1, Y.shape[1] // 5), replace=False))
    observed = np.setdiff1d(np.arange(Y.shape[1]), held)
    scores = project(Y[:, observed], F[observed])
    return float(np.mean((Y[:, held] - scores @ F[held].T) ** 2))


def fit_rejection(diagnostics):
    native = diagnostics["diagnostics"]
    warnings = diagnostics.get("warnings", [])
    if isinstance(warnings, str):
        warnings = [warnings]
    if native.get("objective_decreased", False):
        return "objective_decreased"
    if native.get("convergence") == "iteration_limit":
        return "iteration_limit"
    details = diagnostics.get("warning_details", [])
    for i, warning in enumerate(warnings):
        if "maximum number of iterations reached" not in warning.lower():
            continue
        recorded_initialization = (
            diagnostics.get("method") == "gbcd"
            and isinstance(details, list)
            and len(details) == len(warnings)
            and isinstance(details[i], dict)
            and details[i].get("message") == warning
            and details[i].get("stage") == "initialization"
            and details[i].get("maxiter") == 25
        )
        if not recorded_initialization:
            return "iteration_limit"
    return None


def fit_method(cfg, method, Y, cells, genes, rank, seed, directory):
    directory.mkdir(parents=True, exist_ok=True)
    identity = {
        "method": method,
        "rank": int(rank),
        "seed": int(seed),
        "maxiter": cfg["maxiter"],
        "nsim": cfg["divas_nsim"],
        "matrix_sha256": hashlib.sha256(np.ascontiguousarray(Y).data).hexdigest(),
        "genes": genes.tolist(),
        "cell_ids": cells.cell_id.tolist(),
        "studies": cells.dataset.tolist(),
        "adapter_sha256": sha256(HERE / "methods.R"),
        "runtime_sha256": sha256(HERE / ".runtime/receipt.json"),
    }
    identity_hash = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    status_path = directory / "status.json"
    if status_path.exists():
        status = json.loads(status_path.read_text())
        if status.get("input_identity") != identity_hash:
            raise ValueError(
                "Cached fit inputs/runtime differ; choose a new immutable output directory"
            )
        if status["status"] != "ok":
            return None
        if status["signature_sha256"] != sha256(directory / "signatures.tsv"):
            raise ValueError("Cached signature changed after qualification")
        if fit_rejection(json.loads((directory / "diagnostics.json").read_text())):
            return None
        tab = pd.read_csv(directory / "signatures.tsv", sep="\t")
        if not np.array_equal(tab.gene_id.to_numpy(), genes):
            raise ValueError("Cached signature gene identities differ")
        return normalize_signatures(tab.iloc[:, 1:].to_numpy())
    mmwrite(str(directory / "expression.mtx"), sparse.coo_matrix(Y))
    (directory / "genes.txt").write_text("\n".join(genes) + "\n")
    cells[["cell_id", "dataset"]].to_csv(directory / "cells.tsv", sep="\t", index=False)
    request = {
        "method": method,
        "rank": int(rank),
        "seed": int(seed),
        "maxiter": cfg["maxiter"],
        "nsim": cfg["divas_nsim"],
        "matrix": str(directory / "expression.mtx"),
        "genes": str(directory / "genes.txt"),
        "cells": str(directory / "cells.tsv"),
    }
    write_json(directory / "request.json", request)
    write_json(directory / "input_identity.json", identity)
    env = dict(
        os.environ,
        R_LIBS=":".join(cfg["r_libraries"]),
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        BLIS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
    )
    with (directory / "fit.log").open("w") as log:
        result = subprocess.run(
            [
                cfg["rscript"],
                "--vanilla",
                str(HERE / "methods.R"),
                "fit",
                str(directory / "request.json"),
                str(directory),
            ],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    if result.returncode:
        write_json(
            status_path,
            {
                "status": "method_failed",
                "returncode": result.returncode,
                "input_identity": identity_hash,
                "log": str(directory / "fit.log"),
            },
        )
        return None
    tab = pd.read_csv(directory / "signatures.tsv", sep="\t")
    if not np.array_equal(tab.gene_id.to_numpy(), genes):
        raise ValueError("Native method changed feature identities")
    F = normalize_signatures(tab.iloc[:, 1:].to_numpy())
    diagnostics = json.loads((directory / "diagnostics.json").read_text())
    rejection = fit_rejection(diagnostics)
    if rejection:
        write_json(
            status_path,
            {
                "status": "method_unqualified",
                "reason": rejection,
                "input_identity": identity_hash,
                "native_outputs_retained": True,
            },
        )
        return None
    write_json(
        status_path,
        {
            "status": "ok",
            "final_rank": F.shape[1],
            "input_identity": identity_hash,
            "signature_sha256": sha256(directory / "signatures.tsv"),
        },
    )
    return F


def signature_stability(reference, fits, cfg):
    support = np.zeros(reference.shape[1], dtype=int)
    rows = []
    for seed, candidate in fits.items():
        similarity = np.abs(reference.T @ candidate)
        left, right = linear_sum_assignment(-similarity)
        for a, b in zip(left, right, strict=True):
            cosine = float(similarity[a, b])
            support[a] += cosine >= cfg["signature_cosine"]
            rows.append(
                {
                    "seed": seed,
                    "program": int(a),
                    "matched_program": int(b),
                    "absolute_cosine": cosine,
                }
            )
    return pd.DataFrame(rows), support / len(cfg["seeds"])


def learn_programs(cfg, method, X, cells, genes, directory):
    if method == "divas" and cells.dataset.nunique() < 2:
        raise Unevaluable("DIVAS gene-aligned comparison needs at least two study blocks")
    train, validation = inner_split(cells)
    selected = training_genes(X[train], cells.iloc[train].reset_index(drop=True), cfg)
    Ytrain = X[train][:, selected].toarray()
    Yval = X[validation][:, selected].toarray()
    ranks = [0] if method == "divas" else [k for k in cfg["ranks"] if k < min(Ytrain.shape)]
    candidates = []
    bases = {}
    for rank, seed in itertools.product(ranks, cfg["seeds"]):
        F = fit_method(
            cfg,
            method,
            Ytrain,
            cells.iloc[train],
            genes[selected],
            rank,
            seed,
            directory / "inner" / f"rank{rank}_seed{seed}",
        )
        if F is None:
            candidates.append(
                dict(rank=rank, seed=seed, error=None, status="method_failed_or_unqualified")
            )
            continue
        error = reconstruction_error(Yval, F)
        candidates.append(dict(rank=rank, seed=seed, error=error, status="ok"))
        bases[(rank, seed)] = F
    pd.DataFrame(candidates).to_csv(directory / "rank_validation.tsv", sep="\t", index=False)
    valid = [x for x in candidates if x["status"] == "ok"]
    if not valid:
        raise RuntimeError(f"Every {method} candidate failed qualification; inspect native logs")
    rank_errors = {
        rank: np.mean([x["error"] for x in valid if x["rank"] == rank])
        for rank in ranks
        if any(x["rank"] == rank for x in valid)
    }
    best_rank = min(rank_errors, key=lambda k: (rank_errors[k], k))
    best = min((x for x in valid if x["rank"] == best_rank), key=lambda x: (x["error"], x["seed"]))
    # Hyperparameter selection below uses the inner-training basis, never the outer fit.
    inner_basis = bases[(best_rank, best["seed"])]
    inner_info = dict(train=train, validation=validation, selected=selected, basis=inner_basis)
    selected = training_genes(X, cells, cfg)
    Y = X[:, selected].toarray()
    fits = {}
    for seed in cfg["seeds"]:
        F = fit_method(
            cfg,
            method,
            Y,
            cells,
            genes[selected],
            best_rank,
            seed,
            directory / "final" / f"seed{seed}",
        )
        if F is not None:
            fits[seed] = F
    if best["seed"] not in fits:
        raise RuntimeError(
            "The training-selected seed failed the final fit; no post-hoc substitution"
        )
    reference = fits[best["seed"]]
    native_path = directory / "final" / f"seed{best['seed']}" / "signatures.tsv"
    native_columns = pd.read_csv(native_path, sep="\t", nrows=0).columns[1:].tolist()
    stability, support = signature_stability(reference, fits, cfg)
    stability.to_csv(directory / "stability.tsv", sep="\t", index=False)
    pd.DataFrame(reference, index=pd.Index(genes[selected], name="gene_id")).to_csv(
        directory / "gene_signatures.tsv", sep="\t"
    )
    cells.to_csv(directory / "fitting_cells.tsv.gz", sep="\t", index=False)
    write_json(
        directory / "selection.json",
        {
            "rank": best_rank,
            "seed": best["seed"],
            "final_rank": reference.shape[1],
            "gene_ids": genes[selected].tolist(),
            "native_signature_file": str(native_path),
            "native_columns": native_columns,
            "score_interpretation": "canonical_signed_unit_norm_ridge_projection_not_native_posterior_membership",
            "gene_positions": selected.tolist(),
            "stability_support": support.tolist(),
            "successful_final_seeds": list(fits),
            "requested_seeds": cfg["seeds"],
            "inner_training_units": sorted(cells.iloc[train].biological_unit.unique()),
            "inner_validation_units": sorted(cells.iloc[validation].biological_unit.unique()),
            "rank_selection": "held_out_units_and_20_percent_genes_reconstruction",
        },
    )
    return reference, selected, support, inner_info


def depth_matched(cells):
    keep = []
    for _, part in cells.groupby(["library", "cell_type"], sort=True):
        bins = pd.qcut(np.log1p(part.host_depth), q=min(20, len(part)), duplicates="drop")
        for _, chunk in part.groupby(bins, observed=True):
            a, b = chunk.index[chunk.activity_label == 0], chunk.index[chunk.activity_label == 1]
            n = min(len(a), len(b))
            if n:
                rng = np.random.default_rng(0)
                keep.extend(rng.choice(a, n, replace=False))
                keep.extend(rng.choice(b, n, replace=False))
    return np.sort(np.asarray(keep, dtype=int))


def adjusted_slope(score, burden, cells):
    nuisance = np.column_stack(
        [
            np.ones(len(cells)),
            np.log1p(cells.host_depth),
            cells.mito_fraction,
            np.log1p(cells.n_genes),
        ]
    )
    x = np.log1p(np.asarray(burden, dtype=float))
    x = x - nuisance @ np.linalg.lstsq(nuisance, x, rcond=None)[0]
    y = score - nuisance @ np.linalg.lstsq(nuisance, score, rcond=None)[0]
    if np.std(x) < 1e-8 or np.std(y) < 1e-8:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def unit_inference(values, n_bootstrap):
    values = np.asarray(values, dtype=float)
    effect = float(np.mean(values))
    rng = np.random.default_rng(0)
    if len(values) < 2:
        return effect, None, None, None
    boot = np.mean(rng.choice(values, (n_bootstrap, len(values)), replace=True), axis=1)
    low, high = np.quantile(boot, [0.025, 0.975])
    if len(values) <= 16:
        signs = np.asarray(list(itertools.product([-1, 1], repeat=len(values))))
        pvalue = np.mean(np.abs(signs @ values / len(values)) >= abs(effect) - 1e-12)
    else:
        signs = rng.choice([-1, 1], (10000, len(values)))
        pvalue = (1 + np.sum(np.abs(signs @ values / len(values)) >= abs(effect))) / 10001
    return effect, float(low), float(high), float(pvalue)


def associations(scores, cells, support, cfg):
    rows = []
    for sensitivity in ("primary", "unique_viral", "depth_matched"):
        idx = depth_matched(cells) if sensitivity == "depth_matched" else np.arange(len(cells))
        sub = cells.iloc[idx].reset_index(drop=True)
        S = scores[idx]
        for (study, cell_type), context in sub.groupby(["dataset", "cell_type"], sort=True):
            for program in range(S.shape[1]):
                library_effects = []
                for _, part in context.groupby("library", sort=True):
                    if len(part) < cfg["min_class_cells"] * 2 or part.activity_label.nunique() < 2:
                        continue
                    if not part.target_resolved.all():
                        continue
                    burden = (
                        part.viral_cpm
                        if sensitivity != "unique_viral"
                        else part.viral_unique_molecules / part.host_depth * 1e6
                    )
                    effect = adjusted_slope(S[part.index, program], burden, part)
                    if effect is not None:
                        library_effects.append(
                            (part.biological_unit.iloc[0], bool(part.unit_known.all()), effect)
                        )
                units = pd.DataFrame(library_effects, columns=["unit", "known", "effect"])
                if units.empty:
                    rows.append(
                        dict(
                            dataset=study,
                            cell_type=cell_type,
                            program=program,
                            sensitivity=sensitivity,
                            n_units=0,
                            n_known_units=0,
                            effect=None,
                            ci_low=None,
                            ci_high=None,
                            pvalue=None,
                            descriptive_signflip_p=None,
                            stability_support=float(support[program]),
                            status="no_eligible_within_library_contrast",
                            inference_eligible=False,
                        )
                    )
                    continue
                unit_means = units.groupby("unit").effect.mean()
                effect, low, high, pvalue = unit_inference(
                    unit_means.to_numpy(), cfg["bootstrap_replicates"]
                )
                eligible = (
                    len(unit_means) >= cfg["min_biological_units"]
                    and units.known.all()
                    and cell_type != "unannotated"
                )
                rows.append(
                    dict(
                        dataset=study,
                        cell_type=cell_type,
                        program=program,
                        sensitivity=sensitivity,
                        n_units=len(unit_means),
                        n_known_units=int(units.groupby("unit").known.all().sum()),
                        effect=effect,
                        ci_low=low,
                        ci_high=high,
                        pvalue=pvalue if eligible else None,
                        descriptive_signflip_p=pvalue,
                        inference_eligible=bool(eligible),
                        stability_support=float(support[program]),
                        status="replicate_aware_association"
                        if eligible
                        else "descriptive_replication_or_annotation_limited",
                    )
                )
    return pd.DataFrame(rows)


def independent_exposure_associations(scores, cells, support, cfg):
    """Paired HSV-1 mock/time contrasts use source labels, never viral detection."""
    rows = []
    for (study, cell_type), context in cells.groupby(["dataset", "cell_type"], sort=True):
        for program in range(scores.shape[1]):
            if study != "hsv1":
                rows.append(
                    dict(
                        dataset=study,
                        cell_type=cell_type,
                        program=program,
                        sensitivity="independent_exposure",
                        n_units=context.biological_unit.nunique(),
                        effect=None,
                        ci_low=None,
                        ci_high=None,
                        pvalue=None,
                        inference_eligible=False,
                        stability_support=float(support[program]),
                        status="no_replicated_paired_mock_design",
                    )
                )
                continue
            for hour in ("1", "3", "5", "trend"):
                effects = []
                for _, unit in context.groupby("biological_unit", sort=True):
                    hour_values = unit.time.astype(str)
                    control = unit.independent_status.eq("uninfected")
                    treated = unit.independent_status.eq("infected")
                    if hour != "trend":
                        treated &= hour_values.eq(hour)
                    if (
                        control.sum() < cfg["min_class_cells"]
                        or treated.sum() < cfg["min_class_cells"]
                        or not unit.unit_known.all()
                    ):
                        continue
                    pair = unit[control | treated]
                    x = (
                        pd.to_numeric(pair.time).to_numpy()
                        if hour == "trend"
                        else pair.independent_status.eq("infected").astype(float).to_numpy()
                    )
                    effect = adjusted_slope(scores[pair.index, program], x, pair)
                    if effect is not None:
                        effects.append(effect)
                eligible = (
                    len(effects) >= cfg["min_biological_units"] and cell_type != "unannotated"
                )
                effect, low, high, pvalue = (
                    unit_inference(effects, cfg["bootstrap_replicates"])
                    if effects
                    else (None, None, None, None)
                )
                rows.append(
                    dict(
                        dataset=study,
                        cell_type=cell_type,
                        program=program,
                        sensitivity="independent_exposure_" + hour,
                        n_units=len(effects),
                        effect=effect,
                        ci_low=low,
                        ci_high=high,
                        pvalue=pvalue if eligible else None,
                        descriptive_signflip_p=pvalue,
                        inference_eligible=eligible,
                        stability_support=float(support[program]),
                        status="paired_source_label_contrast"
                        if eligible
                        else "insufficient_paired_source_label_units",
                    )
                )
    return pd.DataFrame(rows)


def discovery(cfg, method, scope):
    root = run_root(cfg)
    verify_runtime(cfg)
    meta = pd.read_csv(root / "libraries.tsv", sep="\t")
    meta = meta[meta.included & (True if scope == "pooled" else meta.dataset.eq(scope))]
    out = root / "discovery" / scope / method
    out.mkdir(parents=True, exist_ok=True)
    try:
        X, cells, genes = read_libraries(cfg, meta.library.tolist())
        F, selected, support, _ = learn_programs(cfg, method, X, cells, genes, out)
        all_scores, all_cells = [], []
        for library in sorted(meta.library):
            directory = root / "prepared" / library
            tab = pd.read_csv(directory / "cells.tsv.gz", sep="\t")
            counts = sparse.load_npz(directory / "host_counts.npz")
            normalized = normalized_counts(counts)
            scores = project_batches(normalized, selected, F)
            all_scores.append(scores)
            all_cells.append(tab)
        tab = pd.concat(all_cells, ignore_index=True)
        scores = np.vstack(all_scores)
        score_table = pd.DataFrame(scores, columns=[f"program_{k}" for k in range(scores.shape[1])])
        pd.concat([tab, score_table], axis=1).to_csv(
            out / "cell_scores.tsv.gz", sep="\t", index=False
        )
        pd.concat(
            [
                associations(scores, tab, support, cfg),
                independent_exposure_associations(scores, tab, support, cfg),
            ],
            ignore_index=True,
        ).to_csv(out / "associations.tsv", sep="\t", index=False)
        write_json(
            out / "status.json",
            {
                "status": "ok",
                "scope": scope,
                "method": method,
                "cells_projected": len(tab),
                "programs": F.shape[1],
                "scientific_claim": "exploratory",
            },
        )
    except Unevaluable as error:
        write_json(
            out / "status.json",
            {"status": "unevaluable", "reason": str(error), "method": method, "scope": scope},
        )
    except (RuntimeError, subprocess.SubprocessError) as error:
        write_json(
            out / "status.json",
            {"status": "method_failed", "reason": str(error), "method": method, "scope": scope},
        )


def outer_folds(meta):
    included = meta[meta.included].copy()
    folds = []
    for study in sorted(included.dataset.unique()):
        sub = included[included.dataset == study]
        folds.append(
            dict(
                name="study_" + study,
                design="leave_one_study_out",
                study=study,
                train=included[included.dataset != study].library.tolist(),
                test=sub.library.tolist(),
            )
        )
        sub = sub[sub.unit_known]
        if sub.biological_unit.nunique() < 3:
            folds.append(
                dict(
                    name="within_" + study + "_0",
                    design="within_study",
                    study=study,
                    train=[],
                    test=[],
                    reason="Fewer than three known biological units",
                )
            )
            continue
        for fold, (train, test) in enumerate(GroupKFold(3).split(sub, groups=sub.biological_unit)):
            folds.append(
                dict(
                    name=f"within_{study}_{fold}",
                    design="within_study",
                    study=study,
                    train=sub.iloc[train].library.tolist(),
                    test=sub.iloc[test].library.tolist(),
                )
            )
    return folds


def metrics(y, probability):
    if len(np.unique(y)) < 2:
        raise Unevaluable("Held-out labels have only one class")
    y = np.asarray(y)
    probability = np.clip(probability, 1e-8, 1 - 1e-8)
    calibration = []
    ece = 0.0
    for low in np.arange(0, 1, 0.1):
        idx = (probability >= low) & (probability < low + 0.1 + (1e-10 if low > 0.89 else 0))
        if idx.any():
            calibration.append(
                dict(
                    bin_low=float(low),
                    n=int(idx.sum()),
                    predicted=float(probability[idx].mean()),
                    observed=float(y[idx].mean()),
                )
            )
            ece += idx.mean() * abs(probability[idx].mean() - y[idx].mean())
    return dict(
        auroc=float(roc_auc_score(y, probability)),
        auprc=float(average_precision_score(y, probability)),
        brier=float(brier_score_loss(y, probability)),
        log_loss=float(log_loss(y, probability)),
        ece=float(ece),
        prevalence=float(y.mean()),
        n=len(y),
        calibration=calibration,
    )


def qc_features(cells):
    return np.column_stack(
        [np.log1p(cells.host_depth), cells.mito_fraction, np.log1p(cells.n_genes)]
    )


def classifier(C):
    return make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=2000, random_state=0))


def shuffled_labels(cells):
    y = cells.activity_label.to_numpy().copy()
    rng = np.random.default_rng(1)
    for _, part in cells.groupby(["library", "cell_type"], sort=True):
        bins = pd.qcut(part.host_depth, q=min(10, len(part)), duplicates="drop")
        for _, chunk in part.groupby(bins, observed=True):
            y[chunk.index] = rng.permutation(y[chunk.index])
    return y


def prediction_uncertainty(cells, predictions, cfg):
    if not cells.unit_known.all() or cells.biological_unit.nunique() < cfg["min_biological_units"]:
        return {"status": "insufficient_known_independent_test_units"}
    units = sorted(cells.biological_unit.unique())
    idx_by_unit = {u: np.flatnonzero(cells.biological_unit.eq(u)) for u in units}
    rng = np.random.default_rng(0)
    values = {name: [] for name in predictions}
    deltas = {name: [] for name in predictions if name != "QC_only"}
    skipped = 0
    for _ in range(cfg["bootstrap_replicates"]):
        idx = np.concatenate([idx_by_unit[u] for u in rng.choice(units, len(units), replace=True)])
        y = cells.activity_label.to_numpy()[idx]
        if len(np.unique(y)) < 2:
            skipped += 1
            continue
        baseline = roc_auc_score(y, predictions["QC_only"][idx])
        for name, probability in predictions.items():
            auc = roc_auc_score(y, probability[idx])
            values[name].append(
                [
                    auc,
                    average_precision_score(y, probability[idx]),
                    brier_score_loss(y, probability[idx]),
                ]
            )
            if name != "QC_only":
                deltas[name].append(auc - baseline)
    if not values["QC_only"]:
        return {"status": "all_cluster_bootstraps_single_class", "skipped": skipped}
    return {
        "status": "biological_unit_cluster_bootstrap",
        "n_units": len(units),
        "skipped": skipped,
        "intervals": {
            name: np.quantile(value, [0.025, 0.975], axis=0).tolist()
            for name, value in values.items()
        },
        "interval_metric_order": ["auroc", "auprc", "brier"],
        "delta_auroc_vs_QC": {
            name: np.quantile(value, [0.025, 0.975]).tolist() for name, value in deltas.items()
        },
    }


def predict_fold(cfg, method, fold_name):
    root = run_root(cfg)
    verify_runtime(cfg)
    meta = pd.read_csv(root / "libraries.tsv", sep="\t")
    fold = next(f for f in outer_folds(meta) if f["name"] == fold_name)
    out = root / "prediction" / fold_name / method
    out.mkdir(parents=True, exist_ok=True)
    try:
        if "reason" in fold:
            raise Unevaluable(fold["reason"])
        X, train_cells, genes = read_libraries(cfg, fold["train"])
        T, test_cells, test_genes = read_libraries(cfg, fold["test"], balance=False)
        if not np.array_equal(genes, test_genes):
            raise ValueError("Training and test gene identities differ")
        if set(train_cells.biological_unit) & set(test_cells.biological_unit):
            raise ValueError("Biological unit crossed outer fold")
        if set(train_cells.library) & set(test_cells.library):
            raise ValueError("Library crossed outer fold")
        # Do not train an apparent target-specific classifier on unresolved sibling signal.
        train_mask = train_cells.target_resolved | train_cells.groupby(
            "library"
        ).viral_molecules.transform("sum").eq(0)
        test_mask = test_cells.target_resolved | test_cells.groupby(
            "library"
        ).viral_molecules.transform("sum").eq(0)
        X, train_cells = X[train_mask.to_numpy()], train_cells[train_mask].reset_index(drop=True)
        T, test_cells = T[test_mask.to_numpy()], test_cells[test_mask].reset_index(drop=True)
        for label, cells in (("training", train_cells), ("test", test_cells)):
            counts = np.bincount(cells.activity_label.to_numpy(), minlength=2)
            if counts.min() < cfg["min_class_cells"]:
                raise Unevaluable(f"{label} has insufficient activity classes: {counts.tolist()}")
        F, selected, support, inner = learn_programs(cfg, method, X, train_cells, genes, out)
        train_scores = project(X[:, selected].toarray(), F)
        test_scores = project_batches(T, selected, F)
        inner_scores = project(X[:, inner["selected"]].toarray(), inner["basis"])
        train_qc, test_qc = qc_features(train_cells), qc_features(test_cells)
        responses = {
            "host_programs": (train_scores, test_scores, inner_scores),
            "host_programs_plus_QC": (
                np.c_[train_scores, train_qc],
                np.c_[test_scores, test_qc],
                np.c_[inner_scores, train_qc],
            ),
            "QC_only": (train_qc, test_qc, train_qc),
            "scrambled_host_programs_plus_QC": (
                np.c_[train_scores, train_qc],
                np.c_[test_scores, test_qc],
                np.c_[inner_scores, train_qc],
            ),
        }
        results = []
        predictions = test_cells.copy()
        probabilities = {}
        for name, (A, B, inner_A) in responses.items():
            y = (
                shuffled_labels(train_cells)
                if name.startswith("scrambled")
                else train_cells.activity_label.to_numpy()
            )
            a, b = inner["train"], inner["validation"]
            choices = []
            if min(np.bincount(y[a], minlength=2)) and min(np.bincount(y[b], minlength=2)):
                for C in cfg["classifier_C"]:
                    model = classifier(C).fit(inner_A[a], y[a])
                    probability = model.predict_proba(inner_A[b])[:, 1]
                    choices.append((log_loss(y[b], probability), C))
            C = min(choices)[1] if choices else 1
            model = classifier(C).fit(A, y)
            probability = model.predict_proba(B)[:, 1]
            predictions[name] = probability
            probabilities[name] = probability
            with (out / (name + "_classifier.pkl")).open("wb") as handle:
                pickle.dump(model, handle, protocol=5)
            result = metrics(test_cells.activity_label, probability)
            result.update(
                model=name,
                C=C,
                tuning="inner_unit_log_loss"
                if choices
                else "fixed_C1_single_class_inner_validation",
            )
            matched = depth_matched(test_cells)
            result["depth_matched"] = (
                metrics(test_cells.activity_label.iloc[matched], probability[matched])
                if len(matched)
                else {"status": "no_matches"}
            )
            result["by_cell_type"] = {}
            for cell_type, part in test_cells.groupby("cell_type", sort=True):
                result["by_cell_type"][cell_type] = (
                    metrics(part.activity_label, probability[part.index])
                    if part.activity_label.nunique() == 2
                    else {"status": "single_class"}
                )
            results.append(result)
        predictions.to_csv(out / "predictions.tsv.gz", sep="\t", index=False)
        write_json(
            out / "metrics.json",
            {
                "models": results,
                "fold": fold,
                "training_units": sorted(train_cells.biological_unit.unique()),
                "test_units": sorted(test_cells.biological_unit.unique()),
                "missing_cell_type_fraction": float(test_cells.cell_type.eq("unannotated").mean()),
                "unknown_unit_fraction": float((~test_cells.unit_known).mean()),
                "stability_support": support.tolist(),
                "phenotype": "cohort_relative_viral_transcription_not_infection_status",
                "evaluation_sampling": "all_frozen_called_cells_with_eligible_target_labels",
                "uncertainty": prediction_uncertainty(test_cells, probabilities, cfg),
            },
        )
        write_json(out / "status.json", {"status": "ok", "method": method, "fold": fold_name})
    except Unevaluable as error:
        write_json(
            out / "status.json",
            {"status": "unevaluable", "reason": str(error), "method": method, "fold": fold_name},
        )
    except (RuntimeError, subprocess.SubprocessError) as error:
        write_json(
            out / "status.json",
            {"status": "method_failed", "reason": str(error), "method": method, "fold": fold_name},
        )


def bh_adjust(values):
    values = np.asarray(values, dtype=float)
    order = np.argsort(values)
    ranked = values[order] * len(values) / np.arange(1, len(values) + 1)
    result = np.empty(len(values))
    result[order] = np.minimum.accumulate(ranked[::-1])[::-1].clip(0, 1)
    return result


def compare_programs(root):
    paths = [
        p
        for p in sorted(root.glob("discovery/*/*/gene_signatures.tsv"))
        if (p.parent / "status.json").exists()
        and json.loads((p.parent / "status.json").read_text())["status"] == "ok"
    ]
    rows = []
    for left, right in itertools.combinations(paths, 2):
        a_scope, a_method = left.parent.parent.name, left.parent.name
        b_scope, b_method = right.parent.parent.name, right.parent.name
        if not (a_scope == b_scope or (a_method == b_method and "pooled" in [a_scope, b_scope])):
            continue
        a = pd.read_csv(left, sep="\t", index_col=0)
        b = pd.read_csv(right, sep="\t", index_col=0)
        genes = a.index.intersection(b.index)
        if len(genes) < 3:
            continue
        A, B = (
            normalize_signatures(a.loc[genes].to_numpy()),
            normalize_signatures(b.loc[genes].to_numpy()),
        )
        similarity = np.abs(A.T @ B)
        x, y = linear_sum_assignment(-similarity)
        for i, j in zip(x, y, strict=True):
            rows.append(
                dict(
                    left_scope=a_scope,
                    left_method=a_method,
                    left_program=i,
                    right_scope=b_scope,
                    right_method=b_method,
                    right_program=j,
                    common_genes=len(genes),
                    absolute_cosine=float(similarity[i, j]),
                    interpretation="descriptive_alignment_not_independent_validation",
                )
            )
    pd.DataFrame(
        rows,
        columns=[
            "left_scope",
            "left_method",
            "left_program",
            "right_scope",
            "right_method",
            "right_program",
            "common_genes",
            "absolute_cosine",
            "interpretation",
        ],
    ).to_csv(root / "program_matches.tsv", sep="\t", index=False)


def sharing_classification(table, cfg):
    rows = []
    pooled = table[(table.scope == "pooled") & (table.sensitivity == "primary")]
    for (method, program), part in pooled.groupby(["method", "program"], sort=True):
        stable = part.stability_support.ge(0.8)
        candidates = {
            "formal": part[stable & part.inference_eligible & part.qvalue.le(cfg["fdr"])],
            "descriptive": part[stable & part.n_known_units.ge(2) & part.effect.notna()],
        }
        support = {}
        for label, candidate in candidates.items():
            studies = []
            for study, context in candidate.groupby("dataset", sort=True):
                direction = np.sign(context.effect.mean())
                sensitivity = table[
                    (table.scope == "pooled")
                    & (table.method == method)
                    & (table.program == program)
                    & (table.dataset == study)
                    & table.cell_type.isin(context.cell_type)
                    & table.sensitivity.isin(["depth_matched", "unique_viral"])
                ]
                if label == "descriptive":
                    sensitivity = sensitivity[sensitivity.n_known_units.ge(2)]
                if (
                    direction
                    and set(sensitivity.sensitivity) == {"depth_matched", "unique_viral"}
                    and (np.sign(sensitivity.effect) == direction).all()
                ):
                    studies.append((study, direction))
            positive = sorted(s for s, d in studies if d > 0)
            negative = sorted(s for s, d in studies if d < 0)
            support[label] = positive if len(positive) >= len(negative) else negative
        formal = len(support["formal"]) >= 2
        descriptive = len(support["descriptive"]) >= 2
        rows.append(
            dict(
                method=method,
                program=program,
                classification="candidate_shared"
                if formal
                else "descriptive_cross_context"
                if descriptive
                else "context_associated_or_unresolved",
                supporting_studies=";".join(support["formal"]),
                descriptive_studies=";".join(support["descriptive"]),
                passes_unit_inference_gates=formal,
                descriptive_annotation_limited=bool(
                    part[part.dataset.isin(support["descriptive"])]
                    .cell_type.eq("unannotated")
                    .any()
                ),
                virus_specificity_established=False,
            )
        )
    return rows


def inference_power(meta, cfg):
    rows = []
    for study in sorted(cfg["targets"]):
        n = int(
            meta[meta.included & meta.unit_known & meta.dataset.eq(study)].biological_unit.nunique()
        )
        pvalue = 2.0 ** (1 - n) if n else None
        rows.append(
            dict(
                dataset=study,
                max_known_units_from_metadata=n,
                optimistic_min_two_sided_signflip_p=pvalue,
                raw_threshold=cfg["fdr"],
                can_reach_raw_threshold=bool(pvalue is not None and pvalue <= cfg["fdr"]),
            )
        )
    return rows


def report(cfg):
    root = run_root(cfg)
    statuses, associations_all, performance = [], [], []
    meta = pd.read_csv(root / "libraries.tsv", sep="\t")
    expected = [
        root / "discovery" / scope / method / "status.json"
        for scope in sorted(cfg["targets"]) + ["pooled"]
        for method in cfg["methods"]
    ]
    expected += [
        root / "prediction" / fold["name"] / method / "status.json"
        for fold in outer_folds(meta)
        for method in cfg["methods"]
    ]
    for path in expected:
        status = json.loads(path.read_text()) if path.exists() else {"status": "not_run"}
        status["path"] = str(path.relative_to(root))
        statuses.append(status)
        if status["status"] != "ok":
            continue
        if (path.parent / "associations.tsv").exists():
            tab = pd.read_csv(path.parent / "associations.tsv", sep="\t")
            tab["method"], tab["scope"] = path.parent.name, path.parent.parent.name
            associations_all.append(tab)
        if (path.parent / "metrics.json").exists():
            details = json.loads((path.parent / "metrics.json").read_text())
            for model in details["models"]:
                performance.append(
                    {k: v for k, v in model.items() if isinstance(v, (float, int, str))}
                    | dict(
                        method=path.parent.name,
                        fold=path.parent.parent.name,
                        design=details["fold"]["design"],
                        study=details["fold"]["study"],
                    )
                )
    table = (
        pd.concat(associations_all, ignore_index=True)
        if associations_all
        else pd.DataFrame(
            columns=[
                "dataset",
                "cell_type",
                "program",
                "sensitivity",
                "n_units",
                "n_known_units",
                "effect",
                "ci_low",
                "ci_high",
                "pvalue",
                "inference_eligible",
                "stability_support",
                "status",
                "method",
                "scope",
                "qvalue",
            ]
        )
    )
    sharing = []
    if len(table):
        table["qvalue"] = np.nan
        if "pvalue" in table:
            valid = table.pvalue.notna() & table.inference_eligible
            table.loc[valid, "qvalue"] = bh_adjust(table.loc[valid, "pvalue"])
        sharing = sharing_classification(table, cfg)
    table.to_csv(root / "associations.tsv", sep="\t", index=False)
    pd.DataFrame(
        sharing,
        columns=[
            "method",
            "program",
            "classification",
            "supporting_studies",
            "descriptive_studies",
            "passes_unit_inference_gates",
            "descriptive_annotation_limited",
            "virus_specificity_established",
        ],
    ).to_csv(root / "sharing.tsv", sep="\t", index=False)
    pd.DataFrame(
        performance,
        columns=[
            "model",
            "method",
            "fold",
            "design",
            "study",
            "auroc",
            "auprc",
            "brier",
            "log_loss",
            "ece",
            "prevalence",
            "n",
            "C",
            "tuning",
        ],
    ).to_csv(root / "prediction_metrics.tsv", sep="\t", index=False)
    pd.DataFrame(statuses).to_csv(root / "task_status.tsv", sep="\t", index=False)
    compare_programs(root)
    power = inference_power(meta, cfg)
    pd.DataFrame(power).to_csv(root / "inference_power.tsv", sep="\t", index=False)
    failed = sum(s["status"] == "method_failed" for s in statuses)
    not_run = sum(s["status"] == "not_run" for s in statuses)
    unevaluable = sum(s["status"] == "unevaluable" for s in statuses)
    text = [
        "# Track A host programs",
        "",
        "Exploratory analysis; no universal infection or virus-specific signature is established.",
        "",
        f"Tasks: {len(statuses)}; method failures: {failed}; unevaluable designs: {unevaluable}; not run: {not_run}.",
        "",
        "See task_status.tsv for every denominator and failure; gene signatures, native fits, cells, seeds and selection receipts are retained per task.",
        "",
        "Candidate sharing requires concordant replicate-aware associations in at least two studies, global BH FDR <=0.05, seed stability >=0.8, and concordant unique-count/depth-matched sensitivity results.",
        "Descriptive cross-context programs require stable, concordant adjusted activity associations and sensitivity results in two studies, each with at least two known contributing units; they do not pass the formal unit-inference gate by definition.",
        "See inference_power.tsv for the optimistic sign-flip power bound. "
        + (
            "Formal shared support across two studies is unattainable under the current independent-unit counts and threshold. "
            if sum(p["can_reach_raw_threshold"] for p in power) < 2
            else "At least two studies can theoretically reach the raw threshold; actual contrast counts and FDR may still prevent formal shared support. "
        )
        + "Descriptive programs and held-out prediction are the exploratory endpoints.",
        "",
        "Mixed populations without author cell types and insufficient biological replication remain descriptive. Libraries are not automatically independent replicates.",
        "",
        "DIVAS matches genes across studies. Its nominal subspace inference is not calibrated for correlated genes; its within-single-study fits are unevaluable.",
        "",
        "Prediction targets relative viral transcriptional activity, not absence/presence of infection. Entire studies or biological units are held out; depth/QC and scrambled controls share the same evaluation cells.",
        "",
        "The five datasets cover four distinct target viruses, all DNA viruses; these data do not establish generalization to RNA-virus infection.",
    ]
    (root / "REPORT.md").write_text("\n".join(text) + "\n")
    write_json(
        root / "report.json",
        {
            "status": "incomplete_missing_tasks"
            if not_run
            else "incomplete_method_failures"
            if failed
            else "exploratory_results",
            "tasks": len(statuses),
            "failed": failed,
            "not_run": not_run,
            "unevaluable": unevaluable,
            "candidate_shared": sum(x["classification"] == "candidate_shared" for x in sharing),
            "descriptive_cross_context": sum(
                x["classification"] == "descriptive_cross_context" for x in sharing
            ),
            "inference_power": power,
            "formal_shared_support_feasible_from_metadata": sum(
                p["can_reach_raw_threshold"] for p in power
            )
            >= 2,
            "scientific_validation": "not_established_by_workflow_completion",
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["design", "discover", "predict", "report"])
    parser.add_argument("--config", default=str(HERE / "config.json"))
    parser.add_argument("--method", choices=["gbcd", "ebcd", "divas"])
    parser.add_argument("--scope")
    parser.add_argument("--fold")
    args = parser.parse_args()
    cfg = load_config(args.config)
    if args.command == "design":
        meta = library_metadata(cfg)
        print(
            json.dumps(
                {
                    "config": cfg,
                    "libraries": json.loads(meta.to_json(orient="records")),
                    "folds": outer_folds(meta),
                }
            )
        )
    elif args.command == "discover":
        discovery(cfg, args.method, args.scope)
    elif args.command == "predict":
        predict_fold(cfg, args.method, args.fold)
    else:
        report(cfg)
