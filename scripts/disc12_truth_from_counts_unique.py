#!/usr/bin/env python3
"""DISC-17 truth tables: per-cell UNIQUE molecules of the panel virus from the primary run's multimap h5ad.

``counts_unique`` in ``kb-python/counts_unfiltered/adata_multimap.h5ad`` equals the ``unique`` rows of
``molecule_assignments.tsv.gz`` (package docs/output_reference.md), which the primary runs never wrote and
``rerun-multimap`` cannot add (the runs predate ``log/multimap.done``). Genes of the panel virus are taken from the
same run's ``results/multimap_evidence.tsv`` (``gene_id`` <-> ``virus_name``). Rows = the manifest's called cells
(``called_cells.tsv(combined_off)``), cells absent from the matrix = 0, so the truth cell space is the arms' cell space.

    python scripts/disc12_truth_from_counts_unique.py --manifest docs/plans/disc12/input_manifest.tsv \
        --site-root data/runs/work --lib LIB=VIRUS_NAME_REGEX ... --out docs/plans/disc12/truth
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

import anndata as ad
import numpy as np
import scipy.sparse as sp


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--site-root", type=Path, required=True, help="replaces $SITE_ROOT/viralscan_work in the manifest")
    p.add_argument("--lib", action="append", default=[], metavar="LIB=REGEX", help="panel virus_name regex per library")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    regex = dict(item.split("=", 1) for item in a.lib)
    with a.manifest.open(newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    fix = lambda s: Path(s.replace("$SITE_ROOT/viralscan_work", str(a.site_root)))
    a.out.mkdir(parents=True, exist_ok=True)
    prov = {}
    for lib, pat in regex.items():
        mine = [r for r in rows if r["library"] == lib and r["role"].startswith("positive")]
        run = fix(next(r["run_dir"] for r in mine if r["file"].startswith("host_filtered")))
        cells_tsv = fix(next(r["run_dir"] for r in mine if r["file"].startswith("called_cells"))) / "results" / "called_cells.tsv"
        cells = [l.strip() for l in cells_tsv.read_text().splitlines()[1:] if l.strip()]
        with (run / "results" / "multimap_evidence.tsv").open(newline="") as fh:
            ev = list(csv.DictReader(fh, delimiter="\t"))
        names = sorted({r["virus_name"] for r in ev if re.fullmatch(pat, r["virus_name"])})
        genes = sorted({r["gene_id"] for r in ev if r["virus_name"] in names})
        h5 = run / "kb-python" / "counts_unfiltered" / "adata_multimap.h5ad"
        adata = ad.read_h5ad(h5)
        assert adata.uns["multimap_method"] == "host-conservative", adata.uns["multimap_method"]
        gi = adata.var_names.isin(genes)
        layer = adata.layers["counts_unique"]
        per_cell = np.asarray((layer[:, gi] if sp.issparse(layer) else layer[:, gi]).sum(axis=1)).ravel()
        lookup = dict(zip(adata.obs_names, per_cell, strict=True))
        out = a.out / f"{lib}.truth.tsv"
        with out.open("w", newline="") as fh:
            w = csv.writer(fh, delimiter="\t", lineterminator="\n")
            w.writerow(["barcode", "molecules"])
            for b in cells:
                w.writerow([b, int(round(float(lookup.get(b, 0.0))))])
        n_pos = sum(int(round(float(lookup.get(b, 0.0)))) > 0 for b in cells)
        prov[lib] = {
            "run_dir": str(run), "h5ad_sha256": sha256(h5), "layer": "counts_unique",
            "virus_name_regex": pat, "virus_names": names, "n_genes": len(genes), "genes": genes,
            "cell_space": str(cells_tsv), "n_cells": len(cells), "n_cells_in_matrix": sum(b in lookup for b in cells),
            "n_truth_cells": n_pos, "total_unique_molecules": int(sum(int(round(float(lookup.get(b, 0.0)))) for b in cells)),
            "multimap_method": adata.uns["multimap_method"], "count_schema_version": str(adata.uns.get("count_schema_version")),
        }
        print(lib, names, "genes", len(genes), "cells", len(cells), "in matrix", prov[lib]["n_cells_in_matrix"], "truth cells", n_pos)
    (a.out / "truth_provenance.json").write_text(json.dumps(prov, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
