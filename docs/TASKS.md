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
