/* Matched 2026-10-17 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% twins, see the pair-report matching lane).
 *
 * LIBGTE member: full rtpt over the first three vertices (VXY0/VZ0 ..
 * VXY2/VZ2 loaded from a0/a1/a2), the three SXY fifo results stored
 * through the caller's stacked output pointers (o32 args 5-7 at
 * 0x10/0x14/0x18($sp)), FLAG (C31) captured after rtpt; then the 4th
 * vertex is loaded into VXY0/VZ0 and rtps'd, its SXY2 result plus the
 * MAC0 (DR8) division result stored through stacked args 8-9, and the
 * combined FLAG word (rtps FLAG | rtpt FLAG) through stacked arg 10.
 * Returns SZ3 (DR19) >> 2 - the ordering-table depth cell - with the
 * sra in the return delay slot exactly as retail.
 *
 * The body is one volatile asm block with the retail register
 * assignments hardcoded ($3 = rtpt FLAG, $8/$9/$10 = the stacked-arg
 * pointers, $2 = SZ3): gcc-2.6.3's scheduler floats the sp-relative
 * arg loads across plain volatile asms (no memory clobber) and
 * pre-loads them all at entry with one (memory clobbers force all six
 * loads to function entry), so neither plain-C decomposition
 * reproduces retail's load placement. rtpt/rtps are GTE command
 * aliases GNU as does not know, emitted as their exact retail words.
 * The sra of the return value is plain C on the $2 register-var
 * output so the compiler emits it into the jr delay slot.
 */
long RotTransPers4(long *a0, long *a1, long *a2, long *a3)
{
    register long vv asm("$2");
    __asm__ volatile(
        "lwc2 $0, 0x0($4)\n"
        "lwc2 $1, 0x4($4)\n"
        "lwc2 $2, 0x0($5)\n"
        "lwc2 $3, 0x4($5)\n"
        "lwc2 $4, 0x0($6)\n"
        "lwc2 $5, 0x4($6)\n"
        "nop\n"
        ".word 0x4A280030\n" /* rtpt */
        "lw $8, 0x10($sp)\n"
        "lw $9, 0x14($sp)\n"
        "lw $10, 0x18($sp)\n"
        "swc2 $12, 0x0($8)\n"
        "swc2 $13, 0x0($9)\n"
        "swc2 $14, 0x0($10)\n"
        "cfc2 $3, $31\n"
        "lwc2 $0, 0x0($7)\n"
        "lwc2 $1, 0x4($7)\n"
        "nop\n"
        ".word 0x4A180001\n" /* rtps */
        "lw $8, 0x1C($sp)\n"
        "lw $9, 0x20($sp)\n"
        "lw $10, 0x24($sp)\n"
        "swc2 $14, 0x0($8)\n"
        "swc2 $8, 0x0($9)\n"
        "cfc2 $8, $31\n"
        "mfc2 $2, $19\n"
        "or $8, $8, $3\n"
        "sw $8, 0x0($10)\n"
        : "=r"(vv)
        :
        : "3", "8", "9", "10");
    return vv >> 2;
}
