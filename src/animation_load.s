// 3.0.3 animation resource initialization. X19 is the FLAN resource base.
stp x15, x30, [sp, #-16]!
mov x15, x19
bl #0x03F06EE8
ldp x15, x30, [sp], #16
str x19, [x20]
b #0x0026009C
