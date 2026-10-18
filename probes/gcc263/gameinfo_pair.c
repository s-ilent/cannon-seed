/* Probe: the set_game_info/get_game_info C drafts (both boots).
 *
 * Compiled with STOP_AT_ASM=1 tools/cc.sh (cc1 2.6.3-psx + maspsx);
 * word-compared against the TRUE-view decode (tools/deframe.py --payload;
 * repo-external decode scripts, window cron-20261018-1604). Not part of
 * any build target; lives here as matching evidence for gameinfo.c's
 * API pair (docs/TASKS.md windows cron-20261018-1334 and -1604).
 *
 * THE TRUE-VIEW DECODE THESE DRAFTS ENCODE:
 *
 * Setter: slps true 0x80023D98 (0x3B4 to the getter) / sces 0x80023DC0.
 * Getter: slps true 0x8002414C (0x194 = 101 insns) / sces 0x80024174.
 * sces mirrors at +0x28 code / +0xC data, zero real insn diffs.
 *
 * Retail shapes the drafts must reproduce:
 * - base materialized ONCE (lui a1,0x8001) and reused: selector load,
 *   TV_MODE, and the 0xB28..0xB36 C-block accesses are all a1-relative;
 * - record base in v1 (getter, no calls) / s1 (setter, live across the
 *   case-4 helper calls): mission selector routes A 0x800100B8 vs
 *   B 0x800105F0, exactly 0x538 apart;
 * - guard: sll/sra sign-extend of a0, then ori v0,zero,0x11 + sltu
 *   v0,v0,a0 + bnez-to-default (const-first materialized sltu idiom;
 *   rec1 ledger open delta (1) applies here too);
 * - 18-entry jtbl dispatch (slps table TRUE 0x80020314 setter /
 *   0x8002038C getter; entries encode TRUE addresses = the switch-class
 *   de-frame blocker, so these stay drafts until that transition);
 * - setter: the validated cases are REPORT-AND-SKIP - the store lives
 *   on the valid branch (retail sh rides the join-jump's delay slot on
 *   the bnez-taken path); the assert path joins WITHOUT storing. Case 4
 *   is the only report-and-continue member (the name copy runs after a
 *   failed length check too);
 * - setter validations are ALL unsigned-short-masked compares:
 *   andi+sltiu from (unsigned short)val for the <2/<5/<4 cases, and the
 *   subtract form for the ranges - [1,4] as (u16)(val-1) < 4, [-1,3] as
 *   (u16)(val+1) < 5, [-1,0] as (u16)(val+1) < 2;
 * - getter case 12 returns the -1 SENTINEL (retail tail nor/sltiu/negu),
 *   not a boolean 1: super blaster = -1 iff both mission records say -1;
 * - getter: ZERO per-case asserts (only the default, line 404); two
 *   join points - 0x800242CC is a one-insn materialization stub
 *   `move v0,s0`, 0x800242D0 the real epilogue; the lhu cases funnel
 *   through a shared sign-extend trampoline (j 0x800242CC; sra
 *   s0,v0,0x10) living inside case 3's island as fall-through
 *   sharing; the lh cases jump the epilogue directly with
 *   `move v0,s0` in the delay slot;
 * - getter case 12 reads BOTH mission records: returns 1 iff
 *   recA+0x536 == -1 AND recB+0x536 == -1;
 * - getter case 4 returns the record name-buffer POINTER (rec byte
 *   +4), not a load;
 * - the getter's s0 is NOT initialized on the default path (the
 *   retail returns s0 garbage after the non-fatal assert) - so `v`
 *   stays uninitialized in the draft.
 *
 * Field signedness follows the witnessed loads: lh for the selector,
 * LEVEL, PLAY_RECORDING, CLEAR_LEVEL, the RMW halfword and
 * PARTNER_G_NUM; lhu for TV_MODE, record+0x02, the whole C block, and
 * the case-12 SUPER_BLASTER reads (which then sign-extend via
 * sll/sra for the -1 compares).

 * SHAPING LEDGER (STOP_AT_ASM=1 tools/cc.sh, 2026-10-18, window -1719):
 * getter draft 99 insns vs retail 101; setter draft 197 vs retail 237.
 * ALREADY EXACT (getter): routing arm order (bnez-taken = record B via
 * delay ori, A on the fall-through), the sll/sra id guard, the 18-entry
 * dispatch train, the s0-form/trampoline split concept, case 4's
 * pointer return, case 12's full consensus block (addiu -1 / bne /
 * move-delay / nor / sltiu / j / negu-delay), the join-stub + epilogue
 * pair, and the 6-insn default assert block. ALREADY EXACT (setter):
 * the report-and-skip island architecture with the sh in the join-jump
 * delay, all six validation idioms incl. the subtract forms, the RMW
 * case 7 (bnez / j+sh-zero / lhu+or+sh), the case-4 double call, the
 * single join. CORRECTIONS THE COMPILE LOOP CAUGHT vs the 1604 entry:
 * case 12 returns -1 (negu), not 1; validated cases are report-and-skip,
 * not report-and-continue; validations are u16-masked (andi present),
 * so the 1334 signed-range readings ([1,4] etc.) refine to the subtract
 * forms. OPEN DELTAS (ledger, same classes as rec1): (1) guard form -
 * draft sltu v0,a0,18 + beq-over vs retail ori 0x11 + sltu v0,v0,a0 +
 * bne-to-assert (rec1 open delta (1), now witnessed on an 18-case
 * switch too); (2) dispatch table base - draft %hi/%lo pair vs retail
 * lui+addiu absolute (probe-link artifact, -1 insn); (3) getter tail -
 * int v gives the retail move-tail but lets gcc narrow case 3's load to
 * lh (retail keeps lhu+tramp) and adds one scheduling nop at case 15;
 * short v keeps the lhu forms but adds a tail sll/sra promotion (+1);
 * (4) setter value plumbing - retail materializes val into a0 per
 * island (move a0,s0, sh a0,N) and leaves some bnez delays NOP; draft
 * keeps val in s0 and fills delays with the string lui (~-1/island);
 * (5) setter base register - retail reuses a1 (temp) for the config
 * base, draft pays a third callee-save (s2). (3)-(5) are register-
 * allocation/scheduling variance: permuter/flag-lane territory, not
 * source-shape questions.
 */


extern void func_8002DC10(const char *fmt, const char *file, int line);
extern int func_8002DC20(const char *s);
extern void func_8002DC40(char *dst, const char *src);

#define GAMEINFO_FILE ((const char *)0x80020080)

/* setter: slps true 0x80023D98 / sces true 0x80023DC0 */
void set_game_info(short id, short val)
{
    short *base = (short *)0x80010000;
    short *rec = (*base == 0) ? (short *)0x800100B8 : (short *)0x800105F0;

    switch (id) {
    case 0:
        if ((unsigned short)val < 2)
            *base = val;
        else
            func_8002DC10((const char *)0x8002004C, GAMEINFO_FILE, 200);
        break;
    case 1:
        if ((unsigned short)val < 2)
            *(short *)(base + 1) = val;
        else
            func_8002DC10((const char *)0x8002008C, GAMEINFO_FILE, 207);
        break;
    case 2:
        if ((unsigned short)(val - 1) < 4)
            rec[0] = val;
        else
            func_8002DC10((const char *)0x8002019C, GAMEINFO_FILE, 265);
        break;
    case 3:
        rec[1] = val;
        break;
    case 4:
        if (func_8002DC20((const char *)val) >= 0xa)
            func_8002DC10((const char *)0x800201CC, GAMEINFO_FILE, 276);
        func_8002DC40((char *)rec + 4, (const char *)val);
        break;
    case 5:
        if ((unsigned short)(val + 1) < 5)
            rec[7] = val;
        else
            func_8002DC10((const char *)0x80020200, GAMEINFO_FILE, 283);
        break;
    case 6:
        if ((unsigned short)val < 5)
            rec[8] = val;
        else
            func_8002DC10((const char *)0x80020238, GAMEINFO_FILE, 290);
        break;
    case 7:
        if (val == 0)
            rec[9] = 0;
        else
            rec[9] |= val;
        break;
    case 8:
        if ((unsigned short)val < 2)
            *(short *)((short *)base + 0x594) = val;
        else
            func_8002DC10((const char *)0x800200C0, GAMEINFO_FILE, 214);
        break;
    case 9:
        *(short *)((short *)base + 0x595) = val;
        break;
    case 10:
        if ((unsigned short)val < 2)
            *(short *)((short *)base + 0x596) = val;
        else
            func_8002DC10((const char *)0x800200F4, GAMEINFO_FILE, 226);
        break;
    case 11:
        if ((unsigned short)val < 2)
            *(short *)((short *)base + 0x597) = val;
        else
            func_8002DC10((const char *)0x8002012C, GAMEINFO_FILE, 234);
        break;
    case 12:
        if ((unsigned short)(val + 1) < 2)
            rec[667] = val;
        else
            func_8002DC10((const char *)0x800202A8, GAMEINFO_FILE, 313);
        break;
    case 13:
        *(short *)((short *)base + 0x598) = val;
        break;
    case 14:
        *(short *)((short *)base + 0x599) = val;
        break;
    case 15:
        if ((unsigned short)val < 2)
            *(short *)((short *)base + 0x59a) = val;
        else
            func_8002DC10((const char *)0x80020168, GAMEINFO_FILE, 250);
        break;
    case 16:
        if ((unsigned short)val < 4)
            rec[666] = val;
        else
            func_8002DC10((const char *)0x80020270, GAMEINFO_FILE, 305);
        break;
    case 17:
        *(short *)((short *)base + 0x59b) = val;
        break;
    default:
        func_8002DC10((const char *)0x800202E0, GAMEINFO_FILE, 320);
        break;
    }
}

/* getter: slps true 0x8002414C / sces true 0x80024174.
 * Same routing and guard; all 18 islands are validation-free loads.
 * s0-form (lh) cases jump the epilogue directly; lhu cases funnel
 * through the shared sra trampoline; case 4 returns the name pointer;
 * case 12 is the dual-record consensus read. */
int get_game_info(short id)
{
    short *base = (short *)0x80010000;
    short *rec;
    int v;

    if (*base == 0)
        rec = (short *)0x800100B8;
    else
        rec = (short *)0x800105F0;

    switch (id) {
    case 0:
        v = *base;
        break;
    case 1:
        v = (short)*(unsigned short *)(base + 1);
        break;
    case 2:
        v = rec[0];
        break;
    case 3:
        v = (short)*(unsigned short *)(rec + 1);
        break;
    case 4:
        return (int)((char *)rec + 4);
    case 5:
        v = rec[7];
        break;
    case 6:
        v = rec[8];
        break;
    case 7:
        v = rec[9];
        break;
    case 8:
        v = (short)*(unsigned short *)((short *)base + 0x594);
        break;
    case 9:
        v = (short)*(unsigned short *)((short *)base + 0x595);
        break;
    case 10:
        v = (short)*(unsigned short *)((short *)base + 0x596);
        break;
    case 11:
        v = (short)*(unsigned short *)((short *)base + 0x597);
        break;
    case 12:
        if ((short)*(unsigned short *)((short *)base + 0x2f7) != -1)
            v = 0;
        else
            v = -((short)*(unsigned short *)((short *)base + 0x593) == -1);
        break;
    case 13:
        v = (short)*(unsigned short *)((short *)base + 0x598);
        break;
    case 14:
        v = (short)*(unsigned short *)((short *)base + 0x599);
        break;
    case 15:
        v = (short)*(unsigned short *)((short *)base + 0x59a);
        break;
    case 16:
        v = rec[666];
        break;
    case 17:
        v = (short)*(unsigned short *)((short *)base + 0x59b);
        break;
    default:
        func_8002DC10((const char *)0x8002035C, GAMEINFO_FILE, 404);
        break;
    }
    return v;
}
