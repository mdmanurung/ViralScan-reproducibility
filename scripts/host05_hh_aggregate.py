"""Aggregate DISC-12-HH host_loss.tsv files (hosthomolog.py output) with Wilson 95% intervals.
    python host05_hh_aggregate.py ROOT [ROOT ...]     # ROOT = .../disc12_hostloss_default_2026-10-24 etc.; read-only
"""
import collections
import csv
import glob
import math
import sys


def wilson(k, n, z=1.959964):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


print("root\tpool\tbackground\tstar_params\tconditions\tfragments\tremoved\tmolecules\tlost\tnot_in_lineage\tfrag_loss\tfrag_ci95\tmol_ci95_upper")
for root in sys.argv[1:]:
    agg = collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0])
    for f in sorted(glob.glob(f"{root}/cond/*/host_loss.tsv")):
        for r in csv.DictReader(open(f), delimiter="\t"):
            a = agg[(r["pool"], r["background"], r["star_params"])]
            a[0] += 1
            a[1] += int(r["spiked_fragments"]); a[2] += int(r["removed_fragments"])
            a[3] += int(r["truth_molecules"]); a[4] += int(r["lost_molecules"]); a[5] += int(r["not_in_lineage"])
    for (pool, bg, sp), a in sorted(agg.items()):
        lo, hi = wilson(a[2], a[1]); _, mh = wilson(a[4], a[3])
        print(f"{root.rstrip('/').split('/')[-1]}\t{pool}\t{bg}\t{sp}\t{a[0]}\t{a[1]}\t{a[2]}\t{a[3]}\t{a[4]}\t{a[5]}\t{a[2]/a[1]:.4f}\t[{lo:.4f},{hi:.4f}]\t{mh:.4f}")
