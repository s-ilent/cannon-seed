/* The LBA -> packed-BCD MSF time encoder - psyq's CdIntToPos shape
 * (g3_eu row, one src unit per row under the row's own walk name; the
 * seven members are byte-identical 0x104 rows, one per game target - the
 * census x7 size=0x104 wave, the seventeenth-return queue item 1). The
 * input gains the 150-sector pregap offset, then the CD-MSF law divides it
 * out - 75 sectors per second, 60 seconds per minute - and each of the
 * three fields packs as two decimal nibbles ((field/10)<<4 + field%10)
 * into the CdlLOC record {minute, second, sector}. The divisions compile
 * to the classic signed-magic sequences (0x1B4E81B5>>3 for /75, the
 * 0x88888889 add-shift-5 pattern for /60, 0x66666667>>2 for /10) and the
 * retail schedule interleaves the three quotient magics' mult/mfhi pairs:
 * the sector BCD is computed first (its /10 magic loads before the /75
 * quotient lands), the /60 division stays in a variable so the minute
 * digits divide the variable (no nested-division re-fold), and the stores
 * run second, sector, minute with the minute store filling the return's
 * delay slot. Word-level identity: scripts/wave104_check.py proves the
 * seven retail rows byte-identical (65 words, zero jals, zero lui, zero
 * gp-relative - relocation-free, one decode lands all seven).
 *
 * psyq prototype: char *CdIntToPos(int i, CdlLOC *p) - the counter is the
 * FIRST argument (retail returns $a1, the record pointer, and computes on
 * $a0); the walk name stays (the row-name == unit-name law); the psyq
 * identity is provenance, not an adopted symbol.
 */
char *func_800603DC(int i, char *out)
{
    int t;
    int s;
    int u;
    int m;
    int h;

    i += 150;
    t = i / 75;
    s = ((i % 75) / 10 << 4) + ((i % 75) % 10);
    u = t / 60;
    m = ((t % 60) / 10 << 4) + ((t % 60) % 10);
    h = ((u / 10) << 4) + (u % 10);
    out[1] = m;
    out[2] = s;
    out[0] = h;
    return out;
}
