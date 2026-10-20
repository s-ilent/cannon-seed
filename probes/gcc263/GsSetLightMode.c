/* cc-post: keep-epilogue
 *
 * GsSetLightMode offline draft - probes/gcc263, windows cron-20261020-0957
 * (34/35) and cron-20261020-1112 (35/35 CLOSED).
 * Reference: asm/g3org_jp/nonmatchings/func_80063FD4.s (35 words, true
 * VA 0x8005B284, file 0x3BA84). The function is pinned in SIX targets
 * (symbols.curated.txt LIBGS SCLIB placements: g3_jp 0x8005DDE8,
 * g3_eu 0x8005E44C, g3org_jp 0x8005B284, g3org_eu 0x8005B8A0,
 * mainmenu_jp 0x80072C18, mainmenu_eu 0x80073244) and none is landed.
 * The six-way word comparison (tools/lm_words.py, in-repo re-bank of
 * the eaten repo-external scratch) proves the 35 slots shape-identical
 * across all six copies: only 10 words differ and every one is
 * address-bearing. ONE source serves all six targets - a 6-row wave,
 * larger than NormalColor3's 4.
 *
 * Shape: the retail tree is gcc's equality-chain dispatch over the
 * four case values 0/1/2/3 - beq mode,1 first, then the slti v0,mode,2
 * range gate, the beqz mode zero test, an unconditional j to the error
 * leg, then the range leg re-tests 2 and 3 (the 3-test riding the ==2
 * branch's delay slot), the three out-of-line bodies zero/store/error
 * in that order, then the shared epilogue. A plain C switch does NOT
 * reproduce it (gcc 2.6.3 range-merges contiguous cases into
 * bltz/slti-4 tests); the goto-leg chain below in retail leg order
 * reproduces the tree, the delay-slot fills and the SDK/ASPSX epilogue
 * convention (frame release BEFORE the jump, nop in the branch delay)
 * carried by the cc-post: keep-epilogue marker per the banked
 * convention split.
 *
 * THE ENTRY COPY (former open item, CLOSED offline 2026-10-20): retail
 * opens with addu $a1,$a0,$zero and all five tests plus the store leg
 * read $a1. The answer is the SECOND printf argument. Retail's error
 * leg is jal printf with no $a1 setup at the call site (its delay slot
 * is a plain nop) - the string goes in $a0, so the mode value must
 * already BE in $a1: the source calls printf(str, mode). With one
 * argument gcc homes mode in $a0 (34/35 with every test reading $a0);
 * with the two-argument call, mode's live range conflicts with $a0
 * (printf's first-argument setup clobbers it), so local-alloc homes
 * mode in $a1 for the WHOLE range - the entry copy - and the call
 * site needs only the string into $a0. tools/lm_probe_diff.py (in-repo
 * re-bank; trims gas's 16-byte .text section padding and masks only
 * relocation-carrying fields) reports 35/35 slots on this file, first
 * shot. The remaining per-target variance is exactly the ten
 * address-bearing words the six-way proof lists.
 *
 * LANDING RECIPE (next oracle window): curated entries for the 6 mode
 * statics and 6 strings under shared alias names (per-target data
 * symbols below), src/GsSetLightMode.c from this draft, 6 yaml flips
 * asm->c with 6 stale .s deletions (asm/g3_jp func_80067128, g3_eu
 * func_800678BC, g3org_jp func_80063FD4, g3org_eu func_80064720,
 * mainmenu_jp func_8007F138, mainmenu_eu func_8007F894), judge x6,
 * verify, ratchets, census. printf is already curated (6 LIBC
 * placements). Judge is oracle-gated (baselines/<t>.bin vs
 * config/sha1/<t>.sha1): needs the discs back first.
 *
 * Per-target data symbols (all six statics + strings need curated
 * entries under shared alias names before the yaml flips):
 *   mode static: g3_jp D_80171D7C, g3_eu D_80171E9C, g3org_jp
 *   D_8017FA30, g3org_eu D_8017FB14, mainmenu_jp D_80194D6C,
 *   mainmenu_eu D_80194E80.
 *   printf string: g3_jp D_80021C34, g3_eu D_80021C14, g3org_jp
 *   D_8002256C, g3org_eu D_80022568, mainmenu_jp D_800231DC,
 *   mainmenu_eu D_80023190.
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
    printf(D_8002256C, mode);
}
