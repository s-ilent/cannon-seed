/* MATCHING: verbatim retail bytes as a hand-asm unit (bare
 * file-scope asm; no C body, no compiler framing). The global
 * label sits where the bytes are so cross-object callers resolve. */
__asm__(
    ".section .r_000122BC, \"awx\", @progbits\n\t"
    ".set noreorder\n\t"
    ".globl func_80031ABC\n\t"
    "func_80031ABC:\n\t"
        ".set noreorder\n\t"
        "lui $at, 0x800c\n\t"
        "sw $v0, -0x7298($at)\n\t"
        "jr $ra\n\t"
        "nop\n\t"
    ".set reorder\n\t");
