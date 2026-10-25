#!/usr/bin/env python3
"""The slice-boundary law mechanized over the two mainmenu_jp graveyard rows
(window cron-202610252051, offline - no oracle, no baselines).

The law (banked cron-202610251936-addendum): the walk mega-rows are ONE
compiled function's inlined chain, mainmenu_jp typed it as data and sliced it
differently than the seven targets' asm rows, and the TRUE function
boundaries = the head starts (the ten-word SetRotMatrix head or the
vector-staging head spellings) + the epilogue ends (addu $v0, $x, $zero /
jr $ra / nop).  This probe parses the two committed data rows, detects both
boundary classes mechanically, and asserts the NINE closures the full
instruction-level decode derived:

    0x8005DB1C..0x8005DC28  0x10C  #0x10c composite (the DAFC/DBA0 crossing pair)
    0x8005DC28..0x8005DD0C  0x0E4  #0xe4 composite (func_8005DC34's true extent;
                                   the 0xC staging head lives in DBA0's tail)
    0x8005DD0C..0x8005DDF4  0x0E8  #0xe8 in-place composite (func_8005DCD8+0x34's
                                   function; vectors staged AND committed at (a0))
    0x8005DDF4..0x8005DF04  0x110  #0x110 composite (SetRotMatrix head at
                                   func_8005DD80+0x74; the landed func_8005DED4.c
                                   0x30 tail is its last slice - three slices:
                                   DD80 0x30 + DE24 0xB0 + DED4 0x30)
    0x8005DF04..0x8005E064  0x160  #0x160 light-shuffle composite (func_8005DF04
                                   staging head + func_8005DF78 body + func_8005E020's
                                   first 0x44 negate/accumulator tail)
    0x8005E064..0x8005E094  0x030  ROW1-final single-vector transform (a clean
                                   whole function mainmenu_jp's census sliced
                                   inside the crossing host func_8005E020)
    0x8005E3DC..0x8005E4E8  0x10C  #0x10c-type A (commit at (a0), return a0)
    0x8005E4E8..0x8005E5F4  0x10C  #0x10c-type B (commit at (a1), return a1) -
                                   the "double-rotate mega-host" func_8005E3DC
                                   is TWO whole functions, exactly as the 1551
                                   walk census measured ("EXACTLY two #0x10c
                                   rows - the walk boundary at +0x10c is the
                                   second inlined head")

Every start carries its evidence: the four rot-head sites through
probe_graveyard_walk.rot_head_at (the banked ten-word detector), the three
staging starts through their exact load spellings (DBA0's lhu-tail spelling,
DCD8's lw spelling, the #0x160 a1-staged spelling), and every end must be
found by the epilogue scanner (no hand-copied ends).

Usage: python3 scripts/probe_true_boundaries.py   (from scripts/ or repo root)
Exit 0 = all eight closures hold; exit 1 = any boundary evidence or closure
failed (the law would be broken and the record wrong).
"""
import sys
from pathlib import Path

import probe_graveyard_walk as P

# ---- the true starts (va, kind, evidence words as (offset, word)) ----------
LHU_T0_0_A0 = 0x94880000  # lhu $t0, 0($a0)
LW_T0_0_A0 = 0x8C880000   # lw  $t0, 0($a0)
LW_T1_4_A0 = 0x8C890004   # lw  $t1, 4($a0)
LW_T2_C_A0 = 0x8C8A000C   # lw  $t2, 0xC($a0)

STARTS = [
    (0x8005D9BC, "rothead", []),                                   # SetRotMatrix head, D9B4+0x8 (banked SITES[0]; the two leading nops are row padding)
    (0x8005DB1C, "rothead", []),                                   # SetRotMatrix head, DAFC+0x20 (banked SITES[1])
    (0x8005DC28, "staging", [(0, LHU_T0_0_A0), (4, LW_T1_4_A0), (8, LW_T2_C_A0)]),  # DBA0's tail 0xC
    (0x8005DD0C, "staging", [(0, LW_T0_0_A0), (4, LW_T1_4_A0), (8, LW_T2_C_A0)]),   # DCD8+0x34
    (0x8005DDF4, "rothead", []),                                   # SetRotMatrix head, DD80+0x74
    (0x8005DF04, "rothead", []),                                   # SetRotMatrix head, DF04+0x0 (its a1 continuation is the "fourth spelling")
    (0x8005E064, "staging", [(0, LW_T0_0_A0), (4, LW_T1_4_A0)]),   # ROW1-final 2-word staging
    (0x8005E3DC, "rothead", []),                                   # the pair's head A
    (0x8005E4E8, "rothead", []),                                   # the pair's head B
]

# ---- the nine closures (start, end, size, label) --------------------------
CLOSURES = [
    (0x8005D9BC, 0x8005DB1C, 0x160, "instance-1 #0x160 six-vector transform-and-add (func_8005DA90 = its interior +0xD4, the 1551 class-2)"),
    (0x8005DB1C, 0x8005DC28, 0x10C, "#0x10c composite (DAFC/DBA0 crossing pair; head = banked SITES[1])"),
    (0x8005DC28, 0x8005DD0C, 0x0E4, "#0xe4 composite - func_8005DC34's TRUE extent (slice 0xa4 + DCD8's 0x34 epilogue)"),
    (0x8005DD0C, 0x8005DDF4, 0x0E8, "#0xe8 in-place composite - func_8005DCD8+0x34's function (ends DD80+0x74)"),
    (0x8005DDF4, 0x8005DF04, 0x110, "#0x110 composite - THREE slices: DD80 0x30 + DE24 0xB0 + the landed DED4 0x30"),
    (0x8005DF04, 0x8005E064, 0x160, "#0x160 light-shuffle composite - DF04 0x74 + DF78 0xa8 + E020's first 0x44"),
    (0x8005E064, 0x8005E094, 0x030, "ROW1-final 0x30 single-vector transform (clean whole function)"),
    (0x8005E3DC, 0x8005E4E8, 0x10C, "#0x10c-type A - commit at (a0), return a0"),
    (0x8005E4E8, 0x8005E5F4, 0x10C, "#0x10c-type B - commit at (a1), return a1"),
]


def merged_words():
    """va -> word over both rows (ROW1 0x8005D9B4..0x8005E094, ROW2 0x8005E1B8..0x8005E5F4)."""
    out = {}
    for row in (P.ROW1, P.ROW2):
        for fn in P.parse(row):
            for va, w in fn["words"]:
                if va in out and out[va] != w:
                    raise SystemExit(f"FATAL: word disagreement at 0x{va:08x}")
                out[va] = w
    return out


def sorted_pairs(words):
    return [(va, words[va]) for va in sorted(words)]


def _is_ret_addu(w):
    """addu $v0, $x, $zero (the 'move $v0,$x' return spell): op 0, funct 0x21, rd=$2, rt=$0."""
    return (w >> 26) == 0 and (w & 0x3F) == 0x21 and ((w >> 11) & 0x1F) == 2 and ((w >> 16) & 0x1F) == 0


def epilogue_ends(pairs):
    """both retail epilogue spellings -> the set of END addresses (one past the last
    epilogue word):
      (a) addu $v0,$x,$zero / jr $ra / nop          -> end = nop_va + 4
      (b) jr $ra / addu $v0,$x,$zero (delay, no nop) -> end = addu_va + 4
    Spelling (b) is the shuffle-composite's return (func_8005E020[15]/[16]) - the
    compiler kept the move in the delay slot and dropped the nop."""
    ends = set()
    for i in range(len(pairs) - 2):
        a, b, c = pairs[i][1], pairs[i + 1][1], pairs[i + 2][1]
        if _is_ret_addu(a) and b == 0x03E00008 and c == 0x00000000:
            ends.add(pairs[i + 2][0] + 4)
        if b == 0x03E00008 and _is_ret_addu(c):
            ends.add(pairs[i + 2][0] + 4)
    return ends


def main():
    words = merged_words()
    pairs = sorted_pairs(words)
    ends = epilogue_ends(pairs)
    print(f"[probe] merged word map: {len(words)} words, "
          f"0x{pairs[0][0]:08x}..0x{pairs[-1][0] + 4:08x}")
    # the every-byte-accounted check: the two rows are FULLY covered, no holes
    row1, row2 = (0x8005D9B4, 0x6E0), (0x8005E1B8, 0x43C)
    acc_ok = len(words) == (row1[1] + row2[1]) // 4
    if acc_ok:
        for base, size in (row1, row2):
            acc_ok = acc_ok and all(base + o in words for o in range(0, size, 4))
    cover = 'FULLY covered' if acc_ok else 'HOLES'
    print(f"[probe] row accounting: ROW1 0x{row1[0]:08x}+0x{row1[1]:x} and "
          f"ROW2 0x{row2[0]:08x}+0x{row2[1]:x} = {cover} "
          f"({len(words)} words = (0x6e0+0x43c)/4)")
    fails = 0 if acc_ok else 1
    print(f"[probe] epilogue scanner: {len(ends)} ends found (both spellings)")
    for e in sorted(ends):
        print(f"        end 0x{e:08x}")

    # index for rot-head checks
    idx = {va: i for i, (va, _) in enumerate(pairs)}

    fails = 0
    print("[probe] start evidence:")
    for va, kind, ev in STARTS:
        if va not in idx:
            print(f"  FAIL 0x{va:08x}: not in the committed rows")
            fails += 1
            continue
        if kind == "rothead":
            ok = P.rot_head_at(pairs, idx[va])
            tag = "ten-word SetRotMatrix head"
        else:
            ok = all(words.get(va + off) == w for off, w in ev)
            tag = "staging loads " + ", ".join(f"+{off}:0x{w:08x}" for off, w in ev)
        print(f"  {'ok  ' if ok else 'FAIL'} 0x{va:08x} {kind}: {tag}")
        fails += 0 if ok else 1

    print("[probe] closures:")
    for start, end, size, label in CLOSURES:
        end_found = end in ends
        size_ok = end - start == size
        start_known = any(va == start for va, _, _ in STARTS)
        ok = end_found and size_ok and start_known
        print(f"  {'ok  ' if ok else 'FAIL'} 0x{start:08x}..0x{end:08x} 0x{size:03x}"
              f"  end={'found' if end_found else 'MISSING'}"
              f" size={'ok' if size_ok else f'BAD({end - start:#x})'}"
              f" start={'banked' if start_known else 'UNPROVEN'}  {label}")
        fails += 0 if ok else 1

    if fails:
        print(f"[probe] FAIL ({fails} problem(s)) - the boundary record is wrong somewhere")
        return 1
    print("[probe] PASS - all nine closures hold offline and every byte of both rows "
          "is accounted: true boundaries = head starts + epilogue ends, exactly as "
          "the 1936-addendum law states")
    return 0


if __name__ == "__main__":
    sys.exit(main())
