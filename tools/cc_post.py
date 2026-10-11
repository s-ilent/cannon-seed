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

Every rule triggers on a narrow, byte-verified pattern; anything that
does not match passes through untouched. The SHA-1 oracle gates the
result either way.
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


def apply_rules(insns: list[str]) -> list[str]:
    """Replace instruction subsequences in place; return new list."""
    res = list(insns)

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


def main() -> None:
    if len(sys.argv) != 2:
        sys.stderr.write("usage: cc_post.py <file.mas.s>\n")
        sys.exit(2)
    path = sys.argv[1]
    lines = open(path).read().splitlines()

    out: list[str] = []
    run: list[int] = []  # indices into out of consecutive instructions
    raw: dict[int, str] = {}  # original line per index (for output)

    def flush() -> None:
        if run:
            fixed = apply_rules([out[i].strip() for i in run])
            # map: run positions up to len(run) stay in place; grown tail after
            last = run[-1]
            for pos, i in enumerate(run):
                out[i] = fixed[pos]
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
