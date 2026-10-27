# Data Manifest

Layout and where each kind of data lives: see `data/README.md`. Paths below that start with a bare `benchmark_inputs/` now live under `data/inputs/benchmark_inputs/`.

<!-- Add entries below using the appropriate manifest entry template. -->

### reference_strategy_fastqs
```yaml
name: reference_strategy_fastqs
type: genomic
source: NCBI SRA / ENA (SRR12682296 staged; SRR20710641, SRR8315713 from showcase fastq_root)
date_acquired: 2026-06-28
format: FASTQ.gz (paired-end 10xv3) + source_urls.tsv provenance
size: "~10.9 GB gzipped (staged sample only)"
raw_path: benchmark_inputs/reference_strategy/   # FASTQs gitignored; source_urls.tsv tracked
metadata_path: data/metadata/reference_strategy_fastqs/
status: raw
known_issues:
  - Only 1 of 3 benchmark runs staged locally; others depend on external showcase fastq_root
  - R2 (cDNA) ~8.7 GB gzipped
access_restrictions: none
tags: [fastq, 10x, scrna-seq, sra, ena, benchmark, input]
```

Paired-end 10x FASTQ inputs for the reference-strategy benchmark. Bytes are
gitignored and re-fetchable from ENA via each sample's tracked `source_urls.tsv`
(URL + MD5 + bytes). Feeds the ViralScan/STARsolo runs summarized in
`results/reference_strategy_benchmark.tsv`.

### reference_strategy_refs
```yaml
name: reference_strategy_refs
type: genomic
source: Derived — 10x GRCh38-2024-A + Serratus+expanded-anellovirus panel; STARsolo & kallisto indices built locally
date_acquired: 2026-06-27
format: STAR genomeDir, kallisto .idx, FASTA, GTF, t2g/TSV (20 artifacts)
size: "~64 GB (in-repo references/); more out-of-repo"
raw_path: data/raw/reference_strategy_refs/   # pointer doc only; bytes are gitignored / out-of-repo
metadata_path: data/metadata/reference_strategy_refs/
status: validated   # audited via reference_audit.tsv (SHA256 + feature counts)
known_issues:
  - HHV-6A (NC_001664.4) vs HHV-6B (HUM_HERP6B contigs) must not be conflated
  - Confirm STARsolo genomeDir completeness before benchmark submission
  - viralscan all_virus and combined share identical viral index/t2g (same SHA256)
access_restrictions: institutional-only
tags: [reference, kallisto, starsolo, benchmark, viral, GRCh38, anellovirus]
```

Reference indices and annotations for the reference-strategy benchmark (three
strategies × two aligners). Too large for git (~64 GB); registered in place and
gitignored, with machine-readable provenance in `reference_manifest.json` and
per-artifact SHA256/feature-count audit in `reference_audit.tsv` (both committed).
Rebuild commands are stored verbatim under `build_commands` in the manifest. This
dataset is the shared input for `results/reference_strategy_benchmark.tsv`.

### backups and envs (two-folder migration close-out, 2026-10-27)

| path | size | sha256 |
|---|---|---|
| `data/backups/branch-bundles/ViralScan.2026-10-27.bundle` | 17M | 4ffd914ee9a5c792d5102e63f780389bddcba1c7dae9200df0eeb0f48dd31a65 |
| `data/backups/branch-bundles/ViralScan-reproducibility.2026-10-27.bundle` | 11M | ebca3c64d31d5756b38dbb924a47db7eb51501cd2fa62c2957b0e5adb8f8e244 |
| `data/envs/viralscan_env_pinned.explicit.txt` | 96K | 385ea0f4c104dbeaf182c3112f3473282f3a19890c4ba808a521974157493ee6 |
| `data/backups/viralscan-split/` | 3.4G, 48560 entries | tracker/tests/audit copied to `provenance/migration_tests/` |
| `data/backups/stage5-script-backups/`, `stage7-record-backups/` | 12M, 2.1M | pre-rewrite script/table copies |
