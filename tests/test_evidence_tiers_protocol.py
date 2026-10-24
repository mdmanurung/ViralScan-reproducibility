"""Repro-side: package evidence_tiers defaults against the frozen protocol (moved out of the package tests, 4a)."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from viralscan import evidence_tiers as et
from viralscan.evidence_tiers import Calibration, Cutoffs, GridPoint, TierEvidence  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "analysis" / "v3_validation" / "protocol.yaml"


@pytest.fixture(scope="module")
def protocol() -> dict:
    return yaml.safe_load(PROTOCOL.read_text())


@pytest.fixture(scope="module")
def grid(protocol) -> et.Grid:
    return et.grid_from_protocol(protocol)


@pytest.mark.parametrize(
    "text",
    [
        "molecules per cell in {1, 2}, features per sample in {1}",  # two sets
        "features per sample in {1}, molecules per cell in {1, 2}, support fraction in {0.5}",  # wrong order
        "molecules per cell in {1, 2}, features per sample in {1}, support fraction in {0.5}, extra in {1}",
        "molecules per cell in {2, 1}, features per sample in {1}, support fraction in {0.5}",  # unsorted
        "molecules per cell in {1}, features per sample in {1}, support fraction in {0.5, 1.5}",  # > 1
        "molecules per cell in {0, 1}, features per sample in {1}, support fraction in {0.5}",  # zero
        "no sets at all",
    ],
)
def test_grid_parser_refuses_anything_but_the_three_declared_sets(protocol, text):
    bad = copy.deepcopy(protocol)
    bad["calibration"]["threshold_search"]["grid"] = text
    with pytest.raises(ValueError):
        et.grid_from_protocol(bad)

def test_the_grid_follows_the_protocol_text_not_a_constant(protocol):
    edited = copy.deepcopy(protocol)
    edited["calibration"]["threshold_search"]["grid"] = (
        "molecules per cell in {4}, features per sample in {2}, support fraction in {0.6}"
    )
    assert et.grid_from_protocol(edited).points() == [Cutoffs(4, 2, 0.6)]
