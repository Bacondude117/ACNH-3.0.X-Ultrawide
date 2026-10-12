// Background-copy source rectangle, verified at 3.0.3 VA 03A2EABC.
// X21 = DrawInfo; S2 = reference width; S9 = capture width.
// Orthographic capture passes retain the original conversion.
// Split across two verified executable alignment gaps; all scratch restored.
stp q4, q5, [sp, #-48]!
str x15, [sp, #32]
ldr w15, [x21, #0x4c]
cbnz w15, #0x03F06FEC
ldr s4, [x21, #0x10]
ldr s5, [x21, #0x24]
fdiv s4, s4, s5
fabs s4, s4
ldr x15, [x21, #0xc0]
b #0x03F06FDC
