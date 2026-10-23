/* cc-post: sdk-aspsx
 *
 * SsSeqCalledTbyT offline draft - probes/gcc263, window cron-20261022-2341.
 * DECODE CLOSED at 157/157 shape-exact vs the slps_00270 walk in the SAME
 * window (tools/lm_probe_diff.py, exit 0; the only masked fields are the
 * jal targets and the %hi/%lo data immediates, exactly the per-target
 * deltas). Reference: asm/nonmatchings/func_8004AE48.s (slps walk, true
 * VA 0x80045538, file 0x25D38, extent 0x274, pinned member row). The
 * LIBSND SSCALL member is pinned in FIVE targets - slps 0x80045538,
 * sces 0x80045554, mainmenu_eu 0x80082128, g3_eu 0x8006CB44,
 * g3org_jp 0x80069428 (mainmenu_jp, g3_jp, g3org_eu copies carry no
 * name pin) - and none is landed: the fresh-decode lane item queued by
 * cron-20261022-2231, decoded here.
 *
 * Shape: a re-entry guard long static (== 1 -> plain return), the guard
 * set to 1, one argument-less init call whose delay slot carries
 * slot = 0, then TWO inverted loops over DIRECT 2D indexing
 * tab[slot][i] - THE shape law of this decode: seven cursor-variable
 * variants (a pp cursor advanced by the for, an inner q = pp copy,
 * &tab[slot] re-derivation) all MISallocate (gcc packs away the fp
 * save, or recomputes the address with sll, or hoists the cursor init
 * above the entry blez, or duplicates the rotated inner guard); the
 * direct 2D form makes gcc's loop.c seed the inner-loop giv copy from
 * the outer address cursor by itself - fp = &tab[slot] advancing +4 in
 * the outer back-edge delay, s2 = the seeded copy, s0 = the +0xAC byte
 * giv, s3 = the i<<16 giv feeding the (short)i conversions, s7/s4 =
 * the slot<<16 /(short)slot pair. Outer body: per-slot bit test
 * (slotbits & (1 << slot)), the short slot-count gate re-read from its
 * static (entry blez; the back-edge slt re-reads it after every
 * iteration - calls clobber memory). Inner: the flags word at +0x90 of
 * each 0xAC-stride record, re-read from memory before EVERY test. The
 * dispatch: 0x01 play, with 0x10/0x20/0x40/0x80 NESTED inside the 0x01
 * body (the beqz(0x1) skips straight to the 0x02 test - which is why
 * the (short)i conversion in s1 dominates those four arms but the
 * pause/replay arms re-materialize both args fresh), then 0x02 pause,
 * 0x08 replay, 0x04 the stop call with RAW slot/i (no short conversion
 * - different callee prototype) followed by flags = 0. Loop exits fall
 * into guard = 0 and the standard 0x48 frame epilogue (ra 0x44,
 * fp 0x40, s7..s0 0x3C..0x20, release BEFORE jr - cc-post: sdk-aspsx).
 *
 * LANDING RECIPE staged (next oracle window; all five walk units read):
 * per-target statics for the five shared aliases - guard / nslots /
 * ntracks / slotbits / tab:
 *   slps_00270:  D_8011506C / D_8011C2F4 / D_8011C2F8 / D_80115518 /
 *                D_8011C274
 *   sces_00269:  D_801145EC / D_8011C06C / D_8011C070 / D_80114A94 /
 *                D_8011B7EC
 *   mainmenu_eu: D_8018DC28 / D_80195738 / D_8019573C / D_80194EB8 /
 *                D_8018E070
 *   g3_eu:       D_8016AD04 / D_80172724 / D_80172728 / D_80171EA4 /
 *                D_8016B10C
 *   g3org_jp:    D_80178890 / D_8017FAB8 / D_8017FABC / D_8017FA38 /
 *                D_80178C9C
 * (nslots sits at ntracks-4 in every target; guard ref-count differs
 * 6 vs 4 across walks = the at-register store pairing, not a shape
 * delta.)
 * Callees: Snd_play / Snd_pause / Snd_replay resolve everywhere
 * (curated x8). The 0x40+0x80 arms call Snd_tempo - NAMED in sces
 * (0x8004946C? no: sces walk jal Snd_tempo) and mainmenu_eu, but the
 * slps / g3_eu / g3org_jp walks show woven names (func_800497E8 x2,
 * func_8006CEBC x2, func_8006D6D8 x2): the sdk census placed Snd_tempo
 * in only 5 targets - the SAME undercount class as the SCA pins - so
 * THREE Snd_tempo pins stage in (slps 0x800497E8, g3_eu = the
 * func_8006CEBC VA, g3org_jp = the func_8006D6D8 VA) under the sibling
 * law (same call sites, same arm structure as the five named copies).
 * The remaining four callees (the head init, the 0x10 arm, the 0x20
 * arm, the 0x04 stop arm) are unnamed in ALL FIVE walks (slps
 * func_80040C40 / func_80048E8C / func_800457AC / func_80049408; sces
 * func_80040930 / func_800490AC / func_80045AAC / func_8004946C;
 * mainmenu_eu func_8007D504 / func_80085C80 / func_80082680 /
 * func_80086040; g3_eu func_80067FBC / func_8007069C / func_8006D09C /
 * func_80070A5C; g3org_jp func_80064BCC / func_8006CD7C / func_8006969C /
 * func_8006D2F8) - they are NOT sdk_members placements, so the
 * landing needs either a sig-db extension against the psyq LIBSND
 * archive (SndPitch/SndVolume-class candidates for the 0x10/0x20 arms)
 * or the carve-name rename class for per-target function aliases.
 * CALLEE RESOLUTION (same window, scripts/sndcallee_hunt.py against the
 * psyq 3.3 LIBSND.LIB via sdk_members' LNK parser): the 0x10 arm body
 * IS the CRES member (61/64 words, 3 reloc diffs) exporting
 * Snd_crescendo; the 0x20 arm IS DECRE exporting Snd_decrescendo; the
 * 0x04 arm IS STOP (exports Snd_stop/SsSepStop/SsSeqStop - one body)
 * exporting Snd_stop; the head init matches NOTHING in any psyq 3.3
 * archive - it is GAME-SIDE, unnamed (rename-lane item). The retail
 * call sites set only a0/a1 for CRES/DECRE (the 3.3 header's third
 * long arg never materializes) and pass slot RAW for the stop call,
 * so the landing source declares the three as 2-arg (short,short) /
 * (long,long) forms - the probe's proven shapes. The landing now needs
 * ONLY the curated pins: Snd_tempo x3 (slps 0x800497E8, g3_eu
 * 0x8006CEBC, g3org_jp 0x8006D6D8), Snd_crescendo / Snd_decrescendo /
 * Snd_stop pins wherever the walks show woven jal names (the census
 * placed CRES x1 / DECRE x2 / STOP x0), the five shared-alias static
 * sets, and one resolve for the game-side init.
 * PER-TARGET PIN TABLE (scripts/stage_snd_pins.py, positional from the
 * walks' jal immediates, byte-verified 0x60-deep against the LIBSND.LIB
 * member bodies on each target's own baseline; the tempo40/80 sites hit
 * the CURATED Snd_tempo VAs exactly in sces/mainmenu_eu, which
 * validates the positional mapping):
 *   slps_00270:  tempo 0x800497E8 / crescendo 0x80048E8C /
 *                decrescendo 0x800457AC / stop 0x80049408   (all 92%)
 *   sces_00269:  tempo 0x800458CC (curated) / stop 0x8004946C (92%);
 *                crescendo 0x800490AC + decrescendo 0x80045AAC read
 *                58% at 0x60 depth - DIFFERENT-VINTAGE bodies, the pin
 *                verdict must come from the census, not this prefix
 *   mainmenu_eu: tempo 0x800824A0 (curated) / stop 0x80086040 (92%);
 *                crescendo 0x80085C80 + decrescendo 0x80082680 at 58%
 *                (same vintage question)
 *   g3_eu:       tempo 0x8006CEBC / stop 0x80070A5C (92% each);
 *                crescendo 0x8007069C + decrescendo 0x8006D09C at 58%
 *   g3org_jp:    tempo 0x8006D6D8 / crescendo 0x8006CD7C /
 *                decrescendo 0x8006969C / stop 0x8006D2F8   (all 92%)
 * The 58% sites sit where the walks' byte streams diverge mid-member
 * (the wrapper-2 inner-SCA vintage split class); the landing stages the
 * 92% pins immediately and hands the 58% rows to the census.
 * Probe-only names below; no yaml edit, no curation edit this window.
 */
extern long SsSeqCalledTbyT_guard;       /* slps D_8011506C */
extern short SsSeqCalledTbyT_nslots;     /* slps D_8011C2F4 */
extern short SsSeqCalledTbyT_ntracks;    /* slps D_8011C2F8 */
extern long SsSeqCalledTbyT_slotbits;    /* slps D_80115518 */
struct SsSeqTrack;

extern void SsSeqCalledTbyT_init(void);  /* slps func_80040C40 */
extern void Snd_play(short, short);      /* LIBSND PLAY member */
extern void Snd_pause(short, short);     /* LIBSND PAUSE member */
extern void Snd_replay(short, short);    /* LIBSND REPLAY member */
extern void SsSeqCalledTbyT_fn10(short, short);  /* slps func_80048E8C */
extern void SsSeqCalledTbyT_fn20(short, short);  /* slps func_800457AC */
extern void SsSeqCalledTbyT_fn40(short, short);  /* slps func_800497E8 */
extern void SsSeqCalledTbyT_fnstop(long, long);  /* slps func_80049408 */

struct SsSeqTrack {
    char pad0[0x90];
    long flags;
    char pad1[0x18];
};

extern struct SsSeqTrack *SsSeqCalledTbyT_tab[];  /* slps D_8011C274 */

void SsSeqCalledTbyT(void)
{
    long slot;
    long i;

    if (SsSeqCalledTbyT_guard == 1) {
        return;
    }
    SsSeqCalledTbyT_guard = 1;
    SsSeqCalledTbyT_init();
    for (slot = 0; slot < SsSeqCalledTbyT_nslots; slot++) {
        if (!(SsSeqCalledTbyT_slotbits & (1 << slot))) {
            continue;
        }
        for (i = 0; i < SsSeqCalledTbyT_ntracks; i++) {
            if (SsSeqCalledTbyT_tab[slot][i].flags & 0x01) {
                Snd_play((short)slot, (short)i);
                if (SsSeqCalledTbyT_tab[slot][i].flags & 0x10) {
                    SsSeqCalledTbyT_fn10((short)slot, (short)i);
                }
                if (SsSeqCalledTbyT_tab[slot][i].flags & 0x20) {
                    SsSeqCalledTbyT_fn20((short)slot, (short)i);
                }
                if (SsSeqCalledTbyT_tab[slot][i].flags & 0x40) {
                    SsSeqCalledTbyT_fn40((short)slot, (short)i);
                }
                if (SsSeqCalledTbyT_tab[slot][i].flags & 0x80) {
                    SsSeqCalledTbyT_fn40((short)slot, (short)i);
                }
            }
            if (SsSeqCalledTbyT_tab[slot][i].flags & 0x02) {
                Snd_pause((short)slot, (short)i);
            }
            if (SsSeqCalledTbyT_tab[slot][i].flags & 0x08) {
                Snd_replay((short)slot, (short)i);
            }
            if (SsSeqCalledTbyT_tab[slot][i].flags & 0x04) {
                SsSeqCalledTbyT_fnstop(slot, i);
                SsSeqCalledTbyT_tab[slot][i].flags = 0;
            }
        }
    }
    SsSeqCalledTbyT_guard = 0;
}
