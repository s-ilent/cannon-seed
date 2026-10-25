/* Matched 2026-10-26 through the judge oracle (the pair-pool's second
 * harvest wave; the row-family-normalized pair gate's x8 member -
 * byte-identical across all four region pairs at 100.00% while both
 * sides were still asm: 0x283CC slps_00270, 0x284C8 sces_00269,
 * 0x6443C mainmenu_jp, 0x6509C mainmenu_eu, 0x4EE20 g3_jp, 0x4FAB8
 * g3_eu, 0x4C2BC g3org_jp, 0x4CF0C g3org_eu - all eight the 0x8c sdk
 * rows at the pinned LIBSND member addresses).
 *
 * LIBSND _SsUtBuildADSR (.text+0x5c): the exact inverse of the landed
 * _SsUtResolveADSR (.text+0x0, same member). Packs the per-field
 * halfword record the SsSv* synth family keeps back into the two SPU
 * ADSR attribute words: adsr1 = am-flag | (AR & 0x7F) << 8 |
 * (DR & 0xF) << 4 | SL & 0xF; adsr2 = sm-flag | keep?0x4000 |
 * (SR & 0x7F) << 6 | RR & 0x1F. The three flag fields (+0xA am,
 * +0xC sm, +0x10 keep) are read signed (lh) - Resolve stores the raw
 * 0x8000/0x4000 masks, and any nonzero value sets the bit; the five
 * rate fields are read unsigned (lhu).
 *
 * Source shapes that make GCC 2.6.3 reproduce the retail body:
 * 1. The flag tests compile branchless as sltu/negu/and with the
 *    sign-extended -0x8000 mask materialized once in $a0 and shared
 *    by both 0x8000 flags (gcc's ne-then-negate idiom under the sh
 *    truncation); the keep test stays a real beqz branch with the
 *    ori 0x4000 inside, and gcc's scheduler parks the am-flag and in
 *    that branch's delay slot exactly as retail.
 * 2. Frameless leaf: the adsr1 store lands mid-body, the adsr2 store
 *    rides the jr $ra delay slot, both exactly as retail.
 * 3. The rate fields pack SHIFT-THEN-MASK - the exact mirror of the
 *    Resolve expressions ((f >> s) & M <-> (f << s) & (M << s)):
 *    (x << 8) & 0x7F00 compiles sll-then-andi; the mask-first form
 *    ((x & 0x7F) << 8) flips the pair and misses by two words.
 */
void _SsUtBuildADSR(unsigned short *rec, unsigned short *adsr1,
                    unsigned short *adsr2)
{
    short am = ((short *)rec)[5];
    short sm = ((short *)rec)[6];
    short keep = ((short *)rec)[8];
    unsigned short a1, a2;

    a1 = (am != 0) ? 0x8000 : 0;
    a2 = (sm != 0) ? 0x8000 : 0;
    if (keep != 0)
        a2 |= 0x4000;
    a1 |= (rec[0] << 8) & 0x7F00;
    a1 |= (rec[1] << 4) & 0xF0;
    a1 |= rec[2] & 0xF;
    a2 |= (rec[3] << 6) & 0x1FC0;
    a2 |= rec[4] & 0x1F;
    *adsr1 = a1;
    *adsr2 = a2;
}
