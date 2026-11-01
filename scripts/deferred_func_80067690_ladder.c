/* Real-decompiled-C game function #17 - the func_80067690 row (g3_eu,
 * 0x80067690..0x80067AC8, extent 0x438) lands as the psyq libsnd SVM
 * (sound voice manager) init, identity PROVEN _svm_damper-class VMANAGER
 * member by the psyq row-stream kind-0x30 walk + the def-row offset math
 * (cron-20261101-0536). Decode banked in scripts/deferred_func_80067690.c
 * (window cron-20261101-0151, offline, Law Zero); landed on the witnessed
 * oracle. Single caller: the SSINIT shared body func_8006AC04 at
 * 0x8006ACB0 (delay ori $a0,$zero,0x18 - max_voices = 24). Retail is NOT
 * a byte-verbatim 3.3 VMANAGER build - the game's own cc1 2.6.3-PSX
 * compiled it (same class as the landed func_800642A0).
 * Source-shape laws this body reproduces (retail-asm verified):
 *  - the svm bookkeeping halfwords zero BEFORE the SpuInitMalloc call;
 *    the a1 = &D_80147D64 argument setup hoists above them (GCC arg
 *    hoisting), the call's delay slot carries ori a0,0x20, and the
 *    sweep-A counter init lands after the return;
 *  - u16 counter discipline: the sweep counter and the voice index both
 *    live raw in $a1 and andi 0xFFFF at every use (the u16 register-var
 *    pin); sweep A holds its base in $3 across the loop, sweeps B/C
 *    re-derive the symbol address through $at every iteration;
 *  - the voice-count cap is the register ternary: andi a0,s0,0xFF
 *    (the u8 use-site mask - the prologue keeps the RAW a0 in $s0),
 *    sltiu 0x18, the false arm materializes 0x18 in the delay slot,
 *    the true arm stores a0 out-of-line;
 *  - the gate re-reads the static (lbu) and branches beqz to the tail
 *    with the voice-index init in the delay slot; the two loop-invariant
 *    immediates 1 (t0) and 0xFF (t1) materialize after the gate;
 *  - the svm record fields are PER-FIELD DLABEL indexing (D_8014783E
 *    etc., v*0x1A on the u16 views, v*0x34 on the u8 views) - one
 *    52v multiply chain shared by every store, no held record pointer;
 *  - the SPU voice-register run goes through the volatile-qualified
 *    pointer load *D_800AB874 fresh per voice, the halfword index
 *    (u16)((u16)v*8) andi'd then sll 1 into the base add;
 *  - D_801704A2 stores the RAW index (sh truncates) and the mask split
 *    shifts off the RELOADED value (store-reload round trip, sllv off
 *    the andi'd reload); the re-zero block re-derives v*0x34 from the
 *    reload, not from the raw counter;
 *  - the loop's mask bookkeeping (| into D_8017281C/D_80172820, & ~
 *    into D_80147DF0/D_80147DF4) is observably dead in the init path
 *    (the tail zeroes the same statics) but is the real bytes;
 *  - the +0x24 record store is LAST in its run; D_801652F0 is a WORD
 *    store (retail sw, not sh).
 * The svm statics keep their D_ names; the rename claim (_svm_damper)
 * is lane-owner-gated on the omf_pubsyms publics-parser pin (the archive
 * symbol-table walk stops early - only 2 of VMANAGER's 44 publics carry
 * 0x0c offset rows today).
 */
extern void _spu_setInTransfer();
extern long SpuInitMalloc(long num, char *top);
extern void SsSeqCalledTbyT_init();

/* svm data cluster (D_ names until the lane owner banks the svm names): */
extern unsigned char D_8016B08C;          /* active voice count, cap 0x18 */
extern unsigned short D_8016B108;         /* svm bookkeeping, slotbits-4 */
extern unsigned short D_8016AC24;         /* svm bookkeeping */
extern unsigned short D_801476A4[];       /* 24 x 8 svm voice halfwords */
extern unsigned char D_80147824[];        /* 24 voice flags */
extern unsigned short D_8017278C;
extern unsigned char D_801704A8[];        /* 16 key slots */
extern unsigned short D_8016AD08;         /* guard+4, set 0x80 */
extern unsigned short D_80147DF0;         /* key-on mask low */
extern unsigned short D_80147DF4;         /* key-on mask high */
extern unsigned short D_80147DF8;
extern unsigned short D_80147DFC;
extern unsigned short D_8017281C;         /* voice-on mask low */
extern unsigned short D_80172820;         /* voice-on mask high */
extern unsigned int D_801652F0;           /* retail sw */
extern unsigned int D_801652F4;           /* retail sw */
extern unsigned short D_801652F8;         /* main vol L */
extern unsigned short D_801652FA;         /* main vol R */
extern unsigned char D_8017057C;
extern unsigned short _svm_stereo_mono;   /* CURATED */
extern unsigned short D_801704A2;         /* svm current voice */
/* the svm record fields, one dlabel per retail access (base 0x8014783C,
 * stride 0x34 per voice): */
extern unsigned short D_8014783C[];       /* +0x00 */
extern unsigned short D_8014783E[];       /* +0x02 */
extern unsigned short D_80147840[];       /* +0x04 */
extern unsigned short D_80147842[];       /* +0x06 */
extern unsigned short D_80147844[];       /* +0x08 */
extern unsigned char D_80147846[];        /* +0x0A */
extern unsigned short D_8014784A[];       /* +0x0E */
extern unsigned short D_8014784C[];       /* +0x10 */
extern unsigned short D_8014784E[];       /* +0x12 */
extern unsigned short D_80147850[];       /* +0x14 */
extern unsigned char D_80147857[];        /* +0x1B */
extern unsigned short D_80147858[];       /* +0x1C */
extern unsigned short D_8014785A[];       /* +0x1E */
extern unsigned short D_8014785C[];       /* +0x20 */
extern unsigned short D_8014785E[];       /* +0x22 */
extern unsigned short D_80147860[];       /* +0x24 */
extern unsigned short D_80147864[];       /* +0x28 */
extern unsigned short D_80147866[];       /* +0x2A */
extern unsigned short D_80147868[];       /* +0x2C */
extern unsigned short D_8014786A[];       /* +0x2E */
extern unsigned short D_8014786C[];       /* +0x30 */
extern char D_80147D64[];                 /* SpuInitMalloc table, 264 B */
extern unsigned short *volatile D_800AB874; /* SPU voice reg base = 0x1F801C00 */

void func_80067690(unsigned char max_voices)
{
    unsigned short *spu;
    unsigned short mask_lo, mask_hi;
    unsigned short mask_cur_lo, mask_cur_hi;
    register unsigned int iv asm("$5");
    unsigned short rv;
    register unsigned int rvn asm("$4");

    _spu_setInTransfer(0);
    D_8016B108 = 0;
    D_8016AC24 = 0;
    SpuInitMalloc(0x20, D_80147D64);
    {
        unsigned short *base;
        iv = 0;
        base = D_801476A4;
        for (; (unsigned short)iv < 0xC0; iv++) {
            base[(unsigned short)iv] = 0;
        }
        iv = 0;
        for (; (unsigned short)iv < 0x18; iv++) {
            D_80147824[(unsigned short)iv] = 0;
        }
        D_8017278C = 0;
        iv = 0;
        for (; (unsigned short)iv < 0x10; iv++) {
            D_801704A8[(unsigned short)iv] = 0;
        }
    }
    {
        register unsigned int mv asm("$4");
        mv = max_voices;
        if (mv >= 0x18) {
            D_8016B08C = 0x18;
        } else {
            D_8016B08C = mv;
        }
    }
    {
        register unsigned long off asm("$2");
        unsigned short spu_idx;
        register unsigned short mask_lo asm("$7");
        register unsigned short mask_hi asm("$6");
        for (iv = 0; (unsigned short)iv < (unsigned short)D_8016B08C; iv++) {
            spu_idx = (unsigned short)iv * 8;
            __asm__ volatile("" ::: "memory");
            off = (unsigned short)iv * 0x34;
            __asm__("" : : "r"(off));
            *(unsigned short *)((char *)D_8014783E + off) = 0x18;
            *(signed short *)((char *)D_8014784A + off) = -1;
            *(unsigned short *)((char *)D_8014783C + off) = 0xFF;
            *(unsigned char *)((char *)D_80147857 + off) = 0;
            *(unsigned short *)((char *)D_80147840 + off) = 0;
            *(unsigned short *)((char *)D_80147842 + off) = 0;
            *(unsigned short *)((char *)D_8014784C + off) = 0;
            *(unsigned short *)((char *)D_8014784E + off) = 0;
            *(unsigned short *)((char *)D_80147850 + off) = 0xFF;
            *(unsigned short *)((char *)D_80147844 + off) = 0;
            *(unsigned char *)((char *)D_80147846 + off) = 0x40;
            *(unsigned short *)((char *)D_80147858 + off) = 0;
            *(unsigned short *)((char *)D_8014785A + off) = 0;
            *(unsigned short *)((char *)D_8014785C + off) = 0;
            *(unsigned short *)((char *)D_8014785E + off) = 0;
            *(unsigned short *)((char *)D_80147864 + off) = 0;
            *(unsigned short *)((char *)D_80147866 + off) = 0;
            *(unsigned short *)((char *)D_80147868 + off) = 0;
            *(unsigned short *)((char *)D_8014786A + off) = 0;
            *(unsigned short *)((char *)D_8014786C + off) = 0;
            *(unsigned short *)((char *)D_80147860 + off) = 0; /* +0x24 LAST */
            spu = D_800AB874 + spu_idx;
            spu[3] = 0x200;
            spu[2] = 0x1000;
            spu[4] = 0x80FF;
            spu[0] = 0;
            spu[1] = 0;
            spu[5] = 0x4000;
            __asm__ volatile("" ::: "memory");
            D_801704A2 = iv;
            rv = *(volatile unsigned short *)&D_801704A2;
            __asm__("" : "=r"(rv) : "0"(rv));
            rvn = rv;
            if (rvn < 0x10) {
                mask_lo = 1 << rvn;
                mask_hi = 0;
            } else {
                register unsigned int sh_amt asm("$2");
                mask_lo = 0;
                sh_amt = rvn - 0x10;
                mask_hi = 1 << sh_amt;
            }
            off = (unsigned short)rv * 0x34;
            mask_cur_lo = D_8017281C;
            mask_cur_hi = D_80172820;
            *(unsigned char *)((char *)D_80147857 + off) = 0;
            *(unsigned short *)((char *)D_80147840 + off) = 0;
            *(unsigned short *)((char *)D_8014783C + off) = 0;
            D_8017281C = mask_cur_lo | mask_lo;
            D_80172820 = mask_cur_hi | mask_hi;
            D_80147DF0 &= ~mask_lo;
            D_80147DF4 &= ~mask_hi;
        }
    }
    D_801652F8 = 0x3FFF;
    D_801652FA = 0x3FFF;
    D_80147DF0 = 0;
    D_80147DF4 = 0;
    D_8017281C = 0;
    D_80147DF8 = 0;
    D_80147DFC = 0;
    D_801652F0 = 0;
    D_801652F4 = 0;
    D_8017057C = 0;
    _svm_stereo_mono = 0;
    D_8016AD08 = 0x80;
    SsSeqCalledTbyT_init();
}
