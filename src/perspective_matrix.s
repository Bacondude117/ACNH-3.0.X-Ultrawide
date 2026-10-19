// ARM64 source; assembled at 0x03F06E90. All addresses are module-relative.
// Replaces the first instruction of the perspective matrix builder 037E5968
// ("ldr s0, [x0, #0x98]"), a complete function reached by BL/BLR.
// Calls the aspect-getter routine above, stores its result at +0xB0 (43:18 for
// exact stock 16:9, otherwise the same bits) and replays the original load.
// X16 (IP0) holds the return address during the call; X16, S1 and NZCV are
// caller-saved under the AArch64 procedure call standard. X0/X1 preserved.
    mov x16, x30
    bl #0x03F06E10
    mov x30, x16
    str s0, [x0, #0xb0]
    ldr s0, [x0, #0x98]
    b #0x037e596c
