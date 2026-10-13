/* Matched 2026-10-13 through the round-trip oracle (g3org_jp).
 *
 * LIBETC INTR member .text+0x17c (extent 0x1c; sig-db sig matches
 * retail: lui+lw on the mask pointer, nop, lhu 0($v1) = old mask,
 * sh $a0,0($v1) = new mask, jr $ra + nop). Swaps the interrupt-mask
 * halfword behind `intr_mask_ptr` and returns the previous value.
 * Source-shape note: the two derefs carry volatile casts so the
 * compiler keeps the store ordered before the return jump (without
 * them the store is scheduled into the jr delay slot, one swap off
 * retail). See the CheckCallback unit and the mainmenu_jp curated
 * block for the full statics evidence.
 */
extern unsigned short *intr_mask_ptr;

long SetIntrMask(long mask)
{
    unsigned short old;

    old = *(volatile unsigned short *)intr_mask_ptr;
    *(volatile unsigned short *)intr_mask_ptr = mask;
    return old;
}
