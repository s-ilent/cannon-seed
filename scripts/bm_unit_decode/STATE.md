# block-move unit decode - judge-loop state (cron-202610260919)

The movstrsi landing recipe (cron-202610260649) executed to the first judge
diffs; the tree splits were reverted (ratchet-gated), the decode artifacts
are staged here. Everything below is oracle-proven or judge-observed.

## TRUE UNIT EXTENTS (recipe correction)

The recipe said "split at yaml 0xB660 (VA 0x8002AE60)" - that is the 0649
window's body chunk, NOT the entry. Both boots' units are the SAME source
function whose real entry is the jal'd prologue and whose tail is the
matching epilogue:

- slps_00270: VA 0x8002ADA0..0x8002B464 (0x6c4), yaml/file 0xB5A0..0xBC64.
  Entry func_8002ADA0 (0x40 prologue, jal'd from 0x8002A7C4), epilogue
  func_8002B444 (restores ra/s4/s3/s2/s1/s0, frame 0x28).
- sces_00269: VA 0x8002ABC8..0x8002B28C (0x6c4), yaml/file 0xB3C8..0xBA8C.
  Entry func_8002ABC8 (0x40 prologue, jal'd from 0x8002A5EC), epilogue
  func_8002B26C.

All 33 interior chunks accounted byte-exact between entry and epilogue in
both boots (chunk sizes sum to 0x6c4 exactly). NO external branch enters
either unit's interior; the only outside refs are the two entry jals plus
sces head branches to interior labels func_8002ADA0/func_8002AF10 (both
already in config/symbols.sces_00269.txt - prelude-resolvable).

## DECODE (same C serves both boots, per-target symbols)

Memory-card save unit, o32 8 args: path(s4), code(s2), str(a2->strcpy),
rec(s3, 0x30 record), src5(s0, stack 0x38), src6(stack 0x3C),
src7(stack 0x40), size(stack 0x44). See the two .c files for the full
body: signed-div sector math (three separate /0x2000 expressions), 0xff
byte-loop fill of the work buffer, 'SC'+code header (one pointer var +
two distinct per-byte symbols), strcpy, 0x30 straight-line record copy,
(short)code==0x13 if/else with THREE 0x80 movstrsi block-moves per arm
(both arms re-bind assignment 1 src5->hdr+0x80 - that is why gcc expands
it twice, no CSE), 0x200 block-move copy back into the work buffer, then
open/close/write/read verify tail (returns 2/0/1/-3).

Symbol map: slps D_8006974C/D_801150F8/F9/FA/FB/D_80115158/D_801151F8/
D_80115278 <-> sces D_800693F4/D_80114678/79/7A/7B/D_801146D8/D_80114778/
D_801147F8. sces has NO gp_value -> no gp rewrite; slps does.

## LANDED-BLOCKERS SOLVED THIS WINDOW (bank these)

1. src/ is ratchet-gated: placeholder tokens (func_XXXXXXXX/D_XXXXXXXX)
   are counted PER OCCURRENCE in src/ and include/ - an unmatched unit's
   src cannot land (652/60 vs 644/0). Files stage HERE until the loop
   closes; the memclr build-inert precedent only worked because those
   units' names were already real.
2. slps stager rewrites bare-symbol operands to %gp_rel when the symbol
   is missing from the gp_info table (tools/gp_flags.py info reads ONLY
   config/symbols.slps_00270.txt). The unit's eight data symbols must be
   added to the curated zone of config/symbols.slps_00270.txt with
   `absolute:true` (D_8006974C is within gp range but retail loads it
   lui/addiu - the _spu_inTransfer precedent). Verified: with the entries
   added, the judge mini-links and diffs bytes.
3. The two yaml splits + giant-.s head/tail surgery were rehearsed
   (exact line splits: slps 5374..5971 unit lines out of
   func_800272F8.s, tail file asm/nonmatchings/func_8002B464.s; sces
   5183..5780 out of func_80027340.s, tail asm/sces_00269/
   func_8002B28C.s) and reverted clean.

## JUDGE LOOP STATE (first diffs, slps)

First compile: LINK-FAIL fixed by (2); then a real byte diff of 136+
words starting in the prologue: OURS interleaves the arg binds into the
save sequence (lw a0,0x44(sp) lands where retail still has sw s3,0x1c),
retail keeps ALL SIX saves (ra,s4,s3,s2,s1,s0) ahead of every bind
(s4=a0, s3=a3, lw v1,0x44(sp), s2=a1, lw s0,0x38(sp)). Iteration matrix
queued: statement order around t=size+0x200 (the size load must NOT
hoist into the save window - try computing total after the header
stores, or redeclaring the param order), then the fill-loop form
(sltiu bound, per-iteration base materialization), then per-arm
block-move layout, then the open/close tail scheduling.

## JUDGE LOOP PROGRESS (cron-202610261034)

The splits + symbols + srcs were wired IN-TREE this window (extract clean:
head/tail .s + yamls only; the three-file clobber lesson did NOT fire for
these rows; no unit .s was generated since the srcs existed) and the judge
mini-links cleanly with the curated entries - blocker 2's fix re-verified.
Tree then REVERTED to aaa23ad3 (landing requires a converged loop; only the
curated D_ entries were kept - they are durable across regens and inert
without the split). Variant snapshots live in variants/.

v0 FIRST-JUDGE FACTS (slps_00270):
- SIZE EXACT: built 1732 = retail 0x6c4. SIX diff regions only:
  0x004..0x010 + 0x014..0x018 (prologue bind order), 0x01C..0x15C (divs +
  fill + stores + strcpy + S30 + dispatch head), 0x5CC..0x5D4 (-1 register
  s2 vs s1), 0x5D8..0x6BC (open/close tail scheduling), 0x6C0..0x6C4
  (epilogue final word nop vs addiu sp,0x28).
- THE MIDDLE IS BYTE-EXACT: 0x15C..0x5CC (1132 bytes) - all THREE 0x80
  movstrsi block-moves, the unaligned+aligned dispatch, the 0x30 S30
  straight-line copy, the (short)code==0x13 branch - the decode's core law
  verified end to end.

LAWS BANKED (each oracle-observed):
1. MODULO: `t % 0x2000 != 0` compiles to `andi v0, v1, 0x1fff` + beq - gcc
   2.6.3's zero-test shortcut. Retail instead runs a FULL SECOND branchy
   division. FALSIFIED forms: `t != total` (V3), inline `t != t/0x2000*
   0x2000` (V4), copy-var `u = t; t != u/0x2000*0x2000` (V5a) - ALL merge
   into ONE div (CSE/coalesce) and shrink 4 bytes. Retail's div2 shape:
   `addu v0,v1` BEFORE bgez (branch reads the copy's register, delay slot
   nop) + `addiu v0,v0,0x1fff` + sra + sll + `beq v1,v0` - the div operand
   is a DISTINCT pseudo holding a copy of t, compared against t itself.
   OPEN: which C form blocks the CSE (the real compile kept both divs).
2. PROLOGUE: gcc 2.6.3 emits LAZY saves for the current C (each s-reg
   saved immediately before its bind, interleaved, ra/s1 last); retail is
   BLOCK saves (ra,s4,s3,s2,s1,s0) then binds s4,s3,[v1=size],s2,[s0=src5].
   The str shuffle `addu a1,a2` rides strcpy's DELAY SLOT in retail
   (B670) but gcc hoists it into the entry batch for our C. OPEN.
3. FILL LOOP: built = pointer walk (hoisted base, base+0x1FF end cursor);
   retail = per-iteration lui/addiu base materialization + sltiu bound +
   the 'S' constant (0x53) riding the loop bnez delay slot. Symbol-index
   alone did NOT prevent the hoist. OPEN.
4. -1 REGISTER: ours materializes -1 into s2 at the fd==-1 test; retail
   reuses s1 (hdr's home) after hdr's liveness ends. Likely self-resolves
   with the prologue law. OPEN.
5. TAIL: open/close scheduling region + the epilogue's final delay-slot
   word (cc_post rules 4/5 territory). OPEN.

Register assignment CONFIRMED IDENTICAL both sides (path=s4, code=s2,
src5=s0, rec=s3, size=t via v1) - only emission order and shapes differ.
