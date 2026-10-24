"""Verify a failed search only if a complete native remapping contains no hits."""
import csv
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2].parent / "viralscan_work/trackA_round1"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    job = sys.argv[1]
    task = json.loads((HERE / "zero_recovery_tasks.json").read_text())[job]
    parity = json.loads((HERE / "zero_solo_reproduction/mapping_parity.json").read_text())
    assert parity["mapping_fields_and_raw_tags_exact"] and parity["zero_bam_valid_and_empty"]
    ds, lib, setting = (task[k] for k in ("dataset", "library", "setting"))
    assert ds == "hsv1"
    classifier_job = task["blocked_classifier_job"]
    # scontrol forgets finished jobs; sacct keeps them. The blocked classifier must never have started.
    state = subprocess.run(["sacct", "-j", classifier_job, "-X", "-n", "-P", "-o", "State,Start"], check=True, capture_output=True, text=True).stdout.strip()
    assert state.split("|")[0] == "PENDING" or (state.startswith("CANCELLED") and state.endswith("|None")), state
    suffix = "_relaxed" if setting == "relaxed" else ""
    classified = ROOT / f"anello_classify{suffix}_2026-10-19/{ds}/{lib}"
    assert not classified.exists(), classified
    out = ROOT / f"anello_zero_verification_2026-10-20/{ds}/{lib}/{setting}"
    out.mkdir(parents=True, exist_ok=False)
    command = list(task["original_command"])
    assert command[command.index("--soloCBwhitelist") + 1] == "None"
    assert command[command.index("--soloType") + 1] == "CB_UMI_Simple"
    # No-whitelist CBs remain raw. Corrected UMI counting is skipped only for a zero-hit proof.
    command[command.index("--soloType") + 1] = "CB_samTagOut"
    command.extend(["--soloCBmatchWLtype", "Exact"])
    command.remove("UB")
    command.remove("EM")
    command[command.index("--runThreadN") + 1] = "6"
    command[command.index("--outFileNamePrefix") + 1] = str(out) + "/"
    i = command.index("--readFilesIn")
    fastqs = [Path(command[i + 1]), Path(command[i + 2])]
    before = {str(p): [p.stat().st_size, p.stat().st_mtime_ns] for p in fastqs}
    audit = fastqs[0].parent / "host_filter_audit.tsv"
    with audit.open() as handle:
        expected = [int(r["fragments"]) for r in csv.DictReader(handle, delimiter="\t") if r["category"] == "retained_host_unmapped"]
    assert len(expected) == 1 and expected[0] > 0
    with (out / "execution.log").open("w") as log:
        subprocess.run(["timeout", "--signal=TERM", "--kill-after=10s", "7200s", *command], check=True, stdout=log, stderr=subprocess.STDOUT)
    bam = out / "Aligned.sortedByCoord.out.bam"
    subprocess.run(["samtools", "quickcheck", str(bam)], check=True)
    mapped = int(subprocess.run(["samtools", "view", "-c", "-F", "4", str(bam)], check=True, capture_output=True, text=True).stdout)
    # Any mapped record makes this recovery ineligible: do not infer its corrected molecule count.
    assert mapped == 0, f"Nonzero mapping requires the original corrected-UMI path: {mapped}"
    stats = dict(line.strip().split("|", 1) for line in (out / "Log.final.out").read_text().splitlines() if "|" in line)
    stats = {k.strip(): v.strip() for k, v in stats.items()}
    assert int(stats["Number of input reads"]) == expected[0]
    assert int(stats["Uniquely mapped reads number"]) == 0
    assert int(stats["Number of reads mapped to multiple loci"]) == 0
    assert before == {str(p): [p.stat().st_size, p.stat().st_mtime_ns] for p in fastqs}
    assert not classified.exists(), classified
    classify =[sys.executable, str(ROOT / "scripts/trackA_anello_classify.py"), "bam", str(bam), str(classified), "--threads", "1"]
    with (out / "classifier.log").open("w") as log:
        subprocess.run(classify, check=True, stdout=log, stderr=subprocess.STDOUT)
    with (classified / "library_summary.tsv").open() as handle:
        summary = list(csv.DictReader(handle, delimiter="\t"))
    assert len(summary) == 1
    assert all(int(summary[0][key]) == 0 for key in ("star_aligned_reads", "star_molecules", "candidate_molecules"))
    receipt = {**task, "allocation": os.environ.get("SLURM_JOB_ID"), "recovery_kind": "independent_full_depth_zero_mapping_verification", "command": command, "classifier_command": classify, "expected_input_pairs": expected[0], "observed_input_reads": int(stats["Number of input reads"]), "mapped_reads": mapped, "bam": str(bam), "bam_sha256": sha(bam), "input_fastq_stats_unchanged": before, "input_fastqs_rehashed": False, "host_filter_audit_sha256": sha(audit), "summary": summary[0], "corrected_umi_counting_not_run": True, "original_failure_outputs_preserved": True, "final_dataset_verdict": "pending_full_preregistered_test"}
    path = HERE / f"zero_recovery_receipts/{job}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    if state.startswith("PENDING"):
        subprocess.run(["scancel", classifier_job], check=True)
    print(job, lib, setting, "full-depth zero mapping verified", flush=True)


if __name__ == "__main__":
    main()
