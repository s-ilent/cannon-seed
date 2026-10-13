/* Matched 2026-10-13 through the round-trip oracle (mainmenu_jp).
 *
 * LIBETC INTR member .text+0x154 (extent 0x10; sig-db sig matches
 * retail: lui+lhu on the in-trap flag, jr $ra + nop). Returns the
 * interrupt-trap in-progress flag: trapIntr stores 1 through it on
 * trap entry (ori $v0,1 + sh) and 0 on exit (sh $zero); CheckCallback
 * hands it back. The halfword has no Psy-Q symbol name (INTR.OBJ
 * carries no bss; its COFF symbol table lists only member functions
 * + kernel externals - all sig-db versions 2.60-4.70 agree), so the
 * role-descriptive curated name resolves extern via the per-target
 * symbols file; the bytes sit inside initialized data and the initial
 * value varies per target (retail never calls any of this subsystem).
 * Full statics evidence under target: mainmenu_jp in
 * symbols.curated.txt.
 */
extern unsigned short intr_trap_flag;

long CheckCallback(void)
{
    return intr_trap_flag;
}
