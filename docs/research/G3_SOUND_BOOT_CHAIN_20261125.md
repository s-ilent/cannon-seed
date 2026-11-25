# G3 R1 pass 16 — the sound boot chain: the tone-table writers (the VAB-open chain decoded)

**R1 pass 16 — 2026-11-25 (window cron-20261125-0609).** Bounded
**JP-first read-only static decode** continuing
[G3_SCRIPT_NOTE_ON_20261125.md](G3_SCRIPT_NOTE_ON_20261125.md): the
pass-15 note left "find the writer of the runtime tone tables" as the
open next read. This pass decodes the sound boot chain end to end:
who fills `D_800CFF88` (the per-program note/fine bytes), who fills
`D_800D0744` (the voice-handle cache), and what writes the vab-id
word at `0x80016600`. Source-only: no retail SHA-1 comparison, no
runtime capture, no C conversion, **no rename** (the two game-owned
loaders keep their func_ names; the psyq rows the init calls are
already adopted sdk-symbol names, not touched), no YAML or oracle
change. Zero prior-pass corrections.

## The three runtime words — single writers, machine-checked

A strict reference census (real `%hi/%lo` symbol and `(0xADDR >> 16)`
materialization forms only; byte-column coincidences excluded) over
all eight targets gives:

| word | writer | form | readers |
| --- | --- | --- | --- |
| `0x80016600` (vab id) | the full init, **one store** `sw $v0, 0x0($s1)` at 0x80029D38 | base register materialized once in the init prologue | executor func_80029FC0 (`lw` in the note-on path), keyoff wrapper func_8002A180 (`lw`), re-attach func_80029E2C (`lw` ×2) |
| `0x80016604` (resident VAB header, 0x8620 bytes) | the full init's inlined copy (0x80029C7C unaligned / 0x80029CD8 aligned loop pair) | fixed-size struct copy, alignment-selected | SsVabOpenHead at open; SsVabFakeHead at re-attach |
| `D_800CFF84..0x800D0744` (tone array, 62 × 0x20) | **psyq's SsUtGetVagAtr**, through the pointer argument | library-side stores, no in-image materialization exists | the executor (`D_800CFF88 + prog*0x20`, bytes +0/+1 of its read = record +4/+5) |
| `D_800D0744` (voice handles) | **the executor only** (`sh $s0` at func_8002A140, the post-keyon path) | `lui/addiu %hi/%lo(D_800D0744)` once per use | the keyoff wrapper func_8002A180 (`lh`); **no other reference campaign-wide** |

The `D_800D0744` census supersedes this window's first loose sweep:
grep hits in g3_jp VSync/trapIntrVSync/v_wait, func_800652DC,
func_800659F0, g3org_jp CD_getsector and g3_eu func_80026B40 were
**byte-column false positives** (e.g. `D074428C` = the encoding of
`lw $v0, 0x74D0($v0)` from D_800974D0). The strict census leaves
exactly 2 real references in g3_jp (the executor store + the keyoff
read) and 4 in g3_eu (the byte-twin group). The voice cache is
written only at note-on and read only at keyoff.

## The full sound init — the boot path (0x80029C24 body)

The function whose chunk glabel is func_80029C1C (real entry
0x80029C24, after the preceding function's `jr $ra` tail) is the
complete sound boot. Verified instruction-level:

1. `SsInit()` (func_8006A1A8; placement SSINIT, sig-db agree).
2. `SsSetTickMode(1)` (func_8006A3C8).
3. `buf = fload3("\SE.VH;1")` — func_8002A530: a retry wrapper
   (0xFFFFFFF attempts, then `printf("FLOAD:fault!\n")`) around
   func_8002A598: `CdSearchFile(&CdlFILE, "\SE.VH;1")` → failure
   prints `"Cannot find file(%s) in fload3()\n,filename"` →
   `malloc(size rounded up to 0x800)` → `CdRead2` → returns the
   buffer. **D_80076D6C = the filename string `"\SE.VH;1"`, mapped
   data immediately after the multiplier table D_80076CEC.**
4. Inlined copy: `memcpy(0x80016604, buf, 0x8620)` — a **fixed
   0x8620-byte copy** (0x20 VabHdr + 0x800 ProgAtr[128] +
   63 × 0x200 VagAtr = one complete psyq 3.3 VAB header for 63
   programs) with the compiler's alignment-selected loop pair
   (`andi $v0, $a3, 0x3` picks unaligned lwl/lwr→swl/swr vs aligned
   lw/sw).
5. `free(buf)`.
6. `vabId = SsVabOpenHead(0x80016604, -1)` — the copied header is
   registered with the fresh libsnd.
7. `ret = snd_fload3_TransBody("\SE.VB;1", (short)vabId)` —
   func_8002A2DC: the same retry wrapper shape (D_8002084C
   `"FLOAD:fault!\n"`) around func_8002A354: `CdSearchFile` →
   `"Cannot find file(%s) in snd_fload3_TransBody()\n,filename"`
   (D_8002085C) → `malloc(0x40000)` → `"No enough memory in
   snd_fload3_TransBody()\n"` (D_80020898) on failure → read →
   `SsVabTransBodyPartly` + `SsVabTransCompleted` → free. The VAB
   body lands in SPU.
8. **`sw ret → 0x80016600`** (the delay-slot store before
   `SsStart`) — the vab-id word's only writer. `SsStart(ret)`
   (func_8006A7D8; placement SSINIT, sig-db agree).
9. `SsSetMVol(0x7F, 0x7F)`.
10. `SsUtGetVabHdr(vabId, D_800CFF64)` — the local VabHdr copy
    (0x20 bytes, exactly 0x800CFF64..0x800CFF84, ending at the tone
    array's base).
11. **The tone-array fill loop** (func_80029D64): for
    `prog = 0..0x3D` (62 programs — `slti` bound 0x3E),
    `SsUtGetVagAtr(vabId, prog, 0, D_800CFF84 + prog*0x20)` — each
    call makes the library write one 32-byte VagAtr record. The
    array occupies **0x800CFF84..0x800D0744, ending exactly at the
    voice-handle cache** (62 × 0x20 = 0x7C0).
12. Global volume defaults: `D_800ABB54 = D_800ABB5C = 0x5A` (the
    pass-15 global L/R volume scalers start at 0x5A, not unity);
    `lh(D_800ABF9C)` picks `0x65` vs `0x7F` for the serial volumes
    D_800ABB64/D_800ABB6C; `SsSetSerialAttr(0, 0, 1)`,
    `SsSetSerialVol(...)` (a0 = 0), `SsSetStereo()`.
13. `sw SsUtGetVBaddrInSB(vabId) → 0x8001EC24` — the SPU body
    address stored via `ori $v1, $s1, 0x8000; sw $v0, 0x624($v1)`:
    0x80016600 + 0x8000 + 0x624 = **0x8001EC24 = exactly one word
    past the 0x8620-byte resident header** (0x80016604 + 0x8620).

## The tone identity — the executor's bytes are VagAtr.center/.shift

psyq 3.3 `LIBSND.H`'s `VagAtr` (32 bytes, quoted from the vendored
header): `prior(0x00), mode(0x01), vol(0x02), pan(0x03),
center(0x04), shift(0x05), min(0x06), max(0x07), vibW/vibT/porW/
porT/pbmin/pbmax/reserved1/reserved2 (0x08..0x0F), adsr1(0x10),
adsr2(0x12), prog(0x14), vag(0x16), reserved[4](0x18)`.

The executor reads `lbu(D_800CFF88 + prog*0x20)` and
`lbu(D_800CFF89 + prog*0x20)` = record base 0x800CFF84 + prog*0x20 +
4 and +5 = **VagAtr[prog].center and VagAtr[prog].shift**. So the
pass-15 "noteByte/fineByte" are literally the VAB's per-program
center note and center fine tune, and the played note param is
`center − 0x18` with `fine = shift` (the −0x18 rides the
`SsUtKeyOn` call's delay slot). How psyq's SsUtKeyOn combines that
note param with the tone's center/min/max internally is libsnd
internals — recorded as the standing semantics note, not invented.

Geometry cross-checks: the fill covers programs 0..0x3D (62 of the
header's 63). Every program reachable through the command table
(pass 15's 0x00..0x39 set) plus all six direct-fire programs
(0x08, 0x0A, 0x0B, 0x35, 0x36, 0x37) is ≤ 0x3D — **every reachable
note-on reads a filled record**. The unity-band multiplier slots
≥ 0x3E in pass 15's table have no call sites, consistent with the
"unreachable" remainder — nothing live reads past the array.
D_800D07C4 (the next word past the voice cache) belongs to the STR
streaming setup (StSetRing/StSetStream in func_8002A720) — a
separate subsystem, not sound.

## The re-attach path — the module-swap sound boot (func_80029E2C)

The second function in the sound group re-attaches to the EXISTING
resident state without touching the disc:

```
SsInitHot() (func_8006A1C8; SSINIT/S_IH placements, sig-db agree)
SsSetTickMode(1)
SsStart()
SsSetMVol(0x7F, 0x7F)
SsVabFakeHead(0x80016604, lw(0x80016600), lw(D_8001EC24))
    — re-registers the SAME resident header under the SAME vab id
      and the SAME SPU body address (psyq SsVabFakeHead(char*,
      long, long)); a1 = lw(0x80016600), a2 = lw(0x8001EC24)
SsVabFakeBody(lw(0x80016600))
SsUtGetVabHdr(vabId, D_800CFF64) — refresh the local VabHdr copy
== -1 → printf(D_80020808) = "SsUtGetVabHdr err\n"
```

No CD access, no re-open, no re-transfer — and **no VagAtr refill**.

### Who runs which (the caller census, machine-checked)

- **Full init has callers only in the boot-chain modules:**
  slps_00270 boot main func_80021800 → `jal func_8002C110` at
  0x80021838; sces_00269 boot main func_8002180C → `jal func_8002BF38`
  at 0x80021854 (both before GsInitGraph); mainmenu_eu boot
  func_80023A94 → `jal func_80039038` at 0x800241AC.
- **The g3-family modules call ONLY the re-attach:** g3_jp's main
  (entry 0x800224C0, inside the not-yet-split data region
  data_80022878) executes `jal 0x80029E2C` at 0x80022548 (the raw
  word 0x0C00A78B, found by a j/jal encoding sweep over every
  g3_jp data row), then immediately applies the default global
  volume 0x5A/0x5A through func_8002A2C4.
- A j/jal encoding sweep over ALL g3_jp data rows against the full
  sound-family address set (init entry, re-attach, fload3 family,
  SsInit/SsInitHot/SsStart/SsSetTickMode, SsVabOpenHead/FakeHead/
  FakeBody, SsUtGetVabHdr/VagAtr/VBaddrInSB, TransBodyPartly/
  Completed, SsSetMVol) returns exactly ONE hit: that re-attach.
  **The full init and the SsUtGetVagAtr fill loop have no caller in
  g3_jp** — neither in code chunks (no jal/j to any of the six
  init-range chunk labels) nor in data (no encoded jump) — and the
  same holds for the byte-twin groups in g3_eu/g3org_eu/g3org_jp/
  mainmenu_jp.

### The consequence, recorded as the open remainder

g3_jp's crt0 (entry 0x80047EF0) zeroes `.bss` [0x800ABA8C,
0x80171F04) — the tone array 0x800CFF84 and the voice cache
0x800D0744 are inside — while the below-image sound words
(0x80016600/0x80016604/0x8001EC24) sit outside and survive the
module swap. So after a g3-family boot the tone array is zeroed and
the re-attach does not refill it; the executor would read zero
note/fine bytes. The refill path that must exist on retail — an
SsUtGetVagAtr loop or an equivalent copy reached from a site this
sweep does not cover (an un-split region outside data_80022878's
main, or a boot-order subtlety in the mainmenu→g3 hand-off) — is
the recorded open remainder. No mechanism invented.

## The below-image resident layout (the sound struct at 0x80016600)

| address | content | writer |
| --- | --- | --- |
| 0x80016600 | vab id (word) | full init, step 8 |
| 0x80016604..0x8001EC24 | resident copy of the complete \SE.VH;1 header (0x8620 = 0x20 VabHdr + 0x800 ProgAtr + 63×0x200 VagAtr) | full init's inlined copy |
| 0x8001EC24 | SPU body address (word) | full init, step 13 |

The region sits 0x9A00 below the 0x80020000 load base — exactly why
it survives the per-module EXE swap while the above-image libsnd
state does not. The sibling below-image system at 0x80016106
(memset(0x80016106, 0, 0x298) in every module's script reset path)
is the script state, not sound.

## The voice-handle cache — the complete reference web

`D_800D0744` is written by the executor's post-keyon path only
(`sh $s0, D_800D0744 + id*2` in func_8002A140 — the same store the
pass-15 doc recorded) and read by the keyoff wrapper only
(func_8002A180: `lh(D_800D0744 + prog*2)` = the voice handle passed
to `SsUtKeyOff(voice, vabId, prog)` — func_80068FE0 — with the note
byte re-read from the tone array in the delay-slot argument build).
g3_eu carries the byte-twin group (store at 0x80027A14, reads at
0x80026E10/0x80026E98 and the keyoff materialization at 0x80026D00).
Nothing else touches it, in any module, in code or data.

## The EU twins (pass-15 next question (2), closed)

The EU direct-fire census was already region-invariant by the
byte-twin structure (pass 15); this pass adds the sound-subsystem
twins: g3_eu's group (init func_80029C18, re-attach func_80029E1C,
executor func_80029FB0, keyoff func_8002A170) materializes the same
0x80016600/0x80016604 pair with the same shapes; mainmenu_eu,
mainmenu_jp, g3org_eu/jp, sces_00269 and slps_00270 each carry the
same 4-function group at the same addresses (7–8 materializations
each, the extra hits being the script-state memset). The cue map
and the fill chain are region-invariant.

## Evidence table (verified vs inferred)

| Claim | Level | Backing |
| --- | --- | --- |
| vab id writer = one sw in the full init | verified | 0x80029D38; strict materialization census (2 g3_jp readers) |
| Resident header = 0x8620-byte VAB header copy | verified | fixed-size loop pair; 0x20+0x800+63×0x200 = 0x8620 |
| \SE.VH;1 = the header file, \SE.VB;1 = the body | verified | D_80076D6C/D_80078 strings; CdSearchFile arg path in fload3/snd_fload3_TransBody |
| fload3 / snd_fload3_TransBody = the original loader names | verified | D_800208FC / D_8002085C printf strings |
| Tone array filled by SsUtGetVagAtr through the pointer arg | verified | fill loop func_80029D64; no in-image store materialization to 0x800CFF88 exists |
| Executor bytes = VagAtr.center/.shift (+4/+5) | verified | psyq 3.3 LIBSND.H VagAtr layout + the 0x800CFF84 fill base + the 0x800CFF88 read base |
| Fill covers progs 0..0x3D; all reachable progs ≤ 0x3D | verified | slti bound 0x3E × pass-15 call-site cross-reference |
| Voice cache written only at note-on, read only at keyoff | verified | strict census: 2 g3_jp + 4 g3_eu real refs |
| Boot-chain callers of the full init | verified | slps 0x80021838, sces 0x80021854, mainmenu_eu 0x800241AC |
| g3-family re-attach-only boot | verified | main 0x80022548 jal word 0x0C00A78B; encoding sweep over all data rows |
| crt0 zeroes the tone array on every module load | verified | entry 0x80047EF0 loop bounds 0x800ABA8C..0x80171F04 (exe.json pc0) |
| The g3 tone-array refill site | **open** | no refill site in split code or data-encoded jumps; the retail path remains to be located |

## Next R1 question

(1) Locate the g3-family tone-array refill: sweep the remaining
un-split code regions of g3_jp (the data_80022878 main body beyond
0x800225E4 and its callees into the giant chunk) for a SsUtGetVagAtr
call chain or an inline copy from the resident header's VagAtr area
(0x80016E24+) into 0x800CFF84 — this closes the "what plays when"
score's last static gap. (2) The music-lane state the giant chunk
writes (D_800CFF00/CFF04/CFF14/CFF24, D_80165242 strides, the
func_80029840 lane dispatcher and its four mode handlers
func_80029200/func_800292E8/func_800293C4/func_800293FC) — the
separate mixer/sequencer lane's own boot and tick. (3) When disc
links return: Phase A/B per the runbook (the ladder stays closed);
the fresh-set request rides every report.
