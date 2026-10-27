#!/usr/bin/env python3
"""Batch 4c fixes, run in the package tree after the 4c files are removed."""
import pathlib, re

REPO = "https://github.com/mdmanurung/ViralScan-reproducibility"
read = lambda p: pathlib.Path(p).read_text()
write = lambda p, s: pathlib.Path(p).write_text(s)

def sub1(path, old, new):
    t = read(path); assert old in t, (path, old); write(path, t.replace(old, new, 1))

# 1. exclusions for docs that left
for line in ("write-docs-prompt.md", "showcase_runbook.md", "review-clear-execute-plan.md", "review-clear-execute-tasks.md"):
    t = read("MANIFEST.in"); new = t.replace(f"exclude docs/{line}\n", ""); assert new != t, line; write("MANIFEST.in", new)
for entry in ('    "write-docs-prompt.md",\n', '    "showcase_runbook.md",\n', '    "notices/CAT-30_retraction_DRAFT.md",  # draft notice, not published (DEF-07)\n'):
    sub1("docs/conf.py", entry, "")

# 2. PLAN.md: experiment-only sections now live in the reproducibility repo's PLAN.md (D13)
plan = read("PLAN.md").split("\n")
heads = [i for i, l in enumerate(plan) if l.startswith("## ")]
MOVED = ("## WP0 ", "## WP3 ", "## WP7 ", "## WP9 ", "## Evidence log", "## VR pilot")
out, k = [], 0
for n, h in enumerate(heads):
    pass
i = 0
while i < len(plan):
    l = plan[i]
    if l.startswith(MOVED):
        out += [l, "", f"Moved to `PLAN.md` in [ViralScan-reproducibility]({REPO}) (REPO-SPLIT-01, batch 4c); this package tracker keeps package work only.", ""]
        i += 1
        while i < len(plan) and not plan[i].startswith("## "): i += 1
        k += 1
        continue
    out.append(l); i += 1
assert k == 6, k
write("PLAN.md", "\n".join(out))
sub1("PLAN.md", "Next: 4c (docs, dev files), 4d.", "Batch 4c (this change): 24 docs (experiment plans, handoff drafts, figures, review prompts) and the six\n  experiment-only sections of this file (WP0, WP3, WP7, WP9, Evidence log, VR pilot) move to the\n  reproducibility repo. Next: 4d (root clutter, doc relinks).")

# 3. CLAUDE.md and README point at the sibling repo
sub1("CLAUDE.md", "`scripts/audit_fastq_pair.py`, fresh-control input QC", "`audit_fastq_pair.py` (in ViralScan-reproducibility), fresh-control input QC")
sub1("CLAUDE.md", "## The PLAN.md contract", f"""## Sibling repository

Experiments, validation runs, results, claims/governance ledgers, manuscript drafts and handoffs live in
[ViralScan-reproducibility]({REPO}) (split from this repo, see PLAN `REPO-SPLIT-01`). This repo keeps the package,
its tests, docs, packaging and the panel curation inputs (`curation/panel/`). Experiment `PLAN.md` sections (WP0,
WP3, WP7, WP9, Evidence log, VR pilot) are tracked there. Locally the two checkouts may be linked by uncommitted
symlinks; never commit them.

## The PLAN.md contract""")
sub1("README.md", "## Citation\n", f"## Reproducibility\n\nValidation experiments, benchmarks and manuscript analyses live in [ViralScan-reproducibility]({REPO}).\n\n---\n\n## Citation\n")
