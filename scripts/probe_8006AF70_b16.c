/* BISECT B16 - b9 + ONLY the head's ABA50 load (v1 = D_800ABA50). B9 header:
 * b5 + real c4 AND real c1 (c3/c2 still stubs). B7 header:
 * b5 + the real c4 body restored (c1/c3/c2 still stubs). B5 header:
 * c1..c4 stubbed, c5's load in a DISTINCT plain pseudo v5 (unpinned). B3 header:
 * head removed AND c1..c4 stubbed. B2 header:
 * head removed (v1 = a0 directly; no ABA54/50 stores, no >=6/L_big). Original B1 header:
 * func_8006AF70 alone from the r3 draft (the seven later
 * functions dropped). Question: does the c0/c5 tail-merge still fire
 * with no other function in the translation unit?
 * Expected per the twin_test repro (which keeps ONLY the dispatch +
 * the two chains and does NOT merge): this file isolates the head +
 * dispatch + c1..c4 + the two chains. If the merge fires here, the
 * trigger is inside this function; next probes drop pieces.
 * cc-post: keep-epilogue
 */

extern long D_800ABA38;
extern long D_800ABA3C;
extern long D_800ABA40;
extern long D_800ABA44;
extern long D_800ABA48;
extern long D_800ABA4C;
extern long D_800ABA50;
extern long D_800ABA54;
extern long D_80171E08;              /* = SsSeqCalledTbyT_ntracks (curated) */
extern long jtbl_8002220C[];
extern void intr_stop_begin(void);
extern long func_8006B648(long);     /* LANDED slot clear */
extern long func_8006B500(long, long, long);
extern long func_8006B5D8(long);
extern long func_8004AE64(void);     /* curated intr_restart_commit */
extern void VSyncCallback(void (*fn)(void));
extern long InterruptCallback(long, void (*fn)(void));
extern void SpuQuit(void);
extern void SsSeqCalledTbyT(void);
void func_8006B4B8(void);
void func_8006B484(void);

void func_8006AF70(long a0)
{
    long v0;
    long v1;
    long v5;
    long vt;

    v1 = D_800ABA50;
    __asm__ ("" : : "i"(&&L_c0), "i"(&&L_c1), "i"(&&L_c2), "i"(&&L_c3),
                    "i"(&&L_c4), "i"(&&L_c5));
    if ((unsigned long)v1 < 6)
        goto *((void **)jtbl_8002220C)[v1];
    /* default (B0CC: ori v0,0x3C falls into B0D0's store) */
    vt = 0x3C;
    goto L_store3C;

L_c4:   /* 0x8006AFE4 - the parameter is reassigned to the constant */
    a0 = 0x32;
    v1 = D_800ABA44;
    D_80171E08 = a0;
    if (v1 == 1) {
        v0 = 5;
        goto L_store5;
    }
    D_800ABA50 = a0;
    return;

L_c1:   /* 0x8006B014 - the 5-path falls through B030, 0x3C out-of-line */
    v0 = D_800ABA44;
    v1 = 0x3C;
    D_80171E08 = v1;
    if (v0 != 0)
        goto L_b040;
    v0 = 5;
L_store5:   /* B030: sw v0 -> ABA50, shared by case 1 fall and case 4 beq */
    D_800ABA50 = v0;
    return;
L_b040:     /* B040: sw v1 (0x3C) -> ABA50 */
    D_800ABA50 = v1;
    return;


L_c3:
    D_80171E08 = 0x78;
    return;

L_c2:
    D_80171E08 = 0xF0;
    return;

L_c5:   /* 0x8006B078 - three-path chain; the volatile-memory barrier
         * after the load keeps gcc from merging this chain with case
         * 0's (rounds 2-3 lost it to tail-merge/label redirection -
         * round 3's plain opaque asm did not block it) */
    v5 = D_800ABA44;
    if (v5 == 0)
        goto L_def;
    if (v5 == 1) {
        vt = 0x32;
        goto L_store32;
    }
    vt = 0x3C;
    goto L_store3C;

L_c0:   /* 0x8006B09C - three-path chain, bne polarity, 0x32 falls */
    v1 = D_800ABA44;
    if (v1 == 0)
        goto L_def;
    if (v1 != 1) {
        vt = 0x3C;
        goto L_store3C;
    }
    vt = 0x32;
    /* fall into the shared 0x32 store */
L_store32:  /* B0BC: sw v0 -> D_80171E08 */
    D_80171E08 = vt;
    return;

L_def:      /* B0CC: ori v0, 0x3C, falls into the shared store */
    vt = 0x3C;
L_store3C:  /* B0D0: sw v0 -> D_80171E08 */
    D_80171E08 = vt;
    return;

}
