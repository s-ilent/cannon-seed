/* Probe: the gameinfo rec1 per-field writer/reader C drafts (both boots).
 *
 * Compiled with tools/cc.sh -S; word-compared against the TRUE-view decode
 * (tools/deframe.py --payload, scripts/true_view_gameinfo.py). Not part of
 * any build target; lives here as matching evidence for the gameinfo
 * family's first C candidates (docs/TASKS.md window cron-20261018-1049).
 *
 * THE TRUE-VIEW DECODE THESE DRAFTS ENCODE:
 *
 * Writer: slps true 0x800242E0 (0x144) / sces true 0x80024308 (0x144).
 * Reader: slps true 0x80024424 (0x1A8) / sces true 0x8002444C (0x1A8).
 * Instruction sequences are IDENTICAL JP vs EU (word-diff proved); true
 * addresses differ by exactly +0x28; only the per-boot data addresses
 * differ (table base, assert strings, assert callee).
 *
 * Entry: 44 bytes at 0x80010008 + idx*44, i.e. 22 halfwords. The case map
 * (decoded from the TRUE jump tables slps 0x8002040C/0x8002056C, sces
 * 0x80020418/0x80020578, 0x49 entries each, 21 wired + 52 default):
 *
 *   case 0x10 e[0]   0x11 e[1]   0x12 e[2]      (a1 stores)
 *   case 0x20 f[0]   0x21 f[1]   0x22 f[2]   0x23 f[3]   0x24 f[4]
 *   case 0x30 f[5]   0x40 f[6]   0x41 f[7]   0x42 f[8]   (f = e + 3)
 *   case 0x50 f[9]   0x51 f[10]  0x52 f[12]  0x53 f[14]  0x54 f[16]
 *   case 0x55 f[18]  0x56 f[11]  0x57 f[13]  0x58 f[15]
 *   default          report(<str>, <name>, 0x1EA writer / 0x241 reader)
 *
 * Halfword f[17] (entry byte 0x28) has NO case in either function; both
 * boots additionally carry ONE DEAD BODY per function (writer sh
 * 0x22(v1) = f[17], reader lhu 0x22(v1) = f[17]) that the table never
 * references - zero j/jal/branch hits across the whole true payload,
 * both boots. The original compiled unit emitted a 22nd store body its
 * own table does not wire; byte-faithful C must reproduce it (open
 * shaping question - a plain 21-case switch emits 21 bodies).
 *
 * STRUCTURAL BLOCKER (why these are drafts, not src/ files yet): every
 * address-bearing encoding in the retail bodies is a TRUE (runtime)
 * address - the case j targets (true epilogue 0x80024414), the assert
 * jal (true 0x8002DC10 slps / 0x8002DA04 sces), the dispatch table base
 * (true 0x8002040C), the assert string pairs. The carve-space build
 * links at carve addresses, so a C recompile re-encodes every one of
 * those words differently (e.g. case j: retail 0x80024414 vs carve-link
 * 0x80024EC4) and the byte oracle goes red. The current pinned-asm
 * round-trip survives ONLY through splat's blind-anchor labels sitting
 * at the encoded values. These drafts land at the de-frame transition.
 *
 * SHAPING LEDGER (cc.sh -S, 2026-10-18): the draft writer compiles to
 * 101 insns vs retail 81. ALREADY EXACT: the *44 expansion
 * (sll/addu/sll/subu/sll), the lui+ori 0x80010008 base materialization,
 * e in a1 via addu, fid = (short)(id-0x10) via addiu/sll/sra, f = e+3
 * hoisted into the guard branch's DELAY SLOT, the dispatch train
 * (sll/lui/addiu/addu/lw/nop/jr/nop), and the [j epilogue][sh] case
 * body shape. OPEN DELTAS: (1) the guard form - draft emits
 * sltu v0,a0,73 + beq-over (comparison operand order (a0, const),
 * immediate form); retail emits ori v0,zero,0x49 + sltu v0,v0,a0 +
 * bne-to-assert ((const, a0) order, constant materialized in a
 * register). Tried the explicit `if (0x49 <= (unsigned short)(id-0x10))`
 * const-first form: WORSE (120 insns - the explicit if defeats the
 * guard/default merge and adds frame spills). The winning form is
 * probably switch-internal with a comparison-tree order tweak, or a
 * permuter run once the base converges. (2) the dead 22nd store body
 * (see above) has no known C source form. (3) block placement: the
 * retail default/assert body sits after the case bodies; draft keeps it
 * adjacent to the guard.
 */

extern void func_8002DC10(const char *fmt, const char *func, int line);

/* writer: slps true 0x800242E0 / sces true 0x80024308 */
void gameinfo_rec1_set(short id, short idx, short val)
{
    short *e = (short *)(0x80010008 + idx * 44);
    short *f = e + 3;

    switch (id) {
    case 0x10: e[0] = val; break;
    case 0x11: e[1] = val; break;
    case 0x12: e[2] = val; break;
    case 0x20: f[0] = val; break;
    case 0x21: f[1] = val; break;
    case 0x22: f[2] = val; break;
    case 0x23: f[3] = val; break;
    case 0x24: f[4] = val; break;
    case 0x30: f[5] = val; break;
    case 0x40: f[6] = val; break;
    case 0x41: f[7] = val; break;
    case 0x42: f[8] = val; break;
    case 0x50: f[9] = val; break;
    case 0x51: f[10] = val; break;
    case 0x52: f[12] = val; break;
    case 0x53: f[14] = val; break;
    case 0x54: f[16] = val; break;
    case 0x55: f[18] = val; break;
    case 0x56: f[11] = val; break;
    case 0x57: f[13] = val; break;
    case 0x58: f[15] = val; break;
    default:
        func_8002DC10((const char *)0x800203D4, (const char *)0x80020080, 0x1EA);
        break;
    }
}

/* reader: slps true 0x80024424 / sces true 0x8002444C.
 * Same case map; bodies lhu s0, N(e/f) with the sll/sra sign-extract
 * join shared with the assert path; returns the halfword. */
short gameinfo_rec1_get(short id, short idx)
{
    short *e = (short *)(0x80010008 + idx * 44);
    short *f = e + 3;
    short v = 0;

    switch (id) {
    case 0x10: v = e[0]; break;
    case 0x11: v = e[1]; break;
    case 0x12: v = e[2]; break;
    case 0x20: v = f[0]; break;
    case 0x21: v = f[1]; break;
    case 0x22: v = f[2]; break;
    case 0x23: v = f[3]; break;
    case 0x24: v = f[4]; break;
    case 0x30: v = f[5]; break;
    case 0x40: v = f[6]; break;
    case 0x41: v = f[7]; break;
    case 0x42: v = f[8]; break;
    case 0x50: v = f[9]; break;
    case 0x51: v = f[10]; break;
    case 0x52: v = f[12]; break;
    case 0x53: v = f[14]; break;
    case 0x54: v = f[16]; break;
    case 0x55: v = f[18]; break;
    case 0x56: v = f[11]; break;
    case 0x57: v = f[13]; break;
    case 0x58: v = f[15]; break;
    default:
        func_8002DC10((const char *)0x80020534, (const char *)0x80020080, 0x241);
        break;
    }
    return v;
}
