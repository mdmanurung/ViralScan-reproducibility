#!/usr/bin/env python3
"""Step 3A: history-preserving extraction into work/repro (scratch; nothing pushed).
usage: build_repro_A.py <audit/main-N dir with moved_paths.txt, both_paths.txt> [ref=origin/main]"""
import pathlib, re, subprocess, sys, shutil, os
SPLIT = pathlib.Path("/exports/para-lipg-hpc/mdmanurung/viralscan-split")
REPO = "/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan"
FR = "/home/mdmanurung/.local/bin/git-filter-repo"
man = pathlib.Path(sys.argv[1]); ref = sys.argv[2] if len(sys.argv) > 2 else "origin/main"
W = SPLIT / "work/repro"; shutil.rmtree(W, ignore_errors=True); W.mkdir(parents=True)
run = lambda *a, **k: subprocess.run(a, cwd=W, check=True, capture_output=True, text=True, **k).stdout
run("git", "init", "-q", ".")
sha = subprocess.run(["git", "-C", REPO, "rev-parse", ref], capture_output=True, text=True, check=True).stdout.strip()
run("git", "fetch", "-q", REPO, f"{sha}:refs/heads/main"); run("git", "checkout", "-q", "main")
(W / ".git/BASE_SHA").write_text(sha + "\n")
moved = [l.strip() for l in open(man / "moved_paths.txt") if l.strip()]
both = [l.strip() for l in open(man / "both_paths.txt") if l.strip()]
hist = set(p for p in run("git", "log", "--name-only", "--pretty=format:").split("\n") if p)
GENERIC = {"README.md", "__init__.py", ".gitignore", "conftest.py", "LICENSE", "index.md"}
base = {pathlib.PurePosixPath(p).name for p in moved + both} - GENERIC
TREES = ("analysis/", "results/", "covid_viralscan/", "benchmark_inputs/", "claims/", "audits/", "todo/", "data/", "ref/", "docs/figures/")
SCRIPT_REPRO_PAT = re.compile(r"^(slurm_|dsr|legacy|freeze_|fresh|run_fresh|revalidate|prepare_(fresh|legacy|reference)|summarize_|compare_(legacy|starsolo)|audit_reference|anello_|sens07|cost01|make_manuscript|publication_checklist|bulk_viral|validate_|check_ledger|hostresponse_ebv|ref06|ref07_(level|recovery)|ref13|panel_census|measure_kmer|dlist_kmer|check_reads|matched_barcode|package_starsolo|fetch_reference|benchmark_v3|build_genome_panel|ttv_public)")
extra, why = set(), {}
for p in hist:
    if p.startswith(TREES): continue
    name = pathlib.PurePosixPath(p).name
    if p.startswith(("scripts/", "tests/", "extras/", "config/")) and name in base and p not in moved + both:
        extra.add(p); why[p] = "basename of a moved file (renamed/relocated)"
    elif p.startswith("scripts/") and SCRIPT_REPRO_PAT.match(pathlib.PurePosixPath(p).stem) and not (W / p).exists():
        extra.add(p); why[p] = "deleted historical experiment script"
paths = sorted(set(moved) | set(both) | extra | set(TREES))
(W.parent / "repro-paths.txt").write_text("\n".join(paths) + "\n")
print("base", sha[:8], "| history paths", len(hist), "| moved", len(moved), "| both", len(both), "| extra historical", len(extra), "| total path entries", len(paths))
(W.parent / "repro-extra-historical.txt").write_text("\n".join(f"{p}\t{why[p]}" for p in sorted(extra)) + "\n")
# pass 1: include
subprocess.run(["git", "filter-repo", "--force", "--paths-from-file", str(W.parent / "repro-paths.txt")], cwd=W, check=True, capture_output=True)
# pass 2: panel_expansion stays in the package (D10)
subprocess.run(["git", "filter-repo", "--force", "--path", "analysis/panel_expansion", "--invert-paths"], cwd=W, check=True, capture_output=True)
# filter-repo merges the commit-map across successive runs: this file already maps ORIGINAL package sha -> FINAL repro sha
cm = {l.split()[0]: l.split()[1] for l in (W / ".git/filter-repo/commit-map").read_text().splitlines()[1:]}
z = "0" * 40
out = ["old_package_sha\tnew_repro_sha"] + [f"{o}\t{n}" for o, n in cm.items()]
(W.parent / "package_commit_map.tsv").write_text("\n".join(out) + "\n")
n = len([o for o in out[1:] if o.split("\t")[1] != z])
print("commits kept:", run("git", "rev-list", "--count", "HEAD").strip(), "| commit-map rows with a mapped sha:", n, "of", len(out) - 1)
print("tracked files:", len(run("git", "ls-files").split("\n")) - 1)
