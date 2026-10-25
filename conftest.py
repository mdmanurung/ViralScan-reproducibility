"""Make the pinned ViralScan package importable for pytest (set VIRALSCAN_PKG, or run `source env.sh`)."""
import os
import sys

_pkg = os.environ.get("VIRALSCAN_PKG", "/exports/para-lipg-hpc/mdmanurung/ViralScan-pin2")
for _p in (os.path.join(_pkg, "src"), _pkg):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ["PYTHONPATH"] = os.pathsep.join([os.path.join(_pkg, "src"), _pkg, os.environ.get("PYTHONPATH", "")])  # subprocess-based tests
