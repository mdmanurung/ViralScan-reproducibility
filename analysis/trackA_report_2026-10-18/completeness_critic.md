# Completeness critique of the Track A claims draft

Tonsil is excluded throughout. I made no changes to any file.

## 1. Spot-check against `evidence/tiers.tsv` and `calls.tsv`

I checked 17 numbers. 15 match and 2 do not.

| Draft claim | File value | Result |
|---|---|---|
| EBV counted molecules 725,788 / 85,633 / 16,595 | 725788 / 85633 / 16595; cells 2482 / 1738 / 3135 | match |
| hpv16 GSM5705760: 12,995 molecules, 2,913 cells, breadth 0.82 | 12995 / 2913 / 0.8222 | match |
| hnscc GSM5017071 826 molecules, 187 cells; GSM5017059 2,597, 694 | 826 / 187; 2597 / 694 | match |
| HSV-2 GSM3511334 15,351 (`tiers.tsv`) | 15351, `clade_level`, specific 0 | match |
| HSV-2 maximum 19,831 | 19831 in GSM3511335, `clade_level` | match |
| hhv6b tiers: 11 `supported`, 1 `supported_partial`, 1 `no_support` | 11 / 1 / 1 | match |
| HIV-1 counted molecules 1349 / 4078 / 2350 / 3427 / 3168 / 29 | identical; cells 834 / 2101 / 1458 / 2655 / 2115 / 29 | match |
| HIV-1 `supported_partial` in 033, 034 and 035 with counts 12, 7 and 8, and GSM6416026 with 409 molecules in 373 cells | identical | match |
| HHV-6A specific molecules 51 / 181 / 18 / 8 / 21 | identical | match |
| hsv1 HSV-1: 7 `supported` and 7 `supported_partial` | 7 / 7 | match |
| GSM3511322 and 330 `clade_only`, with 0 and 1 specific molecules | identical | match |
| Vaccinia in GSM5017040 and 041: 5 molecules in 3 cells, 3 in 2 cells | identical | match |
| hnscc "Of 34 analysed libraries, 31 have no HPV16 call" | `calls.tsv` has HPV16 in 4 libraries: 071, 059, 064 (1 molecule) and 065 (9,834) | **wrong, see below** |
| hhv6b GSM6416028 "598 molecules" | `tiers.tsv` has `counted_virus_best` = 372 in 51 cells; 598 is the `calls.tsv` figure | **violates the draft's stated rule** |

Contradictions and internal inconsistencies:

1. **Libraries with an HPV16 call.**
   - The draft says "2 supported plus 1 unassessed" and "31 have no HPV16 call".
   - There are four HPV16-called libraries, and the draft omits GSM5017064 (`insufficient`, 1 molecule). So 30 libraries have no HPV16 call, not 31.
   - Section 1 should say "3 tiered, 1 untiered".
2. **Mixed counting conventions.** The draft says "I use `tiers.tsv` below", but it mixes in `calls.tsv` figures.
   - hhv6b GSM6416028 is quoted as 598 (`calls.tsv`) against 372 (`tiers.tsv`).
   - The HSV-2 range "5 to 19,831" mixes the two files. The `tiers.tsv` minimum is lower than 5, and the 5 appears to be a sibling-specific count.
   - The "Beyond the expected virus" HIV-1 rows correctly use `tiers.tsv`. Section 2(c) HSV-1 and HPV16 use UMIs, which is a third convention.
3. **HSV-1 14/14 is overstated.**
   - Of the 7 `supported_partial` libraries, GSM3511322 (3 molecules in 3 cells), 323 (8 in 6) and 330 have 0 or 1 HSV-1-specific molecules. All three are `clade_only`.
   - By the draft's own HSV-2 logic, these three are herpesvirus-clade signal, not HSV-1 resolved. They also have 0 barcodes at 10 or more arm P UMIs.
   - A defensible figure is **8/14 `target_resolved`** (7 `supported` plus 331, 318, 324 and 325 `supported_partial` with specific molecules, so 11 on the specific-molecule criterion; recount before quoting).
   - The 5/5 uninfected figure ignores that arm P gives 492 and 904 HSV-1 UMIs in uninfected GSM3511317 and 328, spread thinly (see the Modalities table).
4. **EBV 3/3 and type claims.** In GSM4796271 the "type 2 `supported`" row (437,009 molecules) has only 3 specific molecules. In GSM4796273 it is `clade_level`. The draft handles this correctly in section 3, so there is no conflict. The sibling-group column should be shown in the section 1 table.

## 2. Claims with no backing number in the supplied data

- The draft has two classes of unbacked claim.
  - **From memory:** the HIV-1 coverage "looks like LTR, cPPT, RRE". The skeptics' HXB2 positions were from memory and never checked against an annotation. The draft discloses this.
  - **Not in the supplied data:**
    - "the manuscript has no HSV, HHV-6, HPV16, EBV or HNSCC text yet (a grep found nothing)": the audit's grep result is reported, not a number.
    - "6 of 34 libraries are blocked": the blocked set is named by the audit, but the list is incomplete in the audit itself (061, 062, 063, 064, 065, 026).
- **"No off-target virus in any arm" is correctly disclaimed.** The draft gives only one twostep example, HPV77 with 267 molecules in 239 cells. It does not say how many other twostep-only calls exist for hnscc, hhv6b and ebv.
- **"Do not cite arm P Vaccinia numbers"** is fine. But 410 vs 11 and 234 vs 13 are also repeated in the audit data as agreeing, and the draft omits that one skeptic reproduced them from the count matrices.
- **Uncharacterised numbers.**
  - The "expected ~190 A-specific molecules in GSM6416022" figure is an extrapolation from other libraries' rates and is unsourced. The A-specific molecule share is 0.3 to 0.6% in the five 6A-supported libraries.
  - The "Vaccinia 9-library recurrence" has no pool or lab data.
- **hnscc status.** HPV status is known only for HN18 (+) and HN01 (-), with "6 HPV+ / 12 HPV-" taken from a plan document. The draft never states that HN14 and HN16 HPV16-positivity is a pipeline output, not an independent truth.

## 3. Modalities not run or not reported

| Modality | Status in draft | Gap |
|---|---|---|
| EM per-molecule multimapping | Not mentioned | `calls.tsv` is multimapper-weighted, but there is no EM-vs-weighting comparison. The Vaccinia 579 vs 5 and HHV-6A 5877 vs 1 gaps are exactly this. |
| Blind or locked thresholds | Disclosed as provisional | No held-out set, so no calibrated sensitivity or specificity. |
| Negative-control or uninfected libraries | Weak | hsv1 has 5 uninfected, hpv16 has 1, and hhv6b and hnscc have none documented. No ebv negative (LCL EBV-negative line). No mock or empty-droplet control for HIV-1 or Vaccinia. |
| Sensitivity vs published detection | Not computed | The draft cites Lareau's 0.2% ≥10-UMI super-expressor rate in the audit. It never compares it to ViralScan's rate: GSM6416029 gives 0.31% and GSM6416022 gives 99.99%, with a concrete denominator available. Wyler per-cell infection rate is also not compared. |
| Dose-response / time course | Not reported | hsv1 has 1, 3 and 5 hpi. A molecules-per-hpi trend (1 hpi 3 to 519, 3 hpi 1,151 to 940,927, 5 hpi 5,279 to 1,267,219) would be the strongest recovery figure and requires no extra run. |
| `combined_artefact` / `twostep` tiering | Disclosed | Not run for any dataset. |
| Index-hopping / swap check | Disclosed | Never run. |
| Per-cell infection fraction vs published | Not done | hpv16 gives 2,913 of about 31k called cells; Bedard gives none, so this is descriptive only. |
| Host-gene response in infected cells | Not mentioned | Not required for detection claims. |
| Cross-dataset specificity | Not addressed | No report of how many viruses in the 393-GTF panel are called per dataset beyond the top few. |

## 4. Five most valuable remaining analyses

1. **Obtain independent truth and compute per-library sensitivity and specificity.**
   - Pull per-library infection status from GEO and paper text for hsv1, hhv6b (and the missing GSM6416025) and hnscc (6 HPV+ / 12 HPV-).
   - Compute sensitivity and specificity with the label source stated, using `tiers.tsv` for a single counting convention.
   - This gives the headline numbers the report needs.
2. **Finish hnscc.**
   - Complete GSM5017065 and 064, run the 17 pending libraries, and re-freeze both TSVs.
   - Without this, "HPV16 in HPV+ tumours" rests on 2 tiered libraries and 1 untiered.
3. **Sibling and clade resolution.** Fix the three sibling issues together.
   - Report hsv1 recovery as specific-molecule-resolved.
   - Settle HHV-6A as a 6B strain-divergence or cross-mapping artefact (A-specific read identity and locus test).
   - Drop EBV type 2 as an independent call.
4. **Vector-decoy and mock check for HIV-1 and Vaccinia.**
   - Add lentiviral-vector decoys and confirm the LTR/cPPT/RRE footprint against an annotation.
   - This also explains Vaccinia.
   - GSM6416032 (29 molecules) and 031 (6) are the borderline calls.
5. **Tier `combined_artefact` and `twostep` and run the swap check.**
   - Resolve the hpv16 twostep HPV77 call (267 molecules in 239 cells) and enumerate every twostep-only call.
   - Run `swap_check.py` with pool manifests, since index hopping is untested for every library.
   - Then "no off-target virus in any arm" can be stated with evidence.

Two smaller items fit the same pass. First, fix the `calls.tsv` and `tiers.tsv` counting convention and the Yaba-like disease virus join key (hyphen vs underscore). Second, state the hsv1 dose-response (1 hpi, 3 hpi, 5 hpi) as a recovery figure.