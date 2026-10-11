/* Matched 2026-10-11 through the round-trip oracle (g3_eu).
 *
 * Four thin wrappers over the palette-fade / UV-set helper the g3_eu
 * renderer calls with (short, short, short) triples
 * (0x3DC/0x3E8-family x keys and +-0x46..0x73 pairs; 0x14/0x17 as the
 * third argument from the parameterized pair).
 *
 * Shaping notes (GCC 2.6.3 -O2 -G8, MIPS1):
 * - All four wrappers discard the callee's return value, so the source
 *   functions are void: jal then straight to the frame teardown, no
 *   sibling-call rewrite.
 * - short parameters are sign-extended by the callee (old ABI: the
 *   caller passes the raw 16-bit field), giving the sll/sra pairs at
 *   entry; the first wrapper folds its *4 into the extend (sll 16, sra 14).
 * - Positive 16-bit immediates load with ori, negative with addiu —
 *   the compiler's movsi selection, visible in both constant wrappers.
 * - The last argument's materialization lands in the jal delay slot.
 * - Epilogue: lw $ra, nop (load-delay), jr $ra with the frame
 *   release in the delay slot.
 */
extern void func_8004427C(short, short, short);

void func_8004C4CC(short x, short y)
{
    func_8004427C((short)(x * 4 + 0x100), y, 0x14);
}

void func_8004C508(short x, short y)
{
    func_8004427C(x, y, 0x17);
}

void func_8004C538(void)
{
    func_8004427C(0x3DC, -0x73, -0x53);
    func_8004427C(0x3DF, -0x46, -0x49);
}

void func_8004C570(void)
{
    func_8004427C(0x3E8, 0x73, -0x53);
    func_8004427C(0x3E0, 0x46, -0x49);
}
