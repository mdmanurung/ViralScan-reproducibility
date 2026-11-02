# Retraction notice (CAT-30), 2026-11-02

Approved by the user on 2026-11-02. Applies to everything under `covid_viralscan/results/` (untracked; the files there are unchanged).

The `Alphatorquevirus` rows in the `viral_summary.tsv`, `viral_summary.knee.tsv` and `per_cell_viral*.tsv` files, and the combined figure in `SURVEY_SUMMARY*.md`, are **retracted**. They are not evidence of anellovirus infection or of a viral load in these samples.

| Sample | Published `Alphatorquevirus` UMI | Infected cells / all barcodes |
|---|---:|---:|
| `LUM-SJ-x213-g`, `LUM-SJ-x213-g.jul2` | 1,167,103.0 | 17.63 % |
| `LUM-SJ-x216-g`, `LUM-SJ-x216-g.jul2` | 1,605,631.0 | 19.05 % |

The percentages use all barcodes in the matrix (578,938 and 586,305), not called cells.

## Why

- Re-extracting every read the index placed in an anellovirus equivalence class (1,269,176 reads, x213) showed that 99.999 % carry a homopolymer of 15 nt or more (F-019).
- 90.1 % of those reads aligned best to a viral contig, almost all to the poly(C) tract of encephalomyocarditis virus. 9.8 % aligned best to the human genome.
- In a 200,000-read sample, 91 % were at least 80 % poly-G, the signature of empty clusters on two-colour Illumina chemistry.
- Only 9 reads were free of homopolymer and template-switch oligo. All 9 aligned best to GRCh38. No clean read had a viral best hit.
- A competitive STARsolo alignment to GRCh38 plus the viral panel (Phase A) found 0 viral-primary reads in 4,500,299 primary alignments. All 8 detected anellovirus accessions are accession-level artefacts (F-005).

## What stands

- SARS-CoV-2 was not detected in either sample.
- Low-level divergent anellovirus is not excluded. Anelloviruses are common in human blood and the reference covers little of their sequence space. The retraction covers the published magnitude, not the possible presence of a virus.

Do not cite the `Alphatorquevirus` rows. No replacement number exists yet (PLAN `DSR-04`). Registry claim: `ttv-biological-signal` in `claims/registry.json` (status `rejected`, reason already states the retraction). Sources: `.living/findings/FINDINGS_REGISTRY.md` (F-005, F-019), `.living/findings/covid-anellovirus-signal-is-polyg-reads.md`.
