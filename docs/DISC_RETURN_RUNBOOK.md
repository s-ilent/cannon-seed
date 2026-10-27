# DISC RETURN RUNBOOK (banked cron-20261026-2119)

The oracle-return window's exact sequence. Everything below was re-derived
and re-verified across the offline windows (docs/TASKS.md Log + scripts/
bm_unit_decode/STATE.md are the sources); this file consolidates it so the
return window EXECUTES instead of re-researching. Assumes the standard
session start already ran (probe-first, rehydrate, exec bits, digest gate,
reset to origin/main, worklog tail read).

## Phase A - discs, baselines, witness 8/8 (before anything else)

0. ONE-COMMAND PATH (banked cron-20261027-0219): `sh tools/disc_return.sh
   '<EU .chd url>' '<JP .chd url>'` - every step below with the gates
   inline (foreground downloads, sha256 + byte-size gates, sector-count
   assertions, --per-sector hardcoded, witness gate as the exit code);
   ~9 min, run under a >=600s shell timeout. The manual sequence stays
   below as the fallback/reference.
   OFFLINE-VALIDATED (cron-20261027-0334): the script's disc-free surface
   is proven - usage path exits 2; refusal path fail-fasts (connection-
   refused URL -> curl 7 -> script exit 7 via set -e, NO partial file left
   in disk/); the cp names are exact (`iso9660_extract.py` flattens
   `DRAGOON/G3.EXE;1` -> `DRAGOON_G3.EXE;1` via `p.replace("/", "_")` and
   mkdirs its own outdir); the sector asserts are real (chd_extract writes
   bare 2352-byte sectors: EU 267752 x 2352 = 629752704, JP 267504 x 2352
   = 629169408); baselines/ survives a fresh clone (committed
   /baselines/.gitignore keeps the dir). Still disc-only: download ->
   sha gate -> chd_extract -> iso extract -> witness 8/8.
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
EMPIRICAL PROOF (offline, cron-20261027-0449): the patch was applied
verbatim, all 240 src units compiled through cc.sh pre- and post-patch
(scripts/bm_unit_decode/rule1_inert_diff.py pre/post/diff), and every
object came back byte-identical - zero compile failures either side, the
k=2 units reproduce the byte-verified three-load shape exactly at n=2,
the k=9 exempt unit does not move. The analytic census (k=0 x92 / k=1
x10 / k=2 x2 / k=9 x1) is now confirmed at the object level; only the
whole-image verify gate remains for the landing itself.

## Phase D - judge the slps block-move unit under BOTH prologue regimes

Two candidates carry verdicts: **v26 (the best, guard-inverted, 425/432
built 1728, size -4)** and **v22 (the banked artifact, 426/431 default,
381/433 nosched2)**. Judge BOTH - v26 first (it is the tree's truth), then
v22 (the readouts the pre-banked head/tail files pin):

    python3 scripts/bm_unit_decode/wire_split.py \
        scripts/bm_unit_decode/variants/v26_vr2.c
    make verify TARGET=slps_00270          # expect RED - see NOTE below
    python3 tools/judge_unit.py slps_00270 func_8002ADA0
    # revert, then the v22 artifact:
    git checkout -- config/splat.slps_00270.yaml asm/nonmatchings/func_800272F8.s config/symbols.slps_00270.txt
    rm -f src/func_8002ADA0.c asm/nonmatchings/func_8002B464.s
    python3 scripts/bm_unit_decode/wire_split.py \
        scripts/bm_unit_decode/variants/v22_u_prejoin.c
    make verify TARGET=slps_00270
    python3 tools/judge_unit.py slps_00270 func_8002ADA0
    CC1FLAGS_EXTRA="-fno-schedule-insns2" python3 tools/judge_unit.py slps_00270 func_8002ADA0
    # revert between regimes and before any commit (as above)

NOTE (verify-RED is the expected probe shape, banked cron-20261027-1748):
wiring a NON-EXACT candidate makes the whole-image verify fail - the
first differing byte lands INSIDE the unit's own region (twin: file
0xB3CC = word 2 of 0xB3C8..0xBA8C). That is the wiring building cleanly
with a known-divergent unit, not a broken probe; the judge's mini-link is
the measurement. Verify returns GREEN only after the revert.

STABILITY (six returns, cron-20261027-0748..1748): these readouts have
reproduced byte-identically on every fresh baseline set - re-run D/E only
when a candidate file changed, a new variant landed, or the unit moved.

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

NOTE (offline windows, banked cron-20261026-2349): judge_unit is
sha1-gated on baselines/<t>.bin (judge_unit.py:192-212) - the woven-era
baselines are refused by design, so judge VERDICTS ARE LIVE-ONLY,
return-window material; the compile-side head/tail readouts are the only
offline-checkable half, and the wheelhouse-rebuilt toolchain reproduces
all four pre-banked readouts byte-identical (v22 432/436, twin 433/436;
re-confirmed cron-20261026-2349 after a venv+toolchain rebuild), so the
screening pipeline is trusted on return without revalidation.
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

STATUS (cron-20261027-1748): the twin is PARKED at the m1 candidate -
106/433 default (built 1732 = retail size exactly), 423/433 nosched2
(+12) - with EVERY residual word attributed one lever deeper than the
source, at the gcc 2.6.3 cse.c level (record_jump_equiv's path-sensitive
eq-branch equivalence for the -1 family; fold_rtx's same-reg hash rule
for the second division; see STATE.md). No plain-C lever remains (M1
kept; M2/P1/P2/m3/m4 banked negative), so a Phase E run is a STABILITY
re-run unless a new variant or a cc1 patch lands.

wire_split_twin.py is MEASURED + DRY-RUN VALIDATED on the committed tree
(cron-20261026-2119): giant 7451 lines, twin region 598 lines (5183..5780,
starts "nonmatching func_8002ABC8, 0x40", ends "endlabel func_8002B26C" -
the SAME 598-line shape as slps), tail 5781..EOF -> func_8002B28C.s,
yaml rows 0x3888 / [0xB3C8, c, func_8002ABC8] # 0x6c4 / [0xBA8C, asm,
func_8002B28C] # 0x1340, nine absolute:true data symbols
(D_800693F4, D_80114678..7B, D_801146D8, D_801146F8, D_80114778,
D_801147F8). Idempotent. The 50/50 allocator replay pre-predicts its
cascade; expected deltas = the same three prologue residuals as slps.
OFFSET CORRECTION (cron-20261027-0748, live-window): the script's yaml
rows originally carried 0xABC8/0xB28C - the VA low bits, missing the
+0x800 file-offset shift; the judge then mini-linked 0x800 low and
sliced retail mid-function (a total-mismatch mirage). Fixed in-script
(the docstring's own extents 0xB3C8..0xBA8C were always right); the
rehearsal validated only the line-based giant cut, so run the judge
before trusting any wired split's numbers.

## Phase F - post-judge waves (rewritten cron-20261027-0219; the original text here was stale - it fell for the same stale-payload trap)

The original Phase F listed the memclr family flip and the palette-fade
wrapper quartet as land-next. STALE: both landed 2026-10-24 with the live
oracle - the memclr family flip 14/14 via scripts/land_memclr.sh (all
seven targets GREEN first shot, ratchet 386->520) and the wrapper quartet
e5d23db5 (ratchet ->625) - plus the 0x4B pair family (95ace34a) and the
pair-pool harvests (d6b4bfb7 TransposeMatrix x6 + LIBSN x10; the 0534
_SsUtBuildADSR x8 + SetDQB x4 + Square0/12 x4 wave, ratchet 644/0 now).
Do NOT re-run their recipes - the yaml rows are already c.

What actually remains after the Phase D/E judge loop:
1. census + classifier rerun - the freshly landed rows leave the pool
   and the votes re-derive the next waves; per the 0534 record the
   classifier's candidates are the lane-owned D-MID-ROW graveyard rows -
   do NOT grab them. Exact commands (both default to all eight targets,
   the census output is the classifier's gated input):
       python3 tools/invariant_census.py     # -> build/invariant_census.txt
       python3 tools/split_classifier.py     # -> build/split_classifier.txt
2. the pair pool's remaining exact-unmatched singles: the movstrsi
   block-move class IS the Phase C-E unit pair itself; the rest are
   adjudicated library-class stubs/veneers or lane-owned clusters.
3. slps_00270's two un-carved boot-region memclr copies stay parked on
   the carve question (the scan lane's).
Verify 8/8 GREEN precedes any landing; commit+push per landing.

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
- The RESTORE NOTE helper is IN-REPO and durable: `python3
  tools/append_restore_note.py <digest_capture_file>` (banked
  cron-20261027-0104 after the persistent-layer copy was rollback-eaten a
  third time; forced -restore suffix, DIGEST_EXIT/EXIT lines filtered).
  The exec-bit dance is dead too: cc.sh / witness_check.sh / rehydrate.sh
  carry the executable bit IN the index (same banking), so resets and
  checkouts restore it - no post-reset chmod needed for the entry points.
