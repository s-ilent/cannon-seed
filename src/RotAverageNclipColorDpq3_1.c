/* Matched 2026-10-21 through the offline probe first (64/64 slots, full
 * masks, zero relocations, against all five standalone-row renders) and
 * the judge oracle second; the six-target wave lands as one C source -
 * five standalone 0x100 sdk rows flip (g3_eu file 0x3DC4C, g3_jp 0x3E208,
 * g3org_jp 0x3B6A4, g3org_eu 0x3B0A0, mainmenu_eu 0x52128 - all five
 * labels are stale woven-era names, the true VAs are the curated pins)
 * and mainmenu_jp's copy splits out of the 0x110 data row at file 0x5271C
 * as its head (the 0x10 tail is the four-word gp-store stub at file
 * 0x5281C, true VA 0x8007201C, which the render already labels).
 *
 * LIBGTE RotAverageNclipColorDpq3_1: the per-vertex expansion of the
 * landed 0xd0 sibling RotAverageNclipColorDpq3. Where the sibling rotates
 * and projects all three vertices with ONE rtpt and lights them with ONE
 * ncdt, this member does each vertex separately: three SINGLE rtps
 * commands (0x4A180001), one per vertex (a0/a1/a2), each followed by mfc2
 * capturing IR0 - the per-vertex depth quotient - into $15/$24/$25. The
 * flag pointer (stack arg at 0x38) receives LZCR ($31) via cfc2, nclip
 * (0x4B400006) puts the normal-clip value into MAC0 ($24), which mfc2
 * reads into $2 as the return value. The positive branch runs three
 * per-vertex NCDS commands (0x4AE80413): normal i loads into the V
 * registers (a3, then the stack args at 0x10/0x14), the single color word
 * (0x18) loads into RGB ($6) once, and before EACH NCDS the captured
 * depth quotient mtc2s back into IR0 - the Dpq depth-cue carry that makes
 * per-vertex depth cueing correct (the sibling's single ncdt never needs
 * the restore). After each NCDS the projected SXY fifo register
 * ($12/$13/$14, still holding the three rtps results) stores through the
 * stack args at 0x1C/0x20/0x24 and the colored RGB2 ($22 - the color
 * fifo's newest-entry slot) through 0x28/0x2C/0x30; avsz3 (0x4B58002D)
 * writes OTZ ($7) through the otz pointer (0x34). The negative branch
 * skips straight to the epilogue.
 *
 * psyq prototype: long RotAverageNclipColorDpq3_1(SVECTOR *v0, SVECTOR
 * *v1, SVECTOR *v2, SVECTOR *n0, SVECTOR *n1, SVECTOR *n2, CVECTOR *col,
 * long *sxy0, long *sxy1, long *sxy2, CVECTOR *c0, CVECTOR *c1, CVECTOR
 * *c2, long *otz, long *flag); args stay long* so gcc emits no
 * caller-side extensions. One volatile asm block with the retail register
 * assignments hardcoded; the two branches are banked as their exact
 * retail .words (maspsx appends a hazard nop after every branch mnemonic
 * under .set reorder, which retail does not carry) - the bgtz offset is 3
 * (target = the lighting path's first lwc2) and the skip-b offset is
 * 0x22 with BOTH delay slots nop (the landed sibling's shared-slot law
 * does NOT hold here: retail's b delay slot is a plain nop, and the b
 * target is the jr's own slot after the block). rtps/ncds/nclip/avsz3
 * have no GNU-as mnemonics - banked as their exact retail .words; every
 * mtc2/mfc2/cfc2/lwc2/swc2 retail word matches gas's own encodings
 * exactly (0x480F4000 mfc2 $15,$8, 0x488F4000 mtc2 $15,$8, 0x4843F800
 * cfc2 $3,$31, 0x4802C000 mfc2 $2,$24, 0x48083800 mfc2 $8,$7). The $2
 * register-var output needs no post-block move (mfc2 $2, $24 is the last
 * write to $2 in the block) and the epilogue is the stock frameless jr
 * $ra with a nop delay slot landing exactly on retail's 62nd/63rd slots.
 * The $15/$24/$25 captures are internal to the block: written by the
 * capturing mfc2s, read back by the restoring mtc2s.
 */
long RotAverageNclipColorDpq3_1(long *a0, long *a1, long *a2, long *a3,
                                long *a4, long *a5, long *a6, long *a7,
                                long *a8, long *a9, long *a10, long *a11,
                                long *a12, long *a13, long *a14)
{
    register long vv asm("$2");
    __asm__ volatile(
        "lwc2 $0, 0x0($4)\n"
        "\tlwc2 $1, 0x4($4)\n"
        "\tnop\n"
        "\t.word 0x4A180001\n" /* rtps */
        "\tmfc2 $15, $8\n"
        "\tlwc2 $0, 0x0($5)\n"
        "\tlwc2 $1, 0x4($5)\n"
        "\tnop\n"
        "\t.word 0x4A180001\n" /* rtps */
        "\tmfc2 $24, $8\n"
        "\tlwc2 $0, 0x0($6)\n"
        "\tlwc2 $1, 0x4($6)\n"
        "\tnop\n"
        "\t.word 0x4A180001\n" /* rtps */
        "\tlw $2, 0x38($sp)\n"
        "\tmfc2 $25, $8\n"
        "\tcfc2 $3, $31\n"
        "\tnop\n"
        "\tsw $3, 0x0($2)\n"
        "\t.word 0x4B400006\n" /* nclip */
        "\tlw $11, 0x10($sp)\n"
        "\tlw $12, 0x14($sp)\n"
        "\tlw $13, 0x18($sp)\n"
        "\tmfc2 $2, $24\n"
        "\tnop\n"
        "\t.word 0x1C400003\n" /* bgtz $2, 1f - target is bgtz+12 */
        "\tnop\n"
        "\t.word 0x10000022\n" /* b 2f - both delay slots are nops in retail */
        "\tnop\n"
        "1:\n"
        "\tlwc2 $0, 0x0($7)\n"
        "\tlwc2 $1, 0x4($7)\n"
        "\tlwc2 $6, 0x0($13)\n"
        "\tmtc2 $15, $8\n"
        "\tnop\n"
        "\t.word 0x4AE80413\n" /* ncds */
        "\tlw $8, 0x1c($sp)\n"
        "\tlw $9, 0x28($sp)\n"
        "\tswc2 $12, 0x0($8)\n"
        "\tswc2 $22, 0x0($9)\n"
        "\tlwc2 $0, 0x0($11)\n"
        "\tlwc2 $1, 0x4($11)\n"
        "\tmtc2 $24, $8\n"
        "\tnop\n"
        "\t.word 0x4AE80413\n" /* ncds */
        "\tlw $8, 0x20($sp)\n"
        "\tlw $9, 0x2c($sp)\n"
        "\tswc2 $13, 0x0($8)\n"
        "\tswc2 $22, 0x0($9)\n"
        "\tlwc2 $0, 0x0($12)\n"
        "\tlwc2 $1, 0x4($12)\n"
        "\tmtc2 $25, $8\n"
        "\tnop\n"
        "\t.word 0x4AE80413\n" /* ncds */
        "\tlw $8, 0x24($sp)\n"
        "\tlw $9, 0x30($sp)\n"
        "\tswc2 $14, 0x0($8)\n"
        "\tswc2 $22, 0x0($9)\n"
        "\t.word 0x4B58002D\n" /* avsz3 */
        "\tlw $9, 0x34($sp)\n"
        "\tmfc2 $8, $7\n"
        "\tnop\n"
        "\tsw $8, 0x0($9)\n"
        "2:\n"
        : "=r"(vv)
        : : "3", "8", "9", "11", "12", "13", "15", "24", "25");
    return vv;
}
