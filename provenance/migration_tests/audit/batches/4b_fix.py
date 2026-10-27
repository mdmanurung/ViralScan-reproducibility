#!/usr/bin/env python3
"""Batch 4b fixes, run in the package tree after the 4b files are removed (rehearse.sh / PR build)."""
import pathlib, re

PFX = "ViralScan-reproducibility/"
read = lambda p: pathlib.Path(p).read_text()
write = lambda p, s: pathlib.Path(p).write_text(s)

# 1. pre-commit hook for a script (and trees) that left the package
t = read(".pre-commit-config.yaml")
new = re.sub(r"\n  - repo: local\n    hooks:\n      - id: check-tracked-file-sizes\n(?:        .*\n)+", "\n", t)
assert new != t, "check-tracked-file-sizes hook not found"
write(".pre-commit-config.yaml", new.rstrip("\n") + "\n")

# 2. package text that names a moved script by repo-relative path -> point at the reproducibility repo
for path, names in {
    "curation/panel/README.md": ["panel_census", "cat28_panviral_marker_check"],
    "scripts/panel_candidates.py": ["panel_census"],
    "scripts/build_bundled_panel_ref.py": ["bulk_viral_summarize"],
    "src/viralscan/competitive_plot.py": ["dsr02_validate_call", "dsr02_verdicts"],
}.items():
    t = read(path)
    for n in names:
        t2 = re.sub(r"(?<![/\w])scripts/" + n + r"\.py", PFX + "scripts/" + n + ".py", t)
        t = t2
    write(path, t)
t = read("curation/panel/README.md")
t = t.replace("    python ViralScan-reproducibility/scripts/panel_census.py ", "    # from ViralScan-reproducibility: python scripts/panel_census.py ")
assert "# from ViralScan-reproducibility" in t
write("curation/panel/README.md", t)

# 3. PLAN.md row
t = read("PLAN.md")
old = "CLI unchanged, sdist loses 20 entries. Next: 4b (experiment scripts + tests), 4c (docs, dev files), 4d."
assert old in t
t = t.replace(old, "CLI unchanged, sdist loses 20 entries. Merged as #118. Batch 4b (this change): experiment scripts,\n  their tests, `protocol_lock.schema.json`, three `config/*.tsv` inputs and the size-cap pre-commit hook leave\n  the package. Next: 4c (docs, dev files), 4d.")
t = t.replace("Batch 4a (this change, do NOT merge before `ViralScan-reproducibility` has been built and pushed):", "Batch 4a (done):")
write("PLAN.md", t)
