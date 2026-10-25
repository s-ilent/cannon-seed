/* Matched 2026-10-25 (window cron-202610251706) - the walk graveyard's
 * rotation-matrix commit tail, the smallest of the five clean landing
 * classes the banked walk staged (window cron-202610251551): func_8005DED4
 * 0x30, the TAIL of every #0x110 walk mega-row at rel +0xE0 (ends exactly
 * at the row end), with byte-identical twins in all eight executables -
 * mainmenu_jp holds it inside the data_80066CF4 graveyard head row
 * (0x8005DED4..0x8005DF04, bounded by func_8005DE24's end and
 * func_8005DF04's start, a clean cut with no row crossing), the seven
 * other targets carry it as the tail of their own #0x110 mega-row. The
 * proof's word-search pins the sites exactly (one occurrence per target;
 * the walk record's row names carry the banked woven-name drift, the
 * offsets rule - file offsets in the target .bin, VA = file + 0x8001F800):
 *
 *   slps_00270   0x014CF0  (0x800344F0, func_80034410 tail rel +0xE0)
 *   sces_00269   0x0147B8  (0x80033FB8)
 *   mainmenu_jp  0x03E6D4  (0x8005DED4, inside the data_80066CF4 head row)
 *   mainmenu_eu  0x03E0B4  (0x8005D8B4, func_8005D7D4 tail rel +0xE0)
 *   g3_jp        0x02A1C0  (0x800499C0)
 *   g3_eu        0x029BD8  (0x800493D8)
 *   g3org_jp     0x02765C  (0x80046E5C)
 *   g3org_eu     0x02702C  (0x8004682C)
 *
 * The body is frameless pure CPU code, the commit half of a SetRotMatrix-
 * shaped writer: the row's head code leaves the packed matrix halves in
 * the entry register state ($8/$9/$10/$12/$14/$15/$24 - the scrambled rt
 * cycle the walk banked), and the tail merges the lo|hi pairs and commits
 * the GTE rotation matrix control registers c0..c4 (R11R12, R13R21,
 * R22R23, R31R32, R33): $8 |= $12 goes to c1, ($9 << 16) | ($15 & 0xffff)
 * goes to c2, while c0 takes $14 raw, c3 takes $24 raw and c4 takes $10
 * raw - then returns the record pointer (addu $2,$4,$0, the ApplyMatrixLV
 * register-var pattern). No loads, no stores: every input arrives in the
 * entry register state the row head staged, so the body is the walk's
 * shared "SetRotMatrix-then-store" tail and the entry register reads are
 * the honest inline-exposure record of that staging.
 *
 * The block carries the retail words 1:1 (ctc2 assembles natively; no
 * reloc slots - frameless leaf, no jal, no lui/%lo). The return tail
 * follows the landed TransMatrix pattern (addu $2 inside the asm,
 * captured through the register-var output; `return ret` then emits the
 * frameless jr $31 + nop delay exactly as retail).
 *
 * psyq prototype: MATRIX *func_8005DED4(MATRIX *m); the record pointer
 * is the only true argument ($4); the five matrix words ride the caller's
 * register state, not the ABI.
 */
long *func_8005DED4(long *m)
{
    register long *ret asm("$2");
    __asm__ volatile(
        "or $8, $8, $12\n"
        "\tandi $15, $15, 0xffff\n"
        "\tsll $9, $9, 16\n"
        "\tor $9, $9, $15\n"
        "\tctc2 $14, $0\n"
        "\tctc2 $8, $1\n"
        "\tctc2 $9, $2\n"
        "\tctc2 $24, $3\n"
        "\tctc2 $10, $4\n"
        "\taddu $2, $4, $0"
        : "=r"(ret));
    return ret;
}
