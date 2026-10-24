# ViralScan Track A: what the report can and cannot claim

Scope: hsv1, hhv6b, hpv16, ebv and hnscc_gse164690. Tonsil was cancelled and is excluded throughout.

I re-checked the headline tier, molecule and cell numbers against `evidence/tiers.tsv`. Everything else comes from the audit and skeptic JSON and was not re-verified. The tables only carry `combined_off` evidence, so every tier below is for that arm.

Two counting conventions appear in the data. `calls.tsv` gives multimapper-weighted molecules and `tiers.tsv` gives `counted_virus_best`. They differ, for example EBV GSM4796272 is 73,091 versus 85,633, and HSV-2 GSM3511334 is 10,353.8 versus 15,351. The report must name which one it quotes. I use `tiers.tsv` below.

## 1. Recovery of previously reported viruses

The `expected` flag in `calls.tsv` is unusable for hsv1 and hpv16 (false on every row). For hnscc it is a regex that flags any papillomavirus, including HPV29 and HPV118. All expected viruses below come from `PLAN.md`, `BENCHMARK_COMPARISON.md`, `showcase_runbook.md`, dossier files and approved labels. None was checked against the original paper text.

| Dataset | Expected virus | Libraries supported / total | Caveats |
|---|---|---|---|
| hsv1 (GSE123782, Wyler 2019, NHDF fibroblasts) | HSV-1 | **14/14 infected libraries called at any tier, 7/14 at `supported`**. 5/5 uninfected libraries have no HSV-1 call. The 19 single-cell libraries have 7 `supported` and 7 `supported_partial` for HSV-1. | The 7 `supported` libraries are all 3 to 5 hpi (GSM3511319, 326, 327, 332, 333, 334, 335). The 7 `supported_partial` are 1 hpi and early 3 hpi libraries. GSM3511322 and 323 are `clade_only` with 0 HSV-1-specific molecules, and GSM3511330 has 1. The 21 bulk runs (GSM3511297–316) were deleted and have no calls. |
| hhv6b (GSE210063, Lareau 2023, CAR-T) | HHV-6B | **12/13**: 11 `supported`, 1 `supported_partial` (GSM6416028, 598 molecules, breadth 0.155). GSM6416026 is `no_support`. | The audit found no per-library infection or control status. GSM6416026 cannot be called a true negative, and its arm P result agrees (6 barcodes at ≥10 UMI). The accession GSM6416025 is absent from the manifest and unexplained. Ambient RNA is heavy in several libraries (GSM6416022 47%, GSM6416033 7%), so the 16,237 "cells" in GSM6416022 is not an infected-cell count. |
| hpv16 (GSE189670, Bedard 2023) | HPV16 in the HPV16 raft, about none in the parental raft | **1/1 positive, 0/1 negative called, as expected.** GSM5705760 is `supported` (12,995 molecules, 2,913 cells, breadth 0.82). GSM5705759 has no HPV16 call (16 background molecules, 0 called cells). | Two libraries only, so it is a single-pair qualitative control and gives no sensitivity or specificity estimate. The truth statement is qualitative, from `PLAN.md` EXPL-HPV16. There is no swap or index-hopping check. |
| ebv (LCL, GSE158275) | EBV | **3/3** `supported` (725,788, 85,633 and 16,595 molecules; 2,482, 1,738 and 3,135 cells). | Support rests on user-approved labels. It is not a blinded truth set, and the original paper was not read. FASTQs were deleted, so no raw-read re-analysis is possible. Do not report an EBV type (see section 3). |
| hnscc_gse164690 (HPV+ and HPV- tumours) | HPV16 in HPV+ tumours | **2 libraries `supported`** (GSM5017071 HN18 CD45-, 826 molecules, 187 cells; GSM5017059 HN14 CD45-, 2,597 molecules, 694 cells), **plus 1 unassessed** (GSM5017065 HN16 CD45-, 9,834 called molecules). Of 34 analysed libraries, 31 have no HPV16 call. | The dataset is incomplete (see section 3). HN01 CD45- (GSM5017023) is the one documented HPV- negative and has no HPV16 call. HPV29 (artefact, `host_best`) and HPV118 (`no_support`) are not detections despite the `expected` flag. |

## 2. Beyond the expected virus

### (a) Surviving off-target detections (≥2 of 3 skeptics did not refute)

Only one item survives, and it is not an infection call.

- **HIV-1, `locus_restricted`, hhv6b** (GSM6416023, 024, 027, 028, 029, and the weak GSM6416032). Two of three skeptics did not refute it, because the sequence is real.
  - `tiers.tsv` counted molecules are 1,349, 4,078, 2,350, 3,427, 3,168 and 29, in 834, 2,101, 1,458, 2,655, 2,115 and 29 cells.
  - 83–86% of molecules fall in one window. Breadth is only about 0.15–0.18.
  - Host homology, low complexity and sibling ambiguity are all not flagged, and identity is about 99%.
  - The coverage pattern looks like LTR, cPPT and RRE fragments, which fits a lentiviral transfer vector. That reading is the skeptics' inference from memory of HXB2 positions, not an annotation check.
  - The only approved label is for GSM6416035, which is an artefact of the infection interpretation (vector). GUARD.md notes that vector sequence can pass `viral_best` while failing an infection interpretation.
  - Allowed wording is "HIV-1-derived, locus-restricted, probably lentiviral-vector sequence; infection not established". Do not list it as a virus detection.
  - GSM6416032 (29 molecules in 29 cells) is not established and should be marked unresolved.

### (b) Refuted off-target detections

| Call | Libraries | Skeptic votes (refuted of 3) | Refutation reason |
|---|---|---|---|
| HSV-2, hsv1 | 10 libraries, all `clade_level`; molecules rise from 5 to 19,831 | 3 of 3 | HSV-1 reads cross-map to the sibling HSV-2 reference. HSV-2-specific molecules and cells are 0 in all 10 libraries, while HSV-1-specific molecules run into the thousands. Breadth is 0.001–0.053 versus 0.25–0.75 for HSV-1. Arm P labels taxon_10310 `misassigned_virus` (GSM3511334 and GSM3511335). Report it as "HSV clade-level / HSV-1 cross-mapping". |
| HHV-6A tier `supported`, hhv6b | GSM6416023, 024, 027, 031, 032 | 3 of 3 | The 6A-specific molecules (51, 181, 18, 8 and 21) are about 0.3–0.6% of HHV-6B and about 0.7–2.4% of the 6A+6B-specific molecules. Every 6A-specific cell is also an HHV-6B cell. Some 6A-specific molecules share their cell barcode and UMI with HHV-6B molecules (9/51, 37/181, 6/18, 4/8 and 17/21). The tier note itself says "provisional_panel_label_discrimination_not_infection". |
| HHV-6A tier `clade_level`, hhv6b | GSM6416022, 029, 030, 034 | 3 of 3 | 0–1 6A-specific molecules, `clade_only`. 6A is 0.09–0.5% of 6B. Identity is 96–97% to 6A versus 99.2% or more to 6B. |
| HIV-1, `supported_partial`, hhv6b | GSM6416026, 033, 034, 035 | 2 of 3 (the homology lens did not refute) | The signal is the same locus-restricted footprint as in (a), at a low count. In 033, 034 and 035 only 19–33% of molecules sit in frozen cells, and the counts are 12, 7 and 8. GSM6416035 carries the approved vector/artefact label. GSM6416026 (409 molecules, 373 cells) is the only solid library, and even it has a hotspot flag. Treat it as the same vector-like sequence as in (a), not an infection. |
| Vaccinia, `supported_partial`, hnscc | GSM5017040, 041 (`insufficient` in 7 more libraries) | 2 of 3 | `supported_partial` rests on 5 and 3 counted molecules in 3 and 2 cells. Only about 1% of molecules are in frozen cells, with `soup_sufficient`. The sequence is real (99.7% identity to one reference), but it is ambient or reagent-level material, not cell-associated infection. |

Open inconsistencies in these refutations:

- **Vaccinia arm P.** Skeptics disagreed on the arm P numbers for taxon_10245 (410 vs 11 in-cell UMI in GSM5017040; 234 vs 13 in GSM5017041). The homology skeptic reproduced them from the count matrices. The read-level and ambient skeptics could not find the taxon in the summaries. Do not cite the arm P Vaccinia numbers until this is settled.
- **HHV-6A bleed model.** Bleed does not predict the pattern cleanly. GSM6416022 has the most HHV-6B but only 1 A-specific molecule, where roughly 190 would be expected from the other libraries' rate. Cross-mapping is the best explanation. HHV-6B strain divergence from the reference or a trace of true HHV-6A are not excluded.
- **HSV-2 and HHV-6A counts.** The counts in the audit notes differ from `tiers.tsv`, but the conclusion does not change.

### (c) Arm P / PalmDB findings

**Specific, library-restricted:**
- HSV-1 (taxon_10298) in the 3–5 hpi libraries. It is `viral_supported` in exactly 7 libraries (GSM3511319, 326, 327, 332, 333, 334, 335). In GSM3511334 it has 1,094,955 UMIs and 77 proteins.
- HHV-6B (taxon_32604) is present in all 13 libraries by UMI. It is `viral_supported` in 7 (GSM6416022, 023, 024, 027, 030, 031, 032). The other 6 have no confirm row for it.
- HPV16 (taxon_333760) in hpv16 GSM5705760 has 15,808 UMIs in 3,909 barcodes, versus 18 UMIs in GSM5705759.
- EBV (taxon_10376) is `viral_supported` in GSM4796271 and `mixed` in 272 and 273. The EBNA-2 groups are host-derived.
- HPV16 in hnscc has 3 libraries by arm P (GSM5017065 12,024 total UMIs, GSM5017059 3,371, GSM5017071 1,005). Its confirm-group status is unknown. This is the audit's own parse of the retained matrices, not a pipeline output.

**Not specific (do not report as findings):**
- Present across libraries and host-derived, low-complexity or adapter artefacts in confirm:
  - palmdb_u202260 (all 19 hsv1 libraries and the other datasets);
  - HCMV pp71;
  - HPV83 replication protein;
  - EBNA-2;
  - HPV3 envelope;
  - Cercopithecine HSV-2 ICP0;
  - HHV-8 LANA.
- palmdb_u101227 / u226460 (Picornaviridae RdRp) is `protein_only_viral`, with 93–94% TSO-adapter reads, and appears at higher counts in the HPV-negative hpv16 library. It is an artefact signature.
- palmdb_u100644 in ebv is diffuse, at about 1–3 UMI per barcode.
- No PalmDB RdRp hit is promoted to a finding (arm P is complementary evidence, not a confirmation-limited arm; reframed 2026-10-22). There are no novel-virus claims.
- Weakly library-enriched, unconfirmed and untraced candidates:
  - palmdb_u100592 in hnscc GSM5017041 (587 UMIs in 258 cells);
  - the hhv6b S-group (GSM6416030–035) features: Molluscum MC158R, u237705, and Orthomyxoviridae PalmDB hits such as u103829. These look like a batch effect.
  - Molluscum MC158R is classed `host_derived` or low-complexity elsewhere but `protein_only_viral` in the hhv6b S-group. That inconsistency is unexplained.

## 3. Statements the data do NOT support

- **Detection thresholds are provisional and not blind-validated.** Tier rules, the sibling AS margin of 18, and the single-window and hotspot rules are not validated at the calibration gate (GUARD.md). Do not call the benchmark blind or the thresholds locked.
- **Expected-virus truth is not independent of the pipeline authors.** It comes from internal docs and approved labels. The approved label set is small (one library) and not blinded. The original papers' per-library statements were not retrieved for any dataset.
- **No sensitivity or specificity can be computed for hnscc, hhv6b or hpv16.**
  - hnscc: per-patient HPV status is known only for HN18 (HPV+) and HN01 (HPV-).
  - hhv6b: per-library infection status is not available.
  - hpv16: only one positive and one negative library.
  - hsv1 gives only a labelled 14-infected / 5-uninfected comparison, with labels taken from GSM titles.
- **Tonsil was cancelled.** There are no tonsil results, and none may be claimed.
- **hnscc is incomplete.**
  - 34 of 51 libraries are analysed, and 17 are still waiting for download (HN06 CD45+/-, HN07, HN08 PBL, HN12 CD45+/-, HN13, HN14 PBL, HN17, HN18 PBL and CD45+). HN13 and HN17 have no analysed library.
  - GSM5017065 has 7 of 7 verdicts and tiers missing. Its HPV16 tier, cell count and evidence directory do not exist, and its `combined_artefact` arm was not done.
  - GSM5017064 has 1 tier missing.
  - 6 of 34 libraries are blocked, and evidence, provenance and `combined_artefact` jobs were still pending when audited. Counts may change.
- **Only `combined_off` is tiered.** `combined_artefact` and `twostep` are complete for most libraries but not tiered. Off-target calls in those arms are untested, for example twostep HPV77 with 267 molecules in 239 called cells in hpv16 GSM5705760 (1 molecule in `combined_off`). "No off-target virus in any arm" cannot be claimed.
- **No co-infection claim:** HSV-2 in hsv1 and HHV-6A in hhv6b are not co-infection claims.
- **No infection claim for HIV-1 in hhv6b.** The vector reading beyond GSM6416035 is inference.
- **No HSV-1 specificity claim in HSV-1 libraries GSM3511322, 323 and 330.** The HSV-1 sibling status there is `clade_only` or has near-zero specific molecules.
- **No EBV type claim.** Type 2 is `clade_level` in GSM4796273. In GSM4796271 it has only 3 specific molecules. In GSM4796272 the audit gives 4,233 type-2-specific molecules versus 455 type-1-specific, so the type assignment is unresolved.
- **Numbers that are not infected-cell counts.**
  - In ambient-dominated libraries the tier `cells` column is the number of frozen cells with counted virus molecules, not infected cells.
  - GSM6416033 carries the flag `cell_set_vs_viral_barcode_count_unreconciled`. The 438-barcode figure reproduces, the "31 called cells" figure does not.
- **Arm P is complementary to the nucleotide arm (reframed 2026-10-22).** It is a protein-level search and does not need read-level confirmation to be useful. The confirm step covers the top 20 groups per library by design; that is a scope note, not a weakness of arm P, and shared references with arm N are not cited as one. The caveats that stand are specificity: the unmasked index in kallisto 0.50.0 and HSV-1 cross-mapping to HSV-2.
- **Raw reads are gone.** FASTQs were deleted for ebv, hhv6b and others. No read-level re-analysis is possible beyond retained evidence directories.
- **No index-hopping or swap check.** `swap_check.py` needs a pool manifest and was never run. The `soup_sufficient` notes are descriptive and do not show infection.

## 4. Additional analyses needed before submission

1. **Finish hnscc.**
   - Complete GSM5017065 evidence, verdicts and tiers, and GSM5017064's missing tier.
   - Finish provenance for the 6 blocked libraries and the `combined_artefact` arm for 062 and 065.
   - Download and run the 17 pending libraries, or state the 34/51 cap explicitly.
   - Re-freeze `calls.tsv` and `tiers.tsv` afterwards.
2. **Obtain independent ground truth.**
   - Pull per-patient HPV status for hnscc (6 HPV+ / 12 HPV-) and per-library infection status for hhv6b (including GSM6416026, and the missing GSM6416025) from the papers and GEO.
   - Verify every expected virus against the paper text, using `verify-references`. Then compute per-library sensitivity and specificity, with the label source stated.
3. **Tier the other arms.** Run evidence tiers on `combined_artefact` and `twostep` for all five datasets, or enumerate their calls explicitly. Resolve the hpv16 twostep HPV77 call (267 molecules).
4. **Resolve HHV-6A.** Check A-specific read identity and locus clustering, and test HHV-6B strain divergence against the reference. Say why GSM6416022 shows 1 A-specific molecule where about 190 would be expected. Until then report only "HHV-6B with 6A cross-mapping".
5. **Vector-decoy check for HIV-1 in hhv6b.** Add lentiviral-vector decoys, confirm the LTR/cPPT/RRE footprint against an annotation, and label the remaining libraries. Decide GSM6416032 (29 molecules). Defer to recalibration/G3 only if the report omits the infection wording.
6. **Resolve the Vaccinia arm P discrepancy.** Reconcile the arm P taxon_10245 counts, and test pool or lab sources of the 9-library recurrence. Run the swap check with pool manifests for hnscc, hhv6b and hpv16.
7. **Arm P follow-ups (reframed 2026-10-22: optional scope extensions, not gaps in arm P).**
   - Optionally extend confirm to HPV16 (hpv16 and hnscc, including GSM5017065), HHV-6B in the 6 libraries without a confirm row, and HSV-1 in the 12 libraries without a confirm group.
   - Check whether the earlier HHV-6B confirm out-of-memory retries (rows 51, 52, 55) finished.
   - Trace the hhv6b S-group batch features (Molluscum MC158R, u237705, Orthomyxoviridae PalmDB). Decide whether to describe them as a batch effect, and read-confirm palmdb_u100592 in hnscc GSM5017041.
8. **Provenance and cross-checks.**
   - Resolve the counting-scope differences, `calls.tsv` versus `tiers.tsv` versus arm P UMIs, and fix one convention.
   - Fix the join-key mismatch for Yaba-like disease virus (hyphen versus underscore).
   - Check the ambient-dominated cell counts against a decontaminated cell set.
9. **Validation at the calibration gate.** Run the provisional tier rules on a held-out set before any blind-benchmark claim. Until then, call the analysis a development-set recovery check and state the 14/14 and 5/5 hsv1 result as labelled-infected versus labelled-uninfected only.
10. **Reporting.**
    - Add per-dataset tables with the section 1 caveats.
    - Mention the manuscript has no HSV, HHV-6, HPV16, EBV or HNSCC text yet (a grep found nothing).
    - Archive the matrices and results retained after FASTQ deletion.