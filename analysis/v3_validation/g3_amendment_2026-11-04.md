# G3 amendment draft, 2026-11-04

Status: draft for the next independent review round and the user's sign-off. Nothing freezes.
Protocol 0.3.0 becomes 0.4.0. Top-level `status` stays `draft`. No section status, factor status,
`freeze.*` or execution flag moves. Ledger records: `DEV-034` to `DEV-040` in `deviations.yaml`
(`DEV-034` to `DEV-037` the draft, `DEV-038` review round 13, `DEV-039` a pre-freeze deviation, `DEV-040` the user decisions of 2026-11-04).
Decision source "Q<n>" means user decision Q<n>, 2026-11-04.

## Changes

| Section | Old | New | Source | Record |
|---|---|---|---|---|
| `workflow_matrix.workflows` | W10a, W10b (ViralScan 2.2.0 native and matched, 12 rows) | removed | Q6 | DEV-034 |
| `workflow_matrix.expected_row_count` | 98 | 86 | Q6 | DEV-034 |
| `workflow_matrix.predecessor_*` (layer, comparable axes, incomparable-axes rule) | scored 2.2.0 comparison on `counts_original` | removed; `predecessor_comparison_rule` says 2.2.0 is not a comparator | Q6 | DEV-034 |
| `workflow_matrix.excluded_workflows` | `X_kallisto_two_step` | adds `X_viralscan_2_2_0_head_to_head`, `X_translated_protein_search` | Q6, Q7 | DEV-034 |
| `references` | `legacy_v2_native_panel` | removed (no row uses it) | Q6 | DEV-034 |
| `execution_readiness` blocker `tool_environments` | lists `viralscan-2.2.0` | drops it (the validator ties this text to the comparator tools) | Q6 | DEV-034 |
| `exclusions` | X1 to X5 | adds `X6_translated_search`: experimental, never changes `detected`, tier or any endpoint | Q7 | DEV-034 |
| `exclusions` `X3_legacy_or_private` | private clinical results need ethics documentation | adds: in-house COVID x213 and x216 (DSR-04) are a private negative control only, never in public results | Q14 | DEV-034 |
| `datasets` `anellovirus_orthogonal_positive` | claim-gating, screening support only without it | wording restates Q17: no anellovirus detection claim without an orthogonally confirmed positive | Q17 | DEV-034 |
| `protocol_version` | 0.3.0 | 0.4.0 (re-derives stage seeds; none used yet) | whole amendment | DEV-034 |
| `references.curated_human_virus` purpose and index asset | cat42d "stays a candidate until the G4 freeze"; index locator null | cat42d is the v3 production reference; locator `data/references/panel_builds/viral_ref_cat42d`; no hash until the G4 rebuild | Q9, Q16 | DEV-035 |
| `execution_readiness` blocker `production_reference` | "reference, D-list and calibrated safeguards pending" (task REF-09) | G4 = byte-identical rebuild of cat42d plus the GRCh38 D-list (task REF-04); REF-08 and REF-09 run in the truth panel training arm and report at G5 | Q9, Q16 (supersedes Q71) | DEV-035 |
| `principal_risks` | existing items | adds a frozen-panel item: HPV-11, ANELLO-13 and CAT-08 go to 3.1 | Q16 | DEV-035 |
| `factors[viral_abundance]` `pending_reason` | "Proposed by DEF-00" | cites the user decision VAL-01 D3 (levels 1, 3, 10, 30, 100, 300, 1000 unchanged) | VAL-01 D3, 2026-10-05 | DEV-036 |
| `factors[sibling_virus_similarity]` `pending_reason` | "Proposed by DEF-00" | cites VAL-01 D2 | VAL-01 D2, 2026-10-05 | DEV-036 |
| `factors` infected_cell_fraction, host_virus_homology, low_complexity, pcr_duplication, cb_umi_collisions, ambient_index_hopping | "Proposed by DEF-00; frozen at G3" | levels unchanged; `pending_reason` marks `proposed_pending_user_signoff` with a rationale | none recorded; for the user to sign | DEV-036 |
| `seeds.generation` `pending_reason` | no proposal | proposes 20260727005 (`proposed_pending_user_signoff`); `value` stays null | none recorded; for the user to sign | DEV-036 |
| `datasets` | 14 rows | adds `evid06_gse182227`, `evid06_gse166766`, `evid06_gse268542`, `evid06_gse120926`, `evid06_gse184257` and reserve `evid06_gse139324_reserve`: external-evaluation, contextual, no workflow row, assets pending until the verdict code and thresholds are frozen | Q18 to Q20 | DEV-037 |
| `harmonization` digests, schema consts, `frozen_inputs` | `contract_sha256` 16e464a6, `dependent_fields_sha256` 77238132 | 5db74530 and c8c024d6 (the dependent-fields digest covers the dataset list and exclusions); schema consts and `schema_sha256` follow; `frozen_inputs.contract_sha256` e3ad3698 | consequence of the above | DEV-034, DEV-037 |

Also changed outside the protocol: `scripts/gen_workflow_comparison.py` footer (no 2.2.0 rows),
three tests that asserted 2.2.0 is a comparator, and new tests for the items above.

## Values approved by the user (2026-11-04)

The user approved `seeds.generation` and every factor level below on 2026-11-04 (`DEV-040`). Status stays `pending` and the value stays
`null`; the formal G3 sign-off follows the round-14 external review and is not given here.

| Field | Approved value | Rationale |
|---|---|---|
| `seeds.generation` | 20260727005 | Next integer in the 20260727 series after `seeds.bootstrap`; distinct from every stage seed; the generator is Python, so the R integer limit of Q154 does not apply |
| `host_virus_homology` | none, repeat_homology | REF-07 found the homology 98.8 percent low-complexity (F-023); 89 clusters, 70 training and 19 holdout, assigned whole |
| `infected_cell_fraction` | 0.01, 0.04, 0.15 | 20, 80 and 300 designated cells of 2,000 |
| `low_complexity` | 0, 0.01, 0.05 | brackets the measured artefact classes |
| `pcr_duplication` | 2, 5, 10 | low to heavy duplication at 25,000 reads per cell |
| `cb_umi_collisions` | 0, 0.005, 0.02 | collision fraction of viral molecules |
| `ambient_index_hopping` | 0, 0.01, 0.05 | relocated fraction per virus |

## Revision after review round 13 (DEV-038)

Both reviewers returned does-not-pass (`sci05_review_round13.yaml`). Only `frozen_inputs` moves; the schema is unchanged.

| Finding | Change |
|---|---|
| R13-F1, F1, F2 | GSE184257 gate (KSHV latent-veto against total KSHV molecules) is viral-state, so outcome-generating. It waits for G3 clearance and the EVID-06 freeze; results cannot change EVID-06 rules, labels or exclusions. `proposed_pending_user_signoff`: it reverses Q3 "Set 3 now" in favour of Q19 |
| F1 (global rule) | Acquisition and hashing may precede the freeze for any dataset; no run that yields a call, count, tier, label or verdict precedes it. Set 3 (GSM6249889-92) was downloaded 2026-11-04, hashes recorded, no run |
| F3 | "Other virus" splits into unexpected-but-plausible, endogenous or integrated, and technical artefact |
| F4 | GSE139324 reserve re-scoped as HPV specificity substrate (CD45-sorted cells hold no tumour-cell HPV; cannot test sensitivity) |
| F5 | GSE120926 non-malignant libraries: "EBV status unverified", out of the negative tally |
| F6, F7, F9, F14 | KSHV truth is reporter based (cat42d KSHV accession unconfirmed; catalog lists NC_009333.1, paper used GQ994935.1); per-library reporting, no pooling; per-library chemistry and 5-prime strand calibration; cat42d is production pending G4 hashes |
| R13-F2 | `seeds.generation` consumer contract: production mode must consume or enforce the signed value; stale wording removed |

For the user only, not adopted: F8 (hold one virus or chemistry out of tuning), F10 (depth, strain divergence, foreign-virus ambient, co-infection), F11 (2.2.0 concordance), F12 (VIRTUS registry), F13 (record base 69abcc6 as the authoritative before-state).

## Open points for the user

- `EVID06-OV-1` (blocks freezing the other-virus rule): name the evidence-output field and values that mean "flagged as endogenous or integrated", define
  "orthogonal support", and confirm the order of steps 2 and 3. Neither test is defined in the protocol or here, so no threshold was invented.
- The four unopened Set 3 chem outputs (`DEV-039`): open them only after the EVID-06 freeze, or delete them and rerun the check.
- Decided 2026-11-04 (no longer open): VIRTUS is dropped; the EVID-06 bar on accuracy-type claims stays; the GSE184257 gate ordering is approved.
- The E1 acceptance text still lists `viralscan-2.2.0` among tools that declare no invariant. It is left alone (endpoints sit under the dependent-fields digest) and stays true.

## Revision after the user's decisions of 2026-11-04 (DEV-039, DEV-040)

The user approved the 20 recommendations of the afternoon grill. G3 is not signed; the formal sign-off follows round 14.

| Item | Change | Record |
|---|---|---|
| GSE184257 gate ordering | `proposed_pending_user_signoff` becomes user-approved: the gate runs after G3 clearance and the EVID-06 freeze (replaces Q3 "Set 3 now") | DEV-040 |
| Pre-freeze rule | Before the EVID-06 freeze only acquisition and content hashing are allowed. Dataset text that placed the chemistry check before the outcome run now places it after the freeze | DEV-040 |
| Deviation | `check-chemistry` job 25956713 ran on GSM6249889-92 on 2026-11-04, 13:27-13:31, before the rule. It reports barcode geometry only (no call, count, tier, label or verdict). Four 67-byte outputs under `data/runs/round_2026-11-04_veto/chem/` were opened by nobody and stay unopened. Inventory row `PFR-16` | DEV-039 |
| Other-virus rule | Three classes user-approved. The class assignment is now an ordered text in the five EVID-06 datasets (study report, then endogenous or integrated flag, then orthogonal support, then artefact; only the artefact is a disagreement). The tests for steps 2 and 3 are not defined anywhere, so they are open item `EVID06-OV-1` | DEV-040 |
| VIRTUS | Dropped from v3, possible 3.1: rows W9a and W9b (12), reference `virtus_native_panel`, the VIRTUS prose, the blocker text and the E1 list. `X_virtus` joins `excluded_workflows`. `expected_row_count` 86 becomes 74 | DEV-040 |
| `seeds.generation`, factor levels | User-approved (see the table above) | DEV-040 |
| Strand fallback | Kept. A per-chemistry strand default may only enter by a later ledgered amendment before the freeze | DEV-040 |
| EVID-06 | The bar on accuracy-type claims stays | DEV-040 |
| Digests | `workflow_matrix` 29aaf47c to 66b2d0c5. Because `supported_scope` and `endpoints` changed, `harmonization.dependent_fields_sha256` c8c024d6 to 9b294410 and `contract_sha256` 5db74530 to a44536df; the schema consts and `frozen_inputs.schema_sha256` follow | DEV-040 |

## Merge order

The schema constants changed (twice: `DEV-037`, then `DEV-040`), so the packaged copy `src/viralscan/schemas/v3/validation_protocol.schema.json` in the package repo
must become a byte copy of `schemas/v3/validation_protocol.schema.json` here, and `docs/workflow_comparison.md` there must be
regenerated (`python scripts/gen_workflow_comparison.py` with `VIRALSCAN_PKG` pointing at the package checkout). Then move
`provenance/PACKAGE_BASE_SHA`. Until then `test_packaged_schema_matches_the_canonical_schema`,
`test_both_schema_copies_are_identical_and_match_the_pin` and `test_page_is_current` fail by design.
`scripts/check_g3_diff.py` does not apply to this amendment: its allowlist is for the signing commit, which this is not.
