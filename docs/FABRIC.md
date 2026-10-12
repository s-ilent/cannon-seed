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

Remaining known gap before any family C lands: the state-object field map
(Next action 3).

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
3. State-object field map (`$s3`/`$s7`/frame-0x50 locals) -> extend this
   doc before any family C.
4. Known grid drift left in older rows (follow-up carves, low priority):
   JP `func_8003312C` row (3312C..3386C) holds window-14 tail + 0xC of
   sector-14 ECC; EU `func_80033948` row head (33948..33978) holds 0x30 of
   sector-14 ECC and its span crosses the sector-15/16 headers; JP
   `data_8003386C` (0x2678) and EU `data_80034AD0` (0xad4) span multiple
   sectors. Decompose on the same recipe when those zones need C work.
