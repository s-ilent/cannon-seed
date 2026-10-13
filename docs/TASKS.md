# TASKS

Queued work for this repository, newest on top, with a record of what was done
below. Queued tasks are written for whoever picks them up next — usually the
sandbox agent, which is where the build toolchain lives.

## Queued

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
already right. Re-derive the list from `tools/deframe.py`'s layout.

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
