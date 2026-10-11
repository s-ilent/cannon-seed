/* Matched 2026-10-11 through the round-trip oracle (mainmenu_eu).
 *
 * The EU tail of the main-menu wrapper family: 19 tiny void functions,
 * the byte-proven twins of mainmenu_jp's func_80037D0C..func_800380D0
 * (functions 17-35 of src/func_80037A44.c). EU address = JP address
 * - 0x60 across the whole span; a full-span word diff shows 52 differing
 * words, every one a jal target, so the JP C source ports verbatim with
 * renamed callees. These functions hid inside data_80037CAC until the
 * cron-20261011-1156 carve (6745e1f) - the "JP carries 19 more variants
 * than EU" note in the JP header predates this and is now obsolete.
 *
 * Each arms the sequence helper func_80035664(N, M) one or more times,
 * then calls the unprototyped menu primitive func_80025CFC().
 *
 * func_80037FAC is the one stateful member (JP: func_8003800C): it
 * snapshots the counter helper func_80035A18(0) into a callee-saved
 * local, replays the (12, -1) / (0, 1) pair twice around it, and feeds
 * the snapshot back as the last func_80035664 argument.
 *
 * Shaping notes (GCC 2.6.3 -O2 -G8, MIPS1), as proven on the JP twin:
 * - The sequence helper's second argument materializes in the jal
 *   delay slot: ori for >= 1, addiu for -1, and a move-from-$zero
 *   (addu) for 0. The menu primitive takes no arguments, so its jal
 *   delay slot stays a nop.
 * - Both callees discard their return values: no sibling-call
 *   rewrite, the second jal runs straight into the epilogue.
 * - func_80037CD0 (the third call's jal inside func_80037CAC) is the
 *   shared entry other code jumps into, and func_8003B568 jumps to
 *   0x80037CB0 (func_80037CAC's $ra spill): both resolve by address
 *   through build.sh's two-pass auto-definition, exactly like JP's
 *   func_80037D2C, and the oracle checks the bytes those jumps land on.
 */

extern void func_80025CFC(void);
extern void func_80035664(int, int);
extern int func_80035A18(int);

void func_80037CAC(void)
{
    func_80035664(7, 0);
    func_80035664(7, 1);
    func_80035664(7, 2);
    func_80025CFC();
}

void func_80037CF0(void)
{
    func_80035664(7, 0);
    func_80035664(7, 1);
    func_80035664(7, 2);
    func_80035664(7, 4);
    func_80025CFC();
}

void func_80037D40(void)
{
    func_80035664(7, 0);
    func_80035664(7, 1);
    func_80035664(7, 2);
    func_80035664(7, 4);
    func_80035664(7, 8);
    func_80025CFC();
}

void func_80037D9C(void)
{
    func_80035664(8, 1);
    func_80025CFC();
}

void func_80037DC8(void)
{
    func_80035664(8, 0);
    func_80025CFC();
}

void func_80037DF4(void)
{
    func_80035664(10, 1);
    func_80025CFC();
}

void func_80037E20(void)
{
    func_80035664(10, 0);
    func_80025CFC();
}

void func_80037E4C(void)
{
    func_80035664(11, 1);
    func_80025CFC();
}

void func_80037E78(void)
{
    func_80035664(11, 0);
    func_80025CFC();
}

void func_80037EA4(void)
{
    func_80035664(13, 0);
    func_80025CFC();
}

void func_80037ED0(void)
{
    func_80035664(13, 1);
    func_80025CFC();
}

void func_80037EFC(void)
{
    func_80035664(13, 2);
    func_80025CFC();
}

void func_80037F28(void)
{
    func_80035664(13, 3);
    func_80025CFC();
}

void func_80037F54(void)
{
    func_80035664(14, 1);
    func_80025CFC();
}

void func_80037F80(void)
{
    func_80035664(14, 0);
    func_80025CFC();
}

void func_80037FAC(void)
{
    int seq;

    seq = func_80035A18(0);
    func_80035664(0, 0);
    func_80035664(12, -1);
    func_80035664(0, 1);
    func_80035664(12, -1);
    func_80035664(0, seq);
    func_80025CFC();
}

void func_80038018(void)
{
    func_80035664(12, 0);
    func_80025CFC();
}

void func_80038044(void)
{
    func_80035664(15, 0);
    func_80025CFC();
}

void func_80038070(void)
{
    func_80035664(15, 1);
    func_80025CFC();
}
