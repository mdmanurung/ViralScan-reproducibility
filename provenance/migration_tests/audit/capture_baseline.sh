#!/usr/bin/env bash
# Step-1 captures other than pytest: wheel/sdist members, ship-scope check, CLI help hashes,
# strict docs build, CI notebooks. Runs in a shared clone of the package at <ref>; never writes to the repo.
# usage: capture_baseline.sh <name> [git-ref=HEAD]   -> rehearsal/<name>-capture/{summary.tsv,...}
# To compare a later state, run again with another name and: diff -r rehearsal/<a>-capture rehearsal/<b>-capture (skip tree/).
set -uo pipefail
SPLIT=/exports/para-lipg-hpc/mdmanurung/viralscan-split
REPO=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan
E=/exports/archive/hg-funcgenom-research/mdmanurung/conda/envs/viralscan_test_full
PY=$SPLIT/env/bin/python
name=${1:?usage: capture_baseline.sh <name> [ref]}; ref=${2:-HEAD}
W=$SPLIT/rehearsal/$name-capture; rm -rf "$W"; mkdir -p "$W"
sha=$(git -C "$REPO" rev-parse "$ref")
if [ -n "${TREE:-}" ]; then   # capture an already-prepared rehearsal tree (batch applied)
  ln -s "$TREE" "$W/tree"; echo "tree $TREE" > "$W/ref.txt"; cd "$W/tree"
else
  git clone -q --shared --no-checkout "$REPO" "$W/tree" && git -C "$W/tree" checkout -q --detach "$sha" || exit 2
  echo "$ref $sha" > "$W/ref.txt"; cd "$W/tree"
fi
S="$W/summary.tsv"; : > "$S"
rec() { printf '%s\t%s\t%s\n' "$1" "$2" "$3" >> "$S"; echo "$1: $2 $3"; }

# 1. build + ship scope
if "$PY" -m build --outdir "$W/dist" > "$W/build.log" 2>&1 || "$PY" -m build --no-isolation --outdir "$W/dist" > "$W/build2.log" 2>&1; then
  whl=$(ls "$W"/dist/*.whl); sd=$(ls "$W"/dist/*.tar.gz)
  unzip -Z1 "$whl" | sort > "$W/wheel_members.txt"
  tar tzf "$sd" | sed 's|^[^/]*/||' | sort > "$W/sdist_members.txt"
  rec build ok "wheel=$(wc -l < "$W/wheel_members.txt") sdist=$(wc -l < "$W/sdist_members.txt")"
  PATH=$E/bin:$PATH python scripts/check_ship_scope.py --wheel "$whl" --sdist "$sd" --docker-context . > "$W/ship_scope.log" 2>&1 \
    && rec ship_scope ok "" || rec ship_scope FAIL "$(tail -1 "$W/ship_scope.log" | cut -c1-120)"
  PATH=$E/bin:$PATH python scripts/check_dist_size.py "$W/dist" --max-mb 60 > "$W/dist_size.log" 2>&1 && rec dist_size ok "" || rec dist_size FAIL ""
else
  rec build FAIL "see build.log / build2.log"
fi

# 2. CLI help hashes
mkdir -p "$W/cli"
cli() { PATH=$E/bin:$PATH PYTHONPATH=src python -m viralscan "$@" 2>&1; }
cli --help > "$W/cli/_top.txt"
subs=$(grep -oE '\{[a-z0-9_,-]+\}' "$W/cli/_top.txt" | head -1 | tr -d '{}' | tr ',' ' ')
for sc in $subs; do cli "$sc" --help > "$W/cli/$sc.txt"; done
(cd "$W/cli" && sha256sum *.txt > "$W/cli_hashes.txt")
rec cli ok "$(echo $subs | wc -w) subcommands, top=$(head -c 0 /dev/null)$(wc -l < "$W/cli/_top.txt") lines"

# 3. strict docs build
PATH=$E/bin:$PATH PYTHONPATH=$SPLIT/docs-deps:src python -m sphinx -W --keep-going -b html docs "$W/docs_html" > "$W/docs.log" 2>&1 \
  && rec docs ok "" || rec docs FAIL "$(grep -cE 'WARNING|ERROR' "$W/docs.log") warnings/errors"
grep -E 'WARNING|ERROR' "$W/docs.log" | sed 's/^[^ ]*\/tree\///' | sort > "$W/docs_warnings.txt"

# 4. CI notebooks
PATH=$E/bin:$PATH PYTHONPATH="$PWD/src" MPLBACKEND=Agg timeout 1500 python -m pytest --nbmake -p no:cacheprovider -q \
  docs/vignettes/multimapping_correction.ipynb docs/vignettes/cell_calling_denominators.ipynb docs/vignettes/cell_type_enrichment.ipynb \
  docs/vignettes/qc_and_read_evidence.ipynb docs/vignettes/host_response_depth_control.ipynb docs/vignettes/specificity_true_negative.ipynb \
  > "$W/nbmake.log" 2>&1 && rec nbmake ok "$(tail -1 "$W/nbmake.log" | cut -c1-80)" || rec nbmake FAIL "$(tail -1 "$W/nbmake.log" | cut -c1-100)"
