"""Compare positive-read mapping before accepting zero-only technical recovery."""
import gzip
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
root = HERE / "zero_solo_reproduction"
original = json.loads((root / "receipt.json").read_text())[0]["command"]
tag = json.loads((root / "raw_umi_unique_probe_receipt.json").read_text())[0]["command"]
assert json.loads((root / "raw_umi_unique_probe_receipt.json").read_text())[0]["returncode"] == 0
reference = Path(original[original.index("--genomeDir") + 1]) / "anello.fa"
sequence = ""
with reference.open() as handle:
    for line in handle:
        if line.startswith(">"):
            if sequence:
                break
        else:
            sequence += line.strip()
assert len(sequence) > 200
for mate, seq in ((1, "ACGTACGTACGTACGTACGT"), (2, sequence[100:164])):
    with gzip.open(root / f"positive_R{mate}.fastq.gz", "wt") as handle:
        for i in range(20):
            handle.write(f"@positive{i}\n{seq}\n+\n{'I' * len(seq)}\n")
mapped = []
for name, template in (("positive_original", original), ("positive_tag", tag)):
    out = root / name
    out.mkdir(exist_ok=False)
    command = list(template)
    i = command.index("--readFilesIn")
    command[i + 1:i + 3] = [str(root / "positive_R2.fastq.gz"), str(root / "positive_R1.fastq.gz")]
    command[command.index("--outFileNamePrefix") + 1] = str(out) + "/"
    with (out / "execution.log").open("w") as log:
        subprocess.run(["timeout", "--signal=TERM", "--kill-after=10s", "120s", *command], check=True, stdout=log, stderr=subprocess.STDOUT)
    records = subprocess.run(["samtools", "view", str(out / "Aligned.sortedByCoord.out.bam")], check=True, capture_output=True, text=True).stdout.splitlines()
    # CB/UB encode counting-stage corrections; every mapping field and raw tag must agree.
    records = sorted(tuple(r.split("\t")[:11]) + tuple(sorted(t for t in r.split("\t")[11:] if not t.startswith(("CB:", "UB:")))) for r in records)
    assert records and all(int(r[1]) & 4 == 0 for r in records)
    mapped.append(records)
assert mapped[0] == mapped[1]
zero = root / "tag_raw_umi_unique/Aligned.sortedByCoord.out.bam"
subprocess.run(["samtools", "quickcheck", str(zero)], check=True)
assert subprocess.run(["samtools", "view", "-c", "-F", "4", str(zero)], check=True, capture_output=True, text=True).stdout.strip() == "0"
result = {"positive_alignment_records": len(mapped[0]), "mapping_fields_and_raw_tags_exact": True, "corrected_CB_UB_compared": False, "zero_bam_valid_and_empty": True, "real_recovery_permitted_only_if_zero_mapped_and_full_input_count_matches": True}
(root / "mapping_parity.json").write_text(json.dumps(result, indent=2) + "\n")
print(result)
