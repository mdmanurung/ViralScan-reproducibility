# Handoff — merge PRs #91–#99, spike-in grid, close-out to 3.0.0rc1

**Date:** 2026-10-22 · **Root:** shared dirty checkout `codex/drop-py39` @ `5e551c9` (107 entries; never edit/stage/stash/reset it; a Codex session uses it) · **Status:** #90 merged (`736ce74`); #91–#99 open, CI green or queued; grid 3/66 done.
Previous handoff: `HANDOFF_prev_2026-10-22.md`. Full checklist: `.mycelium/run/claude/c28c902a-f93e-419c-8dc3-3f97fc5c2752/last-session.md`.

## Goal
Land all open branches, record the spike-in flank verdict, finish package work → `3.0.0rc1`. Done = every Claude row in the checklist closed with evidence, every user row staged.

## Next action
`gh pr view 91 --repo mdmanurung/ViralScan --json state` — if MERGED, continue with #92; else wait for its 3 queued macOS jobs. Per PR: CI green → `vs_work/notes/trial_merge.sh codex/<branch>` (trial merge into origin/main + inventory validator) → touched tests → `gh pr merge <n> --merge`.

## State
- Merge order: #91 F-027, #92 caveats, #93 shifted-log, #94 tchem, #95 taxonomy, #96 DISC-13, #97 cli hostresponse, #98 coverage maps, #99 cli layout (base = #97; after #97 merges retarget: `gh api -X PATCH repos/mdmanurung/ViralScan/pulls/99 -f base=main`; no force-push needed — local rebase in `vs_work/cli02b-1022` diverges from origin, ignore it).
- Worktrees (all `vs_work/`): q17-docs, hhv6b-finding, shifted-log-1022, tchem, taxonomy, disc13, cli02-1022, cov-star-1022, cli02b-1022, scautoqc-1022, wave2-base-1022, star-confirm, star-align-1022, spikein (GRID RUNS FROM HERE — do not touch), spikein-posthoc, research-trees, merge-trial. `/tmp/vs_work_*` entries are on another node: do not prune.
- Backups: refs `backup/<branch>-pre-rebase-2026-10-22`; tag `spikegrid-code-26c1ac5`.
- Slurm: grid array 25864985 (66 rows, highmem,all, 48G); `tA_advance` 25851736 held (keep); `ebcd_cont` 25854873 running.
- This session ran on compute node res-hpc-exe051 (node-local /tmp).

## Locked decisions
- User authorised Claude to merge #90–#99 in order, one at a time with own check (2026-10-22); merge commits keep pinned SHAs.
- All 2026-10-22 grilling entries in `.living/decisions.md` (Q1–Q17, round on remaining tasks) are approved; follow them.
- Flank verdict rule unchanged; retire beats undetermined across backgrounds; keep with recovery <80% → ask user.
- EBV anellovirus scoped verdict ISSUED; Lareau comparison closed (F-027, `d6807a4`).
- Deletions, Track A sign-off, STAR-GATE-01, D02/D04 start, research-tree commit, installs: user only.

## Dead ends — do not redo
- Automated merge-loop script — classifier denied ("Merge Without Review"); merge PR by PR.
- Force-push of #99 — classifier denied; not needed (see State).
- `blastn -remote` hangs; use Biopython qblast XML (Tabular returns empty).
- Workflow agents as Slurm monitors; job inputs in /tmp.

## Read first
- `vs_work/notes/PUSH_PLAN_2026-10-22.md` — branch/worktree/test table.
- `.living/learnings.md` "Spike-in scorer counts host genes as viral" — why rescoring is needed.
- `analysis/trackA_report_2026-10-18/ARCHIVE_CHECKLIST_hhv6b_2026-10-22.md` §7–8 — replay PASS, gaps 2/5 closed, 3/4/7/8 open.

## Open items
- After #93+#94 merge: in `vs_work/scautoqc-1022` `git rebase --onto origin/main tmp/wave2-base-2026-10-22`, regen cli_reference, re-pin, push, PR.
- After merges: rebase STAR stack (`vs_work/star-align-1022` → `vs_work/star-confirm`), PR; then DISC-13 STAR/route-ii producers + CLI; DISC-12 protocol draft (plan only).
- Grid done → in `vs_work/spikein-posthoc`: `rescore.py`, `aggregate.py check --scores-name scores_v2.tsv`, report, `recovery_ratio.py`; record verdict (early signal: flank +12.6 unsupported in null → likely retire); then rebase spikein branches, PR.
- After docs-revision (#88) merges: quickstart vignette on Slurm. Last: prune worktrees, re-pin inventory.
- Cleanup PR: 10 institutional-path hits already in main's PLAN.md.
- User: research-tree commit (`vs_work/notes/RESEARCH_TREES_FILELIST_2026-10-22.md`), kill orphan 2408964 on login node, report sign-off, HHV-6B gaps 3/4/7/8 then deletion.
