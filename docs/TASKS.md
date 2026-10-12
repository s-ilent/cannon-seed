# TASKS

Queued work for this repository, newest on top, with a record of what was done
below. Queued tasks are written for whoever picks them up next — usually the
sandbox agent, which is where the build toolchain lives.

## Queued

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
