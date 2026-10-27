/* STAGED DECODE ARTIFACT (lands at src/func_8002ADA0.c only when its
 * judge loop closes - src/ is ratchet-gated on placeholder tokens, and
 * this unit's D_/func_ names are still placeholder debt until the loop
 * converges) - the block-move landing recipe banked by cron-202610260649,
 * decoded cron-202610260919; VARIANT v26 (v22 base + the twin's VR2
 * mutation, cron-20261027-1248): the first-open guard is INVERTED -
 * `if (fd != -1) { close(fd); return 2; }` with the create path
 * falling through unguarded - the shape that closed the twin's entire
 * return-2 cluster (judge 144/432 -> 107/433, size delta dead, built
 * 1732 = retail exactly). Retail's layout: the guard branches INTO the
 * create path; close+j-thunk with v0=2 in the j delay slot falls
 * through. slps_00270 unit VA 0x8002ADA0..0x8002B464 (yaml/file
 * 0xB5A0..0xBC64, 0x6c4 bytes), carved out of the giant func_800272F8
 * row at its true entry (the jal'd prologue) through its epilogue; the
 * twin unit is src/func_8002ABC8.c (same source shape, per-target data
 * symbols, scheduler deltas from the different %hi/%lo pairs).
 *
 * Source shapes that make GCC 2.6.3 reproduce the retail body:
 * 1. The sector math is SIGNED division/modulo, three separate
 *    expressions - t/0x2000*0x2000, then the t%0x2000 rebind, then the
 *    final total/0x2000 for the sector byte (the bgez+0x1fff-bias+sra
 *    branchy form, not the add-bias-and-mask round-up idiom).
 * 2. The header stores mix one pointer variable with the distinct
 *    per-byte symbols: 'S' goes through hdr[0] (s1, kept live for the
 *    strcpy dst and the first block-move dst binding), while 'C' and
 *    the code byte address D_801150F9/D_801150FA directly (fresh lui/
 *    addiu materializations per store, exactly as retail).
 * 3. The 0x80 struct assignments compile through the movstrsi
 *    expansion (scripts/bm_shape_probe.c law): or/andi/beqz dispatch,
 *    the 0x54 unaligned lwl/lwr loop, the 0x2c aligned lw/sw loop,
 *    16-stride addiu cursors; the 0x200 copy is the same law at loop
 *    size, and the 0x30 record copy is the straight-line form.
 * 4. The 0xff fill stays a manual byte loop over the extern array
 *    (per-iteration base materialization, sltiu bound) with an
 *    UNSIGNED counter - the unsigned i blocks gcc 2.6.3's loop
 *    reversal so the fill reproduces retail's upward sltiu form.
 */
struct S30 { unsigned char b[0x30]; };
struct S80 { unsigned char b[0x80]; };
struct S200 { unsigned char b[0x200]; };

extern unsigned char D_8006974C[];
extern unsigned char D_801150F8[];
extern unsigned char D_801150F9[];
extern unsigned char D_801150FA[];
extern unsigned char D_801150FB[];
extern unsigned char D_80115158[];
extern unsigned char D_801151F8[];
extern unsigned char D_80115278[];

int func_8002ADA0(char *path, int code, char *str, void *rec, void *src5,
                  void *src6, void *src7, int size)
{
    int t;
    int u;
    int total;
    int fd;
    unsigned int i;
    unsigned char *hdr;

    t = size;
    t += 0x200;
    u = t;
    total = t / 0x2000 * 0x2000;
    if (t != u / 0x2000 * 0x2000)
        total += 0x2000;

    for (i = 0; i < 0x200; i++)
        D_8006974C[i] = 0xFF;

    hdr = D_801150F8;
    hdr[0] = 0x53;
    D_801150F9[0] = 0x43;
    D_801150FA[0] = code;
    D_801150FB[0] = total / 0x2000;
    strcpy(hdr + 4, str);
    *(struct S30 *)D_80115158 = *(struct S30 *)rec;

    if ((short)code == 0x13) {
        *(struct S80 *)(hdr + 0x80) = *(struct S80 *)src5;
        *(struct S80 *)D_801151F8 = *(struct S80 *)src6;
        *(struct S80 *)D_80115278 = *(struct S80 *)src7;
    } else {
        *(struct S80 *)(hdr + 0x80) = *(struct S80 *)src5;
        *(struct S80 *)D_801151F8 = *(struct S80 *)src5;
        *(struct S80 *)D_80115278 = *(struct S80 *)src5;
    }

    *(struct S200 *)D_8006974C = *(struct S200 *)D_801150F8;

    fd = open(path, 1);
    if (fd != -1) {
        close(fd);
        return 2;
    }
    fd = open(path, (D_801150FB[0] << 16) | 0x200);
    if (fd == -1)
        return 0;
    close(fd);
    fd = open(path, 2);
    if (fd == -1)
        return -3;
    if (write(fd, D_8006974C, 0x200) != 0x200) {
        close(fd);
        return -3;
    }
    close(fd);
    fd = open(path, 1);
    if (fd == -1)
        return -3;
    if (read(fd, D_8006974C, 0x200) != 0x200) {
        close(fd);
        return -3;
    }
    close(fd);
    return 1;
}
