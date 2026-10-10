// ARM64 source; assembled at 0x03F06E00. All addresses are module-relative.
// Preserve x15-x17 and NZCV; use an aligned 32-byte stack frame.
    stp x15, x16, [sp, #-32]!
    str x17, [sp, #16]
    mrs x15, nzcv
    ldr w16, [x0, #0xb0]
    ldr w17, original_ratio
    cmp w16, w17
    b.ne selected
    ldr w16, wide_ratio
selected:
    fmov s0, w16
    msr nzcv, x15
    ldr x17, [sp, #16]
    ldp x15, x16, [sp], #32
    b #0x037e5950
original_ratio:
    .word 0x3fe38e39
wide_ratio:
    .word 0x4018e38e
