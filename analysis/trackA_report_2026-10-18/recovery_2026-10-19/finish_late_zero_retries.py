"""After the first batch, recover later failures without duplicating live work."""
import datetime as dt
import json
import os
import shlex
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2].parent / "viralscan_work/trackA_round1"
task_path = HERE / "zero_recovery_tasks.json"
initial = json.loads(task_path.read_text())
snapshot = HERE / "zero_recovery_tasks_initial29.json"
assert len(initial) == 29 and not snapshot.exists()
snapshot.write_text(task_path.read_text())
mapping = {}
for line in (ROOT / "anello_settle_2026-10-19/real_other_jobs.txt").read_text().splitlines():
    ds, lib, setting, star, classifier = line.split()
    job = star.split("=", 1)[1]
    if job.isdigit():
        mapping[job] = (ds, lib, setting, classifier.split("=", 1)[1])
allocation = subprocess.run(["scontrol", "show", "job", "25833654", "-o"], check=True, capture_output=True, text=True).stdout
end = next(x.split("=", 1)[1] for x in allocation.split() if x.startswith("EndTime="))
allocation_end = dt.datetime.fromisoformat(end).timestamp()
while True:
    log = (HERE / "zero_recovery_execution.log").read_text()
    queue = subprocess.run(["squeue", "-u", os.environ["USER"], "-h", "-o", "%i"], check=True, capture_output=True, text=True).stdout.split()
    if "Complete log(s):" in log and not set(queue).intersection(mapping):
        break
    if time.time() > allocation_end - 7200:
        raise TimeoutError("No remaining recovery window; preserve pending work")
    time.sleep(30)
accounting = subprocess.run(["sacct", "-u", os.environ["USER"], "-S", "2026-10-19", "-X", "-n", "-P", "-o", "JobID,State"], check=True, capture_output=True, text=True).stdout
failed = {line.split("|")[0] for line in accounting.splitlines() if "|FAILED|" in line}
additional, unhandled = {}, []
for job in sorted(failed.intersection(mapping).difference(initial)):
    ds, lib, setting, classifier = mapping[job]
    path = ROOT / f"logs/tA_anello_aln_{job}.log"
    text = path.read_text()
    if ds != "hsv1" or "Segmentation fault" not in text or "started Solo counting" not in text:
        unhandled.append(job)
        continue
    original = shlex.split(text.splitlines()[0].split("anello_align: ", 1)[1])
    additional[job] = {"dataset": ds, "library": lib, "setting": setting, "failed_alignment_job": job, "blocked_classifier_job": classifier, "original_command": original, "original_failure_log": str(path)}
packet = {"initial_batch_ids": sorted(initial), "initial_batch_missing_receipts": [job for job in initial if not (HERE / f"zero_recovery_receipts/{job}.json").exists()], "additional_ids": sorted(additional), "other_failures_requiring_diagnosis": unhandled, "new_scheduler_submissions": 0}
(HERE / "late_zero_retry_plan.json").write_text(json.dumps(packet, indent=2) + "\n")
if additional:
    assert json.loads(task_path.read_text()) == initial
    # Append task identities only after the first controller has finished all workers.
    task_path.write_text(json.dumps({**initial, **additional}, indent=2) + "\n")
    targets = [str(HERE / f"zero_recovery_receipts/{job}.json") for job in additional]
    command = ["timeout", "--signal=TERM", "--kill-after=10s", f"{int(allocation_end - time.time() - 120)}s", "/exports/archive/hg-funcgenom-research/mdmanurung/venvs/snakemake_slurm/bin/snakemake", "--snakefile", str(HERE / "zero_mapping_recovery.smk"), "--cores", "6", "--keep-going", *targets]
    result = subprocess.run(command)
    packet["returncode"] = result.returncode
    packet["additional_missing_receipts"] = [job for job in additional if not (HERE / f"zero_recovery_receipts/{job}.json").exists()]
else:
    packet["returncode"] = 0
(HERE / "late_zero_retry_execution_receipt.json").write_text(json.dumps(packet, indent=2) + "\n")
raise SystemExit(packet["returncode"])
