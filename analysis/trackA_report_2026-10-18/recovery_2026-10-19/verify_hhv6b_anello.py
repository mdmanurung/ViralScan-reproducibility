"""Validate all HHV-6B searches and emit narrowly scoped preregistered verdicts."""
import csv
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2].parent / "viralscan_work/trackA_round1"
SAMTOOLS = "/exports/archive/hg-funcgenom-research/mdmanurung/conda/envs/viralscan_test_full/bin/samtools"


def read(path):
    with path.open() as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


inventory = [r for r in read(HERE / "anello_execution_inventory.tsv") if r["dataset"] == "hhv6b"]
assert len(inventory) == 26 and len({r["library"] for r in inventory}) == 13
controls = [r for r in read(HERE / "anello_control_gates.tsv") if r["dataset"] == "hhv6b"]
assert len(controls) == 2 and {r["setting"] for r in controls} == {"shipped", "relaxed"}
assert all(r[key] == "True" for r in controls for key in ("star_gate", "classifier_gate", "negative_control_zero_alignments", "parity_13_fields_match"))
calls = [r for r in read(HERE / "all_primary_kallisto_anello_q137.tsv") if r["dataset"] == "hhv6b"]
assert len(calls) == 5 and all(int(r["n_pass_all_gates"]) == 0 for r in calls)
rows = []
for row in inventory:
    assert row["alignment_done_marker"] == "True" and row["classifier_summary_present"] == "True"
    lib, setting = row["library"], row["setting"]
    assert int(row["star_molecules"]) == 0 and int(row["candidate_molecules"]) == 0
    suffix = "_relaxed" if setting == "relaxed" else ""
    base = ROOT / f"anello_align{suffix}_2026-10-19/hhv6b/{lib}/anello_align"
    bam = base / "Aligned.sortedByCoord.out.bam"
    subprocess.run([SAMTOOLS, "quickcheck", str(bam)], check=True)
    count = int(subprocess.run([SAMTOOLS, "view", "-c", "-F", "4", str(bam)], check=True, capture_output=True, text=True).stdout)
    assert count == 0
    stats = {k.strip(): v.strip() for k, v in (line.split("|", 1) for line in (base / "Log.final.out").read_text().splitlines() if "|" in line)}
    audit = ROOT / f"runs/hhv6b/twostep/{lib}/{lib}/host_filtered/host_filter_audit.tsv"
    expected = [int(r["fragments"]) for r in read(audit) if r["category"] == "retained_host_unmapped"]
    assert len(expected) == 1 and int(stats["Number of input reads"]) == expected[0]
    rows.append({"library": lib, "setting": setting, "mapped_reads": count, "star_input_pairs": int(stats["Number of input reads"]), "retained_host_unmapped_pairs": expected[0], "bam_sha256": sha(bam), "star_final_sha256": sha(base / "Log.final.out"), "host_filter_audit_sha256": sha(audit)})
with (HERE / "hhv6b_anello_full_depth_checks.tsv").open("w") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)
print("Verified full-depth empty BAMs:", len(rows), flush=True)
verdicts = [{"library": library, "preregistered_verdict": "NEGATIVE", "scope": "indexed genomes and preregistered gates only; exact-panel aggregate sensitivity, no universal genus limit"} for library in sorted({r["library"] for r in inventory})]
receipt = {"dataset": "hhv6b", "completed_searches": len(rows), "libraries": len(verdicts), "primary_kallisto_anello_calls": len(calls), "kallisto_q137_passing_molecules": 0, "all_real_bams_independently_verified_empty": True, "all_star_input_counts_match_retained_host_filter_audits": True, "fastqs_independently_recounted": False, "controls": controls, "library_verdicts": verdicts, "dataset_conclusion": "No genuine anellovirus RNA detected under the indexed-genome search and preregistered gates.", "sensitivity_scope": "At 100 molecules per exact-panel genome, aggregate recovery across six genomes was 0.9517 shipped / 0.9650 relaxed; per-genome recovery varies. This is not a universal per-genus or 95-percent detection limit.", "deletion_authorized": False}
(HERE / "hhv6b_anello_verified.json").write_text(json.dumps(receipt, indent=2) + "\n")
