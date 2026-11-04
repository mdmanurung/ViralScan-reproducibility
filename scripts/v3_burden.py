#!/usr/bin/env python3
"""Secondary burden per 10,000 molecules, D21 of the v3 protocol (PLAN VAL-06, burden concordance).

Pure functions, no data read. The protocol allows a per-10k burden only when numerator and
denominator come from the same count layer and the denominator is summed over a frozen common
host-plus-virus gene set (``harmonization.secondary_total_expression_rule``). Anything else is
reported ``incomparable`` and the row is kept, never dropped and never filled in:

* empty common set: ``incomparable`` / ``empty-common-gene-set``;
* a target gene outside the common set: ``incomparable`` / ``target-outside-common-set``;
* a common gene absent from the layer: ``incomparable`` / ``common-gene-missing``;
* zero denominator: ``not_estimable`` / ``zero-denominator``.

Concordance is descriptive: the signed relative difference of the two tools' burdens (difference
over mean, the form of M9), per pair, plus the median over the estimable pairs. No threshold lives
here; acceptance is a protocol decision.
"""

from __future__ import annotations

import math
from collections.abc import Collection, Mapping, Sequence
from statistics import median
from typing import Any

PER = 10_000


def burden_per_10k(
    counts: Mapping[str, float],
    target_genes: Collection[str],
    common_genes: Collection[str],
) -> dict[str, Any]:
    """Target molecules per 10,000 molecules on ``common_genes``, from one count layer."""
    common, target = set(common_genes), set(target_genes)
    if not common:
        return {"status": "incomparable", "reason": "empty-common-gene-set"}
    if not target <= common:
        return {"status": "incomparable", "reason": "target-outside-common-set"}
    if not common <= set(counts):
        return {"status": "incomparable", "reason": "common-gene-missing"}
    if any(not math.isfinite(counts[g]) or counts[g] < 0 for g in common):
        raise ValueError("counts must be finite and nonnegative")
    numerator = sum(counts[g] for g in target)
    denominator = sum(counts[g] for g in common)
    if denominator == 0:
        return {"status": "not_estimable", "reason": "zero-denominator"}
    return {
        "status": "estimable",
        "burden_per_10k": PER * numerator / denominator,
        "numerator": numerator,
        "denominator": denominator,
    }


def burden_concordance(
    pairs: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]],
) -> dict[str, Any]:
    """Per-sample signed relative difference (ViralScan - comparator) / mean, and its median."""
    rows = []
    for ours, theirs in pairs:
        if ours["status"] != "estimable" or theirs["status"] != "estimable":
            rows.append({"status": "incomparable", "difference": None})
            continue
        a, b = ours["burden_per_10k"], theirs["burden_per_10k"]
        if a + b == 0:
            rows.append({"status": "not_applicable", "difference": None})
        else:
            rows.append({"status": "estimable", "difference": (a - b) / ((a + b) / 2)})
    values = [r["difference"] for r in rows if r["difference"] is not None]
    return {
        "pairs": rows,
        "n_pairs": len(rows),
        "n_estimable": len(values),
        "median_difference": median(values) if values else None,
    }
