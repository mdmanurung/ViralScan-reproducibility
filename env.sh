# source from anywhere: package = <repo>/pkg (a worktree of the package at provenance/PACKAGE_BASE_SHA), data = <repo>/data (git-ignored bulk)
_R="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export VIRALSCAN_PKG="${VIRALSCAN_PKG:-$_R/pkg}"
export VIRALSCAN_DATA="${VIRALSCAN_DATA:-$_R/data}"                  # fastq/bam, references, kraken2, run outputs (never in git)
export VIRALSCAN_CACHE="${VIRALSCAN_CACHE:-$VIRALSCAN_DATA/references/gtf}"  # the package reads <cache>/data/*.gtf
export PYTHONPATH="$VIRALSCAN_PKG/src:${PYTHONPATH:-}"   # src only: the package root has its own scripts/ that would shadow ours
unset _R
