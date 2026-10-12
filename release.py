"""Audit and package public source using an explicit file allowlist.

Run after selecting the project license. This checks the distributed bytes;
it does not upload anything or promise that a pattern scan finds every secret.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
FILES = [
    ".gitignore", "README.md", "BUILDING.md", "INSTALL.md", "LICENSE", "THIRD_PARTY.md",
    "requirements.txt", "patch.json", "build.py", "verify.py", "release.py",
    "src/aspect_getter.s", "src/perspective_matrix.s", "src/patch_header.txt",
    "tests/test_build.py", "verify_resources.py", "layout_deltas.json",
    "src/layout_load.s", "src/animation_load.s", "src/resource_patch.s",
    "CHANGELOG.md", "VALIDATION.md", "verify_ui.py", "src/ui_scissor.s",
    "verify_capture.py", "verify_sweep.py", "src/ui_capture.s", "src/ui_capture_tail.s",
]
PATTERNS = {
    "private Windows home path": r"(?i)[a-z]:[\\/]Users[\\/][^\\/\s]+",
    "private Unix home path": r"/(?:home|Users)/[^/\s]+/",
    "private key block": r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----",
    "GitHub token": r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})",
    "AWS access ID": r"(?:AKIA|ASIA)[A-Z0-9]{16}",
    "credential assignment": r"(?im)^\s*(?:api_key|access_token|client_secret|password)\s*[:=]\s*['\"]?[^\s'\"]{12,}",
    "Switch key assignment": r"(?im)^\s*(?:header_key|master_key_[0-9a-f]+|titlekek_[0-9a-f]+)\s*=\s*[0-9a-f]{32,}",
}


def audit():
    payload = {}
    for name in FILES:
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Missing or symlinked release input: {name}")
        data = path.read_bytes()
        if len(data) > 256_000 or b"\0" in data:
            raise ValueError(f"Unexpected binary or oversized source: {name}")
        text = data.decode("utf-8")
        for label, pattern in PATTERNS.items():
            if re.search(pattern, text):
                # Do not echo potential secret contents.
                raise ValueError(f"Audit rejected {name}: {label}")
        payload[name] = data
    config = json.loads(payload["patch.json"])
    return payload, config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    payload, config = audit()
    # Never package a source release that fails its regression/build checks.
    subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-B", "build.py", "--out", str(args.out.resolve() / "build-check")], cwd=ROOT, check=True)
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(payload.items())}
    payload["SOURCE_SHA256.json"] = (json.dumps(hashes, indent=2) + "\n").encode()
    report = {
        "revision": config["revision"], "status": "source packaging checks passed",
        "correction": config.get("correction"),
        "patch_sha256": config["pchtxt_sha256"],
        "scope": "Explicitly allowlisted UTF-8 source/docs; regression suite and exact patch rebuild",
        "excluded": ["game executables/assets", "keys/saves", "emulator configs/logs", "third-party binaries/source", "caches", "private research/extraction tools"],
        "credential_and_private_path_patterns": "no matches",
        "license_file": "LICENSE", "dependencies": "Pinned in requirements.txt; installed separately",
        "limits": "Pattern scanning is not a legal clearance or a guarantee of finding every possible secret. Review changes before publication.",
        "github_upload": "not performed",
    }
    payload["RELEASE_AUDIT.json"] = (json.dumps(report, indent=2) + "\n").encode()
    args.out.mkdir(parents=True, exist_ok=True)
    archive_path = args.out / f"ACNH-3440x1440-v{config['revision']}-source.zip"
    prefix = f"ACNH-3440x1440-v{config['revision']}-source"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(f"{prefix}/{name}", (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise ValueError("Source ZIP integrity check failed")
        if set(archive.namelist()) != {f"{prefix}/{name}" for name in payload}:
            raise ValueError("Unexpected archive members")
        for name, expected in hashes.items():
            if hashlib.sha256(archive.read(f"{prefix}/{name}")).hexdigest() != expected:
                raise ValueError(f"Archived source checksum mismatch: {name}")
        for name in archive.namelist():
            data = archive.read(name)
            if b'\0' in data:
                raise ValueError('Unexpected binary in actual source archive')
            for label, pattern in PATTERNS.items():
                if re.search(pattern, data.decode('utf-8')):
                    raise ValueError(f'Archived source audit rejected {name}: {label}')
    for name in ('SOURCE_SHA256.json', 'RELEASE_AUDIT.json'):
        (ROOT / name).write_bytes(payload[name])
    print(f"Audited source ZIP: {archive_path}")


if __name__ == "__main__":
    main()
