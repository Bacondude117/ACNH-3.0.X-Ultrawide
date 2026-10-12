"""Loader, ARM64 hook, and optional original-NSO verification. No game data included."""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
import random
import re
import struct

from build import require

NATIVE = struct.unpack("<I", struct.pack("<f", 16 / 9))[0]
WIDE = struct.unpack("<I", struct.pack("<f", 3440 / 1440))[0]
RATIOS = [16 / 9, 3440 / 1440, 1., 4 / 3, 16 / 10, 2., 32 / 9, 0.5]


def loader_records(data):
    """Eden v0.2.1 rules relevant to our hex-only patch format.

    Crucially, empty lines terminate an enabled block. This is a deliberately
    narrow validator, not a general implementation of every IPSwitch feature.
    """
    active = False
    shift = 0
    records = []
    for line in data.decode("ascii").splitlines():
        if line.startswith("//"):
            continue
        if not line:
            active = False
            continue
        if line == "@stop":
            break
        if line.startswith("@flag offset_shift "):
            shift = int(line.split()[-1], 0)
        elif line == "@enabled":
            active = True
        elif line == "@disabled":
            active = False
        elif active and re.fullmatch(r"[0-9A-F]{8} [0-9A-F]+", line):
            address, value = line.split()
            records.append((int(address, 16) + shift - 0x100, bytes.fromhex(value)))
    return records


def check_loader(config, patches, data):
    expected = [(p["address"] + offset, p["new"][offset:offset + 4])
                for p in patches for offset in range(0, len(p["new"]), 4)]
    require(data.startswith(f"@nsobid-{config['build_id']}\r\n".encode("ascii")), "Incorrect build ID")
    require(loader_records(data) == expected,
            "Eden would not read every record")
    broken = data.replace(b"@enabled\r\n", b"@enabled\r\n\r\n", 1)
    require(loader_records(broken) == [], "Blank-line regression check failed")
    return {"records": len(expected), "payload_bytes": sum(len(p['new']) for p in patches), "blank_line_regression": "passed"}


def _deps():
    import unicorn
    from unicorn import arm64_const as r
    return unicorn, r


def _machine(patches, relocation=0, original=None):
    unicorn, r = _deps()
    u = unicorn.Uc(unicorn.UC_ARCH_ARM64, unicorn.UC_MODE_ARM)
    pages = {0x37e5000, 0x3f06000}
    for patch in patches:
        pages.update(range(patch['address'] & ~4095, (patch['address'] + len(patch['new']) + 4095) & ~4095, 4096))
    for page in sorted(pages):
        u.mem_map(relocation + page, 0x1000)
        if original is not None:
            u.mem_write(relocation + page, bytes(original[page:page + 0x1000]))
    for patch in patches:
        u.mem_write(relocation + patch["address"], patch["new"])
    u.mem_map(0x100000, 0x1000)
    u.mem_map(0x200000, 0x3000)
    for index in range(29):
        u.reg_write(r.UC_ARM64_REG_X0 + index, 0x123400 + index)
    u.reg_write(r.UC_ARM64_REG_SP, 0x202ff0)
    u.reg_write(r.UC_ARM64_REG_X0, 0x200000)
    u.reg_write(r.UC_ARM64_REG_X1, 0x201000)
    u.reg_write(r.UC_ARM64_REG_LR, 0x100000)
    return u


def _projection(u, ratio, near=1., far=10000., tanhalf=.6, offsetx=0., offsety=0.):
    for offset, value in [(0x98, near), (0x9c, far), (0xac, tanhalf),
                          (0xb0, ratio), (0xb4, offsetx), (0xb8, offsety)]:
        u.mem_write(0x200000 + offset, struct.pack("<f", value))


def _registers(u):
    _, r = _deps()
    ids = [r.UC_ARM64_REG_X0 + index for index in range(29)]
    ids += [r.UC_ARM64_REG_FP, r.UC_ARM64_REG_LR, r.UC_ARM64_REG_SP, r.UC_ARM64_REG_NZCV]
    return [u.reg_read(reg) for reg in ids]


def verify_hooks(config, patches):
    _, r = _deps()
    count = 0
    for relocation in (0, 0x7100000000):
        for ratio in RATIOS:
            bits = struct.unpack("<I", struct.pack("<f", ratio))[0]
            expected = WIDE if bits == NATIVE else bits
            for flags in (0, 0x90000000, 0x60000000, 0xf0000000):
                for index, hook in enumerate(config["hooks"][:2]):
                    site = int(hook["site"], 16)
                    u = _machine(patches, relocation)
                    _projection(u, ratio)
                    u.reg_write(r.UC_ARM64_REG_NZCV, flags)
                    before = _registers(u)
                    # Run from the actual patched instruction to its original
                    # continuation. No copy of the game's function is needed.
                    u.emu_start(relocation + site, relocation + site + 4, count=100)
                    require(u.reg_read(r.UC_ARM64_REG_PC) == relocation + site + 4, "Hook failed to return")
                    require(_registers(u) == before, "Hook changed GPRs, stack, or processor flags")
                    actual_s0 = u.reg_read(r.UC_ARM64_REG_S0)
                    require(actual_s0 == (expected if index == 0 else 0x3f800000), "Unexpected S0 result")
                    stored = bytes(u.mem_read(0x200000 + 0xb0, 4))
                    require(stored == struct.pack("<I", bits if index == 0 else expected), "Unexpected camera aspect")
                    count += 1
    require(count == 128, "Unexpected hook-test count")
    return {"executions": count, "load_bases": 2, "aspect_ratios": 8, "flag_states": 4}


def load_main(path, config):
    import lz4.block

    raw = Path(path).read_bytes()
    require(len(raw) >= 0x100 and raw[:4] == b"NSO0", "Input must be an extracted main NSO")
    require(raw[0x40:0x60] == bytes.fromhex(config["build_id"].ljust(64, "0")), "Wrong main build ID; expected ACNH 3.0.3")
    flags = struct.unpack_from("<I", raw, 0xc)[0]
    image = bytearray(int(config["image_size"], 16))
    checks = []
    for index, expected in enumerate(config["verified_nso_segments"]):
        file_offset, address, size = struct.unpack_from("<III", raw, 0x10 + index * 16)
        compressed = bool(flags & (1 << index))
        stored_size = struct.unpack_from("<I", raw, 0x60 + index * 4)[0] if compressed else size
        require(address == int(expected["address"], 16) and size == expected["size"], "Unexpected NSO segment layout")
        require(file_offset >= 0x100 and file_offset + stored_size <= len(raw), "Truncated NSO segment")
        require(address + size <= len(image), "NSO segment outside expected image")
        stored = raw[file_offset:file_offset + stored_size]
        unpacked = lz4.block.decompress(stored, uncompressed_size=size) if compressed else stored
        require(len(unpacked) == size, "Incorrect decompressed segment length")
        digest = hashlib.sha256(unpacked).digest()
        require(digest.hex() == expected["sha256"], "Original NSO segment differs from verified 3.0.3 build")
        require(digest == raw[0xa0 + index * 32:0xc0 + index * 32], "Embedded NSO segment checksum mismatch")
        image[address:address + size] = unpacked
        checks.append({"address": f"{address:08X}", "size": size, "sha256": digest.hex()})
    return image, checks


def verify_main(path, config, patches):
    image, checks = load_main(path, config)
    for patch in patches:
        address = patch["address"]
        require(image[address:address + len(patch["old"])] == patch["old"],
                f"Unexpected original bytes at {address:08X}")
    rng = random.Random(34401440)
    for index in range(64):
        ratio = RATIOS[index % len(RATIOS)]
        settings = dict(near=rng.uniform(.1, 5), far=rng.uniform(100, 20000),
                        tanhalf=rng.uniform(.2, 1.2), offsetx=rng.uniform(-.4, .4), offsety=rng.uniform(-.4, .4))
        original = _machine([], original=image)
        modified = _machine(patches, original=image)
        for u in (original, modified):
            _projection(u, ratio, **settings)
            u.emu_start(0x37e5968, 0x100000, count=500)
            _, r = _deps()
            require(u.reg_read(r.UC_ARM64_REG_PC) == 0x100000, "Matrix function did not return")
        a = struct.unpack("<16f", bytes(original.mem_read(0x201000, 64)))
        b = struct.unpack("<16f", bytes(modified.mem_read(0x201000, 64)))
        if struct.pack("<f", ratio) == struct.pack("<I", NATIVE):
            require(math.isclose(b[0] / a[0], 32 / 43, rel_tol=2e-6), "Wrong horizontal projection scale")
            require(all(math.isclose(b[i], a[i], rel_tol=2e-6, abs_tol=2e-6) for i in range(1, 16)),
                    "Patch changed vertical/depth/offset projection entries")
        else:
            require(a == b, "A non-native camera ratio was changed")
    from verify_ui import verify_scissor_regression, verify_projected_scissors
    from verify_capture import verify_capture_coordinates, verify_material_projection
    return {"status": "passed", "verified_segments": checks, "full_matrix_tests": 64,
            "minimap_scissor_regression": verify_scissor_regression(image),
            "projected_ui_scissors": verify_projected_scissors(image, patches),
            "background_capture_coordinates": verify_capture_coordinates(image, patches),
            "capture_material_projection": verify_material_projection(image)}
