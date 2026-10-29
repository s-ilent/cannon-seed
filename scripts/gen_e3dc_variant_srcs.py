#!/usr/bin/env python3
"""gen_e3dc_variant_srcs.py - emit the E3DC-early-variant wave's seven
per-row src units (the memclr one-src-unit-per-row law: the row name is the
unit name). Body = the landed compose-rotation anchor's transcription with
the commit moved to the THIRD pointer: the five packed product stores and
the return addu move from $4 to $6 (the six-word delta the pre-check
proves); the prototype gains the out argument. Headers carry no func_ name
mentions beyond the definition (one ratchet mention per file).
"""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

MEMBERS = [
    ("slps_00270", "func_80034138"),
    ("sces_00269", "func_80033C00"),
    ("mainmenu_eu", "func_8005D4FC"),
    ("g3_jp", "func_80049608"),
    ("g3_eu", "func_80049020"),
    ("g3org_jp", "func_80046AA4"),
    ("g3org_eu", "func_80046474"),
]

TEMPLATE = """/* The compose-rotation writer family's third form - the commit-at-out
 * variant ({target} row, one src unit per row under the row's own walk
 * name; the seven members are byte-identical 0x10c rows, one per target
 * except mainmenu_jp). Body = the landed compose-rotation anchor's
 * transcription (the two-arg commit-at-(a0) form) with the commit moved to
 * the THIRD pointer: the head still loads the current rotation matrix from
 * (a0) via ctc2 into c0..c4, the three MVMVA 1,0,0,3,0 passes multiply the
 * packed three-vector record at (a1) exactly as the anchor schedules them
 * (staging interleaved with the previous pass's mfc2 reads), then the five
 * packed product words store at (a2) - halfword interleave
 * [w0=v1.x|v2.x, w1=v3.x|v2.x, w2=v3.y|v2.y, w3=v1.z|v2.z, w4=v3.z],
 * IR3 of the third pass stored raw as swc2 - and the return value is the
 * out pointer. Word-level identity: the pre-check (scripts/e3dcv_check.py)
 * proves the seven retail rows byte-identical and the delta vs the landed
 * anchor exactly the six commit-destination words (five stores + return
 * addu, $4 -> $6).
 *
 * psyq prototype: long *<row>(long *m, long *rec, long *out); args
 * stay long* so gcc emits no caller-side extensions; the record's packed
 * interleave is the caller's contract (this body never unmasks it).
 */
long *{name}(long *m, long *rec, long *out)
{{
    register long *ret asm("$2");
    __asm__ volatile(
        "lw $8, 0x0($4)\\n"
        "\\tlw $9, 0x4($4)\\n"
        "\\tlw $10, 0x8($4)\\n"
        "\\tlw $11, 0xc($4)\\n"
        "\\tlw $12, 0x10($4)\\n"
        "\\tctc2 $8, $0\\n"
        "\\tctc2 $9, $1\\n"
        "\\tctc2 $10, $2\\n"
        "\\tctc2 $11, $3\\n"
        "\\tctc2 $12, $4\\n"
        "\\tlhu $8, 0x0($5)\\n"
        "\\tlw $9, 0x4($5)\\n"
        "\\tlw $10, 0xc($5)\\n"
        "\\tlui $1, 0xffff\\n"
        "\\tand $9, $9, $1\\n"
        "\\tor $8, $8, $9\\n"
        "\\tmtc2 $8, $0\\n"
        "\\tmtc2 $10, $1\\n"
        "\\tnop\\n"
        "\\t.word 0x4A486012\\n" /* mvmva 1,0,0,3,0 */
        "\\tlhu $8, 0x2($5)\\n"
        "\\tlw $9, 0x8($5)\\n"
        "\\tlh $10, 0xe($5)\\n"
        "\\tsll $9, $9, 16\\n"
        "\\tor $8, $8, $9\\n"
        "\\tmfc2 $11, $9\\n"
        "\\tmfc2 $12, $10\\n"
        "\\tmfc2 $13, $11\\n"
        "\\tmtc2 $8, $0\\n"
        "\\tmtc2 $10, $1\\n"
        "\\tnop\\n"
        "\\t.word 0x4A486012\\n" /* mvmva 1,0,0,3,0 */
        "\\tlhu $8, 0x4($5)\\n"
        "\\tlw $9, 0x8($5)\\n"
        "\\tlw $10, 0x10($5)\\n"
        "\\tlui $1, 0xffff\\n"
        "\\tand $9, $9, $1\\n"
        "\\tor $8, $8, $9\\n"
        "\\tmfc2 $14, $9\\n"
        "\\tmfc2 $15, $10\\n"
        "\\tmfc2 $24, $11\\n"
        "\\tmtc2 $8, $0\\n"
        "\\tmtc2 $10, $1\\n"
        "\\tnop\\n"
        "\\t.word 0x4A486012\\n" /* mvmva 1,0,0,3,0 */
        "\\tandi $11, $11, 0xffff\\n"
        "\\tsll $14, $14, 16\\n"
        "\\tor $14, $14, $11\\n"
        "\\tsw $14, 0x0($6)\\n"
        "\\tandi $13, $13, 0xffff\\n"
        "\\tsll $24, $24, 16\\n"
        "\\tor $24, $24, $13\\n"
        "\\tsw $24, 0xc($6)\\n"
        "\\tmfc2 $8, $9\\n"
        "\\tmfc2 $9, $10\\n"
        "\\tandi $8, $8, 0xffff\\n"
        "\\tsll $12, $12, 16\\n"
        "\\tor $8, $8, $12\\n"
        "\\tsw $8, 0x4($6)\\n"
        "\\tandi $15, $15, 0xffff\\n"
        "\\tsll $9, $9, 16\\n"
        "\\tor $9, $9, $15\\n"
        "\\tsw $9, 0x8($6)\\n"
        "\\tswc2 $11, 0x10($6)\\n"
        "\\taddu $2, $6, $0"
        : "=r"(ret));
    return ret;
}}
"""

for target, name in MEMBERS:
    p = REPO / f"src/{name}.c"
    p.write_text(TEMPLATE.format(target=target, name=name))
    print(f"wrote src/{name}.c")
