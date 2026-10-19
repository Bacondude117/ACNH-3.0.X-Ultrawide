"""CPU checks for the ACNH 3.0.3 field create-range correction.

verify_create_range_hook() needs no game files: it executes the installed
branch and cave in isolation. verify_create_range_function() is optional and
runs the user's original 3.0.3 function 013A2864 end to end, unmodified and
patched, with synthetic range parameters. It never stores game code.
"""
import random
import struct

from build import require
from verify import _deps, _machine

SITE = 0x013A29A4
CONTINUATION = 0x013A29A8
FUNCTION = 0x013A2864
SCALE = 1.5  # 43:18 / 16:9 = 1.34375, plus margin

# Field-parameter offsets registered by the 3.0.3 constructor at 013A6D20.
CREATE_LEFT, CREATE_RIGHT, CREATE_NEAR, CREATE_FAR, CREATE_TILT = 0x60, 0x90, 0xC0, 0xF0, 0x120
WIDTH_BUFF, NEAR_BUFF, FAR_BUFF = 0x3C0, 0x3F0, 0x420
WHEREAREN_RIGHT, WHEREAREN_FAR = 0x300, 0x330
SOUND_A, SOUND_B = 0x600, 0x630


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def bits(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def from_bits(value):
    return struct.unpack('<f', struct.pack('<I', value & 0xFFFFFFFF))[0]


def verify_create_range_hook(config, patches):
    _, r = _deps()
    hook = next(hook for hook in config['hooks'] if hook['source'] == 'create_range.s')
    require(int(hook['site'], 16) == SITE and hook['original'] == '4039291E',
            'Create-range hook no longer matches its verified 3.0.3 instruction')
    rng = random.Random(34401440)
    cases = [(30., 30., 12., 0.), (24., 36., 8., -15.), (0., 0., 0., 0.), (90., 75., 40., 1234.5)]
    cases += [(rng.uniform(0, 120), rng.uniform(0, 120), rng.uniform(0, 60), rng.uniform(-800, 800)) for _ in range(8)]
    executions = 0
    for relocation in (0, 0x7100000000):
        for left, right, tilt, focus_x in cases:
            left, right, tilt, focus_x = map(f32, (left, right, tilt, focus_x))
            u = _machine(patches, relocation)
            sp = 0x202f00
            u.reg_write(r.UC_ARM64_REG_SP, sp)
            u.mem_write(sp, bytes(range(0x40)))
            u.mem_write(sp + 0x18, struct.pack('<f', tilt))
            preserved_fp = {r.UC_ARM64_REG_S8: 41.5, r.UC_ARM64_REG_S11: -77.25, r.UC_ARM64_REG_S12: 19.0,
                            r.UC_ARM64_REG_S14: 3.0, r.UC_ARM64_REG_S15: 9.0, r.UC_ARM64_REG_S2: -6.5}
            for reg, value in preserved_fp.items():
                u.reg_write(reg, bits(value))
            u.reg_write(r.UC_ARM64_REG_S9, bits(left))
            u.reg_write(r.UC_ARM64_REG_S13, bits(right))
            u.reg_write(r.UC_ARM64_REG_S10, bits(focus_x))
            u.reg_write(r.UC_ARM64_REG_NZCV, 0x60000000)
            gprs = [u.reg_read(r.UC_ARM64_REG_X0 + i) for i in range(29)]
            frame = [u.reg_read(x) for x in (r.UC_ARM64_REG_FP, r.UC_ARM64_REG_LR, r.UC_ARM64_REG_SP)]
            fp_before = {reg: u.reg_read(reg) for reg in preserved_fp}
            u.emu_start(relocation + SITE, relocation + CONTINUATION, count=32)
            require(u.reg_read(r.UC_ARM64_REG_PC) == relocation + CONTINUATION,
                    'Create-range hook did not return to 013A29A8')
            require([u.reg_read(r.UC_ARM64_REG_X0 + i) for i in range(29)] == gprs, 'Create-range hook changed a GPR')
            require([u.reg_read(x) for x in (r.UC_ARM64_REG_FP, r.UC_ARM64_REG_LR, r.UC_ARM64_REG_SP)] == frame,
                    'Create-range hook changed FP, LR or SP')
            require(u.reg_read(r.UC_ARM64_REG_NZCV) == 0x60000000, 'Create-range hook changed condition flags')
            require({reg: u.reg_read(reg) for reg in preserved_fp} == fp_before,
                    'Create-range hook changed a depth/position register')
            stack = bytes(u.mem_read(sp, 0x40))
            expected_stack = bytearray(range(0x40))
            expected_tilt = f32(tilt * f32(SCALE))
            expected_stack[0x18:0x1c] = struct.pack('<f', expected_tilt)
            require(stack == bytes(expected_stack), 'Create-range hook wrote outside the tilt slot')
            new_left = from_bits(u.reg_read(r.UC_ARM64_REG_S9))
            new_right = from_bits(u.reg_read(r.UC_ARM64_REG_S13))
            require(new_left == f32(left * f32(SCALE)) and new_right == f32(right * f32(SCALE)),
                    'Create-range horizontal extents were not scaled by exactly 1.5')
            require(from_bits(u.reg_read(r.UC_ARM64_REG_S0)) == f32(focus_x - new_left),
                    'Replaced fsub s0, s10, s9 was not replayed with the widened extent')
            executions += 1
    return {'executions': executions, 'load_bases': 2, 'cases_per_load_base': len(cases),
            'scale': '1.5 on mCreateRangeLeft, mCreateRangeRight and mCreateRangeTilt only',
            'depth_terms_unchanged': True, 'gprs_flags_stack_preserved': True, 'gameplay_confirmed': False}


# ---------------------------------------------------------------------------
# Optional original-function execution
# ---------------------------------------------------------------------------
FIELD = 0x10000000
PARAMS = 0x11000000
STUB = 0x12000000
STACK = 0x13000000
POSITION = 0x14000000
RETURN = 0x15000000


def _run_function(image, patches, values, focus, previous=None, frames=0, wherearen=False):
    unicorn, r = _deps()
    u = unicorn.Uc(unicorn.UC_ARCH_ARM64, unicorn.UC_MODE_ARM)
    for page in (0x013A2000, 0x03F06000):
        u.mem_map(page, 0x1000)
        u.mem_write(page, bytes(image[page:page + 0x1000]))
    for patch in patches:
        if patch['address'] & ~0xFFF in (0x013A2000, 0x03F06000):
            u.mem_write(patch['address'], patch['new'])
    for base, size in ((FIELD, 0x20000), (PARAMS, 0x2000), (STUB, 0x1000), (STACK, 0x4000),
                       (POSITION, 0x1000), (RETURN, 0x1000)):
        u.mem_map(base, size)
    # Parameter getter (vtable +0xF0): return a pointer to the stored value.
    u.mem_write(STUB, bytes.fromhex('00800091' 'C0035FD6'))  # add x0, x0, #0x20; ret
    u.mem_write(STUB + 0x100 + 0xF0, struct.pack('<Q', STUB))
    for offset in range(0, 0x700, 0x30):
        u.mem_write(PARAMS + offset, struct.pack('<Q', STUB + 0x100))
    for offset, value in values.items():
        if offset in (SOUND_A, SOUND_B):
            u.mem_write(PARAMS + offset + 0x20, bytes([value]))
        else:
            u.mem_write(PARAMS + offset + 0x20, struct.pack('<f', value))
    sets = FIELD + 0x16F50
    u.mem_write(sets, struct.pack('<I', 1))
    u.mem_write(sets + 8, struct.pack('<Q', FIELD + 0x1F000))
    u.mem_write(FIELD + 0x1F000, struct.pack('<Q', PARAMS))
    u.mem_write(sets + 0xE70, struct.pack('<i', 0))
    u.mem_write(sets + 0xE7C, bytes([1 if wherearen else 0]))
    rects = FIELD + 0x16D78
    u.mem_write(rects + 0x80, struct.pack('<i', frames))
    prev = previous or focus
    u.mem_write(rects + 0x84, struct.pack('<fff', prev[0], 0.0, prev[1]))
    u.mem_write(POSITION, struct.pack('<fff', focus[0], 0.0, focus[1]))
    u.reg_write(r.UC_ARM64_REG_X0, FIELD)
    u.reg_write(r.UC_ARM64_REG_X1, POSITION)
    u.reg_write(r.UC_ARM64_REG_SP, STACK + 0x3000)
    u.reg_write(r.UC_ARM64_REG_LR, RETURN)
    u.emu_start(FUNCTION, RETURN, count=4000)
    require(u.reg_read(r.UC_ARM64_REG_PC) == RETURN, '3.0.3 create-range function did not return')
    data = bytes(u.mem_read(rects, 0x100))
    return {
        'create': struct.unpack_from('<ii', data, 0x00) + struct.unpack_from('<ii', data, 0x10),
        'create_tilt': struct.unpack_from('<f', data, 0x18)[0],
        'buffered': struct.unpack_from('<ii', data, 0x30) + struct.unpack_from('<ii', data, 0x40),
        'buffered_tilt': struct.unpack_from('<f', data, 0x48)[0],
        'copy': struct.unpack_from('<ii', data, 0x60) + struct.unpack_from('<ii', data, 0x70),
        'copy_tilt': struct.unpack_from('<f', data, 0x78)[0],
        'sound': struct.unpack_from('<iiii', data, 0xC0)[:2] + struct.unpack_from('<ii', data, 0xD0),
        'stored_focus': struct.unpack_from('<fff', data, 0x84),
    }


def verify_create_range_function(image, patches):
    """Run original 013A2864 unmodified and patched with synthetic parameters.

    Expected: the patched function equals the unmodified function given
    float32(left*1.5), float32(right*1.5) and float32(tilt*1.5), and
    keeps every depth (Z) bound identical to the unmodified function.
    """
    rng = random.Random(1440)
    scale = f32(SCALE)
    cases = [
        dict(left=32., right=32., near=24., far=64., tilt=12., focus=(160., 288.)),
        dict(left=27.5, right=31., near=16., far=55., tilt=0., focus=(37.3, 401.9)),
        dict(left=40., right=40., near=30., far=80., tilt=20., focus=(12., 15.), wherearen=True),
        dict(left=35., right=35., near=20., far=60., tilt=10., focus=(300., 200.), previous=(296., 203.), frames=4),
    ]
    for _ in range(8):
        cases.append(dict(left=rng.uniform(10, 80), right=rng.uniform(10, 80), near=rng.uniform(5, 50),
                          far=rng.uniform(20, 120), tilt=rng.uniform(0, 30),
                          focus=(rng.uniform(0, 560), rng.uniform(0, 480))))
    executions = 0
    widened = 0
    for case in cases:
        def values(left, right, tilt):
            return {CREATE_LEFT: f32(left), CREATE_RIGHT: f32(right), CREATE_NEAR: f32(case['near']),
                    CREATE_FAR: f32(case['far']), CREATE_TILT: f32(tilt), WIDTH_BUFF: 5., NEAR_BUFF: 5.,
                    FAR_BUFF: 10., WHEREAREN_RIGHT: 3., WHEREAREN_FAR: 4., SOUND_A: 6, SOUND_B: 5}
        common = dict(previous=case.get('previous'), frames=case.get('frames', 0),
                      wherearen=case.get('wherearen', False))
        base = values(case['left'], case['right'], case['tilt'])
        original = _run_function(image, [], base, case['focus'], **common)
        patched = _run_function(image, patches, base, case['focus'], **common)
        right = f32(case['right']) + (3. if case.get('wherearen') else 0.)
        reference_values = values(f32(f32(case['left']) * scale), 0., f32(f32(case['tilt']) * scale))
        reference_values[CREATE_RIGHT] = f32(f32(right) * scale) - (3. if case.get('wherearen') else 0.)
        if not case.get('wherearen'):
            reference = _run_function(image, [], reference_values, case['focus'], **common)
            require(patched == reference, 'Patched function differs from original run with 1.5x horizontal ranges')
        for name in ('create', 'buffered', 'copy'):
            require(patched[name][1] == original[name][1] and patched[name][3] == original[name][3],
                    'Create-range depth (Z) bounds changed')
            require(patched[name][0] <= original[name][0] and patched[name][2] >= original[name][2],
                    'Create-range horizontal bounds did not widen or stay equal')
            widened += (patched[name][2] - patched[name][0]) > (original[name][2] - original[name][0])
        require(patched['sound'] == original['sound'] and patched['stored_focus'] == original['stored_focus'],
                'Unrelated sound rectangle or stored focus changed')
        for name in ('create_tilt', 'buffered_tilt', 'copy_tilt'):
            require(abs(patched[name] - original[name] * SCALE) <= 1e-5 * max(1., abs(original[name])),
                    'Near-edge tilt ratio was not scaled by 1.5')
        executions += 3 if not case.get('wherearen') else 2
    require(widened >= len(cases) * 2, 'Too few cases widened the create-range rectangle')
    return {'original_function_executions': executions, 'cases': len(cases),
            'widened_rectangles': widened, 'depth_bounds_identical': True,
            'sound_rectangle_unchanged': True, 'equivalent_to_scaled_parameters': True}
