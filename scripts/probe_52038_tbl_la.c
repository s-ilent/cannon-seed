typedef long (*StdFn)(long *, long, long, long, long, long, long, long *);
extern long D_800989D8[];
extern long D_80098A98[];
extern long D_80098A10[];
extern long D_8016AB6C;
extern char D_80021AF0[];
extern int printf();
void f(long *ctrlp, long a1p, long a2p, long *recp)
{
    register long *ctrl asm("$4");
    register long *rec asm("$19");
    register long a1 asm("$20");
    register long a2 asm("$21");
    register long s6v asm("$22");
    register long s7 asm("$23");
    register unsigned char *s0 asm("$16");
    register long s1 asm("$17");
    register long s2 asm("$18");
    long fpv;
    long t0;
    long tbl;
    long a2v;
    long *state;
    a1 = a1p; a2 = a2p; rec = recp; ctrl = ctrlp;
    state = (long *)ctrlp[2];
    s0 = (unsigned char *)state[4];
    s1 = state[5];
    s2 = state[0];
    s7 = state[2];
    s6v = 4;
    t0 = a2v * 12;
    fpv = a2v << 2;
    do {
        unsigned int code = (unsigned int)s0[3] & 0xFD;
        switch (code) {
        case 0x24:
            tbl = D_800989D8;
            D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)tbl)))(
                (long *)s0, s2, s7, D_8016AB6C,
                *(unsigned short *)s0, a2, a1, rec);
            s1 -= *(unsigned short *)s0;
            s0 += *(unsigned short *)s0 * 24;
            break;
        case 0x20:
            if (*(unsigned short *)(s0 + 2) & 4) {
                tbl = D_80098A98;
                D_8016AB6C = ((StdFn) * (long *)(s6v + (char *)tbl))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 24;
            } else {
                tbl = D_800989D8;
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)tbl)))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 16;
            }
            break;
        case 0x35:
            tbl = D_80098A10;
            D_8016AB6C = ((long (*)(long *, long, long, long, long, long, long *))(s6v + (char *)tbl))(
                (long *)s0, s2, D_8016AB6C,
                *(unsigned short *)s0, a2, a1, rec);
            s1 -= *(unsigned short *)s0;
            s0 += *(unsigned short *)s0 * 36;
            break;
        default:
            printf(D_80021AF0, code, s0);
            break;
        }
    } while (s1 != 0);
}
