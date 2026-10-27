#!/usr/bin/env python3
"""Classify every tracked file per SPLIT_TRACKER.md §5 and cross-check references. Read-only."""
import re, subprocess, sys, collections, pathlib, csv, os
REF = os.environ.get("REF", "")   # git ref to classify; empty = working-tree HEAD files

REPO = "/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan"
OUT = pathlib.Path(os.environ.get("OUTDIR", pathlib.Path(__file__).parent))
files = subprocess.run(["git", "-C", REPO] + (["ls-tree", "-r", "--name-only", REF] if REF else ["ls-files"]), capture_output=True, text=True, check=True).stdout.splitlines()

SCRIPT_KEEP = set("""check_actions_pinned check_versions check_data_governance check_dist_size check_release_ci check_ship_scope
release_package_smoke release_sif_definition governance_utils write_explicit_lock audit_locks gen_cli_reference
build_bundled_panel_ref panel_integrity panel_promote panel_pool panel_candidates panel_kmer_sharing write_gtf_manifest
fix_thin_gtfs model_hpv_cds_gtfs model_nocds_gtfs apply_repeat_gene_merges ref07_host_homology_table swap_check
prepare_viral_proteins generate_truth_panel v3_score v3_partition v3_lod val08_golden plant_anello_10x""".split())
SCRIPT_DELETE = {"build_curation_view", "curation_manifest"}
SCRIPT_REPRO_PAT = re.compile(r"^(slurm_|dsr|legacy|freeze_|fresh|run_fresh|revalidate|prepare_(fresh|legacy|reference)|summarize_|compare_|"
    r"audit_(fastq|reference)|anello_|sens07|cost01|make_manuscript|publication_checklist|bulk_viral|gen_workflow|validate_|check_ledger|"
    r"hostresponse_ebv|ref06|ref07_(level|recovery)|ref13|panel_census|measure_kmer|dlist_kmer|check_reads|matched_barcode|"
    r"package_starsolo|fetch_reference|benchmark_v3|build_genome_panel|ttv_public|apply_|fix_|v3_|val08|swap|panel_)")

def cls_script(name):
    stem = pathlib.PurePosixPath(name).stem
    if name.startswith("git-hooks/"): return "package", "CI hook"
    if stem in SCRIPT_KEEP: return "package", "scripts keep-list"
    if stem in SCRIPT_DELETE: return "delete", "navigation view of mixed repo"
    if SCRIPT_REPRO_PAT.match(stem) or name.endswith(".sh") or name.endswith(".json"): return "repro", "experiment script pattern"
    return "UNCLASSIFIED", "scripts/ not in keep-list or repro pattern"

PKG_TOP = {"src","tests","docs",".github","conda-recipe","pyproject.toml","README.md","LICENSE","CHANGELOG.md","CITATION.cff",
 "CONTRIBUTING.md","CODE_OF_CONDUCT.md","SECURITY.md","SUPPORT.md","CONTEXT.md","environment.yml","environment.explicit.txt",
 "uv.lock","MANIFEST.in","Dockerfile","Singularity.def",".readthedocs.yaml",".gitignore",".dockerignore",".pre-commit-config.yaml","CLAUDE.md"}
REPRO_TOP = {"results","covid_viralscan","benchmark_inputs","claims","audits","todo","data","ref","reference_manifest.json",
 "reference_audit.tsv","BENCHMARK_COMPARISON.md","PROGRESS.md","skillpacks"}
EXTRAS_REPRO = {"cat09_human_host_sweep.py","cat28_panviral_marker_check.py"}

# test -> destination by what it references
repro_script_stems = set()
for f in files:
    if f.startswith("scripts/"):
        c, _ = cls_script(f[len("scripts/"):])
        if c == "repro": repro_script_stems.add(pathlib.PurePosixPath(f).stem)
MOVED_PATH_RE = re.compile(r"\b(analysis/(?!panel_expansion)|claims/|results/(?!.*tmp)|covid_viralscan|benchmark_inputs|PLAN\.md|\.living/|docs/plans/|migration_plan)")

def read(f):
    try:
        if REF:
            return subprocess.run(["git", "-C", REPO, "show", f"{REF}:{f}"], capture_output=True, errors="ignore", text=True).stdout
        return (pathlib.Path(REPO) / f).read_text(errors="ignore")
    except Exception: return ""

def cls_test(f):
    t = read(f)
    hits = sorted(s for s in repro_script_stems if re.search(r"\b" + re.escape(s) + r"\b", t))
    if hits: return "repro", "tests moved script(s): " + ",".join(hits[:4])
    m = MOVED_PATH_RE.findall(t)
    if m: return "REVIEW", "refs moved path(s): " + ",".join(sorted(set(m))[:4])
    return "package", "no moved refs"

rows = []
for f in files:
    top = f.split("/")[0]
    if top == "analysis":
        c, r = ("package", "D10 -> curation/panel/") if f.startswith("analysis/panel_expansion/") else ("repro", "analysis/")
    elif top == "scripts": c, r = cls_script(f[len("scripts/"):])
    elif top == "extras": c, r = ("repro", "extras cat09/cat28") if pathlib.PurePosixPath(f).name in EXTRAS_REPRO else ("package", "builds src/viralscan/data")
    elif top == "tests": c, r = cls_test(f) if f.endswith(".py") else ("REVIEW", "test data/non-py")
    elif top == "schemas": c, r = "delete", "duplicate of src/viralscan/schemas/v3"
    elif top == "config": c, r = "package", "public_ship_scope.json"
    elif top == ".living": c, r = "TRIAGE", "step 2 triage"
    elif f == "PLAN.md": c, r = "TRIAGE", "step 2 triage (split by rows)"
    elif f.startswith("docs/plans/"): c, r = "repro", "docs/plans"
    elif top == "docs": c, r = "package", "public docs (check refs)"
    elif top in REPRO_TOP: c, r = "repro", f"top-level {top}"
    elif top in PKG_TOP or f in PKG_TOP: c, r = "package", "D4 keep-list"
    else: c, r = "UNCLASSIFIED", "no rule"
    rows.append((f, c, r))

with open(OUT / "file_manifest.tsv", "w", newline="") as fh:
    w = csv.writer(fh, delimiter="\t"); w.writerow(["path", "class", "reason"]); w.writerows(rows)

cnt = collections.Counter(c for _, c, _ in rows)
print("== class counts"); [print(f"{k:14s}{v}") for k, v in cnt.most_common()]

# cross-check: files staying in package that reference moved things
moved = {f for f, c, _ in rows if c == "repro"}
moved_scripts = {pathlib.PurePosixPath(f).name for f in moved if f.startswith("scripts/")}
stay = [f for f, c, _ in rows if c == "package"]
xref = []
for f in stay:
    if f.endswith((".gz", ".ipynb", ".png", ".pdf", ".lock")) and not f.endswith(".ipynb"): continue
    t = read(f)
    hs = set(MOVED_PATH_RE.findall(t))
    hs |= {s for s in moved_scripts if re.search(r"scripts/" + re.escape(s), t)}
    if hs: xref.append((f, sorted(hs)))
with open(OUT / "stay_refs_moved.tsv", "w") as fh:
    for f, hs in xref: fh.write(f"{f}\t{'; '.join(hs)}\n")
print(f"\n== package-staying files that reference moved things: {len(xref)} (see stay_refs_moved.tsv)")
bydir = collections.Counter(f.split("/")[0] for f, _ in xref)
print(dict(bydir))

# reverse: repro files that import kept scripts/src
kept_py = {pathlib.PurePosixPath(f).stem for f, c, _ in rows if c == "package" and f.startswith("scripts/") and f.endswith(".py")}
rev = []
for f in moved:
    if not f.endswith((".py", ".sh", ".R", ".md")) : continue
    t = read(f)
    hs = sorted(s for s in kept_py if re.search(r"(from|import)\s+(scripts\.)?" + re.escape(s) + r"\b|scripts/" + re.escape(s) + r"\.py", t))
    if hs: rev.append((f, hs))
with open(OUT / "repro_refs_kept.tsv", "w") as fh:
    for f, hs in rev: fh.write(f"{f}\t{'; '.join(hs)}\n")
print(f"== repro files that import/call kept scripts: {len(rev)} (see repro_refs_kept.tsv)")
print("\n== UNCLASSIFIED / REVIEW / TRIAGE samples")
for k in ("UNCLASSIFIED", "REVIEW"):
    print(k, [f for f, c, _ in rows if c == k][:40])
