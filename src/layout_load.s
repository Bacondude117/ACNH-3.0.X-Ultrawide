// 3.0.3 Layout::Build section iteration. X21 is the FLYT resource base.
// Preserve our argument and LR, then replay the replaced header load.
stp x15, x30, [sp, #-16]!
mov x15, x21
bl #0x03F06ED8
ldp x15, x30, [sp], #16
ldrh w8, [x21, #6]
b #0x00268EE4
