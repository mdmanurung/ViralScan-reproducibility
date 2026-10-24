# HHV-6B retained-archive checklist (Q9), draft 2026-10-22

Scope: dataset `hhv6b` (GSE210063, 13 libraries, 12 SRA runs plus one local run for GSM6416035). Raw store FASTQs were
already deleted 2026-10-18 (12 runs, 387.0 GB, `status/deleted_hhv6b_2026-10-18.log`). Pending and ON HOLD (user,
2026-10-21): `delete_bus.py hhv6b`, 130 paths, 1072.5 GB. Nothing here was run: no delete script (not even a dry run),
no job submitted. All facts below were read from files; `T1` = `viralscan_work/trackA_round1`,
`REC` = `ViralScan/analysis/trackA_report_2026-10-18/recovery_2026-10-19`. Paths without a prefix are relative to `T1`.

## 1. What the pending deletion removes and keeps

Plan (REC/`hhv6b_delete_bus_dry_run_after_refresh.log`, scripts/delete_bus.py, default flags, no `--with-raw-bus`):

| Deleted | GB | Where |
|---|---|---|
| host_filtered/star_tmp | 488.7 | twostep arm (STAR scratch) |
| read_filtered/R1+R2.fastq.gz | 450.0 | combined_artefact arm |
| host_filtered/R1+R2.fastq.gz | 81.3 | twostep arm |
| output.resolved.sorted.bus.txt | 35.9 | combined_off (text of a kept BUS) |
| output.resolved.sorted.bus | 16.7 | artefact + twostep arms only |

Kept by script design (delete_bus.py docstring and asserts): raw `output.bus` + `output.unfiltered.bus` (all arms), combined_off
`output.resolved.sorted.bus`, `counts_unfiltered/*` (adata, adata_multimap, mtx, barcodes, genes, emptydrops_cells),
`read_filtered/fragment_lineage.tsv.gz` + `read_filter_audit.tsv`, host_filtered audit files, `matrix.ec`, `transcripts.txt`,
whitelist, `results/`, `config.yaml`, plots, `armP/`, `evidence/` (including 278.3 GB `lineage_bus`), `provenance/`.

## 2. Checklist: Biomni item vs what existing gates guarantee vs what is missing

Legend: COVERED = a gate or retained hash guarantees it; PARTIAL; MISSING.

### A. References and indexes

| Item | Status | Evidence (file / field) | Gap |
|---|---|---|---|
| Exact reference FASTA/GTF, targets, t2g, masks, index | COVERED | `provenance/global.json` `reference_cat42d.build_files` has bytes + sha256 for `viral.fa`, `combined.fa`, `combined.gtf`, `viral_panel.gtf`, `host/Homo_sapiens.GRCh38.116.gtf.gz`, `host_cdna.gtf`, `cdna.fa`, `lowcomplexity_mask.tsv`, `panel.idx`, `panel.t2g`, `catalogued_not_indexed.tsv`; per-run `run_manifest.json` `input_fingerprints` (`index:0`, `gtf:0`, `transcripts:0`) and `reference_fingerprint` | none for arm N. Confirm the per-library `reference_fingerprint` of `twostep` (f020656...) differs from combined_off (23129f0...) and that both reference trees are among the hashed files |
| Arm P reference (index, t2g, confirm proteins) | COVERED | `global.json` `armP_reference` (`-i`, `-g`, `confirm:*`, `confirm_ref:*`) with sha256 | none (arm P is complementary; no read-level confirmation requirement) |
| STAR host+virus index/ref used for the anellovirus STAR search | MISSING | `viralscan_work/star_hostvirus/{ref,index}` exist on disk; `star_hostvirus` is not mentioned in `global.json` or `provenance/hhv6b/*.json` | hash `ref/hostvirus.fa`, `hostvirus.gtf` and the STAR index `genomeParameters.txt`; add to global.json |
| Remote BLAST nt identity | PARTIAL | `evidence/*/blast_sampling.json` (seed 42, `lowest_sha256`, 500 reads) and `blast/reads_sample.fasta` retained; `evidence_manifest.json` hashes outputs | nt database version/date and competing hits per Q11 are not recorded in one provenance field; check `blast_identity.tsv` header |

### B. Inputs, relationships, commands, environments, seeds, decisions

| Item | Status | Evidence | Gap |
|---|---|---|---|
| Input accessions, run-to-library relationships | COVERED | `provenance/hhv6b/<lib>.json` `source_files[]` (path, role R1/R2, `lines`); `provenance/concat_plan_retained.tsv`; `provenance/download_receipts.tsv` (12 GSE210063 rows: SRA via prefetch 3.4.1 + `fasterq-dump --split-files --include-technical`, receipt state `done`) | provenance JSON field `download_source` is `null` for the 12 store runs (the facts live in the receipts table) |
| Checksums | PARTIAL | `source_files[].content_sha256` (decompressed stream) and `status/fastq_content_sha256.tsv`; delete_dataset.py check 5 required size = recorded gz_bytes, a recorded content hash and gzip magic before the 2026-10-18 deletion | Reproduction proof exists for 1 of 12 runs only: spot-check `status/spotcheck_ok/trackA_GSE210063__SRR20710645` (log `logs/tA_spotcheck_25825916.log`: both streams MATCH, 182,529,876 lines each, exit 0). The other 11 runs are protected by ENA/receipt checks only |
| ENA read-count equality | PARTIAL | Matched for the 96 deletable runs on 2026-10-17 (deletion-protocol memory); gate was delete_dataset.py check 5 | Current `provenance/ena_readcount_check.tsv` has 0 GSE210063 rows (regenerated for on-disk runs); the 2026-10-20 refresh (`REC/ena_readcount_refresh_verified.json`, 168 accessions) covers HSV-1 + HNSCC only and states `content_hash_redownload_proof: false`. Regenerate the HHV-6B rows (needs network; `scripts/check_ena_readcounts.py`) and keep them with the archive. Cross-check: lines/4 equals SRA spots (45,632,469 for SRR20710645) |
| GSM6416035 local run SRR20710641 | PARTIAL | `source_files` marks `local_not_downloaded_by_round: true`, `download_source: existing local copy (not re-downloaded)`, content hashes recorded; files are outside the store (`ViralScan/benchmark_inputs/reference_strategy/SRR20710641`) and neither script touches them | no download receipt or ENA row for this run; keep the benchmark_inputs copy until that run is receipted or spot-checked |
| Lane/sample relationships | COVERED | `source_files` order + concat plan; `chemistry_json` (path, sha256); per-run `chemistry_detection` in `run_manifest.json` (10xv2, 5p, on-list match rates) | none |
| Exact commands | COVERED (kb), PARTIAL (rest) | `kb-python/kb_info.json` `call` + `commands` (kallisto bus, bustools sort/inspect/correct/sort/count), `run_manifest.json` `options`, `config.yaml`; arm P `armP.command`; `evidence/*/sibling_specific.json`; `REC/*.smk` | STAR host-filter and anello STAR commands live in logs and receipts, not in one index; list them in the archive manifest |
| Environments, tool versions | COVERED | `global.json` `environments` (`viralscan_bench`, `viralscan_test_full`, sha256 + `provenance/env/*.txt` snapshots including star 2.7.11b, minimap2 2.31, samtools 1.23.1), `tools` (kallisto 0.52.0, bustools 0.45.1, sha256), `pinned_code` (commit 97a64f6, build sha256), `round_snapshot.tar.gz` sha256 3b68256... | confirm `round_snapshot.tar.gz` still exists and its sha matches before the hold is released |
| Seeds | COVERED | emptyDrops seed 100, niters 10000 (`config.yaml`, GUARD.md); BLAST sampling seed 42 | none |
| Filtering and cell-calling decisions | COVERED | `status/cells/<lib>.{tsv,barcodes.txt}` (read-only files) and `frozen_cells` sha256; `results/called_cells.tsv`, `cell_calling_input.json`, `emptydrops_cells.tsv` retained; GUARD.md rules (host-only emptyDrops, FDR 0.01, lower 100) | none |

### C. Matrices, calls, QC, logs, evidence for accepted and rejected candidates

| Item | Status | Evidence | Gap |
|---|---|---|---|
| Full count matrices | COVERED | 7 hashed files per library in `status/retained_outputs.tsv` and `provenance/<lib>.json` `retained_outputs` (adata.h5ad, mtx, barcodes, genes, called_cells, per_cell_viral, armP adata); 91/91 verified present 2026-10-18; delete_bus.py asserts `counts_unfiltered` and `armP/` are never in the plan | `adata_multimap.h5ad` and `emptydrops_cells.tsv` are kept by design but are not among the 7 hashed files |
| Called-cell lists | COVERED | `status/cells/`, `called_cells.tsv` (hashed) | none |
| QC and logs | PARTIAL | `count_audit.tsv`, `results/*` (viral_summary, sensitivity, multimap_evidence, virus_identity, positive_control, control_receipts), `log/`, `report.html`, `host_filter_audit.tsv`, `read_filter_audit.tsv` retained | retained but not hashed |
| Evidence, accepted and rejected | COVERED | 69 `evidence/hhv6b__*` directories; readiness requires a pinned verdict AND a tier row for every combined_off call (GUARD.md 2026-10-15), so host_best / artefact / no_support calls are retained, not only accepted ones; `status/deletion_readiness.tsv`: 13/13 READY (n_evidence_calls 2 to 11 per library); each dir has `evidence_manifest.json` with output hashes, plus sibling-specific receipts | `evidence/calls.tsv`, `verdicts.tsv`, `tiers.tsv`, `sibling_specific.tsv` are shared across datasets and were rewritten on 2026-10-20 (08:46-08:48), which is what staled the earlier window (see section 3) |
| Anellovirus scope result (STAR-based, scoped NEGATIVE) | PARTIAL | `REC/hhv6b_anello_verified.json` (26 searches, 13 libraries, all real BAMs verified empty, STAR input counts match retained host-filter audits, 5 primary kallisto anello calls, 0 passing the q137 rule), `REC/hhv6b_anello_full_depth_checks.tsv` (BAM, STAR Log.final.out and host-filter audit sha256 per library/setting), controls with 0.952 shipped and 0.965 relaxed recovery at 600 planted molecules | `fastqs_independently_recounted: false`. The STAR input pairs are the host_filtered R1/R2 that this deletion removes, with no content hash recorded (see D). Wording to keep: scoped to indexed genomes and preregistered gates; computational detection threshold is source/background/layout-specific |
| Molecule-level replays | PARTIAL | `REC/molecule_assignment_receipts/*__GSM6416024.json`, `REC/molecule_replay_inventory.tsv` (export sha256, `source_inputs_rehashed_unchanged: True`) | `REC/molecule_assignments.smk` `source_files()` reads `kb-python/output.resolved.sorted.bus.txt` for GSM6416024, which the plan deletes. Packet flag `dependent_molecule_replays_must_finish_before_deleting_bus_text: true`. The text is regenerable (bustools text of the kept combined_off resolved.sorted.bus, as in multimap.py) but no hash of the text is retained, so byte-identity of a regeneration cannot be shown after the fact. Hash the 13 text files first, or fold this into the replay below |

### D. Relevant read pairs, ambiguity and host-competition evidence

| Item | Status | Evidence | Gap |
|---|---|---|---|
| Reads behind each call | PARTIAL | `evidence/*/viral_reads.fasta`, `viral_reads.umi_dedup.fasta`, `competitive_reads.{raw,umi_dedup,deduplicated.tagged}.bam`, `read_lineage.tsv.gz`, `molecule_support.tsv`, `sibling_specific.{reads,molecules}.tsv.gz`, `target.bus` (about 7 GB per evidence dir) | not verified here: whether CB/UMI of each retained viral read is recoverable (the FASTA is the cDNA side; the CB/UMI side would be in the lineage tables) |
| Ambiguity / host competition | COVERED (summary), PARTIAL (reads) | `results/multimap_evidence.tsv`, `host_homology_loci.tsv`, `count_audit.tsv` (host_virus_ambiguous_molecules), `evidence/*/competitive_alignment.*`, `alignment_qc.tsv`, `interpretation_flags.tsv`; combined_off raw + resolved BUS kept, `lineage_bus` kept | read_filtered FASTQs (artefact arm) and host_filtered FASTQs (twostep arm) are the only full-read copies of the host-filter decision and are about to go; the audits keep counts and `fragment_lineage.tsv.gz` keeps per-fragment lineage, but no content hash of those FASTQs exists |
| 125 kb peak kallisto miss | MISSING (open) | memory `hhv6b-deletion-hold`: 1.8M STAR reads vs about 100x fewer by minimap2, lost at the kallisto selection step; STAR outputs in `viralscan_work/star_hostvirus/GSM6416022` (3.1 GB) and `covmap_hhv6b` | investigation unfinished; this is the reason for the hold. A precondition rather than an archive gap: release only after it is explained and its outputs (and any reads sampled for it) are registered in provenance |

## 3. Gate state for HHV-6B today (read from files only)

- Readiness: `status/deletion_readiness.tsv` 13/13 READY (mtime 2026-10-20 22:48).
- Window: `status/window_open_hhv6b` mtime 2026-10-20 22:48; newest shared evidence table 2026-10-20 08:48 (`evidence/consistency.tsv`;
  the four tables in delete_bus.py `EVID` are older); provenance JSONs 2026-10-20 22:48. By mtime the freshness test would pass today, but the
  recorded dry run (`REC/hhv6b_delete_bus_dry_run_after_refresh.log`) was refused for a stale window and no later dry run is on file.
  A fresh dry run is the user's command; I did not run it.
- Spot-check: `trackA_GSE210063__SRR20710645` present (series-level, 1 run).
- delete_bus.py logs path and bytes only, not content hashes (delete_dataset.py logs both).
- `deletion_authorized: false` in `REC/hhv6b_deletion_packet_20261020.json`.

## 4. Gaps, ranked

1. No demonstrated replay from the retained archive (Biomni item). Proposed in section 5.
2. No hashes for the BUS-stage files the archive depends on: `output.bus`, `output.unfiltered.bus`, `output.resolved.sorted.bus`, `matrix.ec`, `transcripts.txt`, `10x_version2_whitelist.txt`, `kb_info.json`, and the 13 combined_off `.bus.txt` files (the one deleted category with a dependent replay).
3. Deleted FASTQ-type files (read_filtered R1/R2, host_filtered R1/R2) have no recorded content hash; the anello STAR search used host_filtered pairs and was not re-counted from FASTQs.
4. Read-level reproducibility is demonstrated for 1 of 12 SRA runs; ENA read counts for GSE210063 are not in the current check table; SRR20710641 (GSM6416035) has no receipt and lives outside the store.
5. STAR hostvirus reference/index and BLAST nt version/date are not in `global.json`.
6. 125 kb kallisto miss not explained (hold precondition).
7. Retained-but-unhashed: `adata_multimap.h5ad`, `emptydrops_cells.tsv`, `results/*`, `count_audit.tsv`; evidence hashes exist only inside each `evidence_manifest.json`.
8. delete_bus.py log has no hashes.

## 5. Cheapest single replay from the retained archive

Choice: GSM6416031 (smallest raw BUS in the dataset: `output.bus` 478 MB, `output.unfiltered.bus` 34.6 MB; 729,229 input molecules), combined_off, BUS stage to count matrix.
Rationale: it uses only items the plan keeps. It re-derives `output.unfiltered.bus` and the full count matrix from raw `output.bus`
with the recorded kb commands (kb_info.json: sort, correct, sort, count), compares against the hashed retained matrix
(`status/retained_outputs.tsv`: mtx ce7490965611bcb2995ba71b27d1af32195a8f69e04c531c5be47bc21eaef28e, barcodes 7856c3e61b66..., genes 86f1bfcded23...),
and regenerates the `.bus.txt` that the plan deletes, compared byte-for-byte before deletion.
Expected cost: a few minutes, 4 CPUs, 8 GB, under 2 GB of scratch (estimate, not measured).

What it proves: the retained BUS + ec/transcripts/whitelist + pinned bustools 0.45.1 reproduce the matrix and the text export that the deleted files represent.
What it does not prove: reads to BUS (kallisto bus). That step relies on re-download; the single spot-check shows a 1-run content hash reproduces. A full read replay (roughly 15 GB of reads for this library, kallisto bus, plus download) is the optional extension, not the minimum.

Run by the user (nothing here has been submitted). Output goes to a new directory; the script refuses if it exists and writes no existing file.

```bash
M=/exports/archive/hg-funcgenom-research/mdmanurung
R=$M/viralscan_work/trackA_round1
sbatch -p short -c 4 --mem=8G -t 00:30:00 -J tA_replay_hhv6b_GSM6416031 \
  -o "$R/logs/%x_%j.log" --wrap '
set -euo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
R=$M/viralscan_work/trackA_round1
BT=$M/conda/envs/viralscan_bench/lib/python3.11/site-packages/kb_python/bins/linux/bustools/bustools
K=$R/runs/hhv6b/combined_off/GSM6416031/GSM6416031/kb-python
O=$R/replay_2026-10-22/hhv6b_GSM6416031
[ -x "$BT" ] || { echo "no bustools at $BT"; exit 2; }
[ ! -e "$O" ] || { echo "refuse: $O exists"; exit 2; }
mkdir -p "$O/tmp" "$O/counts_unfiltered"
"$BT" sort -T "$O/tmp" -t 4 -m 2G -o "$O/s.bus" "$K/output.bus"
"$BT" correct -w "$K/10x_version2_whitelist.txt" -o "$O/s.c.bus" "$O/s.bus"
"$BT" sort -T "$O/tmp" -t 4 -m 2G -o "$O/output.unfiltered.bus" "$O/s.c.bus"
"$BT" count -o "$O/counts_unfiltered/cells_x_genes" -g "$M/viral_ref_cat42d/build/panel.t2g" -e "$K/matrix.ec" -t "$K/transcripts.txt" --genecounts --umi-gene "$O/output.unfiltered.bus"
"$BT" text -o "$O/resolved.sorted.bus.txt" "$K/output.resolved.sorted.bus"
rc=0
cmp "$O/output.unfiltered.bus" "$K/output.unfiltered.bus" && echo "MATCH output.unfiltered.bus" || { echo "DIFFER output.unfiltered.bus"; rc=1; }
cmp "$O/resolved.sorted.bus.txt" "$K/output.resolved.sorted.bus.txt" && echo "MATCH resolved.sorted.bus.txt" || { echo "DIFFER resolved.sorted.bus.txt"; rc=1; }
for f in mtx barcodes.txt genes.txt; do
  got=$(sha256sum "$O/counts_unfiltered/cells_x_genes.$f" | cut -d" " -f1)
  want=$(awk -F"\t" -v p="runs/hhv6b/combined_off/GSM6416031/GSM6416031/kb-python/counts_unfiltered/cells_x_genes.$f" "\$2==p {print \$4}" "$R/status/retained_outputs.tsv")
  [ "$got" = "$want" ] && echo "MATCH cells_x_genes.$f $got" || { echo "DIFFER cells_x_genes.$f got=$got want=$want"; rc=1; }
done
sha256sum "$O/output.unfiltered.bus" "$O/resolved.sorted.bus.txt" > "$O/replay_hashes.sha256"
echo "replay exit $rc"; exit $rc'
```

Pass rule: all five lines MATCH and exit 0. A DIFFER on the matrix is a finding to record, not to tune away (REPRODUCE.md step 7). Intermediates `s.bus`, `s.c.bus` and `tmp/` stay in the replay directory for the user to remove (the script deletes nothing).
Caveats: the retained_outputs.tsv column layout is `library, path, bytes, sha256`, so the awk lookup uses columns 2 and 4; the bustools path is the one recorded in kb_info.json (viralscan_bench kb_python binary); its existence was not checked and it was not executed (the script exits 2 if it is missing).

## 6. Proposed order before the hold is released (user decides)

1. Run the replay (section 5); keep its log and `replay_hashes.sha256`.
2. Hash the BUS-stage set and the 13 combined_off `.bus.txt` into `status/retained_outputs.tsv` (or a new `retained_bus_sha256.tsv`), so a later regeneration can be compared.
3. Add STAR hostvirus ref/index and BLAST nt identity to `provenance/global.json`.
4. Regenerate HHV-6B ENA read-count rows; decide whether to spot-check a second run, given deletion is irreversible.
5. Explain the 125 kb peak; register its outputs.
6. Fresh `deletion_window.sh hhv6b --yes`, then a `delete_bus.py hhv6b` dry run, then the user's decision on `--yes`.

## 7. Replay result (2026-10-22, job 25865103)
PASS 5/5: output.unfiltered.bus and resolved.sorted.bus.txt byte-identical; cells_x_genes mtx/barcodes/genes sha256 equal to retained_outputs.tsv (the job printed DIFFER only because retained_outputs.tsv has CRLF line endings; digests identical after stripping '\r'). Details: `viralscan_work/trackA_round1/replay_2026-10-22/hhv6b_GSM6416031/REPLAY_RESULT.md`. Gap 1 closed; gaps 2-8 remain for the user's release decision.

## 8. Gaps 2 and 5 closed (2026-10-22)
- Gap 2 CLOSED: job 25866177 hashed 408 files (219,805,882,254 bytes) into `status/retained_bus_sha256_hhv6b_2026-10-22.tsv` (LF; library, arm, path, bytes, sha256, hashed_at): 130 each for combined_off, combined_artefact, twostep (all BUS-stage files incl. the 13 combined_off `.bus.txt`) and 18 `star_hostvirus_ref` files. Cross-check: the replay's regenerated GSM6416031 `output.unfiltered.bus` (880050d2…) and `.bus.txt` (a8734255…) equal the recorded hashes of the retained originals.
- Gap 5 CLOSED (with two UNRECORDED fields): `provenance/global_addendum_2026-10-22.json` records the STAR host+virus reference/index (large-file sha256 in the TSV above), STAR 2.7.11b binary, and the Track B read-check BLAST (qblast megablast core_nt, 2026-10-22). UNRECORDED: the database/version of the original Track A candidate BLAST, and the core_nt release. `global.json` deliberately untouched (deletion-window gate reads provenance mtimes).
- Remaining for the user's release decision: gap 3 (no content hash of the read_filtered/host_filtered FASTQs slated for deletion), gap 4 (ENA read counts for GSE210063; second spot-check), gap 6 (125 kb peak now explained by F-027: gene-only CDS models without 3' flank; register F-027 as the explanation), gaps 7-8 (unhashed retained h5ad/results; delete_bus.py logs no hashes).
