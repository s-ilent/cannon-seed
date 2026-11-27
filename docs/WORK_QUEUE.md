# Current work queue

**Reconciled 2026-11-22** using the **latest** November 21 entry in
[TASKS.md](TASKS.md) (cron-202611211415, close-out at `a13c6f92`) and the
subsequent source-only CI/toolchain commits. This file, **not the October
"## Queued" section at the top of TASKS.md**, is the task entry point.
Use [STATUS.md](STATUS.md) for verification confidence and
[RESEARCH_LOG_INDEX.md](RESEARCH_LOG_INDEX.md) to find older experiments.

**Always start by refreshing evidence:** record HEAD, the relevant yaml
rows/source files, existing branch/PR work, and current
`python3 tools/audit_c_names.py --cross --adjudicate` output. The
numbers below are the last historical snapshot, not a promise about a
newer tree.

## Source-only measurement before selecting a research region

Run `python3 tools/coverage_report.py --strict --json --rows` and use
`origin_unattributed_asm_bytes` to identify **candidate** non-SDK areas,
not confirmed game functions. Inspect any large span's containing YAML
and actual assembly, then use SDK archive evidence and call/data flow
to establish genuine game ownership. The reporting semantics are in
[COVERAGE.md](COVERAGE.md). `make coverage` prints a compact summary.

**Semantic audit discipline:** adding `config/coverage_reviews.json` entries
requires a per-row source review and rationale. A file without detected
inline asm is merely a *candidate for semantic review*, not automatic
semantic-C progress. Shared code repeated in different targets contributes
multiple **target instances** to byte totals.

## Ready: bounded read-only research

### R1 — Game-code recovery atlas (independent research track)

**Twenty-eight bounded runs completed (2026-11-22..27):** the pass-28 curated bank closes pass 27's open item (a) — the four EU accessor twins banked INERT in curated under `// target: g3_eu` (get_game_info = 0x80025920 plus the split-carve dispatcher piece 0x8002594C as get_game_info_dispatch, the suffixed-member name following the intr_restart_tail precedent; set_game_info = 0x8002556C; set_player_info = 0x80025AB4; get_player_info = 0x80025BF8), all five placements inside the uncarved data band exactly like the JP entries, zero new per-section curated collisions (the four accessor names join their g3_jp twins across targets — the established per-target namespace pattern), suite 299/299, ratchets 959/831 baseline; the pass-27 note [G3 gameinfo EU](research/G3_GAMEINFO_EU_20261127.md) closes pass 26's next-question (a) and COMPLETES the passes 20..24 EU corroboration walk: the gameinfo family is two-image — EU carries the complete gameinfo.c string family (+0x18 shifts: "gameinfo.c" 0x8002018C, the four mode-switch printfs, the full 12-string validation schema), the four accessors are body-verified twins at a uniform -0x24 band (**get_game_info = 0x80025920 entry + 0x8002594C dispatcher piece — EU's carve SPLITS the getter**; set_game_info = 0x8002556C; set_player_info = 0x80025AB4 body-verified stride-0x2C/base 0x80010008/-0x10/0x49/head+6; get_player_info = 0x80025BF8, error tail 0x80025D70), the four jtbls at +0x18 (jtbl_80020498/80020420/80020518/80020678), the __LINE__ constants identical (set_player_info's error prints line 0x1EA both regions), and the decisive fact: **the below-image hand-off block is REGION-IDENTICAL — flag 0x80010000, record bases 0x800100B8/0x800105F0, the 0x80010B28.. array, player base 0x80010008 stride 0x2C, id space 0x10..0x58, and the record-index cells D_80010E04/06/08 are the same addresses in both retail images**; the caller censuses reconcile exactly (get_game_info 35 = 35 with the same 10 raw pilot words 0x0C009648, set_game_info 9 = 9 with the same 3 raw words 0x0C00955B, set_player_info **6 = 6**, get_player_info 23 = 23 no raw either side), with a **pass-24 census erratum: pass 24's "set_player_info x3" undercounted JP — the func_8002A2DC-row jal at 0x80026610 and two raw words 0x0C0096B6 at 0x80045B00/B20 (JP stores the launcher-adjacent pair as data words where EU carves them as jals 0x80045768/0x80045788) are real sites the name-only census missed; the corrected JP count is 6, matching EU exactly; the field-map reading is unaffected**; the pass-26 note [G3 exit machines EU](research/G3_EXIT_MACHINES_EU_20261127.md) closes pass 25's next-question (a) [G3 exit machines EU](research/G3_EXIT_MACHINES_EU_20261127.md) closes pass 25's next-question (a) — the exit machines are two-image: **EU exit flag = D_800ACD44 (+0x850)** with the dispatcher reader (lh @ 0x8004298C, bne to the 0x800428F8 loop head, else jal func_8002AD14) and all FOUR writers as instruction-identical twins (machine A +0x60: sh @ 0x800236D0 / 0x80023D78 / func_80023D84 incl. the executor twin func_80029FB0 with a0=0x35; machine B -0x398: the store trio func_80043C14 = sh D_800ACDFC=1 (mode word twin) / D_800AC6E4=0 / D_800ACD44=1 — JP func_80043FAC verbatim); the six guard words' EU twins measured (not extrapolated): vsync_grace_cnt = EU gp+0xA = 0x800ABABA (three same-line sites), attract_step_cnt = D_800AC9B4 (+0x850, arm @ 0x80023030 same line as JP's), attract_variant = D_800AC7EC (+0x850, variant A sh zero @ 0x800304B0 / B sh v0 @ 0x8003054C inside the EU timeline-init twin; EU main calls it a0=0 so variant B is static-dead in EU too), attract_outcome = D_800AC814 (+0x850), attract_stream_len2 = D_800ACAE4 (+0x850, the gate's lw compares), **st_next_rec = D_800AC3B8 at +0x844 (the band exception — the StGetNext retry-loop twin func_8002AE68 passes it; the +0x850 prediction misses by 0xC, exactly why every twin is read)**; the gate: STAR_MODE7 at EU 0x8002146C (string table -0x20), the script-selector twin func_80022E40, the three shared thresholds 0x16F8/0xC78/0x1E76 byte-identical on JP's lines, and **the fourth fallthrough tier diverges: EU slti 0x1418 (5144) vs JP 0x141E (5150) — the lane's second code-side constant divergence, in a tier static-dead in both regions** (variant B unreachable both sides); the bss slot-state arrays are per-region data: EU s6/fp = D_80147E28/D_80148058 (+0x92C, own bss band), button bitfield D_800AC17C → D_800AC9CC (+0x850); the pass-25 note [G3 main EU walk](research/G3_MAIN_EU_WALK_20261127.md) closes pass 20's open (c) [G3 main EU walk](research/G3_MAIN_EU_WALK_20261127.md) closes pass 20's open (c) — main's schedule is now two-image: **EU main = 0x800224D8..0x800227E8** (code-in-data in EU's data_80022A18.data.s row, entered terminally by EU's crt0 jal 0x0C008936 at 0x80047BF8; **EU gp = 0x800ABAB0**), same five phases with every anchor twinned (attract frame wiring = pass 19's census site re-read from the main side; VSyncCallback(0x8002376C) = the EU twin head + the same +0x14 mid-entry offset; dispatcher twin 0x800428D4 head-verified incl. the −1 store +0x850 and the dispatch vector base D_8008B734 = D_8008AF1C +0x818; teardown SDK chain + **LoadExec("cdrom:\\MAINMENU.EXE;1", 0x801FFF00, 0)** with the EU string at 0x80020094); EU boot carries SIX extra calls: **`SetVideoMode(1)` (PAL — the regions' video split made static, JP main never calls it)**, an extra func_8002DEDC-twin call (EU (0,0xBD)+(0xBD,-1) vs JP (0,-1)), an extra func_80024760-twin call (EU 3x vs JP 2x over the +0x840 config-pointer band), and the **0x8002FCCC trio (0x50/0x51/0x52 × 0/1/2) whose JP twin func_8003003C is machine-total unreferenced in g3_jp — the lane's first asymmetrically-wired function** (pass 19's dead-in-BOTH pattern gets a one-sided counter-example; same VA ≠ same entity re-confirmed: JP's own func_8002FCCC is a different 0x38-byte entity); two pass-20 errata land: **call 16 is the game-side two-halfword setter func_8002A2C4 → D_800ABB54/5C (EU twin func_8002A2B4 → D_800AC398/A0 at +0x844), NOT psyq GsSetOrign** (the real GsSetOrign = 0x80027A60 JP / 0x80027A5C EU, same 6-insn body shape, never called from main), and **calls 10/11's "0x4D/0x4E arguments" are dead caller fillers** (both callee bodies overwrite a0 before any read in both regions; EU leaves 0/1); main's own data-band map measured: +0x844 gp/pair/fixed-stores-A, +0x840 config pointers, −0xF7B0 fixed-stores-B (0x800BC3C4 → 0x800ACC14 family), +0x850 fixed-stores-C, +0x8E8 TIM-loader data, +0x124 service base, ±per-library shifts (LIBETC −0x5C0, LIBGPU −0x690, LIBSPU +0x990, LIBMIDI +0xBA8); EU's PadStop site = 0x80026D48, a game-side 7-insn wrapper body-identical to JP's sdk-region func_8004B074 (not where a band shift predicts); the pass-24 note [G3 gameinfo fields](research/G3_GAMEINFO_FIELDS_20261127.md) closes the refreshed questions (a)+(b) in one pass: the set_game_info binding is now INSTRUCTION-VERIFIED per case (the register fact that fixes it: in the setter cases a1 = the flag cell 0x80010000 and s1 = the flag-selected record base, so mission/TV_MODE live in the flag cells while LEVEL = record+0x0, PARTNER NAME = record+0x4 with strlen<10, PLAY_RECORDING = +0xE, CLEAR_LEVEL = +0x10 with the +0x12 bitfield clear tail, PAUSE_DISP = 0x80010B28, MUTEKI_MODE = 0x80010B2C, MAP_COUNTER_DISP = 0x80010B2E, TUNE_LEVEL = 0x80010B34, SUPER_BLASTER = record+0x536, PARTNER_G_NUM = record+0x534, with ids 3/9/0xD/0xE/0x11 unvalidated bare stores; the string order is NOT the id order - the pass-23 table-order guess is superseded; the id-0xC cross-base consistency closes: the setter stores s1+0x536 = exactly the two words the getter's slot probe reads at a1+0x5EE/a1+0xB26); the pilot loader's three writes decoded (set_game_info(3,-1), set_game_info(4, runtime-RAM string at 0x800BB2B0), set_game_info(0x10, func_80045C10()>>16)); **get_player_info = func_80025C1C pinned** (id space 0x10..0x58 offset -0x10 with the 0x49 range check, jtbl_80020660, stride-0x2C records at base 0x80010008) and both 73-slot tables are mapped: 22 live fields (ids 0x10..0x12, 0x20..0x24, 0x30, 0x40..0x42, 0x50..0x58 at the scattered head+6 offsets 0x0..0x24) with 51 slots error-padded loud; the caller censuses: get_player_info x5 / set_player_info x3, ids 0x10/0x11 dominant, record indices from the below-image cells 0x80010E04/06/08 and D_800ABE44, and the metric formatter's set_player_info(0x10, rec, 1/0) flag pair; get_player_info banks in curated closing pass 23's deliberate hold; the pass-23 note [G3 gameinfo accessors](research/G3_GAMEINFO_ACCESSORS_20261127.md) closes pass 20's item (e) — the getter func_80025944 is **get_game_info() of gameinfo.c**, named by its own __FILE__/__LINE__ printf ("%s(%d):Invalid mode switch in get_game_info()" with a1 = the literal "gameinfo.c"); the complete 18-id map lands from jtbl_80020480 (id 0 = the 0x80010000 flag itself, ids 8..0xB/0xD..0xF/0x11 = the 0x80010B28..0x80010B37 halfword array, ids 2..7/0x10 = the flag-selected record base 0x800100B8/0x800105F0 — the pass-20 "stateful slot-2 wrinkle" resolved mechanically as that base selection, id 4 = the POINTER return record_base+4, id 0xC = the slot-free probe with ZERO g3_jp callers), the caller census is complete (35 sites: 25 asm rows + 10 raw jal words inside the code-in-data pilot loader func_8002278C, every id except 0xC called), and the family extends: **set_game_info = func_80025590** (the write twin, jtbl_80020408, per-field validation strings naming the schema: mission / TV_MODE / PAUSE_DISP / MUTEKI_MODE / MAP_COUNTER_DISP / TUNE_LEVE / LEVEL / PLAY_RECORDING / CLEAR_LEVEL / PARTNER_G_NUM / SUPER_BLASTER at gameinfo.c lines 200..243), **set_player_info = func_80025AD8** (73 fields, id < 0x49, stride-0x2C records at base 0x80010008, jtbl_80020500) with **get_player_info** located by its error tail func_80025D94 but deliberately unbanked until its entry is pinned, the reset func_800252A8 wipes the block header, the whole block lives below the payload (the module-swap-surviving resident region), and the metric-rank tail shows the game WRITING BACK (set_game_info(6, get_game_info(2)) at attract_outcome == 1); three function names banked INERT in curated (get_game_info / set_game_info / set_player_info — each named by its own printf, the strongest evidence class); WORK_QUEUE R1 paragraph retitled twenty-three runs; the pass-22 note [G3 exit-guard owners](research/G3_EXIT_GUARD_OWNERS_20261127.md) closes pass 21's open (a)-(c) with complete owner censuses for both exit machines' guard words: the button-bit word *(s1) is NOT the pad buffer - s1 = the bss slot-state array at 0x8014772C (halfword stride 2, parallel array D_801474E4, written only by the vsync mode machine itself: `sh 3` at 0x80023880 after the executor ack and `sh zero` at func_80023884; bit 0x10 = the mode-2 exit request, bit 0x1 = the sibling's scripted-counter request; pad lane untouched); gp+0xA = 0x800AB276 is the vsync grace countdown - re-armed 0x32 by func_8002377C every tick while the mode word is neither 2 nor 0x32, decremented by func_80023910, and the mode-5/tick2==4 exit arm requires it fully decayed to 0; D_800AC164 is the mode-4 step counter - armed by func_80022F24 from getter(9)'s return (1..6 at mode 4, a new getter id for the map), cleared in the " WAIT_STEP0" (func_80042F18) and func_800447A8 packs, +1 per func_80043730 step call, -1 per func_800239F4 tick, exit arm (+ script cmd 0x35) at 0; D_800ABF9C is the attract timeline variant selector - sole writer func_80030838 (the two-variant checkpoint-pack initializer: variant A checkpoints 50/95/140/185/230/275/320/365/410 + D_800ABE34=490, variant B 55..451 + 420), whose ONLY caller is main's raw jal word 0x0C00C20E at 0x800224EC with a0=0, so variant B is static-dead and the selector is a constant-0 switch for ~40 readers (the pass-19 dead-twin shape); D_800ABFC4 is the attract outcome selector - 1 = VICTORY_INIT (func_80041B98/func_80041C08), 2 = DEFEAT_INIT (func_80042054) / DEAD_END (func_800423C0) / func_80041AEC, and outcome 2 picks the higher exit threshold; D_800AC294 is the STAR_MODE7 length mirror - sole writer func_80022EC8 = (StGetNext record +0x8) << 1 via func_8002B20C (the record pointer D_800ABB74 = the StGetNext out pointer), re-derived per service tick, not an accumulator; the gate errata: FOUR threshold sites not three (the missed fallthrough tier func_80043F70 = 0x141E = 5150) and 0xC78 = 3192 not 3200, with the live tier map outcome 2 -> 5880 / else 3192; six game data words banked INERT in curated (attract_variant / attract_outcome / attract_stream_len2 / attract_step_cnt / vsync_grace_cnt / st_next_rec, all g3_jp-unique, no sdk placement, zero new curated collisions, suite 299/299); the pass-21 note [G3 exit-flag census](research/G3_EXIT_FLAG_CENSUS_20261126.md) closes pass 20's reboot-trigger question: D_800AC4F4 (the dispatcher exit flag) has exactly FOUR writer sites in TWO machines, every one storing 1 and no zero-writer anywhere in the static image (gp+0x1288 alias checked - none) - the flag is write-once-per-load and only the crt0 bss-zero clears it; machine A = the vsync-side mode machinery in the registered-vsync row: func_8002366C (the button-bit 0x10 exit at mode 2, the sibling tail firing executor command 0x36), func_80023D14 (mode D_800AC5AC==5 AND s3==4 AND *(gp+0xA)==0), func_80023D24 (the D_800AC164 counter expiry, which ALSO fires script command 0x35 through the pass-15 executor); machine B = the dispatcher-row attract timer: func_80043EEC runs func_80022DE0("STAR_MODE7"), gates on D_800ABF9C/D_800ABFC4 and compares the length word D_800AC294 against the three mode-keyed thresholds 0xC78/0x16F8/0x1E76, then func_80043F80 either exits immediately or lets the D_800ABE7C countdown expire and stores the trio D_800AC5AC=1 / D_800ABE94=0 / D_800AC4F4=1; the dispatcher's reader is instruction-pinned (lh at 0x80042D24, bne v1,1 back to 0x80042C90, else jal func_8002AD24 and return); the pass-20 note [G3 main flow decode](research/G3_MAIN_FLOW_DECODE_20261126.md) decodes main (0x800224C0..0x80022788) instruction by instruction and lands the module's top-level schedule: 49 call sites in five phases (boot / attract / service setup / game loop / teardown+reboot), the attract tier is the frame function func_8002FC68's own private frame engine (probe + service chain + the func_8002FDB8 loop: state word D_8016AEB0, the video-prep pair func_8005E6C4/func_8005E740, music driver 1 func_8002FF48 whose return 1 is the primary exit, OT clear, VSync(4), GsSwapDispBuff, func_8002AC04, GsDrawOt), the vsync clock is registered only AFTER attract returns (VSyncCallback(0x8002370C) = a mid-entry of the sound orchestrator func_800236F8, the D_800ABE4C countdown + D_800AC5AC mode-counter machinery), the game loop is the master dispatcher func_80042C6C (loops while D_800AC4F4 != 1, the 8-way mode dispatch per iteration = the per-scene tier), and the teardown tail ends in LoadExec("cdrom:\\MAINMENU.EXE;1", 0x801FFF00, 0) - the module-swap reboot back to the launcher, which is why the crt0 continuation has only data words after jal main (main is the terminal call); the boot pilot loader func_8002278C (the second code-in-data function) decodes as the pilot/data setup: getter(3)==1 gates the pilot chain, getter(4) = the name string strcmp'd against "FRANK"/"REIKO"/"JOHNSON"/"SHARK" writing bit masks 1/2/4/8 to *(0x800AB284), "GHOST" diverts to the ramp chain, the default path runs the binding layer func_80026D6C and builds "\\DRAGOON\\%s%d.DAT;1" via func_8004803C + loads via func_80024954 with the "card load err(%d) name = %s\n" report; the pass-19 0x8BE divergence constant is confirmed in situ at 0x8002FCB4 as the a0=0 variant's s1; gp = 0x800AB26C fixed from the crt0 lui/addiu pair; the pass-19 note [G3 music-lane EU twins](research/G3_MUSIC_LANE_EU_TWINS_20261126.md) closes pass-18's scheduler/driver-2 question - g3_eu carries the same two entry-less shapes: the EU scheduler twin func_800299D4 and driver-2 twin func_8002FC48 (verified by normalized word alignment plus full hand reads) hold ZERO static references of any form in g3_eu (real-name census over 586 files, .word sweep, raw hi/lo scan all empty), so the pair is machine-total unreferenced in BOTH retail images and stays dead-variant unless a runtime trace fires it; the EU caller census otherwise mirrors pass 18's JP counts 1:1 (tick 2 <- 3 callers, binding <- 4 jals + main's data word 0x0C009B5A, driver 1 <- the frame function's jal, frame function <- main's data word 0x0C00BE3E, snapshot 2, evaluator 40 internal), the initializer is the EU scene-reset twin's fallthrough tail (byte-read), the pass banks two census traps (the .s comment word column is byte-reversed so the caller census's code-enc path is inert - census by the REAL carve names; EU glabel func_8002FFB8 is a render-function branch-join, NOT JP's driver 2: same VA, different entity) and records the lane's first code-side JP/EU divergence (EU frame branch pack s1=0x8BC vs JP 0x8BE); tools/audit_eu_twins.py lands the normalized-alignment twin finder; the pass-18 note [G3 music-lane callers](research/G3_MUSIC_LANE_CALLERS_20261125.md) corrects pass-17's empty census with the intra-row lesson (splat rows are carve units - chunk-to-chunk calls inside one row file are real references) plus the un-split main living in two data rows, anchors tick 1/tick 2/initializer/driver 1/the dispatcher to main end to end, leaves exactly the scheduler + driver 2 unreferenced (machine-total), and lands tools/audit_caller_census.py; the pass-17 note [G3 music-lane dispatch](research/G3_MUSIC_LANE_DISPATCH_20261125.md) decodes the four-lane music engine end to end (per-lane records at D_80165242 stride 0x44, the dispatcher's 2/4/8/default map, the four handlers' shadow writes, the tick skeleton, the request evaluator's classes and budget, the two ramps, the binding layer's tag-to-mode map 0x12->2/0x23->4/0x41->1/0x53->8); the pass-16 note [G3 sound boot chain](research/G3_SOUND_BOOT_CHAIN_20261125.md) closes pass-15's tone-table writer question — the full sound init at 0x80029C24 loads fload3("\SE.VH;1") (the 0x8620-byte 63-program VAB header), parks an inlined copy in the below-image resident region at 0x80016604 (0x80016600 = the vab id, 0x8001EC24 = the SPU body address; all three survive module swaps), opens it with SsVabOpenHead, streams the \SE.VB;1 body via snd_fload3_TransBody, and the SsUtGetVagAtr loop (progs 0..0x3D) fills the tone array D_800CFF84..0x800D0744 whose record bytes +4/+5 are psyq's VagAtr.center/.shift — exactly the executor's noteByte/fineByte; the voice cache D_800D0744 is executor-write-only and keyoff-read-only (strict census, the loose-sweep "consumers" exposed as byte-column false positives); the boot-chain caller census: slps/sces/mainmenu_eu run the full init, the g3-family modules re-attach only (SsVabFakeHead/FakeBody over the resident state) and the re-attach's own SsUtGetVagAtr loop re-fills all 62 records from the FakeHead-registered resident header — the crt0 bss-zero wipes the array per module load and the re-attach repairs it before any script runs, so the module-swap sound model closes with no open remainder (a same-window correction to the note's first reading); the pass-15 note [G3 script note-on semantics](research/G3_SCRIPT_NOTE_ON_20261125.md) decodes the handler executor func_80029FC0 end to end — every script command is a psyq SsUtKeyOn VAB note-on (prog = handler id, volumes = per-program multiplier x global L/R scalers, tone bytes from the runtime table D_800CFF88), the callee identity proven on four legs (sig-db 27/27 row alignment + LIBSND.H prototypes + the keyon/set-VVol error strings + the single-caller census), 10 direct-fire sites with hardcoded progs mapped; the pass-14 note [G3 script absent-command resolution + EU pin](research/G3_SCRIPT_ABSENT_COMMANDS_20261125.md) closes both pass-13 open questions (no second consumer anywhere — cursor/stream/labels/tables swept; no table patcher; absent commands advance the stream and consume the once-latch; the counter clock + latch lifecycle + mode-handler vector decoded; the complete EU twin machinery pinned and the EU corpus machine-compared — the 3 mode-1 variant scripts are the only JP/EU divergence: JP absent band vs EU present payloads over identical gates); the pass-13 note [G3 script stream corpus](research/G3_SCRIPT_STREAM_CORPUS_20261124.md) decodes the {frame-gate, payload} two-channel format and the whole mapped corpus; the pass-12 note [G3 script interpreter + 4-lane rank](research/G3_SCRIPT_INTERP_LANE_RANK_20261124.md) decodes the two remaining unnamed slot-4 stage helpers, the 46-command script table and the script stream base; the earlier eleven:
[G3 render preparation](research/G3_RENDER_PREP_ATLAS_20261122.md)
identifies staging/submission;
[HUD/font queue and outer frame loop](research/G3_HUD_QUEUE_FRAME_LOOP_20261122.md)
recovers Psy-Q GsOT, ten-entry font queue and game frame;
[mode sequence atlas](research/G3_MODE_SEQUENCE_ATLAS_20261122.md)
enumerates eight game-state callbacks and submodes;
[FOBJ sprite-path atlas](research/G3_FOBJ_SPRITE_PATH_20261122.md)
proves a 100×6-byte 2D sprite command queue, 12-way display-state
dispatcher and GsSortSprite OT submission; the
[3D TMD polygon-path atlas](research/G3_TMD_GEOMETRY_TO_OT_20261122.md)
proves **descriptor creation → GsLinkObject4 → 0x6C-byte
3D scene records → GsSortObject4J-like dispatcher → GsTMDfast*
polygon packet insertion → GsDrawOt** in JP, with EU corroboration; and the
[communication buffer schema](research/G3_COMM_BUFFER_SCHEMA_20261122.md)
now proves `D_80166360` is a **per-frame immediate-mode 0x18-byte request
pool** (literal "Communication Buffer" string evidence) with a bump
allocator, 756-record capacity gate, laser (`mylaser.c`) and object-spawn
producer systems, the corrected dispatch consumption rule and the 0x6C
record field map; and the [producer records atlas](research/G3_PRODUCER_RECORDS_20261122.md)
decodes both producer pools — `D_8016B014` (124 × 0xAC objects, two scan
bounds, 256-way type dispatch `D_8008A2F4`, three creation paths, complete
field map) and `D_80163944` (32 × 0x84 lasers, `lsr_mode` lifecycle) — plus
the `D_800ABBE4` 0x14-row model table schema, the `func_80024910`
offset-directory resolver and the `\\DRAGOON\\TMD.DAT;1` loader family,
recording the negative result that the table setter and loaders are
**unreached** in the static g3_jp image — a negative pass 8 then **closed at
byte level on both twins**: every word of the witnessed retail executables
scanned, zero `jal`/`j`/literal/lui-pair references reach the block, all
branch hits branch-internal (the block is branch-closed), leaving only
runtime-computed control flow; pass 8 also decoded the four gameplay handler
bodies (types 0x18/0x19/0x1C/0x1D), extending the object field map into
`+0x34..+0x54`/`+0x6C..+0x84`, mechanizing the `+0x30` resource selector,
and banking the definition-chain step, the 0x31 type morph, the laser-contact
resource link via `+0x2A`, the camera-anchor triple and the EU model table
`D_800AC428`.

**Next specific R1 questions:** (a) the gameinfo field SEMANTICS at runtime — what the player record's 22 fields hold and the below-image cells 0x80010E04/06/08's roles (runtime territory; a PCSX-Redux trace per RUNTIME.md would name them); (b) the stride-12 work base - what s2 points at in func_80026718's caller frame and who consumes the tick calls' sp+0x10/sp+0x12 stack-buffer outputs; (c) the attract state timer D_800ABE7C's per-state value map (the ~50 dispatcher-row re-arm sites) - a census fact for the attract-machine owner, not named in pass 22; (d) the scheduler + driver 2 runtime question is now two-image machine-total (pass 19) - only a PCSX-Redux trace per RUNTIME.md could revive either entry; (e) the standing pass-11 runtime question, whose static half is closed: the PCSX-Redux trace per RUNTIME.md — pass 11
(atlas §16) closed the request→render-surface chain end to end: the consumer
constructors decode per case (case 0/4 camera-relative words minus the
D_8016AC18/1C/20 anchor, case 1/5 absolute halfword coordinates, case 3/7
halfwords through the `func_800326A8` transform, case 0xE the laser
constructor with id+8 and the forced type-3 word), the shared builders
`func_8002E4B8` (world) / `func_8002E770` (projected, which hard-rejects
kind 7 — dead end-to-end), and the two resource lookups
`func_8002F368` (world/TMD; head = `lw(D_800ABBE4)`, 0x14-byte rows) and
`func_8002F3D4` (projected/sprite; head = `lw(D_800ABBEC)`, 0x34-byte rows).
Since both tables image-initialize to 0 and the game renders, the tables
MUST be populated at run time — the sharp PCSX-Redux question is now "what
writes the two table head pointers at runtime"; optionally `func_800326A8`
to label the case-3/7 coordinate space. The render arrays are
proven frame-local staging; do not convert builders before a producer-side
landing decision.
**Owner/SDK provenance gate:** EU `src/func_80052038.c` is an
already retail-matched C row (historical claim), but functions as
a Psy-Q **`GsSortObject4J`-like** TMD dispatcher. Investigate
archive/member evidence separately; **do not rename or change its
C row/coverage ownership unilaterally**. Packet-workbuffer allocation
bounds, sprite resource `0x707`, and current retail oracle remain open.

**Target:** `g3_jp` first; `g3_eu` for comparison.

**Why:** Current C coverage includes abundant SDK members and wrappers,
while the meaningful main-game code remains poorly classified. A
game-specific map gives the next matching campaign high-value targets
rather than another pass over identical glue functions.

**One-run scope:** choose exactly one coherent contiguous game-code
region or function family **not already settled** in TASKS.md, and:

1. Establish row/ROM/VA extent with `config/splat.g3_jp.yaml`, asm
   labels, any nearby data pointers, call targets and candidate function
   entry/exit boundaries.
2. Check ownership: SDK member/window evidence
   (`config/sdk_anchors.txt`, `tools/sdk_members.py` outputs) vs
   game-owned code; report ambiguities.
3. Cross-check EU offsets/call graph when possible; distinguish exact
   byte twins, address-shifted siblings, and inferred analogues.
4. Explain **gameplay or state responsibility** in terms of observable
   writes/reads/dispatch; avoid invented names and interpretative leaps.
5. Produce an evidence table (address/extent, backing path, xrefs,
   verified vs inferred) and rank one or two feasible future semantic-C
   conversion candidates. Record a negative result when evidence rules out
   a candidate.

**Deliverable:** a short source-linked investigation, appended to a
*focused* durable subsystem document or a standalone research note;
cross-link from [RESEARCH_LOG_INDEX.md](RESEARCH_LOG_INDEX.md). No source
changes unless the full oracle is available and a separate landing
decision was made.

**Done for a run:** at least one NEW conclusion or clearly demonstrated
negative/blocked finding, with source/offset evidence and the next
specific question. Do not reopen a previously measured region merely to
repeat its summary.

### R2 — Cross-target source reuse and semantic-quality classification

**Passes 1–5 delivered 2026-11-23:**
[the classification sample](research/G3_R2_SOURCE_REUSE_CLASSIFICATION_20261123.md) —
pass 1: 16 shared C rows (x5–x8 instances) fully read and tiered: 7
semantic_c, 9 asm_preserved (the whole sampled GTE math family), 0
hybrid; the three sampled unknown-name rows are GTE compose-rotation
members, not game logic. Pass 2: the origin-unattributed C frame —
10 more rows registered (the g3_jp 0x1CC hand-asm subdivision four-up =
game-owned rendering; SetVertex0-2/ReadSZfifo3/4 = SDK members in an
evidence gap; func_800642A0 g3_eu = the first live hybrid, a real
decompiled SPU-init driver). Pass 3: the g3_eu/mainmenu_eu
unattributed-C singletons — 13 rows fully read and placed against their
live YAML rows: 11 semantic_c (the palette-fade wrapper family with
per-target callee deltas, CD host-command glue, init-driver constant
wrappers, slot-clear trio, fixed-slot stores) + 2 hybrid (the
identity-proven SVM init func_80067690, register pins $5/$4/$2; the
_SN_write write-all loop, `total` pinned to $18), 0 asm_preserved.
Pass 4 (same window): the mainmenu_eu 8-byte mini family — 8 rows of
one empty void function each, the empty body IS the retail two-instruction
return; registered semantic_c (func_80030990 is an R3 Class-B shared
name — classification only).
Pass 5 (same window): the wave/fifo INSTANCE registration — all 30
pending target instances of pass 2's classifications registered at the
four lane-free targets (g3_eu 9, mainmenu_eu 6, g3org_jp 9, g3org_eu
6): the 0x1CC subdivision wave (16 of its 20 instances; every body
byte-identical to g3_jp func_8005A13C modulo the row name, re-verified
mechanically) and the LIBGTE fifo family (19 instances across the five
targets that carry the members); placements double-checked against the
live report and the target YAMLs; mainmenu_jp's instances lane-owned
and untouched. Registry now 90 entries (34 semantic_c / 5 hybrid /
51 asm_preserved, 22,092 reviewed bytes); g3_eu reviewed bytes
3,620 → 5,552, mainmenu_eu 2,340 → 4,224. **mainmenu_eu's
unattributed-C frame is fully reviewed AND registered (4,224 of
4,224); g3_eu's only unreviewed unattributed-C rows are the two gated
ones (func_80052038 owner gate, func_8006AC04 runbook-gated partial);
the g3org singleton populations (g3org_eu 164 bytes / 4 rows, g3org_jp
244 bytes / 9 rows) are the last unregistered non-lane frames. The
remaining R2 value is the boot-target C rows (check the do-NOT-grab
lanes first), the g3org singleton passes, then the asm-row
wrapper-boundary sampling — which overlaps R1; coordinate there
instead of duplicating.**

**Passes 6–7 delivered 2026-11-24 (window cron-20261124-0609):**
pass 6 — the g3org singleton populations: 13 instances over 12 shared
files fully read and registered (8 semantic_c: the empty-void pair +
three palette-fade wrappers per target, callees func_800416D0 /
func_80041AB0; 5 asm_preserved bare hand-asm units at g3org_jp); both
g3org unattributed-C frames close exactly (g3org_eu 2,048 of 2,048;
g3org_jp 2,176 of 2,176). Pass 7 (same window) — the boot-target C
rows: the do-NOT-grab check held (sces's five rows are the fifo
family, not the parked setIntr family; slps's rows are fifo + a
matched live c row), one full read (slps func_80024F00, the boot
targets' first review, hybrid: volatile hand-asm nop + the real C
store boot_flag_0 = 0) plus ten mechanical fifo instance
registrations; sces closes at 92 of 92, slps at 108 of 108. Registry
now 114 entries (42 semantic_c / 6 hybrid / 66 asm_preserved,
22,700 reviewed bytes); fifo registered at 29 of its 30 live
instances (mainmenu_jp's ReadSZfifo4 lane-owned). **The unattributed-C
classification frame is exhausted at every lane-free target: closed at
g3_jp (pass 2), mainmenu_eu (pass 5), g3org_eu/g3org_jp (pass 6),
sces_00269/slps_00270 (pass 7); the only unreviewed unattributed-C
rows left campaign-wide are mainmenu_jp's lane-owned frame and g3_eu's
two gated rows (func_80052038 SDK-ownership gate, func_8006AC04's
44-byte runbook Phase D tail). The lane's remaining value is the
asm-row wrapper-boundary sampling — which overlaps R1; coordinate
there instead of duplicating.**

**Target:** a bounded sample of current `src/` C rows and their actual
target yaml consumers.

**Question:** Which C rows reconstruct behavior, and which are
assembly-preserved, register-pinned, special-rule hybrids or thin wrappers?
What game structures are still opaque?

**Method:** classify no more than 10–20 functions in one pass; use the
per-target `coverage_report.py --json --rows` output to verify which YAML
rows actually compile each source, rather than deducing ownership from
the filename. Extend `config/coverage_reviews.json` only after examining
the **entire** row, and record a narrow evidence-backed tier. Keep binary-match evidence separate from C
semantic quality. Include samples from `g3_jp` where possible.

**Deliverable:** a small reusable evidence-backed classification table,
with links to source/yaml rows, not an unverified global percentage.

### R3 — Read-only status of the retained naming exceptions

**Delivered 2026-11-22:**
[the decision brief](research/R3_SHARED_NAME_DECISION_BRIEF_20261122.md) —
the 13 cross-target names decompose into travelling definition names
(Class A, 15 by-construction mismatches) and the mainmenu pair-family
(Class B, 16 rows + the `func_80030990` sces asm third holder); four options
with costs, a four-rule collision policy, unchanged parked/laned
exceptions. **Awaiting the owner's ratification; no renames made.**
Membership re-checks stay cheap:
`python3 tools/audit_c_names.py --cross --adjudicate`.

<details><summary>Original task text (retired)</summary>

**Target:** the last recorded 13 cross-target shared-name cases,
mainmenu_jp's 20 reserved name/placement rows, and the known parked
memclr/INTR and `func_800629A0`/`func_80036CFC` exceptions.

**Method:** rerun the census/adjudicator and check live YAML ownership,
definitions, curated names and C references. Report changed membership,
owner conflicts, and exact affected targets. **Do not rename, repartition
or automatically "fix" intentional shared-name mismatches.**

**Deliverable:** a decision brief with options for shared canonical name
vs region-local alias, with proposed collision policy and complete impact
surface. This can be worked on without the retail baseline.

</details>

## Ready only with full retail oracle

### L1 — Guarded toolchain roll-out verification

After pulling commit `2d5e0673` or later, on a host with the legally
provisioned baseline and exact historical tools:

```sh
# Guarded compiler rebuild/attestation on an existing checkout:
sh tools/patch_cc1_263.sh
sh tools/rehydrate.sh
python3 tools/toolchain_preflight.py
sh tools/witness_check.sh
for target in slps_00270 sces_00269 mainmenu_jp mainmenu_eu \
              g3_jp g3_eu g3org_jp g3org_eu; do
    make clean
    make verify TARGET="$target" || exit 1
done
```

If the guarded compiler source build is absent, run
`sh tools/build_cc1_263.sh` before the patch script. A clean
`make verify` must **never** fall back to a prebuilt unguarded compiler.
Save exact command/output hashes and record success or the first precise
failure (environment vs source vs oracle).

**Acceptance:** witnessed baseline 8/8 and full-image 8/8 matching
at the **same HEAD**, with the preflight passing; source-only green CI
is not acceptable substitute evidence.

### L2 — Candidate gameplay C conversions

Only after R1/R2 establish boundaries, owners and source hypotheses:
make one bounded C conversion on a dedicated branch, then
`make clean verify TARGET=<target>`. If shared headers, common
translation units or shared source resolution changed, verify **all
eight** executables before merge. A unit-level judge or a good
partial-diff score is not a substitute for image SHA-1.

## Owner-gated or parked; do not schedule as self-directed landings

| Subject | Current rule / unblock condition |
| --- | --- |
| 13 cross-target shared names | Owner chooses naming convention after R3 decision brief |
| mainmenu_jp 20 tool-fair rows | Reserved naming lane; obtain lane handoff/owner direction |
| `func_8006AF70` / `SsSetTickMode` | Owner choice for round-7 4-word mismatch, see DISC_RETURN_RUNBOOK phase C |
| `setIntr` / `GsSetDrawBuffOffset` / 43 size-wrong units | Previously parked, investigate only a **new** mechanism or explicit assigned scope |
| SDK memclr/OMF def-base cases | Require member/ownership evidence; not generic rename or asm-to-C work |
| Tracked extracted retail files and Git-history rewrite | Owner has deferred remediation; preserve history, do not force-push |

## Run protocol for scheduled research

- **One bounded, substantive investigation per execution.** Do not
  default to repeated sweeps, status recaps, mass edits or speculative
  "matching" work.
- **Reconcile first.** Check HEAD, current branches/PRs, focused docs
  and the relevant previous TASKS.md entries. Retire completed work;
  don't restage old tasks based on stale top-of-file queue text.
- **Always provide evidence.** State target, addresses, byte extents,
  source paths, method, verified facts, inferences, negative results
  and unresolved requirements.
- **No-oracle mode:** read-only static research and documentation.
  Do not modify C, assembly, YAML or oracles merely to show activity.
- **Oracle mode:** require a baseline witness, guarded toolchain
  preflight and per-target full-image hashes before any match claim.
- **Progress is not a claim.** `tools/progress.py` is a heuristic
  function-instance census, not a percentage of recovered gameplay.
- **Finish with an exact next step** and mark any decision blocked on
  owner input as **owner-gated**.

New research evidence should live in focused documents where
possible, indexed from [RESEARCH_LOG_INDEX.md](RESEARCH_LOG_INDEX.md).
Keep [TASKS.md](TASKS.md) as historical source, not as an ever-growing
new task queue.
