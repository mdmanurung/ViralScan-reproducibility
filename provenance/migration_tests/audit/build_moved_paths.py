#!/usr/bin/env python3
"""Single source of truth for what leaves the package: classify.py manifest + move sets + triage + decisions.
usage: build_moved_paths.py <outdir>   (reads <outdir>/file_manifest.tsv made by classify.py with REF=origin/main)
writes: moved_paths.txt (repro gets these, incl. history) ; both_paths.txt (stay AND copy) ; delete_paths.txt ;
        stay_paths.txt ; unresolved.tsv (needs a decision)"""
import csv, sys, pathlib, collections
A = pathlib.Path(__file__).parent
out = pathlib.Path(sys.argv[1])
man = {r[0]: (r[1], r[2]) for r in list(csv.reader(open(out / "file_manifest.tsv"), delimiter="\t"))[1:]}
lines = lambda n: {l.strip() for l in open(A / n) if l.strip() and not l.startswith("#")}
tests_move_set, docs_move_set, slurm_move_set = lines("tests_move_set.txt"), lines("docs_move_set.txt"), lines("slurm_move_set.txt")
# triage classes for docs/plans etc (main-0 triage is the latest)
tri = {r[0]: r[3] for r in list(csv.reader(open(A / "main-0/triage.tsv"), delimiter="\t"))[1:] if r[2] == "" and r[0].startswith("docs/")}

REPRO_SCRIPTS = "adjudicate_candidates validate_protocol_lock check_g3_diff explore_ledger longitudinal_compile super_expressors combine_palmdb_reference cal13_decoys subset_fastq_pair audit_fastq_pair check_tracked_file_sizes validate_v3_protocol gen_workflow_comparison ref13_normaliser_qc generate_truth_panel v3_score v3_partition v3_lod val08_golden plant_anello_10x".split()
PKG_SCRIPTS = "make_panel_archive prepare_viral_proteins compare_reference_reproducibility".split()
TEST_OF_REPRO = [f"test_{s}" for s in REPRO_SCRIPTS if s not in ("check_g3_diff", "validate_v3_protocol", "ref13_normaliser_qc", "generate_truth_panel", "v3_score", "v3_partition", "v3_lod", "val08_golden", "plant_anello_10x")] + ["test_tracked_file_sizes"]
D46_TEST_PREFIXES = ("test_generate_truth_panel", "test_v3_scorer", "test_v3_lod", "test_v3_partition", "test_val08_golden", "test_val_generator_audit", "test_plant_anello_tails", "test_truth_panel_exact")
D37_TESTS = "test_dsr_host_shutoff_diagnostic test_dsr_round2b_sens07 test_dsr_round_compare test_dsr_round_env test_protocol_code_honouring test_protocol_lock test_sci05_round13_code test_sci05_round14_code test_sci05_round15_code test_validation_protocol_round12 test_validation_protocol_round13".split()
FORCE = {  # explicit path overrides (decision in comment)
    "config/large_file_allowlist.txt": "repro",            # D29
    "ENVIRONMENTS_INSTALLATIONS.md": "delete",              # D29, only with user approval at 4d
    "environment.tools.lock.txt": "package", "MAINTAINER_CHECKLIST.md": "package", "pixi.toml": "package",
    "Singularity.pixi.def": "package", "environment.coverage.yml": "package", "environment.discovery.yml": "package",  # D29
    "tests/test_compare_reference_reproducibility.py": "package",  # D31
    "tests/test_confirm_hits.py": "repro", "tests/test_spikein_aggregate.py": "repro", "tests/test_spikein_detection_limit.py": "repro",
    "tests/test_spikein_grid.py": "repro", "tests/test_spikein_posthoc.py": "repro", "tests/test_translated_search_tools.py": "repro",  # load code from moved analysis/ dirs (found by 4a collect-only)
    "schemas/v3/protocol_lock.schema.json": "repro",              # only exists at top level (not in src/viralscan/schemas); used by validate_protocol_lock
    "config/dsr_round2b_sens07.template.tsv": "repro", "config/dsr_round2c_sens07.template.tsv": "repro", "config/track_b_denylist.txt": "repro",
    "tests/_truth_panel_real.py": "repro",                        # helper used only by moved truth-panel tests
    "tests/_fastq.py": "both", "tests/_exact_control.py": "both", "tests/__init__.py": "both",   # helpers shared with staying tests: copy, do not move
    "tests/test_count_library.py": "repro",                        # imports analysis/translated_search/count_library.py
    "tests/data/adjudication_lock_TEST_ONLY.json": "repro",         # fixture of test_adjudicate_candidates/test_protocol_lock
}
res = {}; why = {}
for p, (c, r) in man.items():
    cls, why_ = c, r
    name = pathlib.PurePosixPath(p).name; stem = pathlib.PurePosixPath(p).stem
    if p.startswith("scripts/") and stem in REPRO_SCRIPTS: cls, why_ = "repro", "D29/D30 script"
    if p.startswith("scripts/") and stem in PKG_SCRIPTS: cls, why_ = "package", "D29/D31 script"
    if p.startswith("scripts/slurm_") and p in slurm_move_set: cls, why_ = "repro", "slurm_move_set"
    if p in tests_move_set: cls, why_ = "repro", "tests_move_set"
    if p.startswith("tests/") and stem in TEST_OF_REPRO: cls, why_ = "repro", "test of a moved script"
    if p.startswith("tests/") and stem.startswith(D46_TEST_PREFIXES): cls, why_ = "repro", "D46"
    if p.startswith("tests/") and stem in D37_TESTS: cls, why_ = "repro", "D37"
    if p.startswith("docs/figures/"): cls, why_ = "repro", "D40"
    if p.startswith("docs/") and p in docs_move_set and p not in tri: cls, why_ = "repro", "docs_move_set"
    if p in tri and p.startswith("docs/plans/"):
        cls, why_ = {"experiment": "repro", "both": "both", "package": "package"}.get(tri[p], cls), "triage (D14)"
    if p.startswith("skillpacks/"): cls, why_ = "package", "D38"
    if p in FORCE: cls, why_ = FORCE[p], "FORCE"
    if cls == "REVIEW": cls, why_ = "package", "REVIEW default: audited false positive (run-output results/ naming) - stays"
    if p.startswith(".living/") or p == "PLAN.md": cls, why_ = "both", "D13/D15"
    res[p] = cls; why[p] = why_
by = collections.defaultdict(list)
for p, c in res.items(): by[c].append(p)
for c, name in (("repro", "moved_paths.txt"), ("both", "both_paths.txt"), ("delete", "delete_paths.txt"), ("package", "stay_paths.txt")):
    (out / name).write_text("\n".join(sorted(by[c])) + "\n")
unres = [(p, c, why[p]) for p, c in res.items() if c in ("REVIEW", "UNCLASSIFIED", "TRIAGE")]
csv.writer(open(out / "unresolved.tsv", "w", newline=""), delimiter="\t").writerows([("path", "class", "why")] + sorted(unres))
print({c: len(v) for c, v in by.items()})
print("unresolved:", len(unres)); [print("  ", u[0], u[1]) for u in sorted(unres)[:40]]
