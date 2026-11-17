/* Matched 2026-10-11 through the round-trip oracle (mainmenu_eu).
 *
 * The main-menu wrapper family (0x2c8 cluster): sixteen tiny void
 * functions, each arming the menu-state flag and/or driving the
 * sequence helper func_80035664(N, M), then calling the unprototyped
 * menu primitive func_80025CFC().
 *
 * Placement and naming (the 2026-11-17 name-space repair): the cluster
 * was matched while it sat at the pre-flip yaml window whose VAs gave
 * the functions their original names; the de-frame re-baseline then
 * re-placed the row at 0x15004 (VMA base 0x80034804), where the
 * object's sixteen symbols verifiably land (total text 0x2c8 = the row
 * extent). The original names encoded the vacated VAs - whose true
 * occupants are different units inside the big caller dump (the
 * nonmatching extent at 0x156BC) - so the
 * functions re-spelled to their placement-derived names (the readelf
 * FUNC table of the built object, sizes 0x28/0x2c x13/0x38), the row
 * and file ride the same motion, and the dump's collision-pass _2
 * units reclaimed their plain address-derived names. The stale-name
 * collision was the whole dedup-drop residue; no body is a sibling
 * copy - the dump blocks at the vacated VAs are different code.
 *
 * Shaping notes (GCC 2.6.3 -O2 -G8, MIPS1):
 * - Storing 0 folds to sw $zero; storing 1 materializes $v0 first
 *   (ori) - the compiler's movsi selection, as in the g3_eu wrappers.
 * - The sequence helper's second argument materializes in the jal
 *   delay slot: ori for >= 0, addiu for -1, and a move-from-$zero
 *   (addu) for 0. The menu primitive takes no arguments, so its jal
 *   delay slot stays a nop.
 * - Both callees discard their return values: no sibling-call
 *   rewrite, the second jal runs straight into the epilogue (lw $ra,
 *   nop load-delay, jr $ra with the frame release in the branch
 *   delay slot).
 * - Three functions were scanned as head/tail pairs (func_80034960 +
 *   func_80037B60, func_8003498C + func_80037B7C, func_800349B8 +
 *   func_80037BA4) because other code tail-jumps into their epilogue
 *   region (func_8003B14C, func_8003B3F8, func_8003B400, and the
 *   func_8003B360/func_8003B45C tails). The C sources are whole
 *   functions; the mid-function labels resolve by address through
 *   build.sh's two-pass auto-definition, and the oracle checks the
 *   bytes those jumps land on.
 */

extern int menu_state_flag;
extern void func_80025CFC(void);
extern void func_80035664(int, int);

void func_80034804(void)
{
    menu_state_flag = 0;
    func_80025CFC();
}

void func_8003482C(void)
{
    menu_state_flag = 1;
    func_80025CFC();
}

void func_80034858(void)
{
    func_80035664(6, 0);
    func_80025CFC();
}

void func_80034884(void)
{
    func_80035664(6, 1);
    func_80025CFC();
}

void func_800348B0(void)
{
    func_80035664(6, 2);
    func_80025CFC();
}

void func_800348DC(void)
{
    func_80035664(6, 3);
    func_80025CFC();
}

void func_80034908(void)
{
    func_80035664(6, 4);
    func_80025CFC();
}

void func_80034934(void)
{
    func_80035664(9, -1);
    func_80025CFC();
}

void func_80034960(void)
{
    func_80035664(9, 1);
    func_80025CFC();
}

void func_8003498C(void)
{
    func_80035664(9, 2);
    func_80025CFC();
}

void func_800349B8(void)
{
    func_80035664(9, 3);
    func_80025CFC();
}

void func_800349E4(void)
{
    func_80035664(9, 4);
    func_80025CFC();
}

void func_80034A10(void)
{
    func_80035664(9, 5);
    func_80025CFC();
}

void func_80034A3C(void)
{
    func_80035664(9, 6);
    func_80025CFC();
}

void func_80034A68(void)
{
    func_80035664(7, 0);
    func_80025CFC();
}

void func_80034A94(void)
{
    func_80035664(7, 0);
    func_80035664(7, 1);
    func_80025CFC();
}
