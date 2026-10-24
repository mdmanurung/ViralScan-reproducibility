# Technical recovery of failed Drop-seq searches — 2026-10-20

STAR 2.7.11b crashes during Solo counting for an all-unmapped Drop-seq
fixture with no whitelist. The original command, unique-only counting,
disabled cell filtering and exact barcode matching all reproduce the crash.
No failed search is treated as negative on that evidence.

The native `CB_samTagOut` mode completes the fixture. It requires exact
barcode matching, raw UR rather than corrected UB, and unique-only counting.
For a no-whitelist input, raw barcodes remain unchanged. A 20-read positive
fixture produces exactly the same mapping fields and raw tags as the
original command; corrected CB/UB tags are excluded from that comparison.
This is a narrow technical check, not a sensitivity calibration.

The recovery workflow runs the complete original FASTQ pair in a separate
output directory with those counting-only changes and six native threads.
Mapping filters, reference, read geometry and two-pass mode are unchanged.
Acceptance requires successful STAR completion, a valid BAM with **zero
mapped records**, zero unique/multimapped read counts in Log.final.out, and
an input count equal to the retained host-filter audit. Input sizes and
modification times must remain unchanged. FASTQs are not rehashed here.

Any mapped record rejects this recovery: corrected-UMI molecule counts
cannot be inferred from tag-only output. The original classifier runs only
after the zero-mapping proof; its blocked duplicate job is cancelled only
after a validated receipt is written. Original failures and frozen pinned
source are preserved. The original completion marker is never manufactured.

This is a documented post-preregistration execution repair. It does not
change candidate thresholds or establish a dataset verdict. The inventory
must distinguish original completion from independent zero verification.
Both settings and the existing sensitivity/evidence gates remain required
before any final dataset conclusion. See `zero_recovery_tasks.json`,
`zero_solo_reproduction/mapping_parity.json` and `zero_recovery_receipts/`.
