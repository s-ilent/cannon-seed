/* Matched 2026-10-10 through the round-trip oracle (slps_00270).
 * Retail body: nop; sh $zero,0x68($gp); jr $ra; nop(delay).
 *
 * The store target is the small-data area off the game's gp base
 * (0x8006322C, set at 0x800304D4): 0x68($gp) = 0x80063294, a halfword
 * object (lh users elsewhere confirm the 16-bit width). Compiled with
 * the pinned flags, now -G8 because retail demonstrably uses
 * gp-relative data addressing.
 *
 * CLASSIFIED (2026-10-10, probe sweep): the leading nop is a source-level
 * hand-written asm construct, not compiler output — see the (=0) store
 * leaf's header for the sweep summary (no cc1/cc1plus flag or source
 * shape emits an entry nop). The volatile asm below is therefore
 * the settled, faithful reproduction of a hand-asm stub.
 */
extern unsigned short D_80063294;

void func_8002A0DC(void)
{
    __asm__ volatile("nop");
    D_80063294 = 0;
}
