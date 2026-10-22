/* MATCHING: verbatim retail bytes as a hand-asm unit (bare
 * file-scope asm; no C body, no compiler framing). The global
 * label sits where the bytes are so cross-object callers resolve. */
__asm__(
    ".section .r_00026B68, \"awx\", @progbits\n\t"
    ".set noreorder\n\t"
    ".globl func_80046368\n\t"
    "func_80046368:\n\t"
        ".set noreorder\n\t"
        "beqz $v0, 1f\n\t"
        "move $v0, $v1\n\t"
        "addiu $v0, $zero, -1\n\t"
        "1:\n\t"
        "jr $ra\n\t"
    ".set reorder\n\t");
