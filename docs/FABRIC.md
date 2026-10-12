# FABRIC: the mainmenu state-machine continuation web

Measured 2026-10-12 against both mainmenu baselines (SHA-1 proven by
`tools/grid_walk.py` and every prior carve). Evidence: scripts
`fabric_recon1-3.py` (repo-external), spimdisasm inventories of
`asm/mainmenu_{jp,eu}/nonmatchings/func_8002{C220,CB50,CC5C,D480,DE00,E6E0,EB64,F368}.s`,
raw word xref scans over the full 0xAA000 load image. This document exists
to close queue item "state-machine fabric recon": map the family end to end,
then decide the C unit BEFORE any C is written.

## Verdict

The C220..F834 neighborhood plus the 30348..3312C tail is ONE interlinked
continuation web, not a set of functions:

* **95 cross-references enter the family on each disc** - byte-for-byte the
  same count on JP and EU (55 from inside, 40 from the 30348+ tail), all but
  one of them tail `j` instructions or data pointers. Exactly ONE `jal`
  enters from outside (JP and EU both: `800306B4 jal 8002E4FC`, itself an
  unclaimed island inside the func_80030348 row, targeting a mid-body
  `jal 80026988` shared stub).
* **Nothing in the family has an ordinary caller.** Every entry is either a
  function pointer taken from a data table, a tail `j` from elsewhere in the
  web, or fallthrough from the previous fragment. This is why the
  standalone-C scan (cron-20261011-1926) found zero candidates: there are
  none. The premise is now measured, not inferred.
* The web continues past the old F834 boundary into the 30348..3312C rows:
  the `func_80030348` asm row holds unclaimed islands that jump back into
  the family (`8003047C j 8002E21C`, `800306B4 jal 8002E4FC`), and the
  `data_800313C0` data row holds more continuation `j`-chains.

## Who enters the family (complete entry catalog)

Four handler tables live in the boot data row `data_80020000`, all entries
stride 0x20, all pointing into the pool body:

| table | entries | targets |
| --- | --- | --- |
| `0x80021160` | 10 | CDB4 CDD4 CDF4 CE14 CE34 CF10 CF30 CF50 CF70 CF90 |
| `0x800211F8` | 5 | D2A0 D2C0 D2E0 D300 D320 |
| `0x800213A0` | 5 | D970 D990 D9B0 D9D0 D9F0 |
| `0x80021520` | 5 | F314 F334 F354 F374 F394 |

The fourth table points INTO the "data" row `data_8002EF10` and the
`func_8002F368` row - the state handlers themselves live inside spans the
scanner classified as data (see below). The table directory
`0x80021100..0x80021560` is walked with lui/addiu pairs from the 30xxx/31xxx
zone (`8003160C`, `800317C8`, `80031890`, `80034DB0`, `80038C78..80038E8C`),
which is the web's outer loop.

67 single pointers in the `0x80096xxx..0x8009Axxx` data zone (the callback
table range labelled `data_80086D3C` on JP / `data_8008765C` on EU, inside
the big `data_8007D5D0` tail row) point at handler entries, concentrated in
the E320..E7E4 band: `8002E320`, `8002E36C`, `8002E3B8`, `8002E610`,
`8002E728`, `8002E760`, `8002E78C`, `8002E7B8`, `8002E7E4`, ... plus a few
into the pool body (`8002C610`). These are the menu-item callbacks.

Everything else is internal web traffic: 55 in-family j/jal edges and 40
edges arriving from the 30348..31888 tail (`func_80030C48 j 8002E944`,
`func_80030DB8 j 8002EC8C`, `func_80031638 j 8002F3B0 x4`, ...). The
target set of the tail's jumps is exactly the E6E0/EB64/F368 continuation
band - the outer loop hands control back into the fabric mid-body.

## Frame contract

* **State pointer `$s3`.** Both dispatcher heads open with
  `lw $v0, 0($s3); nop; beqz $v0, ...` (`8002E6E0`, and the same shape again
  at `8002E520` inside the E4B0 block). `$s3` holds the current state id /
  pool pointer; the dispatcher switches on it.
* **Inherited arguments.** Fragment heads use caller registers before any
  setup: the C220 head's first `jal 80026414` consumes the predecessor's
  `$a0/$a1`, and its own `addu $a0, $s3, $zero; addu $a1, $zero, $zero`
  only prepares the NEXT call. Entry labels are not function boundaries.
* **One shared 0x50 frame.** The prologue `addiu $sp, $sp, -0x50` at
  `8002D974` (inside code block 4, after j-entry `8002D930`) pairs with the
  epilogue `lw $ra, 0x48($sp); lw $s0..$s7, 0x28..0x44($sp); jr $ra;
  addiu $sp, $sp, 0x50` at `8002DDD4..8002DDFC`. The whole `data_8002DDB0`
  row (0x50, DDB0..DE00) is that tail - NO sector header in it: byte dump
  shows `addiu $v0,<rel>`; `sw $v0,0($s7)` (the DDB4 tail store, an alabel
  entry); `ori $v0,1; sw $v0,0x380/0x37C($gp)` (JP/EU small-data offsets
  differ); `j 8002C024` + nop; `lui $v0,0x8008; addiu $v0,<rel>; sw
  $v0,0($s7)` (next-state pointer store, 0x7094 JP / 0x78A8 EU); then the
  epilogue. The earlier DDC8..DE00 bound was wrong. Carved 2026-10-12 as
  asm `func_8002DDB0` on both discs. The web's continuations run inside
  this saved-s0..s7 frame.
* **Trampoline band E1A8..E250.** Byte-identical on JP and EU except jal
  targets (uniform 0xB0 callee shift): `addu $a0, $s1, $zero; jal <helper>;
  ori $a1, 0x91C/0x91D/0x91E/0x91F; j 8002C45C` - string-id-selected
  message calls whose jal delay slot carries the argument, then a tail j
  back into the pool body. Classic continuation fragments; a standalone C
  function cannot emit a jr-less, caller-frame-epilogue-sharing body.

## Misclassified code inside "data" rows

Real continuation code sits in three data-classified spans (both discs):

| row | evidence |
| --- | --- |
| `data_8002EF10` (0x458) | state-id switch chains at 8002F10C..8002F328: `ori $v0, N; beq $v0, $v1; nop; j <pool entry>` sequences calling `80026414`/`80026668`, interleaved with `lui/addiu` string constants; also host of root-table 4's handler entries |
| `data_8002F834` (0xb14 JP / 0x137c EU) | same switch-chain shape at 8002F9C8..8002FB78 and 8002FEC0..80030324; calls `8005C62C`, `80035D50`, `80026668`, `80026414`; jumps into D480 mid-body (D8BC, D8D4, D930, DA0C, DA58) and the DDB4 tail store |
| `data_800313C0`/`data_800313D0` zone | CARVED 2026-10-12 - the zone is the raw-sector grid, headers verified at 314B8/31DE8/32718/33048 (0x930 pitch) on BOTH discs; all four user windows are the continuation web's CALL-SITE BANK: window 11 314D0..31CD0, window 12 31E00..32600, window 13 32730..32F30, window-14 head 33060.. - each 0x800 carries 83-90 `jal`, dense `lui/addiu` argument pairs, `lw/sw` locals, ZERO raw pointers. The earlier "tail j-chains at 80031348..80031888" note saw only window 11's head. Carved as asm `func_800314D0`/`func_80031E00`/`func_80032730`/`func_80033060` (JP+EU; JP's window-14 head is the 0xCC to the existing func_8003312C row) |

The earlier "6/278 and 0/709 words decode" census note was measured over
whole rows and is wrong as a classification signal: the code islands decode
cleanly, the rows also contain long genuine-data stretches. The correct
statement is "mixed code+data rows", and the code half is exactly the
web-traffic listed above. (`data_80030A88` was earlier called "genuinely
data: its three j-shaped words target garbage" - WRONG, that census was
parity bytes. The row is [0x100 sector-9 ECC | 0x18 sector-10 header (MSF
00:17:61 JP / 00:19:63 EU, mode 02, subheader) | 0x10 user = window-10 head
CODE: `lw $ra,0x10($sp); nop; jr $ra; addiu $sp,0x18`, byte-identical JP/EU].
Carved 2026-10-12: JP mirrors EU's func_80030BA0 row; EU's func_80030BB0
ECC head (313A0..313D0) is now data too.)

## JP/EU twin structure

Bytes are relocation twins at the same vram for every span except code
block 2; spimdisasm's glabel boundaries are NOT:

| span (vram) | words | eq | j | jal | hi | other |
| --- | --- | --- | --- | --- | --- | --- |
| C220 block 2 | 512 | 9 | 4 | 142 | 21 | 336 |
| CB50 block 3 | 512 | 278 | 1 | 99 | 3 | 131 |
| D480 block 4 | 512 | 370 | 0 | 77 | 0 | 65 |
| DDB0 pool tail | 20 | 17 | 0 | 0 | 0 | 3 |
| DE00 block 5 | 512 | 375 | 0 | 60 | 0 | 77 |
| E6E0 dispatcher | 289 | 218 | 0 | 39 | 0 | 32 |
| EB64 | 235 | 163 | 0 | 26 | 0 | 46 |
| F368 | 307 | 212 | 0 | 50 | 0 | 45 |

"other" includes mem-operand and lo-half immediates that move with
relocation, so the relocation-twin reading stands for blocks 3-5/E6E0/EB64/
F368. Code block 2 (C220) is genuinely region-divergent code (9/512 equal) -
the menu front half differs, the pool behind it does not.

Glabel divergence at identical bytes: CB50 file has 3 functions on JP,
1+16 on EU (the EU `func_8002CC5C` head and CD00/CD18 dispatcher entries are
split artifacts of the same fabric); EB64 file 2 on JP vs 16 on EU; F368
file 2 vs 10; DE00 file 31 vs 32. The dispatcher's `j` targets land on EU
glabel starts (CD00, CD18, CE50, CFA8, ...) that JP files only contain as
mid-body addresses. Conclusion: function identities in this zone are
per-disc scanner opinions; the web edges are the ground truth.

## C-unit decision

No standalone C function exists in the family, on either disc. The only
honest C unit is the web itself - and only after two prerequisites:

1. **Honesty carve of the mixed rows** - DONE 2026-10-12 (carves 1-4,
   see Next actions); the fabric's code side is now fully visible to the
   scanner as hand-pinned asm rows.
2. **Frame/state model**: identify the state object (`$s3`) field offsets
   and the 0x50 frame's s-register roles before writing C. The epilogue
   tells us the frame shape; the dispatcher tells us the state word.
   DONE 2026-10-12 - see the field map below.

Only then attempt family-level C: the smallest independent component first
(the E1A8..E250 trampoline band plus its C45C/C4C0/C50C targets) as a probe
of whether GCC 2.6.3 reproduces the `ori/beq-chain + j` switch shape and the
delay-slot argument placement (`ori $a1` inside jal delay slots). If the
probe fails, the fabric stays asm permanently and the C effort moves to the
framed SDK members path (docs/MATCHING.md 3c) - which the probe result will
have cost one small unit to learn, not a month.

**Probe verdict (2026-10-12, `probes/gcc263/tramp.c`): GO.** GCC 2.6.3 with
the pinned flags (`-mips1 -O2 -G8 -funsigned-char -fno-builtin`) reproduces
every idiom in the band from plain C:

* sparse-case `switch` compiles to the `ori $v0,C; beq $x,$v0,L` chain,
  variable-first compare, `j Ldefault; nop` for the default path - and the
  scheduler fills `beq` delay slots with independent downstream insns
  (the probe saw a duplicated `li $a0,0x100` arg setup land there).
* back-to-back calls put the last independent arg setup in each `jal` delay
  slot with word-exact classes: `ori $a1,0x91F` (`3405091F`),
  `addiu $a2,-1` (`2406FFFF`), `addu $a1,$zero,$zero` (`00002821`),
  `ori $v0,8` (`34020008`) - all byte-identical to retail words.
* the E1C4 -> E1D8 structure reproduces exactly: `j Lnext` whose delay slot
  carries the target block's `a0` setup, target block opening directly with
  `jal` (no own arg setup), the unconditional `j` NOT shortened away because
  its delay slot holds live work.
* standalone-probe caveat, and it supports the family-C premise: a
  standalone C function must open `addiu sp,-N; sw ra` (the probe's first
  `beq` delay slot took the `sw ra`), which the frameless retail fragments
  lack - the fragments are label blocks of the shared parent frame, not
  functions. Family-level C is therefore not just feasible but REQUIRED
  for these shapes, exactly as this document decided.

Both C-unit prerequisites are now measured: the honesty carves (Next
action 1) and the frame/state model (field map below). The probe above is
the gate the web's first real C component must clear.

## State object field map (measured 2026-10-12)

Source: scripts/fabric_fields.py (repo-external) over the fabric rows on
both discs - every s0..s7/sp-relative load-store tallied by offset, width,
and owner row. JP and EU aggregates are IDENTICAL for every s-register
(the only deltas are the C220/CC5C region-divergent front half), so the
frame/state contract below is region-independent.

### Parent frames seen in the web

| parent | frame | layout |
| --- | --- | --- |
| `func_8002C220` | 0x28 | outgoing args 0x00..0x0F; s0-s4 @ 0x10..0x20; ra @ 0x24; NO spill locals - fragments keep everything in s-regs (epilogue C45C) |
| D930 (inside `func_8002D480` row) | 0x50 | outgoing args 0x00..0x0F; six spill locals @ 0x10..0x24; s0-s7 @ 0x28..0x44; ra @ 0x48 (epilogue in `func_8002DDB0`) |
| `func_8002CB50` | 0x48 | (plus a small -0x18 prologue in the same row) |
| `func_8002DE00` | 0x40 | (plus -0x30/-0x18 sub-prologues in the same row) |
| `func_8002EB64` | 0x20 | (plus -0x18) |
| `func_8002F368` | 0x38 | (plus -0x18) |

The 0x50 frame is a textbook GCC MIPS layout: outgoing argument area
0x00..0x0F (never touched by the tallied loads/stores), then locals
0x10..0x24 (all six slots see paired lw/sw), then the saved s-regs and ra.
Continuation fragments entered under a given parent run inside that
parent's frame - which is why they have no prologues of their own.

### The `$s3` state object (>= 0x18 bytes)

| field | accesses | meaning as far as measured |
| --- | --- | --- |
| `+0x00` word | 12 lw, 1 sw (8002DA14) | flags/state word: dispatcher gate (`lw 0($s3); beqz`; `andi 0x20` test then `helper(s3, 0x20)` at E6E0), and the switch-chain input the predecessors hold in `$v1` |
| `+0x04` word | 2 lw | word read in D480/E6E0 |
| `+0x04` byte | 1 sb (8002DA18) | byte write paired with the +0x00 store in the same continuation |
| `+0x08`, `+0x0C` word | 1 lw each | D480 |
| `+0x10`, `+0x14`, `+0x16` half | 1 lh each | D480 (DB7C/DB88 area) - counter-like halfword fields |

### s-register roles (all object pointers, word-0 heavy)

| reg | deref census (aggregate JP==EU) | reading |
| --- | --- | --- |
| `$s3` | see table above | the state object |
| `$s7` | sw 0x0 x2 (DDB0's next-state pointer + flag stores), lw 0x0 x2 (DE00), lw 0x4 x1 (D480) | the successor/next-state sink the DDB0 tail writes |
| `$s5` | lw 0x0 x7 (E6E0 x4, DE00 x2, D480 x1) | another object, word-0 reader |
| `$s4` | lw 0x0 x4 (E6E0), sw 0x0 x1 (D480) | object, word 0 |
| `$s2` | sw 0x40 x2 (CB50/CC5C, D480) | object with a +0x40 word store |
| `$s1` | lw 0x4 (DE00), lw 0x8 x2 (D480, E6E0), lw 0x54 (DE00 E300) | object with +0x4/+0x8/+0x54 fields; ALSO the trampoline band's argument source (`addu $a0,$s1,$zero`) |
| `$s0` | sw 0x0 x6 (C220 x3 / DE00 x2 / CB50 x1), lw 0x4 x2, lw 0x8 x1, sw 0x40 x2, sw 0x44 x4 | object with +0x0/+0x40/+0x44 stores, +0x4/+0x8 reads |

### Consequences for family-level C

1. Every web parent holds object pointers in s-registers across its whole
   body - which is exactly GCC 2.6.3's natural allocation for a local used
   across calls (probe shape B allocated its reused argument to s0 the same
   way). No register pinning needed; the s-reg roles should fall out of
   plain locals in the parent C function.
2. The 0x50 frame's six local slots bound the spill budget of the first
   family component: whatever the source computes beyond s-reg capacity
   must fit 0x10..0x24.
3. The state object is small (~0x18 bytes, flags first, halfword fields at
   +0x10..+0x16) - a plain struct in the C unit, initialized/stored only
   through word/byte stores measured above.

## Multi-subsegment C machinery (design 2026-10-12, implement next)

AMENDED 2026-10-12 (probe session, `probes/gcc263/c478.c`): the first
proof below - four c-rows at C45C/C4C0/C50C/E1A8 fed by one
`src/fabric_band.c` - is STRUCTURALLY IMPOSSIBLE and is dropped. Those
four windows are frame-sharing label blocks of the parent functions
(the C45C epilogue tail, C4C0/C50C inside func_8002C478's 0x20 frame,
the E1A8 band under the C220 0x28 frame): a GCC standalone function
always opens with its own prologue and closes with its own return, and
cc1 cannot emit a lone epilogue, a fall-through window end, or a
save-less callee-saved write - the probe verdict block below already
said as much ("the fragments are label blocks of the shared parent
frame, not functions"). The sound family-C unit is therefore the WHOLE
PARENT FUNCTION, one c-row each, with the multi-subsegment machinery
(<base>.pN rows) reserved for genuinely function-boundary-aligned
window sets.

The corrected first component: **func_8002C478 (C478..C608) as one c
row** - a complete function (real prologue saving ra/s1/s0, real
epilogue), the band's `j .L8002C4C0/.L8002C4DC/.L8002C50C` targets land
inside it, and the cross-object jumps keep resolving through build.sh's
two-pass auto-definition (already exercised: func_8003B568's
`j .L80037CB0` into the C-matched func_80037CAC). Probe results
(probes/gcc263/c478.c, 2026-10-12):

* Prologue and epilogue compile RETAIL-EXACT through the pipeline:
  `[lw v0,0x3D8(gp)][addiu sp,-0x20][sw ra][sw s1][beqz (sw s0 delay)]`
  and `[lw ra][lw s1][lw s0][jr ra (addiu sp delay)]`. Two new narrow
  cc_post rules carry this: rule 1's three-load epilogue variant
  ([lw $ra][lw $rX][lw $rY][addu $sp][j $ra] -> release into the branch
  delay) and rule 7 (leading-load hoist, [frame-alloc][lw $2,N($gp)] ->
  load first). All 8 targets verify GREEN with both rules landed.
* The four gp-relative accesses (0x3D8/0x1048/0x1050 off mainmenu's
  runtime gp base - value still unmeasured) compile byte-exact as
  literal-offset asm from a `$2` file-scope register variable.
* OPEN GAP (only divergence class left): cc1 folds the constant pointer
  `s0 = &D_80089440` - the `*s0` store becomes an at-pair and
  `(int)s0 - 0x40` folds to absolute lui/addiu pairs, while retail
  materializes s0 and stores/adds through the register. The retail
  source held s0 opaquely; finding the C-89 shape that does the same
  without extra insns is the remaining question before the function
  lands as src/func_8002C478.c. Everything else about the function
  (the call trains, delay-slot fills, the bne/s1 compare, the
  j .L8002ABD4 tail with maspsx's reorder-mode delay nop) already
  matches the pipeline evidence.

The machinery itself (tools/cc_split.py + build.sh grouping, commit
917502f) is unchanged and stays dormant until a function-boundary-
aligned multi-window unit appears.

## Next actions

1. DONE 2026-10-12: honesty carves 1+2 (EF10, F834), carve 3 (DDB0 whole
   row -> asm `func_8002DDB0`), carve 4 (313C0/313D0 zone -> grid
   decomposition with call-bank windows 11-14 as asm), JP 30A88 split
   mirroring EU, BB0-row ECC-head trims. All rows carry the `pinned`
   marker: `make scan` reproduces them verbatim (generalized pin
   mechanism, commit 7c7451c).
2. DONE 2026-10-12: trampoline-band C probe (`probes/gcc263/tramp.c` +
   docs/TOOLCHAIN.md probe table). Verdict GO - see the verdict block in
   the C-unit decision above. GCC 2.6.3 reproduces the switch chain, the
   jal delay-slot arg placement (word-exact), and the goto/delay-slot-steal
   structure of E1C4 -> E1D8 from plain C.
3. DONE 2026-10-12: state-object field map (section above;
   scripts/fabric_fields.py repo-external). Frames enumerated, `$s3` state
   object laid out (+0x00 flags word / +0x04 word+byte / +0x08 / +0x0C /
   halfwords +0x10..+0x16), all seven s-registers assigned deref censuses,
   JP==EU aggregates confirmed. Family-C consequences recorded.
4. Known grid drift left in older rows (follow-up carves, low priority):
   JP `func_8003312C` row (3312C..3386C) holds window-14 tail + 0xC of
   sector-14 ECC; EU `func_80033948` row head (33948..33978) holds 0x30 of
   sector-14 ECC and its span crosses the sector-15/16 headers; JP
   `data_8003386C` (0x2678) and EU `data_80034AD0` (0xad4) span multiple
   sectors. Decompose on the same recipe when those zones need C work.
