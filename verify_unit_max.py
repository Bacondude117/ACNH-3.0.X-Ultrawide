"""CPU checks for the ACNH 3.0.3 field-unit model pool (mUnitMax) doubling.

verify_unit_max_hook() executes the installed branch and cave in isolation; no
game files are needed. The cave must load mUnitMax, double it in W8, change no
other general-purpose register, flag, or floating-point register, and return
to 01462BB8, where the original code stores W8 at manager +0x6E8.
"""
import random

from build import require
from verify import _deps, _machine

SITE, BACK, ORIGINAL = 0x01462BB4, 0x01462BB8, '080040B9'
FACTOR = 2


def verify_unit_max_hook(config, patches):
    _, r = _deps()
    hook = next(h for h in config['hooks'] if h['source'] == 'unit_max.s')
    require(int(hook['site'], 16) == SITE and hook['original'] == ORIGINAL,
            'mUnitMax hook no longer matches its verified 3.0.3 instruction')
    rng = random.Random(2000)
    values = [2000, 1, 0, 1500, 4096, 0x3FFFFFFF] + [rng.randrange(1, 20000) for _ in range(6)]
    executions = 0
    for relocation in (0, 0x7100000000):
        for value in values:
            u = _machine(patches, relocation)
            u.mem_write(0x201800, value.to_bytes(4, 'little'))
            u.reg_write(r.UC_ARM64_REG_X0, 0x201800)
            u.reg_write(r.UC_ARM64_REG_X8, 0xDEADBEEFCAFEF00D)
            u.reg_write(r.UC_ARM64_REG_NZCV, 0x60000000)
            keep = [r.UC_ARM64_REG_X0 + i for i in range(29) if i != 8] + [
                r.UC_ARM64_REG_FP, r.UC_ARM64_REG_LR, r.UC_ARM64_REG_SP, r.UC_ARM64_REG_NZCV]
            keep += [r.UC_ARM64_REG_D0 + i for i in range(32)]
            before = [u.reg_read(x) for x in keep]
            u.emu_start(relocation + SITE, relocation + BACK, count=8)
            require(u.reg_read(r.UC_ARM64_REG_PC) == relocation + BACK, 'mUnitMax hook did not return to 01462BB8')
            require([u.reg_read(x) for x in keep] == before, 'mUnitMax hook changed a preserved register or flags')
            require(u.reg_read(r.UC_ARM64_REG_X8) == (value * FACTOR) & 0xFFFFFFFF,
                    'mUnitMax was not doubled into W8 (upper half must be zero)')
            executions += 1
    return {'executions': executions, 'load_bases': 2, 'factor': FACTOR,
            'site': f'{SITE:08X}', 'default_unit_max': 2000, 'default_after_patch': 2000 * FACTOR,
            'gameplay_confirmed': False}
