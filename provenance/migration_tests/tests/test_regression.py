"""R1-R7: regression tests. Green before any move and after every stage ("same bytes, same work, same git")."""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

import pytest

import mig

L, R = mig.LAYOUT, mig.R
B = mig.baseline()
CAPTURED_AT = (mig.BASE / "baseline.json").stat().st_mtime
MOVES = [m for m in L["moves"] if not B["moves"].get(m["old"], {}).get("missing")]
ENV_PY = sys.executable
PKG_DEFAULT = os.path.join(R["repro_new"], "pkg") if os.path.isdir(os.path.join(R["repro_new"], "pkg", "src")) else os.path.join(R["scratch"], "ViralScan-pin2")


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---- R1 tree integrity ---------------------------------------------------------------------------------
@pytest.mark.parametrize("m", MOVES, ids=[m["old"] for m in MOVES])
def test_R1_tree_is_the_same_tree(m):
    base = B["moves"][m["old"]]
    p = mig.resolve(m)
    assert mig.is_real_dir(p), f"{p} is not a real directory"
    assert mig.inode(p)[1] == base["inode"][1], "inode changed: this is a copy or a different tree, not a rename"  # st_dev is a per-host mount id; the inode alone proves a rename
    now = set(mig.listing(p, 3))
    lost = set(mig.load_listing(m["old"])) - now
    assert not lost, f"{len(lost)} entries (depth<=3) disappeared, e.g. {sorted(lost)[:3]}"
    for rel, size, nlink, h in base["samples"]:
        f = os.path.join(p, rel)
        assert os.path.exists(f), f"sampled file missing: {rel}"
        st = os.stat(f)
        if st.st_mtime > CAPTURED_AT:
            continue  # a live job rewrote it after the baseline; not a migration effect
        assert (st.st_size, st.st_nlink) == (size, nlink), f"size/hardlink count changed: {rel}"
        assert mig.partial_hash(f, st.st_size) == h, f"content changed: {rel}"


def test_R1_gtfs_and_leftovers_intact():
    g = L["gtf_move"]
    dirs = [os.path.join(R["archive"], g["old_dir"]), os.path.join(R["repro_new"], g["new_dir"])]
    for name, (size, h) in B["gtf"].items():
        hits = [os.path.join(d, name) for d in dirs if os.path.isfile(os.path.join(d, name))]
        assert hits, f"GTF lost: {name}"
        assert _sha(hits[0]) == h, f"GTF content changed: {name}"
    assert len(B["gtf"]) == g["expected_count"]
    keep = os.path.join(R["repro_new"], "data/backups/old-checkout-leftovers")
    for name, (size, h) in B["leftovers"].items():
        hits = [p for p in (os.path.join(keep, name), os.path.join(R["old_checkout"], name)) if os.path.isfile(p)]
        assert hits, f"leftover file lost: {name}"
        assert _sha(hits[0]) == h


# ---- R2 job safety -------------------------------------------------------------------------------------
def test_R2_every_path_a_queued_job_needs_exists():
    bad = []
    for j, d in mig.jobs().items():
        wd, cmd = d.get("WorkDir"), d.get("Command")
        if wd and not os.path.isdir(wd):
            bad.append((j, "WorkDir", wd))
        if cmd and cmd != "(null)" and not os.path.isfile(cmd):
            bad.append((j, "Command", cmd))
        for k in ("StdOut", "StdErr"):
            p = d.get(k)
            if p and not os.path.isdir(os.path.dirname(p)):
                bad.append((j, k, p))
    assert not bad, bad[:5]


# ---- R3 live-script paths -------------------------------------------------------------------------------
_PATH = re.compile(r"/exports/[A-Za-z0-9_./\-]+(?![A-Za-z0-9_./\-%])")  # a `%j` Slurm log template is not a path
_SNAP = mig.BASE / "script_paths.json"


def _script_paths():
    out = {}
    for f in mig.live_script_files():
        txt = open(f, errors="ignore").read()
        out[f] = sorted({p.rstrip(".") for p in _PATH.findall(txt) if "$" not in p})
    return out


def test_R3_paths_named_in_live_scripts_still_resolve():
    now = _script_paths()
    if not _SNAP.exists():  # first run, before any move: remember which named paths are already broken
        assert not os.path.isdir(os.path.join(R["repro_new"], "data/runs")), "snapshot must be taken before moves"
        _SNAP.write_text(json.dumps({f: [p for p in ps if not os.path.exists(p)] for f, ps in now.items()}))
    broken0 = {p for ps in json.loads(_SNAP.read_text()).values() for p in ps}
    broken = sorted({p for ps in now.values() for p in ps if not (os.path.exists(p) or glob.glob(p))} - broken0)
    assert not broken, broken[:8]


# ---- R4 package git -------------------------------------------------------------------------------------
def test_R4_package_git_unchanged():
    repo = R["old_checkout"]
    ls = mig.git(repo, "ls-files", "-s")
    assert hashlib.sha256(ls.encode()).hexdigest() == B["git"]["package"]["ls_files_sha256"], "tracked files changed"
    assert not any(x.startswith("120000") for x in ls.splitlines())
    dirty = [x for x in mig.git(repo, "status", "--porcelain", "--untracked-files=no").splitlines() if not x[3:].startswith(".living/")]
    assert not dirty, dirty[:5]
    head = B["git"]["package"]["head"]
    ok = subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor", head, "HEAD"]).returncode == 0
    assert ok, "package HEAD no longer contains the baseline commit"


# ---- R5 repro git + validators ---------------------------------------------------------------------------
def _repro():
    return R["repro_new"] if os.path.isdir(os.path.join(R["repro_new"], ".git")) else R["repro_old"]


def test_R5_repro_git_has_baseline_and_no_symlinks():
    repo = _repro()
    head = B["git"]["repro"]["head"]
    assert subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor", head, "HEAD"]).returncode == 0
    assert not any(x.startswith("120000") for x in mig.git(repo, "ls-files", "-s").splitlines())


def test_R5_governance_validators_pass():
    repo = _repro()
    env = {**os.environ, "VIRALSCAN_PKG": os.environ.get("VIRALSCAN_PKG", PKG_DEFAULT)}
    for s in ("validate_artifact_inventory.py", "validate_claim_registry.py"):
        p = subprocess.run([ENV_PY, os.path.join(repo, "scripts", s)], capture_output=True, text=True, cwd=repo, env=env)
        assert p.returncode == 0, (s, p.stdout[-300:], p.stderr[-300:])


@pytest.mark.slow
def test_R5_repro_suite_matches_baseline():
    repo = _repro()
    env = {k: v for k, v in os.environ.items() if not k.startswith("VIRALSCAN_TCHEM")}
    env["VIRALSCAN_PKG"] = os.environ.get("VIRALSCAN_PKG", PKG_DEFAULT)
    x = os.path.join(mig.BASE, "repro_suite_now.xml")
    subprocess.run([ENV_PY, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", "-W", "ignore", f"--junitxml={x}"], cwd=repo, env=env, capture_output=True)
    import xml.etree.ElementTree as ET
    r = ET.parse(x).getroot()
    s = r if r.tag == "testsuite" else r[0]
    got = {k: int(s.get(k)) for k in ("tests", "failures", "errors", "skipped")}
    assert got["failures"] == got["errors"] == 0 and got["tests"] == B["repro_suite"]["tests"], got


@pytest.mark.slow
def test_R4_package_suite_matches_baseline():
    ps = B.get("package_suite")
    if not ps:
        pytest.skip("no package baseline captured")
    env = {**os.environ, "PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1"}
    x = os.path.join(mig.BASE, "package_suite_now.xml")
    subprocess.run([ENV_PY, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", "-W", "ignore", f"--junitxml={x}"], cwd=R["old_checkout"], env=env, capture_output=True)
    import xml.etree.ElementTree as ET
    r = ET.parse(x).getroot()
    s = r if r.tag == "testsuite" else r[0]
    got = {k: int(s.get(k)) for k in ("tests", "failures", "errors", "skipped")}
    assert got == ps, (got, ps)


# ---- R6 worktrees ----------------------------------------------------------------------------------------
def test_R6_worktrees_not_broken_by_moves():
    rp = lambda p: os.path.realpath(mig.moved_path(p))  # a moved worktree is listed under its new path (compat links are gone after stage 7)
    base = B["worktrees"]
    now = mig.worktrees(R["old_checkout"])
    base_prunable = {rp(p) for p, pr in base if pr}
    new_prunable = {p for p, pr in now if pr} - base_prunable
    assert not new_prunable, f"worktrees broken by a move: {sorted(new_prunable)[:5]}"
    healthy_base = {rp(p) for p, pr in base if not pr}
    lost = healthy_base - {rp(p) for p, _ in now}
    assert not lost, f"healthy worktrees vanished from the registry: {sorted(lost)[:5]}"


# ---- R7 package still finds the GTFs -----------------------------------------------------------------------
def test_R7_package_finds_all_gtfs():
    g = L["gtf_move"]
    cache = os.path.join(R["repro_new"], "data/references/gtf")
    if not glob.glob(os.path.join(cache, "data", "*.gtf")):
        cache = os.path.join(R["archive"], "ViralScan/src/viralscan")  # before stage 2 the GTFs sit in src/viralscan/data
    code = "from viralscan import data_fetch as d; print(len(list(d.viral_data_dir().glob('*.gtf'))))"
    env = {**os.environ, "PYTHONPATH": os.path.join(R["old_checkout"], "src"), "VIRALSCAN_CACHE": cache}
    p = subprocess.run([ENV_PY, "-c", code], capture_output=True, text=True, env=env)
    assert p.stdout.strip() == str(g["expected_count"]), (p.stdout, p.stderr[-200:])


# ---- R0 the move/rollback scripts cover layout.yaml ---------------------------------------------------------------
def test_R0_move_and_rollback_scripts_cover_every_move():
    for m in L["moves"]:
        o, n = mig.abspath(m["old"]), mig.abspath(m["new"])
        for kind in ("move", "rollback"):
            f = mig.HERE / "scripts" / f"{kind}_stage_{m['stage']}.sh"
            assert f.exists(), f"{f.name} missing (run gen_moves.py)"
            t = f.read_text()
            assert f'"{o}"' in t and f'"{n}"' in t, f"{m['old']} not in {f.name}"
        assert "mv -n" in (mig.HERE / "scripts" / f"move_stage_{m['stage']}.sh").read_text()
    assert "rm -r" not in "".join(p.read_text() for p in (mig.HERE / "scripts").glob("*.sh")), "recursive rm is forbidden"
