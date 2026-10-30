/* probe round 4: bisect E->F. G adds state pins/loads to E. H adds the loop. */
extern long D_80147E24;
extern long D_80164268;
extern long D_801727D4;
extern long D_80171E04;
extern long D_80147E20;
extern long D_8016AF90;
extern long D_8016AFA4;
extern long D_8016AB6C;
extern long GsSetLightMode_lmode;
extern long D_80098998[];

typedef long (*StdFn)(long *, long, long, long, long, long, long, long *);

static void head(long *ctrl, long *rec, long a1, long a2)
{
    long f1, f2, f3, f5, a1v;
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
    if (a1v != 0) {
        rec[0] = a1v;
        rec[1] = D_8016AF90;
        rec[2] = D_8016AFA4;
    }
}

/* G: E + state loads feeding pinned s0/s1/s2/s7; NO loop/call */
void probeG(long *ctrlp, long a1p, long a2p, long *recp)
{
    register long *ctrl asm("$4");
    register unsigned char *s0 asm("$16");
    register long s1 asm("$17");
    register long s2 asm("$18");
    register long *rec asm("$19");
    register long a1 asm("$20");
    register long a2 asm("$21");
    register long s6v asm("$22");
    register long s7 asm("$23");
    long *state;
    ctrl = ctrlp;
    a1 = a1p;
    a2 = a2p;
    rec = recp;
    if (*ctrl >= 0) {
        head(ctrl, rec, a1, a2);
        state = (long *)ctrl[2];
        s0 = (unsigned char *)state[4];
        s1 = state[5];
        s2 = state[0];
        s7 = state[2];
        s6v = s1 + s2 + s7 + (long)s0;
        D_8016AB6C = s6v;
    }
}

/* H: G + the do-while loop with the call */
void probeH(long *ctrlp, long a1p, long a2p, long *recp)
{
    register long *ctrl asm("$4");
    register unsigned char *s0 asm("$16");
    register long s1 asm("$17");
    register long s2 asm("$18");
    register long *rec asm("$19");
    register long a1 asm("$20");
    register long a2 asm("$21");
    register long s6v asm("$22");
    register long s7 asm("$23");
    long fpv, t0, a1v, a2v, mode;
    long *state;
    ctrl = ctrlp;
    a1 = a1p;
    a2 = a2p;
    rec = recp;
    if (*ctrl >= 0) {
        head(ctrl, rec, a1, a2);
        a1v = D_801727D4;
        a2v = (a1v != 0);
        mode = (GsSetLightMode_lmode == 1);
        state = (long *)ctrl[2];
        s0 = (unsigned char *)state[4];
        s1 = state[5];
        s2 = state[0];
        s7 = state[2];
        if (s1 == 0) {
            return;
        }
        s6v = mode << 2;
        t0 = a2v * 12;
        fpv = a2v << 2;
        do {
            D_8016AB6C = ((StdFn) * (long **)((char *)D_80098998 + t0 + s6v))(
                (long *)s0, s2, s7, D_8016AB6C,
                *(unsigned short *)s0, a2, a1, rec);
            s1 -= *(unsigned short *)s0;
            s0 += *(unsigned short *)s0 * 16;
        } while (s1 != 0);
    }
}
