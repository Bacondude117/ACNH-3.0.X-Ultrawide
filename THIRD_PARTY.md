# Dependencies and provenance

Third-party packages are installed separately with pip; no third-party package binaries or source are vendored in the source ZIP.

| Dependency | Version | Use | Upstream |
| --- | --- | --- | --- |
| keystone-engine | 0.9.2 | Assemble original ARM64 patch routines | https://www.keystone-engine.org/ |
| unicorn | 2.1.4 | Execute CPU-level patch tests | https://www.unicorn-engine.org/ |
| lz4 | 4.4.5 | Optional decompression of a locally supplied NSO | https://github.com/python-lz4/python-lz4 |

These dependencies retain their own upstream license terms; the project license does not relicense them. This bundle does not make a claim about the licenses of all native components based solely on Python package metadata.

The hook routines and public build/test tools, including the capture hook, grouped-resource writer, UI checks, and v4 create-range and tree/item-area hooks, are original project source. The manifests contain build identifiers, hashes, numeric addresses, ten original four-byte instructions for validation/replay, resource names, and numeric field deltas. Optional scissor/capture/material regressions read the user's own verified executable; their game routines are not embedded in source. No full game routines, executables, assets, keys, saves, or dump/extraction tools are included. The project MIT-0 license covers original project source; it does not claim ownership of Nintendo's game or resource names.

Research references used during development:

- Earlier ACNH aspect-ratio work by Hyper, theboy181, victoria4dx, and OldManKain: https://gamebanana.com/mods/449287
- Eden's NSO loading and IPSwitch patch format. The local parser validator covers only this patch's hex-record subset and is independently implemented in Python: https://git.eden-emu.dev/eden-emu/eden/src/tag/v0.2.1/src/core/file_sys/ips_layer.cpp
- Eden NSO segment alignment and patch application, inspected to verify the padding model: https://github.com/eden-emulator/mirror/blob/master/src/core/loader/nso.cpp
- BFLAN format documentation used as a format reference; no parser source was copied: https://github.com/Tyulis/3DSkit/blob/master/doc/BFLAN.md
- BFLYT material/texture-coordinate format reference; no parser source was copied: https://github.com/Tyulis/3DSkit/blob/master/doc/BFLYT.md
- Older aspect-ratio patch collection, used only as a research reference: https://github.com/lucasgamer489/Switch-Ultrawide-Mods
- Older ACNH HUD mod by Fl4sh_: https://gamebanana.com/mods/489594 . Its archive membership was inspected as a research reference. Its CC BY-NC-ND license does not authorize incorporating adaptations into MIT-0; none of its code or assets was copied or adapted. All v3 layout changes were derived independently from the local 3.0.3 resources.

No code from those repositories or downloaded patch archives is included here. This project is not affiliated with Nintendo or the Eden emulator project.

For the UI sweep, material projection direction, embedded part overrides, resource identities and instruction sites were checked against the local 3.0.3 files. The v4 create-range and tree/item-area hook sites, original instructions, parameter offsets (from the 3.0.3 parameter constructor), scratch-register liveness and continuation were checked in the local 3.0.3 `main` NSO, and the original function was executed before and after patching; the full executable is not distributed. The earlier v4 actor-bounds and terrain-cell sphere hooks were removed. Older aspect-ratio patches were reviewed: they change only the projection aspect and do not address the create range. Older format notes and mods were not treated as evidence that offsets or rendering behavior were unchanged in 3.0.3.
