/* MATCHING: verbatim retail bytes as a hand-asm unit (bare
 * file-scope asm; no C body, no compiler framing). The global
 * label sits where the bytes are so cross-object callers resolve. */
__asm__(
    ".section .r_000235E0, \"awx\", @progbits\n\t"
    ".set noreorder\n\t"
    ".globl func_80042DE0\n\t"
    "func_80042DE0:\n\t"
        ".set noreorder\n\t"
        "sw $v0, 0x1c($a0)\n\t"
        "jr $ra\n\t"
        "sw $v0, 0x20($a0)\n\t"
    ".set reorder\n\t");
