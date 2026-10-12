/* Probe: the E1A8..E250 trampoline-band idioms measured on the mainmenu
 * fabric (docs/FABRIC.md). Compiled with tools/cc.sh — compare the emitted
 * .mas.s / objdump words against
 * asm/mainmenu_jp/nonmatchings/func_8002DE00.s (glabels E1A8..E1FC).
 * Not part of any build target; lives here purely as compiler-pin
 * evidence for the family-level C-unit decision.
 *
 * Shapes under test (register names differ from retail because a
 * standalone probe receives its inputs per the ABI; the idioms are the
 * point, not the registers):
 *
 *   A  switch chain (E1A8): sparse cases compile to
 *        ori $v0,0x8; beq $x,$v0,L8; ori $v0,0x100 (branch delay slot!);
 *        beq $x,$v0,L100; nop; j Ldefault; nop
 *      i.e. variable-first beq and the NEXT case's compare value
 *      scheduled into the previous beq's delay slot.
 *
 *   B  back-to-back calls (E1FC head):
 *        addu $a0,$x,$zero; jal f; ori $a1,C (jal delay slot);
 *        addu $a0,$x,$zero; addu $a1,$zero,$zero; jal g;
 *        addiu $a2,-1 (jal delay slot)
 *      i.e. the last independent argument-setup instruction is scheduled
 *      into each call's delay slot.
 *
 *   C  goto chain (E1C4 -> E1D8): a fragment ends
 *        j Lnext; <independent insn> (j delay slot)
 *      where Lnext's body opens with the jal whose a0 was prepared by
 *      the delay-slot instruction — control transfer used as free
 *      instruction space. In retail E1D8 has no a0 setup of its own.
 */

extern void helper(int, int);        /* func_800266B8 shape */
extern void helper2(int, int, int);  /* func_80026414 shape */
extern void skip(void);

/* Shape A. */
void shape_a(int v1)
{
    switch (v1) {
    case 8:
        helper(v1, 0x91F);
        helper2(v1, 0, -1);
        break;
    case 0x100:
        helper(v1, 0x91D);
        break;
    default:
        skip();
        break;
    }
}

/* Shape B (also covers E1FC's call pair). */
void shape_b(int s1)
{
    helper(s1, 0x91F);
    helper2(s1, 0, -1);
}

/* Shape C: force a j whose target opens with the next call's a0 setup;
 * watch what the scheduler puts in the j's delay slot. */
void shape_c(int s1, int which)
{
    if (which) {
        helper(s1, 0x91C);
        goto next;
    }
    skip();
next:
    helper(s1, 0x91E);
    helper2(s1, 0, -1);
}
