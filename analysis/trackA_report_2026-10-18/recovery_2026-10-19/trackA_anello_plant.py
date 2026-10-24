#!/usr/bin/env python3
"""Plant realistic anellovirus reads into one Track A library's own host_filtered background (PREREG step 1b), 2026-10-19.

  python scripts/trackA_anello_plant.py <ds> <lib> <window 3p|5p> <read_len> <cb_len> <umi_len> [--n-background 2000000]
Output: anello_settle_2026-10-19/plant/<ds>/{planted/R1.fastq.gz,R2.fastq.gz, truth.tsv, selection.tsv, plant_manifest.json}.
Reuses the pinned plant_anello_10x.py (plant_reads: 3p window = [templated body][untemplated polyA] from the annotated cleavage site, mutate,
UMI generator, truth.tsv with body_len). Genomes:
  exact    one panel anellovirus per genus from anello.fa, CDS spans from viral_panel.gtf (identity to the index = 100%)  -> the gates
  held-out the 8 Modha genomes of ANDET-09e (identity bands vs the same 2,040-contig panel, selection.tsv there)         -> detection limit only
Cells: the 2,000 most frequent barcodes of the background. A planted (CB, UMI) never reuses a background one.
"""
import argparse, csv, gzip, json, os, random, sys
from collections import Counter

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
M = "/exports/archive/hg-funcgenom-research/mdmanurung"
R = f"{M}/viralscan_work/trackA_round1"
sys.path.insert(0, f"{M}/vs_pinned/97a64f6/scripts")
import plant_anello_10x as pl

PLANT = f"{M}/viral_ref_cat42b/runs_anello_plant"
GBK = f"{PLANT}/heldout/Modha_genomes_annotated.gbk"
SEL = f"{PLANT}/fastq/selection.tsv"
PANEL_FA = f"{R}/anello_ref_2026-10-19/anello_star/anello.fa"
GTF = f"{M}/viral_ref_cat42d/build/viral_panel.gtf"
IDENT = f"{R}/runs/ebv/twostep/GSM4796271/GSM4796271/results/virus_identity.tsv"
GENERA = ["Alphatorquevirus", "Betatorquevirus", "Gammatorquevirus", "Samektorquevirus", "Memtorquevirus", "Gyrovirus"]

ap = argparse.ArgumentParser()
ap.add_argument("ds"); ap.add_argument("lib"); ap.add_argument("window", choices=["3p", "5p"])
ap.add_argument("read_len", type=int); ap.add_argument("cb_len", type=int); ap.add_argument("umi_len", type=int)
ap.add_argument("--n-background", type=int, default=2_000_000)
ap.add_argument("--seed", type=int, default=20261019)
ap.add_argument("--tail-rate", type=float, help="fraction of 3' reads carrying a poly-A tail (PREREG_ADDENDUM_1; default = pinned planter, ~1/3)")
ap.add_argument("--plant-dir", default="plant", help="output folder under anello_settle_2026-10-19/ (v3: plant_v3_tail5)")
a = ap.parse_args()
if a.tail_rate is not None:  # starts are uniform over WINDOW_3P_LEN; a read is tailed iff start > cleavage - read_len, i.e. the last (r-1) offsets
    tail_offsets = round(a.tail_rate * pl.WINDOW_3P_LEN) + 1
    pl.cleavage_site = lambda row: row["last_cds_end"] + pl.WINDOW_3P_LEN + a.read_len - tail_offsets
rng = random.Random(a.seed)
out = f"{R}/anello_settle_2026-10-19/{a.plant_dir}/{a.ds}/"
os.makedirs(out + "planted", exist_ok=True)
bg = f"{R}/runs/{a.ds}/twostep/{a.lib}/{a.lib}/host_filtered"

# exact panel genomes
fa = pl.read_fasta(PANEL_FA)
genus_of = {}
for r in csv.DictReader(open(IDENT), delimiter="\t"):
    if r["family"] == "Anelloviridae" and r["genome_accession"]:
        genus_of[r["genome_accession"]] = r["genus"] or "Anelloviridae"
cds = {}
for ln in open(GTF):
    f = ln.split("\t")
    if len(f) > 8 and f[2] in ("CDS", "exon") and f[0] in fa:
        cds.setdefault(f[0], []).append((int(f[3]) - 1, int(f[4])))
genomes, selection = {}, []
for g in GENERA:
    pool = sorted(acc for acc, spans in cds.items() if genus_of.get(acc) == g and 1500 <= len(fa[acc]) <= 4500)
    if not pool:
        print(f"WARNING: no exact panel genome for {g}", file=sys.stderr)
        continue
    acc = rng.choice(pool)
    orf1 = max(cds[acc], key=lambda s: s[1] - s[0])
    genomes[acc] = dict(seq=fa[acc].upper(), orf1_start=orf1[0], last_cds_end=max(e for _, e in cds[acc]))
    selection.append(dict(genome=acc, genus=g, identity_band="exact", nearest_identity=1.0, nearest_panel_genome=acc, completeness="panel",
                          length=len(genomes[acc]["seq"]), orf1_start=orf1[0], last_cds_end=genomes[acc]["last_cds_end"]))
# held-out Modha genomes
modha = pl.read_gbk(GBK)
for row in csv.DictReader(open(SEL), delimiter="\t"):
    if row["genome"] in modha:
        genomes["modha_" + row["genome"]] = modha[row["genome"]]
        selection.append({**row, "genome": "modha_" + row["genome"], "length": int(row["length"]), "orf1_start": int(row["orf1_start"]),
                          "last_cds_end": int(row["last_cds_end"])})
with open(out + "selection.tsv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(selection[0]), delimiter="\t")
    w.writeheader()
    w.writerows(selection)

# background + barcode pool
taken, cbs, n = set(), Counter(), 0
with gzip.open(f"{bg}/R1.fastq.gz", "rt") as i1, gzip.open(f"{bg}/R2.fastq.gz", "rt") as i2, \
        gzip.open(out + "planted/R1.fastq.gz", "wt") as o1, gzip.open(out + "planted/R2.fastq.gz", "wt") as o2, \
        open(out + "truth.tsv", "w", newline="") as tf:
    while n < a.n_background:
        h1, s1, p1, q1 = (i1.readline() for _ in range(4))
        h2, s2, p2, q2 = (i2.readline() for _ in range(4))
        if not h1 or not h2:
            break
        o1.write(h1 + s1 + p1 + q1)
        o2.write(h2 + s2 + p2 + q2)
        cb, ub = s1[:a.cb_len], s1[a.cb_len:a.cb_len + a.umi_len]
        taken.add((cb, ub))
        cbs[cb] += 1
        n += 1
    pool = [c for c, _ in cbs.most_common(2000)]
    truth = csv.writer(tf, delimiter="\t")
    truth.writerow(["read_id", "genome", "genus", "identity_band", "window", "level", "cb", "umi", "pos", "body_len", "tail_len"])
    n_planted = pl.plant_reads(selection, genomes, pool, rng, o1, o2, truth, read_len=a.read_len, umi_len=a.umi_len, levels=pl.LEVELS,
                               windows=(a.window,), barcode_blocks=None, taken=taken)
json.dump(dict(ds=a.ds, lib=a.lib, window=a.window, read_len=a.read_len, cb_len=a.cb_len, umi_len=a.umi_len, n_background_pairs=n,
               n_planted_reads=n_planted, tail_rate=a.tail_rate, n_cells=len(pool), seed=a.seed, error_rate=pl.ERROR_RATE, levels=list(pl.LEVELS),
               background=bg), open(out + "plant_manifest.json", "w"), indent=2)
print(f"{a.ds}: {n:,} background pairs + {n_planted:,} planted reads over {len(pool)} cells; {len(selection)} genomes")
