# DISC RETURN RUNBOOK (banked cron-20261026-2119; Phases C-G rewritten cron-20261101-0736)

The oracle-return window's exact sequence. Phases A/B are the standing
mechanics; Phases C-F are the CURRENT parked-draft landing queue (the
2026-10-27/28 phases landed with the oracle returns - the rule-1 n-load
generalization is in tools/cc_post.py, GsMapModelingData sits as c rows in
all six game yaml files - and the block-move twin pair stays parked at its
banked ceilings, so the stale payloads were rewritten out per this file's
own convention). Sources: docs/TASKS.md Log, the parked drafts' headers,
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
