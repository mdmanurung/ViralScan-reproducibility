"""Bounded native zero-mapping Drop-seq crash reproduction; no source edits."""
import gzip
import json
import shlex
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2].parent / "viralscan_work/trackA_round1"
root = HERE / "zero_solo_reproduction"
root.mkdir(exist_ok=False)
for mate, sequence in ((1, "ACGT" * 5), (2, "N" * 64)):
    with gzip.open(root / f"R{mate}.fastq.gz", "wt") as handle:
        for i in range(20):
            handle.write(f"@zero{i}\n{sequence}\n+\n{'I' * len(sequence)}\n")
line = (ROOT / "logs/tA_anello_aln_25842242.log").read_text().splitlines()[0]
original = shlex.split(line.split("anello_align: ", 1)[1])
results = []
for mode in ("EM", "Unique"):
    out = root / mode
    out.mkdir()
    command = list(original)
    command[command.index("--readFilesIn") + 1:command.index("--readFilesIn") + 3] = [str(root / "R2.fastq.gz"), str(root / "R1.fastq.gz")]
    command[command.index("--outFileNamePrefix") + 1] = str(out) + "/"
    if mode == "Unique":
        command.remove("EM")
    with (out / "execution.log").open("w") as log:
        process = subprocess.run(["timeout", "--signal=TERM", "--kill-after=10s", "120s", *command], stdout=log, stderr=subprocess.STDOUT)
    results.append({"mode": mode, "returncode": process.returncode, "command": command, "bam_exists": (out / "Aligned.sortedByCoord.out.bam").exists()})
    print(mode, process.returncode, flush=True)
(root / "receipt.json").write_text(json.dumps(results, indent=2) + "\n")
