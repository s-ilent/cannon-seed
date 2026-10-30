/* probe: does gcc 2.6.3 honor a $4 pin on a non-volatile pointer local?
 * variant A: non-volatile pointer pin $4, init from param
 * variant B: volatile-qualified pointer pin $4
 * variant C: no pin at all (param used directly)
 * compiled cc.sh -S; inspect which reg the loads use and whether a copy exists
 */
extern long D_80147E24;
extern long D_80164268;

void probeA(long *ctrlp)
{
    register long *ctrl asm("$4");
    long f1, f2;
    ctrl = ctrlp;
    f1 = (long)((*(unsigned long *)ctrl >> 3) & 3);
    f2 = (long)((*(volatile unsigned long *)ctrl >> 5) & 1);
    D_80147E24 = f1;
    D_80164268 = f2;
}

void probeB(long *ctrlp)
{
    register volatile long *ctrl asm("$4");
    long f1, f2;
    ctrl = ctrlp;
    f1 = (long)((*(unsigned long *)ctrl >> 3) & 3);
    f2 = (long)((*(volatile unsigned long *)ctrl >> 5) & 1);
    D_80147E24 = f1;
    D_80164268 = f2;
}

void probeC(long *ctrl)
{
    long f1, f2;
    f1 = (long)((*(unsigned long *)ctrl >> 3) & 3);
    f2 = (long)((*(volatile unsigned long *)ctrl >> 5) & 1);
    D_80147E24 = f1;
    D_80164268 = f2;
}
