# Kraken2 discovery on EBV SRR12682296: settings trade-off (2026-10-22)

- Source: Slurm 25862538, code c41e330, PlusPF-16 2026-06-26; outputs `viralscan_work/discovery_ebv_2026-10-21/r10/`.
- 0.05/4 (Cellsnake) vs 0.0/2 (Kraken2 default), polyA/T trim on: EBV groups in called cells 246,233 vs 623,096; EBV+ cells 2,224 vs 2,471 of 2,524; per-cell Spearman vs ViralScan 0.890 vs 0.966; human clade 4.1% vs 20.9% of reads; candidates 47 vs 1,906.
- PolyA/T trim (2.03 M reads) moved human 4.5% -> 4.1% only.
- The synthetic benchmark (settings move <= 8 UMIs) does not transfer to real data.
- Status: one library, read level, descriptive; not an accuracy estimate.
