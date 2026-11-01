/* cc-post: keep-epilogue
 *
 * Real-decompiled-C game function #16 - the func_8006AC04 row (g3_eu,
 * listed 0x120, REAL extent 0x14C) lands as the psyq 3.3 LIBSND SSINIT
 * SsInit / SsInitHot SHARED BODY. Decode banked cron-20261031-1525
 * (scripts/deferred_func_8006AC04.c); landed on the witnessed oracle,
 * judge EXACT 332/332, whole-image 8/8 GREEN. THE TAIL FINDING made the
 * landing possible: spimdisasm had misclassified the last 0x2C bytes as
 * data - the "dlabel D_8006AD24" is the function's own tail (jal
 * GetVideoMode sealing the PAL/NTSC selector D_800ABA44 + the
 * SsSeqCalledTbyT_guard clear + the epilogue mirroring the row prologue);
 * the split fix folded it back (yaml extent 0x120 -> 0x14C, the data row
 * deleted, the row ends jr $ra).
 * Identity chain: flag 0 -> func_8006B6A0 -> func_800642A0(0) FULL (the
 * landed SPU reset/init driver), flag 1 -> func_8006B680 -> hot; callers
 * func_8006AD50 (SsInit, boot path) / func_8006AD70 (SsInitHot) both
 * landed. SsSetTableSize (func_8006AD90) stays HELD for the psylib lane.
 * Source-shape laws banked by the seven-round probe ladder:
 *  - counter inits precede the base materialization in program order
 *    (retail move $a0,0 BEFORE lui/addiu $a3 in all three loops);
 *  - the inner loop head is the comma-init counter-then-cursor order
 *    (`for (r = 0, src = vsrc; ...)` = retail move a1,0; move v1,a3, the
 *    outer bnez target lands on the counter init);
 *  - the loop-invariant base goes through the OPAQUE ASM DEFINITION
 *    (__asm__("" : "=r"(vsrc) : "0"(D_800ABA08))): a plain constant
 *    rematerializes and CSE-hoists its lui/addiu pair to the preheader
 *    HEAD (above the counter init, 3 words off); the asm definition pins
 *    the pair after move $a0 and holds the base in $a3 with the cursor
 *    re-derived per outer row (retail addu $v1,$a3,$zero);
 *  - per-loop register-var pins (the banked func_800642A0 idiom): voice
 *    loop outer $4 / inner $5 / cursor $3; control loop counter $4 /
 *    cursor $3; zero loop outer $5 / inner $4 / walk $2 / base $3;
 *  - the zero-loop outer counter carries an input-only opaque asm (no
 *    code) so gcc cannot down-convert the trip-20 loop (retail keeps the
 *    up-count slti 0x20 form);
 *  - the descending inner zero loop is the pre-decrement do-while
 *    (`while (--i >= 0)`, 16 stores - the post-decrement form
 *    over-stores 17);
 *  - D_80171E08 declared long (retail sw, not sh); the -1 for
 *    D_800ABA3C rides $v0 across the slotbits/ABA38 stores (pure
 *    scheduling from source order).
 */
extern long D_800ABA38[];
extern long D_800ABA3C[];
extern long D_800ABA40[];
extern long D_800ABA44[];
extern long D_800ABA48[];
extern long D_80171E08[];
extern unsigned short D_800ABA08[];
extern unsigned short D_800ABA18[];
extern long SsSeqCalledTbyT_tab[];
extern long SsSeqCalledTbyT_slotbits;
extern long SsSeqCalledTbyT_guard;
extern long GetVideoMode(void);
extern void ResetCallback(void);
extern void func_8006B6A0(void);
extern void func_8006B680(void);
extern void func_80067690(long);

void func_8006AC04(long flag)
{
    unsigned short *dst;
    unsigned short *vsrc;
    long *base;

    ResetCallback();
    if (flag == 0)
        func_8006B6A0();
    else
        func_8006B680();

    dst = (unsigned short *)0x1F801C00;
    vsrc = D_800ABA08;
    {
        register long i asm("$4");
        register long r asm("$5");
        register unsigned short *src asm("$3");
        i = 0;
        __asm__("" : : "r"(i));
        __asm__("" : "=r"(vsrc) : "0"(D_800ABA08));
        for (; i < 0x18; i++) {
            for (r = 0, src = vsrc; r < 8; r++)
                *dst++ = *src++;
        }
    }

    dst = (unsigned short *)0x1F801D80;
    {
        register long i asm("$4");
        register unsigned short *src asm("$3");
        i = 0;
        src = D_800ABA18;
        for (; i < 0x10; i++)
            *dst++ = *src++;
    }

    func_80067690(0x18);

    base = SsSeqCalledTbyT_tab + 0x20;
    {
        register long r asm("$5");
        register long i asm("$4");
        register long *p asm("$2");
        register long *b asm("$3");
        r = 0;
        b = base;
        for (; r < 0x20; r++) {
            __asm__("" : : "r"(r));
            i = 0xF;
            p = b + 0xF;
            do {
                *p = 0;
                p--;
            } while (--i >= 0);
            b += 0x10;
        }
    }

    D_80171E08[0] = 0x3C;
    SsSeqCalledTbyT_slotbits = 0;
    D_800ABA38[0] = 0;
    D_800ABA3C[0] = -1;
    D_800ABA40[0] = 0;
    D_800ABA48[0] = 0;

    D_800ABA44[0] = GetVideoMode();
    SsSeqCalledTbyT_guard = 0;
}
