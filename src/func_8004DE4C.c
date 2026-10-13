/* Matched 2026-10-14 through the round-trip oracle (g3org_eu).
 *
 * LIBETC INTR_VB member .text+0xd4 (extent 0x2c; curated `setIntrVSync`,
 * sdk_members.py unique placement, sig-db 3.3 sig matches the retail body
 * byte-for-byte with only the member-.data-base immediates wildcarded).
 * Registers an interrupt-class VBlank callback: computes the slot address
 * (intr_vb_cb_slots + idx*4) and stores the callback ONLY if it differs
 * from the current slot content (the beq-to-return skip).
 *
 * Evidence chain (full block under target: mainmenu_jp):
 * - psyq/3.3 LIBETC.LIB INTR_VB.OBJ: startIntrVSync +0x0, trapIntrVSync
 *   +0x58, setIntrVSync +0xd4, memclr +0x100; the member's own
 *   relocations resolve setIntrVSync's lui/addiu pair to its own
 *   .data+0 - the 8-word callback slot array (member .data 0x28 bytes:
 *   8 zero slots, exported Vcount +0x20, I_MASK constant 0x1F801114
 *   +0x24). startIntrVSync passes the same base as $a0 and writes
 *   0x107 through the +0x24 pointer; trapIntrVSync dispatches through
 *   the slots; g3_eu's bodies reference the D-names at 0x80097CCC/CEC/CF0 - the same
 *   +0x00/+0x20/+0x24 layout.
 * - Body fingerprint (scripts/setintrvsync_fp.py): all eight targets
 *   carry the byte-identical 11-word body; per-target slot-array
 *   addresses are the materialized lui/addiu immediates.
 *
 * Source shape: plain scalar extern array, unsized - no opaque call
 * sits between the slot read and the conditional store, so CSE keeps
 * the $a0 base register exactly as retail does (probe:
 * scripts/sivsync/; register plan base=$v0, slot addr=$a0, cb=$a1,
 * GCC's own load-delay nop after the slot read). No cc-post marker:
 * frameless, call-free, no bare-symbol operands.
 */

extern long intr_vb_cb_slots[];

void setIntrVSync(int idx, long cb)
{
    if (cb != intr_vb_cb_slots[idx])
        intr_vb_cb_slots[idx] = cb;
}
