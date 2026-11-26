# R1 pass 20 — main's flow decode: the g3_jp module's five-phase
# top-level schedule, boot attract loop, and the LoadExec reboot
# back to MAINMENU.EXE

Date: 2026-11-26 (window cron-20261126-1409, job 540513's seventeenth
fire). Scope: g3_jp only, JP-first discipline maintained (the EU
corroboration is a next-pass item — the pass-19 band map already
carries the jal twins). Docs only; zero source, YAML, asm or oracle
change; zero renames.

## The question this pass closes

Pass 18 anchored the music lane end to end but left main itself as
"the un-split main living in the two data rows": a jal-encoded call
map whose ~55 `.word` call sites had no phase reading. This pass
decodes main's body instruction by instruction, assigns every call
site to a run phase (boot / attract / service setup / game loop /
teardown), and lands the module's top-level schedule.

**Verdict: main (0x800224C0..0x80022788) is one straight-line block
with a single internal branch pair and 49 call sites in five phases;
its tail is a full SDK teardown ending in
`LoadExec("cdrom:\\MAINMENU.EXE;1", 0x801FFF00, 0)` — the module-swap
reboot back to the launcher executable, which is why the crt0
continuation has no code after `jal main` (only the stack-size table
words).** Pass 16's module-swap sound model is now proven from main
itself at the flow level.

## Where main lives and how it is entered

- The crt0 continuation (pass 18, the `data_80047F1C` row) runs its
  table-driven SP setup, calls `InitHeap` (0x8004B494, LIBAPI, with
  `addi a0, a0, 4` in the delay slot), then `jal main` (0x0C008930 at
  0x80047F90). The words after the jal's delay slot are data
  (0x0000004D and four 0x00200000 stack-size words, then the row's
  enddlabel) — **main is the continuation's terminal call**; it only
  "returns" in the sense of never returning (LoadExec replaces the
  process).
- main proper sits wholly in the first data row
  (`data_80022878.data.s`, 0x800224C0..0x80022788): prologue
  `addiu sp, sp, -0x48` / `sw ra, 0x40(sp)`, one internal branch pair
  (the probe-failure block, below), epilogue `lw ra, 0x40(sp)` /
  `jr ra` at 0x80022784. The word table jtbl_80022494
  (0x80022494..0x800224BC, twelve pointers into 0x8006DFC0..0x8006E060)
  precedes it and is not main's.
- The refinement to pass 18's "two data rows" phrasing: main + the
  second code-in-data function (the boot pilot loader
  func_8002278C, below) are the pair spanning the seam. main itself
  is wholly inside row one; func_8002278C..0x80022AF8 starts four
  bytes after main's epilogue in row one and continues to its own
  `jr ra` (0x80022AF4) inside row two (`data_80022800.data.s`).
  The "main's data word" jal anchors quoted in passes 16/18/19
  (0x0C00A78B at 0x80022548, 0x0C00BF1A at 0x80022594, 0x0C010B1B at
  0x800226F4, 0x0C009B5B at 0x80022A04) belong to main proper except
  the last, which is inside func_8002278C — the census phrasing
  "main's data word" meant "a code-in-data jal", not "inside main".
- gp is set by the continuation (`lui gp, 0x800B` /
  `addiu gp, gp, -0x4D94`) = **0x800AB26C**; main's boot store
  `sw zero, 0(gp)` at 0x800224E8 therefore clears *(0x800AB26C) —
  the four-word zero block the data row labels D_800AB26C, and the
  same word the vsync handler's mode machinery reads back (below).

## The map — all 49 call sites in true-VA order, phase-tagged

Phase key: B = boot (once), A = attract (nested loop host),
S = service setup (once, post-attract), G = game loop (until the
dispatcher exits), T = teardown+reboot (once). psyq identities from
sdk_members/sig-db; game-side callees stay carve-named (their decode
is the lane's open ledger).

| # | VA | target | phase | note |
|---|------------|---------------------------|---|------|
| 1 | 0x800224C8 | 0x80047EE8 | B | game-side, identity open |
| 2 | 0x800224D0 | SetMem(2) | B | 2 MB main-memory config |
| 3 | 0x800224D8 | ResetCallback() | B | LIBETC |
| 4 | 0x800224E0 | func_8002658C | B | tick-1-adjacent init region |
| 5 | 0x800224E8 | *(gp) = 0 | B | *(0x800AB26C) cleared; vsync machinery reads it back |
| 6 | 0x800224EC | func_80030838(0) | B | game-side |
| 7 | 0x800224F4 | func_80024224 | B | pass 18's scene-reset chain head |
| 8 | 0x800224FC | func_8002FB20(2) | B | game-side; re-called with 0 in teardown |
| 9 | 0x8002250C | func_80024760(*(0x8007179C)) | B | pointer from the config page |
| 10 | 0x80022514 | func_80024AD8(0x4D) | B | |
| 11 | 0x8002251C | func_800250B0(0x4E) | B | |
| 12 | 0x8002252C | func_8002DECC(0x80072FD4) | B | |
| 13 | 0x80022538 | func_8002DEDC(0, -1) | B | |
| 14 | 0x80022540 | func_80024738 | B | |
| 15 | 0x80022548 | func_80029E2C | B | pass 16's sound re-attach (FakeHead/FakeBody) |
| 16 | 0x80022554 | GsSetOrign(0x5A, 0x5A) | B | drawing origin 90,90 (psyq spelling) |
| 17 | 0x80022564 | func_80024760(*(0x800717A4)) | B | |
| 18 | 0x80022574 | func_8002DE2C(0x800717C4) | B | |
| 19 | 0x8002257C | func_8002DE3C | B | |
| 20 | 0x80022584 | func_8002DA58 | B | |
| 21 | 0x8002258C | func_8002278C | B | the boot pilot loader (own section below) |
| 22 | 0x80022594 | func_8002FC68(0) | A | the attract frame loop, a0=0 variant |
| 23 | 0x800225A4 | VSyncCallback(0x8002370C) | S | the vsync clock — mid-entry of func_800236F8 |
| 24 | 0x800225B0 | func_8002A8AC(sp+0x20, 0) | S | the probe; outputs 3 bytes at sp+0x20..22 |
| — | 0x800225C8 | printf("file not found\n") | S | only when the probe returns 0 |
| — | 0x800225D0 | StopCallback | S | ditto |
| — | 0x800225D8 | PadStop | S | ditto |
| — | 0x800225E0 | exit | S | ditto — boot-fatal |
| 25 | 0x80022600 | func_8002A7B4(sp+0x18) | S | arg bytes copied from the probe outputs |
| 26 | 0x8002262C | ClearImage({0,0,512,480}, 0,0,0) | S | full-frame black fill |
| 27 | 0x80022634 | DrawSync(0) | S | |
| 28 | 0x8002266C | func_8002A830(D_8016AEA8, 0,0,0) | S | service base shared with the attract chain |
| 29 | 0x8002268C | func_8002A720(D_8016AEA8, sp+0x18, func_8002AAB0, 0) | S | callback registration, same as attract |
| 30 | 0x800226A4 | func_8002ADA0(D_8016AEA8, *(0x800BBA9C), 2) | S | *(0x800BBA9C) just stored = 0x7530 |
| 31 | 0x800226AC | SetDispMask(1) | S | |
| 32 | 0x800226F4 | func_80042C6C | G | the master dispatcher (HUD note section 6) |
| 33 | 0x800226FC | func_80022B6C | T | |
| 34 | 0x80022704 | func_800265E4 | T | |
| 35 | 0x8002270C | func_8002A7D8 | T | |
| 36 | 0x80022714 | func_8002FB20(0) | T | the boot call's sibling, arg 2 -> 0 |
| 37 | 0x8002271C | func_80024738 | T | |
| 38 | 0x80022724 | StopCallback | T | |
| 39 | 0x8002272C | ResetGraph(3) | T | |
| 40 | 0x80022734 | PadStop | T | |
| 41 | 0x8002273C | SpuQuit | T | LIBSPU |
| 42 | 0x80022744 | SsEnd | T | LIBSND |
| 43 | 0x8002274C | SsQuit | T | LIBSND |
| 44 | 0x80022754 | _96_remove | T | CD-ROM driver |
| 45 | 0x8002275C | _96_init | T | re-init ahead of LoadExec's disc access |
| 46 | 0x80022774 | LoadExec("cdrom:\\MAINMENU.EXE;1", 0x801FFF00, 0) | T | the reboot |

Fixed-word stores interleaved with the service-setup phase:
*(0x800BBAA4)=1, *(0x800BBA9C)=0x7530 (read back as call 30's a1),
*(0x800BC364)=4, *(0x800DD1E4)=0, *(0x800DD3E4)=0, *(0x800DCF E4)=0,
halfword *(0x800BC4F4)=0, and *(0x800BC3C4) |= 0x20 (the pass-18
request-mask word family at 0x800BC3C4).

## The five phases, with the evidence that fixes each boundary

1. **Boot (calls 1-21, once).** SDK bring-up (SetMem, ResetCallback),
   the scene-reset chain (pass 18), the sound re-attach (pass 16),
   GsSetOrign, and the boot pilot loader func_8002278C. Nothing here
   recurs: main runs each site exactly once.
2. **Attract (call 22, nested loop).** func_8002FC68(0) is the
   attract frame engine and loops internally (section below); it
   returns when its music driver signals done. This is the only
   call site of the frame function (pass 19's census), so the
   attract phase runs once per module load, before any dispatcher
   iteration.
3. **Service setup (calls 23-31, once, after attract returns).** The
   vsync clock is registered only here — the attract loop polls its
   own driver and runs without the vsync machinery; the dispatcher
   phase inherits it. The probe (a1=0 here; the attract twin used
   a1=4) gates a boot-fatal failure path that prints "file not
   found\n", stops callbacks/pads and calls exit(). The service
   chain (func_8002A7B4 / func_8002A830 / func_8002A720 with the
   func_8002AAB0 callback / func_8002ADA0) re-arms the same
   D_8016AEA8 service the attract chain armed, this time with a2=2
   (attract used s5=1) and a1 = the just-stored 0x7530.
   ClearImage({0,0,512,480}) + DrawSync(0) black-fill the full
   double-height frame before the dispatcher's first iteration.
4. **Game loop (call 32, until D_800AC4F4 == 1).** The master
   dispatcher per the HUD note's section 6: graphics/MDEC prep, the
   stage helpers, the font-queue reset, the eight-way mode dispatch
   (jalr through D_8008AF1C — per-scene), the render submit
   func_80022FE4, the exit check. **The per-frame tier of this
   module is the dispatcher's loop body; the per-scene tier is the
   eight mode callbacks it jalrs through; the boot-only tier is
   phases 1-3; there is no per-frame work left in main proper.**
5. **Teardown+reboot (calls 33-46, once, after the dispatcher
   exits).** Game-side closes (func_80022B6C / func_800265E4 /
   func_8002A7D8), func_8002FB20(0), then the full SDK teardown
   (StopCallback, ResetGraph(3), PadStop, SpuQuit, SsEnd, SsQuit,
   _96_remove, _96_init) and LoadExec back to
   cdrom:\\MAINMENU.EXE;1 with the stack top 0x801FFF00. The
   dispatcher's exit flag D_800AC4F4 == 1 is therefore the
   "return to launcher" trigger — who sets it stays open (the
   vsync-clock family and the mode machinery are the suspects).

## The attract frame engine (func_8002FC68, a0=0 variant)

- Entry head 0x8002FC68..0x8002FCB8: a0=0 selects the variant with
  a1=4, s5=1 and **s1 = 0x8BE — the pass-19 JP/EU divergence
  constant, confirmed in situ at 0x8002FCB4** (EU carries 0x8BC in
  the same branch pack); a0!=0 selects a1=2, s5=2, s1=0xA4E.
- Probe func_8002A8AC(sp+0x18, a1) — fail prints D_80020B64
  ("file not found\n", a second copy at 0x80020B64) and runs the
  same StopCallback / PadStop / exit() death path as main's.
- The setup chain mirrors main's service setup (func_8002A7B4 with
  the probe bytes, func_8002A830, func_8002A720 with the
  func_8002AAB0 callback, func_8002ADA0 with the literal 0x7530
  here vs main's re-read of the stored 0x7530, SetDispMask(1)).
- Loop head func_8002FDB8: read the state word *(D_8016AEB0), index
  the pointer table at D_8016AEA8 (s3) by it, and run the video
  prep pair func_8005E6C4 / func_8005E740 (the render-prep atlas's
  helpers); ramp func_8002ADA0; a -1 ramp return exits. The gate
  func_8002B20C(sp+0x38) fills the word compared against
  (s4+s6+s7)>>1 — a progress measure against the s1=0x8BE-derived
  bound; passing it exits. Then **jal func_8002FF48 — music driver
  1 (pass 18's frame-function caller anchor); its return value 1 is
  the loop's primary exit**.
- The render half: GsGetActiveBuff, the OT clear (0xF0-byte stride
  at D_8016AF20; s2 = *(sp+0x38) - the active buffer id),
  func_8003025C when fp==1, func_8002AB5C (render/HUD drain), then
  **VSync(4) -> GsSwapDispBuff -> func_8002AC04 -> GsDrawOt -> back
  to the loop head**. Exit paths converge on func_8002FF0C, which
  calls func_8002AD24 — the same close-out the master dispatcher
  calls on its own exit.
- So the attract tier is a complete private frame engine (own OT,
  own swap, own VSync(4)) that renders and drives the music until
  driver 1 declares the attract finished; only then does main arm
  the vsync clock and enter the dispatcher.

## The boot pilot loader (func_8002278C, the second code-in-data
## function)

0x8002278C..0x80022AF8, called from main's boot phase (call 21).
Its verified skeleton:

1. func_8003044C first; getter(0x11); **when it returns 1, jal
   func_800299BC** — the scheduler func_800299D8's immediate
   predecessor (the music-dispatch note's row).
2. getter(2) -> s0: the numeric switch over {1,2,3,4,6,7} stores the
   mapped value to *(0x8009AF40) (the pass-14 mode-handler-adjacent
   word). getter(0xF) != 0 routes to the second switch with the same
   join.
3. getter(0xA) -> *(0x800BBF84); getter(5) -> a1; `sltiu a1, 4`
   picks **func_800459D4(0) vs func_800459D4(2)** — the record-load
   pair.
4. **getter(3) must return 1** or the whole pilot chain is skipped
   (bne straight to the tail store).
5. getter(4) -> s1 = the pilot-name string. The strcmp chain
   (0x8004800C, LIBC) against the six name strings at
   0x800AB288..0x800AB2B0: **"FRANK" -> mask 1 (s2), "REIKO" -> 2,
   "JOHNSON" -> 4, "SHARK" -> 8**, each match stored to
   *(0x800AB284) — the pilot id is a bit mask. "GHOST" is matched
   separately: a GHOST name diverts to the ramp chain
   (func_800459D4(a1=-1), func_80045C10, func_80025590(0x10, mask))
   and skips the loader; the default path runs the binding layer
   jal func_80026D6C (pass 18's anchor), then
   func_8002B22C(-1, getter(0), 4, sp+0x20) with the sp+0x24/28/2C
   pointer trio, func_8002B520(getter(0), 0), and the memory-card
   error report printf("card load err(%d) name = %s\n",
   0x800200AC) when the compare against s2 fails. The "NONE"
   string (0x800AB2B0) feeds a late func_80025590(4, &"NONE") call
   whose exact semantics stay open.
6. The mask switch (v1 = *(0x800AB284), values 2/4 and the default)
   picks a3 in {1,2,3} and calls
   func_8004803C(0x800AD614, "\\DRAGOON\\%s%d.DAT;1",
   getter(2)-string, a3) — **the DRAGOON pilot data filename
   builder** (0x800AD614 = the path buffer) — then
   func_80024954(0x800AD614) loads it (adjacent to the producer
   atlas's offset-directory resolver func_80024910).
7. Tail: halfword *(0x800BBE44) = the result, epilogue.

One honest wrinkle: getter(2) is read twice with different roles —
the early read feeds the numeric switch (small ints), the late read
(after func_800459D4's load) feeds the %s of the DRAGOON filename.
Either the accessor is stateful or the load rewrites slot 2; marked
open, not guessed.

## What this closes and what it opens

Closed: the pass-18 census's top-level schedule question — every
"main's data word" jal now has a phase; the module-swap model has
its flow-level proof (LoadExec back to MAINMENU.EXE); the attract
tier is a complete private frame engine; the vsync clock's
registration point is exact; the pass-19 0x8BE constant has its
in-situ anchor.

Open (the next questions, in the lane's order):
(a) who sets D_800AC4F4 = 1 — the dispatcher exit / reboot trigger
    (the vsync-clock family func_8002334C/384/C8/D8 and the
    *(gp) word the vsync machinery reads are the suspects);
(b) the getter func_80025944 id map (0x11, 2, 3, 4, 5, 0xA, 0xF and
    the stateful slot-2 wrinkle);
(c) the EU corroboration of main's map in one pass (the pass-19
    band map already carries the jal twins; a g3_eu walk of its
    main twin would make the schedule two-image like the rest of
    the lane);
(d) the word table jtbl_80022494's twelve pointers into
    0x8006DFC0..0x8006E060 (string pointers?) and their consumer;
(e) the fixed-word stores' owners (0x800BBAA4 / 0x800BBA9C /
    0x800BC364 / 0x800BC3C4 family) as named data rows.
