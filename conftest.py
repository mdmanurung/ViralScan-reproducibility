"""Make the pinned ViralScan package importable for pytest (set VIRALSCAN_PKG, or run `source env.sh`)."""
import os
import sys

_pkg = os.environ.setdefault("VIRALSCAN_PKG", "/exports/para-lipg-hpc/mdmanurung/ViralScan-pin2")  # governance_utils.package_path reads it too
# only src: the package root also has a scripts/ dir, which would shadow this repo's scripts/ namespace package
if os.path.join(_pkg, "src") not in sys.path:
    sys.path.insert(0, os.path.join(_pkg, "src"))
os.environ["PYTHONPATH"] = os.pathsep.join([os.path.join(_pkg, "src"), os.environ.get("PYTHONPATH", "")])  # subprocess-based tests
