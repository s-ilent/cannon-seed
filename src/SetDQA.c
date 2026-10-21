/* Matched 2026-10-21 through the judge oracle (byte-identical five-target
 * wave from the in-repo near-twin census: file offsets 0x13794
 * slps_00270, 0x1325C sces_00269, 0x2F2DC g3_jp, 0x2EC18 g3_eu, 0x2C778
 * g3org_jp - all five the 0xc sdk rows at the pinned LIBGTE member
 * addresses).
 *
 * LIBGTE SetDQA: the single argument lands in $4 and the whole body is
 * one move-to-GTE-data-register into register 27 (DQA), followed by the
 * stock frameless jr $ra with a nop delay slot.
 *
 * The move is banked as its exact retail .word 0x48C4D800: this member's
 * retail encoding carries the rs=6 cop2 form, while the landed AverageZ3
 * /AverageZ4 members and GNU as's own mtc2 mnemonic carry rs=4 - the
 * retail binary mixes both provences across sdk members, so the mnemonic
 * cannot reproduce this one (the avsz3 .word precedent).
 *
 * psyq prototype: void SetDQA(short dqa); the value passes through the
 * argument register untouched, so the frame stays empty.
 */
void SetDQA(long dqa)
{
    __asm__ volatile(
        ".word 0x48C4D800\n" /* move-to-gte-data $4 -> reg 27 (rs=6 form) */
    );
}
