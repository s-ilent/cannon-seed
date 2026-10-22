/* Matched 2026-10-22 through the sibling probe (slps_00270).
 *
 * LIBETC INTR_VB member .text+0xd4 (extent 0x2c; sdk_members.py
 * unique placement, sig-db 3.3 sig matches the retail body
 * byte-for-byte with only the member-.data-base immediates
 * wildcarded). Registers an interrupt-class VBlank callback: computes
 * the slot address (intr_vb_cb_slots + idx*4), and stores the
 * callback ONLY if it differs from the current slot content (the
 * beq-to-return skip).
 *
 * The body landed for all six game modules (2026-10-14); the sibling
 * probe measured slps_00270's retail body two words off each landed
 * copy (dw=2 @0x0+0x4) and the dump pins both words to the
 * per-target slot-array address carried by the member's own lui/addiu
 * pair: slps 0x8004E360, where the retail payload carries the
 * member's own .data layout (eight zero slots then the hardware
 * constants 0x1F801114/0x1F801814/0x1F801110 at +0x20..). Words
 * 0x8..0x2c are byte-identical to every landed copy. The shared
 * source resolves intr_vb_cb_slots per-target at link, so the flip is
 * first-shot by construction. Full evidence chain under target:
 * mainmenu_jp (INTR_VB.OBJ .text 0x12c bytes: startIntrVSync +0x0,
 * trapIntrVSync +0x58, setIntrVSync +0xd4, memclr +0x100; the
 * member's own relocations resolve the lui/addiu to its .data+0).
 *
 * Source shape: plain scalar extern array, unsized (no opaque call
 * sits between the slot read and the conditional store, so CSE keeps
 * the $a0 base register exactly as retail does). Probe
 * (scripts/sivsync/): `if (cb != tbl[idx]) tbl[idx] = cb;` with
 * idx:int / cb:long reproduces the retail register plan (base=$v0,
 * slot addr=$a0, cb=$a1) and instruction order 1:1, including GCC's
 * own load-delay nop after the slot read. No cc-post marker:
 * frameless, call-free, no bare-symbol operands.
 */
extern long intr_vb_cb_slots[];

void setIntrVSync(int idx, long cb)
{
    if (cb != intr_vb_cb_slots[idx])
        intr_vb_cb_slots[idx] = cb;
}
