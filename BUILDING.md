# Building v3

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

Output: `dist/ACNH-3.0.3-3440x1440-Eden-v3.zip`, containing the mod folder and `exefs/3440x1440.pchtxt`. The mod README comes directly from `INSTALL.md`.

The patch SHA-256 must be:

```text
b68345823fe8af80b52413309814bfd6c313cb26410821b5d95104050d11a052
```

The `.pchtxt` contains assembled machine-code/data records; Eden applies them at load time. CRLF line endings, addresses, payload bytes, and record ordering are deterministic across hosts. ZIP metadata is fixed. The verification report differs if optional game verification is requested; the patch does not.

## Optional local verification

For an already extracted, unmodified ACNH 3.0.3 `main` NSO:

```text
python -B build.py --out dist --verify-main path/to/main
```

This checks the build ID, all three NSO segment hashes, original instructions and padding, runs 64 whole-projection CPU comparisons, reproduces the old minimap clipping error in eight executions, tests corrected clipping with 52 executions of the game routine, and runs 32 background-copy coordinate checks plus four original material-projection executions with 28 coordinate samples. Do not add the NSO to this source project or its archive.

Developers with the specific original `.bflyt`/`.bflan` resources listed in `layout_deltas.json` can call `verify_resources.verify_local_resources(directory, config, patches)` to validate their hashes and run the actual-resource CPU checks. These files are not required to build or run the public regression suite. Extraction/decryption tools and keys are not distributed here.

`verify_ui.verify_local_ui(directory)` additionally parses the corrected DAL/minimap layouts and 19 phone/menu/wipe layouts. It checks mask coverage, retained foreground/material geometry, capture alignment, and 60 interpolated samples from 12 resized animation segments. These checks are not GPU tests.

`verify_sweep.verify_local_sweep(directory)` checks the 47 additional layouts against their original hashes, validates 39 embedded background overrides and eight capture-material projection fields, and rejects unrelated foreground geometry changes. The public tests additionally execute the new capture hook 128 times without requiring a game file.

## Source packaging

```text
python -B release.py --out release
```

This runs the regression suite and exact-byte build, audits an explicit allowlist, creates `ACNH-3440x1440-v3-source.zip`, checks the actual archive members and bytes, and records source hashes/audit results. It does not upload anything.

For a fresh-source reproduction, extract that archive into a new directory, install the pinned dependencies separately, and run the build commands again. Compare the patch SHA-256 with the value above. Never package the whole workspace or `.venv` directory.

## Modifying the patch

The resource table is generated entirely from `layout_deltas.json`. Each entry starts with u32 file length, u32 total entry length and a u64 whole-file FNV-1a identity. Writes sharing a replacement value are grouped as u16 count, u32 replacement and that many u16 byte offsets. A zero-size entry ends the table. Normal-memory reads can be unaligned; all write offsets must be four-byte aligned, at most 65535 and within the identified resource. Identical resources are deduplicated only when their deltas agree. Grouping keeps the expanded manifest within the verified padding without changing the resource-match policy.

Most writes are float fields/keyframes. Two writes zero the single-entry user-data counts for minimap `ScissorOn` registration; setting its value to zero would not work because the 3.0.3 pane factory checks property presence. Background-only changes include explicit `prt1` embedded overrides, which otherwise replace the shared background's dimensions at instantiation.

The two resource hooks preserve registers/flags and replay the replaced instruction. The shared routine compares the complete loaded resource before writing. Changed resources, including resources already patched during this process, do not match. No repeated offset accumulates.

`src/ui_scissor.s` corrects the horizontal conversion in the verified 3.0.3 ScissorPane calculation at `03A308E8`. It reads the current UI projection and preserves scratch registers/flags. Perspective clipping uses viewportWidth/layoutHeight * abs(m00/m11), while orthographic and capture-local paths keep their original behavior. Public CPU tests exercise this hook without a game file.

`src/ui_capture.s` and `src/ui_capture_tail.s` hook `03A2EABC`. For perspective draws they multiply the original normalized copy width by abs(m00/m11) * layoutWidth/layoutHeight; the subsequent game instructions therefore also produce the correct horizontal source center. Orthographic draws replay the original division. This replaces the earlier phone-specific 32/43 preprojection in the resource deltas, avoiding double correction. Eight selected Entire Layout material projectors use X scale 43/32 because the original texture-coordinate routine divides by that scale. The optional original-code tests verify that direction.

Executable code uses verified text alignment padding; the table uses verified read-only segment alignment padding. This depends on Eden's page-aligned desktop NSO loader. Do not assume console hardware or another loader supports it.

If changing source or deltas, intentionally regenerate `pchtxt_sha256` in `patch.json`, update the documented fingerprint and tests, and repeat original-byte, conflict, archive, and fresh-extraction checks. Passing assembly/CPU tests does not establish correct in-game rendering.
