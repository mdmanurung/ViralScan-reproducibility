# Target verdicts, round 2026-11-04

**Exploratory, not reportable (pre G3/G4 freeze).** Status: jobs submitted 2026-11-04; results tables below are filled by
`scripts/target_verdict_collect.py` once the jobs finish (see "To finish").

## Question and rule

Do the reads behind the EXPECTED virus call of eight positive libraries align better to the virus than to GRCh38?
A target call is **CONFIDENT** when all three hold (user decision 2026-11-04):
1. the library is an expected positive by study design;
2. the read verdict is predominantly virus-best (counted molecules, majority cut 0.5; every fraction is reported);
3. a matched negative is clean where one exists (HPV16 raft vs parental SRR19537339; HN18 vs HN01 SRR13418973).

Splice junctions (annotated junctions seen) and strand (`strand_qc.tsv`) are supporting evidence where evaluable.
Wording: HHV-6B is "HHV-6B RNA detected" (no ciHHV-6 claim). HIV-1 in SRR20710641 and HSV-1 in tonsil ERR13027027 are
"unexplained, not reported" and were not investigated.

## Method

- Command: `viralscan evidence --run-dir <sample dir> --virus <label> --viral-fasta cat42d/build/viral.fa --host-fasta GRCh38 genome.fa --host-gtf genes.gtf --blast --cell-tags --splice`
  through `scripts/dsr02_validate_call.py --splice --host-gtf` (adds the per-read verdict table with repeat class). The two flags are new, opt-in
  arguments of that script; earlier rounds' commands are unchanged (`tests/test_dsr02_validate_call.py`).
- Package: worktree `data/pkg_13ea776` (13ea776). Current main is `ed7da79`; `git diff 13ea776 ed7da79` touches no evidence, splice, strand, verdict or read-replay code
  (only `run --reference-host-species`, `utils.host_gene_mask`, scautoqc, build_reference, docs). minimap2 2.31-r1302 (`--splice` needs >= 2.29).
- Host: GRCh38-2024-A `fasta/genome.fa` and `genes/genes.gtf` from the same directory (one assembly). `--host-gtf` is needed for `strand_qc.tsv`; the DSR-02 rounds did not pass it.
- Arm: round 2026-11-02 `combined_off` (`combined_off_r2` for HSV-1 and GSM5725696, the recorded primary arms). Calls table: `target_verdict_calls.tsv`.
- Output: `data/runs/round_2026-11-04_target_verdicts/<dataset>/<sample>/evidence_splice/` (fresh; the sbatch refuses an existing directory). Not committed (bulk data).
- Verdict unit: molecule (CB+UMI). `molecule_verdict_summary.tsv` has scope `counted` (molecules counted in the run's matrix) and `all`.
- Job 25950550 (HPV16 SRR19537341 evidence) has no `--splice`, so HPV16 gets its own splice run here. The matched negative needs no evidence run
  (the command has no negative comparison); its state is read from the existing `viral_summary.tsv`.

### GSM5725696 subsample (KSHV induced)

`viralscan evidence` has no molecule-sampling option (`--sampling-seed` only seeds the 500-read BLAST sample), and the full library
(23,671,063 HHV-8 molecules, 26,981,294 target reads) ran out of memory at 24G and 48G. Package code is unchanged; the input is cut instead
(`scripts/target_verdict_subset.py`, job below):
1. Frame: `read_lineage.tsv.gz` of the earlier full replay (job 25952505 row 8, `_kshv/evidence_r2/_failed/...oom_25952505_8`), which lists every exact target read with `cb`, `ub`, `read_number`.
2. Draw 20,000 whole molecules (CB+UMI): a molecule's score is the first 8 bytes of `sha256("<seed>\0<cb>_<ub>")`, the 20,000 lowest scores are kept
   (the rule of the package's `sample_fasta_deterministic`, applied to molecules, independent of file order). **Seed 20261104.** All member reads of a chosen molecule are kept; never random reads.
3. Stream the real R1/R2 once and write only those records, in original order, to a new FASTQ pair
   (`.../GSM5725696/subset/subset_fastq/`; `sample_molecules.tsv` and `subset_manifest.json` list the draw).
4. A shadow run directory (`.../subset/subset_run/GSM5725696/`) has the primary `config.yaml` with `kb_r1`, `kb_r2`, `output` changed, and symlinks to the primary `results/` and the `kb-python` files evidence reads.
   `viralscan evidence` replays the subset pair against the same index and runs unchanged.

Result of the draw (job 25957773, COMPLETED in 14 min): 20,000 molecules, 22,186 target reads, from a frame of 26,981,294 reads; 290,744,863 FASTQ records streamed. Fractions from this library are over the sampled molecules (Wilson 95 % interval given); counts are not library totals. GSM5725695 (latent, 59,365 molecules), BC-1 (555,654), EBV (735,872) and the others run in full.

## Prior evidence: splice realignment of all viral reads (2026-11-03)

`data/runs/round_2026-11-02/_splice_realign_2026-11-03/splice_summary.tsv` (minimap2 2.31-r1302, `splice:sr`, all reads of the call, not only counted virus-best molecules; a different unit from the table below):

| Call | Contig | Annotation | Annotated introns | Reads | Aligned | Spliced reads | Spliced at annotated intron | Unique junctions | Annotated junctions seen |
|---|---|---|---|---|---|---|---|---|---|
| HSV-1 | NC_001806.2 | exon | 8 | 60,748 | 60,068 | 63 | 2 | 59 | 1 |
| EBV | NC_007605.1 | exon | 51 | 920,888 | 920,161 | 6,147 | 3,186 | 1,383 | 30 |
| HHV-6B | AF157706.1 | CDS | 6 | 3,474 | 3,466 | 160 | 0 | 50 | 0 |

EBV splices at annotated introns (30 of 51 junctions seen, 52 % of spliced reads at an annotated intron). HSV-1 has few spliced reads, as expected for a mostly unspliced genome. HHV-6B has CDS-only annotation, so no junction can match.

## Matched negatives (existing `viral_summary.tsv`, `combined_off`)

| Positive | Negative | HPV16 molecules | Called cells | Detected | Clean |
|---|---|---|---|---|---|
| SRR19537341 (raft, 7,673 molecules, 1,950 called cells) | SRR19537339 | 8 | 0 of 10,085 | False | yes |
| SRR13419165 (HN18, 562 molecules, 151 called cells) | SRR13418973 (HN01) | no HPV16 row | 0 | none | yes |

Also in `target_verdict_negatives.tsv`. KSHV, EBV, HSV-1 and HHV-6B libraries have no matched negative in this round.

## Results

Pending: the evidence jobs had not started when this note was committed. `target_verdicts.tsv` holds the table once they finish.

## To finish

Jobs (2026-11-04): subset 25957773 COMPLETED; libraries array 25957774 (rows 0-3,5-7: EBV, HSV-1, HHV-6B, GSM5725695, BC-1, HPV16, HN18) pending; GSM5725696 evidence 25957775 (row 4, on the subset) pending.
Per-job log: `data/runs/round_2026-11-04_target_verdicts/logs/r1104_tverdict_<array id>_<row>.log`.
When all rows are COMPLETED (`sacct -j 25957774,25957775`):
1. `VIRALSCAN_DATA=<repro>/data python scripts/target_verdict_collect.py` rewrites `target_verdicts.tsv` and `target_verdict_negatives.tsv`.
2. Replace "Results" above with the table (per library: counted and all virus-best / host-best / tie / unaligned counts and fractions, read verdicts, spliced molecules and annotated, strand status and fraction in expected orientation, host-homology flag, CONFIDENT or NOT CONFIDENT).
   Compare the splice columns with the prior-evidence table; EBV should show annotated splicing, HHV-6B cannot match junctions (CDS-only annotation).
3. Set the `TARGET-VERDICT-01` row in `PLAN.md` to done and list the verdicts.
A failed row leaves a partial directory: rerun with a new output name, never overwrite.
