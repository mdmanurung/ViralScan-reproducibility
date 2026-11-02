"""HOST-05 collect (round 2026-11-02): host-loss on the planted EBV arms, SENS-07 scores per arm, endogenous molecules.

    python host05_collect.py [--root DATA/runs/round_2026-11-02/host05]

Writes only under ROOT/{host_loss_*,score_*,summary}/ (new dirs; refuses to overwrite). Reads runs and inputs only.
Needs PYTHONPATH=<pin>/src and the viralscan_test_full env. Wilson 95% interval for every fraction.
"""
import argparse
import csv
import json
import math
import subprocess
import sys
from pathlib import Path

REPRO = Path(
    "/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility")
P2C = REPRO / "data/runs/work/dsr_round2c/runs/ebv/sens07/SRR12682296/plant"
SENS = REPRO / "scripts/sens07_planted_sensitivity.py"
S = "SRR12682296"


def wilson(k, n, z=1.959964):
    if n == 0:
        return (math.nan, math.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def sh(cmd):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run([str(c) for c in cmd], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(REPRO / "data/runs/round_2026-11-02/host05"))
    root = Path(ap.parse_args().root)
    out = root / "summary"
    out.mkdir(exist_ok=False)
    truth = P2C / "truth.tsv"
    conv = out / "truth_for_loss.tsv"
    with open(truth, newline="") as fh, open(conv, "w") as o:
        o.write("read_id\tlabel\tmolecule_id\n")
        for r in csv.DictReader(fh, delimiter="\t"):
            o.write(f"{r['read_id']}\tviral\t{r['cb']}-{r['umi']}\n")
    rows = []
    for f in ("pinned", "star-default"):
        arm = root / f"ebv_planted_{f}"
        hl = root / f"host_loss_{f}"
        sh([sys.executable, "-m", "viralscan.menu", "host-loss", "--run-dir", arm / "run" / S, "--truth", conv, "-o", hl])
        j = json.loads((hl / "host_loss.json").read_text())
        c = j.get("counts", j)
        rows.append((f, c))
    with open(out / "host_loss.tsv", "w") as o:
        o.write("star_params\tfragments\tremoved\tfrag_loss\tfrag_ci_lo\tfrag_ci_hi\tmolecules\tlost\tmol_loss\tmol_ci_lo\tmol_ci_hi\tnot_in_lineage\n")
        for f, c in rows:
            nf, rf, nm, lm = c["d15_truth_fragments"], c["d15_removed_fragments"], c["d16_truth_molecules"], c["d16_lost_molecules"]
            fl, fh_ = wilson(rf, nf)
            ml, mh = wilson(lm, nm)
            o.write(f"{f}\t{nf}\t{rf}\t{rf / nf:.5f}\t{fl:.5f}\t{fh_:.5f}\t{nm}\t{lm}\t{lm / nm:.5f}\t{ml:.5f}\t{mh:.5f}\t{c['not_in_lineage']}\n")
    for f in ("none", "pinned", "star-default"):
        run = root / f"ebv_planted_{f}/run/{S}"
        twin = root / f"ebv_unplanted_{f}/run/{S}"
        sh([sys.executable, SENS, "score", "--out-dir", root / f"score_{f}", "--truth", truth,
            "--counts-h5ad", run / "kb-python/counts_unfiltered/adata_multimap.h5ad",
            "--twin-h5ad", twin / "kb-python/counts_unfiltered/adata_multimap.h5ad",
            "--layer", "X", "--identity", run / "results/virus_identity.tsv"])
    print("host_loss.tsv and score_* written under", root)


if __name__ == "__main__":
    main()
