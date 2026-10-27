"""T2-T8: target-state tests. RED before the migration; each turns green when its stage is done (`pytest --stage N`)."""
import glob
import json
import os
import re
import subprocess

import pytest

import mig

L, R = mig.LAYOUT, mig.R
B = mig.baseline()


def moves(stage):
    return [m for m in L["moves"] if m["stage"] == stage]


def _moved_ok(m):
    new, old = mig.abspath(m["new"]), mig.abspath(m["old"])
    assert mig.is_real_dir(new), f"missing at new location: {new}"
    assert not mig.is_real_dir(old), f"still a real directory at the old location: {old}"  # a compat link is fine until stage 7


# ---- stage 2 / 3 / 6: every tree is where layout.yaml says ----------------------------------------------------
@pytest.mark.stage(2)
@pytest.mark.parametrize("m", moves(2), ids=[m["old"] for m in moves(2)])
def test_T2_old_checkout_dir_moved_to_data(m):
    _moved_ok(m)


@pytest.mark.stage(2)
def test_T2_gtfs_moved():
    g = L["gtf_move"]
    new = glob.glob(os.path.join(R["repro_new"], g["new_dir"], g["glob"]))
    old = [f for f in glob.glob(os.path.join(R["archive"], g["old_dir"], g["glob"])) if not os.path.islink(f)]  # compat links are fine until stage 7
    assert len(new) == g["expected_count"] and not old, (len(new), len(old))


@pytest.mark.stage(2)
def test_T2_old_checkout_is_tracked_files_only():
    repo = R["old_checkout"]
    tracked_top = {p.split("/")[0] for p in mig.git(repo, "ls-files").splitlines()}
    extra = [n for n in os.listdir(repo) if n not in tracked_top and n not in L["old_checkout_allow"] and not os.path.islink(os.path.join(repo, n))]  # compat links are removed in stage 7 (T7)
    assert not extra, f"untracked top-level entries left in the package checkout: {sorted(extra)}"


@pytest.mark.stage(3)
@pytest.mark.parametrize("m", moves(3), ids=[m["old"] for m in moves(3)])
def test_T3_sibling_dir_moved_to_data(m):
    _moved_ok(m)


@pytest.mark.stage(6)
def test_T6_viralscan_work_moved_and_idle():
    for m in moves(6):
        _moved_ok(m)
    old = mig.abspath("viralscan_work")
    assert not any(old in (d.get("WorkDir") or "") + (d.get("Command") or "") for d in mig.jobs().values()), "a job still runs from the old path"


# ---- stage 4: repro defaults ---------------------------------------------------------------------------------
@pytest.mark.stage(4)
def test_T4_repro_lives_on_archive_with_data_and_pkg():
    repo = R["repro_new"]
    assert os.path.isdir(os.path.join(repo, ".git")), "repro is not cloned on archive"
    assert not os.path.exists(os.path.join(repo, "setup_links.sh")) and not os.path.exists(os.path.join(repo, "links"))
    pkg = os.path.join(repo, "pkg")
    want = open(os.path.join(repo, "provenance/PACKAGE_BASE_SHA")).read().split()[0]
    assert mig.git(pkg, "rev-parse", "HEAD").strip().startswith(want[:7]), "pkg/ is not the pinned package commit"


@pytest.mark.stage(4)
def test_T4_defaults_point_at_the_new_locations():
    repo = R["repro_new"]
    for f in ("env.sh", "conftest.py"):
        t = open(os.path.join(repo, f)).read()
        assert "ViralScan-pin2" not in t and "ViralScan-data" not in t, f"{f} still names an old location"
    assert "VIRALSCAN_CACHE" in open(os.path.join(repo, "env.sh")).read()


# ---- stage 5: scripts no longer name old paths --------------------------------------------------------------------
@pytest.mark.stage(5)
def test_T5_live_scripts_name_no_old_paths():
    rx = re.compile(L["old_path_regex"])
    bad = {}
    for f in mig.live_script_files():
        txt = "\n".join(l for l in open(f, errors="ignore").read().splitlines() if "ViralScan-reproducibility/data/" not in l)  # a line already under data/ is migrated
        hits = {m.group(0) for m in rx.finditer(txt)} - {"/viralscan_work/"}  # that move is stage 6 (T6)
        if hits:
            bad[f] = sorted(hits)[:3]
    assert not bad, list(bad.items())[:4]


# ---- stage 7: no symlinks, no extra folders, worktrees repaired ------------------------------------------------------
@pytest.mark.stage(7)
def test_T7_only_the_two_folders_remain():
    pat = re.compile(r"viral|vs_|virtus|kraken2|_kbtest", re.I)  # _misc stays (other projects); its two viralscan links are in moves
    for key, want in (("archive", L["final"]["archive_viralscan_names"]), ("scratch", L["final"]["scratch_viralscan_names"])):
        got = sorted(n for n in os.listdir(R[key]) if pat.search(n))
        assert got == sorted(want), (key, got)


@pytest.mark.stage(7)
def test_T7_no_symlink_at_the_old_locations_or_in_git():
    for repo in (R["old_checkout"], R["repro_new"]):
        assert not any(x.startswith("120000") for x in mig.git(repo, "ls-files", "-s").splitlines())
    for m in L["moves"]:
        old = mig.abspath(m["old"])
        assert not os.path.lexists(old), f"compat link/dir still at {old}"


@pytest.mark.stage(7)
def test_T7_worktrees_repaired():
    wts = mig.worktrees(R["old_checkout"])
    assert not [p for p, pr in wts if pr], "prunable worktrees left"
    inside = (R["old_checkout"], R["repro_new"])
    assert all(p.startswith(inside) for p, _ in wts), [p for p, _ in wts if not p.startswith(inside)][:5]


# ---- stage 8: git remotes -------------------------------------------------------------------------------------
def _remote_branches(repo):
    out = subprocess.run(["gh", "api", f"repos/mdmanurung/{repo}/branches", "--paginate", "--jq", ".[].name"], capture_output=True, text=True).stdout
    return sorted(out.split())


@pytest.mark.stage(8)
def test_T8_remote_branches_clean_and_bundled():
    assert _remote_branches("ViralScan") == sorted(L["final"]["package_remote_branches"])
    assert _remote_branches("ViralScan-reproducibility") == sorted(L["final"]["repro_remote_branches"])
    assert glob.glob(os.path.join(R["repro_new"], "data/backups/branch-bundles/*.bundle")), "no branch bundles saved"


@pytest.mark.stage(7)
def test_T7_nothing_reads_old_paths():
    """Gate for removing the compat links: no queued job and no live script under data/runs/work names an old path."""
    olds = [mig.abspath(m["old"]) for m in L["moves"]]
    jobs = {j: d for j, d in mig.jobs().items() if any(o in v for o in olds for v in d.values())}
    assert not jobs, f"queued jobs still name an old path: {jobs}"
    rx, skip = re.compile(L["old_path_regex"]), re.compile(L["frozen_dir_regex"])
    bad = []
    for dp, dns, fns in os.walk(os.path.join(R["data"], "runs/work")):
        if skip.search(dp + "/"):
            dns[:] = []
            continue
        for f in fns:
            p = os.path.join(dp, f)
            if skip.search(os.path.join(dp, f)) or not f.endswith((".py", ".sh", ".sbatch")):
                continue
            txt = "\n".join(l for l in open(p, errors="ignore").read().splitlines() if "ViralScan-reproducibility/data/" not in l)  # new paths contain /vs_pinned/, /viral_ref_ etc. (as T5)
            if rx.search(txt):
                bad.append(p)
    assert not bad, f"{len(bad)} live scripts under data/runs/work name an old path, e.g. {bad[:3]}"
