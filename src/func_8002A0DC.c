/* Matched 2026-10-10 through the round-trip oracle (slps_00270).
 * Retail body: nop; sh $zero,0x68($gp); jr $ra; nop(delay).
 *
 * The store target is the small-data area off the game's gp base
 * (0x8006322C, set at 0x800304D4): 0x68($gp) = 0x80063294, a halfword
 * object (lh users elsewhere confirm the 16-bit width). Compiled with
 * the pinned flags, now -G8 because retail demonstrably uses
 * gp-relative data addressing.
 *
 * OPEN QUESTION: the leading nop is real, executed code (retail jal's
 * this entry from two call sites in the 0x8002A8xx/0x8002ACxx region),
 * but no cc1 2.6.3 flag combination tested so far emits it for a plain
 * global store. It is reproduced with a volatile asm until a probe
 * explains it — see probes/gcc263/gp_probe.c and the worklog.
 */
extern unsigned short D_80063294;

void func_8002A0DC(void)
{
    __asm__ volatile("nop");
    D_80063294 = 0;
}
