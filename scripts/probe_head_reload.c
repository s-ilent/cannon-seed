/* Probe: does cc1 2.6.3-PSX hoist the next *ctrl load above the previous
 * extern-long store? Variant A: separate statements (current form).
 * Variant B: reassigned local. Variant C: consecutive loads first. */
extern long D_E24;
extern long D_D64268;
extern long D_E20;
extern long D_D727D4;
extern long D_D71E04;

void probeA(long *ctrl)
{
    if (*ctrl >= 0) {
        D_E24 = (long)((*(unsigned long *)ctrl >> 3) & 3);
        D_D64268 = (long)((*(unsigned long *)ctrl >> 5) & 1);
        D_E20 = (long)((*(unsigned long *)ctrl >> 6) & 1);
        D_D727D4 = (long)((*(unsigned long *)ctrl >> 9) & 7);
        D_D71E04 = (long)((*(unsigned long *)ctrl >> 30) & 1);
    }
}

void probeB(long *ctrl)
{
    unsigned long t;
    if (*ctrl >= 0) {
        t = *(unsigned long *)ctrl;
        D_E24 = (long)((t >> 3) & 3);
        t = *(unsigned long *)ctrl;
        D_D64268 = (long)((t >> 5) & 1);
        t = *(unsigned long *)ctrl;
        D_E20 = (long)((t >> 6) & 1);
        t = *(unsigned long *)ctrl;
        D_D727D4 = (long)((t >> 9) & 7);
        t = *(unsigned long *)ctrl;
        D_D71E04 = (long)((t >> 30) & 1);
    }
}
