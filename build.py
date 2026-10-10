"""Portable, deterministic assembler and packager for the exact v2 patch."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from keystone import Ks, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN

ROOT = Path(__file__).resolve().parent
MOD_NAME = "ACNH 3.0.3 - 3440x1440 Ultrawide - v2"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_config():
    return json.loads((ROOT / "patch.json").read_text(encoding="utf-8"))


def assemble(config):
    assembler = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)
    patches = []
    for hook in config["hooks"]:
        site, cave = int(hook["site"], 16), int(hook["cave"], 16)
        source = (ROOT / "src" / hook["source"]).read_text(encoding="ascii")
        # Comments are documentation, not assembler input.
        source = "\n".join(line.split("//", 1)[0] for line in source.splitlines())
        payload = bytes(assembler.asm(source, cave)[0])
        branch = bytes(assembler.asm(f"b #{cave}", site)[0])
        original = bytes.fromhex(hook["original"])
        require(len(branch) == len(original) == 4, "Hook branch must be one ARM64 instruction")
        require(len(payload) % 4 == 0, "Unaligned hook payload")
        require(int(config["code_padding_start"], 16) <= cave
                and cave + len(payload) <= int(config["code_padding_end"], 16),
                "Hook exceeds executable alignment padding")
        patches.extend([
            {"address": site, "old": original, "new": branch, "label": hook["site_label"]},
            {"address": cave, "old": bytes(len(payload)), "new": payload, "label": hook["cave_label"]},
        ])
    ordered = sorted(patches, key=lambda item: item["address"])
    for a, b in zip(ordered, ordered[1:]):
        require(a["address"] + len(a["new"]) <= b["address"], "Overlapping patch records")
    return patches


def render_patch(config, patches):
    lines = (ROOT / "src" / "patch_header.txt").read_text(encoding="ascii").splitlines()
    require(lines[-1] == "@enabled", "Patch header must end with @enabled")
    for patch in patches:
        lines.append("// " + patch["label"])
        if patch["address"] >= int(config["code_padding_start"], 16):
            lines.append("// Code lives in the executable segment alignment padding; requires Eden-style NSO loading.")
        for offset in range(0, len(patch["new"]), 4):
            lines.append(f"{patch['address'] + offset:08X} {patch['new'][offset:offset + 4].hex().upper()}")
    lines.extend(["", "@stop"])
    # Original v2 release used CRLF. Explicit bytes make builds identical on
    # Windows, Linux, and macOS rather than depending on host newline handling.
    return ("\r\n".join(lines) + "\r\n").encode("ascii")


def package_zip(path, package, members=None):
    # Stable timestamps/order/permissions; no compression-library variation.
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        entries = package.rglob("*") if members is None else (package / name for name in members)
        for entry in sorted(entries):
            if not entry.is_file():
                continue
            info = zipfile.ZipInfo(f"{package.name}/{entry.relative_to(package).as_posix()}",
                                   date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, entry.read_bytes())


def build(output, main_path=None):
    from verify import check_loader, verify_hooks, verify_main

    config = load_config()
    patches = assemble(config)
    patch_data = render_patch(config, patches)
    digest = hashlib.sha256(patch_data).hexdigest()
    require(digest == config["pchtxt_sha256"],
            "Output differs from the v2 release. If intentionally modifying it, update the fingerprint and tests.")
    loader = check_loader(config, patches, patch_data)
    hooks = verify_hooks(config, patches)
    main_result = verify_main(main_path, config, patches) if main_path else {
        "status": "not_run", "reason": "No --verify-main supplied; game executable is not required to assemble v2."
    }
    # Do not emit a nominally successful build before validation finishes.
    package = output / MOD_NAME
    (package / "exefs").mkdir(parents=True, exist_ok=True)
    (package / "exefs" / "3440x1440.pchtxt").write_bytes(patch_data)
    (package / "README.md").write_bytes((ROOT / "INSTALL.md").read_bytes())
    for notice in ("LICENSE", "THIRD_PARTY.md"):
        (package / notice).write_bytes((ROOT / notice).read_bytes())
    report = {
        "revision": 2, "title_id": config["title_id"], "build_id": config["build_id"],
        "patch_sha256": digest, "patch_bytes": sum(len(p["new"]) for p in patches),
        "loader_check": loader, "hook_execution_tests": hooks, "original_game_verification": main_result,
        "known_issue": "v2 loading-screen overlays can leave terrain visible at the sides; v3 is not included.",
    }
    (package / "verification.json").write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    archive = output / "ACNH-3.0.3-3440x1440-Eden-v2.zip"
    package_zip(archive, package, ["exefs/3440x1440.pchtxt", "README.md", "verification.json", "LICENSE", "THIRD_PARTY.md"])
    return archive, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "dist", help="Build output directory")
    parser.add_argument("--verify-main", type=Path,
                        help="Optional extracted 3.0.3 ExeFS main NSO for original-byte and full-matrix checks")
    args = parser.parse_args()
    try:
        archive, report = build(args.out.resolve(), args.verify_main)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Build failed: {error}\n")
    print(f"Built: {archive}\nPatch SHA-256: {report['patch_sha256']}")
    print("v2 patch reproduced exactly; loader and 128 hook execution checks passed.")
    if args.verify_main:
        print("Original NSO validation and 64 full projection tests passed.")


if __name__ == "__main__":
    main()
