"""Install pinned method sources into this analysis's private R library."""

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path

from tracka_data import HERE, load_config, sha256, write_json


def package_hashes(library):
    return {
        str(p.relative_to(library)): sha256(p)
        for p in sorted(library.rglob("*"))
        if p.is_file() and (p.suffix in (".rdb", ".rdx", ".so") or p.name == "DESCRIPTION")
    }


def apply_source_fixes(package, pin):
    for fix in pin.get("source_fixes", []):
        path = package / fix["path"]
        text = path.read_text()
        if text.count(fix["after"]) == 1 and fix["before"] not in text:
            continue
        if text.count(fix["before"]) != 1 or fix["after"] in text:
            raise ValueError(f"Upstream source differs from the qualified correction: {path}")
        path.write_text(text.replace(fix["before"], fix["after"]))


def verify_runtime(cfg):
    runtime = HERE / ".runtime"
    receipt = json.loads((runtime / "receipt.json").read_text())
    if receipt["upstream"] != json.loads((HERE / "upstream.json").read_text()):
        raise ValueError("Runtime source pins changed; rebuild isolated runtime")
    if receipt["installed_hashes"] != package_hashes(runtime / "library"):
        raise ValueError("Private R library differs from its installation receipt")
    for name, dependency in receipt["dependencies"].items():
        if dependency["hashes"] != package_hashes(Path(dependency["path"])):
            raise ValueError(f"R dependency changed after qualification: {name}")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(HERE / "config.json"))
    parser.add_argument("--source-cache", type=Path)
    parser.add_argument(
        "--fetch", action="store_true", help="Download pinned upstream source archives"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Reinstall only the private analysis library; retain the previous receipt",
    )
    args = parser.parse_args()
    cfg = load_config(args.config)
    runtime = HERE / ".runtime"
    library = runtime / "library"
    previous = (
        json.loads((runtime / "receipt.json").read_text())
        if (runtime / "receipt.json").exists()
        else None
    )
    if (runtime / "receipt.json").exists() and not args.rebuild:
        verify_runtime(cfg)
        print("Pinned private runtime already verified")
        return
    if (runtime / "receipt.json").exists():
        old = runtime / "receipt.json"
        old.rename(runtime / ("receipt_" + sha256(old)[:16] + ".json"))
    library.mkdir(parents=True, exist_ok=True)
    pins = json.loads((HERE / "upstream.json").read_text())
    sources = {}
    for name, pin in pins.items():
        identity = pin["commit"] if "commit" in pin else pin["sha256"]
        marker = "UPSTREAM_COMMIT" if "commit" in pin else "ARCHIVE_SHA256"
        dest = runtime / "sources" / name
        if not dest.exists():
            cached = args.source_cache / name if args.source_cache else None
            if (
                cached
                and (cached / marker).is_file()
                and (cached / marker).read_text().strip() == identity
            ):
                shutil.copytree(cached, dest)
            elif args.fetch:
                url = (
                    pin["archive_url"]
                    if "archive_url" in pin
                    else f"https://api.github.com/repos/{pin['repo']}/tarball/{pin['commit']}"
                )
                archive = urllib.request.urlopen(url, timeout=90).read()
                if "sha256" in pin and hashlib.sha256(archive).hexdigest() != pin["sha256"]:
                    raise ValueError("Upstream source archive checksum mismatch")
                dest.mkdir(parents=True)
                (dest / "archive.sha256").write_text(hashlib.sha256(archive).hexdigest() + "\n")
                with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as handle:
                    prefix = handle.getmembers()[0].name.split("/")[0]
                    for member in handle.getmembers():
                        if member.isfile():
                            rel = Path(member.name).relative_to(prefix)
                            if rel.is_absolute() or ".." in rel.parts:
                                raise ValueError("Unsafe upstream archive path")
                            path = dest / rel
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.write_bytes(handle.extractfile(member).read())
                (dest / marker).write_text(identity + "\n")
            else:
                raise FileNotFoundError(
                    f"No pinned source for {name}; use --fetch or --source-cache"
                )
        if (dest / marker).read_text().strip() != identity:
            raise ValueError(f"Wrong source commit for {name}")
        package = dest / pin["package_dir"]
        apply_source_fixes(package, pin)
        sources[name] = {
            str(p.relative_to(dest)): sha256(p)
            for p in sorted(package.rglob("*"))
            if p.is_file()
            and (
                p.suffix == ".R" or p.name in ("DESCRIPTION", "NAMESPACE", "LICENSE", "LICENSE.md")
            )
        }
        env = dict(
            os.environ,
            R_LIBS=":".join(cfg["r_libraries"]),
            MAKEFLAGS="-j1",
            PATH=str(Path(cfg["rscript"]).parent) + ":" + os.environ.get("PATH", ""),
        )
        installed = {name + "/" + k: v for k, v in package_hashes(library / name).items()}
        previous_installed = (
            {
                k: v
                for k, v in previous.get("installed_hashes", {}).items()
                if k.startswith(name + "/")
            }
            if previous
            else {}
        )
        if (
            previous
            and previous["upstream"].get(name) == pin
            and previous["source_hashes"].get(name) == sources[name]
            and installed
            and installed == previous_installed
        ):
            continue
        with (runtime / f"install_{name}.log").open("w") as log:
            subprocess.run(
                [
                    str(Path(cfg["rscript"]).with_name("R")),
                    "CMD",
                    "INSTALL",
                    "--no-test-load",
                    "--no-multiarch",
                    "-l",
                    str(library),
                    str(package),
                ],
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=True,
            )
    env = dict(os.environ, R_LIBS=":".join(cfg["r_libraries"]), TZ="Europe/Amsterdam")
    session = subprocess.run(
        [
            cfg["rscript"],
            "--vanilla",
            str(HERE / "methods.R"),
            "preflight",
            str(runtime / "dependencies.json"),
        ],
        env=env,
        text=True,
        capture_output=True,
    )
    (runtime / "preflight.log").write_text(session.stdout + session.stderr)
    session.check_returncode()
    dependencies = json.loads((runtime / "dependencies.json").read_text())
    for dependency in dependencies.values():
        dependency["hashes"] = package_hashes(Path(dependency["path"]))
    write_json(
        runtime / "receipt.json",
        {
            "upstream": pins,
            "source_hashes": sources,
            "installed_hashes": package_hashes(library),
            "dependencies": dependencies,
            "session": session.stdout,
        },
    )
    print("Pinned method packages installed; see .runtime/receipt.json and preflight.log")


if __name__ == "__main__":
    main()
