"""CPU checks for the ACNH 3.0.3 tree/item area widening (function 01125DDC).

verify_area_range_hooks() needs no game files: it executes the three installed
branch sites (two BL into one shared routine) and caves in isolation. verify_area_range_function() is optional: it
runs the user's original 3.0.3 function end to end, unpatched and patched,
with synthetic parameter objects. No game code is stored in this project.
"""
import random
import struct

from build import require
from verify import _deps, _machine

SCALE = 1.5  # 43:18 / 16:9 = 1.34375, plus margin
FUNCTION = 0x01125DDC
# (source, site, return address, original instruction). Both rectangle sites
# BL into one shared routine that RETs to site+4, so LR changes there (LR is
# already saved by 01125DDC's prologue and restored before its own return).
HOOKS = [
    ('area_range.s', 0x01126144, 0x01126148, '800240BD'),
    ('area_range.s', 0x01125FE4, 0x01125FE8, '800240BD'),
    ('area_tilt.s', 0x0112616C, 0x01126170, '030040BD'),
]
# Parameter offsets in the owner object, mapped from the 3.0.3 registration
# code at 011227A0.. (each parameter object is 0x30 bytes).
TREE = dict(left=0x8450, right=0x8480, near=0x84B0, far=0x84E0, tilt=0x8510)
AREA = dict(left=0x8540, right=0x8570, near=0x85A0, far=0x85D0, tilt=0x8600)
WIDTH_BUFF, NEAR_BUFF, FAR_BUFF = 0x8630, 0x8660, 0x8690
SCENE_HASH = 0x054CDB30      # 054CDAF8 + 0x38, compared with E820FF3D
SCENE_FLAG_PTR = 0x050F0338  # pointer to a structure whose +0x0C enables path A


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def from_bits(value):
    return struct.unpack('<f', struct.pack('<I', value & 0xFFFFFFFF))[0]


def verify_area_range_hooks(config, patches):
    _, r = _deps()
    by_site = {int(h['site'], 16): h for h in config['hooks']}
    for source, site, _, original in HOOKS:
        hook = by_site.get(site)
        require(hook is not None and hook['source'] == source and hook['original'] == original,
                f'{source} at {site:08X} no longer matches its verified 3.0.3 instruction')
        require(bool(hook.get('link')) == (source == 'area_range.s'),
                f'{source} at {site:08X} has the wrong branch type')
    rng = random.Random(1440343)
    cases = [(32., 32., 12., 160.), (0., 0., 0., 0.), (75.5, 40.25, 30., -12.5), (150., 150., 2.618, 400.)]
    cases += [(rng.uniform(0, 200), rng.uniform(0, 200), rng.uniform(0, 60), rng.uniform(-50, 600)) for _ in range(8)]
    executions = 0
    for relocation in (0, 0x7100000000):
        for source, site, back, _ in HOOKS:
            for left, right, tilt, focus in cases:
                left, right, tilt, focus = map(f32, (left, right, tilt, focus))
                u = _machine(patches, relocation)
                value_ptr = 0x201800
                u.mem_write(value_ptr, struct.pack('<f', tilt if source == 'area_tilt.s' else focus))
                u.reg_write(r.UC_ARM64_REG_X20, value_ptr)
                u.reg_write(r.UC_ARM64_REG_X0, value_ptr)
                u.reg_write(r.UC_ARM64_REG_S8, bits(left))
                u.reg_write(r.UC_ARM64_REG_S9, bits(right))
                for reg, val in ((r.UC_ARM64_REG_S10, 11.5), (r.UC_ARM64_REG_S11, -3.25),
                                 (r.UC_ARM64_REG_S4, 9.0), (r.UC_ARM64_REG_S5, 8.0), (r.UC_ARM64_REG_S6, 5.0)):
                    u.reg_write(reg, bits(val))
                u.reg_write(r.UC_ARM64_REG_NZCV, 0x60000000)
                keep = [r.UC_ARM64_REG_X0 + i for i in range(29)] + [r.UC_ARM64_REG_FP,
                                                                     r.UC_ARM64_REG_SP, r.UC_ARM64_REG_NZCV,
                                                                     r.UC_ARM64_REG_S10, r.UC_ARM64_REG_S11,
                                                                     r.UC_ARM64_REG_S4, r.UC_ARM64_REG_S5,
                                                                     r.UC_ARM64_REG_S6]
                if source == 'area_tilt.s':
                    keep += [r.UC_ARM64_REG_LR, r.UC_ARM64_REG_S8, r.UC_ARM64_REG_S9, r.UC_ARM64_REG_S0]
                before = [u.reg_read(x) for x in keep]
                u.emu_start(relocation + site, relocation + back, count=16)
                require(u.reg_read(r.UC_ARM64_REG_PC) == relocation + back, f'{source} did not return')
                require([u.reg_read(x) for x in keep] == before, f'{source} changed a preserved register or flags')
                if source == 'area_range.s':
                    require(u.reg_read(r.UC_ARM64_REG_LR) == relocation + back, 'Shared area routine LR is not site+4')
                if source == 'area_tilt.s':
                    require(from_bits(u.reg_read(r.UC_ARM64_REG_S3)) == f32(tilt * SCALE),
                            'Area tilt was not scaled by 1.5')
                else:
                    require(from_bits(u.reg_read(r.UC_ARM64_REG_S8)) == f32(left * SCALE)
                            and from_bits(u.reg_read(r.UC_ARM64_REG_S9)) == f32(right * SCALE),
                            'Area Left/Right were not scaled by 1.5')
                    require(from_bits(u.reg_read(r.UC_ARM64_REG_S0)) == focus,
                            'Replayed focus load returned the wrong value')
                executions += 1
    return {'executions': executions, 'load_bases': 2, 'hooks': len(HOOKS), 'shared_routine_sites': 2, 'cases_per_hook': len(cases),
            'scale': '1.5 on mTreeArea/mArea Left, Right and Tilt only', 'depth_terms_unchanged': True,
            'gameplay_confirmed': False}


# ---------------------------------------------------------------------------
# Optional original-function execution
# ---------------------------------------------------------------------------
OWNER = 0x10000000
STUB = 0x12000000
STACK = 0x13000000
RECT = 0x14000000
POSITION = 0x14000800
RETURN = 0x15000000


def _run(image, patches, params, focus, tree, buffers, alt_scene=False):
    unicorn, r = _deps()
    u = unicorn.Uc(unicorn.UC_ARCH_ARM64, unicorn.UC_MODE_ARM)
    for page in (0x01125000, 0x01126000, 0x03F06000):
        u.mem_map(page, 0x1000)
        u.mem_write(page, bytes(image[page:page + 0x1000]))
    for patch in patches:
        if patch['address'] & ~0xFFF in (0x01125000, 0x01126000, 0x03F06000):
            u.mem_write(patch['address'], patch['new'])
    for base, size in ((OWNER, 0x9000), (STUB, 0x1000), (STACK, 0x4000), (RECT, 0x1000), (RETURN, 0x1000),
                       (SCENE_HASH & ~0xFFF, 0x1000), (SCENE_FLAG_PTR & ~0xFFF, 0x1000)):
        u.mem_map(base, size)
    u.mem_write(STUB, bytes.fromhex('00800091' 'C0035FD6'))  # add x0, x0, #0x20; ret
    u.mem_write(STUB + 0x1F0, struct.pack('<Q', STUB))
    for offset in range(0x8450, 0x86F0, 0x30):
        u.mem_write(OWNER + offset, struct.pack('<Q', STUB + 0x100))
    for offset, value in params.items():
        u.mem_write(OWNER + offset + 0x20, struct.pack('<f', value))
    if alt_scene:
        u.mem_write(SCENE_HASH, struct.pack('<I', 0xE820FF3D))
        u.mem_write(SCENE_FLAG_PTR, struct.pack('<Q', STUB + 0x800))
        u.mem_write(STUB + 0x80C, struct.pack('<I', 1))
    u.mem_write(POSITION, struct.pack('<fff', focus[0], 0.0, focus[1]))
    u.reg_write(r.UC_ARM64_REG_X0, OWNER)
    u.reg_write(r.UC_ARM64_REG_X1, RECT)
    u.reg_write(r.UC_ARM64_REG_X2, POSITION)
    u.reg_write(r.UC_ARM64_REG_X3, 1 if tree else 0)
    u.reg_write(r.UC_ARM64_REG_X4, 1 if buffers else 0)
    u.reg_write(r.UC_ARM64_REG_SP, STACK + 0x3000)
    u.reg_write(r.UC_ARM64_REG_LR, RETURN)
    u.emu_start(FUNCTION, RETURN, count=3000)
    require(u.reg_read(r.UC_ARM64_REG_PC) == RETURN, '3.0.3 area function did not return')
    data = bytes(u.mem_read(RECT + 0x10, 0x1C))
    x0, z0 = struct.unpack_from('<ii', data, 0)
    x1, z1 = struct.unpack_from('<ii', data, 0x10)
    return (x0, z0, x1, z1), struct.unpack_from('<f', data, 0x18)[0]


def verify_area_range_function(image, patches):
    rng = random.Random(34401440)
    cases = [dict(l=32., r=32., n=20., f=60., t=12., focus=(160., 288.)),
             dict(l=27.5, r=31., n=16., f=55., t=0., focus=(37.3, 401.9)),
             dict(l=45., r=40., n=25., f=70., t=18., focus=(300., 120.))]
    cases += [dict(l=rng.uniform(10, 90), r=rng.uniform(10, 90), n=rng.uniform(5, 40), f=rng.uniform(20, 120),
                   t=rng.uniform(0, 30), focus=(rng.uniform(0, 560), rng.uniform(0, 480))) for _ in range(5)]
    runs = widened = 0
    for case in cases:
        for tree in (False, True):
            names = TREE if tree else AREA
            for buffers in (False, True):
                for alt in (False, True):
                    def params(left, right, tilt):
                        return {names['left']: f32(left), names['right']: f32(right), names['near']: f32(case['n']),
                                names['far']: f32(case['f']), names['tilt']: f32(tilt),
                                WIDTH_BUFF: 4., NEAR_BUFF: 3., FAR_BUFF: 6.}
                    base = params(case['l'], case['r'], case['t'])
                    orig, orig_tilt = _run(image, [], base, case['focus'], tree, buffers, alt)
                    new, new_tilt = _run(image, patches, base, case['focus'], tree, buffers, alt)
                    runs += 2
                    require(new[1] == orig[1] and new[3] == orig[3], 'Area depth (Z) bounds changed')
                    require(new[0] <= orig[0] and new[2] >= orig[2], 'Area horizontal bounds did not widen')
                    widened += (new[2] - new[0]) > (orig[2] - orig[0])
                    if alt and tree:  # the alternate path exists only for the tree rectangle
                        require(new_tilt == orig_tilt == 0.0, 'Alternate path tilt changed')
                    else:
                        require(abs(new_tilt - orig_tilt * SCALE) <= 1e-5 * max(1., abs(orig_tilt)),
                                'Area tilt ratio was not scaled by 1.5')
                    if not buffers:
                        ref, ref_tilt = _run(image, [], params(f32(f32(case['l']) * f32(SCALE)),
                                                               f32(f32(case['r']) * f32(SCALE)),
                                                               f32(f32(case['t']) * f32(SCALE))),
                                             case['focus'], tree, buffers, alt)
                        runs += 1
                        require(ref == new and ref_tilt == new_tilt,
                                'Patched area differs from original run with 1.5x Left/Right/Tilt')
    require(widened >= len(cases) * 6, 'Too few cases widened the area rectangle')
    return {'original_function_executions': runs, 'cases': len(cases), 'widened_rectangles': widened,
            'paths': 'tree/item x buffered/unbuffered x normal/alternate', 'depth_bounds_identical': True,
            'equivalent_to_scaled_parameters': True}
