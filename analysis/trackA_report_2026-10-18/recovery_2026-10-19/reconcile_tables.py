"""Reconcile existing Track A receipts without changing scientific outputs."""

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path("/exports/archive/hg-funcgenom-research/mdmanurung/viralscan_work/trackA_round1")
HERE = Path(__file__).resolve().parent
ARMS = ("combined_off", "combined_artefact", "twostep")


def read(path):
    with Path(path).open() as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write(name, rows):
    assert rows
    with (HERE / name).open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    manifest = [m for m in read(ROOT / "manifest.tsv") if m["dataset"] != "tonsil_atlas"]
    assert len(manifest) == 71 and len({m["sample"] for m in manifest}) == 71
    tiers = {t["evidence_dir"]: t for t in read(ROOT / "evidence/tiers.tsv")}
    calls = [c for c in read(ROOT / "evidence/calls.tsv") if c["dataset"] != "tonsil_atlas"]
    joined = []
    anello_kallisto = []
    for call in calls:
        key = "__".join((call["dataset"], call["sample"], call["arm"], re.sub(r"[^A-Za-z0-9]+", "_", call["virus"]).strip("_")))
        assert key in tiers, key
        t = tiers[key]
        joined.append({"dataset": call["dataset"], "library": call["sample"], "virus": call["virus"], "tier": t["tier"], "counted_virus_best": t["counted_virus_best"], "cells": t["cells"], "sibling_status": t["sibling_status"], "specific_molecules": t["specific_molecules"], "specific_cells": t["specific_cells"], "evidence_dir": key})
        if call["arm"] == "combined_off" and call["anellovirus"] == "true":
            source = ROOT / "evidence" / key / "read_support_summary.tsv"
            summary = read(source)
            assert len(summary) == 1
            anello_kallisto.append({"dataset": call["dataset"], "library": call["sample"], "virus": call["virus"], "screening_molecules": call["molecules"], "evidence_dir": key, "n_pass_all_gates": summary[0]["n_pass_all_gates"], "source_summary_sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
    assert len(joined) == len(tiers) == 281
    write("reconciled_evidence.tsv", joined)
    assert len(anello_kallisto) == 54
    write("all_primary_kallisto_anello_q137.tsv", anello_kallisto)
    inventory = []
    for m in manifest:
        ds, lib = m["dataset"], m["sample"]
        for arm in ARMS:
            base = ROOT / f"runs/{ds}/{arm}/{lib}"
            validator = ROOT / f"validate_run_2026-10-19/noverify/{ds}__{arm}__{lib}.json"
            validation = json.loads(validator.read_text()) if validator.exists() else {}
            inventory.append({"dataset": ds, "library": lib, "arm": arm, "run_complete": (base / "run_complete.json").exists(), "structural_validation_ok": validation.get("ok", "missing"), "input_hashes_reverified": False})
    write("run_inventory.tsv", inventory)
    variant_calls = []
    for m in manifest:
        for arm in ARMS:
            path = ROOT / f"runs/{m['dataset']}/{arm}/{m['sample']}/{m['sample']}/results/viral_summary.tsv"
            for row in read(path):
                if row["detected"].lower() != "true":
                    continue
                variant_calls.append({"dataset": m["dataset"], "library": m["sample"], "arm": arm, "virus": row["virus_name"], "viral_molecules_total_est": row["viral_molecules_total_est"], "infected_called": row["infected_called"], "claim_scope": row["claim_scope"], "evidence_scope": "primary tiers only" if arm == "combined_off" else "selected extra-arm evidence only"})
    write("all_arm_screening_calls.tsv", variant_calls)
    extras = []
    for path in sorted((ROOT / "evidence_extra_2026-10-19").glob("*/read_support_summary.tsv")):
        row = read(path)[0]
        extras.append(row)
    assert len(extras) == 10
    write("extra_arm_read_support.tsv", extras)
    anello = []
    zero_recoveries = {}
    for path in HERE.glob("zero_recovery_receipts/*.json"):
        receipt = json.loads(path.read_text())
        assert receipt["mapped_reads"] == 0
        assert receipt["expected_input_pairs"] == receipt["observed_input_reads"]
        zero_recoveries[(receipt["dataset"], receipt["library"], receipt["setting"])] = str(path)
    for m in manifest:
        if m["dataset"] == "hpv16":
            continue
        for setting, suffix in (("shipped", ""), ("relaxed", "_relaxed")):
            ds, lib = m["dataset"], m["sample"]
            align = ROOT / f"anello_align{suffix}_2026-10-19/{ds}/{lib}"
            classifier = ROOT / f"anello_classify{suffix}_2026-10-19/{ds}/{lib}"
            path = classifier / "library_summary.tsv"
            original_done = (align / "log/anello_align.done").exists()
            zero_receipt = zero_recoveries.get((ds, lib, setting), "")
            result = read(path)[0] if path.exists() and (original_done or zero_receipt) else {}
            if zero_receipt:
                assert result and int(result["star_molecules"]) == 0 and int(result["candidate_molecules"]) == 0
            anello.append({"dataset": ds, "library": lib, "setting": setting, "alignment_done_marker": original_done, "zero_mapping_recovery_receipt": zero_receipt, "classifier_summary_present": bool(result), "star_molecules": result.get("star_molecules", "not_completed"), "candidate_molecules": result.get("candidate_molecules", "not_completed"), "candidate_cells": result.get("candidate_cells", "not_completed"), "candidate_start_sites": result.get("candidate_start_sites", "not_completed"), "final_verdict": "pending_full_preregistered_test"})
    assert len(anello) == 138
    write("anello_execution_inventory.tsv", anello)
    controls = []
    settle = ROOT / "anello_settle_2026-10-19"
    parity = read(settle / "parity_GSM5017024/parity.tsv")
    parity_ok = len(parity) == 13 and all(r["match"] == "True" for r in parity)
    for ds in ("hhv6b", "hnscc_gse164690", "hsv1", "ebv"):
        version = "plant" if ds == "hhv6b" else "plant_v3_tail5"
        for setting in ("shipped", "relaxed"):
            path = settle / version / ds / setting / "score.tsv"
            exact = [r for r in read(path) if r["identity_band"] == "exact" and r["level"] == "100"] if path.exists() else []
            n = sum(int(r["planted"]) for r in exact)
            assert n in (0, 600)
            star = sum(int(r["star_recovered"]) for r in exact) / n if n else None
            candidate = sum(int(r["candidate_recovered"]) for r in exact) / n if n else None
            log = settle / f"control_negative/{setting}/anello_align/Log.final.out"
            metrics = {a.strip(): b.strip() for line in log.read_text().splitlines() if "|" in line for a, b in [line.split("|", 1)]}
            negative_ok = int(metrics["Number of input reads"]) > 0 and int(metrics["Uniquely mapped reads number"]) == 0 and int(metrics["Number of reads mapped to multiple loci"]) == 0
            controls.append({"dataset": ds, "plant_version": version, "setting": setting, "exact_molecules_at_level_100": n, "star_recovery": star if n else "not_scored", "candidate_recovery": candidate if n else "not_scored", "star_gate": star >= 0.90 if n else "not_scored", "classifier_gate": candidate >= 0.50 if n else "not_scored", "negative_control_zero_alignments": negative_ok, "parity_13_fields_match": parity_ok, "scope": "exact-panel aggregate; not a universal per-genus limit"})
    write("anello_control_gates.tsv", controls)
    summary = {"libraries": len(manifest), "libraries_by_dataset": dict(Counter(m["dataset"] for m in manifest)), "runs": len(inventory), "runs_complete": sum(r["run_complete"] for r in inventory), "structural_validation_ok": sum(r["structural_validation_ok"] is True for r in inventory), "combined_off_calls_with_tiers": len(joined), "extra_arm_selected_calls": len(extras), "tier_counts": dict(Counter(t["tier"] for t in joined)), "input_hashes_reverified": False, "input_table_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT / "manifest.tsv", ROOT / "evidence/calls.tsv", ROOT / "evidence/tiers.tsv", ROOT / "evidence/sibling_specific.tsv"]}}
    (HERE / "reconciliation.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "input_table_sha256"}, indent=2))


if __name__ == "__main__":
    main()
