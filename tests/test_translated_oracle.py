"""AA-11: the package's ``viralscan.translated.summarize`` reproduces the frozen arm P summaries.

Re-analysis only: ``bustools text`` on the existing ``output.unfiltered.bus`` files under
``$ARMP_ROOT/counts/<GSM>/``; compared with ``$ARMP_ROOT/summary/<GSM>/{all,cells}/<GSM>.summary.json``.
Set ``ARMP_ROOT=data/runs/work/trackA_round1/armP`` and ``VIRALSCAN_PKG`` to a package with
``viralscan.translated``; otherwise skipped.
"""

import json
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.research

ROOT = Path(__file__).resolve().parents[1]
ARMP = os.environ.get("ARMP_ROOT")
PROTEINS = (
    ROOT
    / "data/runs/old_checkout_analysis/translated_search/work/palmdb_plus_annotated_2026-10-14/reference_final/proteins.tsv"
)
RUNS = ROOT / "data/runs/work/trackA_round1/runs"
# (library, dataset, chemistry); cells = the combined_off called_cells.tsv (2472 / 31212 / 2716 barcodes,
# the sizes recorded in summary/<GSM>/check_barcodes.txt)
LIBS = [
    ("GSM3511317", "hsv1", "dropseq"),
    ("GSM4796272", "ebv", "10xv2"),
    ("GSM5705760", "hpv16", "10xv3"),
]


def _expected(dataset: str) -> list[str]:
    for line in (
        (ROOT / "analysis/translated_search/expected_taxa.tsv")
        .read_text()
        .splitlines()[1:]
    ):
        name, ids, _ = line.split("\t", 2)
        if name == dataset:
            return [f"taxon_{t}" for t in ids.split(";")]
    raise KeyError(dataset)


@pytest.mark.skipif(not ARMP, reason="ARMP_ROOT not set")
@pytest.mark.parametrize(
    "lib,dataset,chem", LIBS, ids=[f"{lib}-{chem}" for lib, _, chem in LIBS]
)
@pytest.mark.parametrize("restrict", ["all", "cells"])
def test_summarize_reproduces_frozen_summary(lib, dataset, chem, restrict):
    translated = pytest.importorskip("viralscan.translated")
    armp = Path(ARMP)
    frozen = json.loads(
        (armp / "summary" / lib / restrict / f"{lib}.summary.json").read_text()
    )[lib]
    cells = None
    if restrict == "cells":
        cells_tsv = (
            RUNS / dataset / "combined_off" / lib / lib / "results/called_cells.tsv"
        )
        cells = {
            translated.normalize_barcode(b) for b in translated.read_barcodes(cells_tsv)
        }
        assert len(cells) >= frozen["barcodes_in_matrix"]
    got = translated.summarize_counts_dir(
        armp / "counts" / lib, PROTEINS, _expected(dataset), cells
    )
    assert got == frozen
