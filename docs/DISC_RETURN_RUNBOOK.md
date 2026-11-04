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

THE SCALE LAW (banked cron-202611042128, measured): the offline .text
counts the UNLINKED .o - every bare-symbol data access (the D_ statics,
the _spu_/SpuMalloc calls) is one word + relocs; the live judge's
mini-link expands the HI16/LO16 pairs, so LIVE SIZE = offline words x 4 +
14 on this unit (draft20: offline 260 w / 1040 B, live 274 w / 1096 B =
the exact 0x448 row). NEVER compare an offline absolute SIZE to a live
judge SIZE; the offline DELTAS are the lever ledger and are scale-exact:

    draft20  260 w (1040 B)   live 1096  (the judged anchor, cron-202611041243)
    draft21  262 w (+2)       live 1098 expected (the rule17 trampoline)
    draft22  262 w ( 0)       live 1098 held   (the slt re-shape is reg-neutral)
    draft23  260 w (-2)       live 1096 again  (the de-share funds the trampoline)
    draft24  260 w ( 0)       live 1096
    draft25  260 w ( 0)       live 1096  (".text 0x410 = 1040 unchanged")
    draft26  260 w ( 0)       live 1096  (the end_addr revert, see H.3)

Every one of these numbers reproduced on cron-202611042128 from the
committed drafts; re-derive them if a draft header ever disagrees.
Offline aligned-match vs the row column (scripts/word_diff.py, the
standalone-as config - cross-config numbers do NOT compare): draft25
152/274, draft26 153/274 (the end_addr check's sltu now retail-class).

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

Run order 21 -> 22 -> 23 -> 24 -> 25 -> 26 is CUMULATIVE (each draft =
the previous + one lever; 26 = 25 with the end_addr revert): a judge
surprise at draft N re-opens N-1's region first. The row does NOT enter
the tree until the H.5 landing gate.

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
  a2/base-chain territory (H.4).
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
  bne src $3 vs retail $2 (the draft24 slt-dst open item, unchanged);
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
