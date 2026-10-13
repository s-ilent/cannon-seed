/* Matched 2026-10-13 through the round-trip oracle (g3org_jp).
 *
 * LIBETC INTR_DMA member memclr (extent 0x2c; sig-db sig matches retail
 * byte-for-byte - no relocations: addiu $sp,-8 / beqz $a1 with the
 * len-1 init in the delay slot / -1 sentinel in $v1 / sw + countdown
 * loop over whole words / addiu $sp,8 / jr $ra + nop). Clears `len`
 * whole words at `ptr`. The same source ships in three LIBETC members
 * (INTR / INTR_VB / INTR_DMA) - each target carries three
 * byte-identical copies; this is the curated `memclr` copy, the other
 * two stay func_-named asm. Source shape: the guard-free countdown
 * for-loop is what makes GCC 2.6.3 reproduce the retail body (loop
 * rotation rewrites the entry test into the beqz, the frame stays at
 * the retail 8 bytes). Full copy-census under target: mainmenu_jp in
 * symbols.curated.txt.
 */

void memclr(void *ptr, long len)
{
    long *p;
    long i;

    p = (long *)ptr;
    for (i = len - 1; i != -1; i--) {
        *p = 0;
        p++;
    }
}
