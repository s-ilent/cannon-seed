/* Matched 2026-10-11 through the round-trip oracle (mainmenu_eu).
 *
 * The main-menu wrapper family (0x2c8 cluster at 0x800379E4): sixteen
 * tiny void functions, each arming the menu-state flag and/or
 * driving the sequence helper func_80035664(N, M), then calling
 * the unprototyped menu primitive func_80025CFC().
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
 * - Three functions were scanned as head/tail pairs (func_80037B40 +
 *   func_80037B60, func_80037B6C + func_80037B7C, func_80037B98 +
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

void func_800379E4(void)
{
    menu_state_flag = 0;
    func_80025CFC();
}

void func_80037A0C(void)
{
    menu_state_flag = 1;
    func_80025CFC();
}

void func_80037A38(void)
{
    func_80035664(6, 0);
    func_80025CFC();
}

void func_80037A64(void)
{
    func_80035664(6, 1);
    func_80025CFC();
}

void func_80037A90(void)
{
    func_80035664(6, 2);
    func_80025CFC();
}

void func_80037ABC(void)
{
    func_80035664(6, 3);
    func_80025CFC();
}

void func_80037AE8(void)
{
    func_80035664(6, 4);
    func_80025CFC();
}

void func_80037B14(void)
{
    func_80035664(9, -1);
    func_80025CFC();
}

void func_80037B40(void)
{
    func_80035664(9, 1);
    func_80025CFC();
}

void func_80037B6C(void)
{
    func_80035664(9, 2);
    func_80025CFC();
}

void func_80037B98(void)
{
    func_80035664(9, 3);
    func_80025CFC();
}

void func_80037BC4(void)
{
    func_80035664(9, 4);
    func_80025CFC();
}

void func_80037BF0(void)
{
    func_80035664(9, 5);
    func_80025CFC();
}

void func_80037C1C(void)
{
    func_80035664(9, 6);
    func_80025CFC();
}

void func_80037C48(void)
{
    func_80035664(7, 0);
    func_80025CFC();
}

void func_80037C74(void)
{
    func_80035664(7, 0);
    func_80035664(7, 1);
    func_80025CFC();
}
