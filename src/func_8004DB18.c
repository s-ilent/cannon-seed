/* Matched 2026-10-13 through the round-trip oracle (g3org_jp).
 *
 * LIBETC INTR member .text+0x164 (extent 0x18; sig-db sig matches
 * retail: lui+lw on the mask pointer, nop, lhu 0($v0), jr $ra + nop).
 * Returns the interrupt-mask halfword through the member's pointer
 * static `intr_mask_ptr` (the deref'd halfword is the mask consumed
 * by Get/SetIntrMask and the trapIntr/setIntr/stopIntr/restartIntr
 * machinery). See the CheckCallback unit and the mainmenu_jp curated
 * block for the full statics evidence; the pointer resolves extern.
 */
extern unsigned short *intr_mask_ptr;

long GetIntrMask(void)
{
    return *intr_mask_ptr;
}
