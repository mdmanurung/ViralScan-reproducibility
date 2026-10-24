"""Locate the zero-alignment STARsolo failure without changing alignment gates."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent / "zero_solo_reproduction"
original = json.loads((root / "receipt.json").read_text())[0]["command"]
results = []
for name, option, value in (("tag_raw_umi_unique", "--soloType", "CB_samTagOut"),):
    out = root / name
    out.mkdir(exist_ok=False)
    command = list(original)
    command[command.index("--outFileNamePrefix") + 1] = str(out) + "/"
    if option in command:
        command[command.index(option) + 1] = value
    else:
        command.extend([option, value])
    if name == "tag_raw_umi_unique":
        command.extend(["--soloCBmatchWLtype", "Exact"])
        command.remove("UB")
        command.remove("EM")
    with (out / "execution.log").open("w") as log:
        process = subprocess.run(["timeout", "--signal=TERM", "--kill-after=10s", "120s", *command], stdout=log, stderr=subprocess.STDOUT)
    results.append({"case": name, "returncode": process.returncode, "command": command})
    print(name, process.returncode, flush=True)
(root / "raw_umi_unique_probe_receipt.json").write_text(json.dumps(results, indent=2) + "\n")
