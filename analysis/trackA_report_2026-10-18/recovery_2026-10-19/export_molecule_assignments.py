"""Replay pinned molecule allocation from retained BUS text; never write into a source run."""

import argparse
import csv
import hashlib
import json
import resource
import sys
import time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

import h5py
import numpy as np
from anndata.io import read_elem

PIN = Path("/exports/archive/hg-funcgenom-research/mdmanurung/vs_pinned/97a64f6")
sys.path.insert(0, str(PIN / "src"))
from viralscan.scripts import multimap as mm  # noqa: E402

ROOT = Path("/exports/archive/hg-funcgenom-research/mdmanurung/viralscan_work/trackA_round1")
HERE = Path(__file__).resolve().parent
DATASETS = {"GSM5017040": "hnscc_gse164690", "GSM6416024": "hhv6b", "GSM3511335": "hsv1"}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("library", choices=DATASETS)
    parser.add_argument("method", choices=["host-conservative", "em-global", "sibling-weighted"])
    args = parser.parse_args()
    library, method = args.library, args.method
    source = ROOT / f"runs/{DATASETS[library]}/combined_off/{library}/{library}"
    baseline = source if method == "host-conservative" else ROOT / f"multimap_em_2026-10-18/{method}/{library}/{library}"
    cfg = mm.RunConfig.from_yaml(baseline / "config.yaml")
    assert cfg.multimap_method == method
    mm.config = mm.RunConfig.from_yaml(source / "config.yaml")
    mm.output = str(source)
    mm.kb = mm.KbCountOutputs.from_config_output(source)
    adata_path, _, ec_path, transcripts_path, barcodes_path, text_path, genes_path, names_path, t2g_path = mm.define_paths()
    inputs = [Path(p) for p in (adata_path, ec_path, transcripts_path, barcodes_path, text_path, genes_path, names_path, t2g_path)]
    inputs += [source / "config.yaml", baseline / "config.yaml", baseline / "kb-python/counts_unfiltered/adata_multimap.h5ad", source / "results/virus_identity.tsv", ROOT / f"status/cells/{library}.barcodes.txt"]
    before = {str(p): sha(p) for p in inputs}
    out = HERE.parent / f"outputs/molecule_assignments_20261019/{method}/{library}"
    out.mkdir(parents=True, exist_ok=False)
    original, _, n_genes = mm.load_adata(adata_path)
    barcodes, n_cells = mm.load_barcodes(barcodes_path)
    genes, _ = mm.load_genes(genes_path, names_path, n_genes)
    transcripts, t2g = mm.load_transcripts(transcripts_path, t2g_path)
    ec = mm.read_ec(ec_path, transcripts, t2g, genes)
    identity = mm.load_run_identity(str(source))
    assert identity is not None and len(barcodes) == n_cells
    identities = identity.by_gene()
    viral = mm.viral_gene_partition(str(source))
    viral_indices = {i for i, gene in enumerate(genes) if gene in viral}
    sibling = {i: identities[gene].sibling_group for i, gene in enumerate(genes) if gene in identities and identities[gene].viral and identities[gene].sibling_group}
    started = time.monotonic()
    layers = mm.build_multimap_layers(bus_df=Path(text_path), barcode_to_idx=barcodes, ec_map=ec, n_cells=n_cells, n_genes=n_genes, viral_gene_indices=viral_indices, original_counts=original.X, method=method, pseudocount=cfg.multimap_pseudocount, em_max_iter=cfg.multimap_em_max_iter, em_tol=cfg.multimap_em_tol, sibling_groups=sibling, molecule_assignments=out / "molecule_assignments.tsv.gz", gene_names=genes)
    with h5py.File(baseline / "kb-python/counts_unfiltered/adata_multimap.h5ad", "r") as handle:
        for name, observed in [("counts_unique", layers.unique), ("counts_corrected", layers.corrected)]:
            expected = read_elem(handle["layers"][name])
            assert expected.shape == observed.shape and expected.dtype == observed.dtype
            assert all(np.array_equal(getattr(expected, attr), getattr(observed, attr)) for attr in ("indptr", "indices", "data")), (library, method, name)
    assert sum(layers.method_diagnostics["molecule_assignments"].values()) == layers.audit.input_molecules
    called = {mm.strip_10x_suffix(line.strip()) for line in (ROOT / f"status/cells/{library}.barcodes.txt").read_text().splitlines() if line.strip()}
    mask = np.zeros(n_cells, dtype=bool)
    for barcode, index in barcodes.items():
        mask[index] = barcode in called
    assert int(mask.sum()) == len(called)
    unique = np.asarray(layers.unique[mask].sum(axis=0)).ravel()
    allocated = np.asarray(layers.corrected[mask].sum(axis=0)).ravel()
    totals = defaultdict(lambda: [0.0, 0.0])
    for index in sorted(viral_indices):
        name = identities[genes[index]].virus_name
        totals[name][0] += float(unique[index])
        totals[name][1] += float(allocated[index])
    with (out / "called_virus_counts.tsv").open("w") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["virus", "unique_molecules", "allocated_ambiguous_mass", "total_molecule_mass", "called_cells"])
        for virus, (u, a) in sorted(totals.items()):
            writer.writerow([virus, u, a, u + a, int(mask.sum())])
    after = {str(p): sha(p) for p in inputs}
    assert before == after
    receipt = {"library": library, "dataset": DATASETS[library], "method": method, "source": str(source), "baseline": str(baseline), "pinned_source": str(PIN), "allocation": 25833654, "full_source_inputs_rehashed_unchanged": before, "exact_sparse_arrays_match_saved_baseline": True, "audit": asdict(layers.audit), "method_diagnostics": layers.method_diagnostics, "native_elapsed_seconds": time.monotonic() - started, "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, "assignment_sha256": sha(out / "molecule_assignments.tsv.gz"), "exported_weight_precision": "9 significant digits; count exactness checked before serialization", "script_sha256": sha(__file__), "pinned_allocator_sha256": sha(PIN / "src/viralscan/multimapping.py")}
    receipts = HERE / "molecule_assignment_receipts"
    receipts.mkdir(exist_ok=True)
    (receipts / f"{method}__{library}.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(library, method, "allocation matched saved sparse arrays exactly; export complete", flush=True)


if __name__ == "__main__":
    main()
