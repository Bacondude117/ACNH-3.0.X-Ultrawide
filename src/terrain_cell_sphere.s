// The 3.0.3 terrain-cell path provides X/Z diameters in S0/S1 and a third
// (vertical/other) diameter candidate in S13. The original max-side radius
// does not enclose a box corner when more than one extent is nonzero. Use the
// full 3D half-diagonal, the tight sphere containing that axis-aligned bound.
// S2 is dead after 013A373C and is not used by the caller after this test.
fmul s2, s0, s0
fmadd s2, s1, s1, s2
fmadd s2, s13, s13, s2
fsqrt s2, s2
fmul s0, s2, s9
b #0x013A37C8
