/* Matched 2026-10-17 through the round-trip oracle (g3org_jp first;
 * cross-target byte-identical in mainmenu_jp, g3_eu, g3org_jp, g3org_eu -
 * the matching lane's GTE families queue item).
 *
 * LIBGTE RotTrans: the vector (a0) goes into VXY0/VZ0 ($0/$1), mvmva
 * 1,0,0,0,0 (0x4A480012 - GNU as has no GTE mnemonics, banked as its
 * exact retail .word) rotates it by the current matrix, the IR1/IR2/IR3
 * results ($25/$26/$27) store through a1 as the rotated vector, and
 * FLAG (C31) is the return value. Retail keeps the flag store
 * *a2 = flag IN the jr delay slot - the compiler sinks the independent
 * store into the empty slot by itself (the ReadGeomOffset sink law,
 * wanted direction: the delay slot is free because the return value
 * needs no sra).
 *
 * psyq prototype: long RotTrans(VECTOR *v, VECTOR *vout, long *flag);
 * args stay long* so gcc emits no caller-side extensions.
 */
long RotTrans(long *a0, long *a1, long *a2)
{
    register long flag asm("$2");
    __asm__ volatile(
        "lwc2 $0, 0x0($4)\n"
        "\tlwc2 $1, 0x4($4)\n"
        "\tnop\n"
        "\t.word 0x4A480012\n" /* mvmva 1,0,0,0,0 */
        "\tswc2 $25, 0x0($5)\n"
        "\tswc2 $26, 0x4($5)\n"
        "\tswc2 $27, 0x8($5)\n"
        "\tcfc2 $2, $31"
        : "=r"(flag));
    *a2 = flag;
    return flag;
}
