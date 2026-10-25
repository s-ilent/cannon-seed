/* Matched 2026-10-26 through the judge oracle (the pair-pool's second
 * harvest wave; byte-identical four-target set from the row-family-
 * normalized pair gate: file offsets 0x137A0 slps_00270, 0x13268
 * sces_00269, 0x2F2E8 g3_jp, 0x2EC24 g3_eu - all four the 0x18 sdk rows
 * at the pinned LIBGTE member addresses, each row the 0xc function plus
 * four zero words of row padding).
 *
 * LIBGTE SetDQB: the single argument lands in $4 and the whole body is
 * one move-to-GTE-control-register into register 28 (DQB, the depth-
 * queuing B parameter the AVSZ3/AVSZ4 average-Z commands consume),
 * followed by the stock frameless jr $ra with a nop delay slot. The
 * DQB sibling of the landed SetDQA (control 27).
 *
 * The move is banked as its exact retail .word 0x48C4E000: like SetDQA
 * this member's retail encoding carries the rs=6 cop2 form, while GNU
 * as's own ctc2 mnemonic carries rs=4 - the retail binary mixes both
 * provences across sdk members, so the mnemonic cannot reproduce this
 * one (the SetDQA .word precedent, byte for byte the same bank).
 *
 * psyq prototype: void SetDQB(short dqb); the value passes through the
 * argument register untouched, so the frame stays empty. The row's
 * trailing four zero words are the row extent's padding - ld's
 * inter-section zero fill reproduces them without instruction bytes.
 */
void SetDQB(long dqb)
{
    __asm__ volatile(
        ".word 0x48C4E000\n" /* move-to-gte-ctl $4 -> ctl 28 (DQB, rs=6 form) */
    );
}
