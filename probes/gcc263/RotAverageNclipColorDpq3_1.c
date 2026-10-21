/* RotAverageNclipColorDpq3_1 probe draft (window cron-202610211743): the
 * 0x100 LIBGTE member, byte-identical across the six game modules (the
 * boots have no member; found by the in-tree renders - all five standalone
 * row renders carry the same 64 words, and mainmenu_jp's data-row copy
 * renders the same 64 words plus a separate 0x10 tail stub func_8007201C).
 *
 * Retail body (g3_jp render func_80066D48.s): three SINGLE rtps projections
 * (0x4A180001 - not the sibling's rtpt), one per vertex, each followed by
 * mfc2 reading IR0 into $15/$24/$25 - the per-vertex depth quotients are
 * CAPTURED, and the lighting path then mtc2s each captured quotient back
 * into IR0 before its NCDS (the Dpq depth-cue carry: the sibling's single
 * ncdt needs no such restore, this per-vertex expansion does); cfc2 reads
 * LZCR ($31) and *flag = LZCR; nclip; the
 * MAC0 value returns via the $2 register-var output (mfc2 $2, $24 is the
 * last write to $2 in the block, so no post-block move). The positive
 * branch runs three per-vertex NCDS commands (0x4AE80413): normal i loads
 * into V0 (a3 then the stack args at 0x10/0x14), the single color word
 * (0x18) loads into RGB once, and after each NCDS the SXY fifo register
 * ($12/$13/$14) stores through the sxy pointer and RGB2 ($22 - the color
 * fifo's newest-entry slot) stores through the color pointer. avsz3 writes
 * OTZ ($7) through the otz pointer (0x34). The negative branch skips
 * straight to the epilogue: retail's b delay slot is a nop (unlike the
 * landed sibling's shared-slot law), so both branches bank as their exact
 * retail .words (maspsx would append a hazard nop under .set reorder):
 * bgtz offset 3 (0x1C400003, target = the first lwc2 of the lighting
 * path) and b offset 0x22 (0x10000022, target = the jr's slot after the
 * block). rtps/ncds/nclip/avsz3 have no GNU-as mnemonics - .word banked.
 * mtc2/mfc2/cfc2/lwc2/swc2 retail words match gas's own encodings exactly
 * (verified arithmetically: 0x480F4000 mfc2 $15,$8, 0x488F4000 mtc2 $15,$8,
 * 0x4843F800 cfc2 $3,$31, 0x4802C000 mfc2 $2,$24, 0x48083800 mfc2 $8,$7).
 * Clobbers: $3/$8/$9/$11-$13 plus $15/$24/$25 (written by the capturing
 * mfc2s, read back by the restoring mtc2s - internal to the block).
 *
 * Landing recipe (staged for the next oracle window; the yaml rows are
 * verified in-tree): five pure yaml flips - g3_eu [0x3DC4C] func_8006665C,
 * g3_jp [0x3E208] func_80066D48, g3org_jp [0x3B6A4] func_80063AC4,
 * g3org_eu [0x3B0A0] func_800634C0, mainmenu_eu [0x52128] func_8007DBE8,
 * each 0x100 sdk asm -> c RotAverageNclipColorDpq3_1 (all five labels are
 * stale woven-era names - the true VAs are the curated pins: g3_eu
 * 0x8005D44C, g3_jp 0x8005DA08, g3org_jp 0x8005AEA4, g3org_eu 0x8005A8A0,
 * mainmenu_eu 0x80071928; interestingly each woven label equals the body's
 * address in the WOVEN baseline, the deframe shift made visible); plus the
 * mainmenu_jp split: [0x5271C, data, data_8007E1DC] 0x110 -> [0x5271C, c,
 * RotAverageNclipColorDpq3_1] 0x100 + [0x5281C, asm, func_8007201C] 0x10
 * (the tail is a four-word gp-store stub the render already labels as its
 * own fragment - lui $at,0x8019; sw $a0,0x4d70($gp); jr $ra; nop - code,
 * not data, correcting the scout's "0x10 data tail carve" wording), and a
 * new curated pin in symbols.mainmenu_jp.txt: RotAverageNclipColorDpq3_1 =
 * 0x80071F1C (type:func, pinned member row). Offline probe: 64/64 slots
 * with full masks (zero relocations - the body is relocation-free) against
 * ALL FIVE standalone-row renders; judge-ready first shot.
 *
 * psyq prototype: long RotAverageNclipColorDpq3_1(SVECTOR *v0, SVECTOR *v1,
 * SVECTOR *v2, SVECTOR *n0, SVECTOR *n1, SVECTOR *n2, CVECTOR *col,
 * long *sxy0, long *sxy1, long *sxy2, CVECTOR *c0, CVECTOR *c1,
 * CVECTOR *c2, long *otz, long *flag); args stay long* so gcc emits no
 * caller-side extensions. Frameless: the stacked args are read at the
 * caller's 0x10($sp) window exactly as retail.
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
        "\t.word 0x1C400003\n" /* bgtz $2, 1f */
        "\tnop\n"
        "\t.word 0x10000022\n" /* b 2f - delay slot is a nop, epilogue follows */
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
