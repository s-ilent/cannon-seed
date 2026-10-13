/* Matched 2026-10-13 through the round-trip oracle (sces_00269;
 * body shape = the g3_eu match, 44-slot fingerprint). The unit file is
 * named src/stopIntr.c: slps_00270's SetIntrMask lives at the SAME
 * vram 0x80030FEC (the boot EXEs load identically), and a shared yaml
 * label maps both rows to one src file - so this row carries the real
 * member name instead (memclr precedent for name-labeled sdk member
 * rows).
 *
 * LIBETC INTR member .text+0x5b0 (extent 0xb0; sdk_members.py unique
 * placement, sig-db sig agrees). Shuts the interrupt subsystem down:
 * gate on the active flag at the INTR state base, run the shutdown
 * cluster (intr_stop_begin/intr_stop_commit - real code the scanner
 * mis-typed as data inside data_8004A828), save the mask halfword and
 * the DMA DICR word, zero the I_MASK port (re-reading it through the
 * intr_imask_ptr slot), clear the per-channel+master DICR enables
 * (AND 0x77777777), clear the gate, and return the gate's address
 * (0 on the early-exit path). The slot initial values are arbitrary
 * linker leftovers - retail never calls this subsystem. Full statics
 * evidence in the mainmenu_jp curated block.
 *
 * Source shapes that make GCC 2.6.3 reproduce the retail body (each
 * one probed byte-level against the retail stream, see the
 * cron-20261013-1356 worklog):
 * 1. THE S0 PIN. Retail keeps &intr_active_flag in $s0 across BOTH
 *    opaque calls (entry read 0($s0), exit `move $v0,$s0` serving the
 *    clear AND the return). A scalar extern (single-set pseudo set to
 *    a symbol+offset constant) is REMATERIALIZED by cc1/reload after
 *    the last call - four plain shapes and all of -O0..-O3 remat.
 *    Declaring the static as an unsized ARRAY and taking the address
 *    by array decay (`&intr_active_flag[0]`) defeats the single-set
 *    REG_EQUIV remat: $s0 is allocated in the prologue and survives.
 * 2. LOCAL PORT-POINTER COPIES. The port pointers must be read into
 *    locals ONCE (`mp`, `dp`, `ip`); inline re-references of the slot
 *    statics re-load from memory after any store (GCC 2.x flushes its
 *    memory-CSE table at stores), while retail reuses the registers.
 *    With locals the allocation lands exactly on retail: mp=$v0,
 *    dp=$a0, values=$v1, ip reuses dp's $a0.
 * 3. VOLATILE-QUALIFIED POINTER SLOTS (`void *volatile`): volatile
 *    slot reads stay in program position (the imask slot load is NOT
 *    hoisted to the top like plain loads) and the dicr slot is
 *    re-read at the AND 0x77777777 read-modify-write exactly as
 *    retail does. The port memory itself is dereferenced through
 *    volatile casts, which keeps the re-read (no store/load
 *    forwarding) and keeps the DICR store out of the commit call's
 *    delay slot.
 * 4. SDK/ASPSX CONVENTIONS (`cc-post: sdk-aspsx` marker, this
 *    file): retail keeps GCC's own epilogue order (frame release
 *    before `j $ra`, nop in the branch delay) - the ASPSX
 *    .set-reorder convention of Sony's library build - while the
 *    game-compiled units carry the swapped branch-delay form that
 *    cc_post's rule 1 reproduces. stopIntr is the first SDK member
 *    whose frame saves a callee-saved register AND makes calls, which
 *    is why the split only surfaces here.
 */

extern unsigned short intr_active_flag[]; /* the gate halfword, viewed
    as an unsized array for the decay pin - see shape note 1 */
extern unsigned short intr_saved_mask;
extern long intr_saved_dicr;
extern void *volatile intr_mask_ptr;
extern void *volatile intr_imask_ptr;
extern void *volatile intr_dicr_ptr;
extern void intr_stop_begin(void);
extern void intr_stop_commit(void);

long stopIntr(void)
{
    unsigned short *p = &intr_active_flag[0];
    void *mp;
    void *dp;
    void *ip;

    if (*p == 0)
        return 0;
    intr_stop_begin();
    mp = intr_mask_ptr;
    dp = intr_dicr_ptr;
    intr_saved_mask = *(unsigned short *)mp;
    intr_saved_dicr = *(long *)dp;
    ip = intr_imask_ptr;
    *(volatile unsigned short *)mp = 0;
    *(volatile unsigned short *)ip = *(volatile unsigned short *)mp;
    *(volatile long *)intr_dicr_ptr &= 0x77777777;
    intr_stop_commit();
    *p = 0;
    return (long)p;
}
