/* cc-post: keep-epilogue
 *
 * GsSetLightMode offline draft - probes/gcc263, window cron-20261020-0957.
 * Reference: asm/g3org_jp/nonmatchings/func_80063FD4.s (35 words, true
 * VA 0x8005B284, file 0x3BA84). The function is pinned in SIX targets
 * (symbols.curated.txt LIBGS SCLIB placements: g3_jp 0x8005DDE8,
 * g3_eu 0x8005E44C, g3org_jp 0x8005B284, g3org_eu 0x8005B8A0,
 * mainmenu_jp 0x80072C18, mainmenu_eu 0x80073244) and none is landed.
 * The six-way word comparison (scripts/lm_words.py, repo-external)
 * proves the 35 slots shape-identical across all six copies: only 10
 * words differ and every one is address-bearing (4 internal j targets,
 * 4 mode-static %hi/%lo pairs, 2 string %hi/%lo, 1 jal printf). ONE
 * source serves all six targets - a 6-row wave, larger than
 * NormalColor3's 4.
 *
 * Shape: the retail tree is gcc's equality-chain dispatch over the
 * four case values 0/1/2/3 - beq mode,1 first, then the slti v0,mode,2
 * range gate, the beqz mode zero test, an unconditional j to the error
 * leg, then the range leg re-tests 2 and 3 (the 3-test riding the ==2
 * branch's delay slot), the three out-of-line bodies zero/store/error
 * in that order, then the shared epilogue. A plain C switch does NOT
 * reproduce it (gcc 2.6.3 range-merges contiguous cases into
 * bltz/slti-4 tests); the goto-leg chain below in retail leg order
 * reproduces 34 of the 35 slots exactly (masked compare on the
 * address-bearing fields, scripts/lm_probe_diff.py): the epilogue is
 * the SDK/ASPSX convention (frame release BEFORE the jump, nop in the
 * branch delay) carried by the cc-post: keep-epilogue marker per the
 * banked convention split.
 *
 * OPEN ITEM (one instruction): retail opens with addu $a1,$a0,$zero -
 * an entry copy of the mode parameter into $a1, which ALL five tests
 * and the store leg then read. No source form probed reproduces it yet
 * (K&R parameter definition, long m = mode locals - gcc coalesces both;
 * the plain switch restructures the whole tree). At landing: judge
 * iteration starting from this draft; the copy is a single instruction
 * with known fields.
 *
 * Per-target data symbols (all six statics + strings need curated
 * entries under shared alias names before the yaml flips):
 *   mode static: g3_jp D_80171D7C, g3_eu D_80171E9C, g3org_jp
 *   D_8017FA30, g3org_eu D_8017FB14, mainmenu_jp D_80194D6C,
 *   mainmenu_eu D_80194E80.
 *   printf string: g3_jp D_80021C34, g3_eu D_80021C14, g3org_jp
 *   D_8002256C, g3org_eu D_80022568, mainmenu_jp D_800231DC,
 *   mainmenu_eu D_80023190.
 * printf itself is already curated (6 LIBC placements).
 */
extern int D_8017FA30;
extern char D_8002256C[];
extern int printf(const char *, ...);

void GsSetLightMode(long mode)
{
    if (mode == 1) goto store;
    if (mode >= 2) goto range;
    if (mode == 0) goto zero;
    goto err;
range:
    if (mode == 2) goto store;
    if (mode == 3) goto store;
    goto err;
zero:
    D_8017FA30 = 0;
    return;
store:
    D_8017FA30 = mode;
    return;
err:
    printf(D_8002256C);
}
