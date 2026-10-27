#!/usr/bin/env python3
"""Generate move_stage_N.sh and rollback_stage_N.sh from layout.yaml (explicit lists, `mv -n`, never rm -r). Writes nothing else.
Run a script with DRY=1 to only print the commands. Forward scripts leave an untracked compat link at every old path (stages 2-6);
stage 7 removes them. Links inside the package checkout are added to its .git/info/exclude, never to .gitignore."""
import glob
import os
import sys

import mig

L, R = mig.LAYOUT, mig.R
OUT = mig.HERE / "scripts"
OUT.mkdir(exist_ok=True)
HDR = '#!/usr/bin/env bash\nset -euo pipefail\nrun() { if [ "${DRY:-0}" = 1 ]; then echo "+ $*"; else "$@"; fi; }\n'
EXCL = os.path.join(R["old_checkout"], ".git/info/exclude")


def mv_lines(old, new, link=True):
    ls = [f'[ -e "{old}" ] || [ -L "{old}" ] || {{ echo "missing source {old}" >&2; exit 1; }}',
          f'[ ! -e "{new}" ] || {{ echo "destination exists {new}" >&2; exit 1; }}',
          f'run mkdir -p "{os.path.dirname(new)}"',
          f'run mv -n "{old}" "{new}"']
    if link:
        ls.append(f'run ln -s "{new}" "{old}"')
        if old.startswith(R["old_checkout"] + "/"):
            ls.append(f'[ "${{DRY:-0}}" = 1 ] || echo "/{os.path.relpath(old, R["old_checkout"])}" >> "{EXCL}"')
    return ls


def rb_lines(old, new):
    return [f'[ -L "{old}" ] && run rm "{old}"  # compat link only (rm of a symlink, not of data)',
            f'[ -e "{new}" ] || {{ echo "nothing at {new}" >&2; exit 1; }}',
            f'run mv -n "{new}" "{old}"']


stages = sorted({m["stage"] for m in L["moves"]} | {L["gtf_move"]["stage"]})
for st in stages:
    fw, rb = [HDR], [HDR]
    for m in [m for m in L["moves"] if m["stage"] == st]:
        o, n = mig.abspath(m["old"]), mig.abspath(m["new"])
        fw += mv_lines(o, n)
        rb = rb[:1] + rb_lines(o, n) + rb[1:]  # reverse order
    if st == L["gtf_move"]["stage"]:
        g = L["gtf_move"]
        od, nd = os.path.join(R["archive"], g["old_dir"]), os.path.join(R["repro_new"], g["new_dir"])
        fw.append(f'run mkdir -p "{nd}"')
        for f in sorted(glob.glob(os.path.join(od, g["glob"])) or [os.path.join(nd, x) for x in sorted(mig.baseline()["gtf"])]):
            b = os.path.basename(f)
            fw += [f'run mv -n "{od}/{b}" "{nd}/{b}"', f'run ln -s "{nd}/{b}" "{od}/{b}"']
            rb.insert(1, f'[ -L "{od}/{b}" ] && run rm "{od}/{b}"; run mv -n "{nd}/{b}" "{od}/{b}"')
        fw.append(f'[ "${{DRY:-0}}" = 1 ] || echo "/{g["old_dir"].split("/", 1)[1]}/*.gtf" >> "{EXCL}"')
        keep = os.path.join(R["repro_new"], "data/backups/old-checkout-leftovers")
        fw.append(f'run mkdir -p "{keep}"')
        for pat in L["leftover_globs"]:
            for f in sorted(glob.glob(os.path.join(R["old_checkout"], pat))):
                fw.append(f'run mv -n "{f}" "{keep}/{os.path.basename(f)}"')
                rb.insert(1, f'run mv -n "{keep}/{os.path.basename(f)}" "{f}"')
    if st == 3:  # D58: prune stale registrations, then repair the 32 real worktrees that moved
        oc = R["old_checkout"]
        pin, wk = os.path.join(R["repro_new"], "data/pinned_snapshots/vs_pinned"), os.path.join(R["repro_new"], "data/runs/vs_work")
        opin, owk = os.path.join(R["archive"], "vs_pinned"), os.path.join(R["archive"], "vs_work")
        fw.append(f'run git -C "{oc}" worktree prune')
        fw.append(f'run git -C "{oc}" worktree repair $(ls -d "{pin}"/* "{wk}"/*)')
        rb.insert(1, f'run git -C "{oc}" worktree repair $(ls -d "{opin}"/* "{owk}"/*)  # after the dirs are back (the pruned /tmp entries stay pruned)')
    (OUT / f"move_stage_{st}.sh").write_text("\n".join(fw) + "\n")
    (OUT / f"rollback_stage_{st}.sh").write_text("\n".join(rb) + "\n")
    print(f"stage {st}: {len([m for m in L['moves'] if m['stage'] == st])} dir moves")
