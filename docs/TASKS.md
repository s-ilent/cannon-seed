# TASKS

Queued work for this repository, newest on top, with a record of what was done
below. Queued tasks are written for whoever picks them up next — usually the
sandbox agent, which is where the build toolchain lives.

## Queued

### State checkpoint (2026-10-15, `d3434c3`): gates green, sdk adoption closed

First independent full-gate audit since the anchor landing (`8a66466`) and the
adoption lands (`7cce6f3`/`0ad2d31`/`f276290`):

* `make verify` GREEN 8/8; ratchets 365/0 == baseline; matched 174, progress
  TOTAL 14590 (census grew 13659→14590 with the anchor rows — filesystem
  heuristic, the oracle is unaffected); screens cover 2651 asm/c subsegs (was
  1813 pre-landing). 1 SUSPECT total: Witness B's `func_80061780`
  (mainmenu_eu, 96 B, opfrac 0.417 — the documented, deferred row; no new
  suspect). 27 DATA flags, all score-40 padding-class: slps/sces 24 B = the
  adjudicated SetDQB tail; the rest are 96–244 B member-tail zero12/zero13
  paddings. One spot-checked flag (mainmenu_jp `func_8007EFDC`, 244 B) is real
  INTR-handler code (`mfc0 $13`, `sw $ra,0x7C($k0)`) with a nop tail — a
  heuristic false-positive on code-with-padding, left untouched (INTR lane).
* sdk adoption residue = ZERO: a fresh `tools/sdk_curated.py` run over the
  psyq 3.3 archives reproduces `config/symbols.curated.txt` byte-identical —
  1607 adoptions, skips all justified (name-dup "both copies real; one label
  each" for the GsSetOrign/SpuVmDamperOn/memclr/Snd_play second copies,
  addr-curated for the hand rows), guard block silent. The adoption queue
  from the anchor landing is CLOSED; nothing left to adopt until a new member
  report lands.
* Housekeeping: the "Teach `sdk_members.py` the 0xF000 archives" and "Retire
  the MODE2-framing rows" headers below are DONE (cc7ae6f, 87f84d1); they stay
  listed as history.

### Teach `tools/sdk_members.py` the `0xF000`-section archives (LIBC/LIBAPI/…)

TOOL + REPORT DONE 2026-10-15 (see Log): `parse_archive()` now canonicalizes
section ids by name at section-def time (`0xF000` vintage: LIBAPI, LIBC,
LIBCARD, LIBCOMB, LIBSN — plus mixed-in members of LIBGTE/LIBC2), and the
report regenerates at `--min-fixed 8` so the 16-byte zero-relocation BIOS
thunks (exactly 9 non-zero bytes each) census. 425→748 members, 1068→1975
placements, 144→145 anchored (thunks are `unique`, not anchored: zero
relocations to reconstruct), sdk_anchors.txt 856→1703 rows. mainmenu_eu is
landed and verified GREEN; the remaining seven targets' scan/extract/verify
landing is the open part of this item.

Original finding, for the record:

`parse_archive()` keys every member's `.text` on section id 2. Five
archives' members — LIBAPI, LIBC, LIBCARD, LIBCOMB, LIBSN — number `.text`
as `0xF000` instead (all 3.3 archives share the same outer `LIB\x01`
wrapper; the section-id scheme inside the member records differs by lib
vintage), so the parser returns 0 members for those five and
`config/sdk_members.txt` has never census'd their placements
(the 2026-10-12 3.3 re-pin counts its 968 placements from the 11 new-format
libs only). Much of LIBC/LIBAPI is 16-byte zero-relocation BIOS thunks —
see the Witness A thunk identification addendum, which grew out of exactly
such a member set — and those place trivially by byte match; the full
implementations place like any other member once the section id is mapped.

Fix: accept both `.text` ids in `parse_archive()`/`Member.text()` (and in
the symbol filters), regenerate `config/sdk_members.txt` + the anchored
census, and re-run the scan with `--sdk-anchors`: any NEW anchored
placements become walk-stop anchors, so land the yaml/symbols drift with
the usual re-scan discipline (verify 8/8 must stay GREEN). Small,
independent, self-checking.

### Retire the `asm` rows that are MODE2 sector framing

The framed-file layout (see the de-frame item below) puts 304 bytes of MODE2
framing — 280 bytes of EDC/ECC plus the next sector's 24-byte
sync/address/mode/subheader — between every pair of 2048-byte data areas. 341
carve rows are >90% that framing: 241 typed `data` (correct) and **100 typed
`asm`, 7832 bytes, which are not code at all**.

This settles the "runtime-opaque block" gate without an emulator. The two
blocks the 58Fxx library pass pinned — mainmenu_jp `data_80058D90` (308 B) and
`data_800596C4` (300 B) — are that framing, not runtime-patched code, and the
"real bne targets inside them" (carve `0x80058DAC`, `0x800596CC`) land in the
ECC, so they are misdecodes. The "clean code → high-entropy block → clean code"
shape is data area → ECC → next data area, and the shared marker is the sector
header. Nothing is patched or decrypted in place; the branches are dead.

Fix: re-type the 100 `asm` rows to `data` (the carve-pin path), which also
retires the bogus `func_XXXXXXXX` names they carry. The 241 `data` rows are
already right. Regenerate the list with `python3 tools/deframe.py
--framing-rows` (every row per target, then the type totals) — it recomputes
from the carve, so use it rather than a snapshot.

### Split the de-framed payload, not the framed on-disc file

`baselines/*.bin` are raw MODE2/2352 sector images, not plain EXEs: the MODE2
sync `00 FF FF FF FF FF FF FF FF FF FF 00`, an incrementing BCD address, mode
`02` and subheader every 2352 bytes, first at `0x918`, ~296 sectors per file.
Their SHA-1s match `config/sha1/**`, so the disc really does hold the framed
file — this is not an extraction bug. `docs/GRID.md` found the `0x930` grid but
did not draw the consequence.

**UPDATE 2026-10-15 (Log, "the boot load model closes"): the premise above is
REFUTED** — it IS an extraction artifact. `Iso.read()` reads `size` bytes
contiguously from `lba*2352+24`, weaving in every sector's 280-byte EDC/ECC +
24-byte sync header and truncating the tail user data (~12.9-13% of every
payload). ECC regenerates 100% (genuine woven sectors); `t_size ==
len(baseline)-0x800` for all 8; the boots' .sdata window is provisioned by the
load and its bytes are disc-only. The queued "decide what make verify
compares" sharpens to corrupt-extraction-vs-true-file.

The game de-frames at load. Verified against the running game through the GDB
stub (`tools/gdb_stub_proxy.py`), 2026-10-13:

* 4 KiB read at `0x80020000` equals the de-framed payload byte for byte, and
  does not match the framed file;
* `Too few TOC` runs at `0x80020000`; the carve puts it at `0x80020130`;
* `func_800253F8`'s bytes run at `0x80024818`; the carve puts them at
  `0x800253F8`.

So `splat` maps the framed file linearly and every VRAM past the file's start
is offset from the real runtime address by an amount that grows with position
(`0x130` near the start, `0xBE0` further in). Every `func_XXXXXXXX` name is a
file offset, not a runtime address.

Carve impact: 481 of 1841 (26%) of `asm`/`c` subsegments overlap framing bytes
— 197 start inside a framing region, 59 have a full 304-byte chunk strictly
inside, so their code is interrupted and cannot match as clean C. None of the 12
matched `c` regions is affected, so existing matches stand.

Fix: de-frame each baseline into the real payload image, point the splat config
at that, and re-derive the symbol addresses from it. Decide first what
`make verify` compares: the on-disc framed file (today's oracle, what the disc
holds) or the de-framed payload that actually executes — if the former stays the
target, the build must re-frame.

Witness A — the `mainmenu_eu` twin islands (2026-10-14, the func_80066388
head hunt, first fully-worked example of the pathology):

* The drift is not `0xBE0 further in` and done — it grows ~304 B per sector
  and reaches **0x9210** at mainmenu_eu carve `0x8006626C` (= runtime
  `0x8005D05C`, `tools/deframe.py --map-framed`). Every address-based
  conclusion deeper than the first sector inherits this skew.
* The carve row `data_80065F50` (0x490) is, in order: 4 BIOS-call thunks
  (`addiu $t2,0xa0/0xb0; jr $t2; addiu $t1,N` — the $t1/$t2 call
  convention, address-independent shape), island 1 = a real leaf transform
  helper (runtime `0x8005CEBC..0x8005D054`, 0x198: `move $t7,$a0` head,
  bgez/negu abs-handling, a `lui 0x800b/lw 0x470($t9)` sign table, six
  `multu/mflo/subu|addu/sra/sh N($a1)` blocks, `jr $ra`), then a framing
  pocket (sync at carve file `0x661F8`, address/mode `00 21 06 02`,
  subheader `00 00 08 00` twice — the bytes the linear disasm decodes as
  `sll $zero,$t0,0`), then island 2 = the X/Y twin of island 1, runtime
  `0x8005D05C..0x8005D1F4`, same 0x198 shape with halfword offsets 0/2/4
  instead of 6/8/0xa.
* Island 1 is framing-SPLIT in the carve: pieces `[0x4679C..0x468E0)` +
  `[0x46A10..0x46A64)` with the pocket between — no carve row can hold it
  as one function. Island 2 happens to be carve-contiguous
  (`[0x46A6C..0x46C04)`); today's `func_800663E0` (0x24) is its last 0x24.
  Runtime-continuous across the pocket: data area 1 ends at runtime
  0x8005D000 and data area 2 resumes at exactly 0x8005D000.
* Callers prove the runtime encoding: exactly one real `jal` per twin —
  carve `0x80045398` encodes `jal 0x8005CEBC`, carve `0x800453A8` encodes
  `jal 0x8005D05C`, adjacent sites calling the two twins back to back.
  Decoded as carve addresses (what the scanner does with every anchor),
  those encodings point ~0x9210 bytes BELOW the twins' true carve
  positions. The ~30 "jal pairs" into the pocket (`0x800660D0/0x800660E4`,
  sources in `func_80070070`/`data_80070650`/...) are the same phenomenon
  seen from the other side: runtime-addressed words whose carve-space
  decode lands inside framing — which is why v3d rejects every walk that
  crosses the pocket and why the whole zone fell to `data`.
* Why verify stays green anyway: the pipeline is byte-preserving
  end-to-end. The split emits retail bytes verbatim, cross-row references
  stay literal (nothing re-encodes a `jal` field), mkpsxexe reproduces the
  2048-byte header, and the carve's framing bytes live inside `data` rows
  and round-trip. The build output is byte-identical to the framed retail
  including its 297 syncs — no re-framing pass exists or is needed today.
  The address skew costs nothing at link time; it only poisons address
  DERIVATION (scanner anchors, pointer decoding, "who references X").
* Consequence for the fix: this is why no carve-side re-boundary was
  landed for `func_80066388` — the true head is carve `0x8006626C`, but a
  hand pin there would (a) claim a carve-space identity the de-frame
  transition will re-derive, and (b) leave island 1 (the framing-split
  twin) unfixable anyway. Re-derive from the de-framed payload; the head
  hunt is closed, not abandoned.
* Cross-target addendum (same window): the family is a TRIO, not a pair.
  Every game-module target has exactly 3 hits of the twin-head byte
  pattern (`addu $t7,$a0,$zr; addu $v0,$a1,$zr`), zero in the boot EXEs;
  the three 0x198 siblings sit runtime-contiguous at a 0x1A0 stride
  (0x198 + 8 B pad — plausibly the X/Y/Z axis variants of one helper).
  Where the framing pocket falls differs per region exactly as the sector
  grid predicts: mainmenu_eu pockets 1↔2 and is contiguous 2↔3;
  mainmenu_jp is contiguous 1↔2 (carve 0x800666EC→0x8006688C, 0x1A0
  apart) and pockets 2↔3; g3/g3org show the same 3-hit shape at their own
  depths. Same runtime code, different sector alignment per region — the
  trio is the cleanest demonstration that the carve view's row structure
  is a per-region artifact of where 304-byte gaps happen to land.
* Thunk identification addendum (2026-10-14/15 window): the 4 thunks at
  `data_80065F50`'s head are not hand-rolled stubs — they are Psy-Q 3.3
  **LIBC members linked verbatim**, 16 bytes each, byte-identical to the
  archive bodies (psyq's own scheduling: `addiu $t2,TAB; jr $t2;` with
  the `addiu $t1,N` ordinal in the delay slot, then `nop`): A0#0x18
  `strncmp`, A0#0x1A `strncpy`, A0#0x34 `free`, B0#0x38 `exit` —
  splat-map addresses `0x80065F5C/6C/7C/8C`, row head is 3 nops of
  padding before the block. Triple-sourced: psyq 3.3 `LIBC.LIB` member
  bodies parsed from the archive, lab313ru sig-db 330 (`LIBC.LIB.json`
  C24/C26/C52/A56.OBJ — same sigs byte for byte), and the documented
  BIOS A0/B0 tables. The same contiguous 4-thunk block exists in every
  target at its own depth (splat-map addresses of the `strncmp` head,
  block stride 0x10): mainmenu_jp `0x800666AC`, g3_jp `0x8004EFBC`,
  g3_eu `0x8004E9D4`, g3org_jp `0x8004BE68`, g3org_eu `0x8004B708`; the
  two boot EXEs carry a **fifth** LIBC thunk, `rand` (A0#0x2F), between
  `free` and `exit` — slps_00270 `0x80030E20..0x80030E60`, sces_00269
  `0x80030894..0x800308D4`. The members are zero-relocation pure
  immediates, so the identification is address-independent and survives
  the de-frame transition unchanged.

* Witness B — the j-target rescue victim `func_80061780` (mainmenu_eu,
  2026-10-15, found reviewing the sdk-landing screens): the 8a66466
  re-partitioning left a 0x60 row at carve `0x80061780` whose 24/24 words
  decode as nothing (spimdisasm emits them as `.word`, several marked
  invalid instructions; no prologue, no zero runs, no ASCII — a
  high-entropy blob). Pre-landing the same bytes were interior `.word`
  data inside the big walk row `func_8006107C` (0x764). The scanner heads
  there on every re-scan because FOUR real `jal`s decode into it
  (`0x8005B060`, `0x8005B2CC`, `0x8005B8B0`, `0x8005B968`, words
  `0x0C185E0X`) — the v4 j-target rescue law "a tail call only ever
  targets code" doing exactly what it is told, on drifted fields. This is
  Witness A's law seen from the rescue side: the fields are
  runtime-encoded; decoded as carve addresses they land below the true
  target, here at a depth where the skew has grown past Witness A's
  0x9210 (consistent with the ~304 B/sector growth). Consequence, same
  call as Witness A: no carve-side fix — a data pin would fight the
  rescue on every scan and claim a carve identity the de-frame
  transition will re-derive; the row is verify-neutral (bytes
  round-trip); it is the sole SUSPECT in the screens (opfrac 0.42).
  Deferred to the de-frame transition with the rest of the family.

* Thunk runtime + caller census addendum (2026-10-15, de-framed payload;
  independent scan that converged on the same identification): runtime
  addresses straight from the de-framed payload, no drift arithmetic —
  mainmenu_eu's 4-thunk block runs 0x8005CE7C..0x8005CEBC, immediately
  followed by island 1 at 0x8005CEBC, so thunks + transform helper are
  ONE runtime library region the framing splits (the block's runtime
  addresses cannot be recovered from the carve view: splat-map and
  runtime differ by the ~0x9880 local skew here). Payload offsets of the
  block head: game modules 0x3CE7C mainmenu_eu / 0x3D49C mainmenu_jp /
  0x28E5C g3_jp / 0x28874 g3_eu / 0x262F8 g3org_jp / 0x25CC8 g3org_eu
  (4-thunk variant), boots 0xEA80 slps / 0xE624 sces (5-thunk variant
  confirmed: strncmp→strncpy→free→rand→exit walked byte for byte in the
  de-framed payloads). Real `jal` callers exist in every module —
  mainmenu: strncmp 5 / strncpy 9 / free 4 / exit 5 (exit from runtime
  0x80023C28, 0x80024F34, ...); the g3/g3org family: 5/3/5/3, identical
  counts across all four; boots: 5/3/5 and rand 7 / exit 4, identical in
  both — so these are live library thunks, not dead bytes, and they join
  the twins as runtime-real members unrepresentable in the carve view.
  No carve-side pin (same rule as the twins): the de-frame transition
  re-derives them.

* Boot rand caller site census addendum (2026-10-15, de-framed payload;
  closes the census's one optional item): the boots' 7 `rand` callers are
  all in ONE runtime routine — a 0x1C8-byte loop (head runtime 0x80023474
  slps / 0x8002349C sces, the +0x28 shift the two boots carry at this
  depth; prologue `addiu $sp,-0x28` + ra/s3/s2/s1/s0 saves, `$s0` = output
  pointer param) that fills a 10-entry, 0x10-stride table with
  `rand()`-derived halfwords: 7 `rand` calls per entry (`s3` counts to 0xA
  — 70 `rand()` calls per fill), signed-%512/%511/%3-style mods via the
  gcc `div`/`mfhi`+`break 6/7` idiom, halfword stores at +0/+2/+4/+0xa/
  +0xc, back-edge `bnez` to the first site. Cross-boot: the routine is
  byte-identical over 420 bytes head-to-tail — the ONLY 7 differing words
  are the `jal` fields themselves (0x0C00BAAC vs 0x0C00B995, the two
  boots' rand thunks), so it is the same source in both boots with only
  the call encodings differing. Exactly one parent `jal` per boot (slps
  runtime 0x80022254 / sces 0x8002234C) and the parent also sits in a
  data-labeled region (slps `data_80021810`, sces `data_8002287C`);
  deeper chain not chased. Carve-view contrast (the Witness A trio's
  per-region-artifact law, once more): slps's carve labels the whole
  routine's region `data_8002376C` (data, 0x8002376C..0x80024BFC) — real
  code, data-labeled — while sces's carve labels the same code
  `func_8002392C` (asm, 0x8002392C..0x80024080). The wider boot mirror
  census: most boot thunk callers live in data-labeled rows too (slps:
  strncmp 2/5 + strncpy 3/3 in `data_80028428` — game code, per the
  library census addendum below; the SpuVmDamperOn pin sits just BEFORE
  it at 0x80028414; free 3/5 + exit 1 in `data_8002E578`; exit 2 more in
  `data_80021810`; sces the same shape under its own row split) — the
  boots carry the "12.9% of data is code" pathology with live callers.
  Method: jal-encoding scan of the de-framed payload (runtime = payload +
  0x80020000), mapped back with `tools/deframe.py --map-runtime`; mapping
  validated — every thunk's mapped carve address reproduces the pinned
  member rows exactly (slps 0x80030E20..0x80030E60, sces
  0x80030894..0x800308D4). No carve-side pin (same rule).

* Boot library census addendum (2026-10-15, de-framed payload; the
  follow-up the rand census set up): which Psy-Q members did the boots
  link, and what is the caller-cluster region really made of? Method:
  `tools/sdk_members.py`'s parser + placer over the DE-FRAMED payloads
  (748 members with `.text` from the 3.3 archives; runtime = payload +
  0x80020000 — the de-framed view is the stricter instrument: a member
  split by a 0x130 framing gap can never match in the framed view the
  committed reports slide). slps: 254 placements (36 anchors, 91
  sig-agree); sces: 234 (27 anchors, 78 sig-agree). Roster shape, both
  boots: LIBGS `EMULIB` opens; LIBSND `VM_DON` (0x14, sig-agree) — which
  IS the carve's pinned `SpuVmDamperOn` row (runtime 0x80027244 ↔ carve
  0x80028414 slps / 0x8002728C ↔ 0x8002845C sces, exact via deframe.py;
  the member object is named VM_DON, the exported symbol
  SpuVmDamperOn — one label each, the name-dup note's boot copy); LIBSND
  `VM_DEBUG` sig only; LIBETC kernel block after the thunks (`INTR`
  0x714 ANCHOR+agree, `INTR_DMA`, `INTR_VB`, `PAD`, `VSYNC`, `VMODE` —
  link order differs: slps VMODE sits late at 0x80032650, sces VMODE
  opens the block at 0x8002E674); LIBAPI 0x10 veneer rows; LIBC/LIBC2
  stubs; LIBSN `LIBGCC2`. THE ANSWER: the strncmp/strncpy/free caller
  cluster sits in a **member void** — runtime slps 0x80027258..0x8002C7B0
  (0x5558 B) ↔ carve 0x80028428..0x8002E560, sces 0x800272A0..0x8002C5CC
  ↔ 0x80028470..0x8002E37C — with NO 3.3 member `.text` placement and NO
  sig hit covering any of the nine callers (3+3+3 per boot). The cluster
  is the boot's OWN game code living in data-labeled carve rows: the
  boots' "data is code" pathology is game code, not hidden library
  members (only LIBSND's two stubs and the kernel block are library).
  Both void ends corroborated by the repo's own pinned sdk rows: VM_DON
  opens it, the EMULIB 0x18 rows close it (`func_8002E560` slps /
  `func_8002E37C` sces, the "0x18 sdk" rows). No carve-side action — the
  de-frame transition re-derives; the void is game code for the C lane.

* Member void anatomy census addendum (2026-10-15, de-framed payload; the
  follow-up the library census set up): what IS the void, function by
  function? Method: prologue census over the de-framed payloads (the boot
  convention is `addiu $sp,-N` FIRST, then `sw $ra,N($sp)` — verified on
  the rand census's routine head, `27bdffd8`/`afbf0020`), a `jal` census
  with runtime targets, and each external target classified by deframe
  mapping to its containing carve row plus exact match against the pinned
  member runtimes. THE SHAPE: 63 prologue-bearing function heads in BOTH
  boots (min 8, max 705 words; a lower bound — frameless leaves are
  invisible); 93 internal `jal`s into 37 distinct internal targets in
  BOTH boots; the prologue-site offsets are void-relative equal for sites
  #0–18, then shifted 0x220 for sites #19–56 and 0x22C for sites #57–62 —
  the same 63-function sequence in the same order with the same sizes
  except TWO size deltas (one slps function among the first 19 is 0x220
  larger, one more 0xC larger between sites 56–57), and the internal call
  sites are void-relative equal across the whole pre-shift segment. Byte
  identity does NOT hold (42% word equality over the common void range;
  first divergence at void+0x18, an `addiu` %low literal): unlike the
  byte-identical rand routine, the void's functions carry absolute
  address literals and their external call targets sit at different
  runtimes per boot (strcat slps `0x8002DC00` vs sces `0x8002D9F4`) — the
  linked SDK layout differs (254 vs 234 placements). THE CALL ROSTER
  (what the boot's own game code does): the libc string/printf set
  (strcat x14 slps / x18 sces, strcpy x8, printf x5, strlen, strncat,
  bzero), the whole LIBCARD file API (open x6, close x9, read/write/lseek
  x2 each, firstfile, nextfile, delete, format, OpenEvent x8, EnableEvent
  x8, TestEvent x16), card control (InitCARD, StartCARD, _bu_init,
  _new_card, _card_load/_info/_auto/_clear/_read), the streaming API
  (StSetStream, StSetRing, StGetNext, StFreeRing), CdRead2, and the SN
  audio family (SsSetStereo, SsSetMVol, SsSetSerialVol x5,
  SsSetSerialAttr, SsVabOpenHead, SsVabFakeHead/Body, SsUtGetVabHdr/
  VagAtr, SsUtGetVBaddrInSB) — every one an exact match against a pinned
  member runtime. The three apparent roster differences (CdRead2/
  SsSetStereo/_card_clear "slps-only") are pin-state artifacts, not
  linkage: sces calls the same members from unpinned rows at
  shift-aligned sites (`data_8003F3A0`+0, `c:func_80049794`,
  `data_8004F980`+0). The void also calls ~14 distinct GAME-code targets
  outside itself, most in data-labeled rows deeper in the file
  (`data_8003BFB8`+0x8ac.. slps / `data_8003C15C`+0x2bc.. sces; some
  MID-ROW: `func_8003B4F0`+0x30/+0xfc/+0x180 slps — rows holding several
  functions each), plus 2 into the rows right after the void
  (`data_8002E578`+0x0/+0x384 slps) — the boots' "data is code" pathology
  is load-bearing for the void's call graph too. Carve view: the void
  spans 10 rows slps (`data_80028428` 0x354C through `func_8002DDE0`) and
  16 rows sces (`data_80028470` through `func_8002DEE4`). The C lane's
  first boot work item is 63 functions. No carve-side action (same rule).

* Member void size-delta localization addendum (2026-10-15, de-framed
  payload; the follow-up the anatomy census set up): WHICH two functions
  carry the size deltas, and what exactly differs? Method: the prologue
  census reproduced over the de-framed payloads (63 sites both boots;
  the shift structure reproduces exactly — +0x0 sites #0–18, +0x220
  #19–56, +0x22C #57–62 — an independent audit pass), per-index size
  pairing, common prefix/suffix word analysis, word-level diff of the
  two delta middles, and a capstone decode under the region-bit jal law
  (target = (PC & 0xF0000000) | (idx << 2); adding the load base
  0x80020000 instead skews every target +0x20000 — caught immediately
  because the corrected strcat targets landed on the anatomy census's
  documented runtimes 0x8002DC00/0x8002D9F4). THE ANSWER:
  - Delta 1 = function #18 (head void+0x2890 both boots → slps
    0x80029AE8 / sces 0x80029B30; slps 0x4A4 B vs sces 0x284 B). A
    descriptor/string composer: builds a fixed-format record on the
    stack from rodata presets selected by a mode dispatch (`sltiu` 2 /
    `bnez`), composes a string, tail-calls function #19 (both boots —
    the next void function's head, 0x80029F8C / 0x80029DB4), and in the
    >=2 mode also calls an internal void helper (0x8002A71C /
    0x8002A544). strcat 4x slps vs 8x sces — the anatomy roster's whole
    strcat delta (x14 vs x18) lives in this one function. The +0x220 is
    codegen shape, not functionality: slps expands each fixed-size
    rodata→stack copy as an alignment-dispatch loop pair (`andi` 3 →
    lwl/lwr 16 B-per-iter loop vs lw/sw loop + byte tail, `j` into
    shared tails), one full expansion per preset (0x30 B and 0x20 B
    sizes x2 modes), while sces emits straight-line lwl/lwr single-shot
    copies for the same transfers. 9 common head words, 8 common tail
    words; first divergence at function word 9 — the gp-relative load
    slot (0xa0($gp) slps vs 0xa4($gp) sces, the differing .sdata
    layouts).
  - Delta 2 = function #56 (head slps 0x8002C110 / sces 0x8002BF38;
    slps 0x208 B vs sces 0x1FC B). The void's external game-code
    fan-out: 14 jals to 14 DISTINCT targets outside the void, the same
    call sequence in both boots at per-boot layout offsets (slps
    0x800436B8/0x800438D8/0x8002CA1C/0x8002EAA0/0x800440D8/0x8002C7C8/
    0x80043CE8/0x80044F20/0x80044BFC/0x80044CE0/0x800499C8/0x80045304/
    0x800440C8/0x8003E518; sces each a few words into its own layout;
    3 sit just past the void end 0x8002C7B0, 11 deeper in the file).
    The same function also materializes a blob into low memory with an
    identical structure both boots (jal a getter, alignment-dispatch
    copy loop to dest 0x80016604, a 0x20-stride table-walk loop of
    calls, halfword stores into 0x8006xxxx globals). The +0xC is
    immediate-range fallout of a GENUINE content difference: the blob
    is 0x8620 B in slps vs 0x7E20 B in sces (+0x800), so slps's size
    and end immediates (0x8620/0x8624) exceed the signed-16-bit
    addiu/sw range and force 2-instruction ori+addu / ori+sw expansions
    at exactly 3 sites (+3 words = +0xC); sces's 0x7E20/0x7E24 fit
    single instructions. Bonus content delta in the same function: the
    table-walk bound is `slti` 0x3E (62 entries) slps vs `slti` 0x3A
    (58) sces — size-neutral, another real per-boot difference. Word
    diff ratio 0.747; every other REPLACE block is a per-boot literal
    (jal fields, gp/data slots, rodata addresses).
  - Census law confirmed: both deltas are real content/codegen
    differences, not prologue-census artifacts; the other 61 functions
    pair at equal sizes. No carve-side action (same rule) — the
    de-frame transition re-derives; functions #18 and #56 are the
    boots' first two shape-known C-lane targets.

* Func #56 fan-out row-containment addendum (2026-10-15, de-framed
  payload; the follow-up the size-delta localization queued): WHERE do
  the 14 external targets live in the carve? Method: `deframe.py`'s
  runtime_to_framed per target + yaml row containment over
  `config/splat.<t>.yaml` (336 rows slps / 325 sces), cross-checked
  against the pinned member rows. THE SHAPE (both boots, same call-site
  order): 10–11 of 14 targets land at ROW STARTS of rows the carve
  already labels code — 9 asm `func_` rows slps (10 sces, one of them
  `func_8002E394`, the row right after the void), sces target 13 is
  type `c` (16-byte matched-C row) where slps's counterpart is asm —
  plus ONE mid-row asm target each (+0x154 into `func_800489B4` slps /
  +0x14c into `func_800489C8` sces — rows holding several functions,
  the census's `func_8003B4F0` pattern again); the remaining 3–4 land
  in DATA-labeled rows: slps 4 (`data_80048C84`+0x1d4 and +0x5e4
  mid-row x2, `data_8002E578`+0x0 and +0x384), sces 3
  (`data_80048CAC`+0x1b8 and +0x5c8 mid-row x2, `data_8002E5E0`+0x138).
  ATTRIBUTIONS:
  - The anatomy census's "plus 2 into the rows right after the void
    (`data_8002E578`+0x0/+0x384 slps)" are BOTH func #56's calls
    (targets 6 and 3) — and the blob-getter call is one of them
    (target 3): slps `data_8002E578`+0x384 vs sces
    `data_8002E5E0`+0x138 — different rows entirely (the per-region
    row split differs there: slps one 0x11C4-byte row, sces a
    0x1A0-byte row).
  - Target 6 (0x8002C7C8 slps / 0x8002C5E4 sces) is a LABEL ARTIFACT
    PAIR: slps buries it at `data_8002E578`+0x0 (data), sces labels
    the same call target `func_8002E394` (asm, row start) — the same
    function, opposite labels per region.
  - Target 4 is the free() BIOS THUNK: carve `func_80030E40` slps /
    `func_800308B4` sces, both `= free; // type:func (pinned member
    row)` in the symbols files — func #56 calls free() (the release
    side of its blob materialization).
  - Target 13 is a 16-byte row with per-region type disagreement: slps
    `func_80049778` (asm) vs sces `func_80049794` (c, matched-C) — an
    sdk-thunk-class row labeled asm in one boot and c in the other.
  - func #18's rodata presets sit in the carve's FIRST data row
    `data_80020000` near its head (+0x8fc/+0x90c/+0xa70/+0xaa0 slps,
    +0x908/+0x918/+0xa60/+0xa7c sces); its descriptor pointers
    (0x8004BF18/0x8004BF44 slps) sit in the tail mega-row
    `data_8005135C` at +0x143c/+0x1468.
  - Net: the void's external fan-out is MOSTLY into properly-labeled
    code — func #56's own "data is code" instances are the 3–4
    data-row targets above; the anatomy census's deeper data-row
    examples (`data_8003BFB8`+0x8ac, `func_8003B4F0` mid-row) remain
    attributed to other void functions. No carve-side action (same
    rule).

### Carve the code out of the `data` rows — the other direction

The landed carve-pin patch handles `asm` rows whose bytes are data. The mirror
error is larger: rows the splat map calls `data` that are really code, and it
is measured, not suspected.

* 12.9% of every byte the eight maps label `data` is byte-verified Psy-Q
  library code — 446 KB of 3.45 MB — measured with `tools/libshare.py` at
  3.3. 77% of the whole library share sits in `data` rows.
* Runtime agrees: `tools/coverage_vs_fragments.py` reports regions the static
  classifier calls `ORPHAN … end=data_stop` that the CPU executes — 13 in
  slps_00270, 4 in g3org_jp, 1 in mainmenu_jp.

A walk-stop rule symmetric to the pin — a `data` row whose bytes are a
byte-verified SDK member, or carry a high instruction-validity density — would
surface them. The SDK re-pin is DONE (see Log): the 3.3 match set below is
this task's evidence base.

**The walk-stop rule itself is DONE (see Log 2026-10-12, the `--sdk-anchors`
rule): 805 member rows carved in one pass, 8/8 GREEN.** What remains here is
the NAME side: the ~800 new rows are `func_XXXXXXXX` — the anchors file
holds each row's evidence name, so the next adoption pass is: regenerate
`sdk_members.txt` (the adoptable set changes now that the rows exist), then
adopt through `config/symbols.curated.txt` as before.

**Evidence census (2026-10-12, `sdk_in_data.py` repo-external): 606 of the
968 anchored/unique placements sit inside rows the maps label `data`** —
per target: slps 52, sces 64, mainmenu_jp 97, mainmenu_eu 90, g3_jp 95,
g3_eu 69, g3org_jp 66, g3org_eu 73. The worst single rows are the tail data
blobs (mainmenu_jp `data_80086D3C` 0x432c4 holds 38 members; g3_jp
`data_8006EB0C` 0xe948 holds 39). First two carves landed as the
pattern-proof: slps `data_80040FF8`/`data_80041690` (4-byte walk-gap
artifacts at anchored `StSetRing`/`_SpuDataCallback` starts) re-typed to
pinned asm rows, 8/8 GREEN.

### Re-pin the Psy-Q SDK to 3.3 and regenerate the SDK reports

DONE 2026-10-12 — see Log. The reports now pin 3.3 (144 anchored placements,
897 sig agreements); docs/MATCHING.md §3b/§3c updated.

## Log

**2026-10-13 — region policy set: Japan is the target, Europe is the
cross-check (GUIDELINES.md §2).**
- Until now every library member was rolled out to all eight builds as a
  matter of course (JP 85 / EU 83 matched), treating EU as a co-target. That
  doubled the symbol count and the address-collision surface for code that is
  byte-identical between regions.
- From here: match the JP row first; port the EU twin when the rollout is
  mechanical and skip it when it is not; an EU port never gates a function.
  Already-landed EU matches stay — they are free verification. Both discs stay
  staged; all eight hashes stay in `config/sha1` as oracles.
- The durable fix for the per-target duplication is real member names: one
  `SetVideoMode` file listed in each overlay manifest instead of eight
  address-named copies (16 src files for the two VMODE getters today). EU
  policy halves that; naming eliminates it.

**2026-10-13 — the runtime-opaque blocks are sector framing; row-start
reachability probed live.**
- The two "runtime-opaque blocks" the 58Fxx pass pinned (mainmenu_jp
  `data_80058D90` 308 B, `data_800596C4` 300 B) are MODE2 sector framing, not
  runtime-patched code: they sit in the 304-byte EDC/ECC + next-header gap, and
  their "real bne targets" (`0x80058DAC`, `0x800596CC`) land in ECC. So that
  gate resolves to dead branches. `func_8005A014`'s row is framing too — its
  "18 noise words" are ECC and its "5 jal sites" misdecode. 341 rows are >90%
  framing (241 `data`, 100 `asm` — queued above). Full layout and the
  carve↔runtime mapping: `docs/RUNTIME.md`, `tools/deframe.py`.
- Row-start reachability, probed on this host (gdb via
  `tools/gdb_stub_proxy.py`, breakpoints at the mapped runtime addresses):
  `func_80058EC4`, `func_80058F08`, `func_80059520`, `func_800597F0`,
  `func_8005981C` and `func_800599A8` were **not reached in ~60 s** of the
  unattended attract cycle, while a breakpoint at the live PC fired
  continuously — the mechanism works, so those rows are simply not on the
  attract path. Reaching them needs a driven session (input), not a longer run.

**2026-10-12 — JP's A9D8-twin island head carved: func_8002AA38 (0x18c
pinned), the twin zone now mirrors EU's func_8002A9D8 structure.**
- Evidence (scripts/jp_head_evidence.py, repo-external — correct
  file-offset arithmetic: vram = file offset + 0x8001F800, the exe
  header is 0x800): the island head's ONLY static reference on either
  disc is the equal-path tail `j` — JP 0x8002C448 -> 0x8002AA38 (inside
  the pinned func_8002C220 row), EU 0x8002C3E8 -> 0x8002A9D8 (inside the
  walk-derived func_8002C3A4 row). Zero beq/bne on both discs.
  CORRECTION to the cron-20261012-1411 record: the claimed "bne at EU
  0x80041538 -> 0x8002A9D8" does not exist. The bne at that (skewed)
  address is real but targets 0x80040DBC; and the definitive
  target-space scan — every branch class and j/jal in the whole image,
  skew-independent — finds ZERO branches to 0x8002A9D8 (EU) and zero to
  0x8002AA38 (JP). EU's rescue came solely from the j source being
  v4-visible (walk-derived row); JP's head stayed data because its j
  source is pinned-row-invisible (the 1411 MIS-STEP lesson, now the
  positive explanation too).
- Twin proof: JP [0x8002AA38,0x8002ABC4) vs EU [0x8002A9D8,0x8002AB64)
  = 99/99 words IDENTICAL (not even relocation diffs). EU's side is
  scanner-verified code (the v4-rescued func_8002A9D8, 0x540). Mirror
  structure: the equal-path tail j lands +0x10 into the island on both
  discs (JP .L8002ABD4 inside func_8002ABC4 / EU .L8002AB74).
- Carve: data_80029D38 0xe8c -> 0xd00, new [0xB238, asm,
  func_8002AA38] # 0x18c pinned. Pinned because JP's j source lives in
  a pinned row (v4-invisible) - an unmarked row would regenerate as
  data (the preserved_types rule). The equal-path j now renders
  `j func_8002AA38`.
- MIS-CARVE + revert (one scan cycle lost, the 1126 lesson repeated):
  first attempt placed the row at yaml 0xAA38 — vram/yaml conflation,
  vram 0x8002AA38 is yaml 0xB238. Symptom: the row's own branch to
  0x8002A40C (func_80029518's row) failed PC16 relocation because the
  content was linked 0x800 above its disassembly base. The diagnostic
  scripts had the same off-by-0x800 (file offset vs payload offset) -
  fixed in the persisted script before any number above was recorded.
- Gates: make verify mainmenu_jp GREEN; 8/8 GREEN; re-scan idempotent
  (yaml diff = the carve only); screen 0 DATA / 0 SUSPECT everywhere;
  ratchets 365/12 unchanged (asm-only carve); matched functions 82.

**2026-10-12 — the state-map naming pass: 36 curated data names, the
unknown_data ratchet 102->12, the twins tied by identical names.**
- New mechanism (tools/scan_functions.py): the symbols writer now emits a
  generated DATA block - curated offsets that are not function entries go
  out as `// type:s32` (splat's parser has no bare `data` type; all
  current curated data are `extern int`). splat applies them to the
  dlabels, the generated asm defines the names, C externs resolve.
  Mid-row splits follow the existing referenced-symbol mechanism; yaml
  untouched (symbols-file-only, byte-identical on re-scan).
- Names (config/symbols.curated.txt, hand sections of both mainmenu
  scopes; role-descriptive, evidence documented per name): the ten
  reset-walker bases -> state_block_0..10 (ascending; state_block_2 also
  feeds func_80026668/func_800267C8), the four-word -1 group inside
  state_block_2 -> state_rearm_0..3, the -1-or-pointer slot ->
  state_cursor (written by both the matched driver and the func_8002C220
  row behind the func_80035A78(0xC) gate), its target -> state_block_9,
  the two 8-byte id records passed to func_800267C8 -> state_record_0/1.
  EU = JP +0x814 (+0x838 for the records), same names under the
  mainmenu_eu scope per the measured relocation map.
- Renamed src/func_8002C478.c and src/func_8002C418.c (externs, call
  trains, the hand-asm store group's %%hi/%%lo refs, header mentions).
  The generated asm rename surface: both discs' state-map data rows plus
  the 15 code files referencing them; encoding columns byte-identical.
- Open question recorded, not solved: the state-map rows' bytes decode
  instruction-like (division-magic idioms, coherent 0x80149E28+
  lui/addiu patch targets - addresses OUTSIDE the 0xAA000 image, all
  eight EXEs load at 0x80020000, so no EXE lives there statically).
  Classification of that blob stays open pending runtime evidence
  (docs/RUNTIME.md); the names claim only the measured consumer roles.
- Gates: 8/8 `make verify` GREEN; re-scan idempotent on both discs;
  screen 0 DATA / 0 SUSPECT everywhere; ratchets 365/12; matched
  functions 82 unchanged. Remaining 12 D_ tokens in src/ are the
  wrapper-family flags D_800C936C/D_800C8B38 and two g3/slps small-data
  globals - each needs its own evidence pass.

**2026-10-12 — the C220-twin zone completed on EU: func_8002C238 carved
(d968396), the twin row structure now mirrors JP on both discs.**
- Word-diff proof (scripts/eu_c220_twin_recon.py, repo-external): EU
  [CA38,CC18) vs JP [CA98,CC78) at the family's -0x60 vram shift = 45/120
  relocation diffs, every one classified (state map +0x814, callee
  -0xB0, func_80035A18 -0x60, j func_8002A9D8 -0x60), 75/120 identical.
  The zone is code, byte-corresponding to JP's pinned twin row.
- Static xrefs: ZERO jal/j/branch/pointer references into the zone in the
  whole EU image (same as JP's twin) — entry is the runtime state-table
  computed jump. Carve is a pinned asm row (FABRIC honesty-carve class).
- Scanner dynamics finding: pinning the MERGED whole [CA38,CC18) kills
  the bridging walk that covers the tail row, so the tail's
  `j func_8002A9D8` never reaches the v4 strong-anchor rescue and
  func_8002A9D8 loses its 0x18c head back to data. Pinning ONLY the
  front keeps the tail's self-sustaining seed chain. Lesson: pinned rows
  are invisible to the v4 j-source scan (it reads covered/walked ranges
  only) — when carving next to a row whose walk chain feeds v4, carve
  the minimum span and leave the walk-derived neighbor unmarked.
- Hygiene: removed the stale tracked func_8002AB64.s (intermediate
  1126-state extract product, not yaml-referenced, not linked); the
  extract does not re-create it once absent.
- Gates: scan idempotent (diff = the carve), screen 0 DATA / 0 SUSPECT
  (276 subsegs), ratchets 365/102 unchanged, 8/8 verify GREEN.

**2026-10-12 — the EU twin port: func_8002C418 landed as C, the second
family-C component; the landing surfaced the C220-twin structure (ed3ba27
prequel + this session's carve).**
- `src/func_8002C418.c` (mainmenu_eu): the JP `func_8002C478` template
  ported with EU's relocation map read off the retail encodings — gp
  displacements -4 (0x3D4/0x1044/0x104C), the state-map words +0x814
  (16/16 consistent), D_800C9B3C/44 +0x838, callees -0xB0 except
  func_80035A18 (-0x60), tail `.L8002AB74` (-0x60). 61/100 words
  identical, every diff a relocation flavor. Same shaping as JP
  (r_v0 file-scope register variable, the hand-asm D_ store group,
  the output-only cse break); `noseed` marker on the yaml row.
- Landing procedure that worked: revert any speculative scan, carve the
  yaml row at the byte-verified address (yaml offset = the EXE file
  offset = the .s comment column; VRAM = yaml + 0x8001F800 on BOTH
  discs — the worklog's earlier +0x800 offset confusion cost one
  mis-carve + revert), `make scan` (the row survives first try), check
  the config diff, extract, screen, verify.
- The scan surfaced two honest code islands from the data row:
  `func_8002C3A4` (0x74, the C220-twin's tail — jal trains, the shared
  state words, the 0x28-frame epilogue) and `func_8002A9D8` (0x540,
  the label block `j 0x8002A9D8` in that tail anchors, v4-rescued +
  v3c-merged with the following walk). Both end at real epilogues;
  the screen stays 0 DATA / 0 SUSPECT (275 subsegs). Structure mirrors
  JP: the equal-path tail target sits +0x10 into `func_8002A9D8` as
  JP's does into `func_8002ABC4`.
- Safety proof: the seven other targets' scans byte-identical; 8/8
  verify GREEN; ratchets 341/57 -> 365/102 (the new file's own
  placeholder tokens, itemized in ratchets.json per precedent); re-scan
  idempotent.
- Next: the EU twin of the C220 row is now a carve + pin task (see
  FABRIC.md "EU c-row landing residues"), then the state-map naming
  pass (36 D_ externs across the two C files) lowers unknown_data.

**2026-10-12 — the name-adoption pass: 788 member names adopted; the
code-in-data census closes at zero (ac56ef8, 629b790).**
- `tools/sdk_curated.py` (new): reads the regenerated member report
  (3.3 + sig-db) and appends a generated adoption block to
  `config/symbols.curated.txt` — every `anchored`/`unique` symbol marked
  `adoptable` (its address is now an asm/c row start). Collision rules:
  hand entries win; a name already curated keeps its address; the same
  name at several addresses is real (LIBC/LIBC2 ship the same sources)
  but one label each — the lowest address takes it; two names at one
  address (never observed) rank by verdict then sig-db, ties skip
  loudly. The adoptable set went 13 -> 826 post-carve; **788 adopted**
  (slps 77, sces 73, mainmenu 115+99, g3 110+111, g3org 100+103), 7
  name-dup skips (memclr x6, Snd_play x1), 25 addr-curated keeps.
  Symbols-file only, per-target scoped, marker-delimited so the
  hand-written head of the file is never touched.
- 8/8 verify GREEN on the first pass with the names applied; ratchets
  317/12 unchanged; re-scan idempotent (two full passes over all 8
  produce byte-identical staged config diffs; the splat yamls do not
  move — curated stays symbols-file-only).
- `libshare.py` re-measure at 3.3: lib bytes are 13.2% of payload
  overall (slps 23.7% payload / 40.8% of code, sces 17.3%/33.1%),
  1778/11612 functions are library members (15.3%).
- Residual census (`sdk_in_data.py`): **606 -> 1 -> 0**. The last one,
  slps `scale_view_param` (MATRIX3), was the tree-wins case: the
  archive next-symbol extent (0xf0) overshoots into the empty C
  function func_80036CFC (the first oracle match, `jr $ra; nop`) that
  the original link placed between it and select_max_param. The true
  extent is the row itself (0xe8) — carved as a pinned member row,
  name adopted (629b790). Every byte-verified SDK member now lives in
  an asm row under its real name.

**2026-10-12 — the `--sdk-anchors` rule: the whole 3.3 match set carved
(c9453ae, 0922fe6).**
- `tools/sdk_anchors.py` (new): reads the committed member report + the
  archives' own .text symbol tables, writes `config/sdk_anchors.txt` — one
  row per `anchored`/`unique` placement with its extent (next symbol's
  offset, or .text size): **821 anchors across the 8 targets, zero extent
  misses.** `ambiguous` is not evidence and stays out.
- The scanner's v6 rule (docstring 13): every anchor becomes a pinned-class
  asm row at its exact address — no-walk pin BEFORE the scan, gap-carve lift
  after. The tree's kept rows win (same offset, different size = the
  hand-verified state stands, the anchor is skipped loudly). This first run:
  **805 carved** (slps 83, sces 74, mainmenu 118+99, g3 111+112, g3org
  103+105), 7 tree-wins skips — exactly the hand-carve and C-function sites
  (startIntrDMA, GsDefDispBuff, StSetRing, _SpuDataCallback, scale_view_param
  over func_80036CFC).
- `preserved_types()` recognizes the end-of-line `sdk` marker (pinned-class:
  hard no-walk span, marker re-emitted), so re-scans keep the carve even
  without the anchors file. 8/8 verify GREEN; ratchets 317/12 unchanged;
  re-scan hash-identical on all 8 targets.
- Aftermath: one rescue fragment in g3org_eu (0x80063FA4, 0x37c) earned the
  screen's DATA verdict once the pin boundary sliced it from the row it used
  to ride inside — no anchored evidence, re-typed to pinned data per the
  d683dc9 procedure. The SUSPECT human-call set grew 25 -> 28 (same
  score-25 short-fragment class near the new pin boundaries).
- The big tail blobs dissolved as predicted: mainmenu_jp `data_80086D3C`
  (0x432c4, 38 members) and g3_jp `data_8006EB0C` (0xe948, 39) are now runs
  of member rows with the unevidenced remainders honestly data.
- Next: the name-adoption pass for the ~800 new rows (regenerate the
  report, adopt via curated); then re-measure the code-in-data share
  (`libshare.py`) — the data side should have dropped by roughly the same
  ~446 KB the census measured.

**2026-10-12 — member-extent carves: VMODE, MATRIX.o whole-member, SCLIB/COR_00
(2fc13c9, 1f039fc, f05f963).**
- psyq re-clone SOLVED sparse: `git clone --depth 1 --filter=blob:none --sparse`
  + sparse-checkout `3.3` = 14M (the full clone stalls at ~116K). Member .text
  extents now measurable: `scripts/member_extent.py` (repo-external) prints
  size + symbol offsets from the archives.
- slps `data_8003523C` (0x51c): LIBETC VMODE.o (0x28, SetVideoMode+GetVideoMode,
  both sig-db) carved out after its zero word; both names adopted; the row's
  veneer stub + one big framed function stay data (no evidence).
- sces `data_80039684`/`data_80039730`: the WHOLE LIBGS MATRIX.o (.text 0x3e8,
  10 symbols) spanned three rows - GsInitCoord2param crossed a row boundary
  (8-byte head in row1, tail 0x24 was an existing walk-owned asm row); member
  split at every symbol boundary into 10 pinned rows, all 10 names adopted
  (all sig-db). The 0xa30 past the member stays data.
- slps `data_80038094` (0xbe8): LIBGS SCLIB gte_rotate_z_matrix (0xb8) +
  LIBGTE COR_00 RotMatrixC (0x180, sig-db) carved; the 0x2a8 gap and 0x704
  tail open with framed prologues (code) but have no anchored evidence - stay
  data until the --sdk-anchors rule.
- 8/8 verify GREEN after each commit; ratchets 317/12 unchanged. Adopted-name
  count: slps 9, sces 14 curated rows emitted.
- Next: the remaining multi-member rows all live in the census list; the
  biggest lever is the --sdk-anchors scanner rule (data_gaps walk-stops at
  byte-verified member starts) so unevidenced prologue runs like
  data_80038150/data_80038578 get surfaced automatically.

**2026-10-12 — the single-member data rows carved; member names adopted
(b8b2bd6, 993af95).**
- slps `data_800316C0` (0x48) and `data_8003ADE8` (0xc) + sces
  `data_8003A8B0` (0xc) decompose as `[4-byte unreferenced zero word |
  anchored member entry]`: `startIntrDMA` (unique + sig-db agree, framed
  body ending `lw ra` exactly at the row end) and `GsDefDispBuff` twice
  (unique; the old row boundary BISECTED the function — the following
  row's frame setup consumes the `$v0` the 2-instruction head loads and
  stores a0/a2/a1/a3 as the x/x2/y/y2 display-env halfwords). Rows
  re-typed to pinned data + pinned asm starting at the member's true
  address.
- `tools/scan_functions.py` now emits curated names for pinned member
  rows (their start IS the byte-verified member entry even though the
  walk never produced a range there); symbols-file-only, like every
  curated name.
- All 13 unambiguous `adoptable` names from the 3.3 report are now
  adopted (6 new: `GsSortGLine`, `select_max_param`, `GsClearOt` x2,
  `SpuSetNoiseVoice`, `_SpuDataCallback`). The 2 `ambiguous` pairs
  (GsSetProjection/SsSetNoiseOff) stay unadopted by design.
- 8/8 verify GREEN after each commit; ratchets 317/12 unchanged.
  Remaining scale step: group contiguous member runs inside the big
  multi-member rows (mainmenu_jp `data_80086D3C`, g3_jp `data_8006EB0C`)
  — each member's `.text` extent from the 3.3 archives is needed so the
  carve ends where the member ends (the psyq re-clone stalled twice this
  session at ~116K; try sparse/blob-filtered clone next).

**2026-10-12 — the SDK re-pin landed (3.3).**
- `config/sdk_members.txt` regenerated against `~/psyq/3.3/PSX/LIB` with
  `--sigs psx_psyq_signatures/330`: 968 placements (was 781), **144 anchored
  (was 8 — one per target; now 16-23 each)**, 13 adoptable names (was 11),
  897 signature-DB agreements. `config/sdk_symbols.txt` is UNCHANGED: the
  same 5 veneer sites resolve at 3.3 and 4.0.
- The 117 `sig-db elsewhere` rows concentrate exactly where §3c says sibling
  families live: 60 LIBSND + 57 LIBCD. One `no-hit`.
- docs/MATCHING.md §3b/§3c updated to the 3.3 path and the measured
  agree/elsewhere census. The code-in-data carve below can now use the 3.3
  match set as its evidence base.

**2026-10-12 — the Psy-Q library share, calibrated.**
- `tools/libshare.py` — matches each SDK member's *individual* functions (split
  at its own `.text` symbols) against the payload, not whole members. Over the
  eight targets at 3.3: **13.2% of payload bytes** are Psy-Q library code, and
  about the same share of the scanner's function list (1509/11463). The boot
  executables are library-heavy (slps 24%, sces 17%); the game executables run
  9–15%.
- `tools/sdk_members.py` under-counts badly: it needs an entire member present,
  and these binaries linked the library function-granular. On slps_00270 the
  whole-member scan covers 1.8% of the payload against 23.7% here. The
  function-level set recovers 97% of the committed report's 810 placement rows,
  83% of its 128 confident rows, and finds ~5× more.
- The pinned SDK is the wrong release: the same scan finds 1.8% of the payload
  at 4.0 and 13.2% at 3.3 (see Queued).
- Library code sits inside ranges the splat map calls `data` — an evenly
  0x30-spaced libetc callback block (`ResetCallback`, `DMACallback`,
  `VSyncCallback`, `GetIntrMask`) lies inside `data_8002FD9C` in slps_00270.
  That carve error runs the other way from the 37 ranges
  `tools/code_data_screen.py` flags.

**2026-10-12 — carve-type pins applied (d683dc9).**
- The queued `docs/carve-pin.patch` landed: 37 DATA-verdict rows re-typed to
  `pinned` data across the eight splat maps, `preserved_types()` taught to
  preserve them. The patch file stays for reference.
- Two round-trip gaps in `tools/scan_functions.py` had to close before the
  pins held; both are now regression-tested by the pin's own acceptance check
  (`code_data_screen --all` after every re-scan):
  1. *marker loss* — the generated-block writer never re-emitted the
     `pinned` comment, so the next scan read an unmarked data row and
     re-typed the range back to code. `preserved_types()` now returns the
     pinned set and the writer re-emits the marker; double scans are
     idempotent on all 8 targets.
  2. *pin-span enforcement* — `hard_stops` only blocked seeds AT the pinned
     start; a j-target strictly inside the span seeded a walk that swallowed
     the pin (witnessed: g3_eu `func_80022A1C` out of pinned
     `data_80022A18`). Pins are now no-walk zones: `walk()` refuses in-pin
     starts and stops before pin words; the v2/v4/v3 seed loops skip pin
     interiors.
- The no-walk rule exposed a third gap: kept rows fully inside a data gap
  were swallowed by the gap (mainmenu_jp `data_800253C4`). `main()` carves
  kept gap rows out as their own subsegment pieces now.
- Post-apply: all 8 targets `make verify` exit 0; stale pseudo-function rows
  removed via `clean_stale_asm.py`; re-audit = 0 DATA / 25 SUSPECT (25 is the
  documented human-call set); ratchets 317/12 and matched C count 80
  unchanged.

**2026-10-12 — static carve auditing.**
- `tools/code_data_screen.py` — flags code subsegments whose bytes are data. 37
  across the eight targets; calibrated against the known `0x80021800` =
  `CD_cachefile`.
- `tools/crossbuild_align.py` — aligns a JP/EU pair by unique-k-mer anchors plus
  LIS. Inside aligned regions the two sides are 88–93% byte-identical, against
  16–24% at fixed offset. Reports that ~35–44% of mappable boundaries disagree
  on code-vs-data.
- `tools/struct_infer.py` — clusters memory accesses into field maps with
  signedness (`lb`/`lbu`, `lh`/`lhu`); drops runs of identical non-nop words,
  which are data misdecoded as code.
- `tools/crossbuild_diff.py` — kept as a weak reference; its docstring records
  why fixed-offset byte-identity cannot validate boundaries here.
- `docs/TOOLCHAIN.md` — compiler-fingerprint table re-measured; the counts had
  drifted after the stale-asm cleanup.
- `docs/RUNTIME.md` — the PCSX-Redux runtime harness, plus its measured limits:
  exact-address Exec breakpoints fire, range breakpoints and watchpoints do not,
  the exe entry is not caught, and the GDB stub shares the same breakpoint
  store. It is not a carve oracle.

**2026-10-13 — flag naming closes unknown_data; reset-walker zone carved.**
- Queue item 2 (wrapper-family flags): the last four D_ objects named through
  the curated data-symbol path — `menu_state_flag` (0x800C8B38 JP / 0x800C936C
  EU; armed 0/1 by the wrapper families before the menu primitive; no other
  static ref on either disc), `boot_flag_0` (0x80063268 slps word; writes
  measured 0/1 via the leading-nop stub family: cleared per walk iteration by
  func_80025AE0, set by twin stub func_80025AF0, no static reader),
  `boot_flag_1` (0x80063294 slps halfword; cleared by stub func_8002A0DC +
  at func_8002706C; ==1 gate in func_80027100 re-enters the walk at
  func_80026288; set-site outside the current scan). unknown_data ratchet
  12->0 — the placeholder class is empty by construction now. Commit 55540b9.
- Queue item 3 (reset-walker zone): data_80026250 (JP, 0x40c) decoded as
  coherent code — gp-table leaf, retry-loop, device-setup block, and the
  reset walker at 0x800263e8. The walker's mid-function entry 0x80026414 is
  the image-wide workhorse: 936 jal sites + the C driver's ten + 14 j-shims
  into its prologue/epilogue + the 9-word dispatch table at 0x800202ec
  (mid-function pieces — the static state-table). Carved
  [0x6A50, asm, func_80026250] # 0x2c4 pinned + tail data row 0x148; extract
  splits at the five function heads (func_80026250/26294/262FC/263E8/264B4,
  alabel func_80026414); the tail row carries a referenced func_80026524
  (walker-family continuation — future carve). 8/8 GREEN, ratchets 365/0,
  re-scan idempotent. Commit d2bf440.
- Runtime evidence (queue item 1) stays blocked: no pcsx-redux, no region
  BIOS, no raw-BIN disc images in the sandbox (build/work empty).

**2026-10-13 — EU walker-family twin carved; state table named on both discs.**
- Queue item 1 (EU twin of the reset-walker carve): scripts/dispatch_table_recon.py
  (repo-external, persisted) located the EU zone head at yaml 0x69A0 = JP - 0xB0
  exactly as the 1411 callee map predicted, and proved the twin: JP
  [0x6A50..0x6D14) vs EU [0x69A0..) = 156/177 words identical, all 21 diffs
  relocations (j/jal targets + gp displacements). EU xref census mirrors JP:
  937 jal -> 0x80026364 (the mid-function entry, `addu a1,v0,zero` after the
  jal's delay slot), 14 j-shims (11 -> 0x8002634C, 3 -> 0x80026334 = JP twins
  -0xB0), the 9-word dispatch table, zero external branches. Carved
  [0x69A0, asm, func_800261A0] # 0x2c4 pinned + unmarked tail row 0x88; the
  scan KEPT the tail as code (seed chain self-sustaining — unlike JP where the
  tail is data; section F of the recon shows the tail bytes are NOT twins:
  11/134 words identical, so each disc's tail classification stands on its own
  bytes). Extract splits the pinned row at the six twin heads (func_800261A0/
  261E4/2624C/26338/26364/26404 — sums to 0x2c4), with the workhorse entry
  func_80026364 as its own glabel block; the tail renders as small blocks with
  alabel func_80026474 = the twin of JP's dlabel func_80026524. Ripples, all
  byte-identical: cross-row j-shims retarget local labels (JP's .L8002C350
  precedent), the old spurious func_80027050 boundary (no symbol, no xref)
  merged away, the dispatch-table words that resolved to symbols now render
  raw hex (JP's landed rendering). Hygiene: removed stale tracked
  data_800261A0.data.s + func_800261E4.s (EU) and data_80026250.data.s (JP,
  left over from the 1641 carve); extract does not re-create them. 8/8 GREEN,
  ratchets 365/0, re-scan idempotent, screen 0 DATA / 0 SUSPECT. Commit 251e708.
- Queue item 2 (dispatch-table naming): the 9 pointer words at 0x800202EC..
  0x80020310 (yaml 0xAEC..0xB10, same addresses on BOTH discs) named
  state_table_0..8 through the curated data path. Evidence: targets are the
  walker family's mid-function pieces (JP: 0x800264C0 = func_800264B4 +0xC,
  0x80026454 = func_80026414 +0x40, 0x8002647C = retry-loop tail +0x68,
  0x800264FC = func_800264B4 +0x48; EU = JP - 0xB0 throughout); zero static
  readers image-wide (no pointer words into the table range, no lui/addiu/ori
  pair materializes any of its addresses) — the table is consumed purely by
  the runtime computed jump, so the names claim the pointer roles only,
  pending the (still blocked) runtime evidence. 8/8 GREEN, ratchets unchanged,
  yaml untouched (symbols-file-only). Commit b4cf7f6.

**2026-10-13 — walker family split at function boundaries; entry contract measured.**
- Queue item 1 (F2/F3 honest splits): the walker-family pinned rows are now
  five function-boundary-aligned rows per disc — F1 gp-table leaf (0x44),
  F2 retry loop (0x68), F3 device setup (0xec), F4 the walker function
  whole (0xcc), F5 continuation (0x60); EU = JP - 0xB0 throughout. The
  scan preserves pinned rows verbatim, so the yaml diff is exactly the
  split; each function keeps its own file for future C or runtime work.
  8/8 GREEN, ratchets 365/0, re-scan idempotent, screen clean.
  Commit 4327547.
- Queue item 3 (entry decode): scripts/walker_entry_decode.py (repo-
  external) settled the func_80026414 contract. The walker function
  (263E8..264B4) is one function: prologue -> s1=a0/s3=a1/~268M counter ->
  phase-1 loop (head 26414: query jal 80059f90, walk jal 800257a4(s1,v0),
  retry on != -1, fatal 0x800200AC) -> phase-2 loop (head 26454: query
  jal 80059f9c, walk(s3,v0), fatal 0x800200C8) -> epilogue returning the
  walk result. 26414 is the phase-1 LOOP HEAD, not an entry: the C
  driver's ten sites are normal C calls (a2 in the delay slot, matching
  the matched source), but addu a1,v0 clobbers the mode argument at
  entry — the live inputs are the caller's v0/s1/s3. All 936 image-wide
  jal sites share the same C-style prefix, so the facade is uniform.
  New open fact: both query targets (80059f90/80059f9c) are scan-
  classified DATA (incoherent heads; the word A4239F7C recurs in other
  data rows) while the walk step 800257a4 is code — the web's own
  callees are classification-mixed, extending the state-map blob
  question; runtime evidence remains the gate. Written into
  docs/FABRIC.md (frame contract). Commit c6cfd7f.
- Runtime harness re-check: still blocked (no pcsx-redux, no BIOS, no
  raw-BIN disc).

**2026-10-13 — query-target question resolved: carve, not debunk.**
- Queue item 1 (carve or debunk 80059f90/80059f9c inside data_80058DA8):
  CARVED. scripts/query_target_recon.py + query_target_recon2.py (repo-
  external) measured: (a) the two query targets are mid-stream entries
  inside a real function whose clean 0x18-frame head is 80059f40 —
  prologue, print-style call func_80037410(a0=D_800C9998), the 42x-jal'd
  func_800598CC, branch, entries, clean epilogue; (b) 8 image-wide jal
  sites in real code enter the entries directly (Q1 5x: walker F3
  0x8002630C, F4 0x8002640C, 0x80024B28, 0x80043570, 0x80043678; Q2 3x:
  phase-2 loop 0x80026454, 0x80062C38, 0x80062E74); (c) the A4239F7C
  word (sh $v1,-0x6084($at)) recurs 35x image-wide because it is a live
  instruction of this and sibling counter blocks, not table data; (d)
  the EU scan had already carved the same library as code
  (func_800597F4 hosts the EU twins 80059bc0/80059bcc = JP - 0x3D0) —
  the JP scan had simply misclassified the whole region as one data row.
- Carve (JP only; EU already code): data_80058DA8 0x13dc -> data 0x1008
  + pinned func_80059F40 (0x78) + pinned func_80059FB8 (0x38, the
  die-block: a0=D_80022218 ptr table + "file not found", then u16
  D_800C9F7C--) + data 0x194; the scan then reclaimed func_80059DB0
  (0x190, a coherent counter state-machine) above the pinned rows and
  split the tail data into data 0x24 + func_8005A014 (0x48, content
  still undecoded .words despite 5 jal sites - kept visible as its own
  row) + data 0x128. Curated evidence block pins the entry names and
  contracts; extract gives each function its own file; the four data
  sidecar ripples are symbol-resolution only. Gates: 8/8 GREEN first
  try, ratchets 365/0, re-scan byte-stable, screen 0 DATA / 0 SUSPECT.
- Open threads this carve exposed: (1) the data head [0x395A8..0x3A5B0)
  still hides the rest of the library - two branches from
  func_800588D4's row land at 0x80058DAC inside it, and the tail-block
  epilogue at 0x80058EC4 restores a frame no head in the row sets, so
  func_800588D4's row end at 0x395A8 is suspected to cut a function
  whose continuation sits in the data head; (2) whether the query
  entries execute as decoded (callers do not set $at in their 6-word
  prefixes) shares the walker's runtime-evidence gate; (3)
  func_8005A014's 5 jal sites vs undecodable content.
- cron-20261012-2141 (2026-10-13): re-bound func_800588D4 and carved the
  library above it out of the old data_80058DA8 head (queue item 1 from
  the previous session). Decode pass (scripts/head_lib_decode.py +
  scripts/head_blob_recon.py, repo-external) mapped [0x80058F00..0x80059DB0)
  and found the runtime-opaque block pattern: TWICE the library shows
  clean code -> high-entropy undecodable block -> clean code, the blocks
  ending in a shared 7-word marker and taking real bne targets INSIDE
  them (0x80058DAC x2, 0x800596CC). Carve (JP only): func_800588D4
  re-bound 0x4d4 -> 0x4bc pinned (true code end 0x80058D90; the D48 tail
  the old extract rendered .word decodes clean - lui+lh to known global
  D_800CA59C, both bne targets 0x80058DAC, s2 write-backs); pinned
  data_80058D90 (0x134) + func_80058EC4 (0x3c, the detached epilogue
  sp+0x68 inverse of the prologue, sh v0/v1 -> D_800C9D10/D_800C9D0E
  then jal func_8005A514); the 14-function middle stays scan-owned
  (func_80058F08 0x618 coarse row); pinned func_80059520 (0x1a4) +
  data_800596C4 (0x12c, second marker instance) + detached tail
  func_800597F0 (0x2c); pinned func_8005981C (0x80, jr-ra stub + twelve
  vector negate/swap leaves the scan demoted to data) + func_800599A8
  (0x9c, jump-table dispatcher, table at 0x8002 21F4). EU cross-check:
  EU holds the same library with its own layout (data_80058DF4 0x104 +
  func_80058EF8 0x860, jal/branch into 0x80058dbc/0x80058dec/0x80058e38)
  but has no byte-identical blob. New FABRIC section "The runtime-opaque
  block pattern"; curated evidence block carries the full measured facts
  and the runtime gate (patched/decrypted in place vs provably-dead
  branches - static evidence cannot settle it). Gates: 8/8 GREEN first
  try, ratchets 365/0, screen 0 DATA / 0 SUSPECT both mainmenu discs,
  re-scan byte-stable. Open threads: (1) the coarse rows func_80058F08
  0x618 / func_80059A44 0x4fc hide 16 measured function boundaries that
  a future C-match pass will need as row splits; (2) data_80058D90 /
  data_800596C4 interpretation shares the $at runtime gate; (3)
  func_8005A014 still undecoded (5 jal sites).

**2026-10-13 — gdb sessions against the stub unblocked.**
- `tools/gdb_stub_proxy.py` — an RSP shim so gdb can attach at all: the stub
  reports its thread as `p1.t1` (`qC` reply, threads-XML id) and gdb 18.1
  aborts with `invalid remote ptid: p1.t1` before any command runs;
  `set remote threads-packet off` does not save it (`qC` still kills the
  session); upstream `gdb-server.cc` still emits `p1.t1`. Shim verified on
  `r7505.d1bc093f`: threads, registers, disassembly, memory reads, `Z0` +
  `continue` to a hit; one client at a time, `detach` unimplemented.
- Corrections to the 10-12 runtime log: headless disc runs die mid-init
  regardless of `-debugger` and with no client attached (3×, always after
  the pad-driver banner) — not a debug-mode-specific crash; and stub exec
  breakpoints fire WITHOUT `-debugger`, so the stub path is cheaper than
  the Lua path for free-run breaking. Recipe in `docs/RUNTIME.md`.
- Runtime evidence (queue item 1) is unblocked on this host: pcsx-redux,
  region BIOS, raw-BIN disc + cue all present.

**2026-10-13 — The 58Fxx library split: 19 honest rows per the
walker-family recipe, and a measured zero-entry contract.**
- Queue item 1 from cron-20261012-2141. The coarse rows func_80058F08
  (0x618) and func_80059A44 (0x4fc) are now split on their measured
  prologue/epilogue boundaries (scripts/head_lib_decode.py map,
  scripts/row_split_census.py census, both repo-external). Row A -> 14
  rows (11 functions + three 8-byte jr-ra leaves: 80058F94 with a real
  delay-slot store sh $zero,0x2c($a0), 80059114/800593D4 jr-ra+nop);
  row B -> 5 rows (clip/cull twins 80059A44/80059BC4, stub 80059D4C,
  leaf 80059D54, and func_80059DB0 0x190 whose 2026 carve the scan had
  re-merged into the coarse row). All 19 rows pinned; sizes sum exactly
  to the two old rows; extract renders the interior entries as alabels
  (func_800590AC/func_80059100 in func_80059074.s) - the walker-family
  rendering.
- NEW MEASURED FACT (entry contract): image-wide census of jal/j,
  conditional branches, pointer words and lui+lo materializations finds
  ZERO static references to any of the 19 row starts. The library's
  only static callers enter at 6 INTERIOR addresses (67 jal sites):
  0x80058F20 (1x, counter-bump tail), 0x800590AC (16x, indexed u16
  read tail), 0x80059100 (46x, clear-fields tail ending jr ra + addiu
  sp,0x8 - func_80059074's own frame size, but measured callers carry
  other frames, e.g. func_8005A184's 0x18; two sites are 2-word stubs
  whose first instruction is the jal), 0x800591BC (1x), 0x8005936C
  (1x), 0x80059410 (2x). Row starts are reachable only through
  runtime-built control flow - the same gate as the state table, the
  $at entries and the runtime-opaque blocks (docs/FABRIC.md).
- Dispatcher table nuance (func_800599A8, re-measured): the bounds
  check passes only for state<=4, and the four in-bounds table entries
  0x800221F4..0x80022208 are STRING bytes ("t Direct!) (Init
  Sprite)\n"); the pointer words at 0x80022214+ are out of bounds. The
  table is runtime-patched or the lookup never executes - recorded in
  curated, runtime-gated.
- Sidecar ripples: cross-row jal/j to the retired branch-target names
  now render as .L labels (func_8005F430.s, func_8006225C.s); byte
  encodings unchanged. Gates: mainmenu_jp verify GREEN first try, full
  8/8 GREEN, ratchets 365/0, screen 0 DATA / 0 SUSPECT both mainmenu
  discs, re-scan byte-stable. Curated: 19 row names + full entry-
  contract evidence block (175 curated names kept, was 157).
  Open threads: (1) func_8005A014 CENSUSED this session: 5 real jal
  sites, consistent ABI (a0=0|3, a1=-1 in the delay slot; the
  0x800634xx pair flag-gated on bit 0 of 0x800CA27C), body = 18 noise
  words with zero static writers - record in curated, settle on the
  pcsx-redux path;
  (2) the runtime-opaque blocks / row-start reachability / sp
  convention of the 46x tail all share one runtime gate (pcsx-redux +
  BIOS + raw-BIN - now present on this host, see the gdb-session entry
  above; queue the runtime check); (3) EU-side mirror of this library
  only when EU C work needs it.


**2026-10-13 — runtime stack wiped by the re-provision; len_param matched
in C across all three placements.**
- The 10-12 gdb-session entry's "now present" was ephemeral to that
  session: the sandbox re-provision took pcsx-redux, the region BIOS,
  the raw-BIN disc + cue and build/work/ with it (sweeps over the home
  tree: no pcsx binary, no SCPH image, no CHD/raw-BIN over 50 MiB). The
  eight baselines survived. BIOS and discs were user-supplied with no
  in-repo acquisition recipe, so the runtime gate-family check (row
  reachability, data-block bne targets, func_8005A014's body, the 46x
  tail's sp convention) is re-blocked until pcsx-redux is rebuilt AND
  the BIOS/disc are re-uploaded — both facts should be checked per
  session, not inherited from a previous one.
- len_param (curated; LIBGS MATRIX3 member .text+0x580, extent 0x1c)
  matched in C from one source in mainmenu_jp, slps_00270 and g3org_jp:
  frameless do-while bit-length counter; GCC 2.6.3 -O2 emitted the
  retail shape on the first compile (blez guard, sra loop, addiu
  increment in the bgtz delay slot). matched 82 -> 85.
- Ratchet lesson: placeholder-shaped tokens in src/ text count wherever
  they appear, comments included — cross-references between matched
  files must name the placement, not the func_XXXXXXXX symbol.
- Deferred with evidence noted: the LIBETC VMODE getters (SetVideoMode/
  GetVideoMode in mainmenu_jp) are one-load C matches once their backing
  global (D_800B4EC4) has a curated, signature-DB-backed name — the
  pair proves the semantics, the canonical SDK name does not exist in
  curated yet.

**2026-10-13 (later) — GsGetActiveBuff matched in C across all eight
targets; the linker auto-define pass now resolves curated names.**
- The 16-byte / one-data-ref shape topping the rank list in every target
  is LIBGS's GsGetActiveBuff (GS_002.OBJ member .text+0x0, extent 0x10;
  already curated everywhere). Psy-Q 3.3 sig-db evidence: the member's
  signature bytes match retail exactly (lui/lh on the backing static,
  jr $ra + nop), and the OBJ's own bss carries PSDIDX (size 2) — the
  only halfword-sized static there. GsSetDrawBuffOffset re-reads the
  same index and scales it by two to pick a slot in a two-entry offset
  table, confirming index semantics; curated as PSDIDX per target with
  the full evidence block under mainmenu_jp.
- Placement fact worth keeping: these Psy-Q library statics sit in the
  EXE's bss, beyond the yaml's payload coverage (mainmenu_jp PSDIDX at
  0x80194E34 vs payload end 0x800CA800), so no dlabel renders and the
  C resolves them extern. build.sh's two-pass auto-define previously
  only handled address-encoded spellings (D_XXXXXXXX / func_XXXXXXXX /
  .LXXXXXXXX); it now falls back to the committed per-target symbols
  file for real-named symbols — the same principle (the address is the
  retail value), just spelled out in the table instead of the symbol.
- matched 101 -> 109 (progress TOTAL 13789); ratchets 365/0; screens 0
  DATA / 0 SUSPECT on all eight targets.
- Hygiene: the VMODE commit had swept in 12 auto-generated splat stubs
  under nested nonmatchings/ paths (extract ran after the flip there);
  removed and the pattern is git-ignored — extract-after-flip noise no
  longer lands in the tree.

## 2026-10-13 later — memclr + the EMULIB common-block discovery

- memclr matched in C, all eight targets (commit after the INTR trio):
  the rows already existed as sdk-marked asm rows everywhere, the body
  references no statics, so it was a pure flip + write + verify. Source
  shape matters and is documented in each unit: the guard-free countdown
  for-loop (`for (i = len - 1; i != -1; i--) { *p = 0; p++; }`) is what
  makes GCC 2.6.3 reproduce the retail body — loop rotation rewrites the
  entry test into `beqz $a1` with the len-1 init in the delay slot, the
  -1 sentinel lands in $v1 for the bottom `bne`, and the frame stays at
  the retail 8 bytes. A guarded do-while (test `--i != -1`) produces the
  same loop frameless (missing the sp dance); an up-counting for-loop
  produces `blez` + `slt` instead of the sentinel. Each target carries
  three byte-identical memclr copies (INTR / INTR_VB / INTR_DMA members
  of the same source); the curated `memclr` copy is matched, the other
  two stay func_-named asm. matched 152 -> 160, TOTAL 13822.
- GsSetDrawBuffOffset evidence pass (writers-first, banked):
  - The EMULIB.C family is THIRTEEN archive members (GS_001..GS_013),
    each defining one function plus the SAME static set: PSDOFSX,
    PSDOFSY, CLIP2, PSDBASEX, PSDBASEY, GsDSTACK, POSITION, PSDIDX,
    PSDCNT, GsDRAWENV, GsDISPENV, PSDGPU, GsORGOFSX, GsORGOFSY (GS_001
    adds GsInitGraph2, GS_004 GsSetOffset, GS_005 GsSetClip, GS_006
    GsSetClip2D, GS_010 GsSwapDispBuff, GS_012 GsSetClip2, GS_013
    GsSetOrign). The statics appear in every member's symbol directory
    -> they are COMMON symbols (tentative definitions merged by the
    linker into one bss instance). This explains why no per-member bss
    layout exists: the layout is the whole-EXE link order of the merged
    commons, scattered across several bss regions.
  - mainmenu_jp GsSetDrawBuffOffset (0x8007F1D4, extent 0x11c) touches:
    D_80194E3C (lh; the EMULIB mode flag; writers exist in 4 files -
    the earlier "never written" guess was wrong), PSDIDX (lh x2,
    curated), D_80189224 + D_80189226 (halves of a word; lh/lhu/sh
    across 3 files), D_8014A3A4 + D_8014A3A8 (lhu reads here; sh
    writers elsewhere - the two per-buffer offset slots), D_8018DAA4 +
    D_8018DAA6 (word written by halves: sh), D_8018DB14 + D_8018DB18
    (lh + sh - read-modify-write pair). Callees: func_800604E0 (jal,
    path A) + tail j to D_80072DB8; func_80062FCC (jal, path B).

**2026-10-13 (later still) — EMULIB attribution COMPLETE (cron-20261013-1126);
all statics named; callee anomaly discovered.**

- Tooling (repo-external, /home/z/my-project/scripts/): `emulib_place.py`
  (sig-place the GS_0xx members in a baseline, then decode every hi/lo
  pair's concrete address from the retail bytes), `mjp_dis.py`
  (standalone mainmenu_jp disassembler), `gsdb_sig_probe.py` (sig probe
  at an address across ALL sig-db versions), `xsearch.py` (cross-target
  byte search with per-target vma bases). Mapping gotcha baked into all
  of them: splat rom offsets INCLUDE the 0x800-byte EXE header, so
  file_off = vma - 0x8001F800 directly for the mainmenu/g3 family —
  skipping the header a second time reads 0x800 too far (cost half a
  session before caught).
- Member placements in mainmenu_jp (3.3 sig-db, full-member sig match):
  GS_001 GsInitGraph @ 0x8006D064 (0x62c), GS_002 @ 0x8007F1C4
  (the curated GsGetActiveBuff+GsSetDrawBuffOffset rows), GS_010
  GsSwapDispBuff @ 0x8007F99C (0xf4). GS_004/005/006/012 have NO
  placements (dead-linked or sig drift); GS_013 GsSetOrign's 24-byte
  wildcard-heavy sig matches twice inside game code — both false
  positives (they store args 8 bytes apart to 0x800C9C0C/14-class
  bss, not to adjacent halves).
- STATIC ATTRIBUTION (all evidence-backed, 2.60-consistent — the
  decisive fact: in Psy-Q 2.60's LIBGS every member declares the SAME
  11 commons, and GsORGOFSX/GsORGOFSY/PSDCNT DO NOT EXIST yet — they
  first appear in 3.30. So the 2-byte flag can only be PSDGPU and the
  DB14/18 pair can only be PSDOFSX/PSDOFSY):
  - PSDIDX = 0x80194E34 (already curated; re-confirmed: GsInitGraph
    zeroes it, GsSwapDispBuff flips it).
  - PSDGPU = 0x80194E3C (2 B): the only other 2-byte common; written
    by GsInitGraph2 from its mode arg (sh a2) and valiable_init; read
    by GsSetDrawBuffOffset as the path selector (beqz -> path B).
  - PSDCNT = 0x80194E30 (4 B, 3.3 name; incremented by GsSwapDispBuff
    with the is-zero -> a0=1 else a0=v1 dance). Not needed by the
    match; noted for the map.
  - POSITION = 0x80189224 (offx) / 0x80189226 (offy), _GsPOSITION
    {short offx, offy}: zeroed by valiable_init; read lhu in path A,
    lh in path B of GsSetDrawBuffOffset.
  - PSDBASEX[2] = 0x8014A3A4, PSDBASEY[2] = 0x8014A3A8: read by
    GsInitGraph and GsSwapDispBuff (lhu, indexed by PSDIDX*2 bytes);
    "double buffer base" per LIBGS.H.
  - GsDRAWENV = 0x8018DA9C, 92 bytes = the LIBGPU.H DRAWENV exactly:
    clip@+0 (8), ofs[2]@+8 (DAA4/A6 - path A writes the sums here),
    tw@+0xC, tpage@+0x14, dtd/dfe/isbg@+0x16-18, r0g0b0@+0x19-1B,
    DR_ENV@+0x1C. valiable_init zeroes DAA4..DAB4 (everything after
    clip) - the zero range is the struct proof.
  - GsDISPENV = 0x8018DAF8, 20 bytes (abuts GsDRAWENV's end exactly):
    disp@+0, screen@+8, isinter/isrgb24/pad@+0x10-13; GsSwapDispBuff
    stores PSDBASE[PSDIDX] into disp.x/y; valiable_init zeroes
    through +0x12.
  - PSDOFSX = 0x8018DB14, PSDOFSY = 0x8018DB18 (4 B words, ALL
    accesses are sh to the low halves): zeroed by gte_init and path A;
    stored (sh) with the computed offsets by path B after its
    func_80062FCC(X,Y) call; read (lh x2) by func_80070998.
- GsSetDrawBuffOffset semantics now fully decoded. Path A (PSDGPU != 0,
  lhu loads): GsDRAWENV.ofs[0/1] = POSITION.offx/offy + PSDBASEX/Y
  [PSDIDX]; PSDOFSX/Y = 0; func_800604E0(&GsDRAWENV); tail j
  0x80072DB8. Path B (PSDGPU == 0, lh loads): X = POSITION.offx +
  PSDBASEX[1-PSDIDX], Y = POSITION.offy + PSDBASEY[1-PSDIDX];
  func_80062FCC(X, Y); PSDOFSX = X; PSDOFSY = Y (sh). gte_init calls
  func_80062F38(0,0,0) then func_80062FCC(0,0) then zeroes PSDOFSX/Y.
- CALLEE ANOMALY (blocks the C match, new project-level finding): all
  three callee targets are MIDDLE-of-function entries, not function
  starts. func_800604E0 is a dlabel inside data row data_80060368
  (real code mis-typed data); func_80062FCC lands inside func_80062B04
  (frame 0x38) at +0x4C8 - its first words store v0 to 0xf6e($gp) and
  its "epilogue" restores ra from 0x30(sp), which is outside
  GsSetDrawBuffOffset's 0x20 frame; the tail target 0x80072DB8 is the
  loop-setup of a 0x88-frame function whose epilogue restores
  0x84(sp). Cross-target byte search: neither callee's bytes exist in
  any other baseline (not even mainmenu_eu); no sig-db member matches
  them in ANY version (20162 sigs probed). gte_init and func_80062B04
  have ZERO callers in the scan's current view. Working hypothesis:
  PSYLINK placed continuation/shared-tail code overlapping larger
  functions (cluster entries mid-body), and the paths through them are
  dead at runtime (the 0x88-frame epilogue restore would read garbage
  ra). Next session: determine whether path A/B are live (who writes
  PSDGPU nonzero, who calls gte_init) - if the jal/j targets are dead,
  the C match still needs them as curated-named callees, and the
  open question becomes how GCC 2.6.3 emitted a frame-unpopped tail j
  (sibcall with shared frame? PSYLINK relocation?) - check the 2.60
  sig-db GS_002 sig's tail-j wildcard and compare against other
  targets' GsSetDrawBuffOffset rows before writing any C.
- The ratchet constraint (no D_/func_ tokens in src/) means the match
  needs curated names for: PSDGPU, POSITION, PSDBASEX, PSDBASEY,
  GsDRAWENV (+ RECT/DRAWENV type shims - check how src/ handles struct
  types today), PSDOFSX, PSDOFSY, and the three callees. POSITION/
  PSDBASEX/PSDBASEY/GsDRAWENV have canonical SDK names; PSDGPU/
  PSDOFSX/PSDOFSY are 2.60-commons names (sig-db-backed); the callees
  have no names yet (role-descriptive per the intr_trap_flag
  precedent, or better once the anomaly is understood).

**2026-10-13 (evening) - INTR tail assessment complete (cron-20261013-1241);
the callee anomaly is SYSTEMIC; stopIntr probe banks a new codegen
question.**

- Full callee/static map of the five INTR tail members in g3_eu
  (startIntr 0xdc / trapIntr 0x1e8 / setIntr 0x154 / stopIntr 0xb0 /
  restartIntr 0x88). EVERY callee lands outside attributed code:
  - func_8004A2CC, .L8004A480, .L8004A56C, .L8004A72C, alabels
    0x8004A740/76C/77C are all mid-body entries inside the mis-carved
    0x7fc mega-function func_8004A02C (>=8 cluster entries the INTR
    members jal/j into).
  - func_8004AA24/AD44/ADF4/AE14/AE64/AE74/AE94/AEB4 (and
    func_80047C54 for trapIntr) are dlabels inside DATA rows
    (data_8004A828 size 0x1ca4, data_8004712C size 0x1c98).
    Disassembly confirms real code: coherent instruction streams,
    valid jal chains into 0x800300bc, structured s0-relative state
    access (e.g. 0x8004AD44 reads the INTR state fields at
    +0x10/+0x12/+0x14/+0x30, fills +0x78..+0x80). Same finding as
    GsSetDrawBuffOffset's func_800604E0: the scanner mis-types whole
    blocks of the interrupt/DMA machinery as data.
- stopIntr probe match attempted (all mechanics proven end to end):
  7 curated names (intr_active_flag 0x80096C08, intr_saved_mask
  0x80096C3A, intr_saved_dicr 0x80096C3C, intr_imask_ptr 0x80097C94,
  intr_dicr_ptr 0x80097C9C, callees intr_stop_begin/intr_stop_commit),
  scan weave + suffix repair, yaml flip, C write, link through the
  auto-define pass - the build linked FIRST TRY with cluster-entry
  callees resolving from the symbols file into a data row. The C shape
  did not converge in session: retail pins &intr_active_flag (a
  2-instruction lui/addiu constant) in s0 across BOTH opaque calls
  (entry read via 0(s0), exit `move v0,s0; sh zero,0(v0)` serving the
  clear AND the return), while GCC 2.6.3 -O2 RE-MATERIALIZES the
  address after the last call and never allocates s0. Four source
  shapes tested (plain extern reads; volatile pointer local; register
  hint; pointer return type) - all four rematerialize identically.
  Probe reverted; tree back to GREEN; the curated attribution stays.
- The s0-pin question generalizes: any INTR-tail C (and the
  GsSetDrawBuffOffset match) has values live across opaque calls.
  Next shape ideas: the address carried in a pointer the compiler
  cannot prove constant at -O2 (e.g. read from a static pointer slot
  whose initializer the linker provides), a struct-typed extern whose
  member accesses span the calls, or -fcaller-saves interactions.
  Also un-proven: restartIntr's tail `j .L8004A72C` (mid-body
  continuation into func_8004A718's body) needs a GCC sibcall-shaped
  tail with the frame NOT popped - how 2.6.3 emits that at all is
  still open (same question as the GsSetDrawBuffOffset tail).
- stopIntr statics semantics banked (evidence in the curated block):
  active flag halfword at the state base +0 (gate; startIntr/restart
  set 1, stopIntr clears), intr_trap_flag is +0x2; saved mask
  (+0x32) and saved dicr word (+0x34) are the stopIntr-save /
  restartIntr-restore pair; intr_imask_ptr receives the volatile
  re-read of the zeroed mask (I_MASK semantics); intr_dicr_ptr's
  target gets AND 0x77777777 (DMA DICR per-channel + master enable
  clear). Initial retail values of all slots are arbitrary linker
  leftovers (the game never calls this subsystem).
- Cross-target scope for the eventual rollout: the INTR member is
  sig-placed only in g3_eu (sdk_members.txt); other targets carry the
  INTR_VB/INTR_DMA members (already matched where applicable). The
  tail members may still exist in other EXEs unattributed - a
  byte-fingerprint pass (0x77777777 / 0x33333333 ori pairs are
  address-free and target-independent) will locate them when the C
  shape converges.

**2026-10-14 (early) - restartIntr attributed everywhere + restored to
asm rows in all 8 targets; the sibcall tail question is CLOSED
(negative, probe-proven); trapIntr inherits the conclusion
(cron-20261013-1626).**

- Byte fingerprint (scripts/restartintr_fp.py, ALL PASS): the g3_eu
  restartIntr body's 34-slot masked word template (opcodes+registers
  kept; address immediates and jal/j indexes zeroed; branch
  displacements kept) matches ALL EIGHT targets exactly at
  stopIntr + 0xb0 - uniform delta, including mainmenu_jp (an earlier
  read had its stopIntr base off by 0x100; corrected against the
  curated stopIntr entries). Extracted statics equal the curated
  intr_* addresses in every target and satisfy saved_mask=flag+0x32,
  saved_dicr=flag+0x34, dicr=mask+4. Member identified as sig-db
  INTR.OBJ .text+0x660 (extent 0x88, ends right before memclr).
- THE SIBCALL QUESTION IS CLOSED - NEGATIVE. Probe matrix
  (scripts/restartintr/, 5 shapes x {-O0,-O1,-O2,-O3} through the
  probe harness): `return tailfn();`, noreturn-attributed call,
  plain void call, volatile-void call, and the r6 control
  (`return (long)p;`) ALL emit `jal <tail>` + a full epilogue. GCC
  2.6.3 MIPS has no sibcall and does not elide epilogues behind
  opaque calls. The r6 control reproduces the retail body AND the
  shared-epilogue jump FORM byte-for-byte (`j <local shared
  epilogue>; move $v0,$s0` with the return-0 block falling through)
  - the ONLY divergence is the jump TARGET (GCC: its own local
  epilogue; retail: an external dispatcher-cluster address). Best
  explanation: the original SDK source closed restartIntr with a
  hand-written asm tail carrying an ra-clobber bug (the tail block's
  `jr $ra` returns into restartIntr's own jump instruction - dead
  code in retail, which never calls this subsystem). CONSEQUENCE:
  restartIntr stays an assembly row; trapIntr closes with the same
  form (`j` + frame not popped) so its C attempt is skipped too;
  the GsSetDrawBuffOffset tail question loses its "maybe 2.6.3
  sibcall" branch.
- Rollout (scripts/restartintr_rollout.py, 8/8 verify GREEN first
  try each): curated 4 names per target (restartIntr,
  intr_restart_begin, intr_restart_commit, intr_restart_tail; full
  evidence block under mainmenu_jp) -> collision census (clear:
  no cross-target row-label reuse - the SetIntrMask/stopIntr lesson
  does not bite) -> hand-carve: the covering data row splits into
  `[asm, func_<ri>] # 0x88 sdk` + a data remainder row (sces's 0x49c
  row leaves a 0x414 remainder; the others 0x38/0x3c) -> make scan
  (suffix churn 7-11 rows/target, restored) -> extract -> stale data
  .s removed -> verify. g3_eu was already an exact asm row: curated
  names only.
- Rendering evidence: with the curated data-type symbols present,
  spimdisasm renders the tail `j intr_restart_tail` BY NAME
  (g3org_eu/slps - the two targets whose tail lives inside a data
  row; the symbol resolves through the build's symbols-file
  auto-define at link). begin/commit render as address-encoded
  labels; spimdisasm created dlabel/alabel islands at the
  newly-referenced addresses (union-preserving re-derivations,
  accepted as scanned). This closes the "cross-row j into a data
  row" mechanism for future members: curate the name, let the
  auto-define resolve it.
- Gates: matched 168 (unchanged - asm row, no C unit); progress
  TOTAL 13830; ratchets 365/0; screens 0 DATA / 0 SUSPECT on all 8;
  8/8 verify GREEN.
- Next queue: (1) startIntr (0xdc) - its body is C-shaped (normal
  jal tail, proven by stopIntr/restartIntr idioms) BUT it jal's into
  cluster entries whose names are now curated; the s0-pin +
  shared-tail shapes are all proven. (2) setIntr (0x154, normal
  return tail) - bigger but same toolkit. (3) trapIntr (0x1e8) -
  branch-heavy AND carries the asm-only tail; keep asm or hybrid.
  (4) memclr as C in the 7 targets where it is still inside data
  remainder rows (g3_eu has it as a c row; the restartIntr splits
  exposed the member start at ri+0x88 everywhere).

## 2026-10-14 later - startIntr C-flip assessment: one allocation diff short

Probe session (scripts/startintr/, the stopintr_probe.sh harness + a new
-G0/-sdk-aspsx-aware comparator startintr_cmp2.py). The g3_eu retail body
(0x800506E0, 0xdc) is fully decoded and every shape below was probed
byte-level. Result: the C flip is ONE compiler-allocation decision short
and stays asm for now (restartIntr precedent).

Body (55 words): gate on intr_active_flag (early exit 0), the three
volatile port slots (ip/mp/dp read in that order; zero the mask port,
write the re-read through ip, 0x33333333 through dp), aux1(p, 0x41a)
with the 0x41a in the call delay slot, aux2(p+0x1c) with the arg computed
INTO a0 IN the delay slot, `if (ret != 0) aux3()` (the retail beqz SKIPS
aux3 - the condition is != 0, not == 0), then the pin OVERWRITE to
flag+0x3c (2-insn lui+addiu), restart_begin(pin-4), the self-pointer
install *(long*)pin = pin+0xfdc sunk into restart_begin's delay slot,
the gate store 1 through pin-0x3c in aux4's delay slot, aux4ret ->
intr_start_tab+0x14 and aux5ret -> tab+4 sunk into the NEXT calls' delay
slots (tab loaded twice, after each call, v1/a0), aux6, commit, and the
return value computed IN commit's delay slot as addiu s0,s0,-0x3c then
move v0,s0.

Shape laws established this session (all probed):
1. -fno-cse-skip-blocks is the structural key: it stops GCC 2.6.3's CSE
   from merging the aux2 arg (flag+0x38) with the restart arg
   (newpin-4) across the conditional aux3 block. Without it the merged
   pseudo forces frame 0x20, a second callee-saved save, move-based arg
   setup, and a 1-insn addiu reassignment. With it: frame 0x18, the pin
   in s0, addiu a0,s0,0x38 directly in aux2's delay slot, the beqz
   shape, and a 2-insn la reassignment - all retail.
2. The aux2-arg CSE entry dies only if the flag flushes the block; the
   memory barrier `__asm__ __volatile__("" ::: "memory")` does NOT
   flush address constants, and neither calls nor the pin re-set do.
3. Symbol-boundary trick (p8/p9): introduce a second unsized-array view
   intr_state_page at base+0x3c (evidence: the retail body installs
   base+0x1018 into that word and passes base+0x38 = page-4 to the
   restart cluster). Two different symbols make the aux2-arg/restart-arg
   merge IMPOSSIBLE even without the flag (symbol differences are
   unknown at compile time), and the reassignment `p = &intr_state_page[0]`
   re-materializes as a fresh 2-insn la (array decay defeats REG_EQUIV
   remat; a scalar symbol address does NOT - p7 proved the scalar form
   gets remat-killed into per-use las).
4. GCC path asymmetry: VALUE uses of a symbol-relative constant take the
   CHEAPEST form (register-relative off the live pin - 1 insn); STORE
   addresses take the CONSTANT form (lui $at + store - 2 insns) whenever
   CSE can resolve the address to a symbol-relative constant. That is
   why the return comes out addiu v0,s0,-0x3c but the gate store comes
   out sh v0,-0x3c($at) from the same expression. The store only stays
   register-relative when its address is CSE-opaque (derived from a
   pseudo whose CSE entry was flushed pre-branch - the p5/p9 dead-old-pin
   trick, where the gate store goes through the dead first pin).
5. Allocator law (the blocker): with more than one callee-saved
   candidate, GCC 2.6.3 gives s0 to the LATER-born pseudo (post-branch
   or multi-set) and s1 to the pre-branch single-set pin; declaration
   order is irrelevant (p6a/p9b). The retail compiler shares s0 between
   the dead first pin and the new pin (frame 0x18, one sw s0). Every
   source shape tested (single reassigned local; two locals; two locals
   + page decay; both declaration orders) lands the first pin in s1 -
   the only remaining diff is this frame/save/registration cascade.

p9 (two pins + page decay + the flag) matches retail EXACTLY except:
sw s1/frame 0x20 vs sw-less/frame 0x18, and every s0 -> s1 on the first
pin (gate read, aux1 arg, aux2 arg, gate store base). p8 (single pin +
page decay, no flag) additionally differs on the gate store form and the
return placement. Next-session candidates, in order: (a) find a source
shape that grows the FIRST pin's conflict clique past the second pin's
(extra entry-block live values are bounded by the retail insn count, so
this is likely closed); (b) a per-unit cc1 flag mechanism (cc-post-style
marker passing -fno-cse-skip-blocks) + the p8 shape, then re-probe the
gate store/return with the flag's CSE table state; (c) keep asm and
spend the time on setIntr/trapIntr fingerprints. The probe corpus
(p1-p9b) stays in scripts/startintr/ for whichever lane picks this up.

## 2026-10-14 later - setIntr fingerprint: present in all 8, two revisions

scripts/setintr_fp.py (member .text+0x45c, extent 0x154, predicted
stopIntr-0x154). Fingerprinting notes:
- The masked-word template needed `j` (op 0x02) masked alongside jal:
  setIntr carries a bare `j` to the dispatcher cluster entry whose
  target is absolute per build (startIntr had only jals, which is why
  the startIntr fingerprint could skip it; restartIntr's fp already
  masked j).
- EU-revision five (sces_00269, mainmenu_eu, g3_jp, g3_eu, g3org_eu):
  the FULL 0x55-word masked template matches UNIQUELY at stopIntr-0x154
  in each - same instruction stream modulo addressing.
- JP-revision three (slps_00270, mainmenu_jp, g3org_jp): setIntr sits at
  stopIntr-0x284 (the same 0x130 revision delta the startIntr region
  showed); the first 53 words (0xd4) are masked-identical to the EU
  template, then the ENTIRE tail (words 53-84) diverges - the EU tail is
  the ori 4/5/6 channel ladder calling the dispatcher entry, the JP tail
  is a different stream. The older revision's member is genuinely
  shorter/different in its dispatch tail.
- Consequence for the C flip: one C source can cover the EU-revision
  five only; the JP-revision three need either their own C shape or
  attribution-only asm rows (the restartIntr precedent). The g3_eu body
  decodes as: setIntr(chan 0..n, on_off) - s1=chan, s2=on_off; the state
  word array at base+0x10 (s4 = state[chan]), the same-value early-out,
  the mask-port read/clear, the per-channel bit set-or-clear through
  base+0x2c, the nor path for off, the shared mask halfword at
  base+0x2c-0x2c... full decode deferred to the flip session.

## 2026-10-14 late - setIntr full decode + C-flip probe round 1 (p1-p4)

scripts/setintr/ (repo-side corpus: setintr_cmp.py + p1-p4 + sib.c).
g3_eu setIntr (0x800509A4, 0x154) fully decoded. Semantics: old =
cb_slots[chan] (word slots at 0x80096C0C = intr_active_flag+4); early-out
`on_off == old` and `!*(u16*)(base-4)` both `return old` (move v0,s4 in
the branch delay slots); mp = intr_mask_ptr slot (0x80097C98); cur = *mp
(lhu); *mp = 0 (clear I_MASK); newm = cur (andi s3 in the beqz delay
slot, feeds both paths). ON path: bit = 1<<chan; slots[chan] = on_off;
shadow (base+0x2c) |= bit via a1-relative lhu/or, then BARE
`j 0x8004A56C` with the shadow store in the delay slot (retail
a4a2002c at +0x8c). OFF path: bit = ~(1<<chan); slots[chan] = 0; shadow
re-read ABSOLUTELY (lui v1 + lhu 0x6c38(v1)); newm &= bit; shadow &=
bit; absolute sh via $at; the chan 0/4/5/6 event ladder (chan 0:
z=(on_off==0) into s0, jal 0x8004ADF4(z), jal 0x8004AE74(3, z); chans
4/5/6: jal 0x8004AE74(0/1/2, on_off==0) with sltiu in each jal delay
slot); final *mp = newm through a re-read slot; return old. setIntr has
NO callers in g3_eu (dead library code, stopIntr precedent) - matching
is byte-level only. The three code targets are unattributed:
0x8004A56C is a .L mid-body entry inside func_8004A02C's cluster (the
jr-delay-slot addiu of the func_8004A560 epilogue pair, setIntr-only
reference), 0x8004ADF4/0x8004AE74 are real code inside data_8004A828
(same mis-typed-data island as intr_stop_begin/commit).

Probe findings (p1-p4, all 85/85 words with structure aligned):
- GCC 2.6.3 has NO sibcall: `return f(x)` compiles jal+epilogue
  (scripts/setintr/sib.c). The retail bare-j tail needs basic asm.
- The tail IS expressible: `__asm__(".set\tnoreorder");
  __asm__("j intr_wakeup"); <shadow store>; __asm__(".set\treorder");`
  - maspsx only skips the delay-slot nop when is_reorder is False, and
  its `.set` matcher requires a TAB (".set\tnoreorder"); a space
  silently passes through and the nop comes back (p2 vs p4).
- OPEN BLOCKER 1 (prologue): retail shifts BOTH args in the entry parm
  block (sw s1/move s1/sw s2/move s2) and materializes the slots base
  into a1 (lui/addiu 0x80096C0C) before the sll/addu; every probe shape
  (ANSI + K&R definition + declaration-initializer) shifts only s1
  early, defers `move s2, a1` to first use, and lands the base pseudo
  in v1. Working theory: GCC shifts an arg early only when the arg reg
  is about to be clobbered - retail's base went to a1 (clobbering the
  on_off arg reg) which FORCED the early s2 shift; our probes allocate
  the base to v1 (first free allocatable reg) so a1 is never clobbered
  and the shift stays late. Need a source shape (or allocation steer)
  that puts the base in a1.
- OPEN BLOCKER 2 (addressing policy): GCC 2.6.3-psx emits symbol+off
  forms (lhu $2,intr_cb_slots-4) for extern-base accesses; maspsx
  passes them through unchanged; GNU as expands dest-based (lui $2;
  lhu $2,%lo($2)) or $at-based (stores) - while retail uses
  REGISTER-relative displacement on the on-path (lhu v0,-4(a1),
  lhu v0,0x2c(a1), sh v0,0x2c(a1)) and ABSOLUTE on the off-path.
  The p4 tail store expanded to `lui at; sh v1,0x2c(at)` which puts
  the LUI in the j delay slot (the store would never execute). Either
  maspsx needs an aspsx-style sym+off -> tracked-base-register
  conversion, or the C needs an opaque base (volatile local has stack
  traffic; not yet probed). The off-path absolute forms already match
  after masking (separate intr_mask_shadow extern + volatile casts
  also correctly stops the scheduler hoisting the shadow load above
  the slots[chan] = 0 store - p1 evidence).
- Next: steer the base into a1 (candidates: anchor the arithmetic on
  intr_active_flag with a two-step decay GCC refuses to fold; probe a
  `base` local whose only def is an array decay + offset in separate
  statements; check what the aspsx assembler's sym+off expansion
  policy implies for the whole pipeline). Then re-run p-series; on
  convergence do the g3_eu flip (curated: intr_cb_slots = flag+4,
  intr_wakeup = 0x8004A56C, func_8004ADF4/func_8004AE74 per target),
  then the EU five (sces/mainmenu_eu/g3_jp/g3org_eu rows sit inside
  data segments - split like the startIntr carve), JP three keep asm
  (their tails diverge past word 53).

## 2026-10-14 late+1 - setIntr round 2: the aspsx la-tracking model, maspsx pass landed

Probe corpus q1-q14 (scripts/setintr/, setintr_cmp.py harness). The
round-1 blockers both dissolved into ONE mechanism:

ASPSX LA-TRACKING (the retail expansion policy). Walking the retail
g3_eu stream against a "la-tracking assembler" model explains 8/8
forms: GCC emits ONE `la a1,intr_cb_slots` (for the elem addu) and
plain `sym+/-off` memory operands everywhere else; aspsx remembers the
la and rewrites later sym+/-off operands as off(a1). Flag read
`lhu v0,cb_slots-4` -> retail `lhu v0,-4(a1)` (+0x44); on-path shadow
read/store -> `lhu v0,0x2c(a1)` / `sh v0,0x2c(a1)` (+0x7c/+0x8c, the
tail store in the j delay slot); unla'd symbols (intr_mask_ptr,
intr_mask_shadow) expand dest-based (loads) / $at-based (stores) which
is exactly the retail off-path forms (+0x54/+0xa0/+0xb0). MASPSX now
implements this: opt-in pass, magic comment `# maspsx:la-track`
anywhere in the input; tracks `la reg,sym` per .ent (latest la wins),
rewrites load/store sym+/-off displacements through the tracked reg,
invalidates on register write (best-effort dest detection). Local
maspsx commit 611fa36; full upstream suite still 154 passed; inert
without the marker so all 8 targets' existing builds are unchanged.

CSE LIVE-RANGE TRUNCATION (why round 1's opaque-base shapes kept
breaking). GCC 2.6.3 CSE substitutes a foldable base's value into
base+/-const addresses, turning them into sym+off operands; the base
pseudo then has no further uses, its live range truncates at the last
necessary use, and GCC reuses its register (q10: base=v1, reused for
cur at +0x60, so the tracker is dead before the shadow read). Retail
only works because base lands in A1: GCC's scratch traffic (mp=v0,
cur=v1, bit/shadow on-path) never touches a1, so the la's track
survives from +0x14 to the tail store. THE REMAINING BLOCKER IS PURE
ALLOCATION: steer base -> a1 (q8 gives v1; ANSI vs K&R def irrelevant
q13; local decl order irrelevant so far). Once a1, the C is the q8
shape + `# maspsx:la-track` + off-path memory clobber - no opacity
needed, the store fold becomes the TRACKED rewrite.

PARM-BLOCK LAW (round 1 blocker 1, resolved). assign_parms emits the
eager entry block (sw s1/move s1/sw s2/move s2) ALWAYS; the final
scheduler then sinks independent parm moves to first use (p4's
deferred move s2,a1 was scheduler sinking, not lazy expansion). Any
inline asm before the sink path blocks it: a no-op `__asm__("")` at
stmt 1 pins both moves early (q8 = retail parm block +0x004..+0x010).
In the converged a1 shape the no-op asm becomes unnecessary: the la
writes a1, the move s2,a1 cannot sink past it (dependency), which is
why retail shows the eager block without any asm.

Other laws banked this round:
- Opaque-base family (q2/q4/q12): asm "=r"/"0" output or asm-emitted
  la DOES kill the CSE substitution (all accesses register-relative,
  tail store included) but the asm's entry-block operand ref promotes
  base above elem in the allocno sort -> base=a0, elem=a1 (retail is
  the exact swap). Opacity is therefore the WRONG lever; tracking is
  the right one.
- The stopIntr decay trick does NOT stop CSE substitution (q9): it
  only defeats the REG_EQUIV note (reload remat). stopIntr never faced
  substitution because all its accesses through p are offset 0.
- Off-path order: the shadow read hoists above slots[chan]=0 unless a
  `__asm__("" ::: "memory")` separates them (q4; volatile casts are
  NOT enough - q2/q8 evidence).
- +0x124 nop: the mp re-read pseudo's register decides the load-delay
  fill - re-read into v0 (retail) and the return move v0,s4 cannot
  enter the slot (nop stays); into v1 and the move fills it (one word
  short, q4). Follows from the base=a1 allocation cascade.

Next queue:
1. Steer base -> a1 with a foldable base. Candidate levers: make cur
   (or another overlapping scratch) sort before base by shaping its
   refs; give the elem pseudo more entry refs WITHOUT touching base;
   decomp-permuter grind on q8 with the 85-word masked scorer (the
   corpus + harness are permuter-ready). Then g3_eu flip (curated:
   intr_cb_slots/intr_wakeup/func_8004ADF4/func_8004AE74 + yaml flip +
   q8-shape C with the marker), then EU five carve, JP three stay asm.
2. startIntr C flip: reopen with the tracking pass available - the
   p8/p9b shapes' s1/s0 cascade may dissolve the same way (retail
   startIntr's pin may be a TRACKED la, not an allocation pin).
3. trapIntr fingerprint when its lane opens.
4. Walker rows stay under the zero-entry contract; coordinate with the
   walker-probe session first.
5. Runtime gate-family: still blocked (fresh-checked this session).

## 2026-10-14 (later): mainmenu_eu INTR_VB carve + setIntrVSync C match

The last incomplete INTR_VB target closed (cron-20261013-2356). The member
sat inside data_800684A0 (file 0x48CA0, 0x25c); byte-driven hand-carve, then
the standard flip. Commit 0e8efaa (attribution) + the match commit.

- The cron-20261013-2241 queue note assumed a 4-row carve (member + memclr
  at +0x100). BYTES FALSIFIED IT: mainmenu_eu's link places 0x130 bytes of
  genuine data at the canonical memclr position (+0x100 past setIntrVSync);
  the member's memclr copy sits 0x130 bytes LATER at 0x800686D0
  (byte-identical to the landed copies). Carve is 3 func rows + 0x130 data
  row + 1 func_-named memclr-copy row. Lesson: member-layout assumptions
  are per-link; check bytes first.
- VRAM-NAMING LAW (cost one failed verify): yaml row symbols are
  VRAM-derived (name = vram & 0xFFFFFF... i.e. file + 0x1F800 here), and
  build.sh decodes each object's rom FROM THE FILE NAME
  (rom = 0x800 + (name_vram - 0x80020000)). Naming a row from its file
  offset (func_80068ED0 for file 0x48ED0) silently produces an orphan
  section (.r_000496D0) that ld appends after the payload: image grows by
  the row size, the row's slot zeroes. Symptom signature: t_size + row
  extent, content at image end, zeros in place.
- setIntrVSync matched first try after the carve (same shape as the five
  landed targets). matched 173 -> 174; ratchets 365/0; screens 0/0.
- Remaining INTR_VB state: slps_00270/sces_00269 stay asm (boot-EXE
  reference-decode mystery, evidence banked in the worklog); all other 7
  targets now carry the C setIntrVSync.

## 2026-10-14 (later): GsSetDrawBuffOffset round-1 decode + probe assessment

Lane opened: the member is curated in all 8 targets (EMULIB .text+0x10,
extent 0x11c = 71 insns) but still asm. The stopIntr banked shapes
(array-decay pin, volatile slots, opaque base) were predicted to transfer;
this round proves most of them do and maps what is left. Probe harness
mirrors tools/cc.sh (cpp -> cc1 under qemu -> maspsx --expand-div ->
cc_post with cc-post marker grep) at scripts/gsdbo/ (repo-external), plus
a bare-symbol -> lui/%lo expansion normalizer so probe output diffs
against retail in the same form.

Structure (retail mainmenu_jp 0x8007F1D4):
- Guard `lh D_80194E3C` hoisted ABOVE the prologue; `beqz` carries the
  s0-save in its delay slot; frame 0x20 saves ra/s1/s0.
- Then-path (guard != 0): "u16 world". PSDIDX loaded once (v1), sll 1,
  table A read at T1 + idx (lhu), out pointer a0 = &D_8018DAA4 (full
  lui+addiu), clears D_8018DB18 then D_8018DB14, add + `sh 0(a0)`,
  table B same shape, `sh D_8018DAA6`, jal func_800604E0 with
  `addiu a0,a0,-8` sunk into the jal DELAY SLOT, then tail `j D_80072DB8`.
- Else-path (guard == 0): "s16 world". Two separate conditional
  increments (&T1 += 2 / &T2 += 2 when PSDIDX == 0 - inverted index),
  cond CSE'd into a1 across both bnez diamonds, sums = 32-bit addu of
  lh-loaded operands, jal func_80062FCC (arg2 move in the jal delay
  slot), stores D_8018DB14/DB18 (sh truncates), normal epilogue
  (GCC's own order - the keep-epilogue SDK convention applies).

Placement facts:
- All 10 referenced data symbols are bss BEYOND the yaml payload (same
  class as PSDIDX): D_80194E3C, PSDIDX, D_80189224/26, D_8014A3A4/A8,
  D_8018DAA4/A6, D_8018DB14/18. C needs externs; only PSDIDX is
  identified so far.
- Callees are cluster entries in mis-typed rows: func_800604E0 sits
  inside data row data_80060368 (0x274); func_80062FCC is a mid-entry
  inside asm blob func_80062B04 (0x82c); the tail target D_80072DB8 sits
  inside data row data_80072B20 (0x49c) and is mid-cluster code (no
  prologue, uses s0/s3/s6) - the INTR-tail "callees are cluster entries
  in mis-typed data" pattern again. A future carve round must name all
  three before the flip can land.

Laws proven this round (probe s01 -> s04):
- Sum-type law: else-path sums must be `long` locals. `short` sums make
  cc1 emit sll/sra sign-extension pairs around the addu (args promote)
  that retail does not have; retail passes raw 32-bit addu results and
  lets the sh stores truncate.
- Select-shape law: the inverted index must be if-statement increments
  (`p = T; if (PSDIDX == 0) p += 1;`), NOT pointer ternaries. A ternary
  makes cc1 re-materialize the constant &T+2 inside each arm; retail
  materializes the base once and increments it in the arm.
- Load-width law: the pair symbols and both tables are read lhu in the
  then-path but lh in the else-path - same addresses, two access types.
  The C needs unsigned pointer derefs in the then-path and the signed
  declarations in the else-path (one TU cannot declare both; casts
  through typed pointers are the lever).
- Opaque-base transfer: `__asm__("# ...\n\tla %0,D_8018DAA4" : "=r"(pout))`
  defeats constant folding and lands the out pointer in a0 EXACTLY as
  retail (full materialization before the clears, `sh 0(a0)` store, arg
  addiu sunk into the jal delay slot). The setIntr opaque-base law
  transfers; this time the allocno promotion direction is retail's own.
- Memory-clobber order law: `__asm__("" ::: "memory")` between the two
  out-pair stores forces retail's store order, but re-loads PSDIDX from
  memory for the second index. Fix: hoist `long idx = PSDIDX;` - a
  register local survives the clobber; retail keeps the single load.
- Guard/branch shape is already retail at s04: guard load above the
  prologue, beqz delay-slot s0 save, clears order DB18 -> DB14, else
  two-diamond with the cond CSE'd into one register, arg moves in delay
  slots.
- -O2 confirmed best for this member too (128 normalized diff lines vs
  137 at -O1, 141 at -O3; s01 baseline was ~160+).

Remaining gaps for round 2 (in probe-diff order):
1. sym+off at-factoring: cc1 folds %lo into the table load
   (`lhu v1,%lo(T1)($at)` with at = hi+idx); retail keeps the FULL base
   (`addiu at,at,%lo; addu at,at,idx; lhu 0(at)`). Same class as the
   setIntr round-2 "sym+off expansion policy" open blocker - a
   post-pass policy question, not a C-shape question.
2. Table-value register: retail keeps the table value in a1 (idx in v1);
   probe swaps them (idx a1, value v1). Allocation-level.
3. Else-path increment arms: cc1 re-materializes &T+2 constants in the
   arms instead of retail's bare `addiu v0,2` increment. Constant-
   propagation level; opaque-izing the base of p1/p2 is the candidate
   lever (costs allocation pressure).
4. Sum placement: probe computes the s1 sum inside the second bne's
   delay slot; retail sums before the branch and moves a0=s1 in the
   delay slot instead.
5. Tail: `j D_80072DB8` via the tab-form noreorder asm per the banked
   setIntr law (probe used it; sequence lands, needs the real carve of
   the target's identity first).
6. Cosmetic for cc_post: `addu reg,reg,-8` vs retail `addiu` negative
   imm; hex vs decimal stores (already-normalized forms).

Next queue for this lane:
1. Round 2 probes: opaque-ize p1/p2 bases (gap 3), sum placement (gap
   4), then re-measure; the at-factoring (gap 1) likely needs the
   maspsx/cc_post policy decision the setIntr lane also owes.
2. Carve round: name func_800604E0, func_80062FCC and the D_80072DB8
   cluster entry (byte-driven, like the INTR_VB carve), plus curated
   statics for any still-D_ bss the C must reference.
3. Then flip mainmenu_jp first, roll out with the byte-fingerprint
   method (0x11c extent, guard-lh prologue, the two-table shape are
   address-free identifiers).

## 2026-10-14 (later): GsSetDrawBuffOffset round-2 probes - else-path closed, at-factoring isolated

Probe rounds s05/s06 (scripts/gsdbo/, repo-external) on the round-1
shape. Real-chain cross-check: tools/cc.sh -S output diffs IDENTICALLY
to the probe chain (125 normalized lines both) - the harness is
faithful, every probe diff is a true toolchain divergence.

- ELSE-PATH SHAPE CLOSED (s05). Opaque la-bases for the two table
  pointers (the stopIntr/setIntr opaque mechanism) produce retail's
  increment arms: `addu v0,v0,2` instead of the per-arm constant
  re-materialization, register-relative `lh v0,0(v0)` loads, cond CSE'd
  into one register across both bnez diamonds, sums and arg moves in
  the right delay slots. The else-path is now shape-correct end to end;
  what remains there is register naming (retail reads D_80189224 into
  a0 and keeps sums in s1/s0; probe shifts one slot) and two
  micro-ordering nits (&T2 materialization landed in bne#1's delay
  slot; retail fills it with nop and materializes after the first lh).
- INTCAST NEGATIVE (s06). `*(u16 *)((long)T1 + (idx << 1))` does NOT
  block the %lo fold: GCC's mips legitimize_address re-splits
  symbol+offset+reg into hi-in-reg + %lo-in-load-offset. The probe
  output is byte-identical to s05's table blocks. Cast-through-integer
  is therefore NOT a lever for the at-factoring (but the negative is
  worth having banked - it rules out the cheapest candidate).
- AT-FACTORING ISOLATED. Retail: `lui at,%hi(T1); addiu at,at,%lo(T1);
  addu at,at,v1; lhu a1,0(at)`. cc1 (any shape tried): `lui at,%hi(T1);
  addu at,at,idx; lhu v1,%lo(T1)($at)`. Resistant to: pointer vars
  (s02), opaque bases (s03/s05 - only works under conditionals),
  intcast (s06). The two forms are instruction-count-identical, so the
  transform is mechanical as a POST-PASS rule:
  [lui $X,%hi(S); addu $X,$X,$Y; load $Z,%lo(S)($X)] ->
  [lui $X,%hi(S); addiu $X,$X,%lo(S); addu $X,$X,$Y; load $Z,0($X)].
  This is the same expansion-policy class as the setIntr lane's
  la-track maspsx pass (their local commit 611fa36 - NOT in this
  sandbox's clone, upstream mkst/maspsx is at e85ecb3). COORDINATION
  NOTE: do not implement a parallel refold pass in this sandbox - the
  policy belongs with the setIntr lane's maspsx work; propose the rule
  there (it may subsume into their tracker).
- IDX-REG SWAP remaining: retail keeps PSDIDX's shifted index in v1 and
  the table value in a1; probe swaps them (opaque-pout pins a0, the
  rest shifts one slot). Next lever is allocno-dump analysis (cc1 -da)
  rather than more shape blind probes.

Probe inventory: s01 structural, s02 pointer-vars, s03 opaque-pout,
s04 if-selects + long sums, s05 opaque table bases (BEST, 125 lines),
s06 intcast (negative). All at -O2 with -O1/-O3 spot checks.

Next queue for this lane:
1. cc1 -da allocno dump on s05 to steer the idx->v1 / value->a1
   allocation (then-path), and the two else-path micro-orders.
2. Coordinate the at-factoring refold rule with the setIntr lane's
   maspsx work before any policy lands.
3. The flip attempt waits for 1+2: the shape is close enough that
   verify diffs would be pure allocation/factoring - do not burn the
   yaml flip until those close.
4. Carve round (attribution, independent of 1-2): name
   func_800604E0 / func_80062FCC / the D_80072DB8 cluster entry.

## 2026-10-14 (later): GsSetDrawBuffOffset carve-prep - the three code addresses decoded (mainmenu_jp)

Byte-driven decode of the three non-row addresses the member touches
(baseline disassembly, word-at-a-time so data desyncs cannot hide):

- func_800604E0 (inside data row data_80060368, 0x178 into it): an
  8-INSTRUCTION STUB with no return - `move t0,zero; ori t1,zero,1;
  addiu a3,zero,-1; lui a1,0x800d; lh a1,-0x5f3c(a1); lhu v0,0x38(v1);
  nop; sh v0,0x3a(v1)` - then the stream degenerates into words whose
  opcodes (ldc1, ldc2, cache, swr-with-at, jalx) CANNOT occur in mips1
  GCC output. The callee region is a code fragment polluted by data:
  there is no whole function to carve here. The calling then-path is
  plausibly DEAD in this link (its guard D_80194E3C == 0 at runtime),
  which is consistent with a shipped library path whose callee tail
  never needed to link coherently. Implication for the flip: the C
  side needs only the stub address to resolve (curated-name-only or
  existing auto-name); no extent carve.
- func_80062FCC (mid-entry inside asm blob func_80062B04): genuine
  code - gp-relative halfword stores (0xf6e/0xf70($gp)), a conditional
  tail `j 0x8005a4f8` deeper into the blob, and a `lw ra,0x30($sp)`
  epilogue. A foreign mid-function splice sharing the enclosing
  function's frame: the g3_jp-splice class. Curated-name-only
  treatment; no row split.
- D_80072DB8 (inside data row data_80072B20, 0x298 into it): genuine,
  continuous mips1 - GsSort-style primitive copying (lwl/lwr/swl/swr
  8-byte struct moves over s0/s2/s3/s6, offset-table walks). A REAL
  cluster entry worth a proper carve later, but the row is 0x49c and
  the block's start/end boundaries need the full-row pass.

Carve-round verdict: NOTHING blocks the flip mechanically - the C
references resolve through existing auto-names + curated entries. The
carve round is now pure attribution quality (the D_80072DB8 cluster)
and rolls into the fingerprint/rollout phase rather than gating it.

## 2026-10-14 (later): GsSetDrawBuffOffset byte fingerprint - 8/8 uniform, imm-only diffs

Fingerprint pass over all 8 baselines (scripts/gsdbo_fingerprint.py,
repo-external): 0x11c words at each curated address, boot EXE load base
corrected to 0x80020000 from the PS-X header (0x18 field; both boots
share it, size 0x46800).

RESULT: prologue-ok in 8/8, and EVERY cross-target diff is an
address-immediate only (same opcode half, different %hi/%lo imm) -
mainmenu_jp is the zero-diff reference; mainmenu_eu 20 diff words,
g3_jp/g3_eu 37, g3org_jp/g3org_eu 33, slps_00270/sces_00269 37. Unlike
setIntrVSync there is NO JP/EU revision divergence: both revisions
carry the identical member. One C source serves all 8 targets; the
rollout after a mainmenu_jp match is the standard curated-addresses +
flip + verify flow with no per-region shape work.

## 2026-10-14 (later): GsSetDrawBuffOffset round-3 - else-path CLOSED, then-path allocno resistance mapped

Probe round 3 (scripts/gsdbo/, repo-external; variants s07-s18, all -O2,
cc1 2.6.3 + maspsx + cc_post via the gsdbo_probe.sh chain). Metric fix
first: gsdbo_norm.py now tab-proof (GCC emits tabs, the retail
spimdisasm asm spaces - the subu/beqz canonicalizers silently missed
every GCC line), operand-canonical (comma spacing, decimal->hex), and
sign-correct (-8 -> -0x8; "0x%x" % -8 yields "0x-8"). The old "125 diff
lines" was mostly formatting noise; the true semantic baseline is 55
(s05) and the honest metric table is s01=94 s02=78 s03=74 s04=54
s05=55 s06=61.

FALSE-DELTA CLASSES PROVEN WITH THE ACTUAL gas 2.31.1 (assembled and
objdumped): `addu/subu reg,reg,imm` assembles as `addiu` byte-identically
(2484fff8 for addu $a0,$a0,-8; 27bdffe0 for subu $sp,$sp,32), and
`j $ra` assembles as `jr $ra` (03e00008). The subu/addu-vs-addiu
prologue/epilogue "deltas" and the j-vs-jr epilogue delta are NOT
deltas; any future norm should fold them.

ELSE PATH CLOSED (s08, 37 diff lines, ALL remaining lines are the false
classes + the two post-pass items below). Four new laws, all probed:
1. RETAIL STATEMENT ORDER LAW: reordering the else body to the retail
   emission order (base A la, PSDIDX reload, first s16 load, if, *p1
   load, base B la, SUM1, second s16 load, if, *p2 load, SUM2) fixed
   THREE allocations at once that no decl-order/opacity steering could
   move: the first s16 load lands in $a0 (was $s1), the bnez#2 delay
   slot gets the a0=s1 arg move (was the sum), and the base-B la stops
   fighting for the delay slot.
2. SUM OPERAND-ORDER LAW: the addu encoding rs/rt follow the C operand
   order. Retail `addu $s1,$a0,$v0` (rs=loaded-D, rt=loaded-value)
   means `s1 = D + *p` - NOT `s1 += *p` (that emits addu s1,s1,v0,
   a different encoding). Same for sum#2.
3. LOAD-INTO-RESULT LAW: retail's second sum loads *p2 DIRECTLY into
   the result reg then adds (lh $s0,0x0($v1); addu $s0,$v0,$s0). The
   C shape is two statements: `s0 = *p2; s0 = d2 + s0;` - the
   single-expression shape puts the load in a temp reg instead.
4. VOLATILE-OPAQUE-LA LAW: a plain opaque la asm can be scheduled INTO
   a branch delay slot by GCC (it filled bnez#1's slot with the base-B
   la, retail keeps a nop there). `__asm__ __volatile__` pins it;
   emission position unchanged.

THEN-PATH ALLOCNO (idx->$a1/value->$v1 vs retail idx->$v1/value->$a1)
RESISTANCE MAPPED: nine source shapes tried (idx split into per-arm
variables, idx decl-first, idx load moved after the pout asm, value
through a temp local, A through a local, pout asm volatile, memory
barrier removed, u16 extern decls replacing the cast-through-pointer
loads, dummy asm-input mentions) - NONE moved it. GCC 2.6.3 internals
decoded from the -da dumps (cpp -> cc1 -da works; dumps land in CWD):
the then/else idx pseudos are LOCAL qtys assigned by local-alloc
(already hard regs in the .greg dump, reg/v), NOT global allocnos; the
greg dump's "preferences: 5/4" entries belong to the multi-block
pseudos (s1/s0/pout class) and come from set_preference - copies
between hard reg and pseudo (global.c); the u16 cast loads decompose
into HImode pseudo + zero_extend insn pairs that grab $2/$3 ahead of
the idx chain. The qty pri formula (log2(n_refs)*n_refs*size/
(death-birth), DESC, ties by qty number, copy-suggested qtys first)
could not be reconciled with the observed order from the source alone -
the remaining lever is a qty-table instrumentation build of cc1 or a
bisection over synthetic microblocks; parked as its own session.

POST-PASS ITEMS CONFIRMED (blockers for the flip, coordination lane):
- At-factoring x2 (lui/addiu/addu vs lui/addu+%lo): unchanged, belongs
  with the setIntr lane's maspsx expansion-policy work.
- Dead join: cc1 emits `nop; j $Ljoin; nop` after the then-path's
  inline-asm tail (the CFG edge survives basic asm). __builtin_unreachable
  does NOT exist in 2.6.3 (compiles to a jal call - probed); a noreturn
  call emits jal (wrong opcode vs retail's j); goto/return shapes
  duplicate the epilogue. The retail member has NO join after the tail,
  so either its source ended the block in a way 2.6.3 cannot express
  from C, or the retail build post-processed it. Elision as a
  marker-gated cc_post rule is the candidate; left for coordination
  with the setIntr lane per the standing do-not-parallel-policy rule.

Probe inventory banked in scripts/gsdbo/: s07 (else order), s08
(else fix = s07 + volatile la + two-statement sum2, BEST at 37), s09
(idx split), s10-s14 (single-lever shapes), s15-s17 (dummy-mention
steering, moves regs into reload instead - negative), s18 (u16
externs, negative). sweep_then.sh runs a variant list and reports
psd/val1 regs + diff count.

## 2026-10-14 (later): GsSetDrawBuffOffset round-4 - then-path CLOSED at source level via .lreg pri arithmetic + retail statement order

The instrumented-cc1 lever was not needed: `cc1 -da` on s08 already
emits `.lreg` (local-alloc's own dump; in 2.6.3 the -a set is
combine/cse/cse2/dbr/flow/greg/jump/jump2/loop/lreg/rtl/sched/sched2
- local-alloc's dump is `.lreg`, named `<input>.i.lreg`). The dump
lists per-qty n_refs/span/size, the live-at-start sets, and the final
`;; Register N in M` decision lines - the pri formula from round 3
became checkable ARITHMETIC instead of source reconstruction.

MECHANISM DECODED (s08 then block, from s08da.i.lreg): the then-path
competition is between the idx*2 pseudo (reg 89, ashift of the PSDIDX
reg/v pseudo, SImode, n_refs=4) and the value1 pseudo (reg 93, HImode
"2 bytes", n_refs=2). With s08's C order (pout la + the two zero
stores BEFORE `*pout = u1 + table[idx]`), value1's birth->death span
is 2 insns (load and sum are RTL-adjacent; only the sunk la asm sits
between), so pri(value1) = 1*2*2/2 = 2.0 > pri(idx*2) = 2*16/30 ~=
1.06. value1 allocates first and takes $v1 (best free after the
sum/u1 share on $v0); idx*2 falls through to $a1 ($a0 is RESERVED -
the call argument `pout - 4` is already materialized as hard reg 4 in
the RTL local-alloc sees, so locals skip it). Retail has the arms
swapped, therefore in retail's compile the ORDER was inverted.

FIVE NEW LAWS (all verified by the s19/s20 builds against retail.norm):
1. THEN-STATEMENT-ORDER LAW (Law 1 extended to the then path): retail
   then emission is idx load, u1 load, table load, pout la, DB18=0,
   DB14=0, sum1, store - i.e. the la and the zero stores sit BETWEEN
   the table load and the sum. Restated in that C order, value1's span
   widens past 5 insns, pri drops to ~0.33 < 1.06, and the allocation
   flips: idx*2 -> $v1, u1 shares $v0 with sum1, value1 -> $a1,
   pout -> $a0 - EXACTLY retail (s19 then block byte-matches the retail
   register assignment).
2. ARM-PRIVATE-VARIABLE LAW: a temp assigned in BOTH if-arms is ONE
   multi-block pseudo; the global allocator gives it a single hard reg
   for both arms. Retail uses $v1 for the then idx and $a1 for the
   else idx - impossible from a shared decl - so retail's source had
   arm-private variables. Shared decls also cross-couple steering:
   s19's then-side fix silently regressed the closed else path
   (shared idx/v pseudos moved to $v1 globally, cascading through the
   else chains). s20 splits then-path temps (idxt/u1/vt) from the else
   temps and the else path returns to the exact s08 output.
3. TEMP-LOAD-WIDTH LAW: a named-temp assignment from a signed-short
   array element sign-extends and emits `lh`; the same load consumed
   inside an add expression (HImode subreg add) emits `lhu` because
   only the low half of the sum is stored. Retail's then table loads
   are lhu, so the temp form needs the u16 cast-through-pointer idiom
   (`vt = *(u16 *)&D_8014A3A4[idxt]`), matching the established
   cast-load shape for D_80189224/D_80189226.
4. LOCAL-ALLOC PRI ARITHMETIC (mechanism law): the {v1,a1} competition
   is decided by pri = floor_log2(n_refs)*n_refs*size/(death-birth),
   larger allocates earlier; hard regs already materialized in the RTL
   (call args) are excluded from the free scan. This reconciles the
   round-3 observation that "allocation order could not be reconciled
   with the pri formula" - it can, once the dump's real spans are used
   and the la/store statement positions are included in the spans.
5. HARD-ARG-REG RESERVATION: local-alloc never assigns a local to a
   hard reg that already appears as a destination in the RTL (a0 for
   the func_800604E0 argument). This is why idx*2 landed in $a1 pre-
   flip and why pout's global placement cannot displace the arg setup.

RESULT (s20_armprivate, diff = 25 lines vs retail.norm, s08 baseline
was 37): the then path now byte-matches retail's register assignment
(idx chain $v1, u1 $v0, value1 $a1, pout $a0, sum1 $v0, value2 $v1,
nop position, addiu $a0,-8 / j D_80072DB8 tail) and the else path is
unchanged from s08. The 25 residual lines are ALL known classes: label
naming (L_ELSE/L_E2/L_E3 vs L_GCC, 3 lines, probe-kit metric only),
at-factoring x2 (4 lines), dead join (3 lines), and the gas-proven
false classes (addu->addiu x4, j->jr, 5 lines). GsSetDrawBuffOffset is
now fully shaped at source level, both paths, modulo the two post-pass
items owned by the coordination lane.

Probe inventory: s19_thenreorder (shared-decl then reorder, then fixed
but else regressed, 45), s20_armprivate (arm-private temps + u16 cast
temp load, CLOSED at 25). sweep_then.sh reports psd->/val1-> regs.

Next queue:
1. (Coordination lane) at-factoring refold + dead-join elision in
   cc_post/maspsx - once those land, s20 is the carve source.
2. D_80072DB8 GsSort cluster attribution carve (independent).
3. Parallel lanes stay theirs: setIntr base->a1 steering, startIntr
   reopen, trapIntr fingerprint.
4. Runtime gate-family: still blocked (no runtime stack in sandbox).

## 2026-10-14 (later): D_80072DB8 attribution carve - the cluster is GsTMDdivTG3L .text+0x78, the then-tail is a cross-member tail-share

The "GsSort-style cluster" impression from round 2 is resolved, and it
is better news than a carve: **D_80072DB8 is an instruction boundary
inside a real LIBGTE member**, so the then-path tail resolves through
an existing member claim and needs NO extent carve of the data row.

Decode facts (baselines/mainmenu_jp.bin, LE words - see the new
"Retail baseline byte order" section in docs/TOOLCHAIN.md for the
endian/offset traps this pass hit and fixed):

- The row data_80072B20 is a MIXED region, not a cluster+padding:
  0x80072B20..~0x80072C24 front DATA (high-entropy words, then
  `ffffff00/ffffffff/ffffff00` markers); ~0x80072C30..0x80072D3C real
  CODE entered mid-row (jal 0x800667b8, arg-setup chain, and a branch
  reaching back into the data_800720F0 row - the same mis-typed-row
  code-weave class as intr_stop_begin); 0x80072D40..0x80072FBC the
  LIBGTE member (below).
- The member at 0x80072D40 is the sdk_members claim `DVGT3_00/01
  GsTMDdivTG3L` (ambiguous pair, sig-db agree): own prologue
  `addiu $sp,$sp,-0x88` + s6/s7/s8 argument takes, continuous legal
  mips1 stream, extent 0x27c ending exactly at the next row
  (GsTMDdivTG4L, unique+adoptable, at 0x80072FBC).
- D_80072DB8 = the member .text+0x78, the divided-primitive
  packet-copy tail: `addiu $s0,$a0,0xc; lhu $v0,6($s0); sll $v0,3;
  addu $v0,$s6; lwl/lwr $v1/$a0 8-byte loads; swl/swr into ($s3)` -
  the round-2 "GsSort-style primitive copying" idiom is the GTE
  division output writer, not a separate GsSort member.
- XRef: the ONLY image-wide `j 0x80072db8` is at 0x8007F264 =
  GsSetDrawBuffOffset+0x90 - the then-path tail, exactly where the
  probe shape has `.set noreorder; j D_80072DB8; nop`. The then path
  jumps INTO the GTE division member's packet-copy tail: a genuine
  cross-member mid-entry tail-share (LIBGS EMULIB -> LIBGTE), the
  same linker-level sharing family as the func_80062FCC splice.
- No legal branch from the member reaches below 0x80072D40 except the
  intra-weave edges noted above; the member boundary is clean.

Implication for the flip: the C side keeps `j D_80072DB8` with
D_80072DB8 resolving as a curated/auto mid-member label; once the
member itself is carved as an asm row the label becomes that row's
.text+0x78 symbol. The full row re-carve (front data extent, the
0x80072C30 weave fragment, DVGT3_00-vs-01 disambiguation from the
Psy-Q lib archives, and the data_800720F0 weave) is a standalone
session task with the libs present; it is NOT a GSD-lane gate.

Carve tool: scripts/gsdb8_carve.py (repo-external) - row legality
pass, TG3L boundary check, image-wide j/jal + lui/%lo XRef scan.

## 2026-10-14 (later): GsSetDrawBuffOffset round-5 - coordination handover: the goto-else source shape kills the dead join on top of s20's laws, RMW-sum encoding law, stray-nop root cause

From the cron-20261014-1227 queue item 1 (coordinate the goto-else shape
against the lane owner's s20). Their s19/s20 sources are repo-external in
their sandbox, so s20 was first RECONSTRUCTED from the round-3/4 documented
laws on top of this sandbox's probe kit (scripts/gsdbo/), then the goto-else
form was applied as a single-variable delta. All probes -O2 through
gsdbo_probe.sh (cpp -> cc1 2.6.3 -> maspsx --expand-div -> cc_post
--sdk-aspsx --keep-epilogue), metric = diff vs retail.norm under the
extended gsdbo_norm.py canon (folds the gas-proven false classes
addu/subu-imm and j/jr).

RECONSTRUCTION VALIDATED the round-3/4 law set end to end; three facts had
to be added, all banked here as laws or refinements:
1. ARM-POLARITY LAW: retail's guard branch is `beqz $v0,L_ELSE` (fall-
   through = then, u16 world). In if/else form the C must be
   `if (D_80194E3C != 0) { then } else { else }` - writing the then body
   under `if (guard == 0)` inverts GCC's branch to bnez. The goto-else
   form (`if (guard == 0) goto else_path;` + then at fall-through) gives
   the matching beqz directly.
2. Law-1 else order is REQUIRED exactly as documented (base A la, PSDIDX,
   first s16 load, if, *p1 load, base B la, SUM1, second s16 load, if,
   *p2 load, SUM2) - with the pre-law-1 order the else allocation
   cascades (idx->v1, u2->a1, p2->v0; the s19 phenomenon reproduced).
3. The *p1-load/SUM1 split is STRUCTURAL, not stylistic: retail emits
   [*p1 load][la p2][SUM1]; a volatile asm la cannot be scheduled across
   anything, so the C must split the load from the sum with the la p2
   statement between (`v1t = *p1; <la p2 asm>; s1 = u1 + v1t;`). v1t
   coalesces into p1's dying reg ($v0) - byte-identical to retail.

THE GOTO-ELSE RESULT (the handover item): with s20's laws in place, the
goto-else form eliminates the dead join at SOURCE level with ZERO other
effect. Matrix (raw diff lines vs retail.norm, same canon):
- s20b (arms inverted + pre-law-1 else order): 57
- s20c (= s20 laws, if/else form): 32
- s22 (s20c + the sum2 copy-fix below): 28
- s21e (goto-else + the sum2 copy-fix): 26
s22 vs s21e differ by EXACTLY [nop; j $Ljoin] plus a cosmetic label
renumber - the dead join is the only delta. s21e residual is 3 classes,
all known: label naming (L_ELSE/L_E2/L_E3, probe-kit metric only),
at-factoring x2, and one stray tail nop (below). CONSEQUENCE: the
cc_post dead-join elision candidate from round 3/4 is NO LONGER NEEDED -
the flip's post-pass dependency set shrinks to {at-factoring refold,
stray-nop elision}, both mechanical.

NEW LAW - RMW-SUM OPERAND ENCODING (fixes the one remaining real
encoding delta): when the sum's destination is also an input
(`s0 = u2 + s0`), GCC 2.6.3 materializes the read-modify-write form and
emits `addu $s0,$s0,$v0` (destination first) REGARDLESS of the C operand
order - round-3's law 2 ("C operand order controls rs/rt") holds only
for sums whose destination is NOT an input (sum1). The retail encoding
`addu $s0,$v0,$s0` (source operand first) is reproduced by routing the
sum through a dying temp: `t2 = u2 + s0; s0 = t2;` - the copy
propagates without commuting the plus and t2 coalesces into s0.
Two-statement, no allocation side effects (s21e proves the else path
unchanged otherwise).

STRAY TAIL NOP ROOT-CAUSED (the last non-at-factoring class): cc1's raw
output for the then tail is exactly retail ([.set noreorder][j
D_80072DB8][nop][.set reorder]); maspsx appends a SECOND nop after the
j - its delay-slot fill does not look inside the user asm block to see
that the slot is already occupied. Evidence: absent in .gcc.s, present
in .mas0.s (post-maspsx, pre-cc_post). Fix class: maspsx noreorder
delay-slot fill should skip when the next instruction inside the block
is already a nop (or a marker-gated cc_post elision). 1 line.

Probe inventory (repo-external scripts/gsdbo/): s20b_recon (negative
control), s20c_recon (s20 laws, if/else), s21_recon (goto-else),
s21e_recon (goto-else + copy-form sum2, BEST at 26 raw / 8 GCC-side
lines in 3 known classes), s22_recon (s20c + copy-form sum2). The s21e
source is the recommended carve source for the flip - it needs only the
at-factoring refold and the stray-nop elision to be byte-clean modulo
splitter label names.

Next queue:
1. (Lane owner) adopt or reject: goto-else replaces the dead-join
   elision; copy-form sum2 replaces the law-2 "same for sum#2"
   extrapolation; stray-nop root cause above for the maspsx pass.
2. (Lane owner) at-factoring refold remains the single substantive
   post-pass dependency for the flip.
3. D_80072DB8 / GsTMDdivTG3L carve stays independent (8d38434).
4. Parallel lanes stay theirs: setIntr base->a1 steering, startIntr
   reopen, trapIntr fingerprint.
5. Runtime gate-family: still blocked (fresh-checked this window).

## 2026-10-15 - func #56's "blob" is the CD file \SE.VH;1: the member void's game-code cluster is the SE ADPCM bank initializer

The size-delta addendum left the +0x800 blob as an open content
question; the fan-out addendum mapped its loader call into a data row.
This window decodes the loader end to end. Everything below is the
de-framed runtime view (payload offset = runtime - 0x80020000; jal =
region-OR law). Script repo-external
(scripts/blob_getter_and_content.py, full disasm in blob_out.txt).

THE FUNCTION IS THE SOUND-EFFECT (ADPCM) BANK INITIALIZER. func #56
(slps 0x8002C110 / sces 0x8002BF38) runs the same 14-call sequence in
both boots; decoded in order:

- Calls 1-2 (0x800436B8/0x800438D8 slps): setup, $s1 = 0x80016600.
- Call 3 is the "blob getter" - and it is NOT a rodata getter: it is
  a RETRY-FILE-LOAD wrapper. Shape: up to 4096 attempts (lui $s0,0xfff
  / ori 0xffff + bnez loop); each attempt = inner worker (0x8002CA84
  slps / 0x8002C8A0 sces) = a game-internal FLOAD: open the file,
  read its size from the handle, n = ceil(size/2048) (the sra 0xb /
  sll 0xb / addiu 1 dance), malloc (0x8002DBE0 slps) n*2048 bytes,
  CD-read into it (0x8002DBF0 slps), return the heap pointer.
  Open failure or malloc failure => panic reporter (0x8002DC10 slps /
  0x8002DA04 sces) printing "FLOAD:fault!\n" (0x80020910 slps /
  0x800208E4 sces), return 0.
- The argument passed to call 3 is the rodata string "\SE.VH;1"
  (slps 0x8004C3FC / sces 0x8004C0A0) - a Psy-Q ADPCM VOICE HEADER.
  THE BLOB IS A CD FILE, NOT EMBEDDED RODATA.
- The copy: 0x8620 (slps) / 0x7E20 (sces) bytes => 0x80016604 via the
  already-documented alignment-dispatch loop pair; the ori+addu
  expansion exists ONLY in slps because 0x8620 > 0x7FFF.
- Call 4 = free() of the heap buffer (0x8002EAA0 slps / 0x8002E644
  sces - exactly the fan-out addendum's target-4 free-thunk
  attribution, now with its calling context).
- Call 5 (0x800440D8 slps / 0x800440F4 sces) takes the copied VH at
  0x80016604 with arg -1 and (by elimination the only caller of the
  VH copy before the record getter reads them) populates the sound
  system's per-record pointer table + gate-byte array in its runtime
  workspace: pointer table 0x80114F48 slps / 0x801144CC sces, gate
  bytes 0x8012A894 slps / 0x80129E10 sces. NOTE: the EXE headers
  declare NO bss at all (b_addr = b_size = 0; t_size 0x46800, image
  ends 0x80066800, initial $sp = 0x801FFFF0) - the sound system's
  work areas are runtime-allocated between image end and stack top,
  which is why every one of these constants differs per boot.
- Call 6 (0x8002C7C8 slps / 0x8002C5E4 sces - the fan-out addendum's
  label-artifact pair) = the same retry-load shape for "\SE.VB;1"
  (the ADPCM VOICE BANK; slps 0x8004C408 / sces 0x8004C0AC = name
  + 0xC), second arg = sign16(call-5 result); its result lands in
  *(0x80016600) (store in call 7's delay slot, 0x80043CE8 slps).
- Call 9 (0x80044BFC slps / 0x80044C18 sces) is a per-index record
  getter: gate byte at (0x8012A894 + i) slps must equal 1, record =
  *(pointer table + i*4), then it copies fields +0x0/+0x4/+0x8
  (words), +0x12/+0x14/+0x16 (halfwords), +0x18 (byte) - the
  VagAtr-shaped 32-B tone record - into a 0x20-B struct. func #56
  calls it ONCE with the struct at 0x800D19C4 slps / 0x800D166C sces
  (one slot below the walk base).
- The LOOP (bound slti 0x3E = 62 slps / 0x3A = 58 sces - the per-boot
  literal the size-delta addendum flagged) calls call 10
  (0x80044CE0 slps / 0x80044CFC sces) per entry i with a3 = walk base
  0x800D19E4 + i*0x20 slps / 0x800D168C + i*0x20 sces and a0 =
  *(0x80016600) (the VB result): registering each tone against the
  VB.
- Tail: halfword defaults into image data globals - slps sh 0x5A =>
  0x8006504/0x80064FC, sh 0x65|0x7F (selected by lh 0x800689C) =>
  0x800650C/0x8006514; sces mirrors: 0x80061A0/0x8006198 and
  0x80061A8/0x80061B0 (selector lh 0x80066544). Same values both
  boots, different global addresses.

WHAT THIS ANSWERS (the size-delta addendum's content question):

- The +0x800 blob delta is EXACTLY ONE 2048-B MODE2 SECTOR of
  per-region SE.VH content. The copy sizes are per-boot literals
  (0x8620 vs 0x7E20) matching per-boot tone-record counts (62 vs 58;
  the record-array share of the delta is 4 x 0x20 = 0x80; the rest
  rides in the VH's parallel per-record tables - the exact file-level
  decomposition needs the discs, see blocker).
- The +0xC func-#56 size delta is now content-causal END TO END:
  JP's SE.VH is one sector bigger => JP's copy-size literal 0x8620
  exceeds signed-16-bit => ori+addu expansion in slps only.
- The "\SE.VH;1" / "\SE.VB;1" / "FLOAD:fault!" string trio appears in
  ALL 8 targets (FLOAD:fault! x2 in the boots + g3/g3org, x1 in
  mainmenu): every module embeds its own copy of this loader cluster,
  and every region's disc ships SE.VH/SE.VB for it.

BLOCKER (disc side): the disk/ CHDs were eaten by the sandbox
re-provision again - the JP/EU SE.VH byte-level diff (which records
differ; true file sizes vs the copy literals) waits on disc
re-provision. docs/MATCHING.md §3 regenerates the extracted trees
FROM the CHDs; the CHDs themselves are not repo-recoverable.

No carve-side action (same rule as the fan-out addendum): the loader
cluster is already-labeled code and the disc files are outside the
EXEs entirely. Docs-only: matched 174, ratchets 365/0, 8/8 verify
GREEN unchanged.

Next queue:
1. func #18's rodata preset family decode (runtime slps 0x800207CC..;
   carve first data row +0x8fc/+0x90c/+0xa70/+0xaa0 per the fan-out
   addendum) stays queued - cheap, independent.
2. Disc-side follow-up when CHDs return: extract SE.VH/SE.VB from
   both regions (tools/iso9660_extract.py), diff, decompose the
   0x800, reconcile true file sizes with the 0x8620/0x7E20 literals.
3. GSD round-5 (db2f96e) adopt/reject stays with the lane owner;
   setIntr base->a1 steering, startIntr reopen, trapIntr fingerprint
   stay theirs; runtime gate-family still blocked.

## 2026-10-15 late - func #18's rodata presets decode: the member-void screen-title composer (JP full-title copies vs EU prefix+suffix composition)

The size-delta addendum localized func #18's +0x220 to "codegen form";
the fan-out addendum mapped four preset carve locations. This window
decodes the presets' CONTENT and finds the real root: the two regions
organize the same titles differently, and the composition code follows.
De-framed runtime view throughout; script repo-external
(scripts/f18_presets.py, output f18_out.txt; regenerate blob_out.txt
note: the 1212-window scripts were eaten again, f18_presets.py is the
surviving artifact).

THE PRESET FAMILY (cp932/Shift-JIS decoded):

- slps 0x800207CC / sces 0x800207D8: the disc-ID ASCII string,
  "BISLPS-00270" / "BESCES-00269" - strcat'd into the record first.
- slps has FOUR complete per-mode titles (copied wholesale):
  mode 0 0x800207DC (0x33 B): "ＧＡＬＡＸＩＡＮ３　ドラグーンプレイレコーディング"
  mode 1 0x80020810 (0x2F B): "ＧＡＬＡＸＩＡＮ３　ガーブプレイレコーディング"
  mode 2 0x80020840 (0x2F B): "ＧＡＬＡＸＩＡＮ３　ドラグーンミッションデータ"
  mode 3 0x80020870 (0x2F B): "ＧＡＬＡＸＩＡＮ３　ガーブミッションデータ"
  (ガーブ = GOURB in katakana; the presets are packed contiguously:
  0x207DC + 0x33 = 0x20810 - 1... each string NUL-terminated, next
  preset starts immediately.)
- sces has FIVE presets composed prefix+suffix:
  prefix 0x800207E8 (0x15 B incl NUL): "ＧＡＬＡＸＩＡＮ３　"
  suffixes: mode 0 0x80020800 "ＤＲＡＧＯＯＮ：ＰＬＡＹ", mode 1 0x8002081C
  "ＧＯＵＲＢ：ＰＬＡＹ", mode 2 0x80020834 "ＤＲＡＧＯＯＮ：ＭＩＳＳＩＯＮ",
  mode 3 0x80020854 "ＧＯＵＲＢ：ＭＩＳＳＩＯＮ" - full-width ASCII for the
  module names where the JP boot uses katakana.
- Mode->title map matches across boots: DRAGOON/GOURB x PLAY/MISSION
  (JP "プレイレコーディング"/"ミッションデータ" vs EU "：ＰＬＡＹ"/"：ＭＩＳＳＩＯＮ").
  Modes >= 4 fall through to the inner helper (0x8002A71C slps /
  0x8002A544 sces) unchanged from the size-delta addendum.

THE COMPOSITION (both boots, same skeleton):

- Stack record at sp+0x80 (frame 0x130): header = word+halfword from
  the .sdata slots (slps 0xa0/0xa4($gp), sces 0xa4/0xa8($gp) - the
  known +4 .sdata shift); strcat(disc-ID); strcat(arg string s1);
  func #19(sp+0xF8, s1); sh 0x11 record field.
- func #19 is an ASCII->FULL-WIDTH SHIFT-JIS CONVERTER: per char,
  (c+0xBF)<0x1A selects A-Z and (c+0xD0)<0xA selects 0-9, emitted as
  lead 0x82 + (c+0x1F) (0x41->0x8260 'Ａ', 0x30->0x824F '０'); other
  bytes via the 0x81 lead path; reads its trailing fields from the
  .sdata slots (0xa8/0xaa($gp) slps, 0xac/0xae($gp) sces).
- Per mode: the preset lands at sp+0xA2, then strcat(sp+0xA2,
  sp+0xF8) appends the fullwidth-converted argument; record fields
  0xe4/0xe8/0xec/0xf0 get the descriptor pointers (+0x2C thrice) and
  0xf4 the constant 0x5600.

THE ROOT OF THE +0x220 (upgrade of the size-delta addendum):

- slps: each mode's COMPLETE title is a fixed-size copy - the
  alignment-dispatch loop pairs already documented (m0 0x33 B via
  0x30-loop + lh/lb tail; m1/m2/m3 0x2F B via 0x20-loop + 0xE tail,
  m2/m3 sharing their tail). All mode paths j into shared tails, so
  the static strcat count is 4 (2 head + 2 shared tails) - the
  census's "strcat x4 slps" now has its mechanism.
- sces: the 0x15-B prefix is an INLINE SINGLE-SHOT copy (six lwl/lwr
  pairs + lb, exactly the NUL-terminated string length), then each
  mode strcat's its suffix AND the shared scratch: 8 static strcat
  sites (2 head + 2 per mode pair) - the "x8 sces" mechanism.
- Same sentence content, different string-data organization => both
  the copy-form difference AND the strcat-count difference are
  content-causal, completing the func-#56 pattern: every member-void
  size delta so far traces to per-region CONTENT, never to arbitrary
  codegen variance.

DESCRIPTORS ARE BYTE-IDENTICAL ACROSS BOOTS:

- slps 0x8004BF18 (modes 0/1) + 0x8004BFD8 (modes 2/3) vs sces
  0x8004BBBC / 0x8004BC7C - same 0xC0 stride per boot, contents
  byte-equal pairwise. Each is a 0x2C-B record (00 00 ff ff / 10 10
  or 04 40 header, then a descending ramp table - gradient/palette-
  shaped; field semantics not pursued this window); the +0x2C
  successor record is referenced three times per composition.

CORRECTIONS TO THE FAN-OUT ADDENDUM's preset carve list:

- Its four offsets per boot were the disc-ID string + modes 0-2
  only. The code-derived family (10 address materializations):
  slps carve +0x8fc/+0x90c/+0xa70/+0xaa0 PLUS mode 3 at +0xad0
  (runtime 0x80020870); sces +0x908/+0x918/+0xa60/+0xa7c PLUS
  +0xa94/+0xab4 (runtime 0x80020834/0x80020854). The drift model
  carve = runtime + 0x130 + 0x130*sector is confirmed on all ten
  mappings (0x130 = the first-sector gap at the image head).

BONUS (entry-point fact): pc0 (0x8002DB14 slps / 0x8002D908 sces)
begins with the huge zero-clear loop 0x800663FC..0x8012C3F4 slps /
0x80066098..0x8012C16C sces - the undeclared-bss zeroing that
provisions the sound-system work areas the SE.VH window found at
0x800Dxxxx-0x8012xxxx.

No carve-side action: the presets and descriptors are already-labeled
rodata; the composition code is already-labeled code. Docs-only:
matched 174, ratchets 365/0, 8/8 verify GREEN unchanged.

Next queue:
1. Descriptor field semantics (the 0x2C-B gradient records + the
   0x5600 constant + the 0x11 record field) - low value, optional.
2. Disc-side SE.VH/SE.VB diff still waits on CHD re-provision.
3. GSD round-5 (db2f96e) adopt/reject stays with the lane owner;
   setIntr base->a1 steering, startIntr reopen, trapIntr fingerprint
   stay theirs; BIG de-frame stays coordination-gated; runtime
   gate-family still blocked.

## 2026-10-15 late - func #18's descriptor fields decode: four desc pointers + a size travel through a stack-struct into 0x8002ADA0; plus a Witness on the boot load model

Queue item 1 of the presets section. De-framed runtime view throughout;
script repo-external (scripts/descriptor_semantics.py, output
descriptor_out.txt). Fixes three details of the presets section along
the way.

THE RECORD LAYOUT (sp-relative vs record-relative correction): the
record base is $s0 = sp+0x80, so the presets section's "record fields
0xe4/0xe8/0xec/0xf0/0xf4" are SP offsets - record-relative they are
+0x64/+0x68/+0x6C/+0x70/+0x74. The "sh 0x11" lands at record+0x20
(sp+0xa0), immediately before the mode-title copy zone at record+0x22
(sp+0xa2). The title string itself starts at record+0x00.

DEAD HEADER STORES (both boots): func #18 first stores the gp+0xa0
word and gp+0xa4 halfword into record+0x00/+0x04, then strcat(disc-ID)
overwrites record+0x00 from index 0. The header stores are dead in the
final record - a source-level aliasing artifact (probably a union or a
hand-typed overlapping assignment), reproduced identically in both
boots, so the rebuild must keep them.

MODE-DEPENDENT SIZE CONSTANT: rec+0x74 gets 0x5600 for modes 0/1
(0x80029D14 slps) but 0xB80 for modes 2/3 (0x80029F04 slps) - the
presets section's "0xf4 the constant 0x5600" holds only for the PLAY
branch.

THE HANDOFF IS THE COMMON TAIL (correction): after the mode dispatch,
the tail copy loop (0x80029F0C slps) moves record+0xC..+0x78 (0x6C B)
to sp+0x10 and calls the inner void helper (0x8002A71C slps /
0x8002A544 sces) with a0 = func #18's own a0 (s3) and a1/a2/a3 =
record words 0/1/2 - an o32 struct-by-value pass. ALL modes reach it;
the size-delta addendum's "in the >=2 mode also calls an internal void
helper" misread the join. Record struct layout (0x78 B): +0x00 title
string (BISLPS-00270/BESCES-00269 + arg), +0x20 halfword 0x11, +0x22
mode title + fullwidth arg, +0x64 desc base ptr, +0x68/+0x6C/+0x70
desc+0x2C successor ptr (same value three times), +0x74 size
(0x5600/0xB80).

HELPER INTERNALS (0x8002A71C slps, 0x28 frame): calls 0x8002AC5C(s3)
for an id/handle (-1 -> return -0xA); calls 0x8002AD0C(id, 0) for a
status (3 -> early return 0, nonzero -> return -1); then formats two
nibbles of the id ASCII (sra 4/andi 0xF, +0x30 - digits '0'-'9' only)
into a local buffer; loads struct+0x14 (rec+0x20, the 0x11 halfword)
as a1, struct+0x58 (rec+0x64, desc base) as a3, and struct+0x5C..0x68
(rec+0x68/6C/70/74) as four stack args; tail-calls 0x8002ADA0(buf,
0x11, buf2, desc_base, [desc_succ, desc_succ, desc_succ, size]).

CONSUMER HEAD (0x8002ADA0, slps): takes desc base -> s3, first stack
arg (desc+0x2C) -> s0, and the size arg (+0x200, then round up to
0x2000 granularity via the sra/sll 13 dance, plus another +0x2000 when
the rounded value differs) - allocation-shaped arithmetic. The size is
NOT the desc blob length: the two desc units sit only 0xC0 apart.

THE DESCRIPTOR BLOBS: byte-equal pairwise across boots (re-confirmed).
desc0 (modes 0/1) vs desc2 (modes 2/3) differ in 72 of the first 0xC0
bytes - bands +0x04..0x27 and +0x82..0xBE; both carry `8c 00 00 00 00
0X 00 0Y` at +0x20 with X=02 for the PLAY pair and X=03 for the
MISSION pair (Y=00/01). desc0's head ramp descends as byte pairs
(0xbfd5..0x9008), desc2's as halfwords (0x7e10..0x7c08). No TIM magic
(0x00000010) anywhere in either - content stays unidentified beyond
the earlier gradient/palette reading.

CALLERS: two per boot, both inside the member void (slps 0x80029214 /
0x800295C4; sces 0x8002925C / 0x8002960C). func #18's a0 flows into
0x8002AC5C as a handle. The gp+0xa0/a4 slots are read at 8 sites
(func #18 x2, several void siblings) - and written NOWHERE in the
image (see Witness).

WITNESS (new, for the de-frame lane): the boot load model does not
close. (a) The de-framed CRT0 at pc0 (0x8002DB14 slps / 0x8002D908
sces) is coherent: zero-clear 0x800663FC..0x8012C3F4, $sp = [0x8002DBC4]
| 0x80000000, $ra saved at 0x80066524, $gp = 0x8006632C slps /
0x80065FC4 sces, then a BIOS A0-thunk table at 0x8002F94C (t2=0xa0,
t1=0x39), then main 0x80021800. (b) The raw/carve-linear load model is
REJECTED: pc0 under file-linear mapping lands on mid-function garbage
(payload 0xBE94), while the de-framed position decodes as the CRT0
above. (c) BUT every link-view address the CRT0 touches ($gp window
0x8006632C..0x800663FC, bss from 0x800663FC) lies BEYOND the de-framed
image end (0x8005D5F0; t_size 0x46800 = the raw remainder including
framing, de-framed content 0x3D5F0). (d) Nothing in the image writes
the gp slots - zero gp-relative stores in the 0x9c..0xb0 window, no
la materializations of 0x800663CC-class addresses; the provisioning of
that 0xD0-B sdata window (and the bss that follows it) happens outside
the de-framed image, by a mechanism this window did not find. (e) The
gp-init pair exists TWICE in the payload (de-framed 0x8002DB94 and
again at 0x8002E394+0x70 - the +0x20800 shift lands on the known
func_8002E394 row the fan-out addendum flagged as "same function,
opposite labels"). (f) config/splat.slps_00270.yaml's gp_value
0x8006322C is a digit-substitution typo of the true $gp 0x8006632C -
the substitution 663->632 appears three times (the gp_value itself and
the comment's example slots 0x80063268/0x80063294, which decode to
0x80066368/0x80066394 off the actual pair). It is inert for the build
(matched C compiles -G0, so no GPREL16 references _gp; the crt0 pair
is a literal in the asm tree), but it poisons any address arithmetic
derived from it - this window nearly did.

No carve-side action; docs-only: matched 174, ratchets 365/0, 8/8
verify GREEN unchanged (slps_00270 re-verified after this window's
reset forward).

Next queue:
1. Resolve the boot sdata provisioning (the Witness): who fills
   0x8006632C..0x800663FC before func #18 reads gp+0xa0? Check main
   (0x80021800) head, the region above the de-framed image end, and
   whether the boots de-frame via a mechanism the game modules don't
   use. Feeds the coordination-gated BIG de-frame item directly.
2. gp_value typo fix (config/splat.slps_00270.yaml 0x8006322C ->
   0x8006632C) - coordinate with the scan lane owner: gen_ld.py emits
   _gp from it; verify blast radius before landing.
3. Descriptor blob content identification (icon/palette candidates) -
   low value, optional.
4. Disc-side SE.VH/SE.VB diff still waits on CHD re-provision; GSD
   round-5 stays with the lane owner; BIG de-frame stays
   coordination-gated; runtime gate-family still blocked.

## 2026-10-15 late - the boot load model closes: the baselines are a corrupted extraction (contiguous raw read); .sdata is provisioned by the load; the gp_value "typo" is refuted

Queue item 1 (and item 2's blast-radius check) of the descriptor section.
Script repo-external (scripts/boot_load_model.py, output
boot_load_model_out.txt). The Witness's open question - who fills
$gp window 0x8006632C..0x800663FC - has a structural answer, it corrects
the de-frame item's premise, and the item-2 verify check FAILED in an
instructive way (reverted; the failure is the finding).

THE MECHANISM (named): tools/iso9660_extract.py's `Iso.read()` is
`seek(lba*2352 + USER_OFF); return f.read(size)` - a CONTIGUOUS read. It
never steps per-sector to take only the 2048-byte user data
(USER_OFF/USER_LEN serve the PVD/directory reads, which stay inside one
sector; the file read forgot the de-interleave). The extracted file is
therefore the raw bytes from the extent's first user-data byte, weaving in
every following sector's 280-byte EDC/ECC tail plus the next sector's
24-byte sync/addr/subheader (304 B per 2048 B delivered), and it STOPS
after `size` bytes - mid-extent, because the raw stream consumes 2352 raw
bytes per 2048 delivered. The queued de-frame item's "the disc really does
hold the framed file - this is not an extraction bug" is REFUTED: it is an
extraction artifact, and the oracle's SHA-1 consistency only proves the
oracle was computed from the same extraction. The GDB-verified de-framed
RAM needs no exotic mechanism: the drive delivers user data per sector.

THE PROOF (measured this window, all 8 targets):
- Sync weave: slps carries 123 syncs at 0x918 + k*0x930, ALL gaps exactly
  2352 - a perfect raw-sector weave (first sector's 24-byte header is the
  only one skipped, hence first gap 0x118).
- MSF addresses are BCD and advance +1 per sector (0x25, 0x26, ... 0x29,
  0x30 - BCD carry). The banked sector_edc_proof run's "MSF monotonic:
  False" was a checker bug (binary frame arithmetic; frames are BCD). The
  sequence is perfect.
- ECC VERIFIES: regenerating P/Q parity with the project's own MAME-derived
  tables (chd_extract.ecc_generate) reproduces 172/172 P and 104/104 Q
  parity bytes of a sampled woven sector. The sectors are genuine MODE2
  form1 records. (EDC still mismatches - 0/122, same as the banked run -
  but with genuine ECC over [12..2076) that is a mastering-tool quirk, not
  a structural doubt; the 4 EDC bytes even interrupt real Shift-JIS user
  text, "オ・システム", at the exact spec offset.)
- t_size == len(baseline)-0x800 EXACTLY for all 8: every header is a normal
  EXE header authored against the true file (payload = filesize - 2048).
- len(payload) == the 0x930-grid prediction for all 8 (123 data areas for
  the boots ... 268 for g3org_eu): deframe() is the user-data join of the
  truncated stream.

THE ARITHMETIC: the true payload is t_size bytes; the baseline carries only
the data areas that fit in `size` contiguous raw bytes; so every target is
MISSING the tail of its true payload:
  missing = t_size - len(payload) =
  slps 0x9210, sces 0x9210, mainmenu_jp 0x16000, mainmenu_eu 0x160B0,
  g3_jp 0x121C0, g3_eu 0x122F0, g3org_jp 0x13D10, g3org_eu 0x13E40
  (= 12.9-13.0% of every payload)
and by algebra (t_size = len-0x800) missing == the baseline's total framing
exactly: the extraction swapped the tail user data 1:1 for sector overhead.
The last ~19 sectors' user data of every file exists ONLY on the disc.

THE RESOLUTION (boots): the BIOS loads t_size bytes of TRUE content (user
data) at 0x80020000, so RAM = the plain payload with NO framing anywhere.
The CRT0 decodes coherently from it and reproduces every Witness number:
slps pc0 0x8002DB14 = zero-clear 0x800663FC..0x8012C3F4, $sp =
[0x8002DBC0]|0x80000000, $ra saved at 0x80066524, $gp = 0x8006632C, jal
0x8002F94C (the A0-thunk table); sces pc0 0x8002D908 = clear
0x80066098..0x8012C16C, $gp = 0x80065FC4 (pair at 0x8002D988). THE .sdata
WINDOW IS PROVISIONED BY THE LOAD: [gp, clear_start) = 0x8006632C..
0x800663FC slps (0xD0) / 0x80065FC4..0x80066098 sces (0xD4) lies INSIDE
the loaded payload (payload offsets 0x4632C..0x463FC / 0x45FC4..0x46098).
No code needs to write it because .sdata initializers live in the FILE -
the Witness's "written nowhere in the image" is exactly what a
file-initialized .sdata looks like - and the zero-clear starting at the
window's end is the normal linker layout (initialized data ends, bss
begins; the image tail [.., 0x80066800) inside the cleared range is
zero-padding the CRT0 also re-wipes, and it hosts the 0x80066524 $ra slot
AFTER the clear). The window's bytes sit in the MISSING TAIL (payload
0x4632C > 0x3D5F0) - disc-only until the CHDs return, like every byte
above payload offset 0x3D5F0 in both boots.

THE gp DUALITY (item 2 refuted by its own blast-radius check): changing
yaml gp_value 0x8006322C -> 0x8006632C broke verify with 46 single-byte
diffs, every one a gp-relative displacement. Link math on the first diff:
built imm 0xCF2C = tree symbol 0x80063258 - new _gp 0x8006632C; retail imm
0x2C = 0x80063258 - 0x8006322C. So the retail's gp-relative ENCODINGS are
authored against 0x8006322C in carve space, and the tree (adopted symbol
addresses + _gp + build.sh's gp_rel rewrite) reproduces them with that
value - the two "wrong" terms cancel. 0x8006322C is the CARVE-SPACE gp
base; 0x8006632C is the TRUE-RUNTIME $gp the CRT0 sets; 0x3100 = the
dual-view offset at that depth. Both facts are real and must not be
"fixed" into each other: the yaml value stays, and any TRUE-runtime
address arithmetic (de-framed scans) must use the CRT0 value instead.
The gen_ld comment's stale "at 0x800304D4" citation was left as-is
(neither the payload nor the baseline decodes as a gp-set there; the
CRT0 pair above is the anchor now).

COROLLARIES for the coordination-gated BIG de-frame item:
1. The drift law (carve = runtime + 0x130*(1+sector)) is this extraction
   artifact's byte-shift, here measured at tail depth: the carve address
   of the slps window (0x8006632C) holds real user data of true payload
   0x3CA4C (local skew 0x98E0); sces's window carve address lands in pure
   overhead. Witness A/B are instances of the same law.
2. The carve's tail region [len(payload)..t_size) of every target holds
   duplicated lower content plus overhead, and the true payload tail is
   absent from every local artifact. The de-frame transition therefore
   REQUIRES the disc: a per-sector re-extraction yields the true EXEs and
   new SHA-1 oracles. Until then today's framed oracle remains the only
   self-consistent gate (it is byte-preserving; matching discipline
   continues unchanged; only address DERIVATION is poisoned).
3. The queued "decide what make verify compares" sharpens: the real choice
   is corrupt-extraction-vs-true-file, not framed-vs-de-framed policy.
4. tools/iso9660_extract.py needs a per-sector read path (join USER_LEN
   per sector across ceil(size/2048) sectors, truncate to size) behind an
   OPT-IN flag - opt-in, because flipping the default would silently
   change what a fresh extraction reproduces and desync it from the
   committed oracles.

No carve-side action (same rule). Docs-only: matched 174, ratchets 365/0;
make verify slps_00270 re-run GREEN after the revert (28 s), the other
targets untouched.

Next queue:
1. iso9660_extract.py opt-in per-sector read flag + a synthetic-sector
   unit test (3 fake sectors, join arithmetic, truncate-to-size) so the
   re-extraction recipe is correct the day the CHDs return.
2. CHD re-provision now unblocks THREE standing items (SE.VH/SE.VB diff,
   the missing tails, the true re-extraction) - raise its priority.
3. The boots' .sdata window content (both 0xD0/0xD4-byte blocks) is
   disc-only; when the disc returns, dump payload 0x4632C..0x463FC slps /
   0x45FC4..0x46098 sces first and identify the gp+0xa0..0xb0 slots the
   member void reads.
4. GSD round-5 (db2f96e) adopt/reject stays with the lane owner; setIntr
   base->a1 steering, startIntr reopen, trapIntr fingerprint stay theirs;
   BIG de-frame stays coordination-gated; runtime gate-family blocked.

## 2026-10-15 late (window cron-20261015-1642) - the discs return: CHD re-provision oracle-proven; the boots' .sdata windows dump; SE.VH's "+0x800" becomes 4 VAGs x 16 slot-groups

Trigger: Silent handed fresh Discord CDN links for both discs into #dragoon
(links expire ~2026-10-16 09:54 UTC; the cron task prompt now carries them
with sha256s - the job was recreated as 461868 after 449530). This window
fetched, verified and banked the first true-content bytes the project has
ever had. scripts/disc_reprovision.py + parse_vh_counts.py (repo-external)
produced scripts/disc_reprovision_out.txt.

Disc re-provision (disk/, git-ignored; CHD v5 "MComprHD"):
- Galaxian3_Europe.chd 382,613,010 B, sha256
  98ccd87749918a3ac2e072f1ab9c7649eae567627c3edd62f8154c4b98cf165c;
  Galaxian3_Japan.chd 382,607,234 B, sha256
  a6025267f57392e178a2feace611a28e5ffd8ee2819358596f0879130fc73d08.
- chd_extract.py: EU 267,752 sectors / JP 267,504 sectors, 4 tracks
  (track 4 audio), map types {NONE, cdlzma, cdzl, flac} as expected.
- ORACLE PROOF: contiguous (default) extraction of ALL 8 EXE targets is
  byte-identical to baselines/*.bin; the boots reproduce the committed
  SHA-1 oracles (slps_00270 f2a13b52..., sces_00269 19698984...). The
  CHDs are the original media; the whole CHD -> bin -> ISO9660 -> file
  chain is exact on both regions.
- True content via the opt-in --per-sector read (last window's tooling,
  first real-disc exercise): both boots + SE.VH;1 + SE.VB;1 per region.

The boots' .sdata windows (queue item 3 of the boot-load-model section):
- slps payload 0x4632C..0x463FC (0xD0 B) and sces 0x45FC4..0x46098
  (0xD4 B) dumped from the TRUE files. Both sit in file sector 141/142 -
  fully inside the contiguous baseline's woven tail; the baseline bytes
  at the same offsets are pure framing (a repeating 02 00 00 fe pattern).
  These bytes have never been seen by the project before this window.
- Content decodes as a small .sdata pool: pilot-name C strings NONE /
  FRANK / REIKO / JOHNSON / SHARK / GHOST (the DRAGOON/*.DAT cast), an
  ints cluster (1, 0, 1 and a 0x3C-scaled field), a second NONE +
  0xFFFFFFFF, six 8-B button-label slots " (1)" " (2)" " (A)" " (B)"
  " (C)" " (D)", the string "bu00:" and halfwords 0x8169 / 0x816A, tail
  word 0x2A.
- LAYOUT DIVERGENCE: the two windows hold the same pool but NOT at the
  same slot indices. sces[gp+0] is the runtime pointer 0x80020040 and the
  common content starts one word later than slps (hence 0xD4 vs 0xD0 B,
  4 spare zero bytes at the sces tail). Whether slps carries the same
  pointer at gp-4 is outside the window (CRT0 decode will tell). The
  member void's gp+0xa0..0xb0 reads therefore land on different fields
  per region ("bu00:" at slps gp+0xA0 vs sces gp+0xA4). Per-region
  gp-relative slot maps are MANDATORY before any .sdata symbol work; a
  one-word shift is exactly what a shared map would silently corrupt.

SE.VH;1 / SE.VB;1 (the func #56 follow-up, blocked since the blob window):
- SE.VH head: "VABp", ver 6, id 0, and fsize == VH+VB combined size
  EXACTLY per region (JP 0x8620+0x62450 = 0x6AA70; EU 0x7E20+0x5E420 =
  0x66240). 0x10 = 0xEEEE marker; the region's VAG count (0x3E = 62 /
  0x3A = 58) sits in THREE halfword slots 0x12/0x14/0x16 - the same
  numbers func #56's slti loop bounds use: the game trusts the header's
  own count field.
- 0x20..0x820: 128 x 16-B program records ("01 00 00 36 ..." templates);
  per-program field diffs every 0x10 between the regions (134 diff runs
  inside the first 0x800) - region tuning lives here.
- VAG table from 0x820 (0x20-B slots): SLOT-COUNT LAW - region size ==
  (numVags+1) x 16 slots x 0x20 B, HOLDS in both regions (JP (62+1) x 16
  x 0x20 = 0x7E00; EU (58+1) x 16 x 0x20 = 0x7600). The JP file is the
  EU file with a 0x800 insert at the region start (12 of 14 0x10-aligned
  shift probes match) = 4 extra VAGs x 16-slot groups = EXACTLY one
  2048-B sector. func #56's "+0x800 = one sector" copy-size observation
  now has a mechanism.
- Record fields carry a repeating template (b1 b2 tags, c0/c1/c2/c3
  halfword runs); the VAG body-size field is NOT yet identified (sweeps
  over u16 fields x 1/0x10/0x80/0x200/0x800 units found no sum equal to
  the VB size) - the Call-5 parser disasm is the cross-reference that
  will pin the field offsets. 481 differing bytes in the common region,
  one 107-B run.
- SE.VB;1: JP 0x62450 / EU 0x5E420 (delta 0x4030). The first 0x39150 B
  (233 KB, ~45%) are byte-identical; divergence is 15-B-period runs
  inside 16-B ADPCM blocks (75 of 189 sectors touched) - shared early
  VAG bodies, region-specific audio later, and JP carries the extra
  bodies for its 4 extra VAGs in the 0x4030 tail.

Gates: docs-only (plus git-ignored disk/ + repo-external scripts); 8/8
verify GREEN untouched; matched 174; ratchets 365/0. No carve-side action.

Next queue:
1. SE.VH record field decode: cross-ref func #56's Call-5 parser (the
   0x8002CA84 slps worker) field offsets against the real bytes; pin the
   VAG body-size field, re-walk the VB with it, and map the 4 extra JP
   VAGs to their VB offsets (the 0x4030 delta tail).
2. The .sdata windows feed the de-frame item: build the per-region
   gp-relative slot maps (slps 0xD0 / sces 0xD4 B) before any .sdata
   symbols are authored; note the sces one-word lead (0x80020040 at
   gp+0) and settle whether slps mirrors it at gp-4 via the CRT0 decode.
3. True re-extraction bookkeeping (de-frame transition prep): the
   --per-sector boots are the FUTURE oracles' source; config/sha1 stays
   untouched until the coordination gate flips.
4. GSD round-5 adopt/reject stays with the lane owner; setIntr steering
   / startIntr reopen / trapIntr fingerprint stay theirs; BIG de-frame
   coordination-gated; runtime gate-family blocked.

## 2026-10-16 - SE.VH layout closes against the real bytes: the parser is Psy-Q libsnd SsVabOpenHead-shaped, the size table sums the VB exactly, the JP/EU audio divergence is mapped per VAG

Queue item 1 of cron-20261015-1642. Window opened on sandbox rollback #N:
repo rolled back to 7623cd2, disk/ and the repo-external scripts of the
last two windows eaten; recovered per protocol (fetch + reset to
90c65b4; CHD links still live, both refetched + sha256-verified - the
recreated cron prompt's disc-assets section exercised for real). All
true-content extractions redone. New repo-external scripts:
vh_parser_xref.py (+_out.txt), vh_size_table_test.py, func56_callsite
disasm (func56_callsite_out.txt).

THE CALL-5 PARSER DECODED (slps 0x800440D8 -> 0x80044174; true-payload
disasm, payload = runtime - 0x80020000):
- It is Psy-Q libsnd SsVabOpenHead-shaped. 16 VAB slots: vab_id -1
  (SsVAB_AUTO) scans the gate bytes 0x8012A894[0..15] for a zero slot,
  claims it (gate = 1), and stores the VH base at 0x80114F48[slot] -
  BOTH are per-VAB tables, NOT per-record (correction below).
- Header checks: word0 >> 8 == 0x564142 ("VAB") and byte3 == 'p';
  version = word+4; stride = 0x40 (ver<5) / 0x80 (ver>=5), kept at
  0x80115070; count = lhu +0x12 (62/58), must be <= stride.
- Program loop: stride x 0x10-B records from VH+0x20 (128 x 0x10 =
  0x800 for ver>=5). +0 = tones count; RUNTIME patches (file holds
  placeholders): +8 = sequential program id for every nonzero-tones
  program; +0xC/+0xE = VB offsets of tones 2p/2p+1 - two tones per
  program max, VAG i belongs to program i/2.
- VAG area = VH+0x820, count x 0x200-B blocks; VagAtr records sit at
  0x20 stride (Call 10 reads attr bytes 0..9 from a slot-scaled
  runtime pointer 0x801150F0 + (0x8012A87B_byte*16 + a2)*0x20).
- SIZE TABLE = VH+0x820 + count*0x200 (the LAST 0x200 block): 2-B
  entries; VAG body bytes = entry << 3 for ver>=5 (sll 3 at
  0x800443F8; ver<5 = << 2). Cumulative sum = the running VB offset
  (with a base arg a3); total sanity-checked against 0x80000.

CORRECTIONS to the 2026-10-15 func #56 section (its disasm-derived
field map was right, its SEMANTICS were not):
- Call 9 (0x80044BFC) is NOT a per-tone record getter: call site
  0x8002C248/0x8002C380 passes a0 = *(0x80016600) = the VAB ID (see
  below), a1 = 0x800D19C4. It checks gate[vab_id] == 1, loads the VH
  base from 0x80114F48[vab_id*4], and copies the VabHdr fields:
  word+0 = "VABp" magic, word+4 = version, word+8 = id, halfwords
  +0x12/+0x14/+0x16 = the count x3, bytes +0x18..1B = 7f 40 00 00.
  The "VagAtr-shaped 32-B tone record" reading is REFUTED - func #56
  was fetching the bank's metadata (incl. the count).
- *(0x80016600) holds Call 6's result = the VAB ID, not a VB heap
  pointer: Call 6 (0x8002C7C8) is SsVabOpenBody-shaped - args are the
  "\SE.VB;1" load + sign16(Call-5 result), i.e. (file, vab_id) - and
  returns the id. Call 5 = SsVabOpenHead(VH copy, -1).
- Call 10 (0x80044CE0) call site 0x8002C3C8: args (vab_id, tone i,
  0, 0x800D19E4 + i*0x20) - the "a0 = VB result" reading was the same
  misidentification. gate[vab_id] again; the per-tone attr bytes land
  in the walk-base structs.

FILE LAYOUT (both regions, now closed byte-exact against the discs):
  0x000   VabHdr 0x20 B ("VABp", ver 6, id 0, fsize = VH+VB sum,
          0xEEEE marker, count x3 at 0x12/0x14/0x16, 7f 40 00 00,
          ffffffff)
  0x020   program table, 128 x 0x10 B (file placeholders at +8/+0xC/
          +0xE are runtime-patched)
  0x820   VAG area, count x 0x200 blocks; VagAtr 0x20-B records at
          0x820+i*0x20; the rest of the area is pre-initialized
          template records (b1 b2 tags + c0/c1/c2/c3 halfword runs)
  0x820+count*0x200   size table, count+1 2-B entries
  total   = 0x820 + (count+1) x 0x200  (JP 0x8620, EU 0x7E20)

THE SIZE TABLE SUMS THE VB EXACTLY, both regions:
- JP: 63 entries at 0x8420, sum << 3 = 0x62450 == len(SE.VB;1) EXACT.
- EU: 59 entries at 0x7C20, sum << 3 = 0x5E420 == len(SE.VB;1) EXACT.
- entry[0] = 0 and entry[count] = 0x3B2 (7568 B) in both; the table
  carries count+1 entries - the "+1" of the block law is real on BOTH
  sides (one extra size entry AND the size table's own block). Whether
  VAG 62 (the 0x3B2 tail body at VB 0x606C0..0x62450) is registered by
  a path outside func #56's 62-loop is open.

JP/EU AUDIO DIVERGENCE MAP (per VAG, from the size tables + bodies):
- VAGs 0..28: bodies byte-identical (same sizes, same offsets).
- VAG 29: first divergence - VB first diff 0x39150 = VAG 29's body
  offset (0x39130 both) + 0x20; same nominal start, region-tuned
  after 0x20 B; size entries already differ here.
- VAGs 30..48 and 57: size entries differ (region-tuned lengths).
- VAGs 58..61: JP-ONLY (offsets 0x59060/0x5A360/0x5C910/0x5F090,
  body sizes 0x1300/0x25B0/0x2780/0x1630).
- Net: sum(JP entries)<<3 - sum(EU common)<<3 = 0x4030 = the VB size
  delta, witnessed from the file side end to end.

gp-4 SETTLED (cron-20261015-1642 queue item 2): payload gp-4 =
0x000A7325 in BOTH boots (identical bytes 25 73 0a 00, zeros after).
sces's 0x80020040 at gp+0 is therefore a genuine one-word INSERT in
the sces .sdata pool, not a shifted mirror of an slps word - the
per-region slot maps are mandatory, exactly as banked.

Gates: docs-only; 8/8 verify GREEN untouched; matched 174; ratchets
365/0. No carve-side action.

Next queue:
1. VAG record field decode: Call 10's attr source (0x801150F0 +
   (0x8012A87B_byte*16 + a2)*0x20) against the real 0x20-B records at
   VH+0x820+i*0x20 - pin pitch/vol/pan/ADSR offsets; identify the
   template records' role (the 0x7440 B between the real records and
   the size table).
2. func #56 tail semantics: whether VAG 62 (entry[count] = 0x3B2) is
   registered anywhere; the 0x80043490 helper (Call 10's first jal);
   the re-open path at 0x8002C360 (Call 5 wrapper variant with
   explicit id).
3. .sdata: build the per-region gp-relative slot maps; identify what
   0xA7325 (gp-4, both boots) and 0x80020040 (sces gp+0) reference.
4. Lanes stay theirs (GSD round-5, setIntr/startIntr/trapIntr); BIG
   de-frame coordination-gated; runtime gate-family blocked.
## 2026-10-16: coddog trial - PSX mipsel WORKS, region-pair similarity baselined

ethteck/coddog (coddog-cli 0.6.3, `cargo install --git ... coddog-cli`) runs on
this project unmodified: it reads the per-target build .elf symtabs through the
new root decomp.yaml (decomp_settings format; its 0.0.10 parser REQUIRES the
`map` path field even though nothing reads it). All PSX skepticism resolved -
MIPS el works fine.

compare2 on the four same-program region pairs (-t 0.5, reports in
build/coddog.*.txt, git-ignored):

  pair                    pairs   100.00%   95-99.99%   80-94.99%   <80%
  slps_00270-sces_00269     698       97        195          62       344
  mainmenu_jp-mainmenu_eu  1845      149        773         216       707
  g3_jp-g3_eu              1453      180        461         188       624
  g3org_jp-g3org_eu        1763      209        675         215       664

Reading: 635 exact pairs = match-once-transplant (setIntrVSync rollout,
automated); ~2100 at 95-99.99% = the imm-diff class, one C source + per-target
externs usually covers both regions; <80% mixes true region divergence
(screen-title composer class) with aligner mispairings, so treat that bucket
as untrusted at -t 0.5.

cluster finds in-binary twins: slps_00270 has 43 groups, 23 with 3+ members
(several are already-curated LIBGS/LIBSND members shipped twice). Needs a TTY
for its version picker (`printf '\n' | script -qec "coddog cluster" /dev/null`).

Workflow adopted: JP stays the matching target; after each JP match, its EU
counterpart comes off this report - exact pairs get the same C renamed,
95-99.99% pairs get the imm-diff treatment before a probe.

## 2026-10-16: unit judge - the per-unit candidate screen (the decomp.wtf loop, native)

tools/judge_unit.py compiles ONE c unit through the build's own pipeline and
judges its bytes against the retail baseline slice: cc.sh -S ->
tools/stage_c.py -> mipsel-as (build ASFLAGS), then a MINI LINK of the unit
alone at its retail VA (yaml offset IS the baseline file offset; VA =
0x80020000 + offset - 0x800) with the build's two-pass undefined-symbol
resolution, then objcopy --only-section and word compare with capstone
disasm of the first diffs. ~0.1 s/unit; all 16 mainmenu_jp units in 1.6 s
vs ~53 s per full build. ~26x faster feedback for the match-edit loop.

Made possible by extracting build.sh's three inline Python heredocs into
shared tools (verbatim, so build and judge cannot drift): gp_flags.py
(gp rewrite inputs), stage_c.py (the .text rename + gp_rel rewrite),
undef_syms.py (two-pass symbol resolution). build.sh calls them; the judge
reuses them. Verdicts are screens, never acceptance: whole-image
`make verify` stays the oracle; the judge cannot see other units or the
link layout.

Judge-only fix worth banking: judged alone, a unit lacks the objects that
define its neighbours (func_8002C478's extern state_block_N jump targets
are defined by a data row's labels in the full link); left undefined, the
suffix-regex fallback resolves state_block_0 AT 0x0. The judge therefore
preloads every config/symbols.<TARGET>.txt entry as a linker-script prelude
to both passes; script assignments cannot override object definitions, so
the full build is unaffected.

Validated: 104/104 c units EXACT across all 8 targets (the judge agrees
with the green oracle everywhere); negative control (>= for !=) flags
slt/bnez rewrite, size delta, and per-word diffs with disasm.
## 2026-10-16: the SE.VH tone records decode - one real tone per VAG, 1-based VAG
## numbering closes the +1 entry, region divergence is 13 pitch bytes + 22 sizes

Fresh per-sector SE.VH;1 both regions (JP 0x8620, EU 0x7E20 - the fsize-law
holds), Psy-Q 3.3 LIBSND.H pulled (sozud/psy-q sparse INCLUDE; VabHdr/ProgAtr/
VagAtr structs) and every field checked against the real bytes.

CORRECTION - the VAG area is NOT packed records. It is the standard blocked
layout: count blocks of 0x200 = 16 VagAtr slots each, block v at
0x820+v*0x200, slot t at +t*0x20. Call 10's runtime formula
(byte@0x8012A87B*16 + a2)*0x20 IS block*16+tone addressing - the runtime
already knew. The 2026-10-15 "packed at 0x820+i*0x20" reading was an aliasing
artifact: packed slot i is block i/16 slot i%16.

EVERY BLOCK'S SLOT 0 IS A REAL TONE (62/58 real records, not one). All are
identical except two link halfwords:
  vol=127 pan=64 center=84 shift=0 min=0 max=127 adsr1=0x80FF adsr2=0x1FC0
  (prior/mode/vib/por/pb all 0; B1 B2 sentinels @0x0E/0F, C0..C3 @0x18..1F)
  u16@0x14 (VagAtr.prog) = block index p = parent program
  u16@0x16 (VagAtr.vag)  = p+1 = the VAG that tone plays
So the bank is a strict 1:1 chain: program p (tones=1) -> tone at block p
slot 0 -> VAG p+1. Psy-Q field names fit with no reinterpretation.

TEMPLATE SLOTS (the other 15 of each block) measured, both regions: 14 zero
bytes, B1 B2 @0x0E/0F, adsr 0, u16@0x14 = the block's own index, 0 @0x16,
C0 00 C1 00 C2 00 C3 00 @0x18..1F. JP 930/930, EU 870/870 slots match this
form exactly. Role: the file ships the FULL runtime tone table pre-filled
(same tool wrote real + template records - these are not Psy-Q zero-fills),
so SsVabOpenHead's copy needs no per-slot construction; only the program
records' link placeholders (+8 = ffffffff, +0xC/+0xE = ffff) get patched.

VAG NUMBERING IS 1-BASED - the count+1 size-table mystery closes:
  entry[k] of the size table = VAG k's body size, k = 1..count;
  entry[0] = 0 is the NULL VAG, not a VAG. There is no 63rd VAG and no
  out-of-band registration path: VAG 62 IS block 61 (its tone's vag field =
  62), inside func #56's 62-loop. The 2026-10-15 open item ("is VAG 62
  registered anywhere?") is CLOSED - the "+1 entry" was the null entry[0].
  Verification: sum(entries[0..28])<<3 = 0x39130 = VAG 29's body offset in
  both regions (matches the VB first-diff witness); totals sum to the VB
  sizes exactly. The 0x3B2 tail sample is VAG 62 (JP, VB 0x606C0) / VAG 58
  (EU, VB 0x5C690) and is BYTE-IDENTICAL between regions (one shared SFX).
  The earlier "JP-only VAGs 58..61" list was entry indices under the old
  numbering; corrected below.

REGION DIVERGENCE MAP, complete (file side, every byte accounted):
- Program table: every record differs in prior/mode (bytes 2/3) ONLY -
  JP 00/36, EU 7f/ff, real and template records alike. EU programs 58..61
  are tone-less templates (tones=0) where JP 58..61 are real programs.
- VAG area: 13 differing bytes total, ALL in slot-0 real records, columns
  center (0x04) / shift (0x05):
    VAG 17: JP center 84 / EU 60      VAG 30: JP 60 / EU 84 (mirror)
    VAG 46: JP 84 / EU 60 (mirror)
    VAGs 54..58: JP center 74 + shift 84 / EU center 84 + shift 0
  (a transpose: JP detunes the note and bends it a semitone, EU plays the
  plain center - the three mirrors suggest the JP bank is the odd one out)
- Size entries: VAGs 29..48, 57, 58 differ (22 common entries); VAGs
  59..62 JP-only (0x4B6/0x4F0/0x2C6/0x3B2 <<3 = 0x9030/0x9380/0x7180/0x6C80
  bytes). VAG 58 is common but region-sized (608 vs 946).

FIELD-OFFSET PINS for VagAtr as this file uses it (all verified against
nonzero data, not inferred): vol@0x02, pan@0x03, center@0x04, shift@0x05,
max@0x07, adsr1@0x10, adsr2@0x12, prog@0x14, vag@0x16; prior/mode/min/
vibW..pbmax are 0 in every record so their offsets are Psy-Q-named, not
pinned. Call 10's "attr bytes 0..9" = prior..vibT: the game reads the
static voice shape (vol/pan/center/min/max/vib) per tone at load.

Program-table template census: JP templates 62..127 = 00 00 00 36 00...,
EU templates 58..127 = 00 00 7f ff 00... - the mode bytes differ per region
even in padding, so the VH builder was run per region, not shared.

Gates: docs-only (analysis repo-external: scripts/vag_record_decode.py,
vag_region_diff.py; psyq headers re-pulled by the sparse recipe); no carve
action; 8/8 verify GREEN untouched; matched 174; ratchets 365/0.

Next queue:
1. func #56 tail semantics (previous queue item 2, mostly superseded): the
   re-open path at 0x8002C360 (Call 5 wrapper with explicit id) and the
   0x80043490 helper (Call 10's first jal) - now against a fully decoded
   tone table.
2. .sdata per-region gp slot maps (queue item 3): gp-4 = 0xA7325 settled;
   what 0x80020040 (sces gp+0) references + the full slot map.
3. Call 9/10 runtime tables: 0x80114F48 (VH bases), 0x801150F0 (tone table
   base) and 0x8012A87B/0x8012A894 (current-VAB byte + gate array) - how
   the runtime reorganizes the blocked table after the copy.
4. Lanes stay theirs (GSD round-5, setIntr/startIntr/trapIntr); BIG
   de-frame coordination-gated; runtime gate-family blocked.

## 2026-10-16: the weave law closes at 100 percent - baselines are a pure
## re-layout; true-EXE SHA-1 witnesses banked; the boots' .sdata slot maps decode

The missing-tail witness unit ran with the discs fresh (per-sector EXEs for
all 8 targets; scripts tail_witness.py, weave_law_test.py, sdata_slot_map.py
- repo-external).

THE WEAVE LAW, proven at 100 percent on all 8 targets: wherever the
committed baseline HAS a byte, baseline[k*2352+j] == true[k*2048+j] exactly
(2048-B user data per disc sector + the 304-B sync/header/EDC/ECC overhead
woven between; zero violations across ~2600 sectors). The baselines are a
PURE DETERMINISTIC RE-LAYOUT of the true EXEs - the "corruption" is
placement, not content. Consequences: the drift at true offset T is
(T>>11)*304 in file space; the de-frame recipe for baseline-present bytes
is mechanical (take 2048 of every 2352); no information is lost in the
baseline-present region.

THE MISSING TAILS (quantified; disc-only bytes): the contiguous read ran
out of file before the true sectors did, so every baseline ends early:
  slps/sces:    true 0x3DDF0..0x47000 missing (37392 B = 1 partial + 17
                full sectors; sector 123 is 1520/2048 present)
  mainmenu_jp:  0x94800..0xAA800 (90112 B, 44 full)
  mainmenu_eu:  0x94800..0xAB000 (90288 B, 44 full + 1 partial)
  g3_jp:        0x7A000..0x8C800 (74176 B)  g3_eu: 0x7A800..0x8D000 (74480)
  g3org_jp:     0x85800..0x99800 (81168)    g3org_eu: 0x86000..0x9A000 (81472)
Content: boots' region = the 8-B pattern 00 00 00 00 02 00 00 fe with the
.sdata windows embedded (90c65b4's dumps); mainmenu_jp head = zeros,
mainmenu_eu head = a real word table (45 f9 81 0e 4b f9 84 0e ...);
g3_jp = 06 00 1f 7c pattern; g3_eu = mixed real words + pattern; g3org
both = palette-like data. Every tail ends in >= 0x40 zero bytes. File-size
law: ISO size = 0x800 + t_size EXACTLY (zero pad); EU game modules are
each exactly one 2048-B sector larger than JP. Correction: the earlier
"every byte above payload 0x3D5F0" for the boots -> measured 0x3DDF0.

TRUE-EXE SHA-1 WITNESSES (the de-frame transition's future oracles; the
committed config/sha1 oracles remain the framed pipeline's gate and were
re-verified 8/8 this window):
  slps fa9474b4e6ecf08e0bfc182fee776cf71f6d8195
  sces 06b4bda68dce0f3734cfb7cbb76913a6e7fa2dc9
  mainmenu_jp d637286a60e36dfeee10c0441509c98b2f952d48
  mainmenu_eu f9f29eebb419b5e957ce2389d33caeedbb93685e
  g3_jp 994a680cd139069404e5c6d6c51d3796a728f2ec
  g3_eu 39030a759e8462575b709f77eed1050f7bbaa572
  g3org_jp 2b2a42250b9fe8849bbd791515ce341a678ddef0
  g3org_eu 01b37b4e01afe69acd2a46e69359dadd4a20877b

THE BOOTS' .sdata SLOT MAPS (true bytes; runtime gp = 0x8006632C slps /
0x80065FC4 sces; windows [gp, gp+0xD0) / [gp, gp+0xD4)):
- ALIGNMENT LAW: 52/52 pairs, sces[X] == slps[X-4] for every X >= 4. The
  sces window is the slps window with ONE word inserted at gp+0
  (0x80020040) and 4 extra zero bytes at the tail; all other content is
  byte-identical. The "genuine one-word INSERT" call is proven.
- CORRECTION to the "payload gp-4 = 0xA7325" note: gp-4 is 0 in both
  boots. 0x000A7325 sits at gp-0x10 (slps payload 0x4631C, sces 0x45FB4)
  and IS THE ASCII STRING "%s\n\0" (25 73 0a 00) - a printf format, not a
  pointer. Three more copies live in the boots' early string pool (slps
  payload 0x11BF/0x142C/0x14AE - odd offsets, string region, not code).
- Content map (common; slps frame; sces = +4):
  gp+0x00  u32 1          (scses slot replaced by the 0x80020040 insert =
                           pointer to the boot string table @payload 0x40:
                           "\W16.DAT;1", "VOICE=%d", "%s(%d):I" ...)
  gp+0x04  rank-name table, 8-B slots: "NONE" "FRANK" "REIKO" "JOHNSON"
           "SHARK" "GHOST" (ends gp+0x34)
  gp+0x34  u32 1, 0, 1, 0, 0x003C0000, 0
  gp+0x4C  "NONE" (second copy)
  gp+0x54  u32 0xffffffff, then zeros to gp+0x70
  gp+0x70  seat-label suffixes, 8-B slots: " (1)" " (2)" " (A)" " (B)"
           " (C)" " (D)" (ends gp+0xA0)
  gp+0xA0  "bu00:\0" memory-card slot path (slps gp+0xA0 / sces gp+0xA4 -
           the member-void landing prediction confirmed exactly)
  gp+0xA8  u16 0x8169 zero-padded = Shift-JIS fullwidth （
  gp+0xAC  u16 0x816A zero-padded = Shift-JIS fullwidth ）
  gp+0xB0  u32 0x2A (42), then zeros to the window end (sces: +4 zeros)
The member-void gp+0xa0..0xb0 reads = memory-card path + the fullwidth
paren pair + the 42. The window is file-initialized .sdata exactly as the
load model concluded: rank display + memory-card strings for the boot.

Gates: docs-only (true-EXE hashes are hashes, not extracted assets; the
missing-tail bytes stay disc-derived per the no-commit rule); no carve
action; 8/8 verify GREEN untouched; matched 174; ratchets 365/0.

Next queue:
1. Boot CRT0 follow-ups now unambiguous: who reads gp+0 (1 / the 0x80020040
   string-table pointer), the gp+0x34..0x4C consts, and which call prints
   via the gp-0x10 "%s\n" format. The 1642-era "pointer at gp-4" question
   is closed (it is a string, one word earlier than thought).
2. The de-frame transition's evidence base is now COMPLETE (weave law +
   missing-tail extents + true-EXE oracles); the decision remains
   coordination-gated - do NOT start unilaterally.
3. Call 9/10 runtime tables (0x80114F48 / 0x801150F0 / 0x8012A87B/894) -
   how SsVabOpenHead reorganizes the blocked tone table; re-open path
   0x8002C360; 0x80043490 helper.
4. Lanes stay theirs (GSD round-5, setIntr/startIntr/trapIntr, coddog
   transplant); runtime gate-family blocked.

## 2026-10-16 late: the boots' window readers decode - gp+0 is read exactly once (sces only, the string-table pointer), the "consts" are live rank-cluster state, gp-0x10 is the InitPAD version buffer

Queue item 1 (CRT0 follow-ups). Both boots re-extracted per-sector from the
re-fetched CHDs (sha256 verified; true-EXE SHA-1s match the banked
witnesses: slps fa9474b4, sces 06b4bda6). Scripts repo-external:
boot_gp_scan.py, boot_window_scan.py, boot_window_sweep.py,
boot_gp_rel_scan.py. TOOLING WARNING for future windows: capstone 5 nests
MEM operand fields under `.mem` (`.mem.base`/`.mem.disp`) - flat `.base`
raises, and an `except: pass` silently empties the result set (two early
"zero gp-relative ops" scans were exactly this artifact; a third scan
conflated `w & 0x3F` with the I-type immediate). Every count below is from
the fixed, capstone-detail scanners.

FINDING 1 - gp+0 IS read, exactly once, sces only. sces 0x800222DC
`lw $a0, ($gp)` loads the inserted word (0x80020040 = the boot string-table
pointer: "VOICE=%d", "%s(%d):Invalid mission value in set_game_info()",
"gameinfo.c", ...) and passes it to 0x8002d5b8, a parser over the table
(calls 0x8002d620, result compared against a -1 sentinel). slps has ZERO
gp+0 readers (no gp-relative op at disp 0, no %hi/%lo materialization, no
data pointer): its u32 1 is dead data. slps consumes the SAME string table
via immediates instead: main's tail 0x800218E4 materializes 0x80020040
("VOICE=%d") and calls the A0#0x51 (sprintf) thunk 0x8002f92c with
0x801FFF00; 0x80021A1C/21DE4/21F08 materialize 0x80020018/0x80020028. So
the EU one-word insert = the string-table pointer promoted into .sdata (EU
codegen routed the table through a variable; JP used immediates). The
alignment law sces[X] == slps[X-4] stays exact for every other word.

FINDING 2 - the window has REAL gp-relative traffic; the de-frame item's
"no gp-relative access" premise is refuted. slps: 114 gp-relative mem ops
(110 in-window-band), sces: 111. Every slps op at +X has its sces twin at
+X+4 - the alignment law confirmed at INSTRUCTION level, 110/111 (the +1
is the sces-only gp+0 read). Reader map (slps frame; sces = +4):
  gp+0x04/0x08  rank names read as data: lw 4($gp) = "NONE"; the GHOST
                copy is lw 0x2c($gp) + lh 0x30($gp) (0x80024BA4/8) - the
                compiler knew these .sdata objects and used $gp directly
  gp+0x34..0x48 LIVE u32/u16 state of the rank-display cluster (NOT
                read-only consts): dedicated leaf setters 0x80024EE8/EF4
                (*(gp+0x34) = 0/1), 0x80024F04/F10 (*(gp+0x3C) = 0/1);
                rw traffic 0x80024F20..0x80025Axx; u16s at +0x40/+0x42/
                +0x44/+0x46/+0x48 - the file's 0x003C0000 u32 initializer
                is the u16 pair 0x0000/0x003C at +0x44/+0x46
  gp+0x54       rw (0x80025F28..0x80026290; 0xffffffff sentinel init)
  gp+0x68       u16 counter rw (0x800260FC..)
  gp+0x6A/6C/6E three u16 counters (0x80028BB0/4/8 clears; lh/sh pairs;
                slti 0x2710 = 10000 cap, 0x28 = 40 clamp at 0x80028BC4..)
  gp+0xE0       .sbss (beyond window end) rw
The content map's "zeros" zones are runtime state arrays, not padding.

FINDING 3 - gp-0x10 "%s\n" is the InitPAD version buffer (closed). 0x8004AB68
(sces mirror 0x8004A79C) = boot-local InitPAD(buf1, 0x22, buf2, 0x22): its
caller 0x80025C4C fills two 0x22-byte (34 = the Psy-Q pad buffer size)
buffers at 0x80079304/0x8007932C with 0xFF, then calls InitPAD, then
0x8004ac30 (StartPAD-shaped) + 0x8002f93c. InitPAD strcpy's (A0#0x3F thunk
0x8002dc10) "PS-X Control PAD Driver  Ver 3.0" (string at payload 0x462F0
slps / 0x45F88 sces; pointer loaded from 0x800662EC / 0x80065F84) INTO
gp-0x10 - the "%s\n" file initializer is dead data overwritten before any
use; zero other references to gp-0x10 in either boot. InitPAD also saves
its 4 args to 0x80066570/74/80/84 (pad buffer descriptors) and zeroes the
0x80066560 flag (slps; sces 0x80066208 via stub 0x8004a938). The other
three "%s\n" copies (payload 0x11BF/0x142C/0x14AE slps; 0x119B/0x1438/0x14BA
sces - odd offsets, the gameinfo.c string pool) are the real printf-format
copies. A0 thunks pinned: 0x8002dc10 = A0#0x3F strcpy, 0x8002dc00 =
A0#0x15 strcat, 0x8002f92c = A0#0x51 sprintf (the $t1/$t2 convention).

Gates: docs-only; matched 174; ratchets 365/0; 8/8 verify GREEN untouched
(no build-side file touched).

Next queue:
1. Rank-display cluster semantic decode (slps 0x80023BB8..0x80025Axx): the
   gp+0x34..0x48 fields' game meaning (the u16 counters' 10000-cap/40-clamp
   pair suggests a ratio/pct pair feeding the rank screen).
2. sces 0x8002d5b8 string-table parser decode (what it looks up; the
   "VOICE=%d" consumer path).
3. Call 9/10 runtime tables (0x80114F48 / 0x801150F0 / 0x8012A87B/894) -
   how SsVabOpenHead reorganizes the blocked tone table; re-open path
   0x8002C360; 0x80043490 helper.
4. Lanes stay theirs (GSD round-5, setIntr/startIntr/trapIntr, coddog
   transplant); BIG de-frame coordination-gated; runtime gate-family
   blocked.

ADDENDUM (same window): the gp+0 consumer decodes as the FLOAD path. sces
0x8002d5b8 = retry wrapper (call 0x8002d620(strtab) until it returns
!= -1, up to 0x0FFFFFFF tries; exhaustion -> error glue with the string at
payload 0xA80 = "FLOAD:fault!\n"). 0x8002d620 = the load prep: if
*(gp+0xD0) != 0 first calls 0x8002e644 (teardown of the previous load);
0x8003b36c(sp+0x18, strtab) parses/loads; the value at sp+0x1C is rounded
UP to a 2048 multiple (+1 sector if exact - the classic CD-read rounding);
0x8002d9d4(0x00066000) allocates; the rounded size lands in *(gp+0xD0);
zero -> "FLOAD:fault!\n" path. So gp+0xD0 - the sces window's "4 extra
zero bytes" - is the loaded-file size state, and its slps twin is gp+0xCC
(the alignment law's +4 again). The string pool both loaders consume sits
at payload 0x10.. in each boot: "EXE;1", "file not found\n", a 6-entry
pointer table at payload 0x20, then "\W16.DAT;1" and "VOICE=%d". Both
boots run the SAME loader; slps passes the table pointer as immediates
(main tail), sces through the .sdata variable at gp+0. The one-word insert
is fully explained: no content difference, only pointer routing.

## 2026-10-16 late: the SE.VH runtime tables decode - the "reorganization" is
## pointer tables + two patched fields, and the docs' 0x8012A87B/94 were hi/lo
## composition errors

Queue item 3. All runtime-table work is static analysis of the boots' true
payloads (scripts rt_xref.py, dump_dis.py, gate_census.py, repo-external;
manual MIPS-I field decode + capstone context - no .mem nesting traps). The
libsnd code is WORD-IDENTICAL between slps and sces except the four data
immediates (proven by word-diff at the Call 9 twin, code delta +0x1C), so
every semantic below is region-independent; only the BSS addresses move.

ADDRESS CORRECTIONS (both docs' values were composed without the %hi sign
adjustment: lui 0x8012 + addiu 0xA894 = 0x80120000 - 0x576C, not
0x8012A894):
  slps: gate array 0x8011A894 (not 0x8012A894), cur-block byte 0x8011A87B
        (not 0x8012A87B)
  sces: gate array 0x80119E10, cur-block byte 0x80119DF7
All other documented addresses (0x80114F48/0x801150F0) had positive %lo and
were already correct. sces moves the whole cluster by roughly -0xA7C (each
table pinned individually, shifts -0xA78..-0xA88, non-uniform).

THE FULL PER-VAB TABLE CLUSTER (slps; sces twin in parentheses) - Call 5
(0x80044174 parser) fills ALL of these, none existed in the docs before:
  0x8011A894 (0x80119E10)  gate[16] bytes: 0 free / 1 head-claimed / 2 fully
                           open
  0x80114F48 (0x801144CC)  VH base pointer per VAB (POINTER store - no copy;
                           the "runtime copy" premise is refuted)
  0x80114EE0 (0x80114464)  VH+0x20 pointer per VAB (program table)
  0x80114F8C (0x80114510)  VH+0x820 pointer per VAB (VAG area)
  0x8011C3A8 (0x80119228)  size-table pointer per VAB (VH+0x820+count*0x200)
  0x8011C360 (0x801191E0)  VB RAM base per VAB (from the 0x800445BC allocator
                           or the explicit-base variant)
  0x8011C31C (0x8011919C)  VB total bytes per VAB
  0x80115070 (0x801145F0)  stride u16 (0x40 ver<5 / 0x80 ver>=5) - global
  0x8011C35C (0x801191DC)  open counter u16 (increment on claim, decrement
                           on every bail past the claim - a refcount)
CURRENT-CONTEXT GLOBALS (single slots, written by the select helper only):
  0x801150F0 (0x80114668)  cur VAG-area pointer - 40 readers across the whole
                           voice/seq machinery, ONE writer (helper)
  0x801150E8 (0x80114670)  cur VH pointer - also written by Call 9
  0x801150A0 (0x80114620)  cur program-table pointer
  0x8011A875/87A/87B (0x80119DF1/DF6/DF7)  cur vab / cur program / cur block
                           bytes
THE 0x80043490 HELPER = the select (SsVabSelect-shaped): (vab_id, program);
requires gate==1 and program < stride/0x10... (program < stride count),
loads VH/PROG/VAG pointers from the per-VAB tables, publishes the five
context globals, and sets cur-block = PROG[program].+8 - THE RUNTIME-PATCHED
SEQUENTIAL PROGRAM ID.

CALL 10'S FORMULA BYTE DECODED: (byte@0x8011A87B*16 + a2)*0x20 indexes the
cur VAG area = block*16+tone addressing because the byte is the +8 field
Call 5's patch loop wrote (sequential index among tone-ful programs), which
for this strict 1:1 bank equals the block index. The runtime "already knew"
the blocked layout because its own patcher wrote the block number into the
program record. Call 10 (0x80044CE0): gate==1 check, jal 0x80043490(vab,
program), then copies VagAtr bytes 0..9 from cur VAG area +
(cur_block*16+tone)*0x20 to the out pointer. Call 9 (0x80044BFC, leaf):
gate==1, loads VH_BASES[vab], copies VabHdr words +0/+4/+8, halfwords
+0x12/+0x14/+0x16, bytes +0x18..0x1B to the out struct, storing the VH
pointer into the cur-VH global as a side effect.

THE PROGRAM-RECORD PATCH LOOP DECODED (Call 5, 0x800444CC..0x80044558): the
size-table read pulls the WHOLE last block (256 u16 entries) into a stack
array, <<3 each (ver>=5), total capped by the 0x80000 sltu check; then for
i in 0..count-1: prog[i/2].+0xC (even i) / .+0xE (odd i) =
(vb_base + inclusive cumulative size thru entry i) >> 3. With entry[0]=0
and 1-based VAGs this puts VAG p+1's body start into program p's tone-0
offset field - exact consistency with the file-side chain, no off-by-one.

GATE STATE MACHINE (all sites classified, 19 total): 0x80040400 loop =
SsVabInit (open counter + all 16 gates cleared); Call 5 claims 1, on full
success (VB registered, patch loop done) sets 2, every bail past the claim
clears its byte and decrements the open counter; Call 9 / Call 10 / helper
/ 0x8003E518 (gate==1-checked VB-base getter) / 0x80048CC8 / 0x800495E0
(the seq-player attr readers) all REQUIRE gate==1; 0x8003CD90 checks ==2
and reclaims to 1 (0x8003CECC) after teardown work; 0x80044B84 = the
reclaimer for the re-open path (gate==2 -> 1, returns vab; else -1).

THE RE-OPEN PATH (0x8002C318 function; the 0x8002C360 jal) decoded end to
end: teardown helpers (0x800436D8, 0x800438D8(1), 0x80043CE8,
0x80044F20(0x7F,0x7F)), then jal 0x80044140 = the THIRD Call 5 wrapper
(explicit VB base: a2 flag=1 skips the allocator, a3 = base) with a0 =
*(0x80016604), a1 = *(0x80016600) (the VAB id), a2 = *(0x8001EC24) - a
stashed copy of VB_BASE[vab] that the SE-walk function's tail saved via
the 0x8003E518 getter; then 0x80044B84 flips the gate 2->1 and Call 9
re-fetches the metadata (its result is actually checked here, unlike the
first walk). The wrapper trio at 0x800440D8/0x8004410C/0x80044140 = the
same parser with (flag, base) = (0, alloc) / (1, caller) / (1, caller).

BIG-PICTURE ANSWER for the queue item: the runtime does NOT reorganize the
blocked tone table. SsVabOpenHead leaves the VH bytes in place, stores six
per-VAB pointers, patches program records +8/+0xC/+0xE only, and all later
access goes through the select helper's current-context globals with the
block*16+tone formula. The "0x801150F0 tone table base" is a single global
(the current VAB's VAG-area pointer), not a table.

Gates: docs-only; no carve action; matched 174; ratchets 365/0; 8/8 verify
GREEN untouched (no build-side file touched). Disc assets re-provisioned
this window first (CHDs re-fetched, sha256 verified; all 8 true-EXE SHA-1
witnesses re-matched), so the analysis ran on the same bytes the banked
witnesses pin.

Next queue:
1. The seq-player attr readers (0x80048CC8/0x800495E0 clusters) now have
   their key decoded (cur VAG area + cur block byte) - a natural follow-up
   for the audio lane.
2. The 0x8003CD90 function (gate==2 checker, indirect-called - no direct
   jal): find its dispatch site (function-pointer table) and identify it.
3. Lanes stay theirs (GSD round-5, setIntr/startIntr/trapIntr, coddog
   transplant); BIG de-frame coordination-gated; runtime gate-family
   blocked.

## 2026-10-16 late: the "indirect-called gate==2 checker" is SsVabTransBodyPartly -
## direct-called from the chunked VB loader; the gate labels flip; the docs' sces
## VB-table twins were refuted by two library members' own immediates

Queue item 2 of the SE.VH runtime-tables window. All analysis on the boots'
per-sector true payloads (CHDs re-fetched a third time, sha256 exact; true-EXE
SHA-1s re-matched: slps fa9474b4, sces 06b4bda6). Scripts repo-external:
cd90_dispatch.py, cd90_xref2.py, cd90_caller.py, cd90_full.py.

THE PREMISE WAS A CARVE-VIEW ARTIFACT. Static searches for 0x8003CD90 in the
true payloads: pointer word 0 hits, lui/addiu materialization 0 pairs (both
the addiu hi=0x8004 idiom and the ori hi=0x8003 idiom), j 0 hits - but the
jal word scan hits: slps 0x8002C9A8 jal 0x8003CD90 (word 0x0C00F364), sces
0x8002C7C4 jal 0x8003CB84. "No direct jal" was true only in the framed view:
the caller sits in the game-side region whose carve addresses drift (slps
drift 0x44E0 at the 0x8004xxxx depth), so the carve-decoded jal target
matches nothing - the same poisoning that hides the twin islands, now
confirmed on the caller side too.

THE CALLER (slps 0x8002C840..0x8002CA18, sces twin shifted -0x1E4 at the
call site) IS THE CHUNKED VB BODY LOADER: a0/handle in, reads the size at
stack+0x14 of a 0x8003b578-filled struct, s2 = ceil(size/2048) = sector
count; allocates a 0x40000 (256 KB = 128-sector) buffer via 0x8002dbe0
(clears it via 0x8002dbf0); walks the CD read cluster (0x80039238 /
0x80038d34 / 0x800391b8 / 0x80039198 poll) one 0x80-sector chunk at a time
with s0/s3 counting sectors; per chunk: a1 = 0x40000, or the tail remainder
(size & 0x3FFFF for the last chunk); jal SsVabTransBodyPartly(buffer, a1,
vab); then polls 0x80045464(0) until nonzero (wrapper -> 0x80045490, which
dispatches on the transfer-mode global slps 0x80065940) - wait for the SPU
write to drain before feeding the next chunk. Returns the last
TransBodyPartly result (s16); negative -> bail with 0x8002eaa0(handle).

IDENTITY: the callee is psyq libsnd's SsVabTransBodyPartly, VERBATIM. The
committed census already carried it: config/sdk_anchors.txt rows
"SsVabTransBodyPartly VS_VTBP LIBSND unique", slps framed 0x80041270 / sces
framed 0x80041064, extent 0x170. Byte-check: census bytes == the true-runtime
functions exactly (0x16C code + 4 zero pad = 0x170 member extent). True
runtime addresses: slps 0x8003CD90, sces 0x8003CB84 (framed census address -
drift: 0x44E0 both regions at that depth). The member is word-identical
across regions modulo references: 19/91 words differ, every one an
address-bearing immediate (tables, globals, jal/branch targets).

SEMANTICS (slps; sces = same code, shifted refs): (addr a0, size a1, vabid
a2). (u16)vabid >= 0x11 -> -1. gate[vab] != 2 -> -1. First chunk (the
transfer-remaining u32 at 0x80065934 == 0): cur-transfer-vab u16 at
0x80065938 = vab, remaining = VB-total[vab] (0x8011C31C), 0x8003cf00(0)
stores the transfer-mode globals (0x80065940 / 0x80065DCC), and
0x8003e414(VB-base[vab] from 0x8011C360) sets the SPU transfer start addr
(census: SpuSetTransferStartAddr S_STSA / _spu_setInTransfer S_IT /
SpuWritePartly S_WP all in the slps cluster). Wrong vab mid-transfer -> -1.
Size clamped to remaining; 0x8003e450(1); 0x8003e48c(addr, size) = the SPU
write; remaining -= size. remaining != 0 -> return -2 (FEED ME MORE).
Completion: cur-transfer-vab = -1, remaining = 0, gate[vab] = 1 (the store
at 0x8003CECC), return vab. The caller's loop reads exactly this protocol:
-2 -> next chunk, >= 0 -> done.

GATE MACHINE REFINED (three members anchor it now): SsUtGetVBaddrInSB
requires gate==1 and returns VB_base[vab]; SsVabTransBodyPartly requires
gate==2 and completes to 1; the re-open reclaimer 0x80044B84 flips 2->1.
Coherent values: 0 = free, 2 = head parsed + VB base registered (body
transfer armed), 1 = READY (what every reader requires). The runtime-tables
section's labels ("1 head-claimed / 2 fully open") are inverted for these
two values, and its "reclaims to 1 (0x8003CECC) after teardown work" was a
misreading: 0x8003CECC is the transfer-COMPLETION store; the function tears
nothing down. (Call 5's transient claim writing 1 mid-parse remains as
decoded - value collision with READY, harmless in the single-threaded boot.)

SCES TWINS RE-PINNED FROM MEMBER IMMEDIATES (two independent members agree):
  VB-total per VAB   slps 0x8011C31C -> sces 0x8011C094   (shift -0x288)
  VB-base per VAB    slps 0x8011C360 -> sces 0x8011C0D8   (shift -0x288)
  gate array         slps 0x8011A894 -> sces 0x80119E10   (doc confirmed)
  transfer remaining slps 0x80065934 -> sces 0x800655C4   (shift -0x370)
  cur-transfer vab   slps 0x80065938 -> sces 0x800655C8   (shift -0x370)
CORRECTION: the runtime-tables section's parenthesized sces twins for
VB-total/VB-base (0x8011919C / 0x801191E0) are REFUTED - SsVabTransBodyPartly
and SsUtGetVBaddrInSB both read 0x8011C094/0x8011C0D8 in sces, and the
refuted values also sit outside that section's own claimed -0xA78..-0xA88
shift window. That section's sces column needs a rebuild from member
immediates (its Call 5 derivation must be re-run against them).

NAMED AS A SIDE EFFECT: the doc's "0x8003E518 (gate==1-checked VB-base
getter)" is SsUtGetVBaddrInSB - census UT_GVBA row (slps framed 0x80042D88)
byte-matches true 0x8003E518 exactly; sces twin true 0x8003E0F0 (framed
0x80042960). Also pinned: the poll wrapper slps 0x80045464 -> 0x80045490,
sces 0x80045480.

Gates: docs-only (hashes and addresses, no extracted assets); no carve
action; matched 174; ratchets 365/0; 8/8 verify GREEN untouched. No curated
name adoption performed - the boots' libsnd/libspu adoption rows belong to
the sdk lane; the true-runtime addresses they need are banked here.

Next queue:
1. The runtime-tables section's sces column rebuild: Call 5's sces twin must
   store VB-total/VB-base at 0x8011C094/0x8011C0D8 (and the size-table
   pointer / VB RAM base rows shift by -0x288 too, per the two members) -
   re-derive from the parser bytes, not from the refuted composed values.
2. The chunked loader 0x8002C840 (slps) deserves its own decode: the CD read
   cluster 0x80039238/0x80038d34/0x800391b8/0x80039198, the 0x8002dbe0/
   0x8002dbf0 allocator pair, and who calls the loader (one jal away from
   the SE walk's VB step).
3. The setter 0x8003cf00 + poll 0x80045490 pair: transfer-mode globals
   0x80065940/0x80065DCC (slps) - sces twins unpinned.
4. sdk lane: boots' libsnd/libspu census rows now have true-runtime addresses
   (drift 0x44E0 at the 0x8003C..0x8004B depth) - adoption ready when the
   lane picks it up.
5. Lanes stay theirs (GSD round-5, setIntr/startIntr/trapIntr, coddog
   transplant); BIG de-frame coordination-gated; seq-player attr readers
   (0x80048CC8/0x800495E0) per the previous queue.

## 2026-10-16 late: the runtime-tables sces column rebuilds from the sces
## parser's own stores - the C-cluster shifts -0x288, the pointer cluster
## splits into three sub-shifts, and the docs' cur-VAG/cur-VH sces twins were
## transposed; the setter and poll sces twins pin from caller-jal pairing

Queue item 1 (d4040af), plus queue item 3 closed on the way. All analysis on
the boots' per-sector true payloads (CHDs re-fetched a FOURTH time this
sandbox cycle, sha256 exact: EU 98ccd877..., JP a6025267...; true-EXE SHA-1s
re-matched: slps fa9474b4, sces 06b4bda6; all four contiguous game-EXE
extractions byte-equal the committed baselines). Script repo-external:
scripts/rt_sces_rebuild.py - code-identity twin search (pure-word anchors +
full-window word scoring) then a linear decode with light backward
const-propagation reporting every load/store's materialized table base.

METHOD VALIDATED ON SLPS FIRST: the decoder run on the slps parser
(0x80044174..+0x420) reproduces the documented slps column EXACTLY - gate
0x8011A894, VH-base 0x80114F48, VH+0x20 0x80114EE0, VH+0x820 0x80114F8C,
size-table 0x8011C3A8, VB-base 0x8011C360, VB-total 0x8011C31C, stride
0x80115070 (sh base lui 0x8011 + 0x5070), open-counter 0x8011C35C (the lui
0x8012 + addiu -0x3CA4 pair the docs' composed arithmetic mishandled). Only
then is the sces column read off the sces twin's own stores.

THE REBUILT SCES COLUMN (sces twin found by word-match: parser
0x80044190 229/264 words, select helper 0x800434A4 49/64, Call 9
0x80044C18 33/36):
  per-VAB cluster (Call 5 parser stores):
    gate[16]            slps 0x8011A894 -> sces 0x80119E10   (-0xA84)
    VH-base-ptr table   slps 0x80114F48 -> sces 0x801144CC   (-0xA7C)
    VH+0x20-ptr table   slps 0x80114EE0 -> sces 0x80114464   (-0xA7C)
    VH+0x820-ptr table  slps 0x80114F8C -> sces 0x80114510   (-0xA7C)
    size-table-ptr      slps 0x8011C3A8 -> sces 0x8011C120   (-0x288)
    VB-RAM-base table   slps 0x8011C360 -> sces 0x8011C0D8   (-0x288)
    VB-total table      slps 0x8011C31C -> sces 0x8011C094   (-0x288)
    open-counter u16    slps 0x8011C35C -> sces 0x8011C0D4   (-0x288)
    stride u16 (global) slps 0x80115070 -> sces 0x801145F0   (-0xA80)
  current-context globals (select-helper stores; Call 9 stores cur-VH):
    cur VAG-area ptr    slps 0x801150F0 -> sces 0x80114670   (-0xA80)
    cur VH ptr          slps 0x801150E8 -> sces 0x80114668   (-0xA80)
    cur program-table   slps 0x801150A0 -> sces 0x80114620   (-0xA80)
    cur vab byte        slps 0x8011A875 -> sces 0x80119DF1   (-0xA84)
    cur prog byte       slps 0x8011A87A -> sces 0x80119DF6   (-0xA84)
    cur block byte      slps 0x8011A87B -> sces 0x80119DF7   (-0xA84)
  transfer globals (setter stores):
    transfer-mode A     slps 0x80065940 -> sces 0x800655D0   (-0x370)
    transfer-mode B     slps 0x80065DCC -> sces 0x80065A5C   (-0x370)

INDEPENDENT CROSS-CHECKS ALL HOLD: VB-base/VB-total match the two member
immediates (d4040af), gate matches the doc-confirmed value, cur-block
matches the b7fb28b correction 0x80119DF7, and the poll wrapper reads
0x80045480 exactly as d4040af pinned it. Five independent anchors, zero
conflicts.

CORRECTIONS TO THE RUNTIME-TABLES SECTION (b7fb28b):
  - Its C-cluster sces values (0x8011919C/0x801191E0/0x80119228/0x801191DC
    and the claimed -0xA78..-0xA88 window for that cluster) are WRONG: the
    C-cluster shifts -0x288 as the member immediates said. The composed
    values sat in a different BSS area entirely.
  - Its cur-VAG/cur-VH sces twins are TRANSPOSED: 0x801150F0 (cur VAG-area)
    -> 0x80114670 and 0x801150E8 (cur VH) -> 0x80114668, not the reverse.
    The store order in the select helper fixes the assignment.
  - The pointer cluster is NON-UNIFORM even among itself: -0xA7C (the three
    VH tables), -0xA80 (stride + the three context pointers), -0xA84 (gate
    + the three context bytes) - three distinct BSS sub-shifts, consistent
    with per-variable .sbss/.bss placement differences between the boots.

CODE-SHIFT LAW (or lack of one): sces code shifts are PER-MEMBER, as static
archive linking predicts - select helper +0x14, parser +0x1C, Call 9 +0x1C,
SsVabTransBodyPartly -0x20C, the setter -0x20C (same member neighborhood as
TransBodyPartly), the chunked loader -0x1E4. No uniform code shift exists;
every twin must be found individually (the composed-column root cause).

QUEUE ITEM 3 CLOSED: the setter (slps 0x8003CF00, right after
SsVabTransBodyPartly) is at sces 0x8003CCF4, found via the TransBodyPartly
twins' jal pairing (jal@0x8003CE1C -> 0x8003CF00 | jal@0x8003CC10 ->
0x8003CCF4); both transfer-mode globals shift -0x370, uniform with the
transfer-remaining/cur-transfer-vab pair already pinned. The poll wrapper
confirms at sces 0x80045480 (from the loader twin's own jal).

SIDEBANK (from the same decodes, for the sdk lane and the loader decode):
  - chunked loader sces start 0x8002C65C (derived from the documented call
    sites); its full jal fan-out pairs: 0x8003b578/0x8003b36c (the struct
    fill), 0x8002dc10/0x8002da04 x3, allocator 0x8002dbe0/0x8002d9d4 +
    0x8002dbf0/0x8002d9e4, CD read cluster 0x8003933C/0x80038ef0 (a fifth,
    earlier cluster call the docs' list lacked), 0x80039238/0x80038dec,
    0x80038d34/0x800388e8, 0x800391b8/0x80038d6c, 0x80039198/0x80038d4c,
    bail 0x8002eaa0/0x8002e644 x2.
  - the SPU transfer primitive set all shifts -0x428: 0x8003e414 ->
    0x8003dfec (transfer-start-addr), 0x8003e450 -> 0x8003e028,
    0x8003e48c -> 0x8003e064 (the SPU write), 0x8003e47c -> 0x8003e054.

Gates: docs-only (addresses and shifts, no extracted assets); no carve
action; matched 174; ratchets 365/0; 8/8 verify GREEN untouched. Disc
assets re-provisioned repo-external this window (disc_j/ disc_e/ contiguous
key files, true_j/ true_e/ per-sector true payloads; contiguous boots
byte-equal the baselines).

Next queue:
1. Queue item 2 stands (the chunked loader 0x8002C840/0x8002C65C deserves
   its own decode - who calls IT, and the CD read cluster's roles; the sces
   column above gives its BSS frame for free).
2. sdk lane: the boots' libsnd/libspu adoption rows now have the COMPLETE
   sces column - adoption ready when the lane picks it up.
3. The seq-player attr readers (0x80048CC8/0x800495E0) sces twins are now a
   mechanical exercise with the proven twin-search + decode script.
4. Lanes stay theirs (GSD round-5, setIntr/startIntr/trapIntr, coddog
   transplant); BIG de-frame coordination-gated; runtime gate-family
   blocked.

## 2026-10-16 late: the chunked VB loader's caller chain closes - retry wrapper,
## SE.VH orchestrator, fload3 staging, the "handle" is the \SE.VB;1 filename, the
## CD read cluster is the libcd Pos/Int pair plus the command issuer, and the
## loader's "bail" is the A0#0x34 free() thunk

Queue item 2 of 1b036cd. All analysis on the boots' per-sector true payloads
(CHDs re-fetched a FIFTH time this sandbox cycle, sha256 exact; true-EXE SHA-1s
re-matched: slps fa9474b4, sces 06b4bda6; contiguous boots byte-equal the
committed baselines: slps f2a13b52, sces 19698984). Scripts repo-external:
scripts/cloader_xref.py, cloader_pass2.py, cloader_pass3.py.

THE CALLER CHAIN (slps; sces per-hop shifts below):
  chunked loader 0x8002C840 (d4040af)
    <- retry wrapper 0x8002C7C8   (sces 0x8002C5E4, -0x1E4)
    <- SE.VH orchestrator 0x8002C110 (sces jal site 0x8002C030, -0x1E0;
       sces head-scan candidate 0x8002BE54 is the seek helper's twin, not the
       orchestrator - the sces head needs the same boundary fix, ~0x8002BF34)
The wrapper decodes as the boot's standard retry idiom (structurally identical
to the fload3 retry wrapper 0x8002CA1C): s0 = 0x0FFFFFFF retries; loop
a1 = (s16)a1 sign-extended; jal loader; on (s16)return == -1 retry; on
exhaustion a0 = "FLOAD:fault!\n" (0x80020910, sces 0x800208E4) ->
jal A0#0x3F thunk 0x8002DC10 (sces 0x8002DA04) -> return 0; else return the
loader's s16.

THE ORCHESTRATOR (0x8002C110): s1 = 0x80016600; the (0,0,0) thunk 0x8002C788
-> 0x80045304 (an SE-side primitive, a1 clamped to 0x7F; unnamed); then
jal 0x8002CA1C with a0 = 0x8004C3FC - and the descriptors are INLINE FILENAME
STRINGS: 0x8004C3FC "\SE.VH;1", 0x8004C408 "\SE.VB;1" (plus "\MOV.STR;1" at
0x8004C330). 0x8002CA1C = the fload3 retry wrapper over 0x8002CA84 (fault
"Cannot find file(%s) in fload3()" 0x800209C0): fills the ISO file-record
struct via 0x8003B578(stack+0x18, filename), size at stack+0x1C, sectors =
(size+0x7FF)>>11, malloc n*2048 (the docs' boot-load-model malloc row), seek +
read (its body owns the cd_c/cd_d/cd_e calls at 0x8002CB50/94/C8). Returns the
staged buffer. The orchestrator copies 0x8620 bytes - EXACTLY the SE.VH size,
34336 - from the staged buffer to 0x80016604 (word loop when staged&3==0,
lwl/lwr/swl/swr path otherwise), then jal 0x8002EAA0(staged) and
0x800440D8(0x80016604, -1), then the retry wrapper(a0 = 0x8004C408, a1 = (s16)v0).

THREE CORRECTIONS/NAMES LAND HERE:
  - 0x8002EAA0 is NOT a panic bail: its body is addiu $t2,0xa0 / jr $t2 /
    addiu $t1,0x34 = the A0#0x34 free() thunk (docs already pin A0#0x34 free).
    The loader's "negative -> bail with 0x8002eaa0(handle)" (d4040af) FREES the
    0x40000 staging buffer; the orchestrator's call frees the staged SE.VH
    after the copy. No panic primitive is involved.
  - the loader's a0 "handle" is the "\SE.VB;1" FILENAME STRING (0x8004C408),
    and a1 is the vab id returned by the open. The chunked loader re-fills the
    same file-record struct for the VB name and reads the size from it; the
    VB is read straight off the CD in 0x80-sector chunks into the malloc'd
    0x40000 buffer, TransBodyPartly per chunk.
  - 0x800440D8 = the PUBLIC SsVabOpenHead-shaped wrapper: (a0 = VH address,
    a1 = requested id) -> sign-extend a1, a2 = 0, a3 = 0, jal the parser
    0x80044174, sign-extend result. Its sibling 0x8004410C is the a2 = 1
    variant. The orchestrator opens the staged copy at 0x80016604 with
    requested id -1 (auto-assign), and the returned id feeds the VB step.

THE CD READ CLUSTER NAMED (slps/sces; word-identity check at shift -0x44C):
  - 0x8003933C / 0x80038EF0 = CdPosToInt: CdlPOS BCD (minute, second, frame
    at (a0)) -> LBA, the tail addiu -0x96 = -150 lead-in. Word-identical in
    both boots (0 diffs in 32 words) - a pure-arithmetic leaf.
  - 0x80039238 / 0x80038DEC = CdIntToPos: LBA -> CdlPOS BCD at (a1), the head
    addiu +0x96 = +150. Also word-identical (0 diffs).
  - 0x80038D34 / 0x800388E8 = the CD command issuer: a0 = command byte
    (a0&0xFF), a1/a2 params; 3 attempts; per-command pointer table at
    0x800654AC -> sces 0x80065130 (-0x37C), ring-pointer global 0x8006552C ->
    0x800651B0, status byte 0x8006553C -> 0x800651C0; callee 0x8003A308 ->
    sces 0x80039EF8 (-0x410) is the drive-ready wait whose fault path reports
    "CD open(%02x)..." (0x80021244) via the same A0#0x3F thunk; low-level
    command writer 0x80039E2C.
  - 0x800391B8 / 0x80038D6C = a 3-attempt wrapper (args a0/a1 SWAPPED into the
    call) over 0x8003AAFC -> sces 0x8003A8E0 (-0x21C), which parks a2 at
    0x8006581C and maps status bits 0x30 to codes 0x200/0x249/0x246 (a
    completion/error normalizer).
  - 0x80039198 / 0x80038D4C = a tail-thunk to 0x8003ABF4 -> sces 0x8003A9D8
    (-0x21C); args pass through; its role needs its own decode.
  The loader calls ALL FIVE in sequence (jals at 0x8002C900/918/928/938/948):
  the per-chunk GetTD/seek-read/issue/wait setup. Fan-in census: the cluster
  also serves the fload3 body (0x8002CB50/94/C8), a second reader family
  (0x8002D8F4/24/48, 0x8002DA8C/BC/DC), and the libcd-engine depth
  (0x8003B468/4D4/BD38, 0x8003BEFC/0x8003BF0C/1C/28).

THE SEEK HELPER: 0x8002C030 (slps) / 0x8002BE54 (sces, calls the sces (0,0,0)
thunk 0x8002C5A4): cd_c(0x10 = CdlGetTD, 0, stack buf) -> BCD bytes -> a stack
CdlPOS -> CdPosToInt = track-1 start LBA; target = start + a0; CdIntToPos;
0x8002BC38(POS, 1) issues the seek. No direct jal callers found in the boot
text (indirect call or orphaned variant - open).

THE ALLOCATOR PAIR: 0x8002DBE0 = the A0#0x33 malloc thunk and 0x8002DBF0 = the
A0#0x2B (43) thunk (ordinal in the $t1 delay slot; the pair sits in the boot's
A0-thunk farm 0x8002DBE0..0x8002DC5C: 0x33, 0x2B, 0x15 strcat, 0x3F, 0x1B,
0x17, 0x19, 0x16). 0x8002DBE0's malloc identity was already pinned by the
boot-load-model entry; 0x8002DBF0 is the loader's buffer-clear step (zero-fill
semantics from usage; ordinal 43 unnamed in the census).

A0#0x3F CONFLICT FLAG: the docs pin A0#0x3F = strcpy from the InitPAD site;
BOTH fault-report sites decoded here pass a bare literal string with no
argument setup ("FLOAD:fault!\n", "CD open(%02x)...") - print-shaped. The
strcpy pin needs re-review in the sdk lane before adoption.

Gates: docs-only (addresses and strings, no extracted assets); no carve
action; matched 174; ratchets 365/0; 8/8 verify GREEN untouched. Disc assets
re-provisioned repo-external this window (disk/*.chd + *.bin, disc_j/ disc_e/
contiguous, true_j/ true_e/ per-sector boots).

Next queue:
1. fload3 body 0x8002CA84 full decode (the seek/read/alloc flow, the second
   reader family 0x8002D8xx-0x8002DADC, and who calls fload3 - the file table
   drivers, one step from the boot load model's own loader).
2. sdk lane: 0x80045304, 0x8003ABF4, and the cd_c callees need census rows at
   their true-runtime addresses; A0#0x2B/A0#0x3F ordinals re-pin; the
   libsnd/libspu adoption rows stand.
3. sces orchestrator head pin (candidate ~0x8002BF34; jal site 0x8002C030
   verified) + the sces descriptor/thunk-twin columns for the chain above.
4. Lanes stay theirs (GSD round-5, setIntr/startIntr/trapIntr, coddog
   transplant); BIG de-frame coordination-gated; runtime gate-family blocked.
5. Matching lane IS the unattended-agent lane (it is the long grind): work
   the coddog region-pair reports (2026-10-16 entry; regenerate
   `coddog compare2 decomp.yaml A decomp.yaml B -t 0.5` per pair, output in
   build/coddog.*.txt). Loop per cluster: pick the densest 100.00%-pair
   cluster in a JP target -> write C against `tools/judge_unit.py <target>
   <unit>` (~0.1 s/attempt) -> judge-sweep the target -> `make verify` ->
   roll the same C to the EU twins (100% pairs rename; 95-99.99% pairs get
   the imm-diff treatment first). Curate every new name in
   config/symbols.curated.txt; commit per landed cluster; the judge is a
   screen, verify is the gate.
