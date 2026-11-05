#!/usr/bin/env python3
"""Read-only diagnosis of KSHV 'mixed' cells under the 5b419d4 gene-programme catalogue.

    PYTHONPATH=<pin 5b419d4>/src python scripts/kshv_mixed_diagnosis.py <sample run dir> [...]

Per library: state counts; for the mixed cells the productive-marker combinations, per-cell unique
productive / latent / total KSHV molecules; ambient check = marker profile of the uncalled barcodes
(the soup) against the mixed cells, and the expected ambient KSHV molecules per cell
(ambient_viral_fraction x the cell's total molecules, per_cell_viral.tsv). Writes nothing.
"""
import collections
import csv
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import scipy.sparse as sp
from viralscan.gene_programs import call_cell_programme, catalogue_virus_facts, resolve_markers

V = "Human herpesvirus 8"
import viralscan

CAT = list(csv.DictReader(open(Path(viralscan.__file__).parent / "data/gene_programs.tsv"), delimiter="\t"))


def q(x):
    return np.percentile(x, [0, 25, 50, 75, 95, 100]).round(1).tolist() if len(x) else []


for d in map(Path, sys.argv[1:]):
    a = ad.read_h5ad(d / "kb-python/counts_unfiltered/adata_multimap.h5ad", backed="r")
    called = set(pd.read_csv(d / "results/called_cells.tsv", sep="\t").iloc[:, 0])
    mask = np.array([o in called for o in a.obs_names])
    res, unres = resolve_markers(V, a.var_names, "bundled", catalogue=CAT)
    idx = [list(a.var_names).index(m.var_name) for m in res]
    names = [m.var_name.split("_")[-1] for m in res]
    prog = np.array([m.programme for m in res])
    info = catalogue_virus_facts(CAT)[V]
    absok = not any(u.programme == "productive" for u in unres) and not info.get("capture_uncertain_productive")
    U = sp.csr_matrix(a.layers["counts_unique_viral"])
    kcols = U[:, idx].tocsr()
    calls = call_cell_programme(kcols[mask], res, latency_observable=info["latency_observable"], absence_assessable=absok)
    st = np.array([c["state"] for c in calls])
    print(f"\n=== {d.name}  called={mask.sum()}  states={dict(collections.Counter(st))}")
    sub = kcols[mask].toarray()
    prod_mol = sub[:, prog == "productive"].sum(1)
    lat_mol = sub[:, prog == "latent"].sum(1)
    for s in ("mixed", "productive", "latent"):
        k = st == s
        if not k.any():
            continue
        sets = collections.Counter(
            tuple(n for n, p, v in zip(names, prog, sub[i]) if p == "productive" and v > 0) for i in np.where(k)[0]
        )
        print(f"{s}: n={k.sum()}  productive-marker sets {sets.most_common(8)}")
        print(f"   productive mol/cell [min,q25,med,q75,q95,max] {q(prod_mol[k])}   latent {q(lat_mol[k])}")
        print(f"   n productive markers detected: {dict(sorted(collections.Counter((sub[k][:, prog == 'productive'] > 0).sum(1)).items()))}")
        print(f"   cells with productive mol==1: {(prod_mol[k]==1).sum()}  <=2: {(prod_mol[k]<=2).sum()}")
    # ambient: uncalled barcodes, marker profile and expected ambient molecules per cell
    amb = kcols[~mask].toarray().sum(0)
    prof_amb = amb / amb.sum() if amb.sum() else amb
    k = st == "mixed"
    if k.any():
        mm = sub[k].sum(0)
        prof_mix = mm / mm.sum()
        cos = float(prof_amb @ prof_mix / (np.linalg.norm(prof_amb) * np.linalg.norm(prof_mix)))
        print("   marker share ambient vs mixed cells (productive only, share of all marker mol):")
        for n, p, x, y in zip(names, prog, prof_amb, prof_mix):
            print(f"     {n:10s} {p:10s} ambient {x:.3f}  mixed-cells {y:.3f}")
        print(f"   cosine(ambient, mixed) = {cos:.3f};  ambient pool: {int(amb.sum())} marker mol in {int((~mask).sum())} uncalled barcodes")
    vs = pd.read_csv(d / "results/viral_summary.tsv", sep="\t")
    vs = vs[vs.virus_name == V].iloc[0]
    pc = pd.read_csv(d / "results/per_cell_viral.tsv", sep="\t")
    pc = pc[pc.virus_name == V].set_index("barcode")
    tot = pc["molecules_total_est"].reindex(np.array(a.obs_names)[mask]).to_numpy()
    f = float(vs["ambient_viral_fraction"])
    expect = f * np.nan_to_num(tot)  # expected ambient KSHV molecules per cell (all KSHV features, rho=1 upper bound)
    share_prod = prof_amb[prog == "productive"].sum()
    print(f"   ambient_viral_fraction={f:.5f} (ub95 {vs['ambient_viral_fraction_ub95']:.5f}), ambient productive share of marker mol={share_prod:.3f}")
    if k.any():
        print(f"   mixed cells: total mol/cell median {np.nanmedian(tot[k]):.0f}; expected ambient KSHV mol/cell median {np.median(expect[k]):.2f}, "
              f"expected ambient productive mol/cell {np.median(expect[k])*share_prod:.3f} vs observed median {np.median(prod_mol[k]):.1f}; "
              f"cells with observed productive mol > Poisson 99th pct of expected: {(prod_mol[k] > np.array([np.percentile(np.random.default_rng(0).poisson(max(e*share_prod,1e-9),10000),99) for e in expect[k]])).sum()}")
