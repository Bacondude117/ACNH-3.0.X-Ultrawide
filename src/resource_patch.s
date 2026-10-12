// Original routine, X15 = an already loaded FLYT/FLAN resource.
// Table entries: u32 size, u32 total entry bytes, u64 original FNV-1a;
// then groups: u16 count, u32 replacement, count u16 byte offsets.
// Unaligned normal-memory reads are intentional; entries are 2-byte aligned.
// A zero-size entry terminates the table. All registers/flags preserved.
// Only an exact whole-resource fingerprint permits writes. A second load
// sees the changed fingerprint and does nothing (no cumulative HUD drift).
stp x8, x9, [sp, #-96]!
stp x10, x11, [sp, #16]
stp x12, x13, [sp, #32]
stp x14, x16, [sp, #48]
str x17, [sp, #64]
mrs x17, nzcv
str x17, [sp, #72]
adrp x8, #0x04724000
add x8, x8, #0x200
ldr w9, [x15, #12]
entry:
ldp w10, w11, [x8]
cbz w10, done
cmp w10, w9
b.ne next
mov x12, #0x2325
movk x12, #0x8422, lsl #16
movk x12, #0x9CE4, lsl #32
movk x12, #0xCBF2, lsl #48
mov x13, #0x1B3
movk x13, #0x100, lsl #32
mov x14, x15
hash_loop:
ldrb w16, [x14], #1
eor x12, x12, x16
mul x12, x12, x13
subs w10, w10, #1
b.ne hash_loop
ldr x14, [x8, #8]
cmp x12, x14
b.ne next
add x11, x8, x11
add x8, x8, #16
group:
ldrh w10, [x8], #2
ldr w13, [x8], #4
write_loop:
ldrh w12, [x8], #2
str w13, [x15, x12]
subs w10, w10, #1
b.ne write_loop
cmp x8, x11
b.lo group
b done
next:
add x8, x8, x11
b entry
done:
ldr x17, [sp, #72]
msr nzcv, x17
ldr x17, [sp, #64]
ldp x14, x16, [sp, #48]
ldp x12, x13, [sp, #32]
ldp x10, x11, [sp, #16]
ldp x8, x9, [sp], #96
ret
