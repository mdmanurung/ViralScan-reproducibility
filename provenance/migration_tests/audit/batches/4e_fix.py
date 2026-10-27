#!/usr/bin/env python3
"""Batch 4e fixes (D61-D77), run in the package tree after the 4e.rm files are removed.
PLAN_ARCHIVE_OUT (env): where to write the verbatim PLAN archive (default: ./PLAN_archive_2026-10.md.tmp, deleted by caller)."""
import os, re, sys, pathlib, subprocess
REPO = "https://github.com/mdmanurung/ViralScan-reproducibility"
PKG = "https://github.com/mdmanurung/ViralScan"
read = lambda p: pathlib.Path(p).read_text()
write = lambda p, s: pathlib.Path(p).write_text(s)
def sub1(path, old, new):
    t = read(path); assert old in t, (path, old[:60]); write(path, t.replace(old, new, 1))
sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()

# ── 1. PLAN.md slim (D63/D67/D68) ────────────────────────────────────────────
src = read("PLAN.md").split("\n")
live_out = pathlib.Path("PLAN.md"); arch_out = pathlib.Path(os.environ.get("PLAN_ARCHIVE_OUT", "PLAN_archive_2026-10.md.tmp"))
"https://github.com/mdmanurung/ViralScan-reproducibility"
ARCH = f"{REPO}/blob/main/provenance/PLAN_archive_2026-10.md"
KEEP_FULL = ("## How to use this tracker", "## Critical path", "## Gate dashboard", "## External inputs and authority", "## Stop rules")
ROW = re.compile(r"^(\s*)- \[([ x~!])\] ")
is_open = lambda m: m.group(2) in " ~!"
def row_blocks(lines):
    """yield (kind, lines): kind in header|row|text; a row block = bullet + its deeper-indented continuation (incl. nested rows)."""
    i = 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("#"):
            yield "header", [l]; i += 1; continue
        m = ROW.match(l)
        if m:
            ind = len(m.group(1)); blk = [l]; i += 1
            while i < len(lines):
                n = lines[i]; mm = ROW.match(n)
                if n.strip() == "":
                    # blank inside a block only if the next non-blank line is still deeper
                    j = i
                    while j < len(lines) and lines[j].strip() == "": j += 1
                    if j < len(lines) and not lines[j].startswith("#") and (len(lines[j]) - len(lines[j].lstrip())) > ind:
                        blk += lines[i:j]; i = j; continue
                    break
                if n.startswith("#"): break
                if (len(n) - len(n.lstrip())) > ind or (mm and len(mm.group(1)) > ind): blk.append(n); i += 1; continue
                if not mm and (len(n) - len(n.lstrip())) >= ind + 2: blk.append(n); i += 1; continue
                break
            yield "row", blk; continue
        yield "text", [l]; i += 1
def keep_row(blk):
    """open row: whole block; done row with an open descendant: first line + the open descendants' blocks."""
    m = ROW.match(blk[0])
    if is_open(m): return blk
    sub = list(row_blocks(blk[1:]))
    kept = [b for k, b in sub if k == "row" and any(is_open(ROW.match(x)) for x in b if ROW.match(x))]
    if not kept: return None
    out = [blk[0]]
    for b in kept: out += keep_row(b) or []
    return out
live = []; section = None; sec_has_rows = {}; cur_full = False
blocks = list(row_blocks(src))
# section bookkeeping: name of current ## / ### header
for kind, blk in blocks:
    if kind == "header":
        h = blk[0]
        cur_full = h.startswith(KEEP_FULL)
        live.append(h); live.append("")
        continue
    if cur_full:
        live.append(blk[0]) if kind != "row" else live.extend(blk); continue
    if kind == "row":
        k = keep_row(blk)
        if k: live += k
        elif "CAT-31" in blk[0]: live += blk          # F8 coupling: keep the CAT-31 row verbatim
# collapse >1 blank lines; a header followed directly by another header gets a pointer line
out = []
for i, l in enumerate(live):
    if l == "" and out and out[-1] == "": continue
    out.append(l)
level = lambda l: len(l) - len(l.lstrip("#")) if l.startswith("#") else 0
final = []
i = 0
while i < len(out):
    l = out[i]
    if l.startswith("#") and level(l) >= 2:
        nxt = next((x for x in out[i+1:] if x != ""), None)
        empty = nxt is None or nxt.startswith("#")
        if empty and level(l) >= 3:            # empty sub-section: drop it (its ## parent keeps the pointer)
            i += 1
            while i < len(out) and out[i] == "": i += 1
            continue
        if empty and (nxt is None or level(nxt) <= 2):   # empty ## section: one pointer line
            final += [l, "", "No open rows; done rows are in the PLAN archive (see Next action).", ""]
            i += 1
            while i < len(out) and out[i] == "": i += 1
            continue
    final.append(l); i += 1
# second pass: a ## header left bare after its empty ### children were dropped gets the pointer too
final2 = []
for i, l in enumerate(final):
    final2.append(l)
    if l.startswith("## "):
        nxt = next((x for x in final[i+1:] if x != ""), None)
        if nxt is None or nxt.startswith("## "):
            final2 += ["", "No open rows; done rows are in the PLAN archive (see Next action).", ""]
final = final2
live_text = "\n".join(final).rstrip("\n") + "\n"
# Next action: replace the whole dated log by a short header block
na = live_text.index("## Next action")
nxt_hdr = re.search(r"^## (?!Next action)", live_text[na+1:], re.M).start() + na + 1
head = live_text[:na]
na_block = f"""## Next action

Live tracker = open rows (`[ ]`, `[~]`, `[!]`) with their section headers, the shared contract sections
(How to use, Critical path, Gate dashboard, External inputs, Stop rules) and `CAT-31`. Every done row and the
dated "Next action" log up to {sha[:7]} are frozen in the reproducibility repo:
[`provenance/PLAN_archive_2026-10.md`]({ARCH}) (REPO-SPLIT-01 batch 4e, D63/D67/D68).

"""
# keep the open rows that were under Next action (already selected above)
na_rows = live_text[na:nxt_hdr].split("\n", 2)[2] if "\n" in live_text[na:nxt_hdr] else ""
na_rows = "\n".join(l for l in na_rows.split("\n") if not l.startswith("No open rows."))
live_text = head + na_block + na_rows.strip("\n") + ("\n\n" if na_rows.strip() else "") + live_text[nxt_hdr:]
live_out.write_text(live_text)
arch_out.write_text(f"# PLAN archive (frozen 2026-10-27)\n\nVerbatim copy of the package `PLAN.md` at ViralScan `{sha}` before batch 4e slimmed it (REPO-SPLIT-01, D63/D68). Frozen: the live tracker is `PLAN.md` in the package repo.\n\n---\n\n" + "\n".join(src))
# invariants
src_rows = [l for l in src if ROW.match(l)]
open_rows = [l for l in src_rows if is_open(ROW.match(l))]
live_set = set(live_text.split("\n")); arch_set = set(("\n".join(src)).split("\n"))
miss_open = [l for l in open_rows if l not in live_set]
miss_any = [l for l in src_rows if l not in live_set and l not in arch_set]
print(f"src rows {len(src_rows)} open {len(open_rows)} | live lines {len(live_text.splitlines())} (from {len(src)}) | open rows missing in live {len(miss_open)} | rows missing everywhere {len(miss_any)} | CAT-31 {'catalogued_not_indexed.tsv' in live_text}")
for l in miss_open[:10]: print("  MISSING", l[:100])

# 4e row (added after the slim so it survives it)
sub1("PLAN.md", "(REPO-SPLIT-01 batch 4e, D63/D67/D68).\n\n", """(REPO-SPLIT-01 batch 4e, D63/D67/D68).

- [x] `REPO-SPLIT-4E` (2026-10-27, batch 4e of REPO-SPLIT-01, tracker §18 D61-D77): the package tree keeps package work only.
  Removed here after a byte compare with the reproducibility repo (D65): `.living/findings` (31), `.living/log` (92),
  `.living/HANDOFF_*`, `last-session.md`, `outputs/reviews` (11), 12 `docs/plans` (the 4 cited plans stay), `docs/handoffs`,
  `docs/superpowers`, `PUBLICATION_READINESS_EXECUTION.md`, `skillpacks`, `.github/prompts`. `.living/decisions.md` and
  `learnings.md` keep package and shared entries (experiment entries live in the repro copy). This file keeps open rows,
  section headers, the shared sections and `CAT-31`; the full pre-4e file is frozen at
  `provenance/PLAN_archive_2026-10.md` in the repro. Rehearsed with `audit/rehearse.sh 4e` (0 vanished / 0 regressed).

""")

# ── 2. decisions / learnings: drop experiment-class entries (D64; triage.tsv classes; D69 keeps "both") ──
REMOVE_DEC = ["[2026-07-06] HHV-6B reference-strategy benchmark included in manuscript (the one clean aligner row)", "[2026-07-06] F-005 CLOSED — TTV ~90% is host-homology artifact; do not cite in manuscript", "[2026-07-02] Follow-up battery: GO program found; MT-ND4L was a mito artifact; convention added", "[2026-07-02] Reference-strategy Selectivity Index blocked — benchmark is only 4/12 complete", "[2026-07-02] Intermediate-attractor hypothesis not supported — host state is a continuum", "[2026-07-01] CPM cross-check + gene characterization corroborate a real, coherent EBV signal", "[2026-07-01] Depth-matched re-analysis resolves the EBV signal to a real AUC ~0.72", "[2026-07-01] Depth-confounder check overturns the EBV headline; revised report + F-001 to \"contradicted\"", "[2026-07-01] Ideation session: 4 lenses converge on the specificity gap as a real cell state", "[2026-07-01] Fixed HVG feature-selection leakage; corrected metrics went UP, not down", "[2026-07-01] Comprehensive report built; scitexlintr unavailable, review consolidated", "[2026-07-01] Add MCC by extending the analysis code and re-running (not hand-computing)", "[2026-07-01] Register (not re-run) the EBV host-response analysis; waive scilintr FPs", "[2026-07-01] Register reference set in place rather than moving into data/raw/", "[2026-07-06] hostresponse close-out: depth-adj AUC reports panel+depth, not panel-alone", "[2026-07-06] TTV (~90% anellovirus prevalence) held out of manuscript pending read-origin test", "[2026-07-06] Read-origin test decoupled from STARsolo re-run via pre-built combined index", "[2026-07-15] EVE analysis design: 4-phase approach for anellovirus host-homology characterisation", "[2026-07-15] SLURM partition: use `all` for multi-CPU jobs to avoid `medium` QOS restriction", "[2026-07-15] T5 reproducibility fix: commit script, do not overwrite existing results", "[2026-07-15] T6 EBV B-cell enrichment — negative result logged", "[2026-07-17] EVE analysis conclusion — close all anellovirus as artifact, surviving non-EVE signal below threshold", "2026-07-26 — GOV-06 deferred to SCI-03; protocol amended with a disclosed highmem tier", "2026-07-27 — SCI-03 design freeze: partition, calibration, and uncertainty choices", "2026-07-27 — SCI-04: freeze the row set, not the pin values", "2026-07-27 — Reverted the SCI-03 and SCI-04 freezes after independent review", "2026-07-27 — Two rails: reject the reviewer's fix for one, reject git for the other", "2026-07-27 — \"Better than the original\" needs ground truth, and the benchmark forgot the original", "2026-07-27 — Frozen-input identity is re-derived at the point of use, not at freeze time only", "2026-09-27 — SFL tonsil: correction, and screening from the cellranger BAM", "2026-10-22 Spike-in grid aggregation rules (SPIKE-02 / I3)"]
REMOVE_LEA = ["[2026-07-06] cDNA-only host reference causes false-positive viral signal from GRCh38 non-coding reads", "[2026-07-06] samtools view exits 1 on duplicate BAM header entry (NC_002076.2)", "[2026-07-06] covid_viralscan/results/ is gitignored — SURVEY_SUMMARY.md not tracked", "[2026-07-06] summarize_survey.py --cellranger-outs skipped: script expects one barcode set for all samples", "[2026-07-02] Controlling for a composite covariate that CONTAINS the tested feature is circular", "[2026-07-02] Mitochondrial genes need a %mito control before claiming them as biology", "[2026-07-01] Raw-count positivity thresholds silently confound with sequencing depth", "[2026-07-01] Feature selection (HVG) before the CV split leaks into held-out metrics", "[2026-07-06] Synthetic depth-proxy test: \"fragile\" is too strict; use \"not robust\"", "[2026-09-27] A self-vs-self positive control cannot catch a strand bug in a k-mer metric", "[2026-09-27] Dereplication thresholds silently set the sensitivity ceiling of a k-mer reference", "[2026-09-30] ENA serves only R2 for many 10x runs on SRA — barcodes missing", "[2026-10-03] Appending R to PATH loses to a conda env that ships its own Rscript", "[2026-10-03] STARsolo discards homopolymer UMIs, and the read then has no barcode at all", "[2026-10-03] A pipeline's own `cdna.fa` is host+viral, so it cannot seed a negative control", "[2026-10-04] NM = 0 without the aligned fraction is not evidence", "[2026-10-04] A 3'-biased chemistry makes the artefact and the real signal look identical", "[2026-10-04] SAM stores SEQ reverse-complemented, which inverts every read-side measure", "[2026-10-04] An empty diagnostic column is \"not measured\", never \"clean\"", "[2026-10-05] A frozen protocol can contradict itself in ways that only show up when you lay out the generator", "[2026-10-05] Deterministic generators leak blinding through names, order, and public seeds", "[2026-10-05] A genome D-list removes host-derived viral background, and moves the cell anchor", "[2026-10-05] Align the small panel and stream the big genome, not the other way round", "[2026-10-05] Amending the v3 protocol touches five pinned layers, in a fixed digest order", "[2026-10-05] A governance re-pin that touches claims/registry.json needs a second re-pin commit", "[2026-10-05] SLURM downloads into the repo tree block the mycelium Stop hook on read-only sessions", "[2026-10-06] kb count is only about a third of a combined full-depth run", "[2026-10-06] The old overlapping-window capture formula overstated recall by tens of points"]
def drop_entries(path, hdr, titles):
    lines = read(path).split("\n"); out = []; i = 0; n = 0
    while i < len(lines):
        l = lines[i]
        if l.startswith(hdr) and l[len(hdr):] in titles:
            n += 1; i += 1
            while i < len(lines) and not lines[i].startswith(hdr): i += 1
            continue
        out.append(l); i += 1
    assert n == len(titles), (path, n, len(titles))
    write(path, "\n".join(out))
drop_entries(".living/decisions.md", "## ", set(REMOVE_DEC))
drop_entries(".living/learnings.md", "### ", set(REMOVE_LEA))
for p, hdr, k in ((".living/decisions.md", "## ", len(REMOVE_DEC)), (".living/learnings.md", "### ", len(REMOVE_LEA))):
    note = f"\n\n<!-- 2026-10-27 batch 4e (D64/D69): {k} experiment-only entries removed from this copy; every entry, including those, is in {REPO}/blob/main{p[1:] if p.startswith('.') else p} -->\n"
    note = f"\n\n<!-- 2026-10-27 batch 4e (D64/D69): {k} experiment-only entries live only in the reproducibility repo copy ({REPO}/blob/main/{p}); this copy keeps package and shared entries -->\n"
    write(p, read(p).rstrip("\n") + note)

# ── 3. stubs (D74) and INDEX rows ─────────────────────────────────────────────
write(".living/findings/FINDINGS_REGISTRY.md", f"""# Findings Registry

> Findings moved to the reproducibility repo (batch 4e, D74): {REPO}/tree/main/.living/findings
> This stub keeps the registry header so the mycelium hooks stay quiet.

| ID | Claim | Status | Topic | Implications | Tags | Last Updated |
|----|-------|--------|-------|--------------|------|--------------|
""")
idx = read(".living/INDEX.md").split("\n")
out = []; done = set()
for l in idx:
    key = l.split("|")[1].strip() if l.startswith("| ") else ""
    if key.startswith("HANDOFF_") or key in ("last-session.md", "log/", "findings/"):
        if "moved" not in done:
            out.append(f"| (moved) HANDOFF_*.md, last-session.md, log/, findings/ | — | 2026-10-27 | in the reproducibility repo (batch 4e): {REPO}/tree/main/.living |"); done.add("moved")
        continue
    out.append(l)
write(".living/INDEX.md", "\n".join(out))

# ── 4. CLAUDE.md (D72, skillpacks line) ───────────────────────────────────────
sub1("CLAUDE.md", "PLAN.md                    # implementation tracker — keep this current!", "PLAN.md                    # live tracker: open rows only — keep this current! (done rows: repro provenance/PLAN_archive_2026-10.md)")
sub1("CLAUDE.md", "WP3, WP7, WP9, Evidence log, VR pilot) are tracked there.", "WP3, WP7, WP9, Evidence log, VR pilot) are tracked there. Done `PLAN.md` rows and the dated \"Next action\" log up to\n2026-10-27 are frozen in the repro's `provenance/PLAN_archive_2026-10.md` (batch 4e); the package tracker holds open work only.\nDev notes that are not package work (`.living/findings`, `.living/log`, old handoffs, superseded plans) live in the repro too.")
sub1("CLAUDE.md", "Only `data/` (ingest target), `todo/`, `skillpacks/`, and `.living/` were kept,", "Only `data/` (ingest target), `todo/`, and `.living/` were kept (`skillpacks/` moved to the repro, batch 4e),")

# ── 5. kept-plan links (D73), MANIFEST.in dead lines, .gitignore ──────────────
sub1("docs/plans/ambient-and-barcode-swapping-controls.md", "docs/plans/2026-10-05-val01-generator-design.md", f"{REPO}/blob/main/docs/plans/2026-10-05-val01-generator-design.md")
for line in ("prune docs/handoffs\n", "prune docs/superpowers\n", "exclude docs/PUBLICATION_READINESS_EXECUTION.md\n"):
    t = read("MANIFEST.in"); new = t.replace(line, ""); assert new != t, line; write("MANIFEST.in", new)
write(".gitignore", read(".gitignore").rstrip("\n") + "\n\n# batch 4e (D64/D70): session logs are hook-written and tracked in the reproducibility repo only\n.living/log/\n")
print("4e_fix.py done")
