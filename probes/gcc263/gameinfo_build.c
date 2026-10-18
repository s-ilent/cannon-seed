/* Probe: the gameinfo builder C draft (both boots).
 *
 * Compiled with STOP_AT_ASM=1 tools/cc.sh (cc1 2.6.3-psx + maspsx);
 * word-compared against the TRUE-view decode (tools/deframe.py --payload;
 * repo-external decode scripts, windows cron-20261018-1604 and -1834).
 * Not part of any build target; lives here as matching evidence for
 * gameinfo.c's builder (docs/TASKS.md window cron-20261018-1604).
 *
 * THE TRUE-VIEW DECODE THIS DRAFT ENCODES:
 *
 * Builder: slps true 0x80023AB0 (0x2E8 = 186 insns, ends at the setter) /
 * sces true 0x80023AD8. Single caller: slps 0x80021828 / sces 0x80021844
 * (jal with a NOP delay). SILENT leaf: no calls, no asserts, no jtbl - the
 * first gameinfo member that is true-view-matchable without the de-frame
 * jtbl blocker resolution.
 *
 * Mirror law holds: 734/744 bytes word-identical JP vs EU; the 6 diff
 * words are ALL data plumbing - 2 gp-relative name loads (slps gp+4/gp+8,
 * sces gp+8/gp+0xC) and the 4 table-source addiu immediates (sces = slps
 * - 0x35C). Zero real insn diffs.
 *
 * THE DEFAULTS-STAGER ARCHITECTURE (all stores, no reads except the name
 * global and the table blob):
 * - config head: four halfword stores at 0x80010000..0x80010007 - 0, 0,
 *   0, then -1 via addiu v0,zero,-1 (the base halfword the mission
 *   selector reads: *base == 0 routes record A);
 * - the four 0x2C player rows (0x80010008..0x800100B7, the rec1 pair's
 *   44-byte entries): a 4-iteration loop, 22 halfword stores per row,
 *   f0 via the row walker (0x80010008, advance in the branch delay slot)
 *   and f1..f21 via the rowend walker (0x80010032, offsets -0x28..0,
 *   advance mid-body), constants hoisted pre-loop into 8 registers
 *   (1, 2, 3, 5, 0x7f, 0x2d, -0x64, 0x64). Row defaults:
 *   { 0,0,1,0, 2,3,5,0, 1,0,0x7f,0x2d, 0,-100,-100, 100,100,
 *     -100,-100, 100,100, 0 } - the enumerated record layout the rec1
 *   pair writes (queue: set/get_player_info case-map re-derivation);
 * - the C block (record C head, 0x80010B28..0x80010B37 = base halfwords
 *   0x594..0x59B, the config block the setter validates): 1, -1, then
 *   six zeros - all via the retained base register;
 * - the two-record loop (counter < 2, stride 0x538, record A 0x800100B8 /
 *   record B 0x800105F0; rec and tail pointers DERIVED from the base
 *   register by addiu once loop 1 and the C block are done):
 *   - head: rec+0 = 2 (mission count), rec+2 = -1, the 5-byte default
 *     partner name copied from the boots' .sdata global (slps 0x80066330
 *     = gp+4, sces 0x80065FCC = gp+8; beyond-file tail - the window
 *     [gp, gp+0xD0] is exactly the queue's .sdata dump item: slps
 *     runtime 0x8006632C..0x800663FC, sces 0x80065FC4..0x80066094) as a
 *     word + a byte (lw gp+4 / sw rec+4; lb gp+8 / sb rec+8), rec+0xE =
 *     -1, rec+0x10 = rec+0x12 = 0 - all via the tail walker (rec+0x536,
 *     byte offsets -0x534/-0x532/-0x52e/-0x528/-0x526/-0x524);
 *   - the four table-copy loops: dest rec+0x14 / +0x154 / +0x294 / +0x3D4
 *     (0x140 strides, each addiu from the record pointer), source = the
 *     four contiguous rodata tables (slps 0x8004B97C / 0x8004BABC /
 *     0x8004BBFC / 0x8004BD3C; sces = slps - 0x35C), each 10 iterations
 *     x 0x20 (8 lw/sw pairs, 2x unrolled) = 0x140 bytes. The four
 *     0x140 copies tile rec+0x14..rec+0x513 contiguously - NO overlap,
 *     NO spill past the record (the earlier 0x200/over-read reading is
 *     retired: 10 x 0x20 = 0x140, not 0x200);
 *   - tail: rec+0x514 = 0 (byte), rec+0x51C = 0 (word), rec+0x524 =
 *     rec+0x526 = rec+0x534 = rec+0x536 = 0 (halfwords) - all via the
 *     tail walker (byte offsets -0x22/-0x1a/-0x12/-0x10/-2/0), including
 *     the SUPER_BLASTER consensus field the getter's case 12 reads
 *     (0 = not armed). Gaps (rec+0x515..0x51B, 0x520..0x523, 0x528..0x533,
 *     0x537) stay untouched by the builder.
 *
 * SHAPING LEDGER (STOP_AT_ASM=1 tools/cc.sh, 2026-10-18, window -1834):
 * draft 190 insns vs retail 186. Sequence match ratio 0.745 with long
 * verbatim blocks: the 22-store row-loop body (22 insns), the record-loop
 * head + tail-store runs (12), and all four copy-loop bodies (24/24/21)
 * match the retail instruction stream exactly once alignment is restored.
 * ALREADY EXACT: the config head's mixed form (base store via the
 * retained register, the other three via per-store lui $at expansions),
 * the two-walker row loop with the rowend walker at 0x80010032 and the
 * -0x28..0 offset partition, all 8 hoisted row constants, the C block
 * via the retained base (0xB28..0xB36, fresh ori/addiu for 1/-1), rec
 * and tail DERIVED from the base by addiu, the tail-walker head/tail
 * store forms at the retail byte offsets (-0x534/-0x532/-0x52e/-0x528/
 * -0x526/-0x524 and -0x22/-0x1a/-0x12/-0x10/-2/0), the four 0x140 copy
 * loops (10 x 0x20, 8 lw/sw pairs, source advance in the branch delay
 * slot, dest addiu from the record pointer), and the single-exit jr ra.
 * OPEN DELTAS (multiset diff, all in known classes):
 * (1) +4/-4 addiu: the four table materializations - the probe's
 *     %hi/%lo la pairs (placeholder immediates, probe-link artifact)
 *     vs retail lui+negative-addiu absolutes; two of the probe's pairs
 *     are additionally hoisted above the C block by loop-invariant
 *     motion, paying +2 move insns (retail materializes lazily, one
 *     lui/addiu per copy loop);
 * (2) +1 sh (R) / -1 sh -I(R) and +2 addiu: gcc rebase partitions - the
 *     draft's tail walker gets a canonical (0x5EE) + rebased (0x5EC)
 *     pair where retail keeps one walker (0x5EE, offsets -0x534..0),
 *     and the f21 store rides the rebased walker;
 * (3) +1 lw (R) / -1 lw I(R): the name loads are gp_rel in
 *     both, but the probe's .sdata stand-in sits at gp+0 (retail global
 *     at gp+4 slps / gp+8 sces) - probe-layout artifact;
 * (4) +1 lbu / -1 lb: the retail builder reads the name's 5th byte as a
 *     SIGNED byte (lb); under the pinned -funsigned-char the draft's
 *     signed char global still compiles to lbu (the sb target makes the
 *     sign extension dead). The lb says the retail unit compiled with
 *     signed-char semantics (psyq default or explicit type) - same
 *     store semantics either way; recorded as a decode refinement.
 * (1)-(3) are probe-link/LIM/register-class variance, not source-shape
 * questions: the C source that reproduces the retail ARCHITECTURE is
 * witnessed, and the builder stays the first gameinfo member whose
 * true-view match does not wait on the jtbl blocker.
 */

struct ent { int w[8]; };   /* 0x20 - the table copy granularity */

/* the four contiguous 0x140 rodata tables (slps 0x8004B97C..; sces =
 * slps - 0x35C); each copy loop moves 10 x 0x20 = 0x140 bytes. */
extern const struct ent tbl0[10];
extern const struct ent tbl1[10];
extern const struct ent tbl2[10];
extern const struct ent tbl3[10];

/* the default partner-name global: boots' .sdata beyond-file tail,
 * slps 0x80066330 / sces 0x80065FCC (5 bytes, gp-relative). The probe
 * carries a local .sdata stand-in so cc1 emits the gp-relative loads
 * (content is a placeholder - the retail global's runtime image is the
 * queue's .sdata window dump item). SIGNED char: the retail builder
 * reads the 5th byte with lb (not lbu), so the global's element type is
 * signed char - compile-loop finding, window -1834. */
signed char dflt_name[5] = { '-', '-', 0, 0, 0 };

/* builder: slps true 0x80023AB0 / sces true 0x80023AD8 */
void build_game_info(void)
{
    short *base = (short *)0x80010000;
    short *rec, *tail;
    short *row = (short *)0x80010008;      /* player rows, f0 walker */
    short *rowend = (short *)0x80010034;   /* f1..f21 walker */
    struct ent *dst;
    int i, j, r;

    base[0] = 0;
    base[1] = 0;
    base[2] = 0;
    base[3] = -1;

    for (i = 0; i < 4; i++) {
        row[0] = 0;
        rowend[-21] = 0;
        rowend[-20] = 1;
        rowend[-19] = 0;
        rowend[-18] = 2;
        rowend[-17] = 3;
        rowend[-16] = 5;
        rowend[-15] = 0;
        rowend[-14] = 1;
        rowend[-13] = 0;
        rowend[-12] = 0x7f;
        rowend[-11] = 0x2d;
        rowend[-10] = 0;
        rowend[-9] = -100;
        rowend[-8] = -100;
        rowend[-7] = 100;
        rowend[-6] = 100;
        rowend[-5] = -100;
        rowend[-4] = -100;
        rowend[-3] = 100;
        rowend[-2] = 100;
        rowend[-1] = 0;
        row += 22;
        rowend += 22;
    }

    base[0x594] = 1;
    base[0x595] = -1;
    base[0x596] = 0;
    base[0x597] = 0;
    base[0x598] = 0;
    base[0x599] = 0;
    base[0x59a] = 0;
    base[0x59b] = 0;

    rec = base + 0x5c;                     /* record A: 0x800100B8 */
    tail = base + 0x2f7;                   /* rec + 0x536: 0x800105EE */

    for (r = 0; r < 2; r++) {
        rec[0] = 2;
        *(short *)((char *)tail - 0x534) = -1;               /* rec+2 */
        *(int *)((char *)tail - 0x532) = *(int *)dflt_name;  /* rec+4 */
        *(signed char *)((char *)tail - 0x52e) = dflt_name[4];  /* rec+8 */
        *(short *)((char *)tail - 0x528) = -1;               /* rec+0xE */
        *(short *)((char *)tail - 0x526) = 0;                /* rec+0x10 */
        *(short *)((char *)tail - 0x524) = 0;                /* rec+0x12 */

        dst = (struct ent *)((char *)rec + 0x14);
        for (j = 0; j < 10; j++)
            dst[j] = tbl0[j];
        dst = (struct ent *)((char *)rec + 0x154);
        for (j = 0; j < 10; j++)
            dst[j] = tbl1[j];
        dst = (struct ent *)((char *)rec + 0x294);
        for (j = 0; j < 10; j++)
            dst[j] = tbl2[j];
        dst = (struct ent *)((char *)rec + 0x3D4);
        for (j = 0; j < 10; j++)
            dst[j] = tbl3[j];

        *(char *)((char *)tail - 0x22) = 0;                  /* rec+0x514 */
        *(int *)((char *)tail - 0x1a) = 0;                   /* rec+0x51C */
        *(short *)((char *)tail - 0x12) = 0;                 /* rec+0x524 */
        *(short *)((char *)tail - 0x10) = 0;                 /* rec+0x526 */
        *(short *)((char *)tail - 0x2) = 0;                  /* rec+0x534 */
        *(short *)((char *)tail - 0x0) = 0;                  /* rec+0x536 */

        rec = (short *)((char *)rec + 0x538);
        tail = (short *)((char *)tail + 0x538);
    }
}
