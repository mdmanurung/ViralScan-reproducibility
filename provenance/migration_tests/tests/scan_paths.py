#!/usr/bin/env python3
"""Stage 5 prep (read-only): build the old->new path map and list scripts that name an old path.
Writes audit/path_map.tsv and audit/step5_scan.tsv (file, n_hits, first hits). Edits nothing."""
import os
import re
import subprocess
import sys

import mig

L, R = mig.LAYOUT, mig.R
OUT = mig.HERE.parent / "audit"
A, S, D = R["archive"], R["scratch"], R["data"]

STAGE = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 3  # only paths whose move already happened
OUT_NAME = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--out=")), "step5")
pairs = []  # (old_prefix, new_prefix)
for m in [m for m in L["moves"] if m["stage"] <= STAGE]:
    new = os.path.join(R["repro_new"], m["new"])
    old = os.path.join(A, m["old"])
    pairs.append((old, new))
    if m["old"].startswith("ViralScan/"):  # /exports/para-lipg-hpc/mdmanurung/ViralScan is an alias of the old checkout
        pairs.append((os.path.join(S, m["old"]), new))
pairs += [(os.path.join(S, "viralscan_showcase"), os.path.join(D, "runs/viralscan_showcase")),
          (os.path.join(S, "viralscan_panel_ref"), os.path.join(D, "references/panel_builds/viralscan_panel_ref")),
          (os.path.join(S, "viralscan_panel_ref_genomic"), os.path.join(D, "references/panel_builds/viralscan_panel_ref_genomic")),
          (os.path.join(A, "ViralScan/src/viralscan/data"), os.path.join(D, "references/gtf/data"))]
# longest old prefix first so nested paths map correctly
pairs = sorted(set(pairs), key=lambda p: -len(p[0]))
OUT.mkdir(exist_ok=True)
(OUT / "path_map.tsv").write_text("old\tnew\n" + "\n".join(f"{o}\t{n}" for o, n in pairs) + "\n")
rx, _ = mig.path_regex(pairs)

SCRIPT = re.compile(r"\.(sh|sbatch|py|smk|R|r)$|(^|/)Snakefile$")
SKIP_DIR = {".snakemake", "__pycache__", ".git", "conda_pkgs:", "env_full", "env_bus", "node_modules"}
roots = [mig.resolve({"old": "viralscan_work", "new": "data/runs/work"}), os.path.join(R["repro_new"], "scripts"), os.path.join(R["repro_new"], "analysis"),
         os.path.join(R["repro_new"], "covid_viralscan"), os.path.join(R["repro_new"], "extras")]
rows = []
for root in roots:
    for dp, dns, fns in os.walk(root):
        depth = dp[len(root):].count("/")
        dns[:] = [d for d in dns if d not in SKIP_DIR and not (depth >= 5 and "outputs" in d)]
        if depth > 6:
            dns[:] = []
        for f in fns:
            if not SCRIPT.search(f):
                continue
            p = os.path.join(dp, f)
            try:
                if os.path.getsize(p) > 2_000_000:
                    continue
                txt = open(p, errors="ignore").read()
            except OSError:
                continue
            hits = sorted({m.group(1) for m in rx.finditer(txt)})
            if hits:
                rows.append((p, len(rx.findall(txt)), "; ".join(hits[:3])))
(OUT / f"{OUT_NAME}_scan.tsv").write_text("file\tn_hits\tfirst_old_paths\n" + "\n".join("\t".join(map(str, r)) for r in sorted(rows)) + "\n")
print(len(pairs), "path pairs;", len(rows), "scripts name an old path", file=sys.stderr)
