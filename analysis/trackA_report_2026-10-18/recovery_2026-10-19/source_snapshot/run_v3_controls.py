"""Complete the six approved v3 control tasks in the existing allocation."""

import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("/exports/archive/hg-funcgenom-research/mdmanurung/viralscan_work/trackA_round1")
TASKS = [
    ("hnscc_gse164690", "10xv2", [(25842487, 25842488), (25842489, 25842490)]),
    ("hsv1", "dropseq", [(25842492, 25842493), (25842494, 25842495)]),
    ("ebv", "10xv2", [(25842497, 25842498), (25842499, 25842500)]),
]


def main():
    for ds, technology, pairs in TASKS:
        deadline = time.monotonic() + 3600
        plant_receipt = HERE / f"retry_{ds}.json"
        while True:
            try:
                ready = json.loads(plant_receipt.read_text())
                if ready["released_alignment_jobs"] == [p[0] for p in pairs]:
                    break
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            if time.monotonic() > deadline:
                raise TimeoutError(f"Plant recovery not ready: {ds}")
            time.sleep(15)
        plant = ROOT / f"anello_settle_2026-10-19/plant_v3_tail5/{ds}"
        for setting, (alignment, classifier) in zip(("shipped", "relaxed"), pairs, strict=True):
            receipt = HERE / f"control_{ds}_{setting}.json"
            assert not receipt.exists(), receipt
            for job in (alignment, classifier):
                state = subprocess.run(["scontrol", "show", "job", str(job)], check=True, capture_output=True, text=True).stdout
                assert "JobState=PENDING" in state, state
            subprocess.run(["scontrol", "hold", str(alignment), str(classifier)], check=True)
            out = plant / setting
            commands = [
                [sys.executable, str(ROOT / "scripts/trackA_anello_align.py"), "--r1", str(plant / "planted/R1.fastq.gz"), "--r2", str(plant / "planted/R2.fastq.gz"), "--out", str(out / "star"), "--technology", technology, "8", "--setting", setting],
                [sys.executable, str(ROOT / "scripts/trackA_anello_classify.py"), "bam", str(out / "star/anello_align/Aligned.sortedByCoord.out.bam"), str(out / "classify"), "--threads", "8"],
                [sys.executable, str(ROOT / "scripts/trackA_anello_score.py"), str(plant), str(out / "classify"), str(out / "score.tsv")],
            ]
            started = time.monotonic()
            with (HERE / f"control_{ds}_{setting}.log").open("x") as log:
                for command in commands:
                    subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=3600)
            with (out / "score.tsv").open() as handle:
                exact = [r for r in csv.DictReader(handle, delimiter="\t") if r["identity_band"] == "exact" and r["level"] == "100"]
            n = sum(int(r["planted"]) for r in exact)
            assert n == 600
            star = sum(int(r["star_recovered"]) for r in exact) / n
            candidate = sum(int(r["candidate_recovered"]) for r in exact) / n
            assert (out / "star/log/anello_align.done").exists()
            result = {"dataset": ds, "setting": setting, "commands": commands, "allocation": os.environ.get("SLURM_JOB_ID"), "elapsed_seconds": time.monotonic() - started, "star_exact_100": star, "candidate_exact_100": candidate, "star_gate": star >= 0.90, "classifier_gate": candidate >= 0.50, "replaces_pending_jobs": [alignment, classifier], "new_scheduler_jobs": 0}
            receipt.write_text(json.dumps(result, indent=2) + "\n")
            subprocess.run(["scancel", str(alignment), str(classifier)], check=True)
            print(ds, setting, "complete", star, candidate, flush=True)


if __name__ == "__main__":
    main()
