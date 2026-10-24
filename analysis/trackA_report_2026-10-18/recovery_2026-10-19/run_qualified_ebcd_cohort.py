"""Run only the qualified engine after the bounded probes release their CPU."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
A = HERE.parents[1] / "trackA_host_programs"
PROBE = HERE.parent / "outputs/production-shape-probe-20261020"
deadline = time.monotonic() + 4200
while True:
    try:
        statuses = {method: json.loads((PROBE / method / "probe_status.json").read_text()) for method in ("gbcd", "ebcd", "divas")}
        break
    except (FileNotFoundError, json.JSONDecodeError):
        if time.monotonic() >= deadline:
            raise TimeoutError("Bounded probes did not finish; no cohort work started") from None
        time.sleep(15)
assert statuses["ebcd"]["status"] == "finite_bounded_basis"
assert not statuses["ebcd"].get("warnings")
inputs = json.loads((PROBE / "input_receipt.json").read_text())
assert inputs["adapter_sha256"] == hashlib.sha256((A / "methods.R").read_bytes()).hexdigest()
production = json.loads((A / "config.json").read_text())
configuration = A / "cohort_preparation_20261019.json"
prepared = json.loads(configuration.read_text())
assert {k: v for k, v in production.items() if k != "output_root"} == {k: v for k, v in prepared.items() if k != "output_root"}
packet = json.loads((HERE / "ebcd_cohort_targets_20261020.json").read_text())
targets = packet["targets"]
assert len(targets) == 22 and all(path.endswith("/ebcd/status.json") for path in targets)
assert sum("/discovery/" in p for p in targets) == 6
assert sum("/prediction/" in p for p in targets) == 16
command = ["timeout", "--signal=TERM", "--kill-after=10s", "86400s", "/exports/archive/hg-funcgenom-research/mdmanurung/venvs/snakemake_slurm/bin/snakemake", "--snakefile", str(A / "Snakefile"), "--config", f"analysis_config={configuration}", "--cores", "1", "--resources", "mem_mb=64000", "--keep-going", *targets]
receipt = {"engine": "ebcd", "qualification_status": statuses["ebcd"], "scope": "six discovery scopes and sixteen held-out prediction tasks; full original rank/seed grid", "production_config_changed": False, "allocation": os.environ.get("SLURM_JOB_ID"), "cpu": 11, "native_threads": 1, "step_memory_mb": 64000, "controller_cap_seconds": 86400, "command": command, "cohort_complete": False}
(HERE / "ebcd_cohort_launch.json").write_text(json.dumps(receipt, indent=2) + "\n")
print("Starting qualified EBCD cohort targets only", flush=True)
result = subprocess.run(command)
receipt["returncode"] = result.returncode
receipt["completed_targets"] = {path: json.loads(Path(path).read_text()) for path in targets if Path(path).exists()}
receipt["cohort_complete"] = result.returncode == 0 and len(receipt["completed_targets"]) == len(targets)
receipt["other_engines_complete"] = False
(HERE / "ebcd_cohort_execution_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
raise SystemExit(result.returncode)
