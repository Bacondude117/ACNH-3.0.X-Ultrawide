// ARM64 source; assembled at 0x03F06E10. All addresses are module-relative.
// Replaces the first instruction of the perspective aspect getter 037E594C
// ("ldr s0, [x0, #0xb0]; ret"), a complete function reached by BL/BLR.
// Exact stock 16:9 is reported as 43:18; every other ratio is unchanged.
// Uses only S0 (result), S1 and NZCV, which the AArch64 procedure call
// standard lets any callee clobber. No memory writes, no stack.
    ldr s0, [x0, #0xb0]
    ldr s1, original_ratio
    fcmp s0, s1
    b.ne done
    ldr s0, wide_ratio
done:
    ret
original_ratio:
    .word 0x3fe38e39
wide_ratio:
    .word 0x4018e38e
