// S4 = abs(projection m00/m11). Read the reference height directly;
// do not reconstruct it by dividing a possibly zero animated capture height.
ldr s5, [x15, #0x2c]
fdiv s2, s9, s5
fmul s2, s2, s4
b restore
native:
fdiv s2, s9, s2
restore:
ldr x15, [sp, #32]
ldp q4, q5, [sp], #48
b #0x03A2EAC0
