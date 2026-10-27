#!/usr/bin/env bash
set -euo pipefail
/exports/para-lipg-hpc/mdmanurung/viralscan-split/env/bin/python - <<'PY'
import pathlib
p = pathlib.Path("PLAN.md"); t = p.read_text()
old = "Open: `ENVIRONMENTS_INSTALLATIONS.md` stays until its deletion is\n  approved. "
assert old in t
p.write_text(t.replace(old, "`ENVIRONMENTS_INSTALLATIONS.md` (an empty template; software versions are pinned in `environment.yml`/`uv.lock`) was deleted with the owner's approval. "))
PY
