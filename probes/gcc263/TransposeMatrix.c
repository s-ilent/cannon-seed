/* TransposeMatrix - LIBGTE 3x3 short-matrix transpose, byte-identical in
 * five of the six targets that carry it (near_twin_census wave, window
 * cron-20261020-2231): file 0x14668 slps_00270, 0x448F4 mainmenu_eu,
 * 0x30ADC g3_jp, 0x30418 g3_eu, 0x2D86C g3org_eu (the sces_00269 copy
 * sits inside the merged 0x480 asm unit func_800370E4 at 0x14834 - that
 * unit carries a dozen internal glabels and needs a re-boundary before
 * its row can flip). a0 = source (read-only), a1 = destination (written),
 * v0 = the destination pointer returned; the early addu v0,a1,zero at
 * slot 1 merges the return pseudo with the store base. NO relocation
 * slots anywhere in the body.
 *
 * Decode state (probe 17/20 shape, register-choice open):
 * - SIGN LAW: plain short-typed copies (short locals, struct fields,
 *   casts) all narrow to lhu; INT-typed temps force the signed lh
 *   retail uses (v_int/v_il probes, 0x84 opcodes throughout).
 * - SCHEDULE LAW: straight row-major statements serialize (one temp,
 *   six load-delay nops, 28 words); per-row local batches give the
 *   3+3 rhythm (20 words, wrong rhythm); the 1:1 interleaved three-int
 *   rotation below reproduces the retail rhythm EXACTLY - every load/
 *   store position and the addu/jr slots match (17/20, the three ok
 *   slots plus offset agreement on all sixteen load/store words).
 * - OPEN: register choice. Retail rotates t1/t2/t3 ($9/$10/$11) and
 *   never touches v1/a1/a2 after the base copy; stock cc1 2.6.3 hands
 *   the temps v1/a1/a2 (its preferred-order allocation). Same family
 *   as the GsTMDdivTG4LFG open question banked in 978f4082 (Sony sched
 *   patch or a flag): the schedule is exact, the allocator's hard-reg
 *   preference is not. Landing waits on that pin - judge masks only
 *   relocation fields, register fields are honest-compare.
 */
int *TransposeMatrix(short src[3][3], short dst[3][3])
{
    int a, b, c;
    a = src[0][0];
    dst[0][0] = a;
    b = src[1][0];
    c = src[2][0];
    dst[0][1] = b;
    a = src[0][1];
    dst[0][2] = c;
    b = src[1][1];
    dst[1][0] = a;
    c = src[2][1];
    dst[1][1] = b;
    a = src[0][2];
    dst[1][2] = c;
    b = src[1][2];
    dst[2][0] = a;
    c = src[2][2];
    dst[2][1] = b;
    dst[2][2] = c;
    return (int *)dst;
}
