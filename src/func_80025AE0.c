/* Matched 2026-10-10 through the round-trip oracle (slps_00270).
 * Retail body: nop; sw $zero,0x3C($gp); jr $ra; nop(delay).
 *
 * The store target is the small-data area off the game's gp base
 * (0x8006322C, set at 0x800304D4): 0x3C($gp) = 0x80063268. Compiled
 * with the pinned flags, now -G8 because retail demonstrably uses
 * gp-relative data addressing.
 *
 * OPEN QUESTION: the leading nop is real, executed code (retail jal's
 * this entry from the caller at 0x80026300), but no cc1 2.6.3 flag
 * combination tested so far emits it for a plain global store. It is
 * reproduced with a volatile asm until a probe explains it — see
 * probes/gcc263/gp_probe.c and the worklog.
 */
extern unsigned int D_80063268;

void func_80025AE0(void)
{
    __asm__ volatile("nop");
    D_80063268 = 0;
}
