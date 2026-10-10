/* gp-relative small-data probe (2026-10-10) — companion to TOOLCHAIN.md.
 *
 * FINDINGS (all probe-confirmed with the pinned cc1 2.6.3 + maspsx +
 * mipsel as 2.31.1):
 *
 * 1. gp base: retail sets $gp = 0x8006322C via lui/addiu at 0x800304D4.
 *    Small offsets (0x3C, 0x68, 0xB4, 0xB8, 0xBC, 0xC0 seen so far) name
 *    a compact global area inside the payload data blob.
 *
 * 2. cc1 -G8 emits bare-symbol memory operands for extern globals
 *    (.extern SYM, size):  sw $0,D_80063268. The real Psy-Q aspsx relaxed
 *    those to gp-relative stores using the .extern size + -G threshold;
 *    maspsx only registers .comm/.sdata-defined symbols, so extern
 *    references pass through bare and GNU as would emit HI16/LO16
 *    (absolute) — which does NOT round-trip. build.sh's C staging
 *    rewrites them to %gp_rel(SYM)($gp); gen_ld.py emits _gp from the
 *    yaml gp_value so the linker resolves GPREL16 (S - _gp).
 *
 * 3. Store shapes (verified against retail):
 *      g = 0;                    -> sw/sh $0,SYM; j $31 (+delay nop)
 *      g = 1;                    -> ori $v0,$zero,1; sh/sw $v0,SYM; j $31
 *      __asm__ volatile("nop");  -> a real leading nop
 *    Retail func_80025AE0/func_8002A0DC are (nop; store; jr; nop) with
 *    the nop genuinely executed (live jal targets). No cc1 flag tested
 *    (-O0..-O3, -G8, volatile, -fvolatile) emits that leading nop for a
 *    plain store, so the matched C carries a volatile asm — OPEN.
 *
 * 4. Tail-jump overlap: the (=1) twins (ori; store; jr) sit immediately
 *    before the (=0) functions; their jr delay slot IS the next
 *    function's entry byte. maspsx always fills the delay slot, so those
 *    twins cannot be C-matched without overlapping objects — they stay
 *    attributed to the preceding data blocks until a hand-asm pass.
 */
extern unsigned int D_80063268;
extern volatile unsigned int V_UNUSED_80063268;

void probe_store_zero(void) { D_80063268 = 0; }
void probe_volatile_store(void) { V_UNUSED_80063268 = 0; }
