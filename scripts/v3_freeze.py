#!/usr/bin/env python3
"""Freeze record for the truth panel (PLAN VAL-09): versions, seeds, protocol and output hashes.

Mechanism only. Nothing is chosen here. Every seed is read from the protocol and
``validate_v3_protocol.frozen_seed`` refuses a seed that is still ``pending``, so a freeze cannot
be built before G3 freezes ``seeds.generation``. The record is a JSON file whose last field is the
sha256 of everything before it; ``verify`` rebuilds each hash from disk and lists every difference.

Run:  python scripts/v3_freeze.py build --out freeze.json --tiny-dir DIR [--holdout-salt-sha256 HEX]
      python scripts/v3_freeze.py verify freeze.json --tiny-dir DIR
``--tiny-dir`` is a directory written by ``generate_truth_panel.py``; every file under it is hashed
by relative path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    from scripts.generate_truth_panel import GENERATOR_VERSION
    from scripts.v3_score import PROTOCOL, SCORER_VERSION
    from scripts.validate_v3_protocol import frozen_seed, load_yaml
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from generate_truth_panel import GENERATOR_VERSION  # type: ignore[no-redef]
    from v3_score import PROTOCOL, SCORER_VERSION  # type: ignore[no-redef]
    from validate_v3_protocol import frozen_seed, load_yaml  # type: ignore[no-redef]

#: Seeds a freeze records (protocol ``seeds`` keys). ``root`` first: the others derive from it.
SEED_NAMES = (
    "root",
    "generation",
    "split",
    "cell_calling",
    "evidence_sampling",
    "bootstrap",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_tree(directory: Path) -> dict[str, str]:
    """sha256 of every file under ``directory``, keyed by relative POSIX path."""
    files = sorted(p for p in directory.rglob("*") if p.is_file())
    return {p.relative_to(directory).as_posix(): sha256_file(p) for p in files}


def _seal(record: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(record, indent=2, sort_keys=True)
    return {**record, "freeze_sha256": hashlib.sha256(body.encode()).hexdigest()}


def build_freeze(
    protocol_path: Path,
    tiny_dir: Path,
    holdout_salt_sha256: str | None = None,
) -> dict[str, Any]:
    """The freeze record; raises ValueError while any seed is not frozen."""
    protocol = load_yaml(protocol_path)
    record = {
        "generator_version": GENERATOR_VERSION,
        "scorer_version": SCORER_VERSION,
        "protocol_sha256": sha256_file(protocol_path),
        "seeds": {name: frozen_seed(protocol, name) for name in SEED_NAMES},
        "holdout_salt_sha256": holdout_salt_sha256,
        "tiny_outputs": hash_tree(tiny_dir),
    }
    return _seal(record)


def verify_freeze(
    freeze: dict[str, Any], protocol_path: Path, tiny_dir: Path
) -> list[str]:
    """Every way the freeze differs from disk; an empty list means it still holds."""
    body = {k: v for k, v in freeze.items() if k != "freeze_sha256"}
    errors = []
    if _seal(body)["freeze_sha256"] != freeze.get("freeze_sha256"):
        errors.append("freeze_sha256 does not match the record body")
    for field, now in (
        ("generator_version", GENERATOR_VERSION),
        ("scorer_version", SCORER_VERSION),
    ):
        if freeze.get(field) != now:
            errors.append(f"{field}: frozen {freeze.get(field)!r}, code is {now!r}")
    if freeze.get("protocol_sha256") != sha256_file(protocol_path):
        errors.append("protocol_sha256 differs from the protocol on disk")
    protocol = load_yaml(protocol_path)
    for name in SEED_NAMES:
        if freeze.get("seeds", {}).get(name) != frozen_seed(protocol, name):
            errors.append(f"seeds.{name} differs from the protocol")
    frozen, found = freeze.get("tiny_outputs", {}), hash_tree(tiny_dir)
    for rel in sorted(frozen.keys() | found.keys()):
        if frozen.get(rel) != found.get(rel):
            errors.append(
                f"tiny output {rel}: frozen {frozen.get(rel)}, on disk {found.get(rel)}"
            )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--out", type=Path, required=True)
    build.add_argument("--tiny-dir", type=Path, required=True)
    build.add_argument("--protocol", type=Path, default=PROTOCOL)
    build.add_argument("--holdout-salt-sha256")
    check = sub.add_parser("verify")
    check.add_argument("freeze", type=Path)
    check.add_argument("--tiny-dir", type=Path, required=True)
    check.add_argument("--protocol", type=Path, default=PROTOCOL)
    args = parser.parse_args(argv)
    if args.command == "build":
        try:
            record = build_freeze(
                args.protocol, args.tiny_dir, args.holdout_salt_sha256
            )
        except ValueError as exc:
            sys.exit(f"cannot freeze: {exc}")
        if args.out.exists():
            sys.exit(f"{args.out} exists; a freeze is never overwritten")
        args.out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        return 0
    errors = verify_freeze(
        json.loads(args.freeze.read_text()), args.protocol, args.tiny_dir
    )
    for line in errors:
        print(line, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
