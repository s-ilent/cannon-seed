/* Matched 2026-10-11 through the round-trip oracle (mainmenu_jp).
 *
 * The main-menu wrapper family (0x6b8 cluster at 0x80037A44): 35 tiny
 * void functions, the JP twin of the mainmenu_eu family at 0x800379E4.
 * Each arms the menu-state flag D_800C8B38 (first two functions) and/or
 * drives the sequence helper func_800356C4(N, M), then calls the
 * unprototyped menu primitive func_80025DAC(). JP carries 19 more
 * variants than EU: single wrappers over N = 8, 10, 11, 13, 14, 15 and
 * multi-sequence functions repeating (7, M) runs up to five calls.
 *
 * func_8003800C is the one stateful member: it snapshots the counter
 * helper func_80035A78(0) into a callee-saved local, replays the
 * (12, -1) / (0, 1) pair twice around it, and feeds the snapshot back
 * as the last func_800356C4 argument.
 *
 * Shaping notes (GCC 2.6.3 -O2 -G8, MIPS1), all proven on the EU twin:
 * - Storing 0 folds to sw $zero; storing 1 materializes $v0 first
 *   (ori) - the compiler's movsi selection.
 * - The sequence helper's second argument materializes in the jal
 *   delay slot: ori for >= 1, addiu for -1, and a move-from-$zero
 *   (addu) for 0. The menu primitive takes no arguments, so its jal
 *   delay slot stays a nop.
 * - Both callees discard their return values: no sibling-call
 *   rewrite, the second jal runs straight into the epilogue (lw $ra,
 *   nop load-delay, jr $ra with the frame release in the branch
 *   delay slot).
 * - Three functions were scanned in pieces because other code jumps
 *   into them (func_8003B1A8 and func_8003B1B4 jump to func_80037BBC
 *   and func_80037BD8; func_8005A184, func_8005C5EC and func_8005C60C
 *   share the func_80037D2C entry): func_80037BA0 + func_80037BBC is
 *   one function, func_80037BCC + func_80037BD8 is one function, and
 *   func_80037BF8 + func_80037C00 is one function. The C sources are
 *   whole functions; the mid-function labels resolve by address
 *   through build.sh's two-pass auto-definition, and the oracle
 *   checks the bytes those jumps land on.
 * - The region continues past this unit with the (7, x) switch
 *   dispatch at func_800380FC (jump tables jtbl_80021244 and
 *   jtbl_8002125C); it stays asm until the switch class is matched on
 *   evidence.
 */

extern int D_800C8B38;
extern void func_80025DAC(void);
extern void func_800356C4(int, int);
extern int func_80035A78(int);

void func_80037A44(void)
{
    D_800C8B38 = 0;
    func_80025DAC();
}

void func_80037A6C(void)
{
    D_800C8B38 = 1;
    func_80025DAC();
}

void func_80037A98(void)
{
    func_800356C4(6, 0);
    func_80025DAC();
}

void func_80037AC4(void)
{
    func_800356C4(6, 1);
    func_80025DAC();
}

void func_80037AF0(void)
{
    func_800356C4(6, 2);
    func_80025DAC();
}

void func_80037B1C(void)
{
    func_800356C4(6, 3);
    func_80025DAC();
}

void func_80037B48(void)
{
    func_800356C4(6, 4);
    func_80025DAC();
}

void func_80037B74(void)
{
    func_800356C4(9, -1);
    func_80025DAC();
}

void func_80037BA0(void)
{
    func_800356C4(9, 1);
    func_80025DAC();
}

void func_80037BCC(void)
{
    func_800356C4(9, 2);
    func_80025DAC();
}

void func_80037BF8(void)
{
    func_800356C4(9, 3);
    func_80025DAC();
}

void func_80037C24(void)
{
    func_800356C4(9, 4);
    func_80025DAC();
}

void func_80037C50(void)
{
    func_800356C4(9, 5);
    func_80025DAC();
}

void func_80037C7C(void)
{
    func_800356C4(9, 6);
    func_80025DAC();
}

void func_80037CA8(void)
{
    func_800356C4(7, 0);
    func_80025DAC();
}

void func_80037CD4(void)
{
    func_800356C4(7, 0);
    func_800356C4(7, 1);
    func_80025DAC();
}

void func_80037D0C(void)
{
    func_800356C4(7, 0);
    func_800356C4(7, 1);
    func_800356C4(7, 2);
    func_80025DAC();
}

void func_80037D50(void)
{
    func_800356C4(7, 0);
    func_800356C4(7, 1);
    func_800356C4(7, 2);
    func_800356C4(7, 4);
    func_80025DAC();
}

void func_80037DA0(void)
{
    func_800356C4(7, 0);
    func_800356C4(7, 1);
    func_800356C4(7, 2);
    func_800356C4(7, 4);
    func_800356C4(7, 8);
    func_80025DAC();
}

void func_80037DFC(void)
{
    func_800356C4(8, 1);
    func_80025DAC();
}

void func_80037E28(void)
{
    func_800356C4(8, 0);
    func_80025DAC();
}

void func_80037E54(void)
{
    func_800356C4(10, 1);
    func_80025DAC();
}

void func_80037E80(void)
{
    func_800356C4(10, 0);
    func_80025DAC();
}

void func_80037EAC(void)
{
    func_800356C4(11, 1);
    func_80025DAC();
}

void func_80037ED8(void)
{
    func_800356C4(11, 0);
    func_80025DAC();
}

void func_80037F04(void)
{
    func_800356C4(13, 0);
    func_80025DAC();
}

void func_80037F30(void)
{
    func_800356C4(13, 1);
    func_80025DAC();
}

void func_80037F5C(void)
{
    func_800356C4(13, 2);
    func_80025DAC();
}

void func_80037F88(void)
{
    func_800356C4(13, 3);
    func_80025DAC();
}

void func_80037FB4(void)
{
    func_800356C4(14, 1);
    func_80025DAC();
}

void func_80037FE0(void)
{
    func_800356C4(14, 0);
    func_80025DAC();
}

void func_8003800C(void)
{
    int seq;

    seq = func_80035A78(0);
    func_800356C4(0, 0);
    func_800356C4(12, -1);
    func_800356C4(0, 1);
    func_800356C4(12, -1);
    func_800356C4(0, seq);
    func_80025DAC();
}

void func_80038078(void)
{
    func_800356C4(12, 0);
    func_80025DAC();
}

void func_800380A4(void)
{
    func_800356C4(15, 0);
    func_80025DAC();
}

void func_800380D0(void)
{
    func_800356C4(15, 1);
    func_80025DAC();
}
