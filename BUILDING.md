# ACNH 3.0.3 — 3440×1440 ultrawide v2 source

This is the complete original source needed to assemble the **v2** ExeFS patch for Eden. It reproduces the working v2 `3440x1440.pchtxt` byte for byte. It does **not** include the later v3 loading-screen correction.

No game executable, game assets, save data, keys, emulator, or personal paths are included. A game executable is **not required to build the patch**. Optional deeper checks use the builder's own extracted ExeFS `main`.

## Requirements

- Python 3.12 is the tested version (64-bit Windows).
- Install the three pinned Python packages in `requirements.txt`.
- Internet access is needed for the initial dependency installation unless the packages are already available locally. Nothing is downloaded by the build script itself.

The scripts use portable Python paths and can also run on Linux/macOS where the dependency packages support the platform; those platforms have not been tested for this release.

## Build on Windows

Extract this entire source folder, open a terminal in it, then run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe build.py
```

If your Python installation does not provide `py`, replace `py -3.12` with `python`.

## Build on Linux/macOS

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python build.py
```

The result is `dist/ACNH-3.0.3-3440x1440-Eden-v2.zip`, plus its unpacked mod folder. Use `--out DIRECTORY` to select a different output directory. The build never installs the mod or changes emulator settings.

The patch file's SHA-256 must be:

```text
5be72a4fbcc998a6f094256c88e93e77cf8ed4f8f758a0e0ddf11597561bb00b
```

The build fails if this fingerprint differs. Patch-file bytes match the original v2 release; the generated ZIP and its verification report have new portable packaging and therefore are not identical to the original release ZIP.

## Tests

The default build assembles both routines from the `.s` source files, checks the exact release fingerprint, checks Eden's patch-block parsing, and executes 128 hook tests using an ARM64 CPU emulator. No game data is required for those checks.

Run the additional regression suite with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

For full verification against your own unmodified 3.0.3 executable:

```powershell
.\.venv\Scripts\python.exe build.py --verify-main "D:\MyDump\exefs\main"
```

On Linux/macOS, use `.venv/bin/python` instead. The input must be the extracted **main NSO**, not an XCI, NSP, NCA, or the entire ExeFS directory. Compressed and decompressed NSO segments are supported. Container extraction is outside this project; no keys are read or needed here.

This optional step validates the exact build ID, all three segment layouts and SHA-256 hashes, original hook instructions, and padding. It then runs 64 complete original-versus-patched projection-matrix comparisons. The file is only read and is never copied into the output.

## Supported build and behavior

- Animal Crossing: New Horizons 3.0.3, Switch version
- Title ID: `01006F8002326000`
- Main build ID: `FF1D1C05670DB6021C85B624A710B963`
- Display: 3440×1440 landscape, exact aspect 43:18
- Emulator: Eden desktop with Stretch to Window

The patch changes a native float32 16:9 perspective aspect to float32 43:18. It does not change internal rendering resolution. The user confirmed v2's wider gameplay view works.

**Known v2 issue:** loading screens at startup and between buildings can leave terrain visible at the sides. This archive intentionally preserves v2, including that issue. HUDs and menus may also stretch. This is an emulator patch using NSO code-segment alignment padding, not a physical-Switch/Atmosphere patch.

## Files

| File | Purpose |
| --- | --- |
| `src/aspect_getter.s` | Conditional aspect getter, with preserved registers and flags |
| `src/perspective_matrix.s` | Conditional perspective-matrix entry hook |
| `src/patch_header.txt` | Exact v2 IPSwitch metadata and header |
| `patch.json` | Build ID, addresses, expected original bytes, segment hashes, release fingerprint |
| `build.py` | Assembles, validates, and packages the mod |
| `verify.py` | Patch-loader and ARM64 tests; optional original-NSO verification |
| `tests/test_build.py` | Release, parsing, CPU, invalid-input, and packaging regression tests |
| `requirements.txt` | Pinned third-party dependencies |
| `INSTALL.md` | Instructions included in the generated mod ZIP |

There are no hidden helper files or required paths outside this folder. Third-party dependency source is not vendored; install the declared packages with pip.

## License and public releases

The original code and documentation in this project use **MIT No Attribution (MIT-0)**; see `LICENSE`. No third-party source is copied into this project. Separately installed dependencies retain their own licenses, described in `THIRD_PARTY.md`. The license does not cover Nintendo's game or any other external software.

To create an audited GitHub-ready source ZIP, run:

```powershell
.\.venv\Scripts\python.exe release.py
```

This runs the regression suite and exact v2 rebuild, scans the selected source for credential/private-path patterns, and packages only an explicit allowlist. The archive includes source hashes and `RELEASE_AUDIT.json`. It does not publish anything. Use the audited source ZIP or its extracted contents for the repository, not the parent development workspace, game dump, emulator folder, or dependency environment.

Future versions must update the manifest, tests, known issues, and file allowlist; review any new third-party code before licensing it. Run this release check and rebuild from a fresh extraction before delivery. Automated scanning supports a source review; it is not a legal clearance or an exhaustive secret detector.

## Implementation notes

The getter at `0x037E594C` branches to `0x03F06E00`. The matrix entry at `0x037E5968` branches to `0x03F06E80`. The routines use otherwise unused executable alignment padding below `0x03F07000`, preserve x15–x17 and NZCV, and keep the stack 16-byte aligned. All addresses are module-relative.

The `.pchtxt` uses `@flag offset_shift 0x100` for the NSO-header offset. Keep all 33 four-byte records in a continuous enabled block: a blank line inside the block makes Eden v0.2.1 stop reading it. The build regression test reproduces this original v1 failure.

Keystone assembles the source, Unicorn executes the hook tests, and lz4 reads compressed NSO segments for optional verification. Their code is not included in this archive. This is the source for a standalone custom patch; it does not require or include Eden's source code.

To develop a different patch, update the assembly and configuration deliberately, including the expected fingerprint and relevant tests. Changing only the build ID cannot port this mod to a different game version.
