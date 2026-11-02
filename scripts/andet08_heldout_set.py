#!/usr/bin/env python3
"""Build the held-out anellovirus genome sets for ANDET-08 (genus-level LOD95).

Purpose: pick genomes that are absent from the panel's reference, label each with the panel's own
    genus group (``virus_key`` of ``virus_identity.tsv``), measure its nearest-panel identity, and
    write the planting inputs (genome FASTA, CDS transcripts, families TSV) for ``sens07 plant``.

Run:     PYTHONPATH=<package>/src python scripts/andet08_heldout_set.py --out-dir <new dir>

Inputs:
    cat42d build/viral.fa                  [REF build, read only]
    cat42d results/virus_identity.tsv      [any viralscan run on cat42d, read only]
    Modha_genomes.fa, Modha_genomes_annotated.gbk, seqids_to_genbank.txt   [ANDET-09e held-out store]
    NCBI nuccore GenBank flatfiles (Gyrovirus, Hetor-, Samektor-, Memtorquevirus, SEN virus,
        Anelloviridae sp.)                 [package fetcher, cached under <out-dir>/ncbi_cache]
Outputs (all in --out-dir, which must not exist):
    panel_anello.fa        the panel's Anelloviridae genomes (minimap2 target)
    candidates.tsv         every candidate: group, source, length, nearest-panel identity/genus, eligibility
    set_<A|B|C|H>/heldout.fa, heldout_cdna.fa, families.tsv, selection_groups.tsv
    build_manifest.json    seeds, digests, counts per group and set
"""

import argparse
import csv
import hashlib
import json
import random
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plant_anello_10x as planter  # noqa: E402
from viralscan.scripts import ncbi_fetch as nf  # noqa: E402

# ── Parameters ───────────────────────────────────────────────────────────────────────────────
SEED = 20261102  # every shuffle and every NCBI subsample derives from this
SET_SIZE = 5  # genomes per genus in one planted run (cells budget: 5 x 8 x levels x cells)
N_LOW_SETS = ("A", "B", "C")  # disjoint draws from the <95 % identity pool
MAX_IDENTITY = 0.95  # VAL-RA-DECISION-01: ANI < 95 % to the panel for the primary sets
MIN_LEN, MAX_LEN = 1500, 4500  # anellovirus genomes are 2-4 kb; shorter are partial, longer chimeric
MIN_CDS = 90  # a transcript must hold one 90 nt read
NCBI_SAMPLE = {  # (esearch term, max records fetched); None = take all
    "Gyrovirus": ('"Gyrovirus"[Organism]', 60),
    "Hetorquevirus": ('"Hetorquevirus"[Organism]', None),
    "Samektorquevirus": ('"Samektorquevirus"[Organism]', None),
    "Memtorquevirus": ('"Memtorquevirus"[Organism]', None),
    "Anelloviridae": ('"SEN virus"[Organism] OR "Anelloviridae sp."[Organism]', 80),
}
NCBI_FILTER = " AND 1500:4500[SLEN] AND complete genome[Title]"
EMAIL = "viralscan-agent@example.org"  # NCBI needs a contact string; a generic one by design

ap = argparse.ArgumentParser()
ap.add_argument("--out-dir", type=Path, required=True)
args = ap.parse_args()
OUT = args.out_dir
OUT.mkdir(parents=True)  # raises if it exists: a run dir is never overwritten

R = Path("/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility")
BUILD = R / "data/references/panel_builds/viral_ref_cat42d/build"
IDENT = R / "data/references/panel_builds/viral_ref_cat42d/runs/SRR12682296/SRR12682296/results/virus_identity.tsv"
HELD = R / "data/references/panel_builds/viral_ref_cat42b/runs_anello_plant/heldout"
GROUPS = [
    "Alphatorquevirus",
    "Betatorquevirus",
    "Gammatorquevirus",
    "Gyrovirus",
    "Samektorquevirus",
    "Hetorquevirus",
    "Memtorquevirus",
    "Anelloviridae",
]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rng_for(label):
    h = hashlib.sha256(f"{SEED}\t{label}".encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big"))


def split_gb(text):
    """One flatfile per record, split on the // terminator."""
    return [rec + "//\n" for rec in text.split("//\n") if rec.strip()]


def origin_seq(rec):
    body = rec.split("\nORIGIN", 1)[1]
    return "".join(re.findall(r"[acgtn]+", body.split("//")[0].lower())).upper()


def cds_transcripts(rec, seq, acc):
    """Sense-strand CDS sequences of one record, spliced and (for '-') reverse-complemented."""
    out = []
    for key, loc, _ in nf.iter_features(rec):
        if key != "CDS":
            continue
        parts = nf._transcript_order(nf._parse_location(loc))
        tx = "".join(seq[s - 1 : e] for s, e, _ in parts)
        if parts and parts[0][2] == "-":
            tx = planter.revcomp(tx)
        if len(tx) >= MIN_CDS:
            out.append((f"{acc}_cds{len(out) + 1}", tx))
    return out


# ── Panel ────────────────────────────────────────────────────────────────────────────────────
panel_group = {}
for row in csv.DictReader(open(IDENT), delimiter="\t"):
    if row["family"] == "Anelloviridae" and row["viral"] == "true":
        panel_group[row["genome_accession"]] = row["genus"]
panel_ids = set(panel_group) | {a.split(".")[0] for a in panel_group}
panel_fa = planter.read_fasta(BUILD / "viral.fa")
with open(OUT / "panel_anello.fa", "w") as fh:
    for acc in sorted(panel_group):
        fh.write(f">{acc}\n{panel_fa[acc]}\n")

# ── Candidates: Modha (genus from the record's SOURCE line) ──────────────────────────────────
cand = {}  # id -> dict(group, source, seq, cds)
bk = dict(line.split() for line in open(HELD / "seqids_to_genbank.txt"))
modha_fa = planter.read_fasta(HELD / "Modha_genomes.fa")
for rec in split_gb(open(HELD / "Modha_genomes_annotated.gbk").read()):
    label = rec.split()[1]
    group = re.search(r"^SOURCE\s+(\w+)", rec, re.M).group(1)
    acc = bk[label]
    cand[acc] = dict(
        group=group,
        source="Modha2025_TPA",
        seq=modha_fa[label].upper(),
        cds=cds_transcripts(rec, modha_fa[label].upper(), acc),
    )

# ── Candidates: NCBI by group ────────────────────────────────────────────────────────────────
for group, (term, cap) in NCBI_SAMPLE.items():
    resp = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params=dict(db="nuccore", term=f"({term}){NCBI_FILTER}", retmax=2000, retmode="json", email=EMAIL),
        timeout=60,
    ).json()["esearchresult"]
    time.sleep(0.4)
    uids = sorted(resp["idlist"])
    if cap and len(uids) > cap:
        uids = sorted(rng_for(f"ncbi\t{group}").sample(uids, cap))
    for i in range(0, len(uids), 20):  # efetch in batches; accessions come from the records
        text = nf._efetch(",".join(uids[i : i + 20]), "gb", EMAIL, None)
        for rec in split_gb(text):
            acc = re.search(r"^VERSION\s+(\S+)", rec, re.M).group(1)
            seq = origin_seq(rec)
            (OUT / "ncbi_cache").mkdir(exist_ok=True)
            (OUT / "ncbi_cache" / f"{acc}.gb").write_text(rec)
            cand[acc] = dict(group=group, source="NCBI_nuccore", seq=seq, cds=cds_transcripts(rec, seq, acc))
    print(f"{group}: esearch {resp['count']} hits, fetched {len(uids)}", file=sys.stderr)

# ── Identity to the panel (minimap2, exact matches via -c) ───────────────────────────────────
with open(OUT / "candidates.fa", "w") as fh:
    for acc, c in sorted(cand.items()):
        fh.write(f">{acc}\n{c['seq']}\n")
with open(OUT / "candidates_vs_panel.paf", "w") as paf, open(OUT / "minimap2.log", "w") as log:
    subprocess.run(
        ["minimap2", "-x", "asm20", "-c", "--secondary=no", "-t", "4", OUT / "panel_anello.fa", OUT / "candidates.fa"],
        stdout=paf, stderr=log, check=True,
    )
nearest = planter.nearest_identity(OUT / "candidates_vs_panel.paf")

# ── Eligibility and draws ────────────────────────────────────────────────────────────────────
rows = []
for acc, c in sorted(cand.items()):
    ident, target = nearest.get(acc, (None, ""))
    in_panel = acc in panel_ids or acc.split(".")[0] in panel_ids
    ok_len = MIN_LEN <= len(c["seq"]) <= MAX_LEN
    clean = set(c["seq"]) <= set("ACGT")
    eligible = (not in_panel) and ok_len and clean and bool(c["cds"]) and c["group"] in GROUPS
    c["eligible"] = eligible
    c["ident"] = ident
    rows.append(
        dict(
            genome=acc, group=c["group"], source=c["source"], length=len(c["seq"]), n_cds=len(c["cds"]),
            nearest_identity=round(ident, 4) if ident else "", nearest_panel=target,
            nearest_panel_group=panel_group.get(target, ""), band=planter.band(ident),
            in_panel=in_panel, eligible=eligible,
        )
    )
with open(OUT / "candidates.tsv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t")
    w.writeheader()
    w.writerows(rows)

sets = {s: defaultdict(list) for s in (*N_LOW_SETS, "H")}
for g in GROUPS:
    low = sorted(a for a, c in cand.items() if c["group"] == g and c["eligible"] and not (c["ident"] and c["ident"] >= MAX_IDENTITY))
    high = sorted(a for a, c in cand.items() if c["group"] == g and c["eligible"] and c["ident"] and c["ident"] >= MAX_IDENTITY)
    rng_for(f"low\t{g}").shuffle(low)
    rng_for(f"high\t{g}").shuffle(high)
    for k, s in enumerate(N_LOW_SETS):
        sets[s][g] = low[k * SET_SIZE : (k + 1) * SET_SIZE]
    sets["H"][g] = high[:SET_SIZE]
    print(f"{g}: low-identity pool {len(low)}, >=95 % pool {len(high)}", file=sys.stderr)

manifest = dict(seed=SEED, set_size=SET_SIZE, max_identity=MAX_IDENTITY, email_used_for_ncbi=EMAIL,
                panel_anello_accessions=len(panel_group), panel_viral_fa_sha256=sha256(BUILD / "viral.fa"),
                identity_sha256=sha256(IDENT), sets={})
for s, by_group in sets.items():
    d = OUT / f"set_{s}"
    d.mkdir()
    chosen = [(g, a) for g in GROUPS for a in by_group[g]]
    with open(d / "heldout.fa", "w") as fa, open(d / "heldout_cdna.fa", "w") as cdna, open(d / "families.tsv", "w") as fam, open(d / "selection_groups.tsv", "w") as sg:
        sg.write("genome\tgroup\tsource\tlength\tnearest_identity\tband\n")
        for g, a in chosen:
            c = cand[a]
            fa.write(f">{a}\n{c['seq']}\n")
            for tid, tx in c["cds"]:
                cdna.write(f">{tid} gene:{tid} chr:{a}\n{tx}\n")
            fam.write(f"{a}\tAnelloviridae\n")  # the scorer joins on the identity table's family
            sg.write(f"{a}\t{g}\t{c['source']}\t{len(c['seq'])}\t{c['ident'] or ''}\t{planter.band(c['ident'])}\n")
    manifest["sets"][s] = {g: len(by_group[g]) for g in GROUPS}
(OUT / "build_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest["sets"], indent=1))
