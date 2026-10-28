/* Matched 2026-10-29 through the invariant census (slps_00270).
 *
 * LIBETC INTR-family memclr (static copy) at slps_00270 vram 0x8002F64C
 * (yaml rom 0xFE4C, extent 0x2c) - one of the two copies the 2026-10-24
 * family landing left on this target (the curated INTR_DMA-member copy
 * src/func_80031940.c is the third; the three retail bodies are
 * byte-identical). Census verdict: word-eq 11/11, votes 7 against the
 * landed anchor body; the build image bytes at the row were re-checked
 * equal to the anchor's before the flip. Lands under this row's own
 * name per the family's one-src-unit-per-row precedent (a one-target
 * duplicate flip to the anchor has no precedent).
 *
 * Source shape (see src/func_80031940.c for the full decode note): the
 * guard-free countdown for-loop is what makes GCC 2.6.3 reproduce the
 * retail body (loop rotation rewrites the entry test into the beqz,
 * the frame stays at the retail 8 bytes). Clears `len` whole words at
 * `ptr`. No relocations, no statics - build-inert by construction.
 */

void func_80031B1C(void *ptr, long len)
{
    long *p;
    long i;

    p = (long *)ptr;
    for (i = len - 1; i != -1; i--) {
        *p = 0;
        p++;
    }
}
