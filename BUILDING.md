# Building v4

Use Python 3.11 or later on a desktop platform supported by the pinned Keystone and Unicorn packages. Building requires no game dump, SDK, encryption key, asset, or Nintendo toolchain.

From the extracted source directory:

```text
python -m venv .venv
```

Activate the environment (`.venv\Scripts\activate` on Windows Command Prompt, or `source .venv/bin/activate` on Linux/macOS), then:

```text
python -m pip install -r requirements.txt
python -B -m unittest discover -s tests -v
python -B build.py --out dist
```

Output: `dist/ACNH-3.0.3-3440x1440-Eden-v4.zip`, containing the mod folder and `exefs/3440x1440.pchtxt`. The mod README comes directly from `INSTALL.md`.

The patch SHA-256 must match the `pchtxt_sha256` value in `patch.json` for this v4 source release:

```text
0633440e57dd94ec91f7b053d561e7d42a114e11032e068a70b3ee1c122cbf0a
```

The `.pchtxt` contains assembled machine-code/data records; Eden applies them at load time. CRLF line endings, addresses, payload bytes, and record ordering are deterministic across hosts. ZIP metadata is fixed. The verification report differs if optional game verification is requested; the patch does not.

## Optional local verification

For an already extracted, unmodified ACNH 3.0.3 `main` NSO:

```text
python -B build.py --out dist --verify-main path/to/main
```

This checks the build ID, all three NSO segment hashes, original instructions and padding (including the create-range hook at `013A29A4` and the tree/item-area hooks at `01126144`, `01125FE4` and `0112616C`), executes the original create-range and area functions before and after patching, runs 64 whole-projection CPU comparisons, reproduces the old minimap clipping error in eight executions, tests corrected clipping with 52 executions of the game routine, and runs 32 background-copy coordinate checks plus four original material-projection executions with 28 coordinate samples. Do not add the NSO to this source project or its archive.

Developers with the specific original `.bflyt`/`.bflan` resources listed in `layout_deltas.json` can call `verify_resources.verify_local_resources(directory, config, patches)` to validate their hashes and run the actual-resource CPU checks. These files are not required to build or run the public regression suite. Extraction/decryption tools and keys are not distributed here.

`verify_ui.verify_local_ui(directory)` additionally parses the corrected DAL/minimap layouts and 19 phone/menu/wipe layouts. It checks mask coverage, retained foreground/material geometry, capture alignment, and 60 interpolated samples from 12 resized animation segments. These checks are not GPU tests.

`verify_sweep.verify_local_sweep(directory)` checks the 47 additional layouts against their original hashes, validates 39 embedded background overrides and eight capture-material projection fields, and rejects unrelated foreground geometry changes. The public tests additionally execute the new capture hook 128 times without requiring a game file.

## Source packaging

```text
python -B release.py --out release
```

This runs the regression suite and exact-byte build, audits an explicit allowlist, creates `ACNH-3440x1440-v4-source.zip`, checks the actual archive members and bytes, and records source hashes/audit results. It does not upload anything.

For a fresh-source reproduction, extract that archive into a new directory, install the pinned dependencies separately, and run the build commands again. Compare the patch SHA-256 with the value above. Never package the whole workspace or `.venv` directory.

## Modifying the patch

The resource table is generated entirely from `layout_deltas.json`. Each entry starts with u32 file length, u32 total entry length and a u64 whole-file FNV-1a identity. Writes sharing a replacement value are grouped as u16 count, u32 replacement and that many u16 byte offsets. A zero-size entry ends the table. Normal-memory reads can be unaligned; all write offsets must be four-byte aligned, at most 65535 and within the identified resource. Identical resources are deduplicated only when their deltas agree. Grouping keeps the expanded manifest within the verified read-only padding without changing the resource-match policy. The FNV offset basis and prime are stored at the verified table-adjacent addresses `04724F80` and `04724F88`.

Most writes are float fields/keyframes. Two writes zero the single-entry user-data counts for minimap `ScissorOn` registration; setting its value to zero would not work because the 3.0.3 pane factory checks property presence. Background-only changes include explicit `prt1` embedded overrides, which otherwise replace the shared background's dimensions at instantiation.

The two resource hooks preserve registers/flags and replay the replaced instruction. The shared routine compares the complete loaded resource before writing. Changed resources, including resources already patched during this process, do not match. No repeated offset accumulates.

`src/ui_scissor.s` corrects the horizontal conversion in the verified 3.0.3 ScissorPane calculation at `03A308E8`. It reads the current UI projection and preserves scratch registers/flags. Perspective clipping uses viewportWidth/layoutHeight * abs(m00/m11), while orthographic and capture-local paths keep their original behavior. Public CPU tests exercise this hook without a game file.

`src/ui_capture.s` and `src/ui_capture_tail.s` hook `03A2EABC`. For perspective draws they multiply the original normalized copy width by abs(m00/m11) * layoutWidth/layoutHeight; the subsequent game instructions therefore also produce the correct horizontal source center. Orthographic draws replay the original division. This replaces the earlier phone-specific 32/43 preprojection in the resource deltas, avoiding double correction. Eight selected Entire Layout material projectors use X scale 43/32 because the original texture-coordinate routine divides by that scale. The optional original-code tests verify that direction.

Executable code uses verified text alignment padding; the table uses verified read-only segment alignment padding. This depends on Eden's page-aligned desktop NSO loader. Do not assume console hardware or another loader supports it.

`src/create_range.s` hooks the 3.0.3 field create-range function `013A2864` at `013A29A4` (original `fsub s0, s10, s9`). There `S9`/`S13` hold `mCreateRangeLeft`/`mCreateRangeRight`, `S8`/`S12` hold Far/Near depth and stack `+0x18` holds `mCreateRangeTilt` (offsets mapped from the constructor at `013A6D20`). The hook multiplies Left, Right and Tilt by 1.5 (`fmov s0, #1.5`), replays the instruction and returns to `013A29A8`.

`src/area_range.s` and `src/area_tilt.s` hook the tree/item area function `01125DDC`, called four times from `010D7158`.. for the tree area (`mTreeArea*`) and item area (`mArea*`), each with and without the Width/Near/Far buffers. Parameter offsets (`+0x8450..+0x8690`) come from the registration code at `011227A0`. At `01126144` (normal path) and `01125FE4` (an alternate scene path with zero tilt) `S8`/`S9` hold Left/Right; both sites `bl` into one shared routine at `03F06E30` that scales them by 1.5, replays `ldr s0, [x20]` and returns with `ret` (LR is already saved by `01125DDC`). At `0112616C` the Tilt value is loaded into `S3`; that hook scales it by 1.5 using the otherwise unused, caller-saved `S7`. Depth terms are untouched.

To fit these hooks, `src/aspect_getter.s` and `src/perspective_matrix.s` were rewritten as short routines that follow the AArch64 procedure call standard. Both replace the first instruction of complete functions, so they use only caller-saved scratch (`S1`, `X16`, flags). The getter returns 43:18 for exact stock 16:9. The matrix routine calls it, stores the result at `+0xB0` and replays its original load. Payload layout: `03F06DF0` create range, `03F06E10` getter, `03F06E30` shared area range, `03F06E44` field-unit pool, `03F06E90` matrix, `03F06EA8` area tilt, `03F06EB8` terrain cell-group sphere. `verify_create_range.py` and `verify_area_range.py` execute every hook at two load bases. With `--verify-main` they run the original functions end to end, unpatched and patched (35 create-range and 160 area executions). Disable earlier ultrawide versions: v2 writes into part of this same gap.

`src/terrain_cell_sphere.s` replaces `013A37B4` (`fcmp s0, s1`) in the terrain-cell loop. It sets the group radius to half of sqrt(X^2 + Z^2 + extent^2), then continues at the original sphere/frustum call at `013A37C8`. `verify_culling.py` runs it 24 times.

`src/unit_max.s` replaces `01462BB4` (`ldr w8, [x0]`). That instruction loads `FieldUnitModelParam.mUnitMax`, and `01462BB8` stores it at manager `+0x6E8`. The cave loads the value, doubles it and returns. The stored count sizes the field-unit instance buffers (`0146534C`, `014654C8`) and unit array (`014663EC`). At draw time, units beyond it reuse slot 0 (`0146ABF4`). `verify_unit_max.py` runs the hook 24 times.

If changing source or deltas, intentionally regenerate `pchtxt_sha256` in `patch.json`, update the documented fingerprint and tests, and repeat original-byte, conflict, archive, and fresh-extraction checks. Passing assembly/CPU tests does not establish correct in-game rendering.
