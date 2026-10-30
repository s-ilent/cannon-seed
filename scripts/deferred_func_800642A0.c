/* Real-decompiled-C game function #14 (window 32, cron-20261030-0458).
 *
 * One g3_eu yaml row, 0x548 bytes, twenty spimdisasm pieces that are ONE
 * function: the game-side SPU reset/init driver (LIBSPU _spu_init family).
 * Every hardware touch runs through the _spu_RXX-style base pointer
 * D_800AB0B8 into the SPU register file at 0x1F801C00+0x180..: SPUCNT
 * (0x1AA/0xD5 in halfword units), SPUSTAT polling (0x1AE/0xD7), the
 * voice register block (24 x 0x10 stride), the DMA/transfer controls and
 * the psyq static _spu_inTransfer. Structure: OR 0xB0000 into the flag
 * word behind D_800AB0C8, SPUCNT=0, then NINE identical x3-multiplier
 * software-timeout spins (volatile locals i@0x10(sp) / x@0x14(sp); the
 * doubled body-end/test load pair is the cc1 2.6.3-PSX volatile-while
 * idiom, probe-verified), the SPUSTAT-&0x7FF wait with the 0x1389-count
 * retry that prints through D_800221C4 on overflow, the register sweep
 * (D_800AB0D8..E4 = 2/3/8/7, 0x1AC=4, volume masks 0x18C/8E=0xFFFF,
 * 0x188|=0xFFFF folding to the constant store while 0x18A|=0xFF keeps
 * the loaded value), and the arg-gated full init: the 24-voice table
 * sweep (vol 0 / pitch 0x3FFF / addr 0x200 pairs), func_800647E8, then
 * four more spins, 0x18C/8E |=, four final spins. Both arms converge on
 * the finish: _spu_inTransfer=1, SPUCNT=0xC000, D_800AB0EC/F0=0, return
 * 0 (v0=0 rides the incoming branch delay slots).
 *
 * cc-post: keep-epilogue
 */
extern long *D_800AB0C8[];
extern volatile unsigned short *D_800AB0B8[];
extern long D_800AB0B0[];
extern unsigned short D_800AB0B4[];
extern long D_800AB0D0[];
extern long D_800AB0D4[];
extern long D_800AB0D8[];
extern long D_800AB0DC[];
extern long D_800AB0E0[];
extern long D_800AB0E4[];
extern long D_800AB0EC[];
extern long D_800AB0F0[];
extern long D_800AB0F4[];
extern long _spu_inTransfer;
extern void func_800647E8();
extern int printf();
extern char D_800221C4[];
extern char D_800221D4[];

long func_800642A0(long arg)
{
    volatile int i;
    volatile int x;
    int j;

    *D_800AB0C8[0] |= 0xB0000;
    D_800AB0B8[0][0xC0] = 0;
    D_800AB0B8[0][0xC1] = 0;
    D_800AB0B8[0][0xD5] = 0;
    x = 13;
    i = 0;
    D_800AB0D0[0] = 0;
    D_800AB0D4[0] = 0;
    D_800AB0B4[0] = 0;
    while (i < 0xF0) {
        x = x * 3;
        i++;
    }
    D_800AB0B8[0][0xC0] = 0;
    D_800AB0B8[0][0xC1] = 0;
    D_800AB0B0[0] = 0;
    if (D_800AB0B8[0][0xD7] & 0x7FF) {
        do {
            if (++D_800AB0B0[0] >= 0x1389) {
                printf(D_800221C4, D_800221D4);
                break;
            }
        } while (D_800AB0B8[0][0xD7] & 0x7FF);
    }
    D_800AB0D8[0] = 2;
    D_800AB0DC[0] = 3;
    D_800AB0E0[0] = 8;
    D_800AB0E4[0] = 7;
    D_800AB0B8[0][0xD6] = 4;
    D_800AB0B8[0][0xC2] = 0;
    D_800AB0B8[0][0xC3] = 0;
    D_800AB0B8[0][0xC6] = 0xFFFF;
    D_800AB0B8[0][0xC7] = 0xFFFF;
    D_800AB0B8[0][0xCC] = 0;
    D_800AB0B8[0][0xCD] = 0;
    if (arg == 0) {
        D_800AB0B8[0][0xC8] = 0;
        D_800AB0B8[0][0xC9] = 0;
        D_800AB0B8[0][0xCA] = 0;
        D_800AB0B8[0][0xCB] = 0;
        D_800AB0B8[0][0xD8] = 0;
        D_800AB0B8[0][0xD9] = 0;
        D_800AB0B8[0][0xDA] = 0;
        D_800AB0B8[0][0xDB] = 0;
        D_800AB0B4[0] = 0x200;
        func_800647E8(D_800AB0F4, 0x10);
        for (j = 0; j < 0x18; j++) {
            D_800AB0B8[0][0] = 0;
            D_800AB0B8[0][1] = 0;
            D_800AB0B8[0][2] = 0x3FFF;
            D_800AB0B8[0][3] = 0x200;
            D_800AB0B8[0][4] = 0;
            D_800AB0B8[0][5] = 0;
            D_800AB0B8[0] += 8;
        }
        D_800AB0B8[0][0xC4] |= 0xFFFF;
        D_800AB0B8[0][0xC5] |= 0xFF;
        x = 13;
        i = 0;
        while (i < 0xF0) {
            x = x * 3;
            i++;
        }
        x = 13;
        i = 0;
        while (i < 0xF0) {
            x = x * 3;
            i++;
        }
        x = 13;
        i = 0;
        while (i < 0xF0) {
            x = x * 3;
            i++;
        }
        x = 13;
        i = 0;
        while (i < 0xF0) {
            x = x * 3;
            i++;
        }
        D_800AB0B8[0][0xC6] |= 0xFFFF;
        D_800AB0B8[0][0xC7] |= 0xFF;
        x = 13;
        i = 0;
        while (i < 0xF0) {
            x = x * 3;
            i++;
        }
        x = 13;
        i = 0;
        while (i < 0xF0) {
            x = x * 3;
            i++;
        }
        x = 13;
        i = 0;
        while (i < 0xF0) {
            x = x * 3;
            i++;
        }
        x = 13;
        i = 0;
        while (i < 0xF0) {
            x = x * 3;
            i++;
        }
    }
    D_800AB0B8[0][0xD5] = 0xC000;
    _spu_inTransfer = 1;
    D_800AB0EC[0] = 0;
    D_800AB0F0[0] = 0;
    return 0;
}
/*
 * ---- PARKING STATE (window 32, cron-20261030-0458) --------------------
 * Parked after three judge iterations; the row stays asm. Re-land by
 * copying this file back to src/func_800642A0.c, flipping the yaml row
 * [0x44AA0] to c, and deleting asm/g3_eu/nonmatchings/func_800642A0.s.
 *
 * BEST BUILD SO FAR (not this file's externs - see below): the v-local
 * variant with SCALAR externs
 *     extern long *D_800AB0C8;
 *     extern volatile unsigned short *volatile D_800AB0B8;
 *     ... v = D_800AB0B8; at each piece boundary ...
 * produced the retail frame exactly (.frame $sp,32, regs 2/0 = s0+ra,
 * i@0x10(sp), x@0x14(sp), arg->s0). Only TWO diff classes remained:
 *   1. gcc hoists the `li $2,13` (x = 13) ABOVE the three volatile sh's;
 *      retail emits it AFTER them (ori v0,0xD / sw / sw). Every tried
 *      shape hoists it - the open question is what barrier retail had.
 *   2. Consequence: the base pointer gets $6 instead of $2 and the whole
 *      stream shifts one slot (judge DIFF 276/332 words, all downstream).
 * VARIANTS TRIED (all worse):
 *   - array extern + volatile element (D_800AB0B8[0] element volatile):
 *     gcc caches the array base with `la $2` + saves it in s0 (frame 40).
 *   - array extern + non-volatile element: still frame 40, arg->s1.
 *   - direct indexing D_800AB0B8[0][i] everywhere: gcc refuses to CSE the
 *     pointer read across pointee-volatile stores - one fused reload per
 *     store, built 1596 B vs retail 1352.
 * CONFIRMED PRODUCIBLE (bank this window):
 *   - the DOUBLED LOAD loop bottom [lw][addiu][sw][lw][lw][slti][bnez] IS
 *     the cc1 2.6.3-PSX idiom for `while (i < 240) { x *= 3; i++; }` with
 *     VOLATILE i/x (probe scripts/probe_looptime.c p2/p4/p6/p7; p1/p3/p8
 *     address-taken forms register-cache x inside the loop - retail does
 *     not - so the locals ARE volatile).
 *   - `v[0xC4] |= 0xFFFF` on a volatile unsigned short lvalue folds to
 *     lhu (dead value kept) + ori $zero,0xFFFF + sh; `|= 0xFF` keeps the
 *     loaded value (ori v0,v0,0xFF). Matches retail 0x644D4/0x6464C.
 *   - bare-symbol loads (scalar externs, -G8 cc1 output) assemble through
 *     -G0 GNU as into the FUSED dest-reg pair (lui reg,%hi; lw reg,%lo(reg))
 *     - proven by the landed _spu_getInTransfer stub judge EXACT.
 * PROVENANCE: game-side copy of the psyq LIBSPU _spu_init family. psyq
 * 3.3 LIBSPU.LIB carries the SAME x3-timeout loop idiom WITH the same
 * doubled load (member near file offset 0xf10; symbol table lists
 * _spu_init/_spu_RXX/_spu_inTransfer/_spu_addrMode; debug strings
 * "wait (wrdy H -> L)" / "wait (dmaf clear/W)") - but NOT byte-identical
 * (different frame), so the game copy was compiled from source by the
 * game's own cc1 2.6.3-PSX. The openpsyq/libspu reference source would
 * settle the head's statement order.
 * NEXT PROBES: (a) split access paths - plain stores through a
 * non-volatile cast, volatile only at the poll/RMW sites; (b) declare
 * i/x WITHOUT volatile but force residency via their address escaping
 * into a noinline call placed BEFORE the first loop; (c) x = 13 written
 * as x += 13 with x pre-zeroed... cheap cc.sh -S probes, no judge needed
 * until the head's first 0x40 bytes match.
 * -----------------------------------------------------------------------
 */
