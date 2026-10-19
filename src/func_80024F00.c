/* Matched 2026-10-10 through the round-trip oracle (slps_00270).
 * Retail body: nop; sw $zero,0x3C($gp); jr $ra; nop(delay).
 *
 * The store target is the small-data area off the game's gp base
 * (0x8006322C, set at 0x800304D4): 0x3C($gp) = 0x80063268. Compiled
 * with the pinned flags, now -G8 because retail demonstrably uses
 * gp-relative data addressing.
 *
 * CLASSIFIED (2026-10-10, probe sweep): the leading nop is a source-level
 * hand-written asm construct, not compiler output. ~620 cc1/cc1plus
 * compilations (all -O0..-O3, -G0/4/8, every -f/-m flag the binary
 * supports, 12 source shapes incl. volatile/defined/static/K&R/unused-
 * param/TU-neighbour variants) emit the bare `sw/sh $0,SYM; j $31` shape
 * and never a leading nop. The same conclusion independently covers the
 * (=1) twins next door (jr delay slot overlapped by the next function's
 * entry — also cc1-impossible) and the GTE ctc2 stub spimdisasm marks
 * handwritten. The volatile asm below is therefore the settled, faithful
 * reproduction of a hand-asm stub.
 */
extern unsigned int boot_flag_0;

void func_80024F00(void)
{
    __asm__ volatile("nop");
    boot_flag_0 = 0;
}
