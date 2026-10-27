#!/usr/bin/env python3
"""Batch 4a fixes, run INSIDE the rehearsal tree (cwd = repo root, 4a files already `git rm`'d, HEAD = base)."""
import ast, json, pathlib, re, subprocess, sys
SPLIT = pathlib.Path("/exports/para-lipg-hpc/mdmanurung/viralscan-split")
CARRY = SPLIT / "audit/batches/carry"; CARRY.mkdir(exist_ok=True)
sh = lambda *a: subprocess.run(a, check=True)
tracked = lambda: subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout.split("\n")
read = lambda p: pathlib.Path(p).read_text()
def write(p, s): pathlib.Path(p).write_text(s)

# 1. D10: analysis/panel_expansion -> curation/panel, and every path constructor / doc mention that names it
pathlib.Path("curation").mkdir(exist_ok=True)
sh("git", "mv", "analysis/panel_expansion", "curation/panel")
PAT_SLASH = re.compile(r'''(["'])analysis\1\s*/\s*(["'])panel_expansion\2''')
PAT_COMMA = re.compile(r'''(["'])analysis\1\s*,\s*(["'])panel_expansion\2''')
for f in tracked():
    if not f or f in ("PLAN.md", "CHANGELOG.md") or f.startswith((".living/", "curation/")): continue
    if not f.endswith((".py", ".md", ".sh", ".yml", ".yaml", ".toml", ".json", ".txt", ".tsv", ".ipynb", ".in", ".cff", ".rst")): continue
    try: t = read(f)
    except Exception: continue
    n = t.replace("analysis/panel_expansion", "curation/panel")
    n = PAT_SLASH.sub(r"\1curation\1 / \2panel\2", n); n = PAT_COMMA.sub(r'\1curation\1, \2panel\2', n)
    if n != t: write(f, n)

# 2. .gitignore: the generated /curation/ symlink view must not ignore the new real dir
lines = read(".gitignore").split("\n"); out = []
for i, l in enumerate(lines):
    if l.strip() == "/curation/":
        while out and out[-1].startswith("#") and "curation" in out[-1].lower(): out.pop()
        continue
    out.append(l)
write(".gitignore", "\n".join(out))

# 3. ci.yml: drop the v3 protocol draft gate and the deviation-ledger steps (both scripts move)
ci = read(".github/workflows/ci.yml").split("\n")
a = next(i for i, l in enumerate(ci) if l.startswith("      # Draft gate only."))
b = next(i for i, l in enumerate(ci) if "check_ledger_append_only.py" in l)
ci = ci[:a] + ci[b + 1:]
write(".github/workflows/ci.yml", "\n".join(ci))

# 4. MANIFEST.in and public_ship_scope.json: remove entries for files that left
moved = {l.strip() for f in ("moved_paths.txt", "delete_paths.txt") for l in open(SPLIT / "audit/main-4" / f) if l.strip()}
man = [l for l in read("MANIFEST.in").split("\n") if not (l.split(" ", 1)[0] == "include" and l.split(" ", 1)[1].strip() in moved)]
write("MANIFEST.in", "\n".join(man))
scope = read("config/public_ship_scope.json").split("\n")
sc = []
for l in scope:
    m = re.match(r'^\s*"([^"]+)",?\s*$', l)
    if m and m.group(1) in moved: continue
    sc.append(l)
text = "\n".join(sc)
text = re.sub(r",(\s*\n\s*[\]}])", r"\1", text)      # a removed last member leaves a trailing comma
json.loads(text); write("config/public_ship_scope.json", text)

# 5. tests that read the deleted top-level schemas/ or moved files
CARRY_HEADER = '''"""Repro-side: package evidence_tiers defaults against the frozen protocol (moved out of the package tests, 4a)."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from viralscan import evidence_tiers as et
from viralscan.evidence_tiers import Calibration, Cutoffs, GridPoint, TierEvidence  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "analysis" / "v3_validation" / "protocol.yaml"


@pytest.fixture(scope="module")
def protocol() -> dict:
    return yaml.safe_load(PROTOCOL.read_text())


@pytest.fixture(scope="module")
def grid(protocol) -> et.Grid:
    return et.grid_from_protocol(protocol)


'''


def rm_funcs(path, names, carry=None):
    t = read(path); tree = ast.parse(t); L = t.split("\n"); cut = []; saved = []
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name in names:
            s = min([n.lineno] + [d.lineno for d in n.decorator_list]) - 1
            e = n.end_lineno
            while e < len(L) and L[e].strip() == "": e += 1
            cut.append((s, e)); saved.append("\n".join(L[s:n.end_lineno]))
    assert len(cut) == len(names), (path, names, len(cut))
    for s, e in sorted(cut, reverse=True): del L[s:e]
    write(path, "\n".join(L))
    if carry: (CARRY / carry).write_text(CARRY_HEADER + "\n\n".join(saved) + "\n")
rm_funcs("tests/test_bus_correction_audit.py", {"test_schema_copies_identical"})
rm_funcs("tests/test_validation.py", {"test_packaged_v3_schemas_match_public_contracts"})
rm_funcs("tests/test_positive_control_receipt.py", {"test_shipped_schema_copies_are_identical"})
for _p in ("tests/test_bus_correction_audit.py", "tests/test_positive_control_receipt.py"): write(_p, read(_p).rstrip("\n") + "\n")
t = read("tests/test_multimapping_counting_contract.py"); assert '("schemas/v3", "src/viralscan/schemas/v3")' in t
write("tests/test_multimapping_counting_contract.py", t.replace('("schemas/v3", "src/viralscan/schemas/v3")', '("src/viralscan/schemas/v3",)'))
t = read("tests/test_docs_consistency.py"); assert ' + [Path("BENCHMARK_COMPARISON.md")]' in t
write("tests/test_docs_consistency.py", t.replace(' + [Path("BENCHMARK_COMPARISON.md")]', ""))
# test_evidence_tiers: 2 of 29 tests compare package defaults with the frozen protocol -> repro (carry file)
tp = "tests/test_evidence_tiers.py"
rm_funcs(tp, {"test_grid_parser_refuses_anything_but_the_three_declared_sets", "test_the_grid_follows_the_protocol_text_not_a_constant"}, carry="test_evidence_tiers_protocol_parts.py")
t = read(tp)
t = re.sub(r'\nPROTOCOL = ROOT / "analysis" / "v3_validation" / "protocol.yaml"\n', "\n", t)
t = re.sub(r'@pytest\.fixture\(scope="module"\)\ndef protocol\(\) -> dict:\n    return yaml\.safe_load\(PROTOCOL\.read_text\(\)\)\n+', "", t)
if "yaml." not in t: t = t.replace("import yaml\n", "", 1)
if "ROOT" not in t.replace("ROOT = Path(__file__).resolve().parents[1]", ""): t = t.replace("ROOT = Path(__file__).resolve().parents[1]\n", "", 1)
t = t.replace("def grid(protocol) -> et.Grid:\n    return et.grid_from_protocol(protocol)", "def grid() -> et.Grid:\n    # the frozen 45-point grid (calibration.threshold_search.grid); consistency with the protocol is tested in the reproducibility repo\n    return et.Grid((1, 2, 3, 5, 10), (1, 2, 3), (0.5, 0.75, 0.9))")
assert "def grid() -> et.Grid" in t
write(tp, t)
subprocess.run(["/exports/archive/hg-funcgenom-research/mdmanurung/conda/envs/viralscan_test_full/bin/ruff", "check", "--fix", "--select", "F401,I001", tp], check=True)

# 6. D41: citations of audits/ now point at the reproducibility repo
URL = "https://github.com/mdmanurung/ViralScan-reproducibility/blob/main/audits/2026-05-08-full-pipeline.md"
for f in tracked():
    if not f.startswith(("src/", "tests/", "docs/", "scripts/", "extras/")) or not f.endswith((".py", ".md", ".sh")): continue
    try: t = read(f)
    except Exception: continue
    if "audits/2026-05-08-full-pipeline.md" in t and URL not in t:
        write(f, t.replace("audits/2026-05-08-full-pipeline.md", URL))
print("4a fixes applied")
