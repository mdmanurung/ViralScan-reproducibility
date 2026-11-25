"""Collect the round 2026-11-04 target-verdict evidence into one table and the matched-negative check.

Purpose:  one row per positive library: molecule verdicts (counted and all), read verdicts, splice and strand
          support, host-homology flags, and the matched negative's HPV16 or target row from viral_summary.tsv.
Run:      VIRALSCAN_DATA=<repro checkout>/data python scripts/target_verdict_collect.py   (or source env.sh)
Inputs:   data/runs/round_2026-11-04_target_verdicts/<dataset>/<sample>/evidence_splice/   (jobs of TARGET-VERDICT-01)
          data/runs/round_2026-11-02/{hpv16/SRR19537339,hnscc_gse164690/SRR13418973}/combined_off/*/results/viral_summary.tsv
          analysis/round_2026-11-04/target_verdict_calls.tsv
Outputs:  analysis/round_2026-11-04/target_verdicts.tsv            one row per library (wide)
          analysis/round_2026-11-04/target_verdict_negatives.tsv   matched negatives
Rule:     CONFIDENT needs (1) expected positive by design (every row here), (2) at least CUT of the counted
          molecules virus-best (plain majority; every fraction is printed so a reader can apply a stricter cut),
          (3) a clean matched negative where one exists (HPV16 only: viral_summary `detected` is False or no row).
          A library whose evidence is missing is `pending`.
"""

import csv
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = (
    Path(os.environ.get("VIRALSCAN_DATA", ROOT / "data")) / "runs"
)  # bulk data is not in git
OUT_ROOT = RUNS / "round_2026-11-04_target_verdicts"
NOTE_DIR = ROOT / "analysis" / "round_2026-11-04"
CUT = 0.5  # plain majority of counted molecules virus-best
Z = 1.96  # Wilson interval, 95 %
SUBSET_SAMPLES = {"GSM5725696"}  # run on a seeded 20,000-molecule subset

# Matched negatives: (positive sample, negative sample, run dir of the negative's combined_off sample directory, virus)
NEGATIVES = {
    "SRR19537341": (
        "SRR19537339",
        "round_2026-11-02/hpv16/SRR19537339/combined_off/SRR19537339",
        "Human papillomavirus 16",
    ),
    "SRR13419165": (
        "SRR13418973 (HN01)",
        "round_2026-11-02/hnscc_gse164690/SRR13418973/combined_off/SRR13418973",
        "Human papillomavirus 16",
    ),
}
LABEL = {
    "SRR12682296": "EBV (NC_007605.1)",
    "SRR8315713": "HSV-1",
    "SRR20710641": "HHV-6B RNA detected",
    "GSM5725695": "KSHV latent",
    "GSM5725696": "KSHV induced (subset)",
    "GSM4682311": "KSHV BC-1",
    "SRR19537341": "HPV16 raft",
    "SRR13419165": "HPV16 HN18",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    d = 1 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / d
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return (centre - half, centre + half)


def main() -> None:
    calls = read_tsv(NOTE_DIR / "target_verdict_calls.tsv")
    negatives = []
    for sample, (neg, rundir, virus) in NEGATIVES.items():
        rows = [
            r
            for r in read_tsv(RUNS / rundir / "results" / "viral_summary.tsv")
            if r["virus_name"] == virus
        ]
        row = rows[0] if rows else {}
        negatives.append(
            {
                "positive": sample,
                "negative": neg,
                "virus": virus,
                "molecules": row.get("viral_molecules_total_est", "0 (no row)"),
                "called_cells": row.get("infected_called", "0"),
                "n_called_cells": row.get("n_called_cells", ""),
                "detected": row.get("detected", "no row"),
                "clean": "yes" if (not row or row.get("detected") == "False") else "NO",
            }
        )
    neg_clean = {n["positive"]: n["clean"] for n in negatives}

    table = []
    for call in calls:
        ev = OUT_ROOT / call["dataset"] / call["sample"] / "evidence_splice"
        mol = {
            (r["scope"], r["verdict"]): int(r["molecules"])
            for r in read_tsv(ev / "molecule_verdict_summary.tsv")
        }
        rd = read_tsv(ev / "read_verdict_summary.tsv")
        splice = (read_tsv(ev / "splice" / "splice_summary.tsv") or [{}])[0]
        strand = (read_tsv(ev / "strand_qc.tsv") or [{}])[0]
        flags = {
            r["flag"]: r["status"] for r in read_tsv(ev / "interpretation_flags.tsv")
        }
        row = {
            "dataset": call["dataset"],
            "sample": call["sample"],
            "label": LABEL[call["sample"]],
            "expected": "yes",
        }
        if not mol:
            row["state"] = "pending"
            table.append(row)
            continue
        for scope in ("counted", "all"):
            n = sum(
                mol.get((scope, v), 0)
                for v in ("virus_best", "host_best", "tie", "unaligned")
            )
            for v in ("virus_best", "host_best", "tie", "unaligned"):
                row[f"{scope}_{v}"] = mol.get((scope, v), 0)
                row[f"{scope}_{v}_frac"] = (
                    round(mol.get((scope, v), 0) / n, 4) if n else ""
                )
            row[f"{scope}_n"] = n
        lo, hi = wilson(mol.get(("counted", "virus_best"), 0), row["counted_n"])
        row["counted_virus_best_ci95"] = f"{lo:.4f}-{hi:.4f}"
        row["reads_by_verdict"] = ";".join(
            f"{r['verdict']}/{r['repeat_class']}={r['reads']}" for r in rd
        )
        row["splice_status"] = splice.get("status", "")
        for k in (
            "reads_aligned",
            "spliced_reads",
            "spliced_molecules",
            "spliced_molecules_annotated",
            "unique_junctions",
            "annotation_status",
        ):
            row[f"splice_{k}"] = splice.get(k, "")
        row["strand_status"] = strand.get("status", "")
        row["strand_reason"] = strand.get("reason", "")
        row["strand_fraction_expected_orientation"] = strand.get(
            "fraction_expected_orientation", ""
        )
        row["strand_host_sense_fraction"] = strand.get("host_sense_fraction", "")
        row["flag_host_homology"] = flags.get("host_homology", "")
        row["flag_low_complexity"] = flags.get("low_complexity", "")
        neg = neg_clean.get(call["sample"], "no matched negative")
        row["matched_negative_clean"] = neg
        majority = (
            row["counted_n"] > 0 and row["counted_virus_best"] / row["counted_n"] >= CUT
        )
        row["verdict"] = (
            "CONFIDENT"
            if majority and neg in ("yes", "no matched negative")
            else "NOT CONFIDENT"
        )
        row["state"] = "done"
        table.append(row)

    fields = list(dict.fromkeys(k for r in table for k in r))
    with (NOTE_DIR / "target_verdicts.tsv").open("w", newline="") as fh:
        w = csv.DictWriter(
            fh, fieldnames=fields, delimiter="\t", lineterminator="\n", restval=""
        )
        w.writeheader()
        w.writerows(table)
    with (NOTE_DIR / "target_verdict_negatives.tsv").open("w", newline="") as fh:
        w = csv.DictWriter(
            fh, fieldnames=list(negatives[0]), delimiter="\t", lineterminator="\n"
        )
        w.writeheader()
        w.writerows(negatives)


if __name__ == "__main__":
    main()
