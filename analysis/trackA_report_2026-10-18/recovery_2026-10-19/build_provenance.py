#!/usr/bin/env python3
"""Track A provenance: everything needed to re-download the FASTQs and reproduce every artefact (user, 2026-10-15).

Writes provenance/ (idempotent, read-only on data):
  global.json                 pinned code commits, tool versions, reference + arm-P reference file hashes, env snapshots
  env/<env>.txt               conda-meta package list + pip freeze of the run / script environments
  reference/cat42d/           small reference inputs + build recipe copied verbatim
  round_snapshot.tar.gz(+.sha256)  scripts/, status tables, ledger, evidence tables of this round
  <dataset>/<library>.json    per library: accessions -> source files (gz sha256 AND decompressed content sha256) ->
                              concat order -> chemistry -> per-arm run_manifest summary -> cells -> arm P -> evidence ->
                              retained outputs; `complete` + `missing` list
  index.tsv                   library, dataset, complete, n_missing
  REPRODUCE.md                step-by-step recipe
Re-download check: compare the DECOMPRESSED content hash (zcat | sha256sum), never the .gz bytes (fasterq-dump | pigz
is not byte-reproducible). Usage (sbatch, hashes ~100 GB of reference files): python scripts/build_provenance.py
"""
import csv
import glob
import hashlib
import json
import os
import subprocess
import tarfile

from sibling_specific_reads import slug

M = "/exports/archive/hg-funcgenom-research/mdmanurung"
R = f"{M}/viralscan_work/trackA_round1"
D = f"{M}/viralscan_work/discovery"
P = f"{R}/provenance"
REF = f"{M}/viral_ref_cat42d"
ARMS = ("combined_off", "combined_artefact", "twostep")


def tsv(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader((ln.replace("\r", "") for ln in fh), delimiter="\t"))


def concat_plans(root):
    plans, sources = {}, {}
    for rel in ("status/concat_plan.tsv", "status/concat_plan_retained.tsv"):
        path = f"{root}/{rel}"
        if not os.path.isfile(path):
            continue
        for row in tsv(path):
            if row["library"] not in plans:
                plans[row["library"]] = row
                sources[row["library"]] = path
    return plans, sources


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def fsha(path):
    return {"path": path, "bytes": os.path.getsize(path), "sha256": sha(path)} if os.path.isfile(path) else {"path": path, "missing": True}


_cache = {}


def cached_sha(path):
    if path not in _cache:
        _cache[path] = fsha(path)
    return _cache[path]


def jload(path):
    with open(path) as fh:
        return json.load(fh)


os.makedirs(f"{P}/env", exist_ok=True)
os.makedirs(f"{P}/reference/cat42d", exist_ok=True)

# ---------------------------------------------------------------- inputs
na = [ln.rstrip("\n").split("\t") for ln in open(f"{R}/status/n_a.tsv") if ln.strip()]
superseded = {r[0] for r in na if "superseded" in "\t".join(r)}
na_libs = {r[0]: r[3] for r in na[1:] if len(r) > 3 and r[2] == "n/a" and not r[3].startswith("superseded")} if na else {}
manifest = [m for m in tsv(f"{R}/manifest.tsv") if m["sample"] not in superseded and m["dataset"] != "tonsil_atlas"]  # tonsil cancelled 2026-10-18
libs = {r["library"]: r for r in tsv(f"{R}/status/libs.tsv")}
plan, plan_sources = concat_plans(R)
ledger = {}
for r in tsv(f"{R}/explore_ledger.tsv"):
    ledger[(r["sample"], r["arm"])] = r
content = {}
if os.path.isfile(f"{R}/status/fastq_content_sha256.tsv"):
    for r in tsv(f"{R}/status/fastq_content_sha256.tsv"):
        content[r["path"]] = r
gz_sha = {}
for f in glob.glob(f"{D}/checksums/*.sha256"):
    for ln in open(f):
        parts = ln.rstrip("\n").split(None, 1)
        if len(parts) == 2:
            gz_sha[os.path.realpath(os.path.join(D, parts[1]))] = parts[0]
downloads = {}
for r in tsv(f"{D}/status/downloads.tsv"):
    if r["state"] == "done":
        downloads[os.path.realpath(r["path"])] = r
retained = {}
if os.path.isfile(f"{R}/status/retained_outputs.tsv"):
    for r in tsv(f"{R}/status/retained_outputs.tsv"):
        retained[(r["library"], r["path"])] = r  # last row wins
verdicts = {r["evidence_dir"]: r for r in tsv(f"{R}/evidence/verdicts.tsv")}
tier_path = f"{R}/evidence/tiers.tsv"
tiers = {r["evidence_dir"]: r for r in tsv(tier_path)} if os.path.isfile(tier_path) else {}
calls = tsv(f"{R}/evidence/calls.tsv")
cells_super = {r["sample"] for r in tsv(f"{R}/status/super_expressors_trackA.tsv")}

# ---------------------------------------------------------------- global
commits, builds, tools = set(), set(), {}
for rm in glob.glob(f"{R}/runs/*/*/*/run_manifest.json"):
    try:
        j = jload(rm)
    except Exception:
        continue
    si = j.get("software_identity", {})
    commits.add(si.get("git_commit"))
    builds.add(si.get("build_sha256"))
    for k, v in j.get("tool_binaries", {}).get("run", {}).items():
        tools[k] = {"version": v.get("version"), "sha256": v.get("sha256")}
reach = {}
for c in sorted(x for x in commits if x):
    out = subprocess.run(["git", "-C", f"{M}/ViralScan", "branch", "-r", "--contains", c], capture_output=True, text=True).stdout
    reach[c] = [b.strip() for b in out.splitlines()][:4]

env_paths = {"viralscan_bench": f"{M}/conda/envs/viralscan_bench", "viralscan_test_full": f"{M}/conda/envs/viralscan_test_full"}
for name, ep in env_paths.items():
    lines = []
    for f in sorted(glob.glob(f"{ep}/conda-meta/*.json")):
        try:
            j = jload(f)
            lines.append(f"{j['name']}=={j['version']}={j.get('build', '')}\t{j.get('channel', '')}")
        except Exception:
            pass
    pip = subprocess.run([f"{ep}/bin/python", "-m", "pip", "freeze"], capture_output=True, text=True).stdout
    with open(f"{P}/env/{name}.txt", "w") as fh:
        fh.write("# conda-meta (name==version=build, channel)\n" + "\n".join(lines) + "\n\n# pip freeze\n" + pip)

ref_small = ["viral_panel.gtf", "viral.fa", "catalogued_not_indexed.tsv", "lowcomplexity_mask.tsv"]
for f in ref_small:
    src = f"{REF}/build/{f}"
    if os.path.isfile(src):
        subprocess.run(["cp", "-p", src, f"{P}/reference/cat42d/{f}"], check=True)
for f in ("build.log", "build.sbatch", "dlist.sha256"):
    if os.path.isfile(f"{REF}/{f}"):
        subprocess.run(["cp", "-p", f"{REF}/{f}", f"{P}/reference/cat42d/{f}"], check=True)
ref_files = {}
for f in sorted(glob.glob(f"{REF}/build/*")) + sorted(glob.glob(f"{REF}/build/host/*")):
    if os.path.isfile(f):
        ref_files[os.path.relpath(f, REF)] = cached_sha(f)

armp_ref = {}
for rc in sorted(glob.glob(f"{R}/armP/counts/*/translated_receipt.json"))[:1]:
    j = jload(rc)
    cmd = j.get("command", [])
    for flag in ("-i", "-g", "-c1", "-c2"):
        if flag in cmd:
            p = cmd[cmd.index(flag) + 1]
            armp_ref[flag] = cached_sha(p)
T = f"{M}/ViralScan/analysis/translated_search/work/arm_p_confirm_2026-10-14"
for f in ("ref/viral_genomes.fa", "ref/Homo_sapiens.GRCh38.pep.all.fa.gz", "ref/pep.sha256"):
    armp_ref["confirm:" + f] = cached_sha(f"{T}/{f}")
for f in ("proteins.faa", "proteins.tsv"):
    armp_ref["confirm_ref:" + f] = cached_sha(f"{R}/armP/confirm_ref/{f}")

# SRA toolkit used by the downloader (bin/worker2.sbatch)
sra = {}
try:
    txt = open(f"{D}/bin/worker2.sbatch").read()
    bdir = [ln.split("=", 1)[1].strip().strip('"') for ln in txt.splitlines() if ln.startswith("B=")]
    if bdir:
        out = subprocess.run([f"{bdir[0]}/prefetch", "--version"], capture_output=True, text=True).stdout
        sra = {"bin_dir": bdir[0], "prefetch_version": out.strip().splitlines()[-1] if out.strip() else None,
               "fasterq_dump_flags": "--split-files --include-technical", "compress": "pigz -c (default level)",
               "worker_script_sha256": sha(f"{D}/bin/worker2.sbatch")}
except Exception as e:  # noqa: BLE001
    sra = {"error": str(e)}

snap = f"{P}/round_snapshot.tar.gz"
with tarfile.open(snap, "w:gz") as tf:
    for rel in ("scripts", "GUARD.md", "manifest.tsv", "explore_ledger.tsv", "evidence/calls.tsv", "evidence/verdicts.tsv", "evidence/tiers.tsv", "evidence/sibling_specific.tsv",
                "status/concat_plan.tsv", "status/concat_plan_retained.tsv", "status/libs.tsv", "status/n_a.tsv", "status/submissions.tsv",
                "status/fastq_content_sha256.tsv", "status/retained_outputs.tsv", "status/confirm_hits.sha256",
                "status/super_expressors_trackA.tsv", "status/variants_README.md"):
        if os.path.exists(f"{R}/{rel}"):
            tf.add(f"{R}/{rel}", arcname=rel)
    tf.add(f"{D}/bin/worker2.sbatch", arcname="discovery_bin/worker2.sbatch")
    tf.add(f"{D}/status/downloads.tsv", arcname="discovery_status/downloads.tsv")
snap_sha = sha(snap)
open(snap + ".sha256", "w").write(f"{snap_sha}  round_snapshot.tar.gz\n")

glob_rec = {
    "pinned_code": {"git_commits": sorted(x for x in commits if x), "reachable_from": reach, "build_sha256": sorted(x for x in builds if x),
                    "pinned_checkout": f"{M}/vs_pinned/97a64f6"},
    "tools": tools,
    "environments": {n: {"path": p, "snapshot": f"env/{n}.txt", "sha256": sha(f"{P}/env/{n}.txt")} for n, p in env_paths.items()},
    "reference_cat42d": {"build_files": ref_files, "copied_to": "reference/cat42d/",
                         "note": "host = Ensembl GRCh38 release 116 cDNA + GTF (build.log step 1); viral FASTAs from NCBI (step 4)"},
    "armP_reference": armp_ref,
    "download_tooling": sra,
    "round_snapshot": {"file": "round_snapshot.tar.gz", "sha256": snap_sha},
}
with open(f"{P}/global.json", "w") as fh:
    json.dump(glob_rec, fh, indent=1, sort_keys=True)

# ---------------------------------------------------------------- per library
index = []
for m in manifest:
    ds, lib = m["dataset"], m["sample"]
    miss = []
    L = libs.get(lib, {})
    rec = {"dataset": ds, "library": lib, "title": L.get("title"), "runs": L.get("runs", "").split(), "pairs": L.get("pairs")}
    # source files
    if lib in plan:
        if (plan[lib]["r1"], plan[lib]["r2"]) != (m["r1"], m["r2"]):
            raise ValueError(f"Concat plan does not match frozen manifest for {lib}")
        files = [("R1", f) for f in plan[lib]["r1_files"].split()] + [("R2", f) for f in plan[lib]["r2_files"].split()]
        rec["concat"] = {"r1": plan[lib]["r1"], "r2": plan[lib]["r2"], "order_r1": plan[lib]["r1_files"].split(),
                         "order_r2": plan[lib]["r2_files"].split(), "method": "cat in listed order (valid multi-member gzip)",
                         "plan_receipt": cached_sha(plan_sources[lib])}
    else:
        files = [("R1", m["r1"]), ("R2", m["r2"])]
        rec["concat"] = None
    srcs = []
    for role, f in files:
        rp = os.path.realpath(f)
        c = content.get(rp)
        d = downloads.get(rp, {})
        s = {"role": role, "path": rp, "gz_bytes": os.path.getsize(rp) if os.path.isfile(rp) else None,
             "gz_sha256_at_download": gz_sha.get(rp), "content_sha256": c["content_sha256"] if c else None,
             "lines": int(c["lines"]) if c else None, "download_source": d.get("source"), "download_finished": d.get("finished"),
             "local_not_downloaded_by_round": "/benchmark_inputs/" in rp}
        if not s["content_sha256"]:
            miss.append(f"content_sha256:{os.path.basename(rp)}")
        srcs.append(s)
    rec["source_files"] = srcs
    # chemistry
    chem = f"{R}/chem/{lib}.json"
    rec["chemistry_json"] = cached_sha(chem)
    if rec["chemistry_json"].get("missing"):
        miss.append("chem_json")
    # arms
    rec["arms"] = {}
    for a in ARMS:
        base = f"{R}/runs/{ds}/{a}/{lib}/{lib}"
        rm_path = f"{R}/runs/{ds}/{a}/{lib}/run_manifest.json"
        if not os.path.isfile(rm_path):
            miss.append(f"{a}:run_manifest")
            continue
        j = jload(rm_path)
        fp = j.get("input_fingerprints", {})
        rc_path = f"{R}/runs/{ds}/{a}/{lib}/run_complete.json"
        rec["arms"][a] = {
            "run_dir": f"runs/{ds}/{a}/{lib}", "git_commit": j.get("software_identity", {}).get("git_commit"),
            "run_fingerprint": j.get("run_fingerprint"), "reference_fingerprint": j.get("reference_fingerprint"),
            "input_fingerprints": fp, "input_paths": j.get("input_paths"), "options": j.get("options"),
            "cell_calling": j.get("cell_calling"), "chemistry": j.get("chemistry_detection"),
            "run_complete": (jload(rc_path).get("completed_at") if os.path.isfile(rc_path) else None),
            "ledger_row": ledger.get((lib, a)), "config_yaml": cached_sha(f"{base}/config.yaml"),
            "run_manifest": cached_sha(rm_path), "viral_summary": cached_sha(f"{base}/results/viral_summary.tsv"),
        }
        if (lib, a) not in ledger:
            miss.append(f"{a}:ledger")
        rec["concat_gz_sha256_note"] = "sample1/sample2 fingerprints are sha256 of the CONCATENATED .gz files; gzip bytes need not reproduce, compare source content hashes"
    # frozen cells
    rec["frozen_cells"] = cached_sha(f"{R}/status/cells/{lib}.barcodes.txt")
    if rec["frozen_cells"].get("missing"):
        miss.append("frozen_cells")
    # arm P
    rcp = f"{R}/armP/counts/{lib}/translated_receipt.json"
    if os.path.isfile(rcp):
        j = jload(rcp)
        rec["armP"] = {"receipt": cached_sha(rcp), "command": j.get("command"), "script_sha256": j.get("script_sha256"),
                       "slurm_job_id": j.get("slurm_job_id"),
                       "summary_dirs": [f"armP/summary/{lib}/all", f"armP/summary/{lib}/cells"]}
    else:
        miss.append("armP:receipt")
    cf = f"{R}/armP/confirm/{lib}/{lib}.confirm_groups.tsv"
    rec["armP_confirm"] = cached_sha(cf)
    if rec["armP_confirm"].get("missing"):
        miss.append("armP_confirm")
    # evidence
    ev = [c for c in calls if c["sample"] == lib and c["arm"] == "combined_off"]
    rec["evidence"] = []
    for c in ev:
        evidence_name = "__".join([ds, lib, "combined_off", slug(c["virus"])])
        v = verdicts.get(evidence_name)
        rec["evidence"].append({"tier": tiers.get(evidence_name),
                                "tier_table": cached_sha(tier_path),
                                "sibling_receipt": cached_sha(f"{R}/evidence/{evidence_name}/sibling_specific.json"),
                                "virus": c["virus"], "molecules": c["molecules"], "evidence_dir": evidence_name,
                                "verdict": v["verdict"] if v else None})
        if evidence_name not in tiers:
            miss.append(f"tier:{c['virus']}")
        if not v:
            miss.append(f"evidence:{c['virus']}")
    rec["super_expressor_row"] = lib in cells_super
    if lib not in cells_super:
        miss.append("super_expressor")
    # retained outputs
    rec["retained_outputs"] = {k[1]: {"bytes": int(v["bytes"]), "sha256": v["sha256"]} for k, v in retained.items() if k[0] == lib}
    if not rec["retained_outputs"]:
        miss.append("retained_outputs")
    rec["complete"] = not miss
    rec["missing"] = miss
    os.makedirs(f"{P}/{ds}", exist_ok=True)
    with open(f"{P}/{ds}/{lib}.json", "w") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
    index.append([lib, ds, "complete" if not miss else "incomplete", len(miss), ";".join(miss)[:300]])

for lib, why in na_libs.items():
    index.append([lib, "n/a", "n/a", 0, why[:300]])
with open(f"{P}/index.tsv", "w", newline="") as fh:
    w = csv.writer(fh, delimiter="\t")
    w.writerow(["library", "dataset", "state", "n_missing", "missing"])
    w.writerows(index)
print("provenance:", sum(1 for r in index if r[2] == "complete"), "complete of", sum(1 for r in index if r[2] != "n/a"), "libraries")
