/* Matched 2026-10-17 through the round-trip oracle (g3org_jp first;
 * cross-target byte-identical in mainmenu_jp, g3_eu, g3org_jp, g3org_eu -
 * the matching lane's GTE families queue item).
 *
 * LIBGTE RotTransPers: the vector (a0) goes into VXY0/VZ0 ($0/$1), rtps
 * (0x4A180001 - GNU as has no GTE mnemonics, banked as its exact retail
 * .word), the SXY fifo result ($14) stores through a1, the MAC0 division
 * result ($8) through a2, and FLAG (C31) through a3. Returns SZ3 (DR19)
 * >> 2 - the ordering-table depth cell - with the sra in the return
 * delay slot exactly as retail.
 *
 * One volatile asm block with the retail register assignments hardcoded
 * ($4-$7 = the o32 args; the banked RotTransPers4 class). cfc2 $31 and
 * mfc2 $19 assemble as real mnemonics (proven on RotTransPers4); the
 * sra of the return value is plain C on the $2 register-var output so
 * the compiler emits it into the jr delay slot.
 *
 * psyq prototype: long RotTransPers(VECTOR *v, long *sxy, long *p,
 * long *flag); args stay long* so gcc emits no caller-side extensions.
 */
long RotTransPers(long *a0, long *a1, long *a2, long *a3)
{
    register long vv asm("$2");
    __asm__ volatile(
        "lwc2 $0, 0x0($4)\n"
        "\tlwc2 $1, 0x4($4)\n"
        "\tnop\n"
        "\t.word 0x4A180001\n" /* rtps */
        "\tswc2 $14, 0x0($5)\n"
        "\tswc2 $8, 0x0($6)\n"
        "\tcfc2 $3, $31\n"
        "\tmfc2 $2, $19\n"
        "\tsw $3, 0x0($7)"
        : "=r"(vv)
        :
        : "3");
    return vv >> 2;
}
