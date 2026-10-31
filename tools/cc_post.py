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


def main() -> None:
    global KEEP_EPILOGUE, SDK_ASPSX, KEEP_RETURN_FILL, KEEP_PROLOGUE
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
    if "--sdk-aspsx" in args:
        KEEP_EPILOGUE = True
        SDK_ASPSX = True
        args.remove("--sdk-aspsx")
    if len(args) != 1:
        sys.stderr.write("usage: cc_post.py [--keep-epilogue|--sdk-aspsx] <file.mas.s>\n")
        sys.exit(2)
    path = args[0]
    lines = open(path).read().splitlines()

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
