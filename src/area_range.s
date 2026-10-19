// ACNH 3.0.3 field-item/tree area rectangle, function 01125DDC.
// Called four times from 010D7158.. to build the tree area (mTreeAreaLeft/
// Right/Near/Far/Tilt) and item area (mAreaLeft/Right/Near/Far/Tilt), with and
// without the Width/Near/Far buffers. These rectangles, not only the create
// range, decide which trees, weeds and items exist around the camera focus.
// Reached by BL from 01126144 (normal path) and 01125FE4 (alternate scene
// path); 01125DDC saved LR in its prologue, so the BL is safe. At both sites
// S8 = Left and S9 = Right (buffers already added) and the replaced
// instruction is "ldr s0, [x20]" (focus X). Widen Left/Right by 1.5 (43:18 /
// 16:9 = 1.34375 plus margin), replay the load and return after the site.
// X0 (pointer to the tilt parameter on the normal path) is preserved.
fmov s0, #1.5
fmul s8, s8, s0
fmul s9, s9, s0
ldr s0, [x20]
ret
