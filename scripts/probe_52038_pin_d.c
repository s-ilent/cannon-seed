/* probe round 2: grow toward the real function to find what breaks the $4 pin */
extern long D_80147E24;
extern long D_80164268;
extern long D_801727D4;
extern long D_80171E04;
extern long D_8016AF90;
extern long D_8016AFA4;
extern long GsSetLightMode_lmode;
extern long D_80147E20;

typedef long (*StdFn)(long *, long, long, long, long, long, long, long *);
extern long D_80098998[];

/* D: the full five-read head + stores + branch + rec fill, NO loop */
void probeD(long *ctrlp, long a1p, long a2p, long *recp)
{
    register long *ctrl asm("$4");
    register long *rec asm("$19");
    register long a1 asm("$20");
    register long a2 asm("$21");
    long fpv, t0, a1v, a2v, mode;
    long f1, f2, f3, f5;
    ctrl = ctrlp;
    a1 = a1p;
    a2 = a2p;
    rec = recp;
    if (*ctrl >= 0) {
        f1 = (long)((*(unsigned long *)ctrl >> 3) & 3);
        f2 = (long)((*(volatile unsigned long *)ctrl >> 5) & 1);
        D_80147E24 = f1;
        f3 = (long)((*(unsigned long *)ctrl >> 6) & 1);
        D_80164268 = f2;
        a1v = (*(unsigned long *)ctrl >> 9) & 7;
        D_80147E20 = f3;
        f5 = (long)((*(unsigned long *)ctrl >> 30) & 1);
        D_801727D4 = a1v;
        D_80171E04 = f5;
        a2v = (a1v != 0);
        if (a1v != 0) {
            rec[0] = a1v;
            rec[1] = D_8016AF90;
            rec[2] = D_8016AFA4;
        }
        mode = (GsSetLightMode_lmode == 1);
    }
}

/* E: D + the loop skeleton with one call through the table (no state loads) */
void probeE(long *ctrlp, long a1p, long a2p, long *recp)
{
    register long *ctrl asm("$4");
    register long *rec asm("$19");
    register long a1 asm("$20");
    register long a2 asm("$21");
    long fpv, t0, a1v, a2v, mode, s1;
    long f1, f2, f3, f5;
    ctrl = ctrlp;
    a1 = a1p;
    a2 = a2p;
    rec = recp;
    if (*ctrl >= 0) {
        f1 = (long)((*(unsigned long *)ctrl >> 3) & 3);
        f2 = (long)((*(volatile unsigned long *)ctrl >> 5) & 1);
        D_80147E24 = f1;
        f3 = (long)((*(unsigned long *)ctrl >> 6) & 1);
        D_80164268 = f2;
        a1v = (*(unsigned long *)ctrl >> 9) & 7;
        D_80147E20 = f3;
        f5 = (long)((*(unsigned long *)ctrl >> 30) & 1);
        D_801727D4 = a1v;
        D_80171E04 = f5;
        a2v = (a1v != 0);
        if (a1v != 0) {
            rec[0] = a1v;
            rec[1] = D_8016AF90;
            rec[2] = D_8016AFA4;
        }
        mode = (GsSetLightMode_lmode == 1);
        s1 = 1;
        t0 = a2v * 12;
        fpv = a2v << 2;
        do {
            D_80147E24 = ((StdFn) * (long **)((char *)D_80098998 + t0 + (mode << 2)))(
                (long *)0, 0, 0, 0, 0, a2, a1, rec);
            s1--;
        } while (s1 != 0);
    }
}
