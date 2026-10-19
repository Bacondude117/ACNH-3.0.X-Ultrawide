// ACNH 3.0.3 field create-range rectangle, function 013A2864.
// The game builds the island cell rectangle in which terrain cells are tested
// and field content is created from mCreateRangeLeft/Right (S9/S13, world
// units beside the camera focus), mCreateRangeTilt (stack +0x18, how much the
// near edge narrows) and Near/Far depth (S12/S8). The values are tuned for a
// 16:9 view. The normal camera faces world -Z, so world X is screen
// horizontal: widen only the horizontal terms. 1.5 = 43:18 / 16:9 (1.34375)
// plus margin for 5-unit cell rounding and object footprints. Depth unchanged.
// Replaces 013A29A4 "fsub s0, s10, s9". S0 and S1 are written by the original
// code before any read, so they are free scratch here. No GPR/flag changes.
fmov s0, #1.5
fmul s9, s9, s0
fmul s13, s13, s0
ldr s1, [sp, #0x18]
fmul s1, s1, s0
str s1, [sp, #0x18]
fsub s0, s10, s9
b #0x013A29A8
