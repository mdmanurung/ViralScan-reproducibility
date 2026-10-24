"""Summarize exact native replay receipts and called-cell molecule mass."""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
METHODS = ("host-conservative", "em-global", "sibling-weighted")
LIBRARIES = ("GSM5017040", "GSM6416024", "GSM3511335")


def write(name, rows):
    with (HERE / name).open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


inventory, comparisons = [], []
for library in LIBRARIES:
    tables = {}
    audits = []
    for method in METHODS:
        receipt = json.loads((HERE / f"molecule_assignment_receipts/{method}__{library}.json").read_text())
        assert receipt["exact_sparse_arrays_match_saved_baseline"] is True
        counts = receipt["method_diagnostics"]["molecule_assignments"]
        assert sum(counts.values()) == receipt["audit"]["input_molecules"]
        audits.append(receipt["audit"])
        inventory.append({"library": library, "method": method, "input_molecules": receipt["audit"]["input_molecules"], **counts, "exact_saved_sparse_arrays": True, "source_inputs_rehashed_unchanged": True, "native_elapsed_seconds": receipt["native_elapsed_seconds"], "process_peak_rss_kib": receipt["process_peak_rss_kib"], "export_sha256": receipt["assignment_sha256"]})
        path = HERE.parent / f"outputs/molecule_assignments_20261019/{method}/{library}/called_virus_counts.tsv"
        with path.open() as handle:
            tables[method] = {row["virus"]: row for row in csv.DictReader(handle, delimiter="\t")}
    assert audits[0] == audits[1] == audits[2]
    assert set(tables[METHODS[0]]) == set(tables[METHODS[1]]) == set(tables[METHODS[2]])
    for virus in sorted(tables[METHODS[0]]):
        totals = {method: float(tables[method][virus]["total_molecule_mass"]) for method in METHODS}
        if not any(totals.values()):
            continue
        reference = tables["host-conservative"][virus]
        assert len({tables[method][virus]["unique_molecules"] for method in METHODS}) == 1
        assert len({tables[method][virus]["called_cells"] for method in METHODS}) == 1
        baseline = totals["host-conservative"]
        for method in METHODS:
            row = tables[method][virus]
            comparisons.append({"library": library, "virus": virus, "method": method, "unique_molecules": row["unique_molecules"], "ambiguous_molecule_mass": row["allocated_ambiguous_mass"], "total_molecule_mass": row["total_molecule_mass"], "change_from_host_conservative": totals[method] - baseline, "percent_change_from_host_conservative": 100 * (totals[method] - baseline) / baseline if baseline else "undefined_zero_baseline", "called_cells": row["called_cells"], "scope": "weighted mass in frozen called cells, not distinct supported viral molecules"})
write("molecule_replay_inventory.tsv", inventory)
write("molecule_method_comparison.tsv", comparisons)
print("Exact replays:", len(inventory), "nonzero virus/method comparisons:", len(comparisons))
