# Dependencies and provenance

Third-party packages are installed separately with pip; no third-party package binaries or source are vendored in the source ZIP.

| Dependency | Version | Use | Upstream |
| --- | --- | --- | --- |
| keystone-engine | 0.9.2 | Assemble original ARM64 patch routines | https://www.keystone-engine.org/ |
| unicorn | 2.1.4 | Execute CPU-level patch tests | https://www.unicorn-engine.org/ |
| lz4 | 4.4.5 | Optional decompression of a locally supplied NSO | https://github.com/python-lz4/python-lz4 |

These dependencies retain their own upstream license terms; the project license does not relicense them. This bundle does not make a claim about the licenses of all native components based solely on Python package metadata.

The hook routines are original custom assembly, not a redistribution of Nintendo game code. The manifest contains build identifiers, cryptographic hashes, numeric addresses, and two original four-byte instructions used for validation. No full game routines, executables, assets, keys, saves, or dump/extraction tools are distributed.

Research references used during development:

- Earlier ACNH aspect-ratio work by Hyper, theboy181, victoria4dx, and OldManKain: https://gamebanana.com/mods/449287
- Eden's NSO loading and IPSwitch patch format. The local parser validator covers only this patch's hex-record subset and is independently implemented in Python: https://git.eden-emu.dev/eden-emu/eden/src/tag/v0.2.1/src/core/file_sys/ips_layer.cpp

No code from those repositories or downloaded patch archives is included here. This project is not affiliated with Nintendo or the Eden emulator project.
