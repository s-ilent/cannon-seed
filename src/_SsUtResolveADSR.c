/* Matched 2026-10-17 through the round-trip oracle (mainmenu_jp first;
 * byte-identical twins in all eight targets - region-pair 100.00% x4,
 * see the coddog/pair-report lane).
 *
 * LIBSND UT member .text+0x0 (extent 0x5c; sdk_members.py unique
 * placement + sig-db agree; the curated rows carry the evidence per
 * target). Resolves the two packed ADSR attribute words of a VAB tone
 * into the per-field halfword struct the SsSv* synth family reads:
 * out[0..4] = AR/DR/SL/RR/keep fields shifted out of adsr1/adsr2,
 * out[5..8] = the four flag bits stored verbatim (0x8000 of adsr1 ->
 * +0xA, 0x8000/0x20 of adsr2 -> +0xC/+0xE, 0x4000 of adsr2 -> +0x10).
 * _SsUtBuildADSR is the exact inverse (same member, .text+0x5c).
 *
 * Source shapes that make GCC 2.6.3 reproduce the retail body:
 * 1. UNSIGNED SHORT PARAMS force the `andi $v1,$a0,0xFFFF` register
 *    re-materialization retail shows before the two srl chains - the
 *    o32 callee may not assume zero-extension of sub-word args.
 * 2. STORE ORDER IS PROGRAM ORDER: +0xA,+0xC,+0x10,+0xE (the four
 *    flag bits, computed from immediates) then +0x0,+0x2,+0x4,+0x6,
 *    +0x8 (the srl/andi fields) - retail's exact store sequence; the
 *    last store lands in the return delay slot.
 * 3. Frameless leaf: no cc-post marker needed (no frame, no calls);
 *    the return delay slot carries the final sh exactly as retail.
 */

void _SsUtResolveADSR(unsigned short adsr1, unsigned short adsr2, unsigned short *out)
{
    out[5] = adsr1 & 0x8000;
    out[6] = adsr2 & 0x8000;
    out[8] = adsr2 & 0x4000;
    out[7] = adsr2 & 0x20;
    out[0] = (adsr1 >> 8) & 0x7F;
    out[1] = (adsr1 >> 4) & 0xF;
    out[2] = adsr1 & 0xF;
    out[3] = (adsr2 >> 6) & 0x7F;
    out[4] = adsr2 & 0x1F;
}
