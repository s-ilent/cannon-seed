#!/usr/bin/env python3
"""cc_post.py - instruction-order fixups for the C compilation path.

Sits between maspsx and the assembler in tools/cc.sh, rewriting the
maspsx output of cc1 (GCC 2.6.3) so that wrapper-style functions match
the retail instruction order byte for byte. Only ever applied to C
sources; the asm split path never runs it.

Why this exists (documented from the first real-function match attempt,
2026-10-11, g3_eu func_8004C4CC cluster): retail shows two scheduling
behaviours that GCC 2.6.3 emits differently, both independent of
-O level, -mcpu, -mgas, -fno-delayed-branch, -fno-schedule-insns{,2}
and every source shape probed (separate statements, explicit casts,
temporaries):

1. EPILOGUE DELAY SWAP. GCC fills the load-delay slot after the $ra
   reload with the frame release and leaves the branch delay to a
   trailing nop:
       lw   $31,N($sp)      lw   $31,N($sp)
       addu $sp,$sp,M   ->  nop
       j    $31             j    $31
       nop                  addu $sp,$sp,M   <- retail (branch delay)
   Retail keeps the load-delay slot empty (nop) and puts the frame
   release into the branch delay slot. Same instructions, same
   semantics, different order - byte difference, so the swap must be
   reproduced. (The trailing nop maspsx appended is absorbed.)

   Two-load variant (found 2026-10-11, mainmenu_jp func_8003800C,
   the first unit member whose frame saves a callee-saved register
   besides $ra): with an intermediate spill reload the release sits
   one slot later, and retail emits NO extra nop - the jump lands
   right after the second load and only the branch delay carries the
   release:
       lw   $31,20($sp)     lw   $31,20($sp)
       lw   $16,16($sp)     lw   $16,16($sp)
       addu $sp,$sp,24  ->  j    $31
       j    $31             addu $sp,$sp,24  <- retail (branch delay)
       nop
   The shrink (5 instructions -> 4) is real: retail has no nop. Fires
   only on [lw $ra][lw $rX,N($sp)][addu $sp][j $ra](nop) with
   rX != $ra; the jump does not read $rX, so the reorder is
   semantically a no-op.

   Three-load variant (found 2026-10-12, mainmenu_jp func_8002C478,
   the first unit member whose frame saves two callee-saved registers
   besides $ra): retail releases the frame in the branch delay after
   both reloads, with no extra nop:
       lw   $31,24($sp)     lw   $31,24($sp)
       lw   $17,20($sp)     lw   $17,20($sp)
       lw   $16,16($sp)  -> lw   $16,16($sp)
       addu $sp,$sp,32      j    $31
       j    $31             addu $sp,$sp,32  <- retail (branch delay)
       nop
   Fires only on [lw $ra][lw $rX][lw $rY][addu $sp][j $ra](nop) with
   rX/rY != $ra; the jump reads neither, so the reorder is
   semantically a no-op. Checked before the two-load variant (the
   two-load window [lw $rY][addu][j] sits inside this shape and would
   otherwise fire first and mis-swap).

2. EXTEND-PAIR UNWEAVE. When two 16-bit sign extensions are scheduled
   together GCC interleaves them; retail emits each pair as a unit:
       sll $A,$B,16         sll $A,$B,16
       sll $C,$D,16         sra $A,$B,16
       sra $A,$B,16    ->   sll $C,$D,16
       sra $C,$D,16         sra $C,$D,16
   Only fires on four consecutive sll/sra-by-16 forming two distinct
   (dest,src) pairs - pure register shifts, side-effect free, so the
   reorder is semantically a no-op.

3. RETURN-MOVE UN-FILL (found 2026-10-11, mainmenu_jp func_800791A4,
   `return d;` getter). GCC fills the return jump's delay slot with the
   value move; retail keeps the move before the jump with an empty
   (nop) delay slot:
       j    $31             addu $2,$7,$zero
       addu $2,$7,$zero ->  j    $31
                            nop
   Fires only on a jump-to-$ra immediately followed by a
   move-to-$v0 (`addu $2,$X,$zero`, X != $2). Pure register move,
   side-effect free; the grown nop reproduces the retail delay slot.

   OPPOSITE RETAIL BEHAVIOUR EXISTS (found 2026-10-26, the pair-pool
   wave 2: Square0/Square12, the LIBGTE GTE SQR members): the same GCC
   output [j $ra][addu $2,$X,$zero] carries the move IN the branch
   delay slot at retail - the RotTransPers sra precedent generalized
   to the bare out-pointer move. The getter class keeps the move
   before the jump; these members fill the slot. Retail is per-unit
   evidence, so the source marker `cc-post: keep-return-fill` skips
   this rule for the units whose retail tail is the filled form (the
   marker only ever toggles the order of a pure $v0 move - semantics
   identical either way).

4. PROLOGUE SAVE RESTORE (found 2026-10-11, mainmenu_eu
   func_80037A0C, `D_800C936C = 1;` wrapper). GCC's scheduler hoists
   an independent constant materialization for the first body store
   above the $ra spill, between the frame alloc and the save; retail
   keeps the prologue pair adjacent:
       subu $sp,$sp,24      subu $sp,$sp,24
       ori  $2,$zero,1  ->  sw   $31,16($sp)
       sw   $31,16($sp)     ori  $2,$zero,1
   Fires only on a frame-alloc instruction immediately followed by a
   $zero-based v0 materialization immediately followed by the $ra
   spill. The materialization reads $zero and writes $2, the spill
   reads $31/$sp - no shared operands, so the reorder is
   semantically a no-op. Keeps every other hoisted instruction
   (arguments, later loads) untouched.

   OPPOSITE RETAIL BEHAVIOUR EXISTS (found 2026-10-31, g3_eu
   func_8006B0F0, the LIBSND tick-mode installer's 999-spin entry,
   landed-unit draft round 5): the pinned-counter init schedules
   first natively ([subu][ori $2,999][sw $31]...) and that IS the
   retail order there (row 8006B0F4 - ori BEFORE the ra save), while
   func_80037A0C's retail carries the sw-first form. Retail is
   per-unit evidence, so the source marker `cc-post: keep-prologue`
   skips rule 4 for the units whose retail prologue keeps the
   materialization above the $ra save (the marker only ever toggles
   the order of two independent insns - semantics identical either
   way).

5. PROLOGUE CALL DELAY NORMALIZATION (found 2026-10-11, mainmenu_jp
   func_8003800C, the first unit member whose frame saves two
   registers). GCC hoists the first call's argument setup above the
   $ra spill and fills the call's delay slot with the callee-saved
   spill; retail keeps both spills adjacent after the frame alloc and
   puts the argument setup in the delay slot:
       subu $sp,$sp,24      subu $sp,$sp,24
       addu $4,$0,$zero     sw   $31,20($sp)
       sw   $31,20($sp) ->  sw   $16,16($sp)
       jal  func_80035A78   jal  func_80035A78
       sw   $16,16($sp)      addu $4,$0,$zero   <- retail (delay)
   Fires only on [frame-alloc][register-only ALU][sw $ra][jal]
   [sw $rS,N($sp)]. Guards: the ALU instruction must not reference
   $sp, must not write $sp/$ra, and must not write the spill's source
   register (the spill moves ahead of it). All five instructions are
   mutually independent under those guards, so the reorder is
   semantically a no-op. Rule 4 and this rule are disjoint: rule 4
   fires on a v0 materialization at the same slot, rule 5 requires a
   register-only ALU form, and after rule 4 rewrites, the shape no
   longer matches rule 5.

Every rule triggers on a narrow, byte-verified pattern; anything that
does not match passes through untouched. The SHA-1 oracle gates the
result either way.

EPILOGUE CONVENTION SPLIT (found 2026-10-13, g3_eu stopIntr - the first
SDK member whose frame saves a callee-saved register AND makes calls).
The game-compiled units follow the swapped branch-delay convention the
rules above reproduce; SDK members assembled by Sony's ASPSX driver in
.set-reorder mode keep GCC's own order (frame release BEFORE the jump,
nop in the branch delay):
    lw   $31,20($sp)     lw   $31,20($sp)
    lw   $16,16($sp)     lw   $16,16($sp)
    addu $sp,$sp,24      addu $sp,$sp,24   <- SDK/ASPSX (maspsx raw)
    j    $31             j    $31
    nop                  nop
maspsx's raw output already IS this form; the rule-1 variants below
would swap it away from retail. Units that carry the source marker
`cc-post: keep-epilogue` (a comment in the .c file, detected by
tools/cc.sh) are compiled with --keep-epilogue, which disables ONLY
the rule-1 epilogue swap variants; every other rule still applies.

6. SDK LOAD-TO-SYMBOL-STORE HAZARD NOP (--sdk-aspsx units; found
   2026-10-13, g3_eu stopIntr). cc1 emits an explicit `#nop` marker
   whenever the instruction after a load reads the loaded register;
   the 1995-era ASPSX assembler materialized those markers and only
   THEN expanded a bare-symbol store into lui $at + sh, giving:
       lhu  $3,0($2)        lhu  $3,0($2)
       sh   $3,symbol  ->   nop              <- retail keeps this nop
                            lui  $at,%hi(symbol)
                            sh   $3,%lo(symbol)($at)
   maspsx (nop_at_expansion=False) instead reasons that the $at
   expansion itself separates the load from the use and drops cc1's
   #nop, emitting the 3-insn form - one nop short of retail. Units
   carrying the source marker `cc-post: sdk-aspsx` (which implies
   keep-epilogue) get rule 8: insert the nop between a load and a
   bare-symbol store that reads the loaded register. Fires only on
   that exact [load $X][store $X,<symbol>] shape; reg-offset stores
   keep maspsx's own hazard logic.

maspsx formatting note: it emits a blank line after every call's
delay-slot instruction. Blank lines carry no bytes, so they are
dropped on read - otherwise the prologue call pattern above would be
split into two runs and never match.
"""

import re
import sys

LW_RA = re.compile(r"^lw\t\$(?:31|ra),(-?0x[0-9a-f]+|\d+)\(\$sp\)$")
ADDU_SP = re.compile(r"^addu\t\$sp,\$sp,(-?0x[0-9a-f]+|\d+)$")
JUMP_RA = re.compile(r"^j(?:r)?\t\$(?:31|ra)$")
SLL16 = re.compile(r"^sll\t\$(\w+),\$(\w+),16$")
SRA16 = re.compile(r"^sra\t\$(\w+),\$(\w+),16$")
MOVE_V0 = re.compile(r"^addu\t\$2,\$(\w+),\$zero$")
FRAME_ALLOC = re.compile(r"^(?:subu|addiu)\t\$sp,\$sp,(-?0x[0-9a-f]+|\d+)$")
V0_IMM = re.compile(r"^(?:ori|addiu|li)\t\$(?:2|v0),(?:\$(?:0|zero),)?(-?0x[0-9a-f]+|\d+)$")
SW_RA = re.compile(r"^sw\t\$(?:31|ra),(-?0x[0-9a-f]+|\d+)\(\$sp\)$")
LW_SREG = re.compile(r"^lw\t\$(\w+),(-?0x[0-9a-f]+|\d+)\(\$sp\)$")
JAL_CALL = re.compile(r"^jal\t\S+")
SW_SREG = re.compile(r"^sw\t\$(\w+),(-?0x[0-9a-f]+|\d+)\(\$sp\)$")
LW_GP_ANY = re.compile(r"^lw[ \t]+\$(\w+),(-?0x[0-9a-fA-F]+|\d+)\(\$gp\)$")
# Register-only ALU op for the prologue hoist (rule 5): captures the
# destination register. Memory ops, branches and frame allocs excluded
# by construction (memory ops are never safe to reorder around stores;
# frame allocs are matched separately).
ALU_X = re.compile(
    r"^(?:addu|addiu|or|ori|and|andi|xor|xori|subu|sub|sll|srl|sra|li|lui|move)"
    r"\t\$(\w+),")

NOP = re.compile(r"^nop(\s*#.*)?$")
# maspsx marks its load-delay decisions as '#nop # DEBUG: ...' comments;
# they carry no bytes, so drop them (otherwise they split instruction
# runs) and normalize 'nop  # DEBUG: branch/jump' to a bare nop.
NOPLIKE = re.compile(r"^#nop\s*#\s*DEBUG:")


def is_instruction(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith("#"):
        return False
    if s.endswith(":"):
        return False
    if s.startswith("."):
        return False
    return True


KEEP_EPILOGUE = False
KEEP_RETURN_FILL = False
SDK_ASPSX = False
KEEP_PROLOGUE = False
REMANT_JOIN = None
REMANT_EXIT = None
REMANT_MODE = None
SWAP_REGS = None        # (a, b) numeric reg tokens, e.g. ("$20", "$21")
ADDU_COMMUTE_N = None   # 1-based occurrence index of `addu $d,$d,$s` to commute
DELAY_SB_OUT = False    # move an sb out of a j's delay slot, restore the nop
SAVE_SWAP = None        # (a, b): exchange the ORDER of the pair's frame-save lines
PAD_LW = None           # 1-based occurrence index of an lw to pad (retail's
                        # load-use nop maspsx's one-ahead re-derivation misses
                        # when gcc's #nop was decided against a far-store use
                        # two slots ahead - the honest upstream fix is the
                        # maspsx one-ahead hazard look, banked cron-202611021158)
PROLOGUE_PARAM_FIRST = False
RULE15_INTERLEAVE = False   # rule 15: prologue-param-interleave (the fully
                            # interleaved save+import prologue the WithMode
                            # family's retail carries; see _prepass_rule15)
RULE17_MERGE = None      # rule 17: merge-polarity invert+trampoline, as
                         # (anchor_label, jdelay_spec) from the marker
                         # (`cc-post: rule17 <$Lerr> jdelay <op> <reg> <imm>`;
                         # see _rule17_on_file)
LT0_SCC = None           # rule 18: lt0-scc materialization rewrite - the
                         # expected site count from the marker
                         # (`cc-post: lt0-scc <count>`); see
                         # _rule18_lt0_scc
SITE_FRESH_CONST = None  # rule 19: site-fresh-const - the hoisted-constant
                         # spill rewrite, as (imm, reg) from the marker
                         # (`cc-post: site-fresh-const <imm> <reg>`); see
                         # _rule19_site_fresh_const
IMPORT_ORDER = None      # rule 21: import-order - the prologue import-pair
                         # order, as [reg, ...] from the marker
                         # (`cc-post: import-order <reg>,<reg>[,...]`); see
                         # _rule21_import_order
VOL_EXTEND = None        # rule 20: vol-extend - the volatile-re-load merge
                         # andi delete, as the expected site count from the
                         # marker (`cc-post: vol-extend <count>`); see
                         # _rule20_vol_extend
RULE16_VERDICT = False   # rule 16: verdict-polarity invert+reorder (the
                         # early `if (f() == K) return -1;` verdict: gcc
                         # emits beq-to-tail with the dead -1 in the branch
                         # delay, retail keeps bne-to-continue with the fail
                         # j+li inline; see _prepass_rule16)
R16_JDELAY = None        # rule 16 j-delay override (`jdelay <op> <reg> <imm>`
                         # marker args): the fail-materialize insn emitted in
                         # the inserted j's delay slot. Default None = the
                         # built branch delay line verbatim (idempotent when
                         # the built delay IS the fail li); the copy-delay
                         # class (a saved-reg copy rides the verdict delay,
                         # e.g. WithMode's addu $17,$16,$zero) REQUIRES it -
                         # the copy must stay in the bne delay, the li is
                         # new.
ADDIU_IMM = False       # normalize `addu $r,$s,imm` -> `addiu $r,$s,imm` (the
                        # sdk units' immediate-form law: retail addu keeps
                        # register-only sums, every immediate sum is addiu)
V0_SINK = False         # sink the first post-call v0 consumer (writing a
                        # callee-saved reg) into the NEXT call's delay slot
ADDR_PIN_LATE = False   # move a stack-address materialization (addiu $sX,$sp,imm)
                        # from its statement position into the consuming call's
                        # arg-setup sequence, right before the first insn that
                        # reads $sX (retail keeps the pin adjacent to its
                        # consumer; gcc -O1 emits it at the assignment)
# -O1 sdk-unit prologue law (found 2026-11-02, mainmenu_eu CdGetToc2; the
# same shape is retail in func_80079758/func_80069740 whose -O2 builds
# reach it via the scheduler): gcc's -O1 prologue emits [frame][sw ra]
# [descending s-reg saves][param copy][consts][jal][arg-ALU delay] while
# retail hoists the FIRST param copy's save+copy and the constant block
# ABOVE the $ra save and sinks the param-byte sb into the call's delay
# slot (sound: the delay executes before the callee, so the stored v0 is
# still the pre-call constant):
#   subu sp,K        subu sp,K
#   sw   ra,M        sw   $sA,N(sp)     <- the copy target's save hoists
#   sw   sQ...       addu $sA,src,zero
#   ...              <imm ALUs>
#   sw   $sA,N(sp)   <arg ALUs>         <- hoisted from the jal delay
#   addu $sA,src     sw   ra,M
#   ...              sw   sQ...         <- remaining saves, order kept
#   jal  T           jal  T
#   <arg ALU> delay  sb   v0,N(sp)      <- the param store sinks (delay)


def _prepass_swap_regs(lines: list[str]) -> list[str]:
    """Marker swap-regs (cc-post: swap-regs $A $B): exchange two register
    tokens throughout the unit's assembly. Rationale (func_80077A18
    CD_cachefile, cron-202611021158): gcc's local-alloc hands the anchor
    materialization and the walker copy the opposite callee-saved pair to
    retail (probe $20=anchor/$21=walker vs retail s5=anchor/s4=walker);
    three source permutations (declaration order, symbol-ref order, init
    order) did not flip the pair - the choice is allocator-internal. The
    two registers are pure allocator picks (no ABI role), the exchange is
    a consistent renaming, and the frame save/restore lines are EXCLUDED
    so the prologue/epilogue slot layout (s4@0x30, s5@0x34 by name, the
    gcc convention retail follows) stays untouched. The judge witnesses
    the result by word diff."""
    a, b = SWAP_REGS
    skip = re.compile(r"^(?:s[wf]|lw)\t\$(?:" + a[1:] + "|" + b[1:] + r"),\d+\(\$sp\)$")
    res = []
    for ln in lines:
        if skip.match(ln):
            res.append(ln)
            continue
        out = []
        i = 0
        while i < len(ln):
            if ln.startswith(a, i):
                out.append(b)
                i += len(a)
            elif ln.startswith(b, i):
                out.append(a)
                i += len(b)
            else:
                out.append(ln[i])
                i += 1
        res.append("".join(out))
    return res


def _prepass_addu_commute(lines: list[str]) -> list[str]:
    """Marker addu-commute (cc-post: addu-commute <n>): commute the n-th
    `addu $d,$d,$s` (1-based) into `addu $d,$s,$d`. gcc canonicalizes both
    C operand orders to $d-first; retail's pipeline emitted s-first at the
    size store (func_80077A18 cron-202611021158). Commutative, zero
    semantic content, one word. The build fails loudly when the unit
    carries fewer than n matches - re-pin n after any source edit."""
    pat = re.compile(r"^addu\t(\$\d+),(\$\d+),(\$\d+)$")
    seen = 0
    res = []
    for ln in lines:
        m = pat.match(ln)
        if m and m.group(1) == m.group(2) and m.group(2) != m.group(3):
            seen += 1
            if seen == ADDU_COMMUTE_N:
                ln = f"addu\t{m.group(1)},{m.group(3)},{m.group(2)}"
        res.append(ln)
    if seen < ADDU_COMMUTE_N:
        sys.stderr.write(
            f"cc_post: addu-commute occurrence {ADDU_COMMUTE_N} not found "
            f"(only {seen} candidates)\n"
        )
        sys.exit(3)
    return res


def _prepass_delay_sb_out(lines: list[str]) -> list[str]:
    """Marker delay-sb-out (cc-post: delay-sb-out): where a `j <label>`
    carries an `sb` in its delay slot, move the sb after the jump and
    restore the plain nop delay. Retail (func_80077A18 arm1,
    cron-202611021158) keeps the byte store inline before the j; gcc's
    schedule packed it into the delay. The halfword store in the sibling
    arm's delay is retail's OWN packing and is left alone (sb only).
    Execution order is unchanged: the delay slot runs unconditionally, so
    the sb's position relative to the taken/untaken edge is identical."""
    res = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if re.match(r"^j\t", ln) and i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if re.match(r"^sb\t", nxt):
                # retail keeps the byte store inline BEFORE the jump:
                # [j, sb(delay)] -> [sb, j, nop]
                res.append("\t" + nxt)
                res.append(ln)
                res.append("\tnop")
                i += 2
                continue
        res.append(ln)
        i += 1
    return res


def _prepass_save_swap(lines: list[str]) -> list[str]:
    """Marker save-swap (cc-post: save-swap $A $B): exchange the ORDER of
    the two callee-saved frame-save lines for a swap-regs pair. gcc emits
    the saves in its allocation order; retail's pipeline emitted the
    lower-reg save first (func_8007736C cron-202611021158: s3's save
    precedes s4's). The stores are independent (distinct frame slots),
    so the exchange is semantics-free. Restore lines are NOT touched
    (gcc's descending restore order already matches retail)."""
    a, b = SAVE_SWAP
    pat_a = re.compile(r"^sw\t\$" + a[1:] + r",\d+\(\$sp\)$")
    pat_b = re.compile(r"^sw\t\$" + b[1:] + r",\d+\(\$sp\)$")
    ia = ib = None
    for i, ln in enumerate(lines):
        if ia is None and pat_a.match(ln):
            ia = i
        if ib is None and pat_b.match(ln):
            ib = i
    if ia is None or ib is None:
        sys.stderr.write("cc_post: save-swap save lines not found\n")
        sys.exit(3)
    if ia > ib:
        lines[ia], lines[ib] = lines[ib], lines[ia]
    return lines



def _prepass_pad_lw(lines: list[str]) -> list[str]:
    """Marker pad-lw (cc-post: pad-lw <n>): insert a plain nop AFTER the n-th
    `lw` line. Retail's cc1 emits #nop after a load whose value's next use
    reads it as store data (func_8007736C's mount-guard copy: lw $2,D_800C7CFC;
    nop; lui $at; sw $2,D_800C8028($at) - cron-202611021158). maspsx's
    re-derivation checks only the IMMEDIATELY following instruction, which
    is the at-expansion prefix the far-store split injected - the hazard one
    slot deeper goes unseen. The upstream-class fix (look one more insn
    ahead when the next is an at prefix) needs the full 8/8 re-verify ritual;
    this marker unblocks the unit in the meantime. Occurrence-indexed for
    the frozen source; loud-fail on a count miss."""
    pat = re.compile(r"^lw\t(\$\d+),")
    seen = 0
    res = []
    for ln in lines:
        res.append(ln)
        m = pat.match(ln)
        if m:
            seen += 1
            if seen == PAD_LW:
                res.append("\tnop")
    if seen < PAD_LW:
        sys.stderr.write(
            f"cc_post: pad-lw occurrence {PAD_LW} not found (only {seen})\n"
        )
        sys.exit(3)
    return res


def _rule10_remnant_prepass(lines: list[str]) -> list[str]:
    """Rule 10 pre-pass (--remnant-ori1 JOIN EXIT absorb|nop): re-insert the
    loop-entry guard that retail's cc1 pipeline keeps and GCC 2.6.3 folds
    away. Retail shape (witnessed on the LIBCD ISO9660 family, mainmenu_jp
    func_80077678 CD_newmedia 2026-11-01 + the parked func_80077A18
    CD_cachefile ladder, b08bd228): between the trace-gate join and the
    loop-invariant init block the retail stream carries
        ori  $2,$0,1
        beqz $2,<loop-exit>
        <delay: the count init, or a nop>
    - a never-taken branch on the constant-folded loop guard
    (count = 0 < 0x80) whose branch gcc's jump cleanup deletes in every
    source shape probed (11 banked loop shapes x pinned flags +
    -funroll-loops + -O3, then 6 more this window: do-while, while(1),
    while(A&&B), for-forms, -O1 - all delete or rotate the guard). The
    pair is DEAD CODE: $2 is loaded with 1, so beqz never fires, and $2's
    next definition is the loop head's own load - the delay-slot init
    executes unconditionally as before (MIPS delay slots run regardless
    of taken/untaken), so semantics are unchanged byte-for-byte.
    Marker: `cc-post: remnant-ori1 <join-label> <exit-label> absorb|nop` in
    the .c header; JOIN = the gcc label at the insertion point, EXIT = the
    loop-exit join the retail branch targets. absorb moves the join's
    first instruction (a $zero-based register init) into the branch's
    delay slot; nop emits a plain nop delay. Anchor mismatches FAIL the
    build loudly (exit 3) - the labels are gcc-deterministic for the
    frozen source, and any source edit that moves them must re-pin the
    marker. Only ever fires on marker-carrying units."""
    join_i = exit_i = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s == f"{REMANT_JOIN}:":
            join_i = i
        if s == f"{REMANT_EXIT}:":
            exit_i = i
    if join_i is None:
        sys.stderr.write(
            f"cc_post: remnant-ori1 join label {REMANT_JOIN}: not found\n"
        )
        sys.exit(3)
    if exit_i is None:
        sys.stderr.write(
            f"cc_post: remnant-ori1 exit label {REMANT_EXIT}: not found\n"
        )
        sys.exit(3)
    j = join_i + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    if j >= len(lines):
        sys.stderr.write("cc_post: remnant-ori1 join at end of file\n")
        sys.exit(3)
    ins = lines[j].strip()
    if REMANT_MODE == "absorb":
        if not re.match(r"^addu\t\$(\w+),\$0,\$zero$", ins):
            sys.stderr.write(
                f"cc_post: remnant-ori1 absorb anchor mismatch at "
                f"{REMANT_JOIN}: '{ins}'\n"
            )
            sys.exit(3)
        pair = ["\tori\t$2,$0,1", f"\tbeqz\t$2,{REMANT_EXIT}"]
    elif REMANT_MODE == "nop":
        pair = ["\tori\t$2,$0,1", f"\tbeqz\t$2,{REMANT_EXIT}", "\tnop"]
    else:
        sys.stderr.write(f"cc_post: remnant-ori1 bad mode '{REMANT_MODE}'\n")
        sys.exit(2)
    return lines[:j] + pair + lines[j:]


def apply_rules(insns: list[str]) -> list[str]:
    """Replace instruction subsequences in place; return new list."""
    res = list(insns)

    if not KEEP_EPILOGUE:
        res = _rule1_epilogue_swap(res)
    if SDK_ASPSX:
        res = _rule8_sdk_hazard_nop(res)
        res = _rule9_param_copy_order(res)
    res = _rule2_extend_pair(res)
    if not KEEP_RETURN_FILL:
        res = _rule3_return_move(res)
    if not KEEP_PROLOGUE:
        res = _rule4_prologue_save(res)
    res = _rule5_prologue_call(res)
    res = _rule7_gp_load(res)
    return res


LOAD_OP = re.compile(r"^(?:l(?:w|h|b|bu|hu|wl|wr)|ulw)\t\$(\w+),")
STORE_SYM = re.compile(r"^(?:s(?:w|h|b|d|wl|wr)|usw)\t\$(\w+),[A-Za-z_]")


def _rule8_sdk_hazard_nop(res: list[str]) -> list[str]:
    # Rule 8 (--sdk-aspsx): [load $X,..][store $X,<bare-symbol>] ->
    # [load $X][nop][store $X,<symbol>]. See header note 6.
    i = 0
    while i < len(res) - 1:
        m1 = LOAD_OP.match(res[i])
        if m1:
            m2 = STORE_SYM.match(res[i + 1])
            if m2 and m1.group(1) == m2.group(1):
                res[i + 1 : i + 1] = ["nop"]
                i += 2
                continue
        i += 1
    return res


PARAM_COPY_A = re.compile(r"^addu\t\$(\w+),\$5,\$zero$")
PARAM_COPY_B = re.compile(r"^addu\t\$(\w+),\$4,\$zero$")
ANDI_0XFF = re.compile(r"^andi\t\$2,\$(\w+),0x00ff$")


def _rule9_param_copy_order(res: list[str]) -> list[str]:
    # Rule 9 (--sdk-aspsx; found 2026-10-22, slps_00270 SsSetSerialVol,
    # the LIBSND SSSETSV member). GCC's first scheduler hoists the
    # a1-copy above the a0-copy so the a0-copy (the andi's input) sits
    # adjacent to the andi; retail keeps the a0-copy first:
    #     addu $A,$5,$zero        addu $B,$4,$zero
    #     addu $B,$4,$zero   ->   addu $A,$5,$zero
    #     andi $2,$B,0x00ff       andi $2,$B,0x00ff
    # Fires only on that exact three-instruction window; both copies
    # are pure register moves from distinct incoming-arg registers and
    # the andi still reads $B after the swap, so the reorder is
    # semantically a no-op.
    i = 0
    while i < len(res) - 2:
        mA = PARAM_COPY_A.match(res[i])
        if mA:
            mB = PARAM_COPY_B.match(res[i + 1])
            if mB and mB.group(1) != mA.group(1):
                mI = ANDI_0XFF.match(res[i + 2])
                if mI and mI.group(1) == mB.group(1):
                    res[i], res[i + 1] = res[i + 1], res[i]
                    i += 3
                    continue
        i += 1
    return res


_R15_SAVE = re.compile(r"^sw\t\$(\w+),(-?0x[0-9a-f]+|\d+)\(\$sp\)$")
_R15_COPY = re.compile(r"^addu\t\$(\w+),\$(\w+),\$zero$")
_R15_ORI = re.compile(r"^ori\t\$(\w+),\$zero,(-?(?:0x[0-9a-f]+|\d+))$")
_R15_JAL = re.compile(r"^jal\t\S+$")


def _rule15_on_run(res: list[str]):
    """Rule 15 (prologue-param-interleave; found 2026-11-03, g3org_jp
    SsVabOpenHeadWithMode 0x80068064, the LIBSND VS_VH WithMode member -
    window cron-202611032143). GCC 2.6.3 emits the batch prologue
        [frame][sw $ra][descending callee saves][import run][jal][delay]
    while this retail family interleaves every param import with its own
    save, keeps $ra LAST, then the leftover saves, and fills the first
    call's delay slot with a leftover save:
        [frame][sw $sN / import]{per import, in import order}[sw $ra]
        [leftover saves][jal][sw $sK]   (the next leftover save)
    The draft's pinned-local imports make gcc's import run ORDER already
    equal the retail pair order (verified draft4, window
    cron-202611032028), so the transform is a pure reorder:
    every import's frame save is pulled from the batch to sit adjacent,
    in import order (the jal-delay import folds in as the LAST import,
    exactly its retail position); $ra follows; the remaining saves keep
    their built order with the LAST of them sunk into the jal's delay
    slot (a save before the first callee - semantics unchanged: delay
    slots execute unconditionally and the slot is our own frame). All
    moved instructions are mutually independent (imports read only
    incoming-arg/zero registers; saves write only the frame); the reorder
    is semantically a no-op. Returns the transformed run or None when the
    shape does not match; the marker-scoped prepass loud-fails when NO run
    matches."""
    n = len(res)
    if n < 4 or not _FRAME_RE.match(res[0]):
        return None
    saves: dict[str, str] = {}
    save_order: list[str] = []
    i = 1
    while i < n:
        m = _R15_SAVE.match(res[i])
        if not m:
            break
        if m.group(1) in saves:
            return None
        saves[m.group(1)] = m.group(2)
        save_order.append(m.group(1))
        i += 1
    if not saves or ("31" not in saves and "ra" not in saves):
        return None
    imports: list[tuple[str, str]] = []
    while i < n:
        mC = _R15_COPY.match(res[i])
        mO = _R15_ORI.match(res[i]) if not mC else None
        if mC:
            imports.append((mC.group(1), res[i]))
        elif mO:
            imports.append((mO.group(1), res[i]))
        else:
            break
        i += 1
    if not imports:
        return None
    jal_idx = None
    delay_is_import = False
    if i < n and _R15_JAL.match(res[i]):
        jal_idx = i
        i += 1
        if i < n:
            mC = _R15_COPY.match(res[i])
            mO = _R15_ORI.match(res[i]) if not mC else None
            if mC:
                imports.append((mC.group(1), res[i]))
                delay_is_import = True
                i += 1
            elif mO:
                imports.append((mO.group(1), res[i]))
                delay_is_import = True
                i += 1
    for reg, _ in imports:
        if reg not in saves:
            return None  # an import whose save is not in the batch: not ours
    out = [res[0]]
    used: set[str] = set()
    for reg, ins in imports:
        out.append(f"sw\t${reg},{saves[reg]}($sp)")
        out.append(ins)
        used.add(reg)
    ra_reg = "31" if "31" in saves else "ra"
    out.append(f"sw\t${ra_reg},{saves[ra_reg]}($sp)")
    used.add(ra_reg)
    rest = [r for r in save_order if r not in used]
    if jal_idx is not None:
        if not rest:
            out.append(res[jal_idx])
            if not delay_is_import and jal_idx + 1 < n:
                out.append(res[jal_idx + 1])
                i = jal_idx + 2
        elif delay_is_import:
            for r in rest[:-1]:
                out.append(f"sw\t${r},{saves[r]}($sp)")
            out.append(res[jal_idx])
            # the folded import freed the delay slot; the next leftover
            # save takes it (the retail form; delay slots run regardless)
            out.append(f"sw\t${rest[-1]},{saves[rest[-1]]}($sp)")
        else:
            # built delay is not an import: sinking a save into the slot
            # would need to displace a real insn - not this rule's shape
            return None
    else:
        for r in rest:
            out.append(f"sw\t${r},{saves[r]}($sp)")
    out.extend(res[i:])
    return out


def _prepass_rule15(lines: list[str]) -> list[str]:
    """Marker rule15 (`cc-post: rule15`): apply _rule15_on_run to the first
    matching instruction run; loud failure (exit 3) when none matches -
    never a silent pass. Only ever fires on marker-carrying units."""
    runs: list[tuple[int, list[str]]] = []
    start = None
    cur: list[str] = []
    for idx, ln in enumerate(lines):
        s = ln.strip()
        if s and is_instruction(ln):
            if start is None:
                start = idx
            cur.append(s)
        else:
            if cur:
                runs.append((start, cur))
            start, cur = None, []
    if cur:
        runs.append((start, cur))
    for start, res in runs:
        fixed = _rule15_on_run(res)
        if fixed is not None:
            return lines[:start] + fixed + lines[start + len(res):]
    sys.stderr.write("cc_post rule 15: no interleavable prologue run found\n")
    sys.exit(3)


_R16_BEQ = re.compile(r"^beq\t\$(\w+),\$(\w+),(\S+)$")
_R16_COPY = re.compile(r"^addu\t\$(\w+),\$(\w+),\$(?:0|zero)$")
_R16_LI = re.compile(r"^(?:addiu|li)\t\$(\w+),(?:\$(?:0|zero),)?-(?:1|0x1)$")
_R16_CLOBBERED = frozenset(
    [str(n) for n in range(2, 16)] + ["24", "25", "v0", "v1",
     "a0", "a1", "a2", "a3", "t0", "t1", "t2", "t3", "t4", "t5", "t6",
     "t7", "t8", "t9"])
# rule 17 (merge-polarity): gcc 2.6.3 compiles the alloc-merge verdict
# `if (slot >= 16) goto err;` as `beq $rX,$0,<far-err>` (fail branches
# FAR, body falls through); this retail family keeps the OPPOSITE
# polarity - `bne $rX,$0,<join>` (+3, success branches past) with the
# inline 2-word err trampoline `j <far-err>` + the err-path delay insn
# (g3org_jp SsVabOpenHeadWithMode 0x80068188-class, window
# cron-202611041358; see _rule17_on_file).
_R17_BEQZ = re.compile(r"^beq\t\$(\w+),\$(0|zero),(\S+)$")
_R17_BEQZ_SPELL = re.compile(r"^beqz\t\$(\w+),(\S+)$")
_R18_SRL31 = re.compile(r"^srl\t\$(\w+),\$(\w+),31$")
_R18_BR = re.compile(r"^(bne|beq)\t\$(\w+),\$(0|zero),(\S+)$")
_R18_BRZ = re.compile(r"^(bnez|beqz)\t\$(\w+),(\S+)$")
_R17_JDELAY_OPS = frozenset(("li", "addiu", "addu", "nop"))


def _r16_jdelay_line(spec: tuple[str, str, str]) -> str:
    """Materialize the rule16 j-delay insn from marker args
    (`jdelay <op> <reg> <imm>`; the remnant-ori1 arg precedent - bare
    reg names, no $, so the shell never expands them)."""
    op, reg, imm = spec
    if op == "li":
        return "\tli\t$%s,%s" % (reg, imm)
    if op == "addiu":
        return "\taddiu\t$%s,$zero,%s" % (reg, imm)
    sys.stderr.write("cc_post rule 16: jdelay op must be li|addiu, got %s\n" % op)
    sys.exit(3)


def _rule16_on_file(lines: list[str], jdelay=None):
    """Rule 16 (verdict-polarity; found 2026-11-04, g3org_jp
    SsVabOpenHeadWithMode 0x80068064, the LIBSND VS_VH WithMode member -
    window cron-202611040358). GCC 2.6.3 compiles the early verdict
    `if (f() == 1) { return -1; }` as
        beq $vX,$vY,<fail-tail-label>
        addiu $vZ,$zero,-1     (delay: the fail value rides the branch
                                delay - gcc knows vZ is dead on the
                                continue path)
        <continue body...>
    while this retail family keeps the verdict inline with the OPPOSITE
    polarity (retail 0x800680A4: `bne $v0,$v1,+3` into the body, the
    fail tail as `j <tail>` with `li $v0,-1` in the JUMP's delay slot).
    gcc's polarity is NOT source-shape reachable (window
    cron-202611040243: the != 1 goto verdict re-inverts into beq-to-
    return, the else-head copy form keeps beq v0,v1 -> the merged tail),
    so the transform is a pure post-pass invert+reorder:
        bne $vX,$vY,$Lr16c     (inverted; the +3 offset == retail's)
        addiu $vZ,$zero,-1     (KEPT as the bne delay - branch delays run
                                unconditionally, so vZ = -1 on BOTH paths
                                exactly as built; no dataflow scan needed)
        j <fail-tail-label>    (the equal path jumps where beq did)
        addiu $vZ,$zero,-1     (the j delay: retail's fail materialize;
                                idempotent duplicate of the delay li)
        $Lr16c: <continue body...>
    Semantics: identical to the built form - the delay li is preserved
    verbatim, the equal path reaches the same tail with the same vZ.
    Fires on the FIRST `beq` + delay run whose target label is defined
    later in the file, in TWO delay classes:
      A. `(addiu|li) $c,-1` with $c call-clobbered (the fail value rides
         the delay dead on the continue path) - the j delay duplicates
         the built delay line verbatim (idempotent: the fail tail
         re-materializes it), or the R16_JDELAY marker insn when given.
      B. `addu $rD,$rS,$zero` with $rD NOT call-clobbered (a saved-reg
         copy rides the delay - WithMode draft7b form: s1 = the vabid
         copy the slot assign reads downstream) - the j delay MUST come
         from R16_JDELAY (loud exit 3 without it): the copy stays in the
         bne delay verbatim and the fail li is new, so duplicating the
         copy into the j delay would diverge from retail.
    Returns None when no site matches."""
    for i, ln in enumerate(lines):
        m = _R16_BEQ.match(ln.strip())
        if not m:
            continue
        target = m.group(3)
        if i + 1 >= len(lines):
            continue
        d = lines[i + 1].strip()
        md = _R16_LI.match(d)
        mc = _R16_COPY.match(d)
        if md and md.group(1) in _R16_CLOBBERED:
            jd = "\t" + d
            if jdelay is not None:
                jd = _r16_jdelay_line(jdelay)
        elif mc and mc.group(1) not in _R16_CLOBBERED:
            if jdelay is None:
                sys.stderr.write(
                    "cc_post rule 16: copy-delay verdict needs jdelay args "
                    "(`jdelay <op> <reg> <imm>`)\n")
                sys.exit(3)
            jd = _r16_jdelay_line(jdelay)
        else:
            continue
        forward = False
        for k in range(i + 2, len(lines)):
            if lines[k].strip() == target + ":":
                forward = True
                break
        if not forward:
            continue
        out = lines[:i]
        out.append("\tbne\t$%s,$%s,$Lr16c" % (m.group(1), m.group(2)))
        out.append("\t" + d)
        out.append("\tj\t" + target)
        out.append(jd)
        out.append("$Lr16c:")
        out.extend(lines[i + 2:])
        return out
    return None


def _prepass_rule16(lines: list[str]) -> list[str]:
    """Marker rule16 (`cc-post: rule16`): invert the first matching
    verdict (see _rule16_on_file); loud failure (exit 3) when nothing
    matches - never a silent pass. Only ever fires on marker-carrying
    units."""
    fixed = _rule16_on_file(lines, jdelay=R16_JDELAY)
    if fixed is not None:
        return fixed
    sys.stderr.write("cc_post rule 16: no inverting verdict (beq + li -1) found\n")
    sys.exit(3)


def _r17_jdelay_line(spec: tuple[str, str, str]) -> str:
    """Materialize the rule17 trampoline j-delay insn from marker args
    (`jdelay <op> <reg> <imm>`; the rule16 arg precedent - bare reg
    names, no $, so the shell never expands them). Ops: li/addiu (the
    rule16 materializers), addu (reg-copy: `addu $reg,$imm,$zero` -
    gcc 2.6.3's own zero-arg spelling, the WithMode trampoline's
    a0=0-class delay), nop (an empty delay slot)."""
    op, reg, imm = spec
    if op == "nop":
        return "\tnop"
    if op == "addu":
        return "\taddu\t$%s,$%s,$zero" % (reg, imm)
    return _r16_jdelay_line(spec)


def _rule17_on_file(lines: list[str], anchor: str, jdelay=None):
    """Rule 17 (merge-polarity; parked as the cc_post candidate since
    draft16, window cron-202611041128; shipped cron-202611041358).
    GCC 2.6.3 compiles the alloc-merge verdict as
        beq $rX,$0,<far-err-label>   (fail branches FAR to the shared
                                      err tail; body falls through)
        <delay insn>
        <continue body...>
    while this retail family keeps the OPPOSITE polarity with the err
    trampoline INLINE (retail g3org_jp 0x80068188-class: `bne
    $rX,$0,+3` - success branches past - followed by the 2-word pair
    `j <far-err-label>` + the err-path delay insn, then the join):
        bne $rX,$0,$Lr17c      (inverted; the +3 offset == retail's -
                                the join sits exactly past the pair)
        <delay insn>           (KEPT verbatim - branch delays run
                                unconditionally, so the built's own
                                delay still executes on BOTH paths)
        j <far-err-label>      (the fail path jumps where beq did)
        <jdelay insn>          (the err-path delay from the marker -
                                WithMode: a0=0, the err tail's
                                setInTransfer(0) arg riding the
                                trampoline's j delay)
        $Lr17c:
        <continue body...>
    Semantics: identical to the built form - the success path skips
    the pair, the fail path reaches the same tail through it.

    The site is ANCHORED on the far-err label (marker arg; the rule-10
    precedent - gcc-deterministic for the frozen source, anchor
    mismatch = loud exit 3, never a silent skip): the file carries
    many other `beq $r,$0,<label>` tests (loop back-edges, local
    joins) that must NOT invert; only the verdict whose target is the
    shared far err tail gets the trampoline. The j-delay content is
    NOT derivable from the built site (it is the err tail's own first
    call-arg setup hoisted into the trampoline) so it is REQUIRED from
    the marker (`jdelay <op> <reg> <imm>`, op li|addiu|addu|nop) -
    loud exit 3 without it.
    Returns None when no site matches."""
    for i, ln in enumerate(lines):
        s = ln.strip()
        m = _R17_BEQZ.match(s)
        if m:
            reg, zeroop, target = m.group(1), m.group(2), m.group(3)
        else:
            mz = _R17_BEQZ_SPELL.match(s)
            if not mz:
                continue
            reg, zeroop, target = mz.group(1), "0", mz.group(2)
        if target != anchor:
            continue
        if i + 1 >= len(lines):
            continue
        d = lines[i + 1].strip()
        if not is_instruction(d):
            continue  # empty delay slot / malformed site - no match
        forward = False
        for k in range(i + 2, len(lines)):
            if lines[k].strip() == anchor + ":":
                forward = True
                break
        if not forward:
            continue
        out = lines[:i]
        out.append("\tbne\t$%s,$%s,$Lr17c" % (reg, zeroop))
        out.append("\t" + d)
        out.append("\tj\t" + anchor)
        out.append(_r17_jdelay_line(jdelay))
        out.append("$Lr17c:")
        out.extend(lines[i + 2:])
        return out
    return None


def _prepass_rule17(lines: list[str]) -> list[str]:
    """Marker rule17 (`cc-post: rule17 <$Lerr> jdelay <op> <reg> <imm>`):
    invert the anchored merge verdict + insert the err trampoline (see
    _rule17_on_file); loud failure (exit 3) when nothing matches -
    never a silent pass. Only ever fires on marker-carrying units."""
    anchor, jdelay = RULE17_MERGE
    fixed = _rule17_on_file(lines, anchor, jdelay=jdelay)
    if fixed is not None:
        return fixed
    sys.stderr.write("cc_post rule 17: no merge site (beq $r,$0,%s with a "
                     "filled forward delay) found\n" % anchor)
    sys.exit(3)


def _rule18_lt0_scc(lines: list[str]):
    """Rule 18 (lt0-scc; shipped cron-202611061501). The (x < 0) VALUE
    materialization: the Sony psyq cc1 emits the scc form
        slti $d,$s,0
    where the vanilla gcc 2.6.3 rebuild always takes emit_store_flag's
    sign-extract special case
        srl $d,$s,31
    Proven cron-202611061501 at three levels: (a) the cc1 -da pass dump
    of the staged unit - the lshiftrt-31 exists already in the .rtl dump
    (the very first), so the pick happens at expansion (store_flag) and
    NO pass introduces it; (b) the scc-path control - a materialized
    (x < 5) emits slt (the scc path exists and fires for nonzero
    constants) while const-0 never reaches it under any of the 12
    probed spellings (the special case fires first for op1 == const0);
    (c) semantics - srl-31 and slti-0 both materialize the sign bit as
    0/1, identical for every input, so the rewrite is unconditional.
    Retail anchor: g3org_jp SsVabOpenHeadWithMode row [221] (0x800683D8)
    = `slti $v0,$v1,0x0` (word 0x28620000) where the built emits
    `srl $2,$3,31`.

    Site contract: `srl $d,$s,31` whose IMMEDIATE successor tests $d
    against $0 (bne/beq $d,$0,<label> or bnez/beqz $d,<label>) - the
    branch test is the value's only use. The div-correction srl-31s
    (the expand_divmod DIRECT lshiftrt, retail-aligned as-built) are
    followed by addu and never match.

    Returns (rewritten_lines, count), or None when no site matches (the
    prepass turns None / a count mismatch into a loud exit 3 - never a
    silent pass)."""
    out = list(lines)
    n = 0
    for i in range(len(out) - 1):
        m = _R18_SRL31.match(out[i].strip())
        if not m:
            continue
        dst, src = m.group(1), m.group(2)
        nxt = out[i + 1].strip()
        mb = _R18_BR.match(nxt)
        if mb:
            if mb.group(2) != dst:
                continue
        else:
            mz = _R18_BRZ.match(nxt)
            if not mz or mz.group(2) != dst:
                continue
        out[i] = "\tslti\t$%s,$%s,0" % (dst, src)
        n += 1
    if n == 0:
        return None
    return out, n


def _prepass_lt0_scc(lines: list[str]) -> list[str]:
    """Marker rule18 (`cc-post: lt0-scc <count>`): rewrite the (x<0)
    sign-extract materializations into the retail scc form (see
    _rule18_lt0_scc); loud failure (exit 3) when no site matches or the
    rewritten count differs from the marker count - never a silent
    pass. Only ever fires on marker-carrying units."""
    res = _rule18_lt0_scc(lines)
    if res is None:
        sys.stderr.write("cc_post rule 18: no lt0 site (srl $d,$s,31 "
                         "followed by a $d-vs-$0 branch) found\n")
        sys.exit(3)
    out, n = res
    if n != LT0_SCC:
        sys.stderr.write("cc_post rule 18: rewrote %d site(s), marker "
                         "expects %d\n" % (n, LT0_SCC))
        sys.exit(3)
    return out


_R19_SPREL = re.compile(r"^(sw|lw)\t\$(\w+),(\d+)\(\$sp\)$")
_R19_FRAME = re.compile(r"^\.frame\t\$sp,(\d+),")
_R19_MASK = re.compile(r"^\.mask\t0x([0-9a-fA-F]+),")
_R19_BRANCH_OPS = ("beq", "bne", "blez", "bgtz", "bltz", "bgez",
                   "bltzal", "bgezal", "j", "jal", "beql", "bnel",
                   "blezl", "bgtzl")


def _rule19_site_fresh_const(lines: list[str], imm: str, reg: str):
    """Rule 19 (site-fresh-const; survey docs/CC_POST_RULE_CLASSES.md
    section 3, window cron-202611070601). The hoisted-constant spill
    class: gcc 2.6.3's regalloc materializes a loop-invariant constant
    into a callee-saved home
        addiu $<reg>,$zero,<imm>     <- hoisted before the loop
        ... beq $X,$<reg>,<label>    <- the site compare
    with an sw/lw $<reg>,K($sp) spill pair, where retail materializes
    the constant FRESH at the site into $2 (v0) and never saves the
    home register (the func_8007736C -1 sentinel: built `addiu
    $22,$zero,-1` hoisted + `beq $4,$22`; retail `addiu $2,$zero,-1`
    fresh + `beq $4,$2`, no s6 word, the frame one slot shorter). The
    source-side escape hatches are all refuted (probe c4: the sep2
    lever needs a non-latch-dominating conditional def; the "0" tie
    inherits the hoisted register; def-before-call forces callee-saved)
    - the fix is a post-pass. Transform, all shape-verified, loud-fail
    on any mismatch:
      1. exactly one `addiu $<reg>,$zero,<imm>` (the hoisted def);
      2. exactly one branch use of $<reg>, one sw, one lw (same K) -
         any other $<reg> reference loud-fails (the home must be
         single-purpose or the spill is load-bearing);
      3. topmost-slot check: every $sp displacement ABOVE K belongs to
         $31/$ra only (a middle-slot delete would need a
         gap-preserving remap - reject);
      4. retarget the branch's $<reg> operand to $2 and insert
         `addiu $2,$zero,<imm>` directly before the branch, whose
         nearest preceding instruction must exist and not be a
         branch/jump (never split a delay-slot pair);
      5. delete the def and the spill pair;
      6. frame renumber: every sw/lw displacement above K shifts -4 (ra
         takes the deleted slot's place; the frame TOTAL and .frame
         stay - retail keeps the size with the freed slot as top pad,
         retail-decoded 2026-11-07), the .mask bit for $<reg> clears.
    Semantics: $<reg> holds the constant on every path (single def),
    so the fresh $2 def is equivalent on every predecessor; the insert
    executes unconditionally within its block immediately before the
    branch, so $2's prior value is dead there by construction. $2 is
    the assembler scratch - the judge verdict (live only) is the
    semantic gate, these textual checks are the fast-fail.
    Returns the rewritten lines or None when the shape does not match
    (the prepass turns None into a loud exit 3 - never a silent pass).
    Only ever fires on marker-carrying units."""
    out = list(lines)
    regnum = reg.lstrip("$")
    tok = re.compile(re.escape(reg) + r"(?![0-9])")
    # comment lines (maspsx's `#nop # DEBUG: ...` notes quote real insns
    # and would pollute the ref census) never count as references
    refs = [i for i, ln in enumerate(out)
            if tok.search(ln) and not ln.strip().startswith("#")]
    def_line = f"addiu\t${regnum},$zero,{imm}"
    def_idx = [i for i in refs if out[i].strip() == def_line]
    if len(def_idx) != 1:
        return None
    sw_idx = [i for i in refs
              if (m := _R19_SPREL.match(out[i].strip()))
              and m.group(1) == "sw" and m.group(2) == regnum]
    lw_idx = [i for i in refs
              if (m := _R19_SPREL.match(out[i].strip()))
              and m.group(1) == "lw" and m.group(2) == regnum]
    br_idx = [i for i in refs
              if out[i].strip().split("\t")[0] in ("beq", "bne")]
    if len(sw_idx) != 1 or len(lw_idx) != 1 or len(br_idx) != 1:
        return None
    k_sw = int(_R19_SPREL.match(out[sw_idx[0]].strip()).group(3))
    k_lw = int(_R19_SPREL.match(out[lw_idx[0]].strip()).group(3))
    if k_sw != k_lw:
        return None
    k = k_sw
    others = (set(refs) - set(def_idx) - set(sw_idx)
              - set(lw_idx) - set(br_idx))
    if others:
        return None
    for ln in out:
        m = _R19_SPREL.match(ln.strip())
        if m and int(m.group(3)) > k and m.group(2) != "31":
            return None  # a non-ra slot sits above K: not the topmost
    b = br_idx[0]
    j = b - 1
    while j >= 0 and not is_instruction(out[j]):
        j -= 1
    if j < 0:
        return None
    prev_op = out[j].strip().split("\t")[0]
    if prev_op in _R19_BRANCH_OPS:
        return None  # never split a delay-slot pair
    # 4. retarget + (later) insert
    out[b] = tok.sub(lambda m: "$2", out[b], count=1)
    # 5. delete def + spill pair (blank lines carry no bytes)
    out[def_idx[0]] = ""
    out[sw_idx[0]] = ""
    out[lw_idx[0]] = ""
    # 6. frame renumber: displacements above K shift -4
    for i, ln in enumerate(out):
        if not _R19_SPREL.match(ln.strip()):
            continue
        out[i] = re.sub(r",(\d+)\(\$sp\)",
                        lambda m: ("," + str(int(m.group(1)) - 4) + "($sp)"
                                   if int(m.group(1)) > k else m.group(0)),
                        ln, count=1)
    fm = None
    for ln in out:
        m = _R19_FRAME.match(ln.strip())
        if m:
            fm = int(m.group(1))
            break
    if fm is None or fm <= k:
        return None
    # THE FRAME SIZE STAYS (retail-decoded, mainmenu_jp func_8007736C:
    # retail `addiu $sp,$sp,-80` with ra at 72 and slot 76 as top pad -
    # the callee-save area's ra slot shrinks by the deleted register but
    # gcc's frame TOTAL is unchanged; only the $sp displacements above K
    # shift). The first implementation renounced the frame to 76 and
    # judged 150/186 - the retail decode refuted it the same window.
    for i, ln in enumerate(out):
        s = ln.strip()
        mm = _R19_MASK.match(s)
        if mm and int(regnum) <= 31:
            mask = int(mm.group(1), 16)
            if mask & (1 << int(regnum)):
                out[i] = ln.replace(mm.group(1),
                                    f"{mask & ~(1 << int(regnum)):08x}", 1)
    # 4b. insert the fresh def directly before the (retargeted) branch
    out.insert(b, f"addiu\t$2,$zero,{imm}")
    return out


def _prepass_site_fresh_const(lines: list[str]) -> list[str]:
    """Marker rule19 (`cc-post: site-fresh-const <imm> <reg>`): retarget
    the hoisted-constant spill class to retail's fresh $2 def at the
    compare site, delete the spill pair and renumber the frame (see
    _rule19_site_fresh_const); loud failure (exit 3) when the shape
    does not match - never a silent pass. Only ever fires on
    marker-carrying units."""
    imm, reg = SITE_FRESH_CONST
    res = _rule19_site_fresh_const(lines, imm, reg)
    if res is None:
        sys.stderr.write(
            "cc_post rule 19: site-fresh-const shape not found "
            f"(need exactly one hoisted `addiu {reg},$zero,{imm}` with "
            "one branch use, one same-slot sw/lw pair, no other refs, "
            "the slot topmost below $ra, and a non-branch predecessor "
            "at the compare)\n")
        sys.exit(3)
    return res


# rule 21 (import-order; survey docs/CC_POST_RULE_CLASSES.md section 5,
# window cron-202611070716): the prologue import-pair order class. The
# func_8007736C built prologue interleaves (sw $s3,0x3c / addu $s3,$a1)
# before (sw $s5,0x44 / addu $s5,$a0) where retail imports $s5 FIRST
# (fresh judge artifacts + wordmap [20]-[32], 2026-11-07: retail sw
# $s5,0x44 / move $s5,$a0 / sw $s3,0x3c / move $s3,$a1). All three
# source-side order levers are refuted (the c3 declaration order, the K&R
# register-param form kr1, the early asm-input use c6: judged 127/186,
# +5 WORSE) - the init-copy order is not first-use-driven in gcc 2.6.3,
# so the reorder is a post-pass. Transform, shape-verified, loud-fail on
# any mismatch:
#   1. within a contiguous instruction run, locate the frame insn
#      (subu/addiu $sp,$sp,N) and parse the consecutive save/copy region
#      after it (sw $r,off($sp) = save; addu $r,$s,$zero and
#      ori $r,$zero,imm = import copy), stopping at the first other insn;
#   2. the region's copy-dest set must equal the marker's listed set
#      exactly (count check), and each listed reg needs exactly one copy;
#   3. independence: no copy may read any copy's dest register (the
#      attested imports read only incoming args / $zero) - a pure reorder
#      of mutually independent insns, semantically a no-op;
#   4. rebuild the region: each listed reg's items (its save + its copy,
#      in their built internal order) first, in the listed order, then
#      the remaining items (pure saves: ra, other callee-saves) in their
#      built order.
# rule15 and rule21 both reshape the prologue - never combine them on one
# unit (rule15's parser assumes the batched save run that rule21's pair
# form does not carry; the attested 7736C shape needs rule21 alone).
def _rule21_import_order(lines: list[str], order: list[str]):
    want = [r.lstrip("$") for r in order if r.strip()]
    if not want or len(want) != len(set(want)):
        return None
    for start_line in range(len(lines)):
        stripped = lines[start_line].strip()
        if not stripped or not is_instruction(lines[start_line]):
            continue
        if not _FRAME_RE.match(stripped):
            continue
        items: list[tuple[str, str]] = []  # (kind, reg); kind: save|copy
        j = start_line + 1
        while j < len(lines):
            s = lines[j].strip()
            if not s or not is_instruction(lines[j]):
                break
            mS = _R15_SAVE.match(s)
            mC = _R15_COPY.match(s)
            mO = _R15_ORI.match(s) if not mC else None
            if mS:
                items.append(("save", mS.group(1)))
            elif mC:
                items.append(("copy", mC.group(1)))
            elif mO:
                items.append(("copy", mO.group(1)))
            else:
                break
            j += 1
        if not items:
            continue
        dests = [r for k, r in items if k == "copy"]
        if len(dests) != len(set(dests)) or set(dests) != set(want):
            continue
        saves: dict[str, int] = {}
        ok = True
        for kind, reg in items:
            if kind == "save":
                if reg in saves:
                    ok = False
                    break
                saves[reg] = 1
        if not ok:
            continue
        # independence: no copy reads any copy's dest (incl. its own)
        bad = False
        for idx, (kind, reg) in enumerate(items):
            if kind != "copy":
                continue
            s = lines[start_line + 1 + idx].strip()
            mC = _R15_COPY.match(s)
            if mC and mC.group(2).lstrip("$") in dests:
                bad = True
                break
        if bad:
            continue
        rebuilt: list[str] = []
        # re-emit from the ORIGINAL lines: walk the region once, taking
        # each reg's items in their built internal order
        order_lines: dict[str, list[str]] = {r: [] for r in dests}
        rest_lines: list[str] = []
        for off, (kind, reg) in enumerate(items):
            ln = lines[start_line + 1 + off]
            if reg in order_lines:
                order_lines[reg].append(ln)
            else:
                rest_lines.append(ln)
        for reg in want:
            rebuilt.extend(order_lines[reg])
        rebuilt.extend(rest_lines)
        return lines[:start_line + 1] + rebuilt + lines[j:]
    return None


def _prepass_import_order(lines: list[str]) -> list[str]:
    """Marker rule21 (`cc-post: import-order <reg>,<reg>[,...]`): reorder
    the prologue import (save, copy) pairs to the listed register order
    (see _rule21_import_order); loud failure (exit 3) when no region
    matches - never a silent pass. Only ever fires on marker-carrying
    units."""
    res = _rule21_import_order(lines, IMPORT_ORDER)
    if res is None:
        sys.stderr.write(
            "cc_post rule 21: import-order shape not found (need a "
            "prologue region whose import-copy dest set is exactly "
            f"{','.join(IMPORT_ORDER)}, each dest with one save and one "
            "copy, no copy reading another copy's dest)\n")
        sys.exit(3)
    return res


# rule 20 (vol-extend; survey docs/CC_POST_RULE_CLASSES.md section 4,
# shipped cron-202611070146): the volatile-load zero-extend. gcc 2.6.3
# volatile reads bypass the zero-extend tracking, so the copy-exit
# re-load's byte gets an explicit `andi $d,$s,0x00ff` at the merge where
# retail's cc1 feeds the re-load's result to the merged zero-test
# directly (probe c7 banked the source laws: no C spelling yields both
# the real re-load AND no andi - a plain read gets CSE-eliminated - and
# the asm-memory-clobber route breaks maspsx's delay-slot handling, so
# the fix cannot ride the source).
_R20_ANDI = re.compile(r"^andi\t\$(\w+),\$(\w+),0x00ff$")
_R20_LBU = re.compile(r"^lbu\t\$(\w+),")
_R20_BRZ = re.compile(r"^(?:beqz|bnez)\t\$(\w+),")
_R20_BR = re.compile(r"^(?:beq|bne)\t\$(\w+),\$(?:0|zero),")


def _rule20_vol_extend(lines: list[str]):
    """Rule 20 site scan. Site contract (shape-verified, never default-on
    - an `andi $r,$r,0x00ff` is a genuine zero-extend elsewhere in the
    corpus; the counted marker is the attestation):
        lbu $s,<...>       <- the volatile re-load
        [nop]              <- maspsx's load-use fill (the empirical c3
                              merge site carries exactly one)
        andi $d,$s,0x00ff  <- THE WORD (blanked; blank lines carry no
                              bytes for the assembler)
        [<label>: ...]     <- the merge label carries no bytes
        beq|bne $d,$0,<l> / beqz|bnez $d,<l>   <- the merged zero test
    The backward walk skips only nops and non-instruction lines (one nop
    max, the load-use fill) - any other real instruction between the lbu
    and the andi breaks the src law; the forward walk skips only
    non-instruction lines.

    Returns (rewritten_lines, count), or None when no site matches (the
    prepass turns None / a count mismatch into a loud exit 3 - never a
    silent pass)."""
    out = list(lines)
    n = 0
    for i, ln in enumerate(out):
        m = _R20_ANDI.match(ln.strip())
        if not m:
            continue
        dst, src = m.group(1), m.group(2)
        # backward: the previous real instruction must be the lbu that
        # defines the andi's src (one maspsx load-use nop tolerated - raw
        # maspsx emits it DEBUG-annotated: `nop # DEBUG: Reuse of ...`;
        # the prepasses run BEFORE main's NOP normalization, so the walk
        # must use the same NOP pattern the main loop normalizes by)
        j = i - 1
        while j >= 0 and not is_instruction(out[j]):
            j -= 1
        if j >= 0 and NOP.match(out[j].strip()):
            j -= 1
            while j >= 0 and not is_instruction(out[j]):
                j -= 1
        if j < 0:
            continue
        ml = _R20_LBU.match(out[j].strip())
        if not ml or ml.group(1) != src:
            continue
        # forward: the next real instruction must be the zero test on dst
        k = i + 1
        while k < len(out) and not is_instruction(out[k]):
            k += 1
        if k >= len(out):
            continue
        mb = _R20_BRZ.match(out[k].strip()) or _R20_BR.match(out[k].strip())
        if not mb or mb.group(1) != dst:
            continue
        out[i] = ""
        n += 1
    if n == 0:
        return None
    return out, n


def _prepass_vol_extend(lines: list[str]) -> list[str]:
    """Marker rule20 (`cc-post: vol-extend <count>`): blank the
    volatile-re-load merge andi (see _rule20_vol_extend); loud failure
    (exit 3) when no site matches or the deleted count differs from the
    marker count - never a silent pass. Only ever fires on
    marker-carrying units."""
    res = _rule20_vol_extend(lines)
    if res is None:
        sys.stderr.write("cc_post rule 20: no vol-extend site (andi $d,$s,"
                         "0x00ff whose src is the preceding lbu's dest and "
                         "whose dest feeds the following zero-test) found\n")
        sys.exit(3)
    out, n = res
    if n != VOL_EXTEND:
        sys.stderr.write("cc_post rule 20: blanked %d site(s), marker "
                         "expects %d\n" % (n, VOL_EXTEND))
        sys.exit(3)
    return out


def _rule1_epilogue_swap(res: list[str]) -> list[str]:
    res = list(res)

    # Rule 1 (n-load variant, n >= 2): [lw $ra][lw $rX]{n}[addu $sp]
    # [j $ra](nop)? -> [lw $ra][lw $rX]{n}[j $ra][addu $sp] (nop
    # absorbed). Generalizes the byte-verified three-load variant
    # (n = 2) to any n >= 2 - the game-code k >= 4 epilogue thunks
    # (func_8002B444-class, k = 6) put the frame release in the branch
    # delay slot. Checked first: the two-load window [lw $rX][addu][j]
    # sits inside this shape and would otherwise fire first and
    # mis-swap.
    i = 0
    while i < len(res) - 4:
        if not LW_RA.match(res[i]):
            i += 1
            continue
        j = i + 1
        while (j < len(res) and LW_SREG.match(res[j])
               and LW_SREG.match(res[j]).group(1) not in ("31", "ra", "29", "sp")):
            j += 1
        if (j - (i + 1) >= 2 and j + 1 < len(res)
                and ADDU_SP.match(res[j]) and JUMP_RA.match(res[j + 1])):
            tail_nop = (j + 2 < len(res) and NOP.match(res[j + 2]))
            res[i : j + (3 if tail_nop else 2)] = (
                res[i:j] + [res[j + 1], res[j]])
            i = j + 2
            continue
        i += 1

    # Rule 1 (two-load variant): [lw $ra][lw $rX,N($sp)][addu $sp]
    # [j $ra](nop)? -> [lw $ra][lw $rX][j $ra][addu $sp] (nop absorbed).
    # Checked first: the plain variant below cannot fire on this shape
    # (the frame release is not adjacent to the $ra reload).
    i = 0
    while i < len(res) - 3:
        m_ra, m_sx = LW_RA.match(res[i]), LW_SREG.match(res[i + 1])
        if (m_ra and m_sx and m_sx.group(1) not in ("31", "ra", "29", "sp")
                and ADDU_SP.match(res[i + 2]) and JUMP_RA.match(res[i + 3])):
            tail_nop = (i + 4 < len(res) and NOP.match(res[i + 4]))
            res[i : i + (5 if tail_nop else 4)] = [
                res[i], res[i + 1], res[i + 3], res[i + 2]
            ]
            i += 4
            continue
        i += 1

    # Rule 1: [lw $ra][addu $sp][j $ra](nop)? -> [lw][nop][j][addu]
    i = 0
    while i < len(res) - 2:
        if (LW_RA.match(res[i]) and ADDU_SP.match(res[i + 1])
                and JUMP_RA.match(res[i + 2])):
            tail_nop = (i + 3 < len(res) and NOP.match(res[i + 3]))
            res[i : i + (4 if tail_nop else 3)] = [
                res[i], "nop", res[i + 2], res[i + 1]
            ]
            i += 4
            continue
        i += 1

    return res


def _rule2_extend_pair(res: list[str]) -> list[str]:
    # Rule 2: [sll A][sll C][sra A][sra C] -> [sll A][sra A][sll C][sra C]
    i = 0
    while i < len(res) - 3:
        m1, m2 = SLL16.match(res[i]), SLL16.match(res[i + 1])
        m3, m4 = SRA16.match(res[i + 2]), SRA16.match(res[i + 3])
        if m1 and m2 and m3 and m4:
            pa = (m1.group(1), m1.group(2))
            pc = (m2.group(1), m2.group(2))
            if pa == (m3.group(1), m3.group(2)) and pc == (m4.group(1), m4.group(2)) \
                    and pa != pc:
                res[i : i + 4] = [res[i], res[i + 2], res[i + 1], res[i + 3]]
                i += 4
                continue
        i += 1

    return res


def _rule3_return_move(res: list[str]) -> list[str]:
    # Rule 3: [j $ra][addu $2,$X,$zero] -> [addu][j $ra][nop]
    i = 0
    while i < len(res) - 1:
        if JUMP_RA.match(res[i]):
            m = MOVE_V0.match(res[i + 1])
            if m and m.group(1) != "2":
                res[i : i + 2] = [res[i + 1], res[i], "nop"]
                i += 3
                continue
        i += 1

    return res


def _rule4_prologue_save(res: list[str]) -> list[str]:
    # Rule 4: [subu $sp][v0 imm][sw $ra] -> [subu $sp][sw $ra][v0 imm]
    i = 0
    while i < len(res) - 2:
        if (FRAME_ALLOC.match(res[i]) and V0_IMM.match(res[i + 1])
                and SW_RA.match(res[i + 2])):
            res[i : i + 3] = [res[i], res[i + 2], res[i + 1]]
            i += 3
            continue
        i += 1

    return res


def _rule5_prologue_call(res: list[str]) -> list[str]:
    # Rule 5: [frame-alloc][ALU X][sw $ra][jal T][sw $rS,N($sp)] ->
    #         [frame-alloc][sw $ra][sw $rS][jal T][X]
    # (the call's delay slot gets X; the spill moves next to the $ra
    # save). Guards below make the five instructions mutually
    # independent: X must not touch $sp or the spill's source register,
    # and must not itself be a spill of $ra.
    i = 0
    while i < len(res) - 4:
        if (FRAME_ALLOC.match(res[i]) and ALU_X.match(res[i + 1])
                and SW_RA.match(res[i + 2]) and JAL_CALL.match(res[i + 3])):
            m_x = ALU_X.match(res[i + 1])
            m_sx = SW_SREG.match(res[i + 4])
            if (m_sx and m_sx.group(1) not in ("31", "ra", "29", "sp")
                    and "sp" not in res[i + 1]
                    and m_x.group(1) not in ("29", "sp", "31", "ra")
                    and m_x.group(1) != m_sx.group(1)):
                res[i : i + 5] = [
                    res[i], res[i + 2], res[i + 4], res[i + 3], res[i + 1]
                ]
                i += 5
                continue
        i += 1

    return res


def _rule7_gp_load(res: list[str]) -> list[str]:
    # Rule 7: [frame-alloc][lw $r,N($gp)] -> [lw $r,N($gp)][frame-alloc]
    i = 0
    while i < len(res) - 1:
        if FRAME_ALLOC.match(res[i]):
            m = LW_GP_ANY.match(res[i + 1])
            if m and m.group(1) not in ("29", "sp"):
                res[i], res[i + 1] = res[i + 1], res[i]
                i += 2
                continue
        i += 1

    return res


_FRAME_RE = re.compile(r"^(?:subu|addiu)\t\$sp,\$sp,(-?0x[0-9a-f]+|\d+)$")
_SAVE_RE = re.compile(r"^sw\t\$(\w+),(-?0x[0-9a-f]+|\d+)\(\$sp\)$")
_COPY_RE = re.compile(r"^addu\t\$(\w+),\$(\w+),\$zero$")
_JAL_RE = re.compile(r"^jal\t(\S+)$")
_ARG_ALU_RE = re.compile(
    r"^(?:addu\t\$(\w+),\$0,(?:\$0|\$zero)$"
    r"|ori\t\$(\w+),\$zero,[-0-9xa-f0-9]+)$")


def _prepass_prologue_param_first(lines: list[str]) -> list[str]:
    """Marker prologue-param-first: hoist the first param copy's save, the
    copy and the constant block above the $ra save; sink the param-byte sb
    into the first call's delay slot; hoist the call's arg ALU out of it.
    Scans the whole file for the prologue run; loud failure (exit 3) when
    no run matches - never a silent pass."""
    # split into maximal instruction runs, find the one that matches
    runs = []
    cur = []
    for ln in lines:
        if is_instruction(ln) and ln.strip() and not ln.strip().startswith("."):
            cur.append(ln.strip())
        else:
            if cur:
                runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    for res in runs:
        fixed = _rule11_on_run(res)
        if fixed is not None:
            # splice: replace this run's lines in the file, preserving
            # non-instruction lines around it
            out = []
            i = 0
            matched = False
            for ln in lines:
                if (not matched and i < len(res) and ln.strip() == res[i]
                        and is_instruction(ln)):
                    out.append(ln)  # placeholder, rebuilt below
                    i += 1
                    if i == len(res):
                        pass
                else:
                    out.append(ln)
            # simpler: operate positionally
            start = None
            for pos in range(len(lines) - len(res) + 1):
                window = [x.strip() for x in lines[pos:pos + len(res)]]
                if window == res:
                    start = pos
                    break
            if start is None:
                continue
            rebuilt = list(lines[:start])
            j = 0
            for k, ln in enumerate(lines[start:start + len(res)]):
                rebuilt.append("\t" + fixed[k])
            rebuilt += lines[start + len(res):]
            return rebuilt
    sys.stderr.write("cc_post rule 11: no run matches the prologue shape\n")
    sys.exit(3)


_ADDU_IMM_RE = re.compile(r"^addu\t\$(\w+),(\$\w+),(-?(?:0x[0-9a-f]+|\d+))$")


def _prepass_addiu_imm(lines: list[str]) -> list[str]:
    """Marker addiu-imm: retail's sdk bodies keep addu for register-only
    sums; EVERY immediate-form sum is addiu (CdGetToc2 2026-11-02: the
    sp-relative address materializations are addiu in retail, gcc emits
    addu for the pointer sums). Pure rewrite, no reorder."""
    out = []
    for ln in lines:
        m = _ADDU_IMM_RE.match(ln.strip())
        if m:
            out.append("\taddiu\t$%s,%s,%s" % (m.group(1), m.group(2), m.group(3)))
        else:
            out.append(ln)
    return out


_PIN_RE = re.compile(r"^addiu\t\$(\w+),\$sp,(-?(?:0x[0-9a-f]+|\d+))$")
_PIN_READ_RE = re.compile(r"^addu\t\$(\w+),\$(\w+),\$zero$")


def _prepass_addr_pin_late(lines: list[str]) -> list[str]:
    """Marker addr-pin-late: retail positions the stack-address pin inside
    the consuming call's argument sequence (CdGetToc2 58F58..58F64: ori /
    addu / addiu s1,sp,0x18 / addu a2,s1), gcc -O1 emits it at the
    assignment statement, before the whole arg block. Move the pin down to
    just before the first insn that reads its register, provided every
    insn in between is an arg-setup ALU that never reads the pin register.
    Loud failure when no pin block matches."""
    out = list(lines)
    for i, ln in enumerate(out):
        m = _PIN_RE.match(ln.strip())
        if not m:
            continue
        pin = m.group(1)
        j = i + 1
        while j < len(out):
            s2 = out[j].strip()
            mr = _PIN_READ_RE.match(s2)
            if mr and mr.group(2) == pin:
                break  # the consumer
            if s2.startswith("jal") or s2.endswith(":") or s2.startswith("."):
                break
            # in-between insns must be arg-setup ALUs not reading the pin
            if pin in s2:
                break
            j += 1
        else:
            continue
        if j >= len(out) or j == i + 1:
            continue
        pin_line = out[i]
        del out[i]
        j -= 1
        out.insert(j, pin_line)
        return out
    sys.stderr.write("cc_post rule 14: no addr-pin block matched\n")
    sys.exit(3)


_V0_CONS_RE = re.compile(r"^addu\t\$(\w+),\$2,\$zero$")


def _prepass_v0_sink(lines: list[str]) -> list[str]:
    """Marker v0-sink: gcc's -O1 delay filler keeps the post-call v0
    consumer (handle = f(0)'s return -> callee-saved) right after the
    call; retail sinks it into the NEXT call's delay slot, swapping with
    that call's own delay insn (an arg setup that hoists into the body).
    Sound: the consumer still reads the FIRST call's v0 (nothing between
    the two calls touches v0 - guarded), and the delay executes before
    the second callee runs. Loud failure when no sink site matches."""
    out = list(lines)
    for i, ln in enumerate(out):
        m = _V0_CONS_RE.match(ln.strip())
        if not m:
            continue
        cons_reg = m.group(1)
        # scan forward for the next jal within the same run
        j = i + 1
        body = []
        while j < len(out):
            s2 = out[j].strip()
            if s2.startswith("jal\t") or s2.startswith("jal "):
                break
            if (s2.endswith(":") or s2.startswith(".") or not s2
                    or s2.startswith("#")):
                break
            if _V0_CONS_RE.match(s2) or "$2" in s2 or "v0" in s2:
                break  # another v0 touch - refuse
            body.append(j)
            j += 1
        else:
            continue
        if j >= len(out):
            return out
        jal_line = out[j]
        # the call's delay slot: the next instruction line
        k = j + 1
        if k >= len(out):
            continue
        old_delay = out[k].strip()
        if old_delay.endswith(":") or not old_delay:
            continue
        # V sinks into the call's delay slot; the old delay insn (an arg
        # setup) hoists to just before the jal, keeping the arg-setup group
        # adjacent to the call (retail order, CdGetToc2 58F58..58F6C)
        del out[i]
        j -= 1
        k -= 1
        out.insert(j, out[k])
        del out[k + 1]
        out.insert(k + 1, "\taddu\t$%s,$2,$zero" % cons_reg)
        return out
    sys.stderr.write("cc_post rule 13: no v0-consumer sink site found\n")
    sys.exit(3)


def _rule11_on_run(res: list[str]):
    """Return the transformed run, or None when the shape does not match."""
    n = len(res)
    if n < 8 or not _FRAME_RE.match(res[0]):
        return None
    # the save run: consecutive sw-to-frame lines, $ra's among them
    saves = []  # (index, reg, offset)
    i = 1
    while i < n:
        m = _SAVE_RE.match(res[i])
        if not m:
            break
        saves.append((i, m.group(1), m.group(2)))
        i += 1
    regs = {r for _, r, _ in saves}
    if "31" not in regs and "ra" not in regs:
        return None
    # the param copy: addu $sA, <arg>, $zero right after the run
    m = _COPY_RE.match(res[i])
    if not m or m.group(1) not in regs or m.group(2) not in (
            "4", "5", "6", "7", "a0", "a1", "a2", "a3"):
        return None
    copy_reg = m.group(1)
    copy_idx = i
    i += 1
    # the constant block up to the jal: ALUs plus at most one sb-to-frame
    block = []
    sb_idx = None
    while i < n and not _JAL_RE.match(res[i]):
        if _SAVE_RE.match(res[i]):
            return None
        if _ARG_ALU_RE.match(res[i]) or True:
            if res[i].startswith("sb\t") and res[i].endswith("($sp)"):
                if sb_idx is not None:
                    return None
                sb_idx = len(block)
            block.append(res[i])
        i += 1
    if i >= n or sb_idx is None:
        return None
    jal_idx = i
    m_jal = _JAL_RE.match(res[jal_idx])
    delay_idx = jal_idx + 1
    if delay_idx >= n or not _ARG_ALU_RE.match(res[delay_idx]):
        return None
    delay_alu = res[delay_idx]
    # reassemble
    save_sA = next((s for s in saves if s[1] == copy_reg), None)
    if save_sA is None:
        return None
    rest_saves = [s for s in saves if s[1] != copy_reg]
    out = [res[0], res[save_sA[0]], res[copy_idx]]
    out += [b for j, b in enumerate(block) if j != sb_idx]
    out.append(delay_alu)
    out += [res[s[0]] for s in rest_saves]
    out.append(res[jal_idx])
    out.append(block[sb_idx])
    return out


def main() -> None:
    global KEEP_EPILOGUE, SDK_ASPSX, KEEP_RETURN_FILL, KEEP_PROLOGUE
    global REMANT_JOIN, REMANT_EXIT, REMANT_MODE
    global SWAP_REGS, ADDU_COMMUTE_N, DELAY_SB_OUT, SAVE_SWAP, PAD_LW
    global PROLOGUE_PARAM_FIRST, ADDIU_IMM, V0_SINK, ADDR_PIN_LATE
    global RULE15_INTERLEAVE, RULE16_VERDICT, R16_JDELAY, RULE17_MERGE
    global LT0_SCC, SITE_FRESH_CONST, IMPORT_ORDER, VOL_EXTEND
    args = sys.argv[1:]
    if "--keep-epilogue" in args:
        KEEP_EPILOGUE = True
        args.remove("--keep-epilogue")
    if "--keep-return-fill" in args:
        KEEP_RETURN_FILL = True
        args.remove("--keep-return-fill")
    if "--keep-prologue" in args:
        KEEP_PROLOGUE = True
        args.remove("--keep-prologue")
    if "--prologue-param-first" in args:
        PROLOGUE_PARAM_FIRST = True
        args.remove("--prologue-param-first")
    if "--rule15" in args:
        RULE15_INTERLEAVE = True
        args.remove("--rule15")
    if "--rule16" in args:
        RULE16_VERDICT = True
        k = args.index("--rule16")
        args.pop(k)
        # optional `jdelay <op> <reg> <imm>` payload immediately after the
        # flag (cc.sh passes the marker args verbatim, in position)
        if len(args) > k and args[k] == "jdelay":
            if len(args) < k + 4:
                sys.stderr.write(
                    "usage: cc_post.py --rule16 jdelay <op> <reg> <imm> ...\n")
                sys.exit(2)
            R16_JDELAY = (args[k + 1], args[k + 2], args[k + 3])
            del args[k : k + 4]
    if "--rule17" in args:
        k = args.index("--rule17")
        # required payload: `<anchor> jdelay <op> <reg> <imm>` immediately
        # after the flag (cc.sh passes the marker args verbatim, in
        # position; a bare marker never reaches here - cc.sh loud-fails
        # on it first)
        if len(args) < k + 6 or args[k + 2] != "jdelay":
            sys.stderr.write(
                "usage: cc_post.py --rule17 <anchor> jdelay <op> <reg> <imm> ...\n")
            sys.exit(2)
        RULE17_MERGE = (args[k + 1], (args[k + 3], args[k + 4], args[k + 5]))
        if RULE17_MERGE[1][0] not in _R17_JDELAY_OPS:
            sys.stderr.write(
                "cc_post rule 17: jdelay op must be li|addiu|addu|nop, got %s\n"
                % RULE17_MERGE[1][0])
            sys.exit(2)
        del args[k : k + 6]
    if "--site-fresh-const" in args:
        k = args.index("--site-fresh-const")
        # required payload: `<imm> <reg>` (cc.sh passes the marker args
        # verbatim, in position; a bare flag is a usage error)
        if len(args) < k + 3:
            sys.stderr.write(
                "usage: cc_post.py --site-fresh-const <imm> <reg> ...\n")
            sys.exit(2)
        SITE_FRESH_CONST = (args[k + 1], args[k + 2])
        del args[k : k + 3]
    if "--import-order" in args:
        k = args.index("--import-order")
        # required payload: the comma-joined register order (cc.sh passes
        # the marker arg verbatim, in position; a bare flag is a usage
        # error - the rule-17 bare-marker lesson, never a silent default)
        if len(args) < k + 2 or not args[k + 1]:
            sys.stderr.write(
                "usage: cc_post.py --import-order <reg>,<reg>[,...] ...\n")
            sys.exit(2)
        IMPORT_ORDER = [r for r in args[k + 1].split(",") if r]
        del args[k : k + 2]
    if "--lt0-scc" in args:
        k = args.index("--lt0-scc")
        # required payload: the expected site count (cc.sh passes the
        # marker arg verbatim; a bare flag is a usage error - the rule-17
        # bare-marker lesson, never a silent default)
        if len(args) < k + 2:
            sys.stderr.write("usage: cc_post.py --lt0-scc <count> ...\n")
            sys.exit(2)
        try:
            LT0_SCC = int(args[k + 1])
        except ValueError:
            sys.stderr.write("cc_post rule 18: --lt0-scc requires an integer "
                             "count (usage: cc_post.py --lt0-scc <count> "
                             "<file.mas.s>); got %s\n" % args[k + 1])
            sys.exit(2)
        if LT0_SCC < 1:
            sys.stderr.write("cc_post rule 18: count must be >= 1\n")
            sys.exit(2)
        del args[k : k + 2]
    if "--vol-extend" in args:
        k = args.index("--vol-extend")
        # required payload: the expected site count (cc.sh passes the
        # marker arg verbatim; a bare flag is a usage error - the rule-17
        # bare-marker lesson, never a silent default)
        if len(args) < k + 2:
            sys.stderr.write("usage: cc_post.py --vol-extend <count> ...\n")
            sys.exit(2)
        try:
            VOL_EXTEND = int(args[k + 1])
        except ValueError:
            sys.stderr.write("cc_post rule 20: --vol-extend requires an integer "
                             "count (usage: cc_post.py --vol-extend <count> "
                             "<file.mas.s>); got %s\n" % args[k + 1])
            sys.exit(2)
        if VOL_EXTEND < 1:
            sys.stderr.write("cc_post rule 20: count must be >= 1\n")
            sys.exit(2)
        del args[k : k + 2]
    if "--addiu-imm" in args:
        ADDIU_IMM = True
        args.remove("--addiu-imm")
    if "--v0-sink" in args:
        V0_SINK = True
        args.remove("--v0-sink")
    if "--addr-pin-late" in args:
        ADDR_PIN_LATE = True
        args.remove("--addr-pin-late")
    if "--sdk-aspsx" in args:
        KEEP_EPILOGUE = True
        SDK_ASPSX = True
        args.remove("--sdk-aspsx")
    if "--remnant-ori1" in args:
        k = args.index("--remnant-ori1")
        if len(args) < k + 4:
            sys.stderr.write(
                "usage: cc_post.py --remnant-ori1 <join> <exit> <absorb|nop> ...\n"
            )
            sys.exit(2)
        REMANT_JOIN, REMANT_EXIT, REMANT_MODE = args[k + 1 : k + 4]
        del args[k : k + 4]
    if "--swap-regs" in args:
        k = args.index("--swap-regs")
        if len(args) < k + 3:
            sys.stderr.write("usage: cc_post.py --swap-regs <regA> <regB> ...\n")
            sys.exit(2)
        SWAP_REGS = (args[k + 1], args[k + 2])
        del args[k : k + 3]
    if "--save-swap" in args:
        k = args.index("--save-swap")
        if len(args) < k + 3:
            sys.stderr.write("usage: cc_post.py --save-swap <regA> <regB> ...\n")
            sys.exit(2)
        SAVE_SWAP = (args[k + 1], args[k + 2])
        del args[k : k + 3]
    if "--pad-lw" in args:
        k = args.index("--pad-lw")
        if len(args) < k + 2:
            sys.stderr.write("usage: cc_post.py --pad-lw <n> ...\n")
            sys.exit(2)
        PAD_LW = int(args[k + 1])
        del args[k : k + 2]
    if "--addu-commute" in args:
        k = args.index("--addu-commute")
        if len(args) < k + 2:
            sys.stderr.write("usage: cc_post.py --addu-commute <n> ...\n")
            sys.exit(2)
        ADDU_COMMUTE_N = int(args[k + 1])
        del args[k : k + 2]
    if "--delay-sb-out" in args:
        DELAY_SB_OUT = True
        args.remove("--delay-sb-out")
    if len(args) != 1:
        sys.stderr.write(
            "usage: cc_post.py [--keep-epilogue|--sdk-aspsx] <file.mas.s>\n"
        )
        sys.exit(2)
    path = args[0]
    lines = open(path).read().splitlines()
    if REMANT_JOIN is not None:
        lines = _rule10_remnant_prepass(lines)
    if SWAP_REGS is not None:
        lines = _prepass_swap_regs(lines)
    if SAVE_SWAP is not None:
        lines = _prepass_save_swap(lines)
    if PAD_LW is not None:
        lines = _prepass_pad_lw(lines)
    if ADDU_COMMUTE_N is not None:
        lines = _prepass_addu_commute(lines)
    if DELAY_SB_OUT:
        lines = _prepass_delay_sb_out(lines)
    if PROLOGUE_PARAM_FIRST:
        lines = _prepass_prologue_param_first(lines)
    if RULE15_INTERLEAVE:
        lines = _prepass_rule15(lines)
    if RULE16_VERDICT:
        lines = _prepass_rule16(lines)
    if RULE17_MERGE is not None:
        lines = _prepass_rule17(lines)
    if LT0_SCC is not None:
        lines = _prepass_lt0_scc(lines)
    if SITE_FRESH_CONST is not None:
        lines = _prepass_site_fresh_const(lines)
    if IMPORT_ORDER is not None:
        lines = _prepass_import_order(lines)
    if VOL_EXTEND is not None:
        lines = _prepass_vol_extend(lines)
    if ADDIU_IMM:
        lines = _prepass_addiu_imm(lines)
    if V0_SINK:
        lines = _prepass_v0_sink(lines)
    if ADDR_PIN_LATE:
        lines = _prepass_addr_pin_late(lines)

    out: list[str] = []
    run: list[int] = []  # indices into out of consecutive instructions
    raw: dict[int, str] = {}  # original line per index (for output)

    def flush() -> None:
        if run:
            fixed = apply_rules([out[i].strip() for i in run])
            # map: run positions up to len(run) stay in place; grown tail
            # after. A rule may also SHRINK the run (rule 1 two-load variant
            # absorbs the trailing nop): blank the surplus slots - blank
            # lines carry no bytes for the assembler.
            last = run[-1]
            for pos, i in enumerate(run):
                out[i] = fixed[pos] if pos < len(fixed) else ""
            grow = fixed[len(run):]
            if grow:
                out[last + 1 : last + 1] = grow
                # original lines after the insertion point shift; since the
                # run is flushed atomically and out beyond last is untouched
                # until now, appending grow right after last keeps order
        run.clear()

    for line in lines:
        stripped = line.strip()
        if NOPLIKE.match(stripped):
            continue  # maspsx 'decided not to insert' marker - no bytes
        if not stripped:
            continue  # maspsx blank after each call delay slot - no bytes
        if NOP.match(stripped):
            line = "\tnop"
        if is_instruction(line):
            run.append(len(out))
            out.append(line.strip())
        else:
            flush()
            out.append(line)
    flush()

    open(path, "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
