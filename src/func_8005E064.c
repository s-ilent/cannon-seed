/* Staged 2026-10-25 (window cron-202610252206) - the walk graveyard's
 * ROW1-final 0x30 whole function, the SECOND row-final tail candidate the
 * boundary probe surfaced (window cron-202610252051: "the new E064 0x30
 * whole function joins DED4's 0x30 as the second row-final tail
 * candidate"). True extent 0x8005E064..0x8005E094, the last 0x30 of
 * mainmenu_jp's data_80066CF4 graveyard head row (yaml 0x3E1B4 # 0x6e0;
 * file offset 0x3E864), cut clean by the probe's epilogue scanner - the
 * walk census sliced it inside the crossing host func_8005E020 and never
 * saw it as its own function.
 *
 * The body decodes at instruction level (the 2051 record): a
 * single-vector transform through the CURRENT rotation matrix -
 *
 *   lw   $8, 0x0($4)     # the 2-word staging: the packed VXY0/VZ0 record
 *   lw   $9, 0x4($4)     #   at (a0), NO mask (whole words into the GTE)
 *   mtc2 $8, $0          # VXY0
 *   mtc2 $9, $1          # VZ0
 *   nop
 *   .word 0x4A486012     # mvmva 1,0,0,3,0 - multiply by the rotation
 *                        #   matrix, no translation (the walk chain's cmd)
 *   swc2 $9, 0x0($5)     # IR1/IR2/IR3 straight to the (a1) record
 *   swc2 $10, 0x4($5)
 *   swc2 $11, 0x8($5)
 *   addu $2, $6, $0      # return a2 - a pointer it never stores through
 *   jr   $31
 *   nop
 *
 * The probe's boundary table closes the row arithmetic EXACTLY: ROW1 0x6e0
 * = 2 nops + 0x160 (instance-1) + 0x10c + 0xe4 + 0xe8 + 0x110 + 0x160
 * (light-shuffle) + 0x30 (this unit) - and after the staged DED4 wave's
 * three-way split (scripts/surgery_ded4_wave.py: 0x520 + 0x30 + 0x190),
 * this unit's cut composes as ONE more row-final cut: data_8005DF04 0x190
 * -> 0x160 (the light-shuffle composite) + 0x30 (this file). 0x190 = 0x160
 * + 0x30, the split is exact and leaves no residue.
 *
 * Proof basis (window cron-202610252206, oracle DOWN - discs gone, links
 * expired): the twelve words above are WORD-IDENTICAL to the committed
 * row's encoding (scripts/prove_func_8005E064.py, offline, zero oracle -
 * the same committed-row class the wrapper quartet proved under). The x8
 * twin word-search is THE ORACLE'S FIRST DECODING JOB on the disc-return
 * (the graveyard-x8-family law expects byte-identical twins in all eight
 * executables; in the seven non-mainmenu_jp targets the twin must sit
 * INSIDE one of their five walk mega-rows - 0x30 is not one of the five
 * row sizes - so the search pins each target's site before any cut). The
 * script carries that search, witness-gated: it refuses the unwitnessed
 * baselines and runs the eight-way site pin the moment the disc-return
 * restores 8/8.
 *
 * The block carries the retail words 1:1 (mtc2/swc2 assemble natively per
 * the landed ApplyMatrixSV/ApplyMatrixLV precedents; the mvmva stays
 * .word-encoded exactly as ApplyMatrixLV banked it; no reloc slots -
 * frameless leaf, no jal, no lui/%lo, the dw=0 class first-shot landings
 * want). The return tail is ApplyMatrixLV's own register-var pattern
 * (addu $2, $6, $0 inside the asm).
 *
 * psyq prototype: long *func_8005E064(long *vec, long *dst, long *out);
 * a0 = the packed 2-word vector record (VXY0/VZ0 halves, 8 bytes), a1 =
 * the 3-word destination the IR1-3 stores write, a2 = the pointer the
 * function returns without ever storing through it (the walk's honest
 * observation - the caller's staging, not this body's, gives it meaning).
 */
long *func_8005E064(long *vec, long *dst, long *out)
{
    register long *ret asm("$2");
    __asm__ volatile(
        "lw $8, 0x0($4)\n"
        "\tlw $9, 0x4($4)\n"
        "\tmtc2 $8, $0\n"
        "\tmtc2 $9, $1\n"
        "\tnop\n"
        "\t.word 0x4A486012\n" /* mvmva 1,0,0,3,0 */
        "\tswc2 $9, 0x0($5)\n"
        "\tswc2 $10, 0x4($5)\n"
        "\tswc2 $11, 0x8($5)\n"
        "\taddu $2, $6, $0"
        : "=r"(ret));
    return ret;
}
