"""Shared helpers for the migration tests. Read-only: nothing here writes outside the baseline dir."""
import glob
import gzip
import hashlib
import json
import os
import random
import re
import subprocess
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
LAYOUT = yaml.safe_load((HERE / "layout.yaml").read_text())
R = LAYOUT["roots"]
BASE = HERE / "baseline"
LISTDIR = BASE / "listings"
CHUNK = 4 << 20


def abspath(rel: str) -> str:
    """`ViralScan/x` / `viral_ref_final` live under the archive root; `data/...` under the new repro."""
    return os.path.join(R["repro_new"], rel) if rel.startswith("data/") else os.path.join(R["archive"], rel)


def is_real_dir(p: str) -> bool:
    return os.path.isdir(p) and not os.path.islink(p)


def resolve(move: dict) -> str:
    """Where the tree is right now: the new location if it exists as a real dir, else the old one."""
    new, old = abspath(move["new"]), abspath(move["old"])
    return new if is_real_dir(new) else old


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return p.stdout


def inode(p: str):
    st = os.stat(p)
    return [st.st_dev, st.st_ino]


def listing(root: str, depth: int = 3):
    """Sorted entries (relative path + type) down to `depth`; no sizes, so live writers only ever add lines."""
    out = []
    root = root.rstrip("/")
    base = root.count("/")
    for dp, dns, fns in os.walk(root, followlinks=False):
        d = dp.count("/") - base
        for n in sorted(dns) + sorted(fns):
            full = os.path.join(dp, n)
            out.append(("l" if os.path.islink(full) else "d" if n in dns else "f") + " " + os.path.relpath(full, root))
        if d + 1 >= depth:
            dns[:] = []
    return sorted(set(out))


def partial_hash(p: str, size: int) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        h.update(f.read(CHUNK))
        if size > 2 * CHUNK:
            f.seek(-CHUNK, 2)
            h.update(f.read(CHUNK))
    return h.hexdigest()


def sample_files(root: str, n: int = 40, seed_text: str = ""):
    """Seeded random walk down the tree; returns [relpath, size, nlink, sha256(head+tail 4 MB)] for up to n regular files."""
    rng = random.Random(seed_text or root)
    got = {}
    for _ in range(n * 6):
        if len(got) >= n:
            break
        cur = root
        for _depth in range(14):
            try:
                kids = sorted(os.listdir(cur))
            except OSError:
                break
            if not kids:
                break
            nxt = os.path.join(cur, rng.choice(kids))
            if os.path.islink(nxt):
                break
            if os.path.isdir(nxt):
                cur = nxt
                continue
            try:
                st = os.stat(nxt)
                rel = os.path.relpath(nxt, root)
                got[rel] = [rel, st.st_size, st.st_nlink, partial_hash(nxt, st.st_size)]
            except OSError:
                pass
            break
    return list(got.values())


def save_listing(key: str, lines):
    LISTDIR.mkdir(parents=True, exist_ok=True)
    with gzip.open(LISTDIR / (key.replace("/", "__") + ".txt.gz"), "wt") as f:
        f.write("\n".join(lines))


def load_listing(key: str):
    with gzip.open(LISTDIR / (key.replace("/", "__") + ".txt.gz"), "rt") as f:
        return f.read().split("\n")


def baseline():
    return json.loads((BASE / "baseline.json").read_text())


def jobs():
    """Per job (squeue ids incl. array tasks): the paths a running/queued/held job needs."""
    ids = subprocess.run(["squeue", "-u", os.environ.get("USER", "mdmanurung"), "-h", "-o", "%A"], capture_output=True, text=True).stdout.split()
    out = {}
    for j in sorted(set(ids)):
        txt = subprocess.run(["scontrol", "show", "job", j], capture_output=True, text=True).stdout
        d = {}
        for tok in txt.replace("\n", " ").split():
            for k in ("WorkDir", "Command", "StdOut", "StdErr"):
                if tok.startswith(k + "="):
                    d[k] = tok.split("=", 1)[1]
        out[j] = d
    return out


def worktrees(repo: str):
    """[(path, prunable)] from `git worktree list --porcelain`."""
    res, cur = [], None
    for line in git(repo, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            cur = [line[9:], False]
            res.append(cur)
        elif line.startswith("prunable") and cur:
            cur[1] = True
    return [tuple(x) for x in res]


def live_script_files():
    out = []
    for pat in LAYOUT["live_scripts"]:
        out += glob.glob(os.path.join(R["archive"], pat))
        out += glob.glob(os.path.join(R["repro_new"], "data/runs/work", pat.split("viralscan_work/", 1)[-1]))
    return sorted(set(out))


def path_regex(pairs):
    """(regex, new_of) for old->new absolute pairs. Matches the path tail after the user root in both the absolute form
    and the variable forms stage 5 missed ($M/..., {M}/..., M / '...'); new_of maps the matched tail to its new tail.
    ponytail: assumes $M / {M} is the archive user root; a script that sets M to the scratch root was already broken."""
    tail = lambda p: p.split("/mdmanurung/", 1)[1]
    new_of = {tail(o): tail(n) for o, n in pairs}
    alts = "|".join(re.escape(t) for t in sorted(new_of, key=len, reverse=True))
    rx = re.compile(r"""(?:(?<=mdmanurung/)|(?<=\$M/)|(?<=\{M\}/)|(?<=M / ')|(?<=M / "))(""" + alts + r""")(?=[/\s"'$:;)]|$)""")
    return rx, new_of


def moved_path(p: str) -> str:
    """Where a pre-migration absolute path lives now, per layout moves (longest old prefix wins); unchanged if not moved."""
    for m in sorted(LAYOUT["moves"], key=lambda m: -len(m["old"])):
        old = abspath(m["old"])
        if p == old or p.startswith(old + "/"):
            return abspath(m["new"]) + p[len(old):]
    return p
