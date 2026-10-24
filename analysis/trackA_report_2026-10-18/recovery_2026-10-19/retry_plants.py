"""Retry the three failed v3 plants, then release their existing alignments."""

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/exports/archive/hg-funcgenom-research/mdmanurung/viralscan_work/trackA_round1")
HERE = Path(__file__).resolve().parent
TASKS = [
    ("hnscc_gse164690", "GSM5017024", 98, 16, 10, [25842487, 25842489]),
    ("hsv1", "GSM3511335", 64, 12, 8, [25842492, 25842494]),
    ("ebv", "GSM4796272", 98, 16, 10, [25842497, 25842499]),
]


def main():
    for ds, lib, length, cb, umi, jobs in TASKS:
        receipt = HERE / f"retry_{ds}.json"
        if receipt.exists():
            raise ValueError(f"Recovery already recorded: {receipt}")
        command = [sys.executable, str(ROOT / "scripts/trackA_anello_plant.py"), ds, lib, "3p", str(length), str(cb), str(umi), "--tail-rate", "0.05", "--plant-dir", "plant_v3_tail5"]
        with (HERE / f"retry_{ds}.log").open("x") as log:
            subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
        out = ROOT / "anello_settle_2026-10-19/plant_v3_tail5" / ds
        manifest = json.loads((out / "plant_manifest.json").read_text())
        with (out / "truth.tsv").open() as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        assert len(rows) == manifest["n_planted_reads"] > 0
        assert manifest["tail_rate"] == 0.05 and manifest["seed"] == 20261019
        assert all(int(r["body_len"]) + int(r["tail_len"]) == length for r in rows)
        rate = sum(int(r["tail_len"]) > 0 for r in rows) / len(rows)
        assert 0.02 < rate < 0.08
        for job in jobs:
            state = subprocess.run(["scontrol", "show", "job", str(job)], capture_output=True, text=True, check=True).stdout
            assert "JobState=PENDING" in state and "DependencyNeverSatisfied" in state, state
        result = {"command": command, "manifest": manifest, "observed_tail_rate": rate, "truth_sha256": hashlib.sha256((out / "truth.tsv").read_bytes()).hexdigest(), "released_alignment_jobs": []}
        receipt.write_text(json.dumps(result, indent=2) + "\n")
        for job in jobs:
            subprocess.run(["scontrol", "update", f"JobId={job}", "Dependency="], check=True)
            result["released_alignment_jobs"].append(job)
            receipt.write_text(json.dumps(result, indent=2) + "\n")
        print(ds, "plant validated; existing alignments released", jobs, flush=True)


if __name__ == "__main__":
    main()
