/* cc-post: keep-epilogue
 * Real-decompiled-C game function #14 (window 32 decode, window 33 landing
 * attempt). One g3_eu yaml row, 0x548 bytes, twenty spimdisasm pieces that
 * are ONE function: the game-side SPU reset/init driver (LIBSPU _spu_init
 * family). Every hardware touch runs through the _spu_RXX-style base
 * pointer D_800AB0B8 into the SPU register file at 0x1F801C00+0x180..:
 * SPUCNT (0x1AA/0xD5 in halfword units), SPUSTAT polling (0x1AE/0xD7), the
 * voice register block (24 x 0x10 stride), the DMA/transfer controls and
 * the psyq static _spu_inTransfer. Structure: OR 0xB0000 into the flag
 * word behind D_800AB0C8, SPUCNT=0, then NINE identical x3-multiplier
 * software-timeout spins (volatile locals i@0x10(sp) / x@0x14(sp); the
 * doubled body-end/test load pair is the cc1 2.6.3-PSX volatile-while
 * idiom, probe-verified), the SPUSTAT-&0x7FF wait with the 0x1389-count
 * retry that prints through D_800221C4 on overflow, the register sweep
 * (D_800AB0D8..E4 = 2/3/8/7, 0x1AC=4, volume masks), the arg-gated full
 * init: the 24-voice table sweep (vol 0 / pitch 0x3FFF / addr 0x200 pairs),
 * func_800647E8, then four spins, 0x18C/8E |=, four final spins. Both arms
 * converge on the finish: _spu_inTransfer=1, SPUCNT=0xC000, D_800AB0EC/F0=0,
 * return 0 (v0=0 rides the incoming branch delay slots).
 *
 * PROVENANCE: game-side copy of the psyq LIBSPU _spu_init family. psyq 3.3
 * LIBSPU.LIB carries the SAME x3-timeout loop idiom WITH the same doubled
 * load (member near file offset 0xf10) but is NOT byte-identical (different
 * frame), so the game copy was compiled from source by the game's own cc1
 * 2.6.3-PSX. scripts/libspu_probe.py banks the archive scan.
 *
 * SHAPE LAWS (window 32 probes + window 33 head probes):
 * - volatile int i/x locals reproduce the doubled load loop bottom;
 *   address-taken non-volatile forms register-cache x (wrong).
 * - `v[0xC4] |= 0xFFFF` on a volatile unsigned short lvalue folds to
 *   lhu (dead value kept) + ori $zero,0xFFFF + sh; `|= 0xFF` keeps the
 *   loaded value (ori v0,v0,0xFF). Matches retail 0x644D4/0x6464C.
 * - scalar externs under -G8 assemble through -G0 GNU as into the fused
 *   dest-reg pair (lui reg,%hi; lw reg,%lo(reg)) - the landed
 *   _spu_getInTransfer stub judged EXACT through this form.
 * - THE HEAD BARRIER: gcc hoists the pure `li $2,13` (x = 13) above the
 *   three volatile sh's; retail keeps it after them. A memory-clobber
 *   barrier asm between the sh's and x = 13 pins the li in place while
 *   emitting zero bytes (probe h3, scripts/probe_li13.c). The base
 *   pointer then reuses $2 for the ori exactly as retail.
 * - the base pointer is re-read (v = D_800AB0B8) at every retail reload
 *   site: head, wait entry, wait bottom, register sweep, voice loop,
 *   post-loop RMWs, C6/C7 RMW, finish. The pointer VARIABLE is volatile
 *   (every read a volatile load), the cache local is not.
 */
extern long *D_800AB0C8;
extern volatile unsigned short *volatile D_800AB0B8;
extern long D_800AB0B0;
extern unsigned short D_800AB0B4;
extern long D_800AB0D0;
extern long D_800AB0D4;
extern long D_800AB0D8;
extern long D_800AB0DC;
extern long D_800AB0E0;
extern long D_800AB0E4;
extern volatile long D_800AB0EC;
extern volatile long D_800AB0F0;
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
    unsigned short *v;
    int j;
    int poll;

    *D_800AB0C8 |= 0xB0000;
    {
        /* the head's base pointer rides $2 (v0) in retail - the same reg
         * the x = 13 constant reuses after the last sh; a block-scoped
         * register var pins the allocation (the banked register-var idiom)
         * and the memory barrier below keeps the li from hoisting. */
        register volatile unsigned short *vp asm("$2");
        vp = D_800AB0B8;
        vp[0xC0] = 0;
        vp[0xC1] = 0;
        vp[0xD5] = 0;
    }
    __asm__ __volatile__("" ::: "memory");
    x = 13;
    i = 0;
    D_800AB0D0 = 0;
    D_800AB0D4 = 0;
    D_800AB0B4 = 0;
    while (i < 0xF0) {
        x = x * 3;
        i++;
    }
    {
        register volatile unsigned short *vp asm("$2");
        vp = D_800AB0B8;
        vp[0xC0] = 0;
        vp[0xC1] = 0;
        poll = vp[0xD7];
    }
    D_800AB0B0 = 0;
    if (poll & 0x7FF) {
        do {
            if ((D_800AB0B0 += 1) >= 0x1389) {
                printf(D_800221C4, D_800221D4);
                break;
            }
            {
                register volatile unsigned short *vp asm("$2");
                vp = D_800AB0B8;
                poll = vp[0xD7];
            }
        } while (poll & 0x7FF);
    }
    {
        register volatile unsigned short *vp asm("$3");
        vp = D_800AB0B8;
        D_800AB0D8 = 2;
        D_800AB0DC = 3;
        D_800AB0E0 = 8;
        D_800AB0E4 = 7;
        vp[0xD6] = 4;
        vp[0xC2] = 0;
        vp[0xC3] = 0;
        vp[0xC6] = 0xFFFF;
        vp[0xC7] = 0xFFFF;
        vp[0xCC] = 0;
        vp[0xCD] = 0;
        if (arg == 0) {
            vp[0xC8] = 0;
            vp[0xC9] = 0;
            vp[0xCA] = 0;
            vp[0xCB] = 0;
            vp[0xD8] = 0;
            vp[0xD9] = 0;
            vp[0xDA] = 0;
            vp[0xDB] = 0;
            D_800AB0B4 = 0x200;
        }
    }
    if (arg == 0) {
        func_800647E8(D_800AB0F4, 0x10);
        {
            register volatile unsigned short *vp asm("$3");
            vp = D_800AB0B8;
            for (j = 0; j < 0x18; j++) {
                vp[0] = 0;
                vp[1] = 0;
                vp[2] = 0x3FFF;
                vp[3] = 0x200;
                vp[4] = 0;
                vp[5] = 0;
                vp += 8;
            }
        }
        {
            register volatile unsigned short *vp asm("$3");
            vp = D_800AB0B8;
            vp[0xC4] |= 0xFFFF;
            vp[0xC5] |= 0xFF;
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
        x = 13;
        i = 0;
        while (i < 0xF0) {
            x = x * 3;
            i++;
        }
        {
            register volatile unsigned short *vp asm("$3");
            vp = D_800AB0B8;
            vp[0xC6] |= 0xFFFF;
            vp[0xC7] |= 0xFF;
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
        x = 13;
        i = 0;
        while (i < 0xF0) {
            x = x * 3;
            i++;
        }
    }
    {
        register volatile unsigned short *vp asm("$4");
        vp = D_800AB0B8;
        _spu_inTransfer = 1;
        vp[0xD5] = 0xC000;
    }
    D_800AB0EC = 0;
    D_800AB0F0 = 0;
    return 0;
}
