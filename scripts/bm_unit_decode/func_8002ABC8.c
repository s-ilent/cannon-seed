/* STAGED DECODE ARTIFACT (lives at scripts/bm_unit_decode/func_8002ABC8.c; lands at src/func_8002ABC8.c only
 * when its judge loop closes - src/ is ratchet-gated on placeholder
 * tokens, and this unit's D_/func_ names are still placeholder debt
 * until the loop converges) -
 * the block-move landing recipe banked by cron-202610260649, decoded
 * cron-202610260919; the judge loop is OPEN (first compile links and
 * diffs: the prologue binds interleave into the save sequence while
 * retail keeps all six saves ahead of every bind - iteration matrix
 * queued in the worklog). sces_00269 unit VA 0x8002ABC8..0x8002B28C
 * (yaml/file 0xB3C8..0xBA8C, 0x6c4 bytes), carved out of the giant
 * boot row at its true entry (the jal'd prologue) through its epilogue;
 * the twin unit is src/func_8002ADA0.c
 * (same source shape, per-target data symbols, scheduler deltas from
 * the different %hi/%lo pairs).
 *
 * RETAIL STRUCTURE (instruction-level decode, all 33 chunks accounted
 * 0x6c4 bytes end to end):sces_00269 unit VA 0x8002ABC8..0x8002B28C
 * (yaml/file 0xB3C8..0xBA8C, 0x6c4 bytes), carved out of the giant
 * func_80027340 row; the twin slps_00269 unit is src/func_8002ADA0.c
 * (same source shape, per-target data symbols, scheduler deltas from
 * the different %hi/%lo pairs).
 *
 * The memory-card save unit: builds the 'SC'+code header at D_80114678,
 * fills the 0x200 work buffer D_800693F4 with 0xFF, copies the 0x30
 * name record into D_801146D8, then THREE 0x80-byte struct assignments
 * selected by the (short)code == 0x13 test (both arms re-bind the same
 * first assignment src5 -> D_801146F8, which is why gcc expands the
 * block-move twice instead of CSE-ing it), copies the 0x200 header
 * block back into the work buffer, and runs the open/close/write/read
 * verify sequence with the sector count byte D_8011467B shifted into
 * the create-open flags.
 *
 * Source shapes that make GCC 2.6.3 reproduce the retail body:
 * 0. The t-chain is the SPLIT assignment (`t = size; t += 0x200;`) -
 *    the size reload lands in t's home register (retail's direct
 *    lw v1 form; the joint expression reloads through a0 instead).
 * 1. The sector math is SIGNED division/modulo, three separate
 *    expressions - t/0x2000*0x2000, then the t%0x2000 rebind, then the
 *    final total/0x2000 for the sector byte (the bgez+0x1fff-bias+sra
 *    branchy form, not the add-bias-and-mask round-up idiom).
 * 2. The header stores mix one pointer variable with the distinct
 *    per-byte symbols: 'S' goes through hdr[0] (s1, kept live for the
 *    strcpy dst and the first block-move dst binding), while 'C' and
 *    the code byte address D_80114679/D_8011467A directly (fresh lui/
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

extern unsigned char D_800693F4[];
extern unsigned char D_80114678[];
extern unsigned char D_80114679[];
extern unsigned char D_8011467A[];
extern unsigned char D_8011467B[];
extern unsigned char D_801146D8[];
extern unsigned char D_80114778[];
extern unsigned char D_801147F8[];

int func_8002ABC8(char *path, int code, char *str, void *rec, void *src5,
                  void *src6, void *src7, int size)
{
    int t;
    int total;
    int fd;
    unsigned i;
    unsigned char *hdr;

    t = size;
    t += 0x200;
    total = t / 0x2000 * 0x2000;
    if (t % 0x2000 != 0)
        total += 0x2000;

    for (i = 0; i < 0x200; i++)
        D_800693F4[i] = 0xFF;

    hdr = D_80114678;
    hdr[0] = 0x53;
    D_80114679[0] = 0x43;
    D_8011467A[0] = code;
    D_8011467B[0] = total / 0x2000;
    strcpy(hdr + 4, str);
    *(struct S30 *)D_801146D8 = *(struct S30 *)rec;

    if ((short)code == 0x13) {
        *(struct S80 *)(hdr + 0x80) = *(struct S80 *)src5;
        *(struct S80 *)D_80114778 = *(struct S80 *)src6;
        *(struct S80 *)D_801147F8 = *(struct S80 *)src7;
    } else {
        *(struct S80 *)(hdr + 0x80) = *(struct S80 *)src5;
        *(struct S80 *)D_80114778 = *(struct S80 *)src5;
        *(struct S80 *)D_801147F8 = *(struct S80 *)src5;
    }

    *(struct S200 *)D_800693F4 = *(struct S200 *)D_80114678;

    fd = open(path, 1);
    if (fd != -1) {
        close(fd);
        return 2;
    }
    fd = open(path, (D_8011467B[0] << 16) | 0x200);
    if (fd == -1)
        return 0;
    close(fd);
    fd = open(path, 2);
    if (fd == -1)
        return -3;
    if (write(fd, D_800693F4, 0x200) != 0x200) {
        close(fd);
        return -3;
    }
    close(fd);
    fd = open(path, 1);
    if (fd == -1)
        return -3;
    if (read(fd, D_800693F4, 0x200) != 0x200) {
        close(fd);
        return -3;
    }
    close(fd);
    return 1;
}

/* LIVE JUDGE MUTATION RECORD (cron-20261027-1018 window, oracle up):
 * V-int-i (the original): the 0xff fill compiles to a COUNTDOWN loop
 * (ori v1,0x1ff; bgez; -1 stride) while retail is UPWARD sltiu/bnez -
 * gcc 2.6.3 reverses the int-induction loop. V-unsigned-i: `unsigned i`
 * blocks the reversal (i >= 0 tautology) and the built reproduces the
 * retail sltiu-bound upward form - law 4 is source-controllable and
 * now REPRODUCED. Judge count equal (144/432 both - the cascade
 * relocates rather than shrinks), but the shape is retail-correct so
 * the mutation STAYS. V-minus1-fill (D[i] = -1): negative, gcc
 * constant-folds to the same 0xff store, no shared pseudo.
 * The remaining 144-word residual clusters: (1) the prologue
 * save/bind permutation + the size-load target reg (a0 vs v1) +
 * the total-in-a0 materialization - allocator/scheduler outcomes;
 * (2) the return-2 path: retail falls THROUGH close(fd)+j-thunk with
 * v0=2 in the j delay slot (the shared k=6 epilogue thunk), ours
 * inverts the fd==-1 branch (bne) and lays return-2 out later;
 * retail's -1 sits in s1, ours in s2 (delta (b), live-confirmed).
 *
 * MUTATION VR2 (inverted guard) - THE WIN: `if (fd != -1) { close(fd);
 * return 2; }` with the create path falling through unguarded closes
 * the ENTIRE return-2 cluster: judge 144/432 -> 107/433 AND the size
 * delta dies (built 1732 = retail exactly). Retail's layout is now
 * reproduced: the guard branches INTO the create path and the
 * close+j-thunk return-2 falls through. The residual is ONE cluster:
 * the prologue save/bind permutation + the size reload target
 * (built lw a0,0x44(sp) + addiu v1,a0; retail lw v1,0x44(sp) + addiu
 * v1,v1 - the t-chain reloads into its carry register) + the sector
 * math cascade - allocator/scheduler outcomes, next window's target.
 *
 * MUTATION M1 split-t (cron-20261027-1248 window): `t = size + 0x200`
 * -> `t = size; t += 0x200;` moves the size reload into t's own home
 * register: built now reloads DIRECTLY into v1 (lw v1,0x44(sp), the
 * exact retail form) instead of through a0. Judge 107/433 -> 106/433
 * (the prologue cluster's reload word matches; the save/bind
 * permutation remains). Mutation KEPT: count-better AND shape-correct.
 * MUTATION M2 hdr-src (same window): extending hdr's last use to the
 * 0x200 copy (`= *(struct S200 *)hdr`) is NEGATIVE - judge 187/432,
 * size 1728 (-4), the exact 0x200 block-move bindings break. Rejected;
 * hdr's death point stays before the first open.
 * The small-run family is decoded: ALL of it is one post-hdr register
 * re-assignment delta - built maps [s1<-0x200-const, s2<-(-1),
 * s3<-cached D_800693F4 address], retail maps [s1<-(-1), s2<-0x200,
 * no cache] (fresh a1 materialization per write/read call). The -1
 * register is the root: retail reuses hdr's freed s1, our build
 * assigns s2 - a global-alloc outcome (find_reg pass-0 reuse), the
 * twin's find_reg replay is the mechanized next step.
 *
 * PROLOGUE CLUSTER DECODED (cron-20261027-1518 window): the 83-word run
 * is FOUR coupled compiler-internal sub-deltas. (1) the alignment test:
 * our `t % 0x2000 != 0` folds to andi/beqz; retail recomputes
 * trunc-align(t) with a SECOND full signed-division idiom + beq (7
 * words) - the recomputed division is cse-DISTINCT from line 80's
 * (needs a reload-time copy pseudo; P1 literal repeat and P2 copy
 * variable both merge, 425/432 built 1728 each, banked negative). (2)
 * the save/bind order: retail saves (ra,s3,s1) first, ours interleaves
 * - the BB's priorities are all 1-2, a sched2 tie-break outcome (Law 2
 * domain). (3) the fill register: retail 0xff in a1 with strcpy's arg
 * set up late; ours in a3 with `move a1, a2` hoisted - global-alloc
 * reg-choice. (4) the lo-fold: retail splits (addiu at,at,%lo; addu;
 * sb 0(at)), ours embeds (sb a3,%lo(at)) - expand-time address RTX.
 * The slps twin's retail prologue is structurally identical (same four
 * sub-deltas, -0x68b4 lo) and our v26 build diverges the same way - the
 * slps -4 size shortfall IS the second division. Every residual word of
 * this unit is now attributed; the cluster is one lever deeper than the
 * source, same honest class as the -1 family.
 */
