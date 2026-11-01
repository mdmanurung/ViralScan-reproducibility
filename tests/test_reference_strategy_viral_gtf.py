"""The combined reference strategy passes the viral-only GTF (moved from the package's tests/test_build_manifest.py)."""

from __future__ import annotations

from scripts import reference_strategy


class TestReferenceStrategyPassesViralGtf:
    def test_combined_strategy_passes_the_viral_only_gtf(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            reference_strategy,
            "fastq_paths_for_dataset",
            lambda manifest, row: (tmp_path / "r1.fq", tmp_path / "r2.fq"),
        )
        manifest = {
            "references": {
                "viralscan": {
                    "all_virus": {
                        "kallisto_index": "v.idx",
                        "t2g": "v.t2g",
                        "gtf": "viral_only.gtf",
                    },
                    "combined": {
                        "kallisto_index": "c.idx",
                        "t2g": "c.t2g",
                        "gtf": "combined_with_host.gtf",
                    },
                }
            }
        }
        row = {"row_id": "r", "method": "viralscan", "technology": "10xv3"}
        for strategy, index in (("combined", "c.idx"), ("all_virus", "v.idx")):
            (cmd,) = reference_strategy.commands_for_row(
                {**row, "reference_strategy": strategy}, manifest, tmp_path
            )
            assert cmd[cmd.index("-i") + 1] == index
            assert cmd[cmd.index("--gtf") + 1] == "viral_only.gtf"
