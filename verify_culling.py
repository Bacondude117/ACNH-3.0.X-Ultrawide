"""CPU checks for the ACNH 3.0.3 terrain-cell group sphere correction."""
import math
import random
import struct

from build import require
from verify import _deps, _machine


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def float_reg(u, register):
    return struct.unpack('<f', struct.pack('<I', u.reg_read(register)))[0]


def verify_culling_hook(config, patches):
    _, r = _deps()
    hook = next(hook for hook in config['hooks'] if hook['source'] == 'terrain_cell_sphere.s')
    site, continuation = int(hook['site'], 16), 0x013A37C8
    require(site == 0x013A37B4 and hook['original'] == '0020211E',
            'Terrain-cell hook no longer matches its verified 3.0.3 instruction')

    # The first cases exercise square, narrow, and third-extent-dominant
    # groups. Remaining cases vary positive X/Z cell extents and height.
    cases = [(200., 200., 0.), (10., 40., 0.), (75., 20., 300.),
             (5., 5., 18.), (5., 45., 20.), (125., 60., 40.),
             (25., 250., 90.), (400., 15., 20.)]
    rng = random.Random(34401440)
    for _ in range(4):
        cases.append((rng.uniform(5., 500.), rng.uniform(5., 500.),
                      rng.uniform(0., 200.)))

    executions = 0
    for relocation in (0, 0x7100000000):
        for width, depth, other_diameter in cases:
            width, depth, other_diameter = map(f32, (width, depth, other_diameter))
            u = _machine(patches, relocation)
            values = {
                r.UC_ARM64_REG_S0: width,
                r.UC_ARM64_REG_S1: depth,
                r.UC_ARM64_REG_S2: -17.25,
                r.UC_ARM64_REG_S9: 0.5,
                r.UC_ARM64_REG_S13: other_diameter,
            }
            for register, value in values.items():
                u.reg_write(register, bits(value))
            u.reg_write(r.UC_ARM64_REG_NZCV, 0x90000000)
            before_x = [u.reg_read(r.UC_ARM64_REG_X0 + i) for i in range(29)]
            before_stack = [u.reg_read(register) for register in
                            (r.UC_ARM64_REG_FP, r.UC_ARM64_REG_LR, r.UC_ARM64_REG_SP)]
            before_other_fp = {register: u.reg_read(register) for register in
                               (r.UC_ARM64_REG_S1, r.UC_ARM64_REG_S3,
                                r.UC_ARM64_REG_S4, r.UC_ARM64_REG_S5,
                                r.UC_ARM64_REG_S6, r.UC_ARM64_REG_S7,
                                r.UC_ARM64_REG_S8, r.UC_ARM64_REG_S9,
                                r.UC_ARM64_REG_S10, r.UC_ARM64_REG_S11,
                                r.UC_ARM64_REG_S12, r.UC_ARM64_REG_S13,
                                r.UC_ARM64_REG_S14, r.UC_ARM64_REG_S15)}

            # Execute the installed site branch, the cave routine, and its
            # branch back. Stop at the original frustum-test call instruction.
            u.emu_start(relocation + site, relocation + continuation, count=32)
            require(u.reg_read(r.UC_ARM64_REG_PC) == relocation + continuation,
                    'Terrain-cell hook did not branch back before the 3.0.3 sphere/frustum test')
            require([u.reg_read(r.UC_ARM64_REG_X0 + i) for i in range(29)] == before_x,
                    'Terrain-cell hook changed a general-purpose register')
            require([u.reg_read(register) for register in
                     (r.UC_ARM64_REG_FP, r.UC_ARM64_REG_LR, r.UC_ARM64_REG_SP)] == before_stack,
                    'Terrain-cell hook changed frame, link, or stack pointer')
            require({register: u.reg_read(register) for register in before_other_fp} == before_other_fp,
                    'Terrain-cell hook changed a non-scratch input or floating-point register')
            require(u.reg_read(r.UC_ARM64_REG_NZCV) == 0x90000000,
                    'Terrain-cell hook changed integer condition flags')

            expected = math.sqrt(width * width + depth * depth +
                                 other_diameter * other_diameter) * 0.5
            actual = float_reg(u, r.UC_ARM64_REG_S0)
            require(math.isclose(actual, expected, rel_tol=2e-6, abs_tol=1e-5),
                    f'Wrong half-diagonal for X/Z/third diameters '
                    f'{width}/{depth}/{other_diameter}: {actual} != {expected}')
            require(actual + 1e-5 >= max(width, depth, other_diameter) * 0.5,
                    'Half-diagonal is smaller than one of the source half-extents')
            executions += 1

    return {
        'executions': executions,
        'load_bases': 2,
        'cases_per_load_base': len(cases),
        'bound': 'sqrt(X^2 + Z^2 + thirdExtent^2) / 2',
        'general_registers_and_other_fp_inputs_preserved': True,
        'frustum_test_unchanged': True,
        'gameplay_confirmed': False,
    }
