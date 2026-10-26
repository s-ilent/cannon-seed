/* STAGED DECODE ARTIFACT (lives at scripts/bm_unit_decode/func_8002ADA0.c; lands at src/func_8002ADA0.c only
 * when its judge loop closes - src/ is ratchet-gated on placeholder
 * tokens, and this unit's D_/func_ names are still placeholder debt
 * until the loop converges) -
 * VARIANT v23 (v22 base, renaming nudge): fd declared FIRST - pseudo-numbering/redeclaration-order lever for the -1 register choice (retail -1->s1, ours -1->s2). the judge loop is OPEN (first compile links and
 * diffs: the prologue binds interleave into the save sequence while
 * retail keeps all six saves ahead of every bind - iteration matrix
 * queued in the worklog). slps_00270 unit VA 0x8002ADA0..0x8002B464
 * (yaml/file 0xB5A0..0xBC64, 0x6c4 bytes), carved out of the giant
 * boot row at its true entry (the jal'd prologue) through its epilogue;
 * the twin unit is src/func_8002ABC8.c
 * (same source shape, per-target data symbols, scheduler deltas from
 * the different %hi/%lo pairs).
 *
 * RETAIL STRUCTURE (instruction-level decode, all 33 chunks accounted
 * 0x6c4 bytes end to end):slps_00270 unit VA 0x8002ADA0..0x8002B464
 * (yaml/file 0xB5A0..0xBC64, 0x6c4 bytes), carved out of the giant
 * func_800272F8 row; the twin sces_00269 unit is src/func_8002ABC8.c
 * (same source shape, per-target data symbols, scheduler deltas from
 * the different %hi/%lo pairs).
 *
 * The memory-card save unit: builds the 'SC'+code header at D_801150F8,
 * fills the 0x200 work buffer D_8006974C with 0xFF, copies the 0x30
 * name record into D_80115158, then THREE 0x80-byte struct assignments
 * selected by the (short)code == 0x13 test (both arms re-bind the same
 * first assignment src5 -> D_80115178, which is why gcc expands the
 * block-move twice instead of CSE-ing it), copies the 0x200 header
 * block back into the work buffer, and runs the open/close/write/read
 * verify sequence with the sector count byte D_801150FB shifted into
 * the create-open flags.
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
 *    (per-iteration base materialization, sltiu bound), and -1 from
 *    the first open is materialized once into s1 and reused by every
 *    later fd == -1 compare after hdr's liveness ends.
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
    int fd;
    int t;
    int u;
    int total;
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
    if (fd == -1) {
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
    close(fd);
    return 2;
}
