"""VAL-06 D21 burden concordance and VAL-09 freeze mechanism, on synthetic inputs."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import v3_burden as burden
import v3_freeze as freeze

COUNTS = {"h1": 900.0, "h2": 90.0, "v1": 6.0, "v2": 4.0}


def test_burden_is_target_over_common_total_per_10k():
    out = burden.burden_per_10k(COUNTS, ["v1", "v2"], COUNTS)
    assert out["burden_per_10k"] == pytest.approx(100.0)
    assert (out["numerator"], out["denominator"]) == (10.0, 1000.0)


@pytest.mark.parametrize(
    ("counts", "target", "common", "status", "reason"),
    [
        (COUNTS, ["v1"], [], "incomparable", "empty-common-gene-set"),
        (
            COUNTS,
            ["v1", "x"],
            ["h1", "v1"],
            "incomparable",
            "target-outside-common-set",
        ),
        (
            {"h1": 5.0, "v1": 1.0},
            ["v1"],
            ["h1", "v1", "h2"],
            "incomparable",
            "common-gene-missing",
        ),
        (
            {"h1": 0.0, "v1": 0.0},
            ["v1"],
            ["h1", "v1"],
            "not_estimable",
            "zero-denominator",
        ),
    ],
)
def test_unmet_denominator_rules_keep_the_row_with_a_reason(
    counts, target, common, status, reason
):
    out = burden.burden_per_10k(counts, target, common)
    assert (out["status"], out["reason"]) == (status, reason)


def test_negative_counts_raise():
    with pytest.raises(ValueError):
        burden.burden_per_10k({"h": -1.0, "v": 2.0}, ["v"], ["h", "v"])


def test_concordance_is_signed_relative_difference_with_incomparable_kept():
    ok = lambda b: {"status": "estimable", "burden_per_10k": b}
    bad = {"status": "incomparable", "reason": "empty-common-gene-set"}
    out = burden.burden_concordance(
        [(ok(12.0), ok(8.0)), (ok(5.0), ok(5.0)), (bad, ok(1.0)), (ok(0.0), ok(0.0))]
    )
    diffs = [r["difference"] for r in out["pairs"]]
    assert diffs == [pytest.approx(0.4), 0.0, None, None]
    assert (out["n_pairs"], out["n_estimable"]) == (4, 2)
    assert out["median_difference"] == pytest.approx(0.2)


def _protocol(tmp_path, generation):
    seeds = {
        n: {"status": "frozen", "value": i + 1} for i, n in enumerate(freeze.SEED_NAMES)
    }
    seeds["generation"] = generation
    path = tmp_path / "protocol.yaml"
    path.write_text(json.dumps({"seeds": seeds}))  # JSON is valid YAML
    return path


def _tiny(tmp_path):
    tiny = tmp_path / "tiny"
    (tiny / "sub").mkdir(parents=True)
    (tiny / "a.tsv").write_text("x\n")
    (tiny / "sub" / "b.tsv").write_text("y\n")
    return tiny


def test_freeze_refuses_a_pending_seed(tmp_path):
    protocol = _protocol(tmp_path, {"status": "pending", "value": None})
    with pytest.raises(ValueError, match="seeds.generation"):
        freeze.build_freeze(protocol, _tiny(tmp_path))


def test_freeze_round_trip_and_every_drift_is_reported(tmp_path):
    protocol = _protocol(tmp_path, {"status": "frozen", "value": 99})
    tiny = _tiny(tmp_path)
    record = freeze.build_freeze(protocol, tiny)
    assert record["seeds"]["generation"] == 99
    assert set(record["tiny_outputs"]) == {"a.tsv", "sub/b.tsv"}
    assert freeze.verify_freeze(record, protocol, tiny) == []
    (tiny / "a.tsv").write_text("changed\n")
    (tiny / "c.tsv").write_text("new\n")
    errors = freeze.verify_freeze(record, protocol, tiny)
    assert [e.split(":")[0] for e in errors] == [
        "tiny output a.tsv",
        "tiny output c.tsv",
    ]
    tampered = {**record, "scorer_version": "other"}
    assert any(
        "freeze_sha256" in e
        for e in freeze.verify_freeze(tampered, protocol, _tiny_clean(tmp_path))
    )


def _tiny_clean(tmp_path):
    clean = tmp_path / "clean"
    (clean / "sub").mkdir(parents=True)
    (clean / "a.tsv").write_text("x\n")
    (clean / "sub" / "b.tsv").write_text("y\n")
    return clean


def test_cli_never_overwrites_a_freeze(tmp_path):
    protocol = _protocol(tmp_path, {"status": "frozen", "value": 99})
    out = tmp_path / "freeze.json"
    args = [
        "build",
        "--out",
        str(out),
        "--tiny-dir",
        str(_tiny(tmp_path)),
        "--protocol",
        str(protocol),
    ]
    assert freeze.main(args) == 0
    with pytest.raises(SystemExit):
        freeze.main(args)
