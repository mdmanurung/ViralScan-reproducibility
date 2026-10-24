"""Read frozen Track A inputs; never write to a source run."""

import argparse
import hashlib
import importlib.metadata
import json
import re
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from anndata.io import read_elem, sparse_dataset
from scipy import sparse

HERE = Path(__file__).resolve().parent


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(path):
    path = Path(path).resolve()
    cfg = json.loads(path.read_text())
    for key in (
        "tracka_root",
        "truth_labels",
        "cell_annotations",
        "output_root",
        "python",
        "rscript",
    ):
        cfg[key] = str((path.parent / cfg[key]).resolve())
    cfg["r_libraries"] = [str((path.parent / p).resolve()) for p in cfg["r_libraries"]]
    return cfg


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def run_root(cfg):
    root = Path(cfg["output_root"])
    source = Path(cfg["tracka_root"]).resolve()
    if root == source or source in root.parents:
        raise ValueError("Analysis output must be outside the frozen Track A store")
    identity = {
        "config": cfg,
        "scripts": {
            p.name: sha256(p)
            for p in HERE.iterdir()
            if p.suffix in (".py", ".R", ".json", ".tsv") or p.name == "Snakefile"
        },
    }
    identity["metadata"] = {
        str(p): sha256(p)
        for p in (
            Path(cfg["truth_labels"]),
            Path(cfg["cell_annotations"]),
            source / "manifest.tsv",
            source / "status/libs.tsv",
            source / "evidence/tiers.tsv",
        )
    }
    identity["python"] = {
        "executable": sys.executable,
        "version": sys.version,
        "packages": {
            p: importlib.metadata.version(p)
            for p in ("anndata", "h5py", "numpy", "pandas", "scipy", "scikit-learn")
        },
    }
    root.mkdir(parents=True, exist_ok=True)
    marker = root / "run_identity.json"
    if marker.exists() and json.loads(marker.read_text()) != identity:
        raise ValueError(
            "Input code/config changed: choose a new output_root; existing run is immutable"
        )
    if not marker.exists():
        write_json(marker, identity)
    return root


def library_metadata(cfg):
    source = Path(cfg["tracka_root"])
    manifest = pd.read_csv(source / "manifest.tsv", sep="\t", dtype=str)
    manifest = manifest[manifest.dataset.isin(cfg["targets"])].copy()
    if manifest["sample"].duplicated().any():
        raise ValueError("Manifest contains duplicate libraries")
    libinfo = pd.read_csv(source / "status/libs.tsv", sep="\t", dtype=str).set_index("library")
    if libinfo.index.duplicated().any():
        raise ValueError("Library metadata has duplicate keys")
    truth = {
        row["library"]: row
        for study in json.loads(Path(cfg["truth_labels"]).read_text())
        for row in study["labels"]
    }
    rows = []
    for row in manifest.itertuples():
        lib, ds = row.sample, row.dataset
        label = truth.get(lib, {})
        title = libinfo.loc[lib, "title"]
        detail = label.get("detail", "")
        unit, known, protocol, time, population, cell_type = (
            "unknown:" + lib,
            False,
            "unknown",
            "unknown",
            "unknown",
            "unannotated",
        )
        if ds == "hsv1":
            rep = re.search(r"replicate\s+(\d+)", detail, re.I)
            protocol = "37C" if "37C" in detail else "4C"
            if rep:
                unit, known = f"hsv1:culture_replicate_{rep[1]}", True
            hour = re.search(r"([135])\s*hpi", detail)
            time = hour[1] if hour else "0"
            population, cell_type = "NHDF", "fibroblast"
        elif ds == "hhv6b":
            donor = re.search(r"\bD(\d+)-Day(\d+)", title)
            if donor:
                unit, known, time = "hhv6b:D" + donor[1], True, donor[2]
            population = "PBMC" if "PBMC" in title else "CAR_T_enriched"
        elif ds == "ebv":
            donor = re.search(r"LCL_(\d+)_(\w+)", title)
            if donor:
                unit, known, protocol = "ebv:donor_" + donor[1], True, donor[2]
            population, cell_type = "LCL", "B_cell_LCL"
        elif ds == "hpv16":
            unit, known = "hpv16:raft_" + lib, True
            population, cell_type = "NIKS_raft", "keratinocyte"
        else:
            donor = re.search(r"HN(\d+)_(PBL|CD45[+-])", title)
            if donor:
                unit, known, population = "hnscc:HN" + donor[1], True, donor[2]
        run = source / "runs" / ds / "combined_off" / lib / lib
        rows.append(
            dict(
                dataset=ds,
                library=lib,
                included=not (ds == "hhv6b" and "TCR" in title),
                exclusion="TCR_enriched_not_GEX" if ds == "hhv6b" and "TCR" in title else "",
                biological_unit=unit,
                unit_known=known,
                protocol=protocol,
                time=time,
                source_population=population,
                default_cell_type=cell_type,
                independent_status=label.get("status", "unknown"),
                title=title,
                source_url=label.get("source_url", ""),
                source_detail=detail,
                matrix=str(run / "kb-python/counts_unfiltered/adata_multimap.h5ad"),
                identity=str(run / "results/virus_identity.tsv"),
                called_cells=str(source / "status/cells" / (lib + ".barcodes.txt")),
            )
        )
    return pd.DataFrame(rows)


def inventory(cfg):
    root = run_root(cfg)
    meta = library_metadata(cfg)
    annotations = pd.read_csv(cfg["cell_annotations"], sep="\t", dtype=str)
    if not {"library", "barcode", "cell_type", "source"}.issubset(annotations.columns):
        raise ValueError("Author annotation table requires library, barcode, cell_type and source")
    if not set(annotations.library).issubset(set(meta.library)):
        raise ValueError("Author annotation table contains libraries outside the Track A manifest")
    checks = []
    for row in meta.itertuples():
        missing = [p for p in (row.matrix, row.identity, row.called_cells) if not Path(p).is_file()]
        if missing and row.included:
            raise FileNotFoundError(f"{row.library}: missing {missing}")
        checks.append({"library": row.library, "included": row.included, "missing": missing})
    meta.to_csv(root / "libraries.tsv", sep="\t", index=False)
    write_json(
        root / "inventory.json",
        {
            "libraries": len(meta),
            "included": int(meta.included.sum()),
            "excluded": int((~meta.included).sum()),
            "checks": checks,
            "metadata_sources": {
                str(p): sha256(p)
                for p in (
                    Path(cfg["truth_labels"]),
                    Path(cfg["cell_annotations"]),
                    Path(cfg["tracka_root"]) / "manifest.tsv",
                    Path(cfg["tracka_root"]) / "status/libs.tsv",
                )
            },
            "cell_type_gap": "Only source-defined homogeneous populations have default labels; mixed cells require author annotations",
            "status": "input_presence_verified_not_scientific_validation",
        },
    )


def validate_counts(X):
    if not np.isfinite(X.data).all() or (X.data < 0).any():
        raise ValueError("Counts must be finite and nonnegative")
    if not np.allclose(X.data, np.rint(X.data), atol=1e-5, rtol=0):
        raise ValueError("Host counts_original must contain integer molecule counts")


def read_called_matrix(path, called):
    with h5py.File(path) as handle:
        obs = read_elem(handle["obs"])
        var = read_elem(handle["var"])
        if not obs.index.is_unique or not var.index.is_unique:
            raise ValueError("Matrix observation/feature keys must be unique")
        idx = obs.index.get_indexer(called)
        if (idx < 0).any() or not pd.Index(called).is_unique:
            raise ValueError("Frozen called barcodes must match the matrix exactly once")
        order = np.argsort(idx)
        raw = sparse_dataset(handle["layers/counts_original"])[idx[order], :].tocsr()
        viral = sparse_dataset(handle["layers/counts_multimap_host_conservative"])[
            idx[order], :
        ].tocsr()
        unique = sparse_dataset(handle["layers/counts_unique_viral"])[idx[order], :].tocsr()
        barcodes = np.asarray(called)[order]
    validate_counts(raw)
    return raw, viral, unique, var, barcodes


def cpm_labels(counts, depth):
    n_positive = int((counts >= 10).sum())
    ratio = counts / np.maximum(depth, 1)
    labels = np.zeros(len(counts), dtype=int)
    labels[np.argsort(-ratio, kind="stable")[:n_positive]] = 1
    return labels


def prepare(cfg, library):
    root = run_root(cfg)
    meta = library_metadata(cfg).set_index("library")
    row = meta.loc[library]
    if not row.included:
        raise ValueError(f"Excluded library: {library}")
    out = root / "prepared" / library
    out.mkdir(parents=True, exist_ok=True)
    called = [
        s.strip()
        for s in Path(row.called_cells).read_text().splitlines()
        if s.strip() and s.strip() != "barcode"
    ]
    raw, viral, unique, var, barcodes = read_called_matrix(row.matrix, called)
    host = ~var.is_viral.astype(bool).to_numpy()
    identities = pd.read_csv(row.identity, sep="\t", dtype=str).fillna("")
    target_ids = set(
        identities.loc[identities.virus_name.isin(cfg["targets"][row.dataset]), "gene_id"]
    )
    target = var.gene_id.isin(target_ids).to_numpy() & ~host
    if not target.any():
        raise ValueError(f"No exact target-virus features for {library}")
    host_ids = var.loc[host, "gene_id"].str.replace(r"\.\d+$", "", regex=True)
    names = var.loc[host, "gene_name"].astype(str).to_numpy()
    genes, inverse = np.unique(host_ids.to_numpy(), return_inverse=True)
    collapse = sparse.csr_matrix(
        (np.ones(len(inverse)), (np.arange(len(inverse)), inverse)),
        shape=(len(inverse), len(genes)),
    )
    X = (raw[:, host] @ collapse).tocsr()
    gene_names = (
        pd.DataFrame({"gene_id": host_ids.to_numpy(), "gene_name": names})
        .groupby("gene_id", sort=True)
        .gene_name.agg(lambda x: "|".join(sorted(set(x))))
        .tolist()
    )
    gene_table = pd.DataFrame({"gene_id": genes, "gene_name": gene_names})
    depth = np.asarray(X.sum(axis=1)).ravel()
    if (depth <= 0).any():
        raise ValueError(
            f"Frozen cells with zero host depth in {library}; explicit QC decision required"
        )
    mt = np.asarray([any(s.startswith("MT-") for s in n.split("|")) for n in gene_names])
    burden = np.asarray(viral[:, target].sum(axis=1)).ravel()
    unique_burden = np.asarray(unique[:, target].sum(axis=1)).ravel()
    cells = pd.DataFrame(
        {
            "barcode": barcodes,
            "host_depth": depth,
            "mito_fraction": np.asarray(X[:, mt].sum(axis=1)).ravel() / depth,
            "n_genes": np.diff(X.indptr),
            "viral_molecules": burden,
            "viral_unique_molecules": unique_burden,
            "viral_cpm": burden / depth * 1e6,
            "activity_label": cpm_labels(burden, depth),
            "raw_label": (burden >= 10).astype(int),
            "unique_activity_label": cpm_labels(unique_burden, depth),
        }
    )
    for key in (
        "dataset",
        "biological_unit",
        "unit_known",
        "protocol",
        "time",
        "source_population",
        "independent_status",
    ):
        cells[key] = row[key]
    cells["library"] = library
    cells["cell_id"] = library + ":" + cells.barcode
    cells["cell_type"] = row.default_cell_type
    annotations = pd.read_csv(cfg["cell_annotations"], sep="\t", dtype=str).fillna("")
    ann = annotations[annotations.library == library]
    if ann.barcode.duplicated().any() or not set(ann.barcode).issubset(set(barcodes)):
        raise ValueError(f"Invalid author annotation barcode join in {library}")
    if len(ann) and ((ann.source == "") | (ann.cell_type == "")).any():
        raise ValueError("Author annotations require cell_type and source")
    if len(ann):
        mapping = ann.set_index("barcode").cell_type
        cells["cell_type"] = cells.barcode.map(mapping).fillna(cells.cell_type)
    tiers = pd.read_csv(Path(cfg["tracka_root"]) / "evidence/tiers.tsv", sep="\t").fillna("")
    prefix = row.dataset + "__" + library + "__combined_off__"
    expected = [prefix + s.replace("-", "_").replace(" ", "_") for s in cfg["targets"][row.dataset]]
    target_tiers = tiers[tiers.evidence_dir.isin(expected)]
    supported = target_tiers.tier.isin(["supported", "supported_partial"])
    resolved = (
        supported & target_tiers.sibling_status.isin(["target_resolved", "no_siblings"])
    ).any()
    # EBV types belong to one HHV-4 species; an unresolved subtype is not a second infection.
    cells["target_resolved"] = bool(resolved or (row.dataset == "ebv" and supported.any()))
    sparse.save_npz(out / "host_counts.npz", X)
    gene_table.to_csv(out / "genes.tsv", sep="\t", index=False)
    cells.to_csv(out / "cells.tsv.gz", sep="\t", index=False)
    paths = [
        row.matrix,
        row.identity,
        row.called_cells,
        cfg["cell_annotations"],
        str(Path(cfg["tracka_root"]) / "evidence/tiers.tsv"),
    ]
    write_json(
        out / "receipt.json",
        {
            "library": library,
            "cells": len(cells),
            "host_genes": len(genes),
            "source_sha256": {p: sha256(p) for p in paths},
            "host_layer": "counts_original",
            "viral_layer": "counts_multimap_host_conservative",
            "targets": cfg["targets"][row.dataset],
            "no_uninfected_cell_claim": True,
            "target_evidence_rows": target_tiers.evidence_dir.tolist(),
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["inventory", "prepare"])
    parser.add_argument("--config", default=str(HERE / "config.json"))
    parser.add_argument("--library")
    args = parser.parse_args()
    config = load_config(args.config)
    if args.command == "inventory":
        inventory(config)
    else:
        if args.library is None:
            parser.error("prepare requires --library")
        prepare(config, args.library)
