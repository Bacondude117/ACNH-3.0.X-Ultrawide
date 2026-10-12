// ACNH 3.0.3 ScissorPane horizontal layout-to-viewport conversion.
// Hook 03A308E8 replaces fdiv s3,s0,s2; capture-local mode bypasses it.
// x19 = DrawInfo, projection matrix at +10; s2/s4 = layout width/height.
// Perspective m33 is zero. Orthographic capture projections pass through.
// Match horizontal clipping to the actual projection, retaining clipping.
// No calls, no camera writes; preserve scratch registers and NZCV.
fdiv s3, s0, s2
str x15, [sp, #-16]!
ldr w15, [x19, #0x4c]
cbnz w15, finish
stp q5, q6, [sp, #-32]!
ldr s5, [x19, #0x10]
ldr s6, [x19, #0x24]
fdiv s5, s5, s6
fabs s5, s5
fdiv s6, s2, s4
fmul s5, s5, s6
fmul s3, s3, s5
ldp q5, q6, [sp], #32
finish:
ldr x15, [sp], #16
b #0x03A308EC
