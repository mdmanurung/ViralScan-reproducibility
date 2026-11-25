"""CAT-08: leave-fold-out confusability of the shipped panel, per family.

Purpose: for every genome in the panel, simulate 90 bp reads, pseudoalign them to a virus-only index that
         lacks that genome, and record where they land (unmapped, same species, same genus, same family, other
         family). Genomes are held out in K stratified folds (K indexes, not one per genome).
Run:     python scripts/cat08_loo_confusability.py OUT_DIR           # builds, quantifies, summarises
         (OUT_DIR must not exist; needs samtools and kb's kallisto on PATH via KALLISTO/SAMTOOLS env)
Inputs:  viral.fa of the shipped build (VIRAL_FA), producer: scripts/build_bundled_panel_ref.py
         virus_catalog.tsv (CATALOG), producer: package data
Outputs: OUT_DIR/per_genome.tsv   one row per held-out genome: category counts, top landing accession
         OUT_DIR/per_family.tsv   per family: reads, P(captured), category fractions
         OUT_DIR/cross_family.tsv foreign families that held-out reads land on
         OUT_DIR/run_info.json    parameters, tool versions, input sha256
"""

import collections
import csv
import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path

import pandas as pd

# Parameters ------------------------------------------------------------------------------
VIRAL_FA = Path(os.environ["VIRAL_FA"])
CATALOG = Path(os.environ["CATALOG"])
KALLISTO = os.environ[
    "KALLISTO"
]  # kb's own binary; the conda kallisto aborts on kb indexes
SAMTOOLS = os.environ.get("SAMTOOLS", "samtools")
K_FOLDS = 20  # held-out share per fold = 1/K; a family smaller than K has some folds without it
READ_LENGTH = 90  # the 10x R2 geometry used by CAT-12
READ_STEP = 30  # tiling step; every 30th window, both strands at random
SEED = 20261102
THREADS = int(os.environ.get("THREADS", "8"))

# Load genomes and taxonomy ------------------------------------------------------------------
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True)

genomes = {}
for line in VIRAL_FA.read_text().splitlines():
    if line.startswith(">"):
        acc = line[1:].split()[0]
        genomes[acc] = []
    else:
        genomes[acc].append(line.strip().upper())
genomes = {acc: "".join(parts) for acc, parts in genomes.items()}

catalog = pd.read_csv(CATALOG, sep="\t", dtype=str, keep_default_na=False).set_index(
    "accession"
)
tax = {}
for acc in genomes:
    row = catalog.loc[acc.split(".")[0]]
    # a blank rank must never match another blank rank
    tax[acc] = {
        rank: row[rank] or f"NA:{acc}" for rank in ("species", "genus", "family")
    }
    tax[acc]["family_label"] = row["family"] or "NA"

# Stratified folds --------------------------------------------------------------------------
rng = random.Random(SEED)
fold_of = {}
by_family = collections.defaultdict(list)
for acc in sorted(genomes):
    by_family[tax[acc]["family_label"]].append(acc)
for members in by_family.values():
    rng.shuffle(members)
    offset = rng.randrange(K_FOLDS)
    for i, acc in enumerate(members):
        fold_of[acc] = (i + offset) % K_FOLDS

# Per fold: index without the fold, reads from the fold, pseudobam ---------------------------------
reverse = str.maketrans("ACGTN", "TGCAN")
rows = []
cross = collections.Counter()
for fold in range(K_FOLDS):
    fold_dir = OUT / f"fold{fold:02d}"
    fold_dir.mkdir()
    held = [acc for acc in genomes if fold_of[acc] == fold]
    with open(fold_dir / "index.fa", "w") as fa:
        for acc, seq in genomes.items():
            if fold_of[acc] != fold:
                fa.write(f">{acc}\n{seq}\n")
    n_reads = collections.Counter()
    with open(fold_dir / "reads.fq", "w") as fq:
        for acc in held:
            seq = genomes[acc]
            for start in range(0, max(len(seq) - READ_LENGTH, 0) + 1, READ_STEP):
                read = seq[start : start + READ_LENGTH]
                if len(read) < READ_LENGTH or "N" in read:
                    continue
                if rng.random() < 0.5:
                    read = read.translate(reverse)[::-1]
                fq.write(f"@{acc}|{start}\n{read}\n+\n{'I' * READ_LENGTH}\n")
                n_reads[acc] += 1
    subprocess.run(
        [
            KALLISTO,
            "index",
            "-k",
            "31",
            "-i",
            fold_dir / "index.idx",
            fold_dir / "index.fa",
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            KALLISTO,
            "quant",
            "-i",
            fold_dir / "index.idx",
            "-o",
            fold_dir / "quant",
            "--single",
            "-l",
            str(READ_LENGTH),
            "-s",
            "20",
            "-t",
            str(THREADS),
            "--pseudobam",
            fold_dir / "reads.fq",
        ],
        check=True,
        capture_output=True,
    )
    # read -> set of compatible targets
    landing = collections.defaultdict(set)
    sam = subprocess.run(
        [SAMTOOLS, "view", fold_dir / "quant" / "pseudoalignments.bam"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    for rec in sam.splitlines():
        qname, flag, target = rec.split("\t")[:3]
        if not int(flag) & 4:
            landing[qname].add(target)
    per_source = collections.defaultdict(collections.Counter)
    top_target = collections.defaultdict(collections.Counter)
    for qname, targets in landing.items():
        src = qname.split("|")[0]
        t = tax[src]
        if all(tax[x]["species"] == t["species"] for x in targets):
            category = "same_species"
        elif all(tax[x]["genus"] == t["genus"] for x in targets):
            category = "same_genus"
        elif all(tax[x]["family"] == t["family"] for x in targets):
            category = "same_family"
        else:
            category = "other_family"
            cross[
                (
                    t["family_label"],
                    ";".join(
                        sorted(
                            {tax[x]["family_label"] for x in targets}
                            - {t["family_label"]}
                        )
                    ),
                )
            ] += 1
        per_source[src][category] += 1
        for x in targets:
            top_target[src][x] += 1
    for acc in held:
        n = n_reads[acc]
        c = per_source[acc]
        mapped = sum(c.values())
        best = top_target[acc].most_common(1)
        rows.append(
            {
                "accession": acc,
                "family": tax[acc]["family_label"],
                "genus": tax[acc]["genus"],
                "species": tax[acc]["species"],
                "fold": fold,
                "length": len(genomes[acc]),
                "n_reads": n,
                "unmapped": n - mapped,
                "same_species": c["same_species"],
                "same_genus": c["same_genus"],
                "same_family": c["same_family"],
                "other_family": c["other_family"],
                "top_landing": best[0][0] if best else "",
                "top_landing_reads": best[0][1] if best else 0,
            }
        )
    for name in ("index.fa", "reads.fq"):
        (fold_dir / name).unlink()  # own scratch only; regenerate with the same seed

# Summaries -------------------------------------------------------------------------------------------
per_genome = pd.DataFrame(rows).sort_values(["family", "accession"])
per_genome.to_csv(OUT / "per_genome.tsv", sep="\t", index=False)
counts = [
    "n_reads",
    "unmapped",
    "same_species",
    "same_genus",
    "same_family",
    "other_family",
]
per_family = per_genome.groupby("family")[counts].sum()
per_family.insert(0, "n_genomes", per_genome.groupby("family").size())
per_family["p_captured"] = 1 - per_family["unmapped"] / per_family["n_reads"]
for col in counts[2:]:
    per_family[f"frac_{col}"] = per_family[col] / per_family["n_reads"]
per_family.round(4).to_csv(OUT / "per_family.tsv", sep="\t")
pd.DataFrame(
    [(a, b, n) for (a, b), n in cross.most_common()],
    columns=["source_family", "landing_families", "reads"],
).to_csv(OUT / "cross_family.tsv", sep="\t", index=False)
json.dump(
    {
        "viral_fa": str(VIRAL_FA),
        "viral_fa_sha256": hashlib.sha256(VIRAL_FA.read_bytes()).hexdigest(),
        "k_folds": K_FOLDS,
        "read_length": READ_LENGTH,
        "read_step": READ_STEP,
        "seed": SEED,
        "kallisto": subprocess.run(
            [KALLISTO, "version"], capture_output=True, text=True
        ).stdout.strip(),
        "n_genomes": len(genomes),
    },
    open(OUT / "run_info.json", "w"),
    indent=1,
)
