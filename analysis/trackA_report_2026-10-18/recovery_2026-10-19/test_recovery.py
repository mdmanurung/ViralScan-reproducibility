"""Replay the v3 closure failure through the pinned planter without real data."""

import ast
import csv
import importlib.util
import io
import os
import random
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
PINNED = Path("/exports/archive/hg-funcgenom-research/mdmanurung/vs_pinned/97a64f6/scripts/plant_anello_10x.py")


@pytest.mark.parametrize("read_len", [64, 98])
def test_tail_geometry_survives_metadata_loop_rebinding(read_len):
    spec = importlib.util.spec_from_file_location("pinned_plant", PINNED)
    pl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pl)
    source = ast.parse((HERE / "trackA_anello_plant.py").read_text())
    block = next(n for n in source.body if isinstance(n, ast.If) and ast.unparse(n.test) == "a.tail_rate is not None")
    ns = {"a": SimpleNamespace(tail_rate=0.05, read_len=read_len), "pl": pl}
    exec(compile(ast.Module(body=[block], type_ignores=[]), "tail_override", "exec"), ns)
    # The real script uses r for identity-table rows after configuring the callback.
    ns["r"] = {"family": "Anelloviridae"}
    row = dict(genome="g", genus="test", identity_band="exact", length=2000, orf1_start=500, last_cds_end=1500)
    truth = io.StringIO()
    assert pl.plant_reads([row], {"g": {"seq": "ACGT" * 500}}, ["ACGTACGTACGTACGT"], random.Random(20261019), io.StringIO(), io.StringIO(), csv.writer(truth, delimiter="\t"), read_len=read_len, umi_len=10, levels=(2000,), windows=("3p",), error_rate=0) == 2000
    rows = list(csv.reader(io.StringIO(truth.getvalue()), delimiter="\t"))
    tailed = sum(int(r[10]) > 0 for r in rows)
    assert 60 <= tailed <= 140  # Binomial variation around the frozen 5% rate.
    assert all(int(r[9]) + int(r[10]) == read_len for r in rows)


def test_retained_concat_order_survives_post_deletion_refresh(tmp_path):
    source = ast.parse((HERE / "build_provenance.py").read_text())
    nodes = [n for n in source.body if isinstance(n, ast.FunctionDef) and n.name in {"tsv", "concat_plans"}]
    ns = {"csv": csv, "os": os}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "provenance_helpers", "exec"), ns)
    status = tmp_path / "status"
    status.mkdir()
    header = "library\tr1\tr2\tr1_files\tr2_files\n"
    active = "a\tA1\tA2\tcurrent1 current2\tcurrent3 current4\n"
    retained = "a\tA1\tA2\told1 old2\told3 old4\nb\tB1\tB2\trun2_R1 run1_R1\trun2_R2 run1_R2\n"
    (status / "concat_plan.tsv").write_text(header + active)
    plans, sources = ns["concat_plans"](tmp_path)
    assert set(plans) == {"a"}
    (status / "concat_plan_retained.tsv").write_text(header + retained)
    plans, sources = ns["concat_plans"](tmp_path)
    assert plans["a"]["r1_files"] == "current1 current2"
    assert plans["b"]["r1_files"].split() == ["run2_R1", "run1_R1"]
    assert sources["b"].endswith("concat_plan_retained.tsv")
