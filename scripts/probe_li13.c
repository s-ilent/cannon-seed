/* probe: what C shape keeps the head's `ori $v0,$zero,0xD` (x = 13) AFTER
 * the three volatile sh's, with the D_800AB0B8 base pointer in $2?
 *
 * Retail head (g3_eu 0x44AA0..0x44B10):
 *   addiu $sp,$sp,-0x20 ; sw $s0,0x18($sp) ; addu $s0,$a0,$zero
 *   lui $a0,%hi(D_800AB0C8) ; lw $a0,%lo(D_800AB0C8)($a0) ; sw $ra,0x1C($sp)
 *   lw $v0,0($a0) ; lui $v1,0xB ; or $v0,$v0,$v1 ; sw $v0,0($a0)
 *   lui $v0,%hi(D_800AB0B8) ; lw $v0,%lo(D_800AB0B8)($v0) ; nop
 *   sh $zero,0x180($v0) ; sh $zero,0x182($v0) ; sh $zero,0x1AA($v0)
 *   ori $v0,$zero,0xD ; sw $v0,0x14($sp) ; sw $zero,0x10($sp)
 *   lw $v0,0x10($sp) ; [D_800AB0D0/D4/B4 stores via $at] ; slti ; beqz
 *
 * Window 32 parked draft: same C order but gcc hoists li $2,13 above the
 * sh's and drops the base into $6 - every downstream word shifts.
 *
 * Variants (one function each, head + first loop only):
 *   h0 - best-build replica (scalar *volatile extern + local v cache)
 *   h1 - block-scoped register var pins the head's base pointer to $2
 *   h2 - whole-function register var $2 (control: expect later-piece break)
 *   h3 - memory-clobber barrier asm between the sh's and x = 13
 *   h4 - non-volatile store cast for the three sh's (i/x stay volatile)
 *   h5 - h1 but the pin declared without initializer (assign inside block)
 */
extern long *D_800AB0C8;
extern volatile unsigned short *volatile D_800AB0B8;
extern long D_800AB0D0[];
extern long D_800AB0D4[];
extern unsigned short D_800AB0B4[];
extern long D_800AB0D8[];
extern long D_800AB0DC[];
extern long D_800AB0E0[];
extern long D_800AB0E4[];
extern void sink(long);

static void spin(void)
{
    volatile int x, i;
    x = 13;
    i = 0;
    while (i < 0xF0) {
        x = x * 3;
        i++;
    }
}

long h0(long arg)
{
    volatile int x, i;
    unsigned short *v;

    v = D_800AB0B8;
    *D_800AB0C8 |= 0xB0000;
    v[0xC0] = 0;
    v[0xC1] = 0;
    v[0xD5] = 0;
    x = 13;
    i = 0;
    D_800AB0D0[0] = 0;
    D_800AB0D4[0] = 0;
    D_800AB0B4[0] = 0;
    while (i < 0xF0) {
        x = x * 3;
        i++;
    }
    if (arg == 0) {
        D_800AB0D8[0] = 2;
        spin();
    }
    return 0;
}

long h1(long arg)
{
    volatile int x, i;
    unsigned short *v;

    v = D_800AB0B8;
    *D_800AB0C8 |= 0xB0000;
    {
        register volatile unsigned short *vp asm("$2");
        vp = D_800AB0B8;
        vp[0xC0] = 0;
        vp[0xC1] = 0;
        vp[0xD5] = 0;
    }
    x = 13;
    i = 0;
    D_800AB0D0[0] = 0;
    D_800AB0D4[0] = 0;
    D_800AB0B4[0] = 0;
    while (i < 0xF0) {
        x = x * 3;
        i++;
    }
    if (arg == 0) {
        D_800AB0D8[0] = 2;
        spin();
    }
    return 0;
}

long h2(long arg)
{
    volatile int x, i;
    register unsigned short *v asm("$2");

    v = D_800AB0B8;
    *D_800AB0C8 |= 0xB0000;
    v[0xC0] = 0;
    v[0xC1] = 0;
    v[0xD5] = 0;
    x = 13;
    i = 0;
    D_800AB0D0[0] = 0;
    D_800AB0D4[0] = 0;
    D_800AB0B4[0] = 0;
    while (i < 0xF0) {
        x = x * 3;
        i++;
    }
    if (arg == 0) {
        D_800AB0D8[0] = 2;
        spin();
    }
    return 0;
}

long h3(long arg)
{
    volatile int x, i;
    unsigned short *v;

    v = D_800AB0B8;
    *D_800AB0C8 |= 0xB0000;
    v[0xC0] = 0;
    v[0xC1] = 0;
    v[0xD5] = 0;
    __asm__ __volatile__("" ::: "memory");
    x = 13;
    i = 0;
    D_800AB0D0[0] = 0;
    D_800AB0D4[0] = 0;
    D_800AB0B4[0] = 0;
    while (i < 0xF0) {
        x = x * 3;
        i++;
    }
    if (arg == 0) {
        D_800AB0D8[0] = 2;
        spin();
    }
    return 0;
}

long h4(long arg)
{
    volatile int x, i;
    unsigned short *v;

    v = D_800AB0B8;
    *D_800AB0C8 |= 0xB0000;
    {
        unsigned short *nv = (unsigned short *)v;
        nv[0xC0] = 0;
        nv[0xC1] = 0;
        nv[0xD5] = 0;
    }
    x = 13;
    i = 0;
    D_800AB0D0[0] = 0;
    D_800AB0D4[0] = 0;
    D_800AB0B4[0] = 0;
    while (i < 0xF0) {
        x = x * 3;
        i++;
    }
    if (arg == 0) {
        D_800AB0D8[0] = 2;
        spin();
    }
    return 0;
}

long h5(long arg)
{
    volatile int x, i;
    unsigned short *v;

    v = D_800AB0B8;
    *D_800AB0C8 |= 0xB0000;
    {
        register unsigned short *vp asm("$2");
        vp = (unsigned short *)D_800AB0B8;
        vp[0xC0] = 0;
        vp[0xC1] = 0;
        vp[0xD5] = 0;
    }
    x = 13;
    i = 0;
    D_800AB0D0[0] = 0;
    D_800AB0D4[0] = 0;
    D_800AB0B4[0] = 0;
    while (i < 0xF0) {
        x = x * 3;
        i++;
    }
    if (arg == 0) {
        D_800AB0D8[0] = 2;
        spin();
    }
    return 0;
}
