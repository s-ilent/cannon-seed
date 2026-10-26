# DISC RETURN RUNBOOK (banked cron-20261026-2119)

The oracle-return window's exact sequence. Everything below was re-derived
and re-verified across the offline windows (docs/TASKS.md Log + scripts/
bm_unit_decode/STATE.md are the sources); this file consolidates it so the
return window EXECUTES instead of re-researching. Assumes the standard
session start already ran (probe-first, rehydrate, exec bits, digest gate,
reset to origin/main, worklog tail read).

## Phase A - discs, baselines, witness 8/8 (before anything else)

1. Download BOTH discs IN FOREGROUND in one Bash call (backgrounded curls
   get killed -> curl error 23). URLs come from Silent's fresh Discord
   links (the 2026-10-25 refresh expired ~2026-10-26 09:53 UTC; fresh links
   requested again in the cron-20261026-2119 report).
2. Gate BEFORE use (retail provenance, unchanged across refreshes):
   - EU: 382613010 bytes, sha256 98ccd87749918a3ac2e072f1ab9c7649eae567627c3edd62f8154c4b98cf165c
   - JP: 382607234 bytes, sha256 a6025267f57392e178a2feace611a28e5ffd8ee2819358596f0879130fc73d08
3. Extract (~2m40s each; one call per file; 590s timeout):
       python3 tools/chd_extract.py disk/Galaxian3_Japan.chd build/Galaxian3_Japan.bin   # JP=267504 sectors
       python3 tools/chd_extract.py disk/Galaxian3_Europe.chd build/Galaxian3_Europe.bin # EU=267752 sectors
4. ISO extract - `--per-sector` is MANDATORY (the true content join;
   contiguous read = the woven corruption):
       python3 tools/iso9660_extract.py build/Galaxian3_Japan.bin build/iso_jp --per-sector 'SLPS_002.70;1' 'MAINMENU.EXE;1' 'DRAGOON/G3.EXE;1' 'GOURB/G3ORG.EXE;1'
       python3 tools/iso9660_extract.py build/Galaxian3_Europe.bin build/iso_eu --per-sector 'SCES_002.69;1' 'MAINMENU.EXE;1' 'DRAGOON/G3.EXE;1' 'GOURB/G3ORG.EXE;1'
   Copy the eight files to baselines/: slps_00270, mainmenu_jp, g3_jp,
   g3org_jp (JP set) / sces_00269, mainmenu_eu, g3_eu, g3org_eu (EU set).
5. `bash tools/witness_check.sh` -> 8/8 STRICT, or STOP and report.

## Phase B - whole-image verify 8/8 GREEN (pre-landing gate)

`make verify TARGET=<t>` for all eight targets. Suite
`python3 -m unittest discover -s tests` (85 cases). Ratchets
`python3 tools/check_ratchets.py` (644/0 = baseline). All green before ANY
landing. If `make extract` runs anywhere, `git checkout --` the three
carrier blobs afterwards (asm/mainmenu_eu/nonmatchings/func_80034EBC.s,
asm/g3_jp/nonmatchings/func_80050108.s, asm/g3org_jp/nonmatchings/
func_800250FC.s) and re-verify.

## Phase C - land the rule-1 k>=4 generalization (verify-gated; byte-inert proof banked cron-202610262304)

In tools/cc_post.py `_rule1_epilogue_swap`, REPLACE the three-load variant
block (comment "Rule 1 (three-load variant)") with the n-load
generalization; the plain and two-load base cases stay untouched:

    # Rule 1 (n-load variant, n >= 2): [lw $ra][lw $rX]{n}[addu $sp]
    # [j $ra](nop)? -> [lw $ra][lw $rX]{n}[j $ra][addu $sp] (nop
    # absorbed). Generalizes the byte-verified three-load variant
    # (n = 2) to any n >= 2 - the game-code k >= 4 epilogue thunks
    # (func_8002B444-class, k = 6) put the frame release in the branch
    # delay slot. Checked first: the two-load window [lw $rX][addu][j]
    # sits inside this shape and would otherwise fire first and
    # mis-swap.
    i = 0
    while i < len(res) - 4:
        if not LW_RA.match(res[i]):
            i += 1
            continue
        j = i + 1
        while (j < len(res) and LW_SREG.match(res[j])
               and LW_SREG.match(res[j]).group(1) not in ("31", "ra", "29", "sp")):
            j += 1
        if (j - (i + 1) >= 2 and j + 1 < len(res)
                and ADDU_SP.match(res[j]) and JUMP_RA.match(res[j + 1])):
            tail_nop = (j + 2 < len(res) and NOP.match(res[j + 2]))
            res[i : j + (3 if tail_nop else 2)] = (
                res[i:j] + [res[j + 1], res[j]])
            i = j + 2
            continue
        i += 1

(Slice check: window = i..j+1 without the nop, i..j+2 with; replacement =
the n+2 insns res[i:j] + [jump, addu]; the trailing nop is absorbed.)
Byte-inert on the witnessed tree: the C-tree produces exactly ONE k>=4
epilogue (SsSeqCalledTbyT k=9, already sdk-aspsx-exempt) and n<=1 keeps
its own rules; the change activates only for func_8002ADA0's game-code
k=6 thunk. Re-run Phase B (verify all eight, ratchets 644/0, suite),
then commit (type: tools:) + push.

## Phase D - judge v22 under BOTH prologue regimes (slps block-move unit)

    python3 scripts/bm_unit_decode/wire_split.py \
        scripts/bm_unit_decode/variants/v22_u_prejoin.c
    make verify TARGET=slps_00270          # whole-image truth first
    python3 tools/judge_unit.py slps_00270 func_8002ADA0
    # regime 2:
    CC1FLAGS_EXTRA="-fno-schedule-insns2" python3 tools/judge_unit.py slps_00270 func_8002ADA0
    # revert between regimes and before any commit:
    git checkout -- config/splat.slps_00270.yaml asm/nonmatchings/func_800272F8.s config/symbols.slps_00270.txt
    rm -f src/func_8002ADA0.c asm/nonmatchings/func_8002B464.s

cc.sh honors CC1FLAGS_EXTRA (cc.sh:64-66); judge_unit mini-links the one
unit at its retail VA and diffs vs the baseline slice (~2 s). The two
regimes' head/tail readouts are PRE-BANKED (scripts/bm_unit_decode/
v22_head_tail_default.txt 432 insns interleaved / v22_head_tail_nosched2.txt
436 insns retail save-block shape; twin: twin_head_tail_*.txt 433/436) -
diff the judge's actual build against them without re-deriving. If the
judge closes EXACT under a regime: land = yaml split + asm surgery +
src file ONLY - the units' data symbols are ALREADY durable in
config/symbols.curated.txt (the slps eight banked cron-202610260919, the
twin nine banked cron-20261026-2234; the session-local generated-table
append is NOT committed - a scan regen or the build refreshes the
generated tables from curated) - commit-only-on-green, ratchet-gated.
Commit message: type: decode.

Expected deltas (STATE.md LAW 5 + the allocator model, pre-registered):
(a) thunk convention - FIXED by Phase C (retail k=6 swapped vs our
gcc-order + trailing nop); (b) -1/0x200 pair (retail: -1 in s1
prologue-era, 0x200 materialized once into s2; ours: -1 in s2 late, write
ret in s1) and (c) D_8006974C cache (retail re-derives per call, ours
caches in s3) - global-alloc ORDER outcomes (find_reg replay 48/48;
retail's str->a2 and -1->s1 are the same rule under retail's allocation
order); (d) shared -3 err block; (e) return-2 j-thunk layout. Prologue
residuals: (i) bind order (retail s3<-a3 + size load before s2<-a1);
(ii) str->a1 hoist at the strcpy call site (delay slot addu a1,a2,zero);
(iii) size-load interlock (our no-sched2 nop vs retail's binds). The
judge is the only arbiter for (b)-(e).

## Phase E - judge the twin (sces block-move unit)

    python3 scripts/bm_unit_decode/wire_split_twin.py \
        scripts/bm_unit_decode/func_8002ABC8.c
    make verify TARGET=sces_00269
    python3 tools/judge_unit.py sces_00269 func_8002ABC8
    # + the CC1FLAGS_EXTRA="-fno-schedule-insns2" regime run
    git checkout -- config/splat.sces_00269.yaml \
        asm/sces_00269/nonmatchings/func_80027340.s config/symbols.sces_00269.txt
    rm -f src/func_8002ABC8.c asm/sces_00269/nonmatchings/func_8002B28C.s

wire_split_twin.py is MEASURED + DRY-RUN VALIDATED on the committed tree
(cron-20261026-2119): giant 7451 lines, twin region 598 lines (5183..5780,
starts "nonmatching func_8002ABC8, 0x40", ends "endlabel func_8002B26C" -
the SAME 598-line shape as slps), tail 5781..EOF -> func_8002B28C.s,
yaml rows 0x3888 / [0xABC8, c, func_8002ABC8] # 0x6c4 / [0xB28C, asm,
func_8002B28C] # 0x1340, nine absolute:true data symbols
(D_800693F4, D_80114678..7B, D_801146D8, D_801146F8, D_80114778,
D_801147F8). Idempotent. The 50/50 allocator replay pre-predicts its
cascade; expected deltas = the same three prologue residuals as slps.

## Phase F - the staged families (after the judge loop, or interleaved if GREEN)

1. MEMCLR FAMILY FLIP - 12 build-inert src units covering all 14 carved
   copies (per-row one-line yaml asm->c flip + .s deletion + zero renames;
   recipes in each src header + docs/TASKS.md 2026-10-24 1231/1347).
2. PALETTE-FADE WRAPPER QUARTET - word-proven (scripts/prove_wrappers.py
   PASS), D-MID-ROW two-cut splits (recipes in headers + docs/TASKS.md
   2026-10-24 1502).
Census rerun after EACH family lands. Verify 8/8 GREEN precedes each
landing; commit+push per family.

## Standing gotchas

- Never commit: PAT, disc images, baselines, extracted assets. The
  pre-commit hook enforces; never --no-verify (documented asm/-regen
  exception only).
- Session-local wire/extract edits are REVERTED before any commit that is
  not the landing itself; ratchets must always equal the tree.
- judge_unit is a screen, not the oracle - acceptance is whole-image
  `make verify`; nothing judge-side feeds ratchets or progress.
- worklog digest gate + RESTORE NOTE SOP every session; end-of-session
  worklog append (Task ID: cron-<UTC yyyyMMdd-HHMM>) + Discord report
  with <t:UNIX:f> window stamps.
