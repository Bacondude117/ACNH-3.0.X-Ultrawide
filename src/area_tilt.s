// 01125DDC normal path: 0112616C "ldr s3, [x0]" loads mTreeAreaTilt or
// mAreaTilt, the near-edge narrowing of the area rectangle. Scale it with the
// horizontal extents so the trapezoid keeps its shape at 43:18.
// S7 is unused by this function and caller-saved.
ldr s3, [x0]
fmov s7, #1.5
fmul s3, s3, s7
b #0x01126170
