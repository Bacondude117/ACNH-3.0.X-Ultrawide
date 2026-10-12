"""Portable deterministic v3 assembler. No game files needed to build."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
import zipfile

from keystone import Ks, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN

ROOT = Path(__file__).resolve().parent
MOD_NAME = "ACNH 3.0.3 - 3440x1440 Ultrawide - v3"


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
    for item in config.get("payloads", []):
        address = int(item["address"], 16)
        source = (ROOT / "src" / item["source"]).read_text(encoding="ascii")
        source = "\n".join(line.split("//", 1)[0] for line in source.splitlines())
        payload = bytes(assembler.asm(source, address)[0])
        require(int(config["code_padding_start"], 16) <= address
                and address + len(payload) <= int(config["code_padding_end"], 16), "Code payload exceeds padding")
        patches.append(dict(address=address, old=bytes(len(payload)), new=payload, label=item["label"]))
    table = resource_table()
    address = int(config["table_address"], 16)
    require(address + len(table) <= int(config["table_end"], 16), "Resource table exceeds read-only alignment padding")
    patches.append(dict(address=address, old=bytes(len(table)), new=table, label="Exact-resource loading and HUD deltas"))
    ordered = sorted(patches, key=lambda item: item["address"])
    for a, b in zip(ordered, ordered[1:]):
        require(a["address"] + len(a["new"]) <= b["address"], "Overlapping patch records")
    return patches


def resource_table(resources=None):
    if resources is None:
        resources = json.loads((ROOT / "layout_deltas.json").read_text())
    result = bytearray()
    seen = {}
    for resource in resources:
        changes = resource["changes"]
        key = (resource["size"], resource["fnv64"])
        require(len(changes) > 0, "Empty resource record")
        signature = [(c['offset'], c['before'], c['after']) for c in changes]
        if key in seen:
            require(seen[key] == signature, "Identical resources have conflicting deltas")
            continue
        seen[key] = signature
        offsets = set()
        groups = {}
        for change in changes:
            offset = change["offset"]
            old, new = bytes.fromhex(change["before"]), bytes.fromhex(change["after"])
            require(offset >= 20 and offset <= 65535 and offset + 4 <= resource["size"] and offset % 4 == 0,
                    "Resource delta outside bounds or unaligned")
            require(offset not in offsets and len(old) == len(new) == 4 and old != new, "Invalid resource delta")
            offsets.add(offset)
            groups.setdefault(new, []).append(offset)
        body = bytearray()
        for value, positions in groups.items():
            require(len(positions) <= 65535, 'Too many grouped offsets')
            body += struct.pack('<H', len(positions)) + value
            body += struct.pack('<'+'H'*len(positions), *positions)
        result += struct.pack('<IIQ', resource['size'], 16+len(body), int(resource['fnv64'],16)) + body
    result += bytes(16)
    return bytes(result) + bytes(-len(result) % 4)


def render_patch(config, patches):
    lines = (ROOT / "src" / "patch_header.txt").read_text(encoding="ascii").splitlines()
    require(lines[-1] == "@enabled", "Patch header must end with @enabled")
    for patch in patches:
        lines.append("// " + patch["label"])
        if int(config["code_padding_start"], 16) <= patch["address"] < int(config["code_padding_end"], 16):
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
    from verify_resources import verify_resource_hooks
    from verify_ui import check_ui_deltas, verify_scissor_hook, check_phone_menu_deltas
    from verify_capture import verify_capture_hook
    from verify_sweep import check_sweep

    config = load_config()
    patches = assemble(config)
    patch_data = render_patch(config, patches)
    digest = hashlib.sha256(patch_data).hexdigest()
    require(digest == config["pchtxt_sha256"],
            "Output differs from the recorded v3 fingerprint.")
    loader = check_loader(config, patches, patch_data)
    hooks = verify_hooks(config, patches)
    resources = verify_resource_hooks(config, patches)
    ui_checks = check_ui_deltas()
    ui_checks['scissor_hook'] = verify_scissor_hook(config, patches)
    ui_checks['phone_menus'] = check_phone_menu_deltas()
    ui_checks['capture_hook'] = verify_capture_hook(config, patches)
    ui_checks['ui_sweep'] = check_sweep()
    main_result = verify_main(main_path, config, patches) if main_path else {
        "status": "not_run", "reason": "No --verify-main supplied; game executable is not required to assemble v3."
    }
    # Do not emit a nominally successful build before validation finishes.
    package = output / MOD_NAME
    (package / "exefs").mkdir(parents=True, exist_ok=True)
    (package / "exefs" / "3440x1440.pchtxt").write_bytes(patch_data)
    (package / "README.md").write_bytes((ROOT / "INSTALL.md").read_bytes())
    for notice in ("LICENSE", "THIRD_PARTY.md"):
        (package / notice).write_bytes((ROOT / notice).read_bytes())
    report = {
        "revision": 3, "title_id": config["title_id"], "build_id": config["build_id"],
        "patch_sha256": digest, "patch_bytes": sum(len(p["new"]) for p in patches),
        "loader_check": loader, "hook_execution_tests": hooks, "original_game_verification": main_result,
        "resource_hook_tests": resources, "targeted_ui_checks": ui_checks,
        "correction": config['correction'],
        "gameplay_status": "Not verified in Eden; CPU/static validation is not gameplay confirmation.",
        "known_issue": "Object culling unchanged. See README for loading/HUD coverage and remaining test cases.",
    }
    (package / "verification.json").write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    archive = output / "ACNH-3.0.3-3440x1440-Eden-v3.zip"
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
    print("v3 assembled; loader, projection hooks, and resource hook CPU checks passed. Gameplay unverified.")
    if args.verify_main:
        print("Original NSO validation and 64 full projection tests passed.")


if __name__ == "__main__":
    main()
