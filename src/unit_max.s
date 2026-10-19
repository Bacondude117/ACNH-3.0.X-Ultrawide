// ACNH 3.0.3 field-unit model pool (FieldUnitModelParam.mUnitMax).
// While the field renderer initialises, 01462BB4 "ldr w8, [x0]" reads
// mUnitMax (code default 2000, the field resource can override it) and
// 01462BB8 stores it at manager +0x6E8. That count sizes the per-frame
// instance buffers (0146534C, 014654C8) and the 0x38-byte unit array
// (014663EC). Every ground, grass, cliff, river and path unit that is drawn
// takes a slot from an atomic counter (0146ABC0). Once the counter passes
// mUnitMax, the extra units all reuse slot 0 (0146ABF4), so they disappear.
// A 43:18 view shows about 1.34x as many field units as 16:9, and the
// 1.5x create range keeps them all, so the far corners ran out of slots.
// The symptoms were see-through ground and grass missing at the sides.
// Double the pool once at load time. This costs a small amount of extra
// memory and no per-frame work. x0 is dead after this load, and the flags
// are untouched.
ldr w8, [x0]
lsl w8, w8, #1
b #0x01462BB8
