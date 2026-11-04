"""Seeded molecule subset of one library, as a shadow run directory that `viralscan evidence` can read.

Purpose:  `viralscan evidence` replays every read of the library (kallisto bus) and holds all target reads in memory.
          GSM5725696 (KSHV induced, 23.7 M HHV-8 molecules, 27 M reads) ran out of memory at 24 G and 48 G. The
          package has no molecule-sampling option, so this script cuts the input instead: it draws N whole
          molecules (CB+UMI) from the target's read lineage, writes only their reads to a new FASTQ pair, and
          builds a run directory whose config.yaml points at that pair. `viralscan evidence` then runs unchanged.
Run:      python scripts/target_verdict_subset.py --lineage <read_lineage.tsv.gz> --run-dir <primary sample dir> \\
              --out <new dir> [--n-molecules 20000] [--seed 20261104]
Inputs:   --lineage    read_lineage.tsv.gz of an earlier full `viralscan evidence` replay of the same run and target
                       (columns read_number, cb, ub; read_number = 0-based record index in the kb_r1/kb_r2 pair)
          --run-dir    the completed primary sample directory (config.yaml, kb-python/, results/)
Outputs:  <out>/subset_fastq/{R1,R2}.fastq.gz        only the reads of the sampled molecules, original order
          <out>/sample_molecules.tsv                 cb, ub, n_reads of every sampled molecule
          <out>/subset_manifest.json                seed, N, frame size, read counts, source paths
          <out>/subset_run/<sample>/                shadow run dir: config.yaml (kb_r1/kb_r2/output changed),
                                                    symlinks to results/ and the kb-python files evidence reads
          <out>/subset_run/run_manifest.json        copy of the primary run manifest
Rule:     a molecule's score is the first 8 bytes of sha256(f"{seed}\\0{cb}_{ub}"); the N lowest scores are kept.
          This is the rule of `viralscan.evidence.sample_fasta_deterministic`, applied to molecules, so it does not
          depend on file order. Fractions from the subset are over sampled molecules; counts are not library totals.
"""

import argparse
import gzip
import hashlib
import heapq
import json
import re
import shutil
import subprocess
from pathlib import Path

# Knobs ------------------------------------------------------------------------------------------------------------
N_MOLECULES = (
    20_000  # user decision 2026-11-04: about 20,000 target molecules per library
)
SEED = 20261104  # date of the decision; fixed so the draw reruns bit for bit
KB_FILES = (
    "matrix.ec",
    "transcripts.txt",
    "output.resolved.sorted.bus.txt",
)  # read by evidence; symlinked
KB_COUNTS_FILES = ("cells_x_genes.genes.txt",)  # under kb-python/counts_unfiltered/


def molecule_score(seed: int, cb: str, ub: str) -> int:
    return int.from_bytes(
        hashlib.sha256(f"{seed}\0{cb}_{ub}".encode()).digest()[:8], "big"
    )


def lineage_rows(path: Path):
    """(read_number, cb, ub) of every lineage record."""
    with gzip.open(path, "rt") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        i_num, i_cb, i_ub = (
            header.index("read_number"),
            header.index("cb"),
            header.index("ub"),
        )
        for line in fh:
            f = line.split("\t", 12)
            yield int(f[i_num]), f[i_cb], f[i_ub]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lineage", type=Path, required=True)
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--n-molecules", type=int, default=N_MOLECULES)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    out, run_dir = args.out, args.run_dir.resolve()
    out.mkdir(parents=True)  # fails if the directory exists: never overwrite

    # Pass 1: the N lowest-scoring molecules, streaming (max-heap on score; repeats of a kept molecule are skipped).
    heap: list[tuple[int, str, str]] = []  # (-score, cb, ub)
    kept: set[tuple[str, str]] = set()
    frame_reads = 0
    for _, cb, ub in lineage_rows(args.lineage):
        frame_reads += 1
        if (cb, ub) in kept:
            continue
        score = molecule_score(args.seed, cb, ub)
        if len(heap) < args.n_molecules:
            heapq.heappush(heap, (-score, cb, ub))
            kept.add((cb, ub))
        elif score < -heap[0][0]:
            _, old_cb, old_ub = heapq.heapreplace(heap, (-score, cb, ub))
            kept.discard((old_cb, old_ub))
            kept.add((cb, ub))
    chosen = set(kept)

    # Pass 2: every read of the chosen molecules.
    reads_of: dict[tuple[str, str], int] = {}
    numbers: list[int] = []
    for num, cb, ub in lineage_rows(args.lineage):
        if (cb, ub) in chosen:
            numbers.append(num)
            reads_of[(cb, ub)] = reads_of.get((cb, ub), 0) + 1
    numbers.sort()
    with (out / "sample_molecules.tsv").open("w") as fh:
        fh.write("cb\tub\tn_reads\n")
        for (cb, ub), n in sorted(reads_of.items()):
            fh.write(f"{cb}\t{ub}\t{n}\n")

    # Subset FASTQ pair: stream the primary pair once (gzip -dc in a child process) and keep the chosen records.
    config_text = (run_dir / "config.yaml").read_text()
    src = {
        k: re.search(rf"^{k}: (.+)$", config_text, re.M).group(1).strip()
        for k in ("kb_r1", "kb_r2")
    }
    fq_dir = out / "subset_fastq"
    fq_dir.mkdir()
    procs = [
        subprocess.Popen(
            ["gzip", "-dc", src[k]], stdout=subprocess.PIPE, bufsize=1 << 22
        )
        for k in src
    ]
    r1, r2 = procs[0].stdout, procs[1].stdout
    wanted = iter(numbers)
    nxt = next(wanted)
    index = 0
    with (
        gzip.open(fq_dir / "R1.fastq.gz", "wb", 4) as w1,
        gzip.open(fq_dir / "R2.fastq.gz", "wb", 4) as w2,
    ):
        while nxt is not None:
            rec1 = [r1.readline() for _ in range(4)]
            rec2 = [r2.readline() for _ in range(4)]
            if not (rec1[0] and rec2[0]):
                raise ValueError(
                    f"FASTQ ended at record {index}, before lineage read {nxt}"
                )
            if index == nxt:
                w1.writelines(rec1)
                w2.writelines(rec2)
                nxt = next(wanted, None)
            index += 1
    for proc in procs:
        proc.kill()

    # Shadow run dir: same config.yaml but kb_r1/kb_r2/output point at the subset; evidence-read files are symlinked.
    shadow = out / "subset_run" / run_dir.name
    (shadow / "kb-python" / "counts_unfiltered").mkdir(parents=True)
    new_text = config_text
    for key, value in {
        "kb_r1": fq_dir / "R1.fastq.gz",
        "kb_r2": fq_dir / "R2.fastq.gz",
        "output": f"{shadow}/",
    }.items():
        new_text, n = re.subn(rf"^{key}: .*$", f"{key}: {value}", new_text, flags=re.M)
        if n != 1:
            raise ValueError(f"config.yaml has {n} '{key}:' lines, expected 1")
    (shadow / "config.yaml").write_text(new_text)
    (shadow / "results").symlink_to(run_dir / "results")
    for name in KB_FILES:
        (shadow / "kb-python" / name).symlink_to(run_dir / "kb-python" / name)
    for name in KB_COUNTS_FILES:
        (shadow / "kb-python" / "counts_unfiltered" / name).symlink_to(
            run_dir / "kb-python" / "counts_unfiltered" / name
        )
    manifest = run_dir.parent / "run_manifest.json"
    if manifest.is_file():
        shutil.copy(manifest, shadow.parent / "run_manifest.json")

    (out / "subset_manifest.json").write_text(
        json.dumps(
            {
                "seed": args.seed,
                "n_molecules_requested": args.n_molecules,
                "n_molecules_sampled": len(reads_of),
                "frame_target_reads": frame_reads,
                "sampled_target_reads": len(numbers),
                "lineage": str(args.lineage),
                "source_run_dir": str(run_dir),
                "source_fastq": src,
                "records_streamed": index,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
