#!/usr/bin/env bash
# Purpose: G4 byte-rebuild of the frozen v3 reference cat42d (user decisions Q9/Q16, 2026-11-04; PLAN REF-04).
#          Re-run the cat42d recipe (data/references/panel_builds/viral_ref_cat42d/build.sbatch) at the same
#          code (d01043c) and compare every text output with the frozen build, byte for byte.
# Run:     sbatch scripts/slurm_g4_cat42d_rebuild.sh
# Inputs:
#   .claude/worktrees/pin-d01043c (package at d01043c) with src/viralscan/data/*.gtf = the current corpus
#     (curation/panel/gtf_corpus_manifest.tsv, all 393 hashes match) minus the 70 accessions promoted after cat42d
#   ~/.cache/viralscan/ensembl/human/release-116   Ensembl 116 cDNA + GTF (same release as the frozen build)
#   ~/.cache/viralscan/ncbi                        viral and anellovirus FASTAs fetched for cat42d
#   viral_ref_cat42d/dlist.fa                      the frozen D-list (sha256 in dlist.sha256)
# Outputs (in viral_ref_cat42d/rebuild_g4_2026-11-04/):
#   build/                the rebuilt panel
#   compare.tsv           per file: frozen sha256, rebuilt sha256, identical (yes/no)
#   env.txt               code commit, python, kb and kallisto versions used
# Note: the frozen build used a pinned env that no longer exists; kb/kallisto come from viralscan_test_full,
#       so panel.idx (binary, version-dependent) is reported but not claimed (REF-04).
#
#SBATCH -J g4_cat42d_rebuild
#SBATCH --cpus-per-task=8
#SBATCH --mem=180G
#SBATCH --time=24:00:00
set -euo pipefail

M=/exports/archive/hg-funcgenom-research/mdmanurung
PIN=$M/ViralScan/.claude/worktrees/pin-d01043c
F=$M/ViralScan-reproducibility/data/references/panel_builds/viral_ref_cat42d
O=$F/rebuild_g4_2026-11-04
PY=/exports/archive/hg-funcgenom-research/evonk/conda/envs/test_viralscan/bin/python
export PATH=$M/conda/envs/viralscan_test_full/bin:$PATH
mkdir "$O"

# record what runs the rebuild
{
  echo "code $(git -C "$PIN" rev-parse HEAD)"
  echo "python $("$PY" --version 2>&1)"
  echo "kb $(kb --version 2>&1 | head -1)"
  echo "gtf_files $(ls "$PIN"/src/viralscan/data/*.gtf | wc -l)"
  sha256sum "$F/dlist.fa"
} > "$O/env.txt"

# rebuild with the frozen recipe
cd "$PIN"
PYTHONPATH=src "$PY" scripts/build_bundled_panel_ref.py --out "$O/build" --homopolymer-run-length 20 \
  --lowcomplexity-kmer-mask --genome-dlist "$F/dlist.fa" 2>&1 | tee "$O/build.log"

# compare every text output with the frozen build
{
  printf 'file\tfrozen_sha256\trebuilt_sha256\tidentical\n'
  for rel in combined.fa combined.gtf viral.fa viral_panel.gtf cdna.fa panel.t2g lowcomplexity_mask.tsv \
             catalogued_not_indexed.tsv host/host_cdna.gtf panel.idx; do
    a=$(sha256sum "$F/build/$rel" 2>/dev/null | cut -d' ' -f1 || true)
    b=$(sha256sum "$O/build/$rel" 2>/dev/null | cut -d' ' -f1 || true)
    printf '%s\t%s\t%s\t%s\n' "$rel" "${a:-missing}" "${b:-missing}" "$([ -n "$a" ] && [ "$a" = "$b" ] && echo yes || echo no)"
  done
} > "$O/compare.tsv"
cat "$O/compare.tsv"
echo REBUILD_DONE
