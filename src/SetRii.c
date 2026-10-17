/* Matched 2026-10-18 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% twins across slps_00270, sces_00269, g3_jp,
 * g3_eu, g3org_jp - the matching lane's GTE Set-family cluster).
 *
 * LIBGTE member: ctc2 the three arguments straight into the GTE
 * control registers $0/$2/$4 (the RiiR/RiiG/RiiB light-colour
 * parameter slots). Frameless leaf.
 */
void SetRii(long r1, long r2, long r3)
{
    __asm__ volatile("ctc2 %0, $0" :: "r"(r1));
    __asm__ volatile("ctc2 %0, $2" :: "r"(r2));
    __asm__ volatile("ctc2 %0, $4" :: "r"(r3));
}
