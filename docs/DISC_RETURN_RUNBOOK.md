# DISC RETURN RUNBOOK (banked cron-20261026-2119; Phases C-G rewritten cron-20261101-0736; Phase H added cron-202611042128)

The oracle-return window's exact sequence. Phases A/B are the standing
mechanics; Phases C-F are the OWNER-GATED/parked landing queue (the
2026-10-27/28 phases landed with the oracle returns - the rule-1 n-load
generalization is in tools/cc_post.py, GsMapModelingData sits as c rows in
all six game yaml files - and the block-move twin pair stays parked at its
banked ceilings, so the stale payloads were rewritten out per this file's
own convention). Phase H is the CURRENT judge-prep queue: the five parked
SsVabOpenHeadWithMode drafts (21-25) with the exact judge sequence, the
per-draft expected pairs, and the landing gate. Sources: docs/TASKS.md
Log, the parked drafts' headers (THE AUTHORITATIVE per-draft records),
scripts/bm_unit_decode/STATE.md. Assumes the standard session start already
ran (probe-first, rehydrate incl. the baseline_audit table, digest gate,
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
   EARLY-EXIT: an already-witnessed tree exits 0 before downloading.
   Links die in ~24-35h; probe both with `curl -sI` first - 404 = oracle
   DOWN, leave Phase A, do offline work (Law Zero), never hold.
1. Download BOTH discs IN FOREGROUND in one Bash call (backgrounded curls
   get killed -> curl error 23). URLs come from Silent's fresh Discord
   links (the cron task carries the current set; every fresh link set is
   issued with its own provenance gates below - verify they still match
   the task sheet before trusting the download).
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
   DISC-FREE REHEARSAL PATH (banked cron-202611040358, nineteenth
   rehearsal): rm -rf build/src, 8x `make build TARGET=<t>` one target
   per call foreground - all eight images byte-exact against the
   committed TRUE oracles - then `cp build/<t>.bin baselines/<t>.bin`.
   THE .bin EXTENSION IS MANDATORY: witness_check.sh reads
   baselines/${t}.bin, and an extension-less cp leaves the rollback's
   woven-era dumps in place while witness keeps reporting 0/8 (the
   dump files are the same SIZE as the true images, only the bytes
   differ).
5. `bash tools/witness_check.sh` -> 8/8 STRICT, or STOP and report.
   Re-run `python3 tools/baseline_audit.py` after provisioning: the
   session-start table must flip from 0 MATCH / 8 MISMATCH (the retired
   woven-era dumps) to 8 MATCH before any judge or landing.

## Phase B - whole-image verify 8/8 GREEN (pre-landing gate)

`make verify TARGET=<t>` for all eight targets, one at a time, foreground
only (single-session rule: `ps aux | grep -E 'build.sh|verify.sh|land_wave'
| grep -v grep` first - if another agent is mid-window, monitor read-only
and take no build). Suite `python3 -m unittest discover -s tests`
(133 cases). Ratchets `python3 tools/check_ratchets.py` - counts must
EQUAL config/ratchets.json (unknown_function 809 / unknown_data 150 at the
cron-20261101-0736 rewrite; recompute from the tree after every landing -
higher is a regression, lower lowers the baseline in the SAME commit).
All green before ANY landing. If `make extract` runs anywhere,
`git checkout --` the three carrier blobs afterwards
(asm/mainmenu_eu/nonmatchings/func_80034EBC.s,
asm/g3_jp/nonmatchings/func_80050108.s,
asm/g3org_jp/nonmatchings/func_800250FC.s) and re-verify.

## Phase C - the func_8006AF70 row (the SSINIT member, g3_eu; OWNER-GATED)

State (round-7 ceiling, decision brief cron-20261101-0507): the row sits
at SIZE 1424 = row, DIFF 4 - c5's lui/lw/beqz/beq reg fields carry the $5
pin where retail carries $v1 - and no source-shape lever beats that
ceiling (round 7 closed the ladder: plain v5 and pin-$3 merge wholesale;
b33's reorder breaks retail block order; b34's opaque load binds $5 =
zero gain; b35's $3-bound load re-merges downstream). Draft:
scripts/deferred_func_8006AF70_r5.c (r3/r4 and probes b1..b35 are the
banked ladder history).

- **OPTION A - the full 9-word asm island.** Replace c5's chain body
  with one byte-emitting asm covering the WHOLE chain (the banked law
  makes partial opacity impossible). Byte-retail by construction; one
  judge run expected EXACT. Cost: the 9 words are no longer
  compiler-derived C. Precedent: handwritten units are an accepted class
  for ASM ROWS; an asm island INSIDE a judged C row is the new variant -
  visible, honest, per-file reversible. The chain is frozen retail (psyq
  SSINIT), no maintenance.
- **OPTION B - the cc_post reg-field fixup class.** A marker-scoped
  post-pass rule rewriting ONLY the four reg fields in the built asm.
  The whole function stays compiler-derived; the 4 words become
  post-processed. Cost: a byte-REWRITE class is heavier than every
  existing cc_post rule (all current rules only reorder side-effect-free
  pairs) - permanent tooling whose barrier, once built, lowers for future
  cases. Semantically safe HERE (v5's chain-local live range replaces
  only the dead v1 value on c5's path), and the judge still witnesses the
  rewrite by diff.
- **OPTION C is NOT a landing.** Under the whole-image oracle a C row
  differing by 4 words makes g3_eu verify exit 1. C's real content: leave
  the row PARKED until the owner picks A or B.
- THE CALL IS THE OWNER'S. No call in hand -> skip this phase entirely,
  do NOT stage (staging (yaml 0x4B770 flip + src copy) must land in the
  SAME window it is staged in, or be reverted per the gates).
- WITH a call in hand: stage, `make verify TARGET=g3_eu` GREEN,
  `python3 tools/judge_unit.py g3_eu func_8006AF70` (live-only verdicts -
  judge_unit is sha1-gated on the TRUE baselines), commit type: match.
- THE COMPOSITION RIDING THIS LANDING (banked cron-20261031-1136/1406 +
  1525): the row's C file adopts SsSetTickMode (0x8006af70) / SsStart
  (0x8006b380) / SsStart2 (0x8006b3a0) / SsEnd (0x8006b3c0) / SsQuit
  (0x8006b464) + the three tick statics (_snd_seq_t_max 0x80171e08,
  _snd_seq_tick_mode 0x800aba50, _snd_seq_no_tick 0x800aba54); the five
  libspu labels (_spu_RXX 0x800AB0B8, _spu_tsa 0x800AB0B4,
  spu_timeout_fmt 0x800221C4, spu_timeout_wait_reset 0x800221D4,
  spu_timeout_wait_wrdy 0x800221E4) adopt via the scan and
  src/func_800642A0.c takes the rename (7 D_ tokens refund); the AC04
  split fix rides (Phase D step 1); expected ratchet refund 150 -> 143
  recomputed from the tree - `make ratchets` is the arbiter, lower the
  baseline in the same commit.

## Phase D - the func_8006AC04 init row (SsInit/SsInitHot shared body) - LANDED (cron-20261101-1028, 16b1e80e)

LANDED: judge EXACT 332/332, whole-image 8/8 GREEN, ratchets 809/150 ->
824/172. The split fix preceded the C (yaml 0x120 -> 0x14C, the
data_8006AD24 epilogue reclassification); the row landed as the sixteenth
real-decompiled-C game function with the seven-round probe ladder's
source-shape laws in the commit message; SsSetTableSize stays HELD for
the psylib lane. Historical state:

State: scripts/deferred_func_8006AC04.c carries the draft + the six-step
matching plan (split fix = step 1). The row's real extent is 0x14C, not
the listed 0x120 - the "data" tail data_8006AD24 is the function's own
epilogue (jal GetVideoMode + sw into the held PAL/NTSC selector D_800ABA44
+ sw zero into SsSeqCalledTbyT_guard, then the epilogue mirroring the row
prologue). D_8006AD24 is unreferenced anywhere in the tree, so
re-classifying breaks nothing (banked cron-20261031-1525).

1. The split fix: yaml row extent 0x120 -> 0x14C, the data label
   re-classified to the function body. No C change.
2. The C draft lands from scripts/deferred_func_8006AC04.c.
3. SsInit = 0x8006AD50 / SsInitHot = 0x8006AD70 are already banked INERT
   in config/symbols.curated.txt (g3_eu scope; the e8b42810 polarity
   chain) - the witnessed re-scan applies them (row-start name; the
   second glabel walks the shared-alias path). SsSetTableSize
   (func_8006AD90) stays HELD - the psylib lane-owner flag.
4. `make verify TARGET=g3_eu` GREEN -> judge live -> commit type: match;
   ratchets recomputed from the tree.

## Phase E - the svm init func_80067690 (_svm_damper, g3_eu) - LANDED (cron-20261101-1143, eb874cc1)

LANDED: judge EXACT 1080/1080, whole-image 8/8 GREEN, ratchets 828/278.
The walk row split (head 0xACC asm + the 0x438 c row); the head's
interior func_80052038 -> func_80052038_2 (the collision pass). The
~25-round probe ladder's source-shape laws are banked in the landed
file header (src/func_80067690.c) and the match commit message; the
intermediate ladder state is parked at scripts/deferred_func_80067690_ladder.c.
REMAINING here: the rename claim (_svm_damper) - still lane-owner-gated
on the omf_pubsyms publics-parser pin below. The cross-target twin
census for this function is a follow-up decode (the g3_jp 0x80067640
name collision is coincidental, not a twin).

Historical state: scripts/deferred_func_80067690.c carries the draft + six-step plan.
Identity PROVEN _svm_damper (not SpuVmInit) by the psyq row-stream
kind-0x30 walk + the def-row offset math (cron-20261101-0536; the VMANAGER
truncation was the 3-kind walk breaking at the first 0x30 row; 80/80 rows
parse, the ALIAS? class is the compilation-group model). Single caller:
the SSINIT body func_8006AC04 at 0x8006ACB0 (delay ori $a0,$zero,0x18 -
max_voices = 24). The byte-compare precedent: retail is NOT a byte-
verbatim 3.3 VMANAGER build - the game's own cc1 2.6.3-PSX compiled it
(same class as the landed func_800642A0).

1. Step 1's yaml split touches the func_80066BC4 walk row - the
   glabel_collision_pass must handle its ~40 interior labels; run the
   pass and re-verify before judging.
2. Steps per the draft header; judge live; verify GREEN; commit
   type: match; ratchets recomputed.
3. The rename claim needs the omf_pubsyms publics-parser pin first (the
   symbol-table walk stops early - only 2 of VMANAGER's 44 publics carry
   0x0c offset rows today; sdk_members.py claims ambiguous at 0x80066E5C,
   a different interior start in the same row). No rename without it.

## Phase F - the func_80084924 cluster (mainmenu_jp; the LIBCD ISO9660 family)

State: the offline decode is COMPLETE (cron-20261101-0507/0621) - five
units + both true heads, structure map + six-step plan banked. Five parked
drafts: scripts/deferred_func_8007796C.c (fn2, the cached-dir lookup
leaf), deferred_func_80077CD4.c (the staged directory-stream loader),
deferred_func_80077A18.c (CD_cachefile, the raw-ISO9660 record parser into
the 0x40-entry cache), deferred_func_8007736C.c (CdSearchFile, the path
resolver), deferred_func_80077678.c (CD_newmedia, the PVD reader + root-dir
indexer; its tail IS the asm row's head fragment). The landing set adds
two undrafted units: the 0x20 match leaf (0x80077654, the strncmp-12
ISO9660 8.3 matcher) and memcpy_iso9660 (the func_80077D40 interior, the
family's qualified name, 7 own-row curated entries one per target).

Remaining steps of the banked six-step plan:

1. STEP 1 - the data_8008433C spill audit on TRUE baselines ONLY
   (deframe/retype on witnessed trees; the --framing-rows trap is banked).
   The real unit includes the preceding 0x4b8 "data" row - real code
   mis-typed data, the intr-cluster precedent. Runtime span 0x5E8 = carve
   0x4B8 + 0x130 (one sector's framing).
2. STEP 6 - yaml split into per-function rows + C rows from the drafts +
   judge on the live oracle + the memcpy_iso9660 rename riding (the
   mainmenu_jp interior alabel is documented for this parent-row split
   fix). One target (mainmenu_jp), one landing commit, verify GREEN, 
   ratchets recomputed.

Landing-critical facts (banked, preserve them in the C):
- fn3's gate is a PLAIN bnez: the C tested `if (!CD_cachefile(id))` but
  CD_cachefile returns -1 (never 0) on failure, so "CdSearchFile: disc
  error" is unreachable dead retail code; the C draft must preserve the
  `== 0` test exactly.
- The component walk requires EMPTY-NAME SENTINEL HOPS (fn2(id, "") at
  every '\\' - each dir's table carries a name_len-0 self marker; the
  sentinel's stream-side construction is loader-family material).
- The cache search is strncmp(rec_name, needle, 0xC) == 0 through the
  0x80077654 leaf - two matchers for two name spaces (fn2's repacked
  table names vs fn3's raw ISO9660 cache names).
- The row is DRIFTED (yaml name 0x80084924 vs listing head 0x80077824):
  the yaml names sit +0xCFD0/+0xD100 above the listing heads and the
  delta grows exactly 0x130 over the single 0x58000 sector boundary -
  the second Witness-A-class data point; reconciling the scan's address
  law vs the encoded-call space stays de-frame-lane material
  (coordination-gated, NOT this landing's problem).

## Phase G - the post-landing loop (every landing, every window)

1. `make verify TARGET=<t>` GREEN before the next landing; `make ratchets`
   after it - counts equal baselines, refunds lower the baseline in the
   same commit.
2. Census re-derivation after batch landings:
       python3 tools/invariant_census.py     # -> build/invariant_census.txt
       python3 tools/split_classifier.py     # -> build/split_classifier.txt
   The freshly landed rows leave the pool and the votes re-derive the
   next waves. The classifier's graveyard candidates and the 43
   SIZE-wrong swarm are LANE-OWNED - do not grab.
3. The wave-pool re-rank: `python3 scripts/wave_offline_census.py
   --parents` (pool 150 waves at the cron-20261101-0355 re-rank; the
   pool's entire independent own-row set is the intr-family 13 -
   lane-owned; everything else is parent-bound interior material - new
   wave decodes pay off only as by-products of parent work).
4. Commit+push per milestone (type: match / tools: / docs: / scan: /
   config:, lowercase summary); worklog append (Task ID: cron-<UTC
   yyyyMMdd-HHMM>) + the docs/TASKS.md window section in the same push;
   Discord report with `window <t:UNIX:f> -> <t:UNIX:f>` stamps.

## Phase H - the SsVabOpenHeadWithMode landing (g3org_jp row 0x48864, extent 0x448; the five parked drafts 21-25; added cron-202611042128)

The LIBSND VS_VH .text+0x90 member body: vab slot allocator + VH head
parser + SPU placer. Identity PROVEN (sdk_members.py unique placement +
sig-db agree x8); the full decode + shape-law ladder is banked in
docs/TASKS.md (cron-202611031258 -> cron-202611042013) and in each draft
header - the headers are the authoritative records, this phase carries the
SEQUENCE. Ladder state: draft1 216/226 @ 904 -> draft20 151/274 @ 1096
(SIZE-exact vs the row, judged live at cron-202611041243); drafts 21-25
attacked the remaining levers offline through the outage and are parked
JUDGE-DEFERRED (oracle down since 2026-11-04 ~05:59 UTC). Row facts: the
g3org_jp yaml row [0x48864, asm, func_80068064] (config/splat.g3org_jp.yaml
line 723); the pinned-member entry `SsVabOpenHeadWithMode = 0x80068064; //
type:func (pinned member row)` in config/symbols.g3org_jp.txt (line 255)
and the registrar src/g3org_jp/func_80068030.c call re-point are ALREADY
committed (453fa4ed) - the landing changes ONLY the yaml row + the src
addition (the landed siblings SsVabOpenHead/SsVabOpenHeadSticky kept their
pins; this one keeps its too).

### H.1 - the offline lever ledger (validated cron-202611042128, all six drafts rebuild)

The outage-window measurement method, reproducible on any clean tree with
no baselines and no oracle:

    STOP_AT_ASM=1 MASPSX_UNIT_FLAGS="--addiu-at on" \
      tools/cc.sh -o /tmp/dN.o probes/gcc263/SsVabOpenHeadWithMode_draftN.c
    # -> /tmp/dN.mas.s; then either:
    #  (a) draft-vs-draft lever isolation:
    diff /tmp/dN-1.mas.s /tmp/dN.mas.s          # delta must be EXACTLY the lever
    #  (b) region word compare vs the retail row column:
    LD_LIBRARY_PATH=$TOOLROOT/usr/lib/x86_64-linux-gnu \
      python3 scripts/word_diff.py /tmp/dN.mas.s \
      asm/g3org_jp/nonmatchings/func_80068064.s 0x80068064 0x800684AC

THE SCALE LAW (banked cron-202611042128; ROOT-CAUSED AND REWRITTEN
cron-202611050728): the banked "+14 = the live judge's mini-link expands
the HI16/LO16 pairs" was a MISDIAGNOSIS - the mini-link expands NOTHING.
The +14 words are the maspsx `--addiu-at` KNOB DELTA: the in-repo
maspsx_delay_slot.patch's addiu-at expansion materializes every bare-symbol
load AND store through $at (loads 3->4 words: lui/addiu %lo/addu/access-0;
stores bare->4 words: lui/addiu/addu/sw 0($at) = retail's exact form), and
+14 words is that delta on THIS unit's site count. The judged windows ran
knob-ALIVE; a stale-HEAD rehydrate (pre-6b, cron-202611050728 failure
mode: rehydrate.sh at 7623cd2e had no step 6b, the clones kept the old
patch, and maspsx's parse_known_args SILENTLY DROPS the --addiu-at flag)
leaves the same commands measuring knob-DEAD = -14 words. maspsx_flags.txt
already carries `unit:SsVabOpenHeadWithMode --addiu-at on` (judge-confirmed
cron-202611041013), so the flags were always right - only the PATCH STATE
flips. RE-RUN rehydrate after every reset --hard origin/main (idempotent);
verify the knob with `grep -c addiu-at /home/z/my-project/tools-src/maspsx/maspsx.py`
(need >= 1 in BOTH clone locations).

THE TRUE LIVE-SIZE LAW (measured cron-202611050728, validated twice): the
judge's SIZE = the mini-linked .r_<rom> section bytes, and the WHOLE judge
pipeline minus the retail-bytes comparison reproduces OFFLINE with zero
oracle:

    MASPSX_UNIT_FLAGS="--addiu-at on" tools/cc.sh -S -o build/judge/wN.o probes/gcc263/SsVabOpenHeadWithMode_draftN.c
    python3 tools/stage_c.py build/judge/wN.mas.s build/judge/wN.r.s 48864 0 ""
    $TOOLROOT/usr/bin/mipsel-linux-gnu-as -march=mips64 -mabi=32 -EL -G0 \
      -I include -I asm/nonmatchings -I asm/g3org_jp -o build/judge/wN.o build/judge/wN.r.s
    # then mini-link exactly as judge_unit.py does (SECTIONS { . = 0x<va>;
    # .r_48864 : { *(.r_48864) } } + the symbols.<t>.txt/curated prelude +
    # the two-pass undef_syms.py fallback), objcopy -O binary --only-section
    # .r_48864, stat the .bin. Validation: draft1 904 = judged 904 EXACT;
    # draft20 knob-alive 1096 = judged 1096 = THE ROW EXACT.

The knob-ALIVE recalibration of the ladder anchors (one pipeline, one
counter - the gas word_diff words; the historical w-counts below were
knob-dead or objdump-based and do NOT compare):

    draft20  268 w   147/274   linked 1096 = THE ROW (validates the 1243 live anchor)
    draft38  266 w   175/274   linked 1092 (-4 B = ONE word short of the row)

THE AT-CHAIN CLASS ITEM IS CLOSED AS A TOOLING ITEM (cron-202611050728):
retail's six 4-word $at store forms are maspsx's addiu-at STORE expansion
(the patch's store branch emits exactly lui at,%hi / addiu at,at,%lo /
addu at,at,<idx> / sw <reg>,0x0($at)) - NO source-shape change exists or
is needed; the "explicit pointer/intermediate" hypothesis is moot. With
the knob alive the six sites (7876C/78704/787B0/FB6C/FB24/FAE0) already
emit retail's form through the judge pipeline; the offline proxy only
undercounts them when the knob is dead. The historical ledger below is
KEPT UNCHANGED as the knob-dead-era record of the source-shape levers
(their DELTAS were measured within one knob state and remain internally
consistent); its live-size predictions are superseded by the recipe above.

    draft20  260 w (1040 B)   live 1096  (the judged anchor, cron-202611041243)
    draft21  262 w (+2)       live 1098 expected (the rule17 trampoline)
    draft22  262 w ( 0)       live 1098 held   (the slt re-shape is reg-neutral)
    draft23  260 w (-2)       live 1096 again  (the de-share funds the trampoline)
    draft24  260 w ( 0)       live 1096
    draft25  260 w ( 0)       live 1096  (".text 0x410 = 1040 unchanged")
    draft26  260 w ( 0)       live 1096  (the end_addr revert, see H.3)
    draft27  260 w ( 0)       parked NEGATIVE (the m-web fifth-routing; the file builds machine-identical to draft26)
    draft28  260 w ( 0)       live 1096  (the condition-chain re-shape; POSITIVE, see H.3)
    draft29  260 w ( 0)       live 1096  (the magic-check temp pin; region-positive, metric-neutral, see H.3)
    draft30  264 w (+4 objdump, +1 REAL)  live 278-predicted (+1 word over the row; the +4 objdump delta is 16-byte section-align padding: 1044 real bytes round to 1056 - the word_diff counter says +1). THE +1 = the loop-bound copy (addu a3,v1,zero - retail HAS the word, the built never did). THE FUND: the built's standalone base def addu $19,$4,32 has NO retail counterpart (retail's base rides the a2-chain: s3 := a2 at the m-check delay) - the copy's SIZE debt rides the same judge-gated a2-chain lever that gates the 12/12 window closure; the SIZE verdict is LIVE-ONLY (H.5 arbitrates)
    draft31  264 w ( 0)       the idx-home pin - reg-neutral (see H.3)
    draft32  264 w ( 0)       the offset-temp pin - reg-neutral (see H.3)
    draft33  264 w ( 0)       the pre-branch reorder (k=0/idx=0 delay-fill) - reg-neutral + SIZE-neutral (see H.3)
    draft34  264 w ( 0)       the ap reorder - SIZE-neutral (see H.3)
    draft35  265 w (+1 REAL, retail-backed)  the total=0 sink-barrier - live 276-predicted (+2 over the row with the copy; the conservative form is draft34 if the H.5 SIZE gate refuses) (see H.3)
    draft36  260 w (-2 objdump, -3 insns)  the head-loop DO-WHILE RE-SHAPE - the for-form's rotated top guard (slt $2,$5,$8 / beq $2,$0,<exit> / dead-sll delay) dies; the entry test becomes retail's do-while shape (end= / slt v0,a3,a1 / bnez v0,+11 / nop); metric-neutral 169/274 (the removed words were all wrong), live-predicted 274 = THE ROW (the d35 +2 debt and the guard's -2 objdump cancel); frame UNCHANGED 1080/1032 (no ghost-reservation shift this time) (see H.3)
    draft37  260 w ( 0)       the 787B0 SPLIT-TEMP EXTEND + the BOUND REMAT ORDER (the ninth $2 web) - 170/274 (+1: the bound word 1004a827 pairs at retail's 0x8006829C slot; the extend pair moves OUT of the store into its own pinned statement so the bound def's list position lands between extend and store) (see H.3)
    draft38  260 w ( 0)       the END= OPERAND-ORDER FLIP (end = ap + nv*4 -> end = nv*4 + ap; gcc preserves source addition order in the commutative-plus encoding) - 171/274 (+1: the end= word 00453821 retail-exact; the whole entry-test group aligns inside the equal blocks). THE POST-LOOP POSITIONAL SET IS CLOSED (see H.3)

Every one of these numbers reproduced on cron-202611042128 from the
committed drafts; re-derive them if a draft header ever disagrees.
Offline aligned-match vs the row column (scripts/word_diff.py, the
standalone-as config - cross-config numbers do NOT compare): draft25
152/274, draft26 153/274 (the end_addr check's sltu now retail-class),
draft28 156/274 - the condition-chain re-shape, NET +3 at the same
built-word count (253 on the word_diff built-words counter for both
d26 and d28; the ledger column above uses the H.1 rebuild counter -
the DELTAS agree, the absolute bases differ by the count method).
draft29 156/274 (metric-neutral, four magic-check words region-exact,
see H.3). The cron-202611050228 outage ladder: draft30 161/274 at 254
built words (+1 = the copy; NET +5 - the loop-bound copy form: the
m2 copy, the p home into the freed v1, the lbu/sw bases, the compare
and the p+=16 all ride the copy choreography), draft31 164/274 (NET
+3 - the idx-home pin: sw $16,8($3) and the idx=0/idx++ dsts flip
retail-exact, total's free web KEPT $16 - no eviction), draft32
166/274 (NET +2 - the offset-temp pin: sll dst v0 + addu src2 v0
flip retail-exact). Ladder total that outage window: +10 words.
REJECTED the same window: the w0 -> $5 home pin on the d30 landscape
(160/274, NET -1 - the second consecutive negative, see H.3).
cron-202611050458: draft33 167/274 at 254 built words (NET +1,
SIZE-neutral - the pre-branch reorder: k=0 straight-line before the
blez, idx=0 IN the delay, the blez offset word 0x1860000C retail-
exact; the ENTIRE 16-word loop window 0x8006824C..0x80068288 is one
binary equal block, see H.3), draft34 168/274 (NET +1, SIZE-neutral -
the ap reorder: the ap word 0x27A50010 was already retail-exact via
the gas law, only its position was wrong), draft35 169/274 at 262
objdump words (NET +1, +1 REAL retail-backed - the total=0
sink-barrier holds the post-exit zeroing; live 276-predicted = +2
over the row with the copy). Outage ladder total: 156 -> 169 (+13).
THE OPCODE-CLASS ITEM CLOSED AS A FALSE ITEM the same window: the
"built addu $16,$16,1 / addu $5,$5,1 / addu $3,$3,16 vs retail addiu
x3" residual was a MNEMONIC-TEXT artifact - gcc 2.6.3 emits the
addu-with-immediate TEXT form pre-maspsx, gas assembles it as the
I-type addiu ENCODING (the built .o words 0x26100001/0x24A50001/
0x24630010 are byte-identical to retail; same for the backfill-loop
addu $5,$5,4 / addu $6,$6,2 text forms -> 0x24A50004/0x24C60002);
word_diff (gas+objdump based) had already counted the sites equal.
Zero words at stake; no flag, no shape change needed - do NOT
re-open it.
cron-202611050613: draft36 169/274 at 260 objdump words (NET 0,
-3 insns - the head-loop DO-WHILE RE-SHAPE: the for-form's rotated
top guard dies, the entry test becomes retail's end<ap bnez + nop
form; live-predicted 274 = the row, the d35 +2 debt cancels against
the guard's -2 objdump; frame unchanged 1080/1032), draft37 170/274
(NET +1 - the 787B0 split-temp extend + the bound remat order: the
extend pair moves out of the store into its own $2-pinned statement
(slot4, the ninth disjoint web) so the bound def's list position
lands between extend and store = retail's 0x8006829C slot; the bound
word 1004a827 pairs), draft38 171/274 (NET +1 - the end= operand-
order flip: end = nv*4 + ap puts the scaled temp FIRST in the
commutative-plus encoding, 00453821 retail-exact; the whole entry-
test group aligns inside the equal blocks). Outage ladder total:
156 -> 171 (+15). THE POST-LOOP POSITIONAL SET IS CLOSED: total=0 /
ap / sll16 / sra14 / BOUND / 787B0-store / reads / tp+= / end= /
slt / bne / nop all retail-ordered; the only remaining store-group
delta is the AT-CHAIN CLASS lever (banked below).

THE A2/BASE CHAIN WAVE (cron-202611050959, oracle DOWN - drafts 39-41
measured on the knob-alive recipe; the draft38 anchors 266 w / 175/274 /
linked 1092 reproduced first-pass in this sandbox through the H.1 recipe
plus a mini-link script; all three drafts measured NET-NEGATIVE and are
BANKED AS MAPS, not candidates):

    draft39  268 w   169/274   linked 1100 (+2 over the row)
    draft40  269 w   170/274   linked 1104 (+3 over the row)
    draft41  269 w   170/274   linked 1104 (+3 over the row)

- d39 (one-variable chain: base = vh pre-verdict, += 0x20 at the magic
  join, raw-slot magic-fail index): gcc picked s1 (vabid_s1's freed reg,
  the long-web callee-saved pick) for base's WHOLE web - no split; the
  w0 read rode s1 (hv coalesced into the equal-valued base); the addiu
  landed in the m40-bne delay.
- d40 (two variables: b0 = the a2-episode, base = the explicit copy;
  tp's $6 pin RELEASED): THREE STRUCTURAL SITES PROVEN LANDABLE -
  `move a2,s3` rides the verdict-1 bnez delay (retail 0x80068194 EXACT),
  the 7876C store's value reads a2 (retail sw $a2 EXACT), the +0x20
  emits IN-PLACE `addiu a2,a2,0x20` (retail's word). The short web took
  the caller-saved a2 exactly as designed. FOUR blockers remain:
  (1) the w0 read rides b0's home (lw a3,0(a2)) - hv coalesced into the
  equal-valued b0 pre-mutation, so the a0 copy sank to the magic-beq
  delay (move a0,a2) instead of retail's post-join addu a0,s3 - and the
  magic delay went to the a0 copy instead of the addiu (the addiu then
  rode the m40-bne delay); (2) the m-check bnez's delay STILL went to
  the speculative sll16 (the store's index prep) - the explicit copy
  emitted as a real word AFTER the delay: the d33 immediately-preceding
  law does NOT beat a speculative store-component candidate (the sll16's
  critical path outranks the copy); (3) base's long web took s1 AGAIN
  (vabid_s1's freed reg) not retail's s3 - retail s1 was NOT free at the
  def (the slot web lived there post-rehome); the built's slot-home
  entanglement decides base's pick; (4) d41's first cut forgot the
  (char *) cast on the 78704 store and emitted sra 12 (double scale) -
  fixed, word-count unchanged.
- NET read: the chain trades the read-home words (d38's reads were
  retail-exact via the hv pin because base had a DIFFERENT value there;
  the chain makes them EQUAL and gcc merges the webs) against the three
  structural sites. The lever needs the read-home decoupled from the
  7876C value web (retail keeps three copies of vh alive: s3 staging, a2
  the 7876C/base episode, a0 the read home - the original source had a
  shape gcc 2.6.3 would not coalesce; find it or pin the read address
  web against the merge) before the delay-race and the base-home pick
  can even matter. NEXT-WINDOW SHAPE IDEAS: the 7876C store value as a
  dedicated temp that dies at the store with base's def re-using a2 by
  recycling (not by web equality); or the err-label mid-function
  restructure first (site 0x0314's fall-through mechanic - the a0=0
  block head needs the trampoline ADJACENT, which the end-of-source err
  label can never give).

THE DYING-TEMP RECYCLING WAVE (cron-202611051113, oracle DOWN - drafts
42-45 measured on the knob-alive recipe; the d41 anchors 269 w / 170/274 /
linked 1104 reproduced first-pass through the rebuilt session-local
minilink.sh - the cron-202611050959 copy was lost to the fourteenth
rollback; reconstruction notes: build/judge/ must exist before cc.sh, the
binutils root is tools-local/mipsel-root for as/ld/objcopy LD_LIBRARY_PATH
but NOT exported to cc.sh, and the symbols prelude must strip the
`// type:func` tails judge_unit.py's regex strips):

    draft42  269 w   168/274   linked 1104   NET -2 (the episode pair took A1 wholesale)
    draft43  269 w   164/274   linked 1104   NET -6 (b0 coalesced into hv)
    draft44  268 w   167/274   linked 1100   NET -3 (zero-copy asm, SEMANTICALLY BROKEN)
    draft45  269 w   167/274   linked 1104   NET -3 (the tied-asm form, reads fixed)

- d42 (the route as written: b0's web dies AT the 7876C store, e0 = b0 +
  0x20 the recycle def, base = e0 the m-check copy): the RECYCLE MECHANISM
  WORKS - the in-place addiu appeared (addu $5,$5,32 = the addiu encoding,
  dst=src in-place) - but gcc packed the b0/e0 pair into A1 (the extended
  slot's vacated reg) instead of a2: the verdict-delay copy became a1 := s3,
  the store sw a1, the reads still rode the episode reg. The verdict-delay
  copy's dst FOLLOWS the episode's home.
- d43 (the order flip: hv = vh BEFORE b0 = vh): the READS FLIP RETAIL-EXACT
  (addu a0,s3,zero rides the verdict delay, the w0 read rides a0, the
  post-join reads ride a0) - blocker 1 is FIXABLE - but the UNPINNED b0 was
  ELIMINATED (its def copy vanished, the store reads a0) and gcc emitted an
  extra staging copy (a3 := a0 at the magic-beq delay) to feed e0's def.
- d44 (the free-input asm decoupler: asm("" : "=r"(hv) : "r"(vh))): gcc
  2.6.3 emits NO copy for an empty-template asm's output - the w0 read
  would read the _spu_setInTransfer call's leftover in $4 at runtime =
  SEMANTICALLY BROKEN, banked as a shape-law only (the reads ride $4 with
  ZERO copy words - the shape gcc produces when the value is already in
  the pinned reg).
- d45 (the tied form: "0"(vh) - the match constraint forces the input into
  $4): the copy MATERIALIZES at retail's post-store position (addu
  a0,a3,zero - the cascade src, one wrong word) and the reads ride $4 - the
  read-home decoupling is ACHIEVED at zero extra words - but the asm's
  presence re-packed the episode into a3 (the verdict copy a3 := s3, the
  store sw a3, the +0x20 addu a3,a3,32) and the magic-beq delay went to the
  ori-0x70 (the +0x20 became a real word post-join).
- THE THREE-WAY LAW (measured four ways, BANKED): (1) gcc 2.6.3 canonizes
  each VALUE to ONE register - the FIRST pseudo to carry it in source order
  - and substitutes every later same-value pseudo's def AND uses with that
  reg; web liveness is IRRELEVANT (d42's dying web did not stop it), and
  the substitution cascade re-sources each new copy from the previous
  copy's reg. (2) Register pins hold HOMES but not USES: the $4 pin did not
  keep the reads off the episode's reg in d41/d42 (cse substitutes the
  uses' rtx before allocation); the pin only forces the COPY's existence
  (d43's unpinned b0 lost its copy, d41's pinned hv kept it). (3) An empty
  volatile asm with an output operand is opaque to cse (the reads after it
  ride the output's home) but an empty template emits NO copy (the "0" tie
  is REQUIRED for the dataflow) and its presence perturbs the packing
  around it (the episode's home floated a2 -> a3).
- NET read: the read-home decoupling is ACHIEVABLE (d43 and d45 both put
  the reads on a0) but every shape that does it costs more words elsewhere
  than the ~3 read-region words it gains: d43 kills the episode's copy
  (-4 sites), d45 floats the episode off a2 (-2 sites + the delay
  competition). The retail triple-copy shape (s3 staging + a2 episode + a0
  read home, all three alive, NO coalescing) needs the a0 copy to be born
  BETWEEN the episode's def and its mutation WITHOUT becoming the value's
  canon - the asm decoupler gets the uses right but still re-sources the
  copy through the cascade (a3, not s3). NEXT shape ideas (from the law):
  (a) the episode's def copy is the canon-stealer - make IT the opaque one
  (the tied asm on B0: asm("" : "=r"(b0) : "0"(vh)) as the episode's def -
  the copy a2 := s3 materializes through the tie, b0's uses stay on b0's
  home, and hv's plain copy reads... the recent reaching copy = the asm's
  output = b0's home a2 - the cascade persists); (b) accept the a2 reads
  and recover the words elsewhere (the H.4b built +7 @0x018c block); (c)
  the err-label mid-function restructure (site 0x0314) is INDEPENDENT of
  the chain - run it first next window.

THE ERR-LABEL MID-FUNCTION RESTRUCTURE (cron-202611051113, same window -
drafts 46-47 on the d41 chain landscape; the FIRST POSITIVE of the chain
work):

    draft46  269 w   171/274   linked 1104   NET +1 (the built-only tail GONE)
    draft47  278 w   177/274   linked 1140   record alignment, +11 SIZE (a MAP)

- d46 (the err body moves from the function END to right after the
  0x80000-check fail block, guarded by if(0)): THE TAIL IS MID-FUNCTION -
  [the merged m-check/sltu fail block: sll16/sra16/at-chain/sb][the tail:
  jal setInTransfer / FB20 dec / j epilogue with li -1 IN THE DELAY][the
  FB24 path continues] = retail's arrangement; the sltu check's delay
  carries total=0 (retail's beqz-delay addu s0,zero,zero); the m-check and
  sltu fail blocks TAIL-MERGE into one shared E038-clear block exactly as
  retail; the H.4b built-only +9 @0x041c block VANISHES. Residual wrongs:
  the a0=0 still merges into the tail's jal DELAY (retail: per-entry
  a0=0s + a nop delay - the block-head word at 0x0314 is still missing)
  and the success path carries an EXTRA skip branch (j + li -1 delay = +2
  words) because gcc 2.6.3 does not thread the check's false edge through
  the unreachable err block.
- d47 (the err block NESTED INSIDE the 0x80000-check's true branch, so the
  check's false edge IS the skip): the alignment jumps to 177/274 - THE
  RECORD (d38's 175 was the old best) - the m-check region 0x01d4-0x01ec
  aligns with the fail sequence inline - but gcc DUPLICATED the fail
  sequence (the m-check fail got its own [sra/at-chain/sb/j] copy instead
  of sharing the merged block, the polarity inverted to beq) = +9 words =
  SIZE 1140, +11 over the row. A landing needs SIZE = the row exactly, so
  d47 is a MAP, not a candidate: it proves the 0x01d4-0x0338 region's
  retail arrangement is REACHABLE in gcc 2.6.3 - the open problem is the
  SHARED-block form with the inline arrangement (d46's merge + d47's
  positions).
- NEXT shape ideas (from the pair): (a) d46 + force the a0=0 into the
  merged fail block's HEAD (retail's 0x0314 word) - the arg is
  path-invariant so gcc merges it into the jal delay; making it per-entry
  needs a variable arg (frame risk - the 0x438 frame is retail-exact) or
  an unmergeable tail; (b) d46 + kill the extra skip branch: the check's
  false edge must branch DIRECTLY to the FB24 path - try the err block
  nested but the m-check fail's goto targeting the MERGED block explicitly
  (a second label on the clear block), or accept the +2 and recover in the
  0x018c block; (c) the d47 record says the region can fully align - the
  target shape is d46's word count with d47's positions.

THE HEAD/SKIP WAVE (cron-202611051343, oracle DOWN - drafts 48-51 measured
on the knob-alive recipe in a fresh sandbox; the d46/d47 anchors 1104 and
1140 reproduced FIRST-PASS through the newly committed tools/minilink.py -
the offline SIZE law is now a REPO TOOL after the fifteenth rollback ate
the session-local minilink.sh twice; all four drafts measured NEGATIVE or
NO-OP and are BANKED AS LAWS, not candidates):

    draft48  276 w   167/274   linked 1128   NET -4, FRAME BROKE (regs 9/0)
    draft49  269 w   171/274   linked 1104   ZERO DELTA (the barrier no-op)
    draft50  269 w   171/274   linked 1104   ZERO DELTA (byte-identical to d46)
    draft51  276 w   151/274   linked 1132   NET -20, FRAME BROKE (regs 10/0)

- d48 (the per-path `err_arg = 0` head force + arg barriers): gcc 2.6.3
  did NOT home the plain long in $4 even though b0's a2-episode (the $4
  web) is dead at both fail sites - it allocated a NEW CALLEE-SAVED reg
  (s7: the head word came out `addu $23,$zero,$zero`) + the prologue save
  + a `move $4,$23` feed at the call. The runbook's variable-arg frame
  risk, MEASURED: frame 1088/regs 9/0 breaks the subu word + every save
  offset. LAW: a plain long defined in cold fail blocks and used at a
  tail call takes a NEW callee-saved home, never the dead arg reg - the
  arg regs are not reused for cross-block pseudos by this allocator.
- d49 (the ARG BARRIER at the err-body top, literal 0 arg): ZERO delta -
  the dbr delay-fill backward scan SKIPS volatile-asm insns (never
  eligible candidates) but does NOT STOP at them; the a0=0 still reached
  the jal delay past the barrier. LAW: empty volatile asms are
  transparent to gcc 2.6.3's delay-slot filling (they block the
  SCHEDULER's crossing but not the reorg scan).
- d50 (the err block nested in the check's branch WITH the check's own
  `goto err` kept): byte-identical to d46 except the .file line + one
  label renumber. LAW: `goto err; if (0) { err: ... }` folds to the
  sibling form's RTL - the goto is the POLARITY BLOCKER (it makes gcc
  invert the check to bne fail->block and thread the SUCCESS edge
  through the [j][li -1] skip pair); the nesting only matters when the
  goto is ABSENT (the folded if(0) leaves the body adjacent, the true
  edge falls into the tail, the false edge IS the skip = d47's working
  half).
- d51 (the goto dropped + the SECOND-LABEL sharing: the m-check fail
  becomes a bare `goto merged_fail`, the slot_x pin a BARE register decl
  with the value assigned after the label): GLOBAL CASCADE - regs 10/0
  (two extra callee-saved) shifted every save offset from the prologue on
  and re-broke the $2 disjoint-web partition (151/274, the ladder's worst
  alignment). MECHANISM: the bare (uninitialized-at-decl) register
  variable changes gcc's reg-var treatment vs the decl-with-init form.
  The second-label idea itself is not dead - it needs the decl-with-init
  form C89 cannot place after a label, so it waits for the d38 rebase.
- NET read: BOTH residual levers of the err-label region (the head a0=0
  word, the skip-branch pair) are REBASE-GATED on this landscape - the
  d41 chain drafts' register pressure (s1/s7 thefts, the episode web)
  owns exactly the homes the levers need. NEXT shape (next window): port
  the d46 restructure onto the D38 LANDSCAPE (the pre-chain base, SIZE
  1092 = one word short, alignment 175) - there $4 is the hv read-home's
  natural home and the fail blocks are pressure-free; then re-apply the
  head force (the $4-pinned asm-def variant is legal there IF the pin
  costs nothing on that landscape - MEASURE) and the skip fusion (the
  d47 nesting without the duplication risk, the m-check fail site
  pressure-free). The d47 map (177/274 inline region) remains the region's
  reachability proof.

### H.2 - the judge sequence (oracle UP only; one run per draft, in order)

Pre-flight: Phase A witness 8/8 + Phase B verify sweep GREEN (suite 145/145,
ratchets 948/538 at the cron-202611042013 rewrite - recompute from the
tree). Per run (the banked rehearsal pattern, draft6-10 precedent):

1. `cp probes/gcc263/SsVabOpenHeadWithMode_draftN.c src/SsVabOpenHeadWithMode.c`
2. yaml line 723: `- [0x48864, asm, func_80068064]` ->
   `- [0x48864, c, SsVabOpenHeadWithMode]`
3. `python3 tools/judge_unit.py g3org_jp SsVabOpenHeadWithMode` (~2 s,
   live-only; verdict EXACT / DIFF n/total words / SIZE built vs row)
4. Read the first-diff region against the draft's expected pairs (H.3);
   bank the verdict + the new byte facts in the draft header.
5. REVERT: `git checkout -- config/splat.g3org_jp.yaml &&
   rm src/SsVabOpenHeadWithMode.c` (never leave a non-exact c row; clean
   judge artifacts). The tree stays probes-only between runs.

Run order 21 -> 22 -> 23 -> 24 -> 25 -> 26 -> 28 -> 29 -> 30 -> 31
-> 32 -> 33 -> 34 -> 35 -> 36 -> 37 -> 38 is CUMULATIVE (each draft = the previous + one lever; 26 = 25
with the end_addr revert; 28 = 26 + the condition-chain re-shape + the
m re-home; 29 = 28 + the magic-check temp pin; 30 = 29 + the
loop-bound copy form; 31 = 30 + the idx-home pin; 32 = 31 + the
offset-temp pin; 33 = 32 + the pre-branch reorder; 34 = 33 + the ap
reorder; 35 = 34 + the total=0 sink-barrier; 36 = 35 + the head-loop
do-while re-shape; 37 = 36 + the 787B0 split-temp extend + the bound
remat order; 38 = 37 + the end= operand-order flip): a judge surprise at
draft N re-opens N-1's region first. The row does NOT enter the tree
until the H.5 landing gate.

### H.3 - the per-draft expected pairs and open judge items

THE CRON-202611042128 OFFLINE AUDIT (the committed retail row dump
asm/g3org_jp/nonmatchings/func_80068064.s is the retail truth - every
RETAIL-form question below was answerable without the oracle; the live
judge reads remain only for the BUILT-form confirms):
- draft21 open 1 RESOLVED: retail's rule17 trampoline jdelay =
  `addu $a0,$zero,$zero` (0x8006819C) - the marker's `addu 4 0` form,
  NOT li; no re-spell needed.
- draft22 open set RESOLVED + ONE REGRESSION FOUND: retail's loop
  compares are slt (0x800682C8 pre-check/guard, 0x80068300 back-edge -
  the re-shape's real wins) but the 0x80000 SPU-bound check at
  0x8006836C is retail SLTU (`lui $v0,0x0008 / sltu $v0,$v0,$v1`); the
  draft22 header mis-cited 0x80068300 for that check. end_addr reverts
  to unsigned in draft26 (the offline delta is EXACTLY the one-word
  slt->sltu flip, nothing else moved).
- draft23 open 1 RESOLVED: retail nv home = s4 (`lbu $s4,0x16($a0)` at
  0x800682B4); the built's $20 IS s4 - already retail-exact. Open 3
  RESOLVED retail-side: retail end home = a3 (`addu $a3,$v0,$a1` at
  0x800682C4, end = (nv<<2) + ap); the built draft23 lands $7 = a3.
  Open 2 (the bound remat count): retail materializes the bound ONCE
  (`addiu $t0,$sp,0x410` at 0x8006829C only).
- draft24 open 1 CONFIRMED: retail m-check pair = `lhu $v0,0x12($a0)` /
  `lh $v1,D_80178894` / nop / `slt $v0,$v1,$v0` (0x80068218..28) -
  exactly the draft24 expected pair. Open 2 (the 0x70/ver window)
  retail map banked: andi $v1,$a1,0xFF / ori $v0,0x70 / bne with the
  ori-0x40 delay / lw $v0,4($a0) / nop / slti $v0,$v0,5 / bnez with the
  ori-0x40 delay / ori $v0,0x80 fork / sh $v0,D_80178894.
- draft25 open 3 RESOLVED: retail's end_addr-check beqz delay =
  `addu $s0,$zero,$zero` (0x80068374); the built already emits
  `addu $16,$0,$zero` = the same word. Open 1 SHARPENED: retail's
  m-check bnez (0x8006822C) targets .L80068378 whose FIRST word is
  `addu $a0,$zero,$zero` (the a0=0 pre-zero) BEFORE the tail's
  sll $v0,$s2,16 / sra $v0,$v0,16 - the built's merged tail starts at
  the sll (its a0=0 rides the jdelays). Open 4 (the a2/base chain)
  FULLY RETAIL-CONFIRMED: addu $a2,$s3,$zero @ 0x80068194 (the
  ALLOC-merge bnez delay, the rule17 site) / addiu $a2,$a2,0x20 @
  0x800681CC (the magic-beq delay) / addu $s3,$a2,$zero @ 0x80068230
  (the m-check bnez delay) / sw $a2 at 0x80068248 (D_80178704),
  0x800682AC (D_801787B0), 0x80068324 (D_8017FB6C) - AND THE A0
  RE-MATERIALIZATION SLOT IS FOUND: retail `addu $a0,$s3,$zero` @
  0x800681B8, POST-JOIN STRAIGHT-LINE (after the D_8017876C store,
  before the magic lw $a1,0($a0)), NOT a delay slot; the built's a0
  copy rides the merge delay and its vh reads go through $19/s3 (lw
  $6,0($19)) where retail reads through a0 - the chain lever's
  steering target: merge delay -> a2=s3, a0 copy -> post-join, vh
  reads -> a0. Still judge-gated (gcc 2.6.3 must be steered to
  re-import a0 post-join), but the map is complete.
- draft27 (authored + measured + parked NEGATIVE the same window): the
  fifth-web routing of the m constants through the pinned `shifted`/$2
  EVICTS the compare webs (the retail-exact andi $3/ori $2/bne pair
  broke to $5/$3, the reload fell $3 -> $8); the parked file builds
  machine-identical to draft26 (pure record). The all-v0 window needs
  the full condition-chain re-shape (the 0x70 constant + m + the ver
  reads through one variable) - parked as the next form, touches the
  a2/base-chain territory (H.4). AUTHORED AND MEASURED as draft28 on
  cron-202611042243 - see the draft28 bullet below.
- **draft28 (authored + measured POSITIVE cron-202611042243, THE PARKED
  NEXT FORM)**: the full-window condition-chain re-shape through the
  $2 pin with explicit gotos (shifted = 0x70; if ((w0 & 0xFF) !=
  shifted) goto m40; shifted = *(long *)(hv + 4); if (shifted < 5)
  goto m40; shifted = 0x80; goto m_store; m40: shifted = 0x40;
  m_store: D_80178894 = shifted) + the m RE-HOME (m = D_80178894 fresh
  after the barrier, PINNED $3 - m's later uses ride the m-check
  RELOAD exactly as retail: v1 feeds slt AND sll v0,v1,4 AND blez v1)
  + the base def moved POST-WINDOW (its first use is the 78704 store;
  pre-window it becomes the bne delay candidate and steals the slot
  from the m40 fold - the measured v1 collateral). MEASURED:
  word_diff 156/274 (d26 153) at the same 253 built words. CLOSED
  OFFLINE: the 9-word m40 core - both branch delays carry the folded
  ori $2,0x40 (the merged 1-insn fail block duplicated into both
  delays and retargeted past), the fork falls through with NO j, the
  standalone fail block gone, sh src = $2 (d26 had 4 wrong words
  there) - AND the m-check compare lh $3 / slt $2,$3,$2 / bne $2,$0,
  which CLOSES THE BANKED OPEN SLT-DST ITEM (the "slt/branch regs land
  $3 as gcc's first-operand habit" open judge item from
  cron-202611041628) OFFLINE. THE COUPLING, NOW MEASURED: the chain's
  first def (ori $2,0x70) floats into the MAGIC-BEQ DELAY - the slot
  retail fills with the a2-chain's addiu $a2,$a2,0x20 (judge-gated
  draft25 open 4) - so the full 12/12 window closure stays CHAINED TO
  THE A2-CHAIN LANDING exactly as the draft27 header predicted; the
  d26 delay word was also wrong there (the base def), the slot count
  is NEUTRAL. COST (recorded): the loop's p := base lost its v1 home
  (m's pin holds $3 through the loop compare; the retail form needs
  the loop-bound COPY choreography - draft23-bucket territory); idx
  moved $7 -> $8 (wrong -> wrong); NET still +3.
- **draft29 (authored + measured cron-202611042243, same window)**: ONE
  pin - the w0>>8 temp through $2 (w0hi = w0 >> 8; if (w0hi !=
  0x564142)). FOUR magic-check words flip retail-exact (srl dst v0,
  the constant lui/ori in v1, the beq v0,v1 pair) - the diff vs d28 is
  EXACTLY those four words - but the aligned-match metric STAYS
  156/274 (the wins absorb into difflib's alignment: the
  count-masking class; region-exactness is the real goal, the metric
  is a lower bound). The w0 -> $5 pin was authored, measured 155/274
  and REJECTED: the pin evicts the early split-temp webs from $5
  (five words lost vs four gained - gcc treats an explicit register
  variable as a whole-function packing reservation for the other
  pseudos); twin-law: pin $5-class regs ONLY when the early traffic
  is already pinned away. H.2 order 21 -> 28 -> 29.
- **draft30 (the LOOP-BOUND COPY FORM, authored + measured POSITIVE
  cron-202611050228)**: the retail first-loop choreography the d28 cost
  note predicted - after the tp def, k = 0 pre-blez, the guard STAYS on
  m (retail blez v1 reads the reload), idx = 0 hoists toward the delay,
  then addu a3,v1,zero (the m -> a3 LOOP-BOUND COPY at 0x80068260) and
  addu v1,s3,zero (p = base into the FREED v1 at 0x80068264); the loop
  compare rides the COPY (slt v0,a1,a3), NOT m. Authored as: the
  do-while re-shape (if (m > 0) { idx = 0; m2 = m; p = base; do {...}
  while (k < m2); }), m2 = a NEW register variable PINNED to $7 (an
  unpinned m2 was COALESCED back into m - the copy died and the compare
  re-read v1; a register var on a different hard reg cannot coalesce),
  and p UNPINNED (a p pin deletes p's stack home: frame 1080 -> 1072,
  flipping subu + all eight save offsets; free, p took the vacated v1 -
  the disjoint-web free-packing precedent). MEASURED 161/274 at 254
  built words, NET +5: the copy word + p's home flip + the lbu/sw bases
  + the compare + the p+=16 base all retail-exact (the copy and p=base
  words BYTE-EXACT, aligned one slot late by the k=0/idx delay-fill
  order). ZERO collateral: end's free web KEPT $7 and spu's pin held -
  the m2/end/spu three-web partition of $7 (the disjoint-web law).
  THE FRAME-PAD: the do-while rewrite alone eliminated reload's 8-byte
  ghost reservation (vars 1032 -> 1024, frame 1072 - no instruction
  references the slot; the for-form's rotated entry created it); the
  dead address-take (long frame_pad; if (0) { (void)&frame_pad; })
  re-reserves the slot AT PARSE TIME with zero emitted code - measured:
  the only build delta is the .file line + label renumbering. C89 note:
  register decls must sit in the declaration block (gcc 2.6.3 parse
  error mid-block). SIZE: +1 real word (the copy) - the fund is the
  a2-chain's base-def elimination (see H.1 draft30 row). REMAINING
  region wrongs (the next-lever menu): the increments' OPCODE class
  (built addu $16,$16,1 / addu $5,$5,1 / addu $3,$3,16 vs retail addiu
  x3 - gcc 2.6.3 emits addu PRE-maspsx, a flag-or-shape question, three
  words), the k=0/idx=0 delay-fill order (built blez delay = k=0,
  retail delay = idx=0 - one positional word), the 78704 sw value +
  the p=base/addu $6 srcs ($19 vs retail s3/a2 - the judge-gated
  a2-chain).
- **draft31 (the IDX-HOME PIN, authored + measured POSITIVE
  cron-202611050228)**: register long idx asm("$16") - retail idx home
  = s0 (addu s0,zero,zero at 0x8006825C in the blez delay; sw s0,8(v1);
  addiu s0,s0,1) and total re-rides s0 after (0x8006828C); the built's
  free idx rode $8 (bound's dead pin). The pin rides vabid's dead $16
  web. MEASURED 164/274, NET +3: sw $16,8($3) BYTE-EXACT, the idx=0 and
  idx++ dsts flip s0; total's free web KEPT $16 (no eviction - the
  idx/bound precedent held). The addu-vs-addiu increment opcodes stay
  wrong (the opcode-class item above).
- **draft32 (the OFFSET-TEMP PIN, authored + measured POSITIVE
  cron-202611050228)**: register long tpose asm("$2"); tpose = m *
  0x10; tp = base + tpose - retail's tp offset rides v0 (sll v0,v1,4 /
  addu a2,s3,v0); the built's free temp rode tp's own home $6. MEASURED
  166/274, NET +2: the sll dst and the addu src2 flip v0 retail-exact;
  the addu src1 ($19 vs retail s3) stays judge-gated a2-chain
  territory. The $2 web is freed by the m-check reads' death (the
  eighth disjoint web on the $2 pin).
- **THE W0-HOME ITEM CLOSES OFFLINE (measured-negative TWICE)**: the
  w0 -> $5 pin re-measured on the d30 landscape (cron-202611050228):
  160/274, NET -1 - the SECOND consecutive negative (the d29-window
  attempt on the d28 landscape also measured NET -1). The eviction set
  is now precise: the alloc-merge sra temp ($5 -> $6), the ext-slot
  index sll ($5 -> $6), the magic-fail sb index ($5 -> $6) AND the
  andi/bne pair's dst flip ($3 -> $5 - gcc reuses w0's $5 for the
  dead-after mask result where retail keeps the mask in v1 with a1
  still holding w0); gains only the lw dst + the srl src. w0's home is
  UNREACHABLE by direct pin; the item rides the a2-chain's a0 steering
  (the load src a0 part) and upstream home pressure - judge-gated
  follow-up territory.
- **draft33 (the PRE-BRANCH REORDER, authored + measured POSITIVE
  cron-202611050458)**: the k=0/idx=0 delay-fill item - idx = 0 moved
  from the first statement inside the if to immediately before it
  (semantically identical: the delay slot executes unconditionally and
  idx dies at loop exit). The d32 form had idx=0 first INSIDE the if
  and the delay-fill scheduler took k=0 (the immediately-preceding
  independent set) for the slot, leaving idx=0 post-branch; the built's
  blez offset word was 0x1860000D vs retail 0x1860000C and the slot
  word was a1=0 vs retail s0=0. MEASURED 167/274 at 254 built words,
  NET +1, SIZE-neutral: the ENTIRE 16-word loop window
  retail[122..137] (0x8006824C..0x80068288) is now ONE binary equal
  block - k=0 pre-branch, the blez word retail-exact, idx=0 in the
  delay, the copy, p=base and the full body byte-identical. The d32 ->
  d33 build delta is EXACTLY the .file line + the reorder (diff
  verified).
- **draft34 (the AP REORDER, authored + measured POSITIVE
  cron-202611050458)**: ap = (long)arr; moved to immediately after
  total = 0, before the D_801787B0 store - retail's post-exit order is
  total=0, ap, 787B0-store-prep; the d33 form had ap after the
  reads+tp+=. The ap word was ALREADY retail-exact (0x27A50010 via the
  gas addu-with-imm law) - only its position was wrong. MEASURED
  168/274 at 261 objdump words, NET +1, SIZE-neutral. Remaining
  post-loop positionals after this: the bound remat (retail addiu
  t0,sp,0x410 sits between the sra14 and the 787B0 lui at 0x8006829C;
  the built keeps it with the end group) and the total=0 float (d35).
- **draft35 (the TOTAL=0 SINK-BARRIER, authored + measured POSITIVE
  cron-202611050458)**: an empty volatile asm (memory clobber) placed
  immediately AFTER the first total = 0 - retail's first total=0 sits
  at the loop exit (0x8006828C) but gcc floats the independent set ~40
  words down to the backfill pre-entry; the barrier (the banked
  m-reload precedent, emits nothing) stops the sink. MEASURED 169/274
  at 262 objdump words, NET +1, +1 REAL retail-backed word (retail HAS
  the post-exit zeroing; the second source total=0 already rode the
  end_addr beqz delay retail-exact per draft25 open 3). LIVE
  prediction 276 = +2 over the row (the copy + this word); the
  conservative SIZE-neutral form is draft34 if the H.5 gate refuses.
  Delay-fill side effect (banked): the pre-entry beq's delay got
  refilled with a DEAD sll duplicate of the 787B0 store prep (retail's
  is a nop; same slot count) - the draft23 pre-entry re-shape refills
  it when it lands.
- **draft36 (the HEAD-LOOP DO-WHILE RE-SHAPE, authored + measured
  cron-202611050613)**: the for-form `for (; ap < bound; ap += 4)`
  made gcc emit a rotated TOP GUARD (addu $8,$sp,1040 late / slt
  $2,$5,$8 / beq $2,$0,<exit> / dead-sll delay = the d35 side effect)
  before the end<ap test, but RETAIL HAS NO TOP GUARD - the entry
  falls straight from end= into .L800682C8 slt v0,a3,a1 / bnez v0 /
  NOP, and ap<bound rides ONLY the back-edge (.L800682FC addiu a1,4 /
  slt v0,a1,t0 / bnez v0 / addiu a2,2 delay). Source re-shaped to
  `do { if (end >= ap) { body } tp += 2; ap += 4; } while (ap <
  bound);` - semantically identical for this caller (ap = sp+0x10,
  bound = ap+0x400, both frame-fixed: the top guard was dead runtime
  code; retail's binary IS the source-shape truth). MEASURED 169/274
  at 260 objdump words, NET 0, -3 insns (the guard's slt/beq/dead-sll,
  all wrong words): live-predicted 260+14 = 274 = THE ROW (the d35
  +2 debt cancels against the guard's -2 objdump; the H.5 SIZE
  arbitration note). Frame UNCHANGED 1080/1032 - no ghost-reservation
  shift from THIS do-while (the d30 frame-pad lesson did not bite).
  The d35->d36 build delta is EXACTLY the guard removal + label
  renumbering (diff verified).
- **draft37 (the 787B0 SPLIT-TEMP EXTEND + THE BOUND REMAT ORDER,
  authored + measured cron-202611050613)**: retail's post-exit order
  is total=0 / ap / sll16 / sra14 / BOUND / 787B0-chain / sw - the
  extend pair scheduled BEFORE the bound def (addiu t0,sp,0x410 at
  0x8006829C, between the extend and the lui). The built emitted the
  extend INSIDE the store's address computation (list position = the
  store's), so NO source position of `bound = ap + 1024;` could land
  the def inside the store group: before the store (pos a) AND after
  the store (pos b) both hoist the independent $8 def above the
  extend pair (pos a measured: total/ap/BOUND/sll16/sra14/sw - the
  bound 2 slots early), and after the reads it sank to the entry test
  (the d36 form). THE FIX = the banked split-temp law (draft17/25
  class): register long slot4 asm("$2") (the NINTH disjoint web on
  the $2 pin), slot4 = (long)slot << 16 >> 14 as its OWN statement,
  the store reads it back (sw $6,D_801787B0($2), same embed form).
  Source order ap= / slot4= / bound= / store => machine list order ap
  / extend / BOUND / store = RETAIL'S ORDER. MEASURED 170/274, NET
  +1: the bound word 1004a827 pairs at retail's slot.
- **draft38 (the END= OPERAND-ORDER FLIP, authored + measured
  cron-202611050613)**: the built's `end = ap + nv * 4` emitted addu
  (a1 + v0) = 00a23821 (ap's home rs, the scaled temp rt) but
  retail's is addu (v0 + a1) = 00453821 (the temp FIRST, the
  draft23-open-3 banked form `addu $a3,$v0,$a1`). gcc 2.6.3 preserves
  the SOURCE addition order in the commutative-plus encoding: `end =
  nv * 4 + ap` flips the word retail-exact. MEASURED 171/274 at 252
  built words, NET +1, SIZE-neutral; the d37->d38 delta is EXACTLY
  the one-word operand flip (diff verified) and the whole entry-test
  group (end= / slt v0,a3,a1 / bnez v0,+11 = 1440000b / nop) now
  aligns INSIDE the equal blocks. THE POST-LOOP POSITIONAL SET (the
  cron-202611050458 next-queue item) IS CLOSED end to end.
- **THE AT-CHAIN CLASS LEVER (discovered cron-202611050613, the
  next-window item)**: retail's SIX symbolic sw stores with a reg-reg
  index - 7876C (0x800681A4..AC), 78704 (0x8006823C..48), 787B0
  (0x800682A0..AC), FB6C (0x80068318..24), FB24 (0x800683C4..D0),
  FAE0 (0x8006845C..68) - ALL use the 4-word form lui at,%hi /
  addiu at,at,%lo / addu at,at,v0 / sw reg,0(at): the FULL symbol
  address materialized, THEN the index added. The built's gcc emits
  the 3-word embed (lui at,%hi / addu at,at,v0 / sw reg,%lo(at) via
  gas) = -1 word per site, ~-6 of the built's remaining word deficit.
  The E038/78894/FB20 sites (sb/sh with a plain reg index) use the
  2-3-word forms the built already matches - the class is specific to
  the unsigned-long-array sw stores. Source-shape hypothesis: the
  original computed the store address through an explicit
  pointer/intermediate (or a two-step at-chain the 2.6.3 scheduler
  kept); needs one careful draft per the lever-isolation law, the
  787B0 site first (its extend is already split out in d37+).
- **THE OPCODE-CLASS ITEM CLOSES AS A FALSE ITEM (cron-202611050458,
  zero words at stake)**: the draft30 "REMAINING region wrongs" entry
  "the increments' OPCODE class (built addu $16,$16,1 / addu $5,$5,1 /
  addu $3,$3,16 vs retail addiu x3)" was a MNEMONIC-TEXT artifact,
  never a binary diff. Chain verified end to end: gcc 2.6.3 emits the
  addu-with-immediate TEXT form pre-maspsx (the .gcc.s intermediate),
  maspsx passes it through unchanged, and gas (mipsel-linux-gnu-as
  2.31.1) assembles "addu reg,reg,imm" as the I-type addiu ENCODING -
  the built .o words at the three first-loop sites are 0x26100001 /
  0x24A50001 / 0x24630010, byte-identical to retail's addiu words (the
  retail dump prints "addiu" because that IS the encoding). The same
  conversion covers the backfill-loop "addu $5,$5,4 / addu $6,$6,2"
  text forms (the .o shows 0x24A50004 / 0x24C60002). word_diff.py
  (gas+objdump based) had already counted all these sites equal - the
  item existed only in text-level reads. No flag, no shape change
  needed; banked so no future window re-opens it.
- **draft21 (rule17 merge-polarity, the 51-word 0x80068188..0x80068250
  region)**: the alloc-merge `beq $2,$0,$L19` (fail far, body falls
  through) inverts to `bne $2,$0,$Lr17c` (+3 by construction = retail's
  bnez-near), the built delay `addu $4,$19,$zero` KEPT verbatim, the
  2-word err trampoline `j $L19` + the marker jdelay inserted before the
  join. OPEN: (1) the jdelay op spelling - the marker says `addu 4 0`
  (gcc 2.6.3's zero-arg spelling, 0x00801025) but retail's actual word may
  be li (0x24040000) - one diff read decides, the marker arg re-spells;
  (2) SIZE 1098 = +2 until a tail lever sheds 2 (draft23 does); (3) the
  err-tail companion - if retail hoisted the a0=0 INTO the trampoline,
  retail's err-tail jal delay may be a nop (separate one-site follow-up).
- **draft22 (the slt signed re-shape, the draft17 byte facts)**: the
  backfill-loop address holders move from `long *` to signed `long` -
  expect slt at the loop compares (retail `slt v0,a3,a1` / `slt v0,a1,t0`)
  and at the 0x80000 check, ALL FOUR sltu->slt with zero collateral; the
  draft18-closed store->reload window stays byte-identical. Reg SELECTION
  still differs (built $5/$8/$7 vs retail a3/a1/t0) - NOT a draft22 item,
  the reg-home chain is later. OPEN: the rule17 anchor $L19 may renumber
  with the source edit (re-pin the marker if gcc's err label moved - the
  rule-10 precedent; cc_post loud-fails exit 3 on anchor mismatch).
- **draft23 (the pre-loop dst-reg/sharing form, the 29-word
  0x80068258..0x800682C8 bucket)**: three sub-levers - (a) the nprogs
  pre-loop load dst rides the $2 pin's third web (`lhu $2,18($4)` feeding
  `tp += shifted << 9`), (b) the end/ap de-share materializes ap DIRECTLY
  (`addiu a1,sp,0x10`), (c) the t0 bound pins the single pre-loop home
  (`addiu $8,$sp,1040`; end falls to a3). Expected built pre-loop word
  forms: lhu $2,18($4) / lbu $20,22($4) / sll $2,$2,9 / addu $6,$6,$2 /
  addu $5,$sp,16 / sll $2,$20,2 / addu $7,$5,$2 / addu $8,$sp,1040 /
  slt $2,$5,$8 / beq $2,$0,<exit> / addu $16,$0,$zero (delay) ... slt
  $2,$7,$5 / bne $2,$0,<skip> / nop ... slt $2,$5,$8 / bne $2,$0,<head> /
  addu $6,$6,2 (delay). OPEN: (1) the nv load dst s4 home is UNBANKED
  retail-side (one diff read; if it differs, one more pin); (2) the bound
  remat COUNT - the pin forces the home, not the count: a second addiu
  $8,$sp,1040 at the entry test = +1 word (SIZE 1097-class, accounting
  shifts); (3) end's a3 home is gcc's free choice - one diff read decides
  the next pin. The rule17 anchor + the rule16 verdict are UPSTREAM of
  every edit (loud-fail sentinels).
- **draft24 (the m-check nprogs FIRST-READ home flip)**: the second
  nprogs read rides the $2 pin too - expected pair against the built
  lhu $3,18($4) / lh $2,D_80178894 / nop / slt $2,$2,$3:
  `lhu $2,18($4) / lh $3,D_80178894 / nop / slt $2,$3,$2`. OPEN:
  (1) whether the m reload lands $3 unpinned or needs the pin - RESOLVED
  OFFLINE in the draft25 build: it lands $3 UNPINNED, matching the
  banked retail v1 home (one judge diff read confirms); (2) the 0x70/ver
  window upstream is NOT fully banked - if the ver/slti window moves,
  the cascade is the next lever, NOT a regression; (3) four disjoint
  webs now share the $2 pin (vb extend, both nprogs reads, mode test) -
  all dead-at each next def, the draft17/23 reuse precedent.
- **draft25 (the LAST in-place err-path extend -> the TEMP form, the
  shared fail tail at built 0x2ec = retail 0x8006834C)**: the tail
  machine stream must read sll v0,s2,16 / sra v0,v0,16 / lui at / addu
  at,at,v0 / sb EXACTLY (the draft16 map class fact); the gcc label $L53
  sits between the tail's sll and sra - the end_addr path falls through
  the tail's own sll, the m-check bne targets $L53 (the sra) and feeds
  $2=slot<<16 from its OWN delay slot (the pre-existing hoisted OK-path
  sll16). Region residual: 2 wrong words (the delay word + the bne word).
  OPEN (the residual singles + the chain): (1) the bne target offset +1 -
  built lands at the sra (tail+1) using the delay-sll; retail's banked
  delay = the a2-chain `move s3,a2` (NOT an sll) so retail's target
  should be the sll (tail+0) - when the a2-chain lever lands, the
  m-check site's pin re-reads (the delay-sll disappears, the target
  returns to tail+0, the tail keeps the full 5-word temp form); (2) the
  bne src $3 vs retail $2 (the draft24 slt-dst open item - RESOLVED
  OFFLINE by draft28 cron-202611042243: the m re-home puts the compare
  dst and the branch src in v0; the item stays open for the 21->26
  ladder runs and closes when 28 judges);
  (3) the retail end_addr-check delay (built move s0,zero) is unbanked -
  one diff read; (4) THE A2/BASE CHAIN (the draft16 map's move a2,s3 ->
  addiu a2,a2,0x20 in the magic-beq delay -> move s3,a2 in the m-check
  bnez delay -> the 78704 sw a2) is JUDGE-GATED on the a0
  re-materialization question: retail must copy vh back to a0 after the
  setInTransfer calls clobber it (the banked lhu 0x12(a0)/lbu
  0x16(a0)/lw 0x4(a0) read homes demand it) but NO banked slot holds
  that copy, and the built's copy occupies the merge delay the chain's
  move a2,s3 needs - any offline authoring must delete-or-relocate the
  a0 copy, a semantic gamble the judge diff must arbitrate. The map is
  banked in the draft25 header (open judge item 4) - the judge window
  reads it directly.

### H.4 - after draft25 (the same window, oracle up)

1. The tail-loop levers (the 66-word 0x80068160-class region): the live
   judge dump is the prerequisite - `build/judge/*.mas.s` from the
   draft25 run + the row .s give the retail-form map. DO NOT author
   blind (the count-masking lesson, cron-202611041128: VA-to-VA diffs
   cannot see content wins behind a skew).
2. The a2/base chain per H.3 draft25 item 4 - judge diff open, one run;
   the retail map is complete (the chain steps + the a0 post-join slot,
   cron-202611042128 audit) and the steering target is concrete:
   merge delay -> a2=s3, a0 copy -> post-join straight-line, vh reads
   -> a0.
3. LAND (H.5) only when the judge verdict is EXACT.

### H.4b - the knob-alive structural map of draft38 (cron-202611050728, offline)

The knob-alive word_diff of draft38 (266 w / 175/274 / linked 1092) leaves
six structural blocks - the NEXT lever map, all offline-derivable, no
oracle needed (VA = 0x80068064 + offset):

- retail +9 w @0x0130 (0x80068194, the rule17 verdict/err-trampoline
  region: retail carries the inline fail j+li pair the built folds)
- built +7 w @0x018c (0x800681F0, built-only spill/shuffle words)
- retail +1 w @0x01cc (0x80068230, the m-check delay copy addu s3,a2,zero
  - the KNOWN a2/base chain lever, item 2 above)
- retail +1 w @0x0314 (0x80068378)
- retail +9 w @0x0338 (0x8006839C)
- built +9 w @0x041c (0x80068480, the built-only tail)

Net retail +20 / built +16 words by the gas counter; the linked SIZE gap
is -4 B (one word). The two +1 retail sites are the cheapest SIZE-closing
candidates; the 9-word blocks are the next content waves. Every block is
visible in the knob-alive word_diff output banked in the window's TASKS
section - re-derive with the H.1 recipe before steering any draft39+.

### H.5 - the landing gate (all of it, or nothing)

- Judge EXACT on the staged row (H.2 step 3) - a DIFF verdict never
  lands; the yaml flip and the src addition land in the SAME commit.
- `make verify TARGET=g3org_jp` GREEN (whole-image; the row's 0x448 must
  not overlap the next row 0x48CAC - SIZE 1096 exact, which is why the
  trampoline +2 must stay funded by the de-share -2, H.1).
- The registrar needs NO edit (453fa4ed already re-pointed it); the
  pinned-member entry STAYS (the landed-sibling precedent).
- `python3 -m unittest discover -s tests` GREEN; ratchets recomputed from
  the tree (`make ratchets` - the arbiter; refunds lower the baseline in
  the SAME commit); commit type: match; then the docs/TASKS.md window
  section in the same push.
- The seven region twins AFTER the g3org_jp landing, one per window
  minimum: g3org_eu 0x493D4, g3_jp 0x4B3C8, g3_eu 0x4BF80, sces_00269
  0x24990, slps_00270 0x24974, mainmenu_eu 0x61564, mainmenu_jp 0x609E4 -
  all extent 0x448; rules 15+16 + the three wave pins carry IF the
  families match; each twin's addiu-at class checks against its own
  flags scope; per-target D_ extern names from each target's own asm
  (g3_jp's set: D_8016AA50/D_8016AAB8/D_8016AAFC/D_8016ABE0/D_80170384/
  D_80171E2C/D_80171E6C/D_80171E70/D_80171EB8).

## Standing gotchas

- Never commit: PAT, disc images, baselines, extracted assets. The
  pre-commit hook enforces; never --no-verify (documented asm/-regen
  exception only).
- Session-local wire/extract edits are REVERTED before any commit that is
  not the landing itself; ratchets must always equal the tree.
- judge_unit is a screen, not the oracle - acceptance is whole-image
  `make verify`; nothing judge-side feeds ratchets or progress. Verdicts
  are LIVE-ONLY (judge_unit is sha1-gated on baselines/<t>.bin; the
  woven-era dumps are refused by design - the baseline_audit table's
  8 MISMATCH pairs are the expected pre-witness state).
- Terminal display eats literal "[m" bytes - byte-scan before any
  'repair'; never casual `splat split`; kill stray verify/build loops
  before landing.
- **Commit messages with `$` tokens (banked cron-202611042013, hit
  live)**: unescaped `$2` in a commit message expands to EMPTY at the
  shell layer (the draft25 "double  pin" log artifact). Escape `\$` in
  message text, or spell registers without the `$`. Byte-scan any pushed
  message that carried a `$` (`git log --format=%B -1 | grep -c '\$2'`);
  the fix is re-escaping in the FOLLOWING commit, never a force-push to
  main.
- **Offline vs live SIZE scales (banked cron-202611042128)**: a
  compile-only `.mas.s` assembles to fewer words than the live judge
  reports for the SAME source - the unlinked .o keeps each bare-symbol
  data access as one word + relocs, and the judge's mini-link expands
  the HI16/LO16 pairs. On the SsVabOpenHeadWithMode unit the constant
  is +14 words (offline 260 w / 1040 B vs live 1096 B). Only same-path
  numbers compare: offline deltas vs offline deltas, live SIZE vs the
  row extent (Phase H.1 carries the ledger).
- Wave landings: the wave104 header shape (one placeholder mention per
  file) applies at template + gen source before landing.
- The sdk_members / sdk_anchors / sdk_curated regen trio is
  TRUE-BASELINE-GATED: the member slide consumes baselines/<t>.bin (the
  splat yaml's own target_path), so running it against the woven-era
  local dumps produces a false census (measured cron-20261101-0953:
  g3_eu 402 -> 357 placements, 110 -> 51 named symbols) whose
  "adoptions" would be woven-baseline evidence. sdk_curated's
  refuse-guard (hand-authored content inside the generated block) is the
  last line of defense - regenerate ONLY after Phase A witness 8/8 flips
  the baseline_audit table to 8 MATCH, and hand facts live ABOVE the
  marker (load_curated applies by `// target:` header, so a moved entry
  must land inside its own target's section, never in a shared pile).
- Single-session rule: one agent per sandbox; builds foreground, one
  target per call; never two at once.
- worklog digest gate + RESTORE NOTE SOP every session (`python3
  tools/append_restore_note.py <digest_capture_file>`; forced -restore
  suffix, DIGEST_EXIT/EXIT lines filtered); end-of-session worklog append
  + Discord report with <t:UNIX:f> window stamps. The exec-bit dance is
  dead: cc.sh / witness_check.sh / rehydrate.sh carry the executable bit
  IN the index.
- **Media mortality (banked cron-202611041358, hit live)**: ALL THREE
  baseline recovery media live in the same rolled-back layer - the repo's
  gitignored `baselines/`, the `disc_*_true/` extractions ("the third
  recovery medium", cron-202611041128), and the `disk/` CHDs. The
  2026-11-04 05:59 UTC rollback took ALL of them at once while the
  2026-11-01 disc links were past their ~24-35h life (both HEAD 404) -
  the first full oracle outage. Consequences: (1) a window that arrives
  to a full-loss state must NOT attempt baseline reconstruction from
  anything local - the oracle is DOWN until Silent issues fresh links,
  and that window's Discord report MUST carry the fresh-link request
  alongside its offline work (Law Zero: the request is not a hold);
  (2) judge-deferred work is the productive offline lane - author the
  draft + prove the shape through the compile-only cc.sh path (no yaml
  flip, no baseline), bank the open judge items in the draft header,
  and park it; (3) `config/sha1/<t>.sha1` + the banked per-file hashes
  in the worklog are the ONLY durable oracle identity - they survive
  in-repo and let the next window's witness check detect the woven set
  instantly (judge_unit's baseline_gate refuses the wrong build loudly).
