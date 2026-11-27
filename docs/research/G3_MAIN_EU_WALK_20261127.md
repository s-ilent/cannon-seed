# R1 pass 25 — the EU corroboration of main's flow decode: g3_eu's
# main is the same five-phase schedule with six extra boot calls,
# a PAL SetVideoMode the JP build never makes, and the first
# asymmetrically-wired function in the lane

Date: 2026-11-27 (window cron-20261127-0609, job 540513's nineteenth
fire). Scope: g3_eu as the comparison image for pass 20's g3_jp main
decode (JP-first discipline maintained: the JP side is pass 20's
machine reading and is not re-derived). Docs only; zero source, YAML,
asm or oracle change; zero renames; zero curated banks.

## The question this pass closes

Pass 20's open item (c): the EU corroboration of main's map in one
pass — a g3_eu walk of main's twin to make the schedule two-image
(the pass-19 band map already carried the jal twins). The walk
verifies where EU's main lives, who enters it, that its five phases
mirror JP's, what its teardown tail does, and where the regions
actually diverge.

**Verdict: g3_eu's main is a 1:1 structural mirror of pass 20's
schedule — same phases, same anchors, same LoadExec("cdrom:\\
MAINMENU.EXE;1", 0x801FFF00, 0) reboot tail — with exactly six extra
boot-phase call sites, one of them `SetVideoMode(1)` (PAL), the
regions' video-mode split made static. The walk also lands two pass-20
errata (the 0x5A/0x5A call is NOT psyq GsSetOrign; the 0x4D/0x4E
arguments are dead caller fillers) and the lane's first
asymmetrically-wired function (a TIM loader dead in JP, called 3x by
EU's main).**

## Where EU's main lives and how it is entered

- EU main = **0x800224D8..0x800227E8** (sp -0x50, saves ra/s1/s0;
  epilogue at 0x800227D8..E8). It sits as code-in-data inside EU's
  data row `data_80022A18.data.s` (listed inside the jtbl_800224AC
  carve), the EU twin of JP's main-in-data-row shape — the carve seams
  differ (JP's main is the whole first data row; EU's main starts
  mid-row after jtbl_8002244C/jtbl_800224AC, and EU's pilot loader
  twin 0x800227EC continues into the separate data_800227EC row).
- Entry: EU's crt0 continuation (row `data_80047B84.data.s`, the twin
  of JP's data_80047F1C) runs the table-driven SP setup, calls
  InitHeap (0x8004AE04, delay `addi a0, a0, 4` — same delay word as
  JP), then **`jal main` = word 0x0C008936 at 0x80047BF8** (JP:
  0x0C008930 at 0x80047F90), followed by the same data words
  (0x0000004D and four 0x00200000 stack-size words) — main is the
  terminal call in both regions.
- **EU gp = 0x800ABAB0** (continuation `lui gp, 0x800B` /
  `addiu gp, gp, -0x4550`; JP 0x800AB26C — the +0x844 below-image
  band). main's boot store `sw zero, 0(gp)` therefore clears
  *(0x800ABAB0), the twin of pass 20's *(0x800AB26C) clear.

## The five phases — the EU call map at the anchors

Phase boundaries hold as pass 20 fixed them; EU's site VAs run
0x800224D8 + (JP VA − 0x800224C0) at the anchors. Key sites, all
instruction-read in the EU row:

| Phase | JP (pass 20) | EU twin | evidence |
|---|---|---|---|
| boot: timeline init | call 6 func_80030838(0), delay a0=0 | jal 0x800304A0, delay 0x00002021 | same delay word; the pass-22 sole-writer's twin |
| boot: scene-reset chain | call 7 func_80024224 | jal 0x80024284 (+0x60 band) | head hand-read |
| boot: pilot loader | call 21 func_8002278C | jal 0x800227EC (+0x60) | carve glabel |
| attract | call 22 frame func(0), `.word 0x0C00BF1A` @ 0x80022594 | `.word 0x0C00BE3E` @ 0x800225F8, delay a0=0 | pass 19's verified census site, re-read from the main side |
| service: vsync clock | call 23 VSyncCallback(0x8002370C) | VSyncCallback(0x8002376C) via jal 0x8004A0E8 | 0x8002376C = the EU tick-2-consumer twin head 0x80023758 + **the same intra-function +0x14 mid-entry offset** as JP's 0x8002370C vs func_800236F8 |
| service: probe + death path | calls 24 + the printf/StopCallback/PadStop/exit quartet | jal 0x8002A89C (−0x10 band), delay a1=0; printf 0x80047C54 on 0x80020084 "file not found\n" (JP copy 0x80020070); StopCallback 0x8004A14C; PadStop 0x80026D48 (below); exit 0x800488A4 | all four death-path targets read |
| service: ClearImage+DrawSync | calls 26/27 {0,0,512,480} | 0x8004B4F8 / 0x8004B364 (−0x690 LIBGPU band); rect build `sh zero` x2 / 0x200 / 0x1E0 instruction-identical | head+rect words |
| service: service chain re-arm | calls 28-30, a2=2, a1 = re-read 0x7530 | 0x8002A820 / 0x8002A710 (callback twin 0x8002AAA0) / 0x8002AD90 on 0x8016AFCC (JP D_8016AEA8 +0x124), delay `li a2, 2`, a1 = *(0x800AC2E0) re-read | call+delay words |
| game loop | call 32 func_80042C6C | **jal 0x800428D4** (−0x398) | head diff vs JP func_80042C6C: same prologue, same `jal` mode-machine twin (0x80043D70 vs 0x80044108), same −1 mode-word store (EU D_800AC72C = JP D_800ABEDC +0x850), same dispatch vector base (**EU D_8008B734 = JP D_8008AF1C +0x818**) |
| teardown SDK tail | calls 38-45 | StopCallback 0x8004A14C, ResetGraph(3) 0x8004AEC4 (−0x690), PadStop 0x80026D48, SpuQuit 0x80064174 (+0x990), SsEnd 0x8006B3C0 (+0xBA8), SsQuit 0x8006B464 (+0xBA8), _96_remove 0x8004AE94 (−0x690), _96_init 0x8004ADD4 (−0x680) | yaml/row names + jal targets |
| reboot | call 46 LoadExec("cdrom:\\MAINMENU.EXE;1", 0x801FFF00, 0) | jal 0x8004ADE4 (yaml `LoadExec`), a0 = 0x80020094 "cdrom:\\MAINMENU.EXE;1" (EU string row read), a1 = lui 0x801F/ori 0xFF00, a2 = zero in the delay | the module-swap reboot is two-image |

The teardown's game-side trio also twins: EU 0x80022BCC / 0x800265C0 /
0x8002A7C8 = JP func_80022B6C (+0x60 row) / func_800265E4 (−0x24) /
func_8002A7D8 (−0x10), and `func_8002F7B0` = the func_8002FB20 twin is
called with a0=2 at boot and a0=0 in teardown exactly as JP does;
`0x80024798` (the func_80024738 twin, +0x60) is called once at boot and
once in teardown in BOTH regions.

## The six extra boot calls — and the one that matters most

EU boot = 26 call sites vs JP's 20; the +6, in EU order:

1. **`SetVideoMode(1)` — EU-only (the PAL fingerprint).** jal 0x800224FC
   → **0x8004A030 = `SetVideoMode`** (EU yaml: `[0x2A830, c,
   SetVideoMode]`, 0x18 bytes; the function 0x28 before EU's
   ResetCallback 0x8004A058, whose identity is pinned by its row
   glabel and the VSyncCallback −0x5C0 LIBETC band), delay `li a0, 1`
   = PAL. JP main makes **no SetVideoMode call** — the JP build ships
   NTSC by default, the EU build sets PAL 1 statically. This is the
   regions' only call-count divergence in the SDK bring-up tier and
   the first *source-level* region divergence the walk has localized
   to a single instruction pair.
2. **an extra `func_8002DEDC`-twin call** (EU 0x8002DCAC, −0x230 band;
   body-verified = JP func_8002DEDC: a0 = an index into a stride-0x34
   record array, a1 = the value). JP calls it once with (0, −1); EU
   calls it twice — (0, **0xBD**) then (**0xBD**, −1) — the same two
   values, rotated across the pair's two slots.
3. **an extra `func_80024760`-twin call** (EU 0x800247C0, +0x60; the
   twin is the main-adjacent copy of three 0.929 normalized-alignment
   candidates — resolved by caller context, the pass-19 lesson). JP
   calls the twin twice (a0 = *(0x8007179C), *(0x800717A4)); EU three
   times (*(0x80071FDC), *(0x80071FE0), *(0x80071FE4) — the +0x840
   config-pointer band), and EU moves the first call EARLIER (before
   the AD8/B0 pair).
4-6. **the `0x8002FCCC` trio — the first asymmetrically-wired function
   in the lane.** EU main calls **EU func_8002FCCC** (0x78 bytes) three
   times with (a0=0x50, a1=0), (0x51, 1), (0x52, 2): a variant-switch
   TIM loader (offset-directory resolver call, then a `beq s0,1` /
   `slti s0,2` / `beq s0,2` dispatch, data base **D_80144A64** = JP
   D_8014417C **+0x8E8**). Its JP twin **func_8003003C** (0x80 bytes,
   same body shape, D_8014417C) holds **ZERO static references of any
   form in g3_jp** — real-name census, `.word` sweep, raw jal word
   0x0C00C00F, and the census hi/lo scan all empty. Pass 19's
   machine-total dead-twin reading (scheduler + driver 2, dead in BOTH
   images) gets its first one-sided counter-example: a function dead in
   JP's entire static image that EU's main wires three times. The same
   VA ≠ same entity trap re-confirmed: JP's own func_8002FCCC (0x38
   bytes, a probe caller) is a different entity that merely shares the
   address.

The boot middle also RESHUFFLES order (EU: DECC-twin first, then the
24760-twin, then the AD8/B0 pair; JP: 24760 → AD8 → B0 → DECC →
DEDC) — same functions, different sequence, consistent with a
different compiler scheduling pass over the same source tier.

## The two pass-20 errata the walk forces

1. **Call 16's target is NOT psyq GsSetOrign.** JP call 16 = jal
   0x8002A2C4 with (0x5A, 0x5A); EU's twin call = jal 0x8002A2B4 with
   (0x5A, 0x5A). Both targets are **game-side two-halfword setters**:
   JP func_8002A2C4 stores a0 → D_800ABB54, a1 → D_800ABB5C; EU
   func_8002A2B4 stores a0 → **D_800AC398**, a1 → **D_800AC3A0** (the
   +0x844 twins). The real psyq GsSetOrign — the same 6-insn
   `sh a0/sh a1/return` body shape, which is what pass 20's reading
   tripped on — is 0x80027A60 (JP, → D_800ABAEC/ABAF4) / 0x80027A5C
   (EU, → D_800AC330/AC338) and is not called from main in either
   region. The 0x5A/0x5A values stand; the "drawing origin via
   GsSetOrign" attribution falls (what the pair feeds downstream is
   the open follow-up).
2. **The 0x4D/0x4E "arguments" of calls 10/11 are dead caller
   fillers.** func_80024AD8 and func_800250B0 (JP) and their EU twins
   func_80024B38/func_8002508C never read their incoming a0 — both
   bodies overwrite a0 (`addu a0, v0, zero` / `lw a0, 0(s0)` /
   `lui a0`) before any read, full-body verified in both regions. JP's
   caller leaves li a0, 0x4D / li a0, 0x4E in the delay slots; EU's
   caller leaves a0 = 0 / a0 = 1. The values are scheduling
   materializations, not semantic arguments — pass 20's map should
   read the pair as argument-less.

## The PadStop placement fact

EU main's PadStop sites (probe-fail path + teardown) target
**0x80026D48**, a 7-insn wrapper (`addiu sp, −0x18; sw ra; jal
func_80071F74; return`) body-identical to JP's sdk-region wrapper
**func_8004B074** (`jal func_80071704`; callee shift +0x870). Same
function, different link placement — EU's copy sits game-side right
before the binding layer twin (EU func_80026D68 = JP func_80026D6C,
pass 19's −4 anchor), JP's copy sits in the sdk region. A naive
band-shift prediction would have looked for EU's PadStop at
0x8004AAB4; it is not there.

## The data bands main measures (JP → EU)

| band | members read this pass |
|---|---|
| +0x844 | gp 0x800AB26C → 0x800ABAB0; D_800ABB54/5C → D_800AC398/A0; *(0x800BBAA4)=1 → *(0x800AC2E8)=1; *(0x800BBA9C)=0x7530 → *(0x800AC2E0) |
| +0x840 | config pointers 0x8007179C/0x800717A4/0x800717C4/0x80072FD4 → 0x80071FDC/0x80071FE0/0x80072004/0x80073814 |
| −0xF7B0 | 0x800BC3C4 (\|=0x20 word) → 0x800ACC14; 0x800BC364 (=4) → 0x800ACBB4; 0x800BC4F4 (halfword 0) → 0x800ACD44 |
| +0x850 | 0x800DD1E4/DD3E4/DCFE4 (byte-zero trio) → 0x800DDA34/DDC34/DD834; D_800ABEDC (dispatcher −1 store) → D_800AC72C |
| +0x8E8 | D_8014417C (JP TIM-loader data) → D_80144A64 |
| +0x124 | D_8016AEA8 (service base) → 0x8016AFCC |
| ±per-library | LIBETC −0x5C0 (ResetCallback 0x8004A618 → 0x8004A058; VSyncCallback); LIBGPU −0x690 (ClearImage/DrawSync/SetDispMask/ResetGraph/_96_init/_96_remove ±0x10); LIBSPU +0x990; LIBMIDI +0xBA8; LIBC printf −0x398 |

The +0x840 vs +0x844 split (config pointers vs the below-image pair)
and the three fixed-store sub-bands confirm pass 19's "the EU record
family does not shift as one block" at main's own data surface.

## Evidence table (verified vs inferred)

| Claim | Level | Backing |
|---|---|---|
| EU main = 0x800224D8..0x800227E8, entered terminally by EU crt0 | verified | jal word 0x0C008936 at 0x80047BF8 + body/epilogue read |
| EU gp = 0x800ABAB0 | verified | continuation lui/addiu pair |
| five-phase structure + all anchor twins | verified | per-site reads (table above) |
| LoadExec tail two-image | verified | string row 0x80020094 + jal 0x8004ADE4 + a1/a2 words |
| SetVideoMode(1) is EU-only | verified | EU yaml name + jal site; JP main's words carry no such call |
| call 16 = the game-side setter, not GsSetOrign | verified | both targets' 6-insn bodies + psyq GsSetOrign's own addresses |
| calls 10/11 args dead in both regions | verified | full-body a0 consumption reads (both regions) |
| func_8003003C machine-total unreferenced in g3_jp | verified (machine-total) | census tool + jal-raw 0x0C00C00F + .word + hi/lo scan |
| EU 0x8002FCCC trio wiring (0x50/0x51/0x52 × 0/1/2) | verified | three raw words 0x0C00BF33 in EU main + body switch read |
| the −0xF7B0 fixed-store band | verified | six store/read sites |
| what D_800ABB54/5C pair feeds downstream | open | not chased this pass |
| whether EU's extra boot calls are PAL-conditional source or a scheduling artifact of a region build flag | open | SetVideoMode(1) is deliberate; the DEDC/24760/FCCC extras read as real source diffs in the boot tier |

## What this closes and what it opens

Closed: pass 20's open (c) — main's schedule is two-image; the
pass-19 jal-twin bands now have main's own data-band map attached.

Open: (a) the EU corroboration of passes 21+22 (the exit machines and
the six guard words' EU twins) — the natural pass 26; (b) the EU
corroboration of passes 23+24 (the gameinfo family's EU addresses —
does EU carry the gameinfo.c strings?); (c) what D_800ABB54/5C (the
0x5A/0x5A pair) feeds downstream; (d) the stride-12 work base
(unchanged); (e) when disc links return, runbook Phase A/B; the
fresh-set request rides every report.
