#!/usr/bin/env python3
"""Step 3B: add the repro-only files on top of the filtered history (scratch; nothing pushed). Run after build_repro_A.py."""
import csv, pathlib, re, shutil, subprocess, sys
SPLIT = pathlib.Path("/exports/para-lipg-hpc/mdmanurung/viralscan-split"); W = SPLIT / "work/repro"
REPO = "/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan"
BASE = (W / ".git/BASE_SHA").read_text().strip()
git = lambda *a, cwd=W: subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout
show = lambda rev, p: subprocess.run(["git", "-C", REPO, "show", f"{rev}:{p}"], capture_output=True, check=True).stdout
def put(rel, data):
    p = W / rel; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data if isinstance(data, bytes) else data.encode())

# --- provenance
put("provenance/package_commit_map.tsv", (SPLIT / "work/package_commit_map.tsv").read_bytes())
put("provenance/PACKAGE_BASE_SHA", BASE + "\n")
put("provenance/repro-paths.txt", (SPLIT / "work/repro-paths.txt").read_bytes())
for f in pathlib.Path(REPO, "migration_plan").glob("*.md"): put(f"provenance/migration_plan_2026-10-02/{f.name}", f.read_bytes())

# --- carry: experiment leftovers that only exist on the local branch codex/drop-py39 (eebcaeb), added files only
added = subprocess.run(["git", "-C", REPO, "diff", "--name-status", BASE, "eebcaeb"], capture_output=True, text=True, check=True).stdout.splitlines()
carry = [l.split("\t", 1)[1] for l in added if l.startswith("A\t")]
for p in carry: put(p, show("eebcaeb", p))
WORKTREE_CARRY = ["analysis/trackA_host_programs/config.json"]   # small untracked inputs that moved tests read
for p in WORKTREE_CARRY:
    if pathlib.Path(REPO, p).exists(): put(p, pathlib.Path(REPO, p).read_bytes())
for f in sorted(pathlib.Path(REPO).glob("HANDOFF*.md")) + [pathlib.Path(REPO, "SESSION_RESUME.md")]:
    if f.exists(): put(f.name, f.read_bytes())
put("provenance/carry_list.txt", "\n".join(carry) + "\n(+ root HANDOFF*.md and SESSION_RESUME.md copied from the package working tree)\n")

# --- vendored frozen copies of package files that moved scripts/tests import (see VENDORED.md)
VEND = ["scripts/governance_utils.py", "extras/build_gene_programs.py", "extras/build_virus_catalog.py"]
for p in VEND: put(p, show(BASE, p))
put("VENDORED.md", f"""# Vendored frozen copies

Copied from ViralScan at `{BASE}` so moved scripts/tests keep working. Do not edit; re-vendor when the package copy changes.

""" + "\n".join(f"- `{p}`" for p in VEND) + "\n")
put("tests/test_evidence_tiers_protocol.py", (SPLIT / "audit/batches/carry/test_evidence_tiers_protocol_parts.py").read_bytes())

# --- repo scaffolding
put("LICENSE", show(BASE, "LICENSE"))
put(".gitignore", """# run outputs and caches
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.snakemake/
.venv/
.ipynb_checkpoints/
Rplots.pdf
# local compatibility links are listed in .git/info/exclude by setup_links.sh (never committed)
# large run outputs stay on disk and are linked from links/
analysis/*/outputs/
analysis/*/work/
analysis/*/.runtime/
analysis/translated_search/config.local.yaml
""")
put("CITATION.cff", """cff-version: 1.2.0
message: "If you use these analyses, please cite the ViralScan package and this repository."
title: "ViralScan-reproducibility"
type: software
authors:
  - family-names: Manurung
    given-names: Mikhael D.
repository-code: "https://github.com/mdmanurung/ViralScan-reproducibility"
license: MIT
""")
put("env.sh", """# source this from the repo root: points experiments at the package checkout (VIRALSCAN_PKG) pinned in provenance/PACKAGE_BASE_SHA
export VIRALSCAN_PKG="${VIRALSCAN_PKG:-/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan}"
export PYTHONPATH="$VIRALSCAN_PKG/src:$VIRALSCAN_PKG:${PYTHONPATH:-}"
""")
put("setup_links.sh", """#!/usr/bin/env bash
# Create the local, never-committed links that let moved scripts/tests find package files (they were written for one combined repo).
# Links are per entry (docs/, schemas/, config/ exist in both repos) and are recorded in .git/info/exclude, never in .gitignore.
set -euo pipefail
cd "$(dirname "$0")"
: "${VIRALSCAN_PKG:=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan}"
made=()
link() { # link <target> <path-in-repro>; skips a path that already exists as a real file/dir
  if [ -e "$2" ] && [ ! -L "$2" ]; then return 0; fi
  mkdir -p "$(dirname "$2")"; ln -sfn "$1" "$2"; made+=("/$2")
}
link "$VIRALSCAN_PKG/src" src
link "$VIRALSCAN_PKG/.github" .github
for f in "$VIRALSCAN_PKG"/docs/*; do link "$f" "docs/$(basename "$f")"; done
for f in "$VIRALSCAN_PKG"/src/viralscan/schemas/v3/*; do link "$f" "schemas/v3/$(basename "$f")"; done
link "$VIRALSCAN_PKG/config/public_ship_scope.json" config/public_ship_scope.json
[ -d "$VIRALSCAN_PKG/extras/vendor_sources" ] && link "$VIRALSCAN_PKG/extras/vendor_sources" extras/vendor_sources
# analysis/panel_expansion moved into the package (curation/panel after the split)
if [ -d "$VIRALSCAN_PKG/curation/panel" ]; then link "$VIRALSCAN_PKG/curation/panel" analysis/panel_expansion
elif [ -d "$VIRALSCAN_PKG/analysis/panel_expansion" ]; then link "$VIRALSCAN_PKG/analysis/panel_expansion" analysis/panel_expansion; fi
mkdir -p links
for d in benchmark_runs references starsolo_p22_6 starsolo_p22_6b ebv_latest_ref_2026-09-27 viral_panel_max_2026-09-28 cost01 logs sources; do
  [ -e "$VIRALSCAN_PKG/$d" ] && link "$VIRALSCAN_PKG/$d" "links/$d"
done
# old package commit ids recorded in ledgers/tests must resolve here: borrow the package object store (local only)
if [ -d "$VIRALSCAN_PKG/.git/objects" ]; then
  mkdir -p .git/objects/info; grep -qxF "$VIRALSCAN_PKG/.git/objects" .git/objects/info/alternates 2>/dev/null || echo "$VIRALSCAN_PKG/.git/objects" >> .git/objects/info/alternates
fi
# local-only ignore block
ex=.git/info/exclude; mkdir -p .git/info; touch "$ex"
sed -i '/^# setup_links.sh begin/,/^# setup_links.sh end/d' "$ex"
{ echo "# setup_links.sh begin"; printf '%s\\n' "/links/" "${made[@]}"; echo "# setup_links.sh end"; } >> "$ex"
echo "links ready (VIRALSCAN_PKG=$VIRALSCAN_PKG): ${#made[@]} links"
""")
(W / "setup_links.sh").chmod(0o755)
put("conftest.py", '''"""Make the pinned ViralScan package importable for pytest (set VIRALSCAN_PKG, or run `source env.sh`)."""
import os
import sys

_pkg = os.environ.get("VIRALSCAN_PKG", "/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan")
for _p in (os.path.join(_pkg, "src"), _pkg):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ["PYTHONPATH"] = os.pathsep.join([os.path.join(_pkg, "src"), _pkg, os.environ.get("PYTHONPATH", "")])  # subprocess-based tests
''')
put("environment.yml", f"""name: viralscan-repro
channels: [conda-forge, bioconda]
dependencies:
  - python=3.11
  - pytest
  - pyyaml
  - jsonschema
  - numpy
  - pandas
  - scipy
  - anndata
  - scanpy
  - matplotlib
  # The package itself: install the pinned commit, or (when pip cannot build all dependencies) use PYTHONPATH via env.sh.
  - pip
  - pip:
      - "viralscan @ git+https://github.com/mdmanurung/ViralScan@{BASE}"
""")
put("README.md", f"""# ViralScan-reproducibility

Analyses, benchmarks, validation studies and manuscript evidence for [ViralScan](https://github.com/mdmanurung/ViralScan).
The software lives in the package repo; this repo holds everything that *uses* it. It was split out of the package repo with
per-file git history (`provenance/package_commit_map.tsv` maps old package commit ids to commits here).

| Where | What |
|---|---|
| `analysis/` | one folder per analysis (see `analysis/ANALYSIS_MANIFEST.md`), incl. `v3_validation/` (protocol, deviation ledger) |
| `results/`, `covid_viralscan/`, `benchmark_inputs/` | result tables, the COVID survey, benchmark inputs |
| `claims/`, `audits/`, `docs/plans/` | claim registry, audits, plans and design notes |
| `scripts/`, `extras/`, `tests/` | SLURM jobs, study scripts, helpers and their tests |
| `.living/`, `PLAN.md`, `HANDOFF*.md` | living-repo notes, tracker (experiment sections), session handoffs |
| `provenance/` | split provenance: commit map, pinned package sha, carry list |

## Pinned package
These analyses were run against ViralScan commit `{BASE}` (see `provenance/PACKAGE_BASE_SHA`; update it when you re-pin).

```bash
export VIRALSCAN_PKG=/path/to/ViralScan      # a checkout of that commit
source env.sh                                # PYTHONPATH for the package
./setup_links.sh                             # local links (src, docs, schemas, .github, big run dirs); never committed
pytest tests -q                              # the moved tests (research-marked ones need -m research)
```
`pip install` of the package can fail on some clusters (a transitive build error); `PYTHONPATH` works.
Large run directories (hundreds of GB) are not in git; `setup_links.sh` links them under `links/` when present.

## Notes
- `VENDORED.md` lists frozen copies of package files that these scripts import.
- Cluster paths (`/exports/...`) are kept as recorded.
""")
put("CLAUDE.md", f"""# CLAUDE.md (ViralScan-reproducibility)

Experiments and evidence for ViralScan; the package is a separate repo (`VIRALSCAN_PKG`, pinned in `provenance/PACKAGE_BASE_SHA`).

- Run experiments from here with `source env.sh && ./setup_links.sh`. Do not copy package code in; vendor frozen copies only via `VENDORED.md`.
- `PLAN.md` here tracks the experiment/validation work (the package keeps its own `PLAN.md`). Update it when you finish a step.
- Never commit the links created by `setup_links.sh` or large run outputs.
- Split provenance and decisions: `provenance/`; the original split tracker is in the package repo history / `provenance/migration_plan_2026-10-02/`.
""")


# --- two-root governance (D39): artifacts owned by the package are resolved in the pinned package checkout (VIRALSCAN_PKG)
gu = (W / "scripts/governance_utils.py").read_text()
gu = gu.replace("def repository_file_error(repo_root: Path, value: str) -> str:", '''def package_fallback(repo_root: Path, value: str) -> Path:
    """Root that holds *value*: the pinned package checkout (env VIRALSCAN_PKG) when it has the file (package-owned artifacts win,
    e.g. README.md and environment.yml exist in both repos), else this repo. Two-root governance, split decision D39."""
    package = os.environ.get("VIRALSCAN_PKG")
    if package and (Path(package) / value).exists():
        return Path(package)
    return Path(repo_root)


def repository_file_error(repo_root: Path, value: str) -> str:''', 1)
gu = gu.replace("    root = repo_root.resolve()\n    candidate = root\n", "    repo_root = package_fallback(repo_root, value)\n    root = repo_root.resolve()\n    candidate = root\n", 1)
if "\nimport os\n" not in gu: gu = gu.replace("\nimport json\n", "\nimport json\nimport os\n", 1)
assert "def package_fallback" in gu and "repo_root = package_fallback" in gu
(W / "scripts/governance_utils.py").write_text(gu)
for name in ("validate_claim_registry.py", "validate_artifact_inventory.py"):
    t = (W / "scripts" / name).read_text()
    t = t.replace("        repository_file_error,\n", "        package_fallback,\n        repository_file_error,\n")
    t = re.sub(r"(\w+) = repo_root / (path_value|relative)\n", r"\1 = package_fallback(repo_root, \2) / \2\n", t)
    assert "package_fallback(repo_root," in t, name
    (W / "scripts" / name).write_text(t)
put("VENDORED.md", (W / "VENDORED.md").read_text() + "\n`scripts/governance_utils.py` is modified here: `package_fallback()` (two-root governance, split decision D39) resolves package-owned artifacts via `VIRALSCAN_PKG`; `scripts/validate_claim_registry.py` and `scripts/validate_artifact_inventory.py` use it.\n")

# --- PLAN.md: experiment + 'both' sections of the package PLAN (D13); the full text stays in the package at the pinned sha
tri = list(csv.reader(open(SPLIT / "audit/main-0/triage.tsv"), delimiter="\t"))[1:]
cls = {}
for f, where, item, c, reason in tri:
    if f == "PLAN.md" and re.match(r"^\d+-\d+$", where): cls[re.sub(r"\W+", "", item.lower())[:40]] = c
plan = show(BASE, "PLAN.md").decode().split("\n"); heads = [i for i, l in enumerate(plan) if l.startswith("## ")]
keep, dropped = [], []
for k, h in enumerate(heads):
    end = heads[k + 1] if k + 1 < len(heads) else len(plan); title = plan[h]
    c = cls.get(re.sub(r"\W+", "", title[3:].lower())[:40], "both")
    (keep if c in ("experiment", "both") or title.startswith("## Next action") else dropped).append((title, "\n".join(plan[h:end])))
hdr = f"""# Experiment and validation tracker (ViralScan-reproducibility)

Split from the package `PLAN.md` at ViralScan `{BASE}` (decision D13): this file keeps the sections classed *experiment* or *both*
plus the full *Next action* section. The complete package tracker, including {len(dropped)} package-only sections, lives in the
package repo at that commit. Section classification: package `audit/main-0/triage.tsv` (split tracker).

"""
put("PLAN.md", hdr + "\n".join(t for _, t in keep))
put("provenance/PLAN_sections_kept.txt", "\n".join(t for t, _ in keep) + "\n\n--- dropped (package-only) ---\n" + "\n".join(t for t, _ in dropped) + "\n")
git("add", "-A")
git("-c", "user.name=mdmanurung", "-c", "user.email=m.d.manurung@lumc.nl", "commit", "-q", "-m",
    f"chore: scaffold the reproducibility repo (split from ViralScan {BASE[:8]})\n\nREADME, env/links tooling, vendored frozen copies, provenance (commit map, pinned sha), trimmed PLAN.md,\nand the experiment files that only existed on the local branch (carry list in provenance/carry_list.txt).\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>")
print("carry files:", len(carry), "| PLAN sections kept", len(keep), "dropped", len(dropped), "| HEAD", git("rev-parse", "--short", "HEAD").strip(), "| tracked", len(git("ls-files").split("\n")) - 1)
