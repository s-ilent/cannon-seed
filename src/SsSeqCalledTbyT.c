/* cc-post: sdk-aspsx
 *
 * LIBSND SSCALL member (extent 0x274) - the sequencer tick dispatcher,
 * landed as ONE source across the two targets whose full callee set is
 * byte-evidenced (slps_00270 at 0x80045538, g3org_jp at 0x80069428; the
 * sces/mainmenu_eu/g3_eu copies wait for the census verdict on their
 * crescendo/decrescendo call sites, whose bodies read 58 percent at
 * 0x60 depth against the psyq 3.3 archive - a different-vintage member
 * class). Decoded offline to a shape-exact 157/157 schedule against
 * ALL FIVE pinned walks (probes/gcc263/SsSeqCalledTbyT.c carries the
 * full story; tools/lm_probe_diff.py, exit 0).
 *
 * Shape law: DIRECT 2D indexing over the track table - seven
 * cursor-variable variants (a pp cursor advanced by the for, an inner
 * copy, a re-derived row address) all misallocate (gcc packs away the
 * fp save, recomputes the row address with sll, hoists the cursor init
 * above the entry blez, or duplicates the rotated inner guard); only
 * the direct tab[slot][i] form makes gcc's loop.c seed the inner-loop
 * giv copy from the outer address cursor by itself. The 0x01 play arm
 * NESTS the 0x10/0x20/0x40/0x80 arms (the beqz on 0x01 skips straight
 * to the 0x02 test, so the (short) conversions in s1 dominate those
 * four arms but the pause/replay arms re-materialize both arguments
 * fresh); the 0x04 stop arm passes the slot and track indices RAW (no
 * short conversion - different callee prototype) then clears the
 * flags word. Re-entry guard set to 1 before the scan and cleared on
 * every exit path; the argument-less init call's delay slot carries
 * slot = 0.
 *
 * Callees (each pinned per target in config/symbols.curated.txt,
 * window cron-20261022-2341): play/pause/replay resolve in every
 * target (curated x8); tempo/crescendo/decrescendo/stop evidenced by
 * 92 percent 0x60-depth body matches against the psyq 3.3 LIBSND.LIB
 * member bodies on each target's own baseline (slps: tempo 0x800497E8,
 * crescendo 0x80048E8C, decrescendo 0x800457AC, stop 0x80049408;
 * g3org_jp: tempo 0x8006D6D8, crescendo 0x8006CD7C, decrescendo
 * 0x8006969C, stop 0x8006D2F8). The stop call site passes raw slot and
 * track indices, and retail's crescendo/decrescendo sites set only two
 * argument registers, so those three declare 2-arg forms - the probe's
 * proven shapes.
 *
 * The head init call is GAME-SIDE (matches nothing in any psyq 3.3
 * archive): a shared alias per target, slps 0x80040C40, g3org_jp
 * 0x80064BCC.
 *
 * The five statics use shared alias names (curated per target, the
 * banked cross-target data-reference mechanism) because the five
 * copies' data lives at per-target addresses:
 *   guard:     slps 0x8011506C, g3org_jp 0x80178890
 *   slot count: slps 0x8011C2F4, g3org_jp 0x8017FAB8 (sits at the
 *              track count minus 4 in every target)
 *   track count: slps 0x8011C2F8, g3org_jp 0x8017FABC
 *   slotbits:  slps 0x80115518, g3org_jp 0x8017FA38
 *   track table: slps 0x8011C274, g3org_jp 0x80178C9C (array of
 *              pointers to 0xAC-stride records, flags word at +0x90)
 */
extern long SsSeqCalledTbyT_guard;
extern short SsSeqCalledTbyT_nslots;
extern short SsSeqCalledTbyT_ntracks;
extern long SsSeqCalledTbyT_slotbits;
extern void SsSeqCalledTbyT_init(void);
extern void Snd_play(short, short);
extern void Snd_pause(short, short);
extern void Snd_replay(short, short);
extern void Snd_crescendo(short, short);
extern void Snd_decrescendo(short, short);
extern void Snd_tempo(short, short);
extern void Snd_stop(long, long);

struct SsSeqTrack {
    char pad0[0x90];
    long flags;
    char pad1[0x18];
};

extern struct SsSeqTrack *SsSeqCalledTbyT_tab[];

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
                    Snd_crescendo((short)slot, (short)i);
                }
                if (SsSeqCalledTbyT_tab[slot][i].flags & 0x20) {
                    Snd_decrescendo((short)slot, (short)i);
                }
                if (SsSeqCalledTbyT_tab[slot][i].flags & 0x40) {
                    Snd_tempo((short)slot, (short)i);
                }
                if (SsSeqCalledTbyT_tab[slot][i].flags & 0x80) {
                    Snd_tempo((short)slot, (short)i);
                }
            }
            if (SsSeqCalledTbyT_tab[slot][i].flags & 0x02) {
                Snd_pause((short)slot, (short)i);
            }
            if (SsSeqCalledTbyT_tab[slot][i].flags & 0x08) {
                Snd_replay((short)slot, (short)i);
            }
            if (SsSeqCalledTbyT_tab[slot][i].flags & 0x04) {
                Snd_stop(slot, i);
                SsSeqCalledTbyT_tab[slot][i].flags = 0;
            }
        }
    }
    SsSeqCalledTbyT_guard = 0;
}
