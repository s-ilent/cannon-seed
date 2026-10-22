/* MATCHING: verbatim retail bytes as a hand-asm unit (bare
 * file-scope asm; no C body, no compiler framing). The global
 * label sits where the bytes are so cross-object callers resolve. */
__asm__(
    ".section .r_00029064, \"awx\", @progbits\n\t"
    ".set noreorder\n\t"
    ".globl func_80048864\n\t"
    "func_80048864:\n\t"
        ".set noreorder\n\t"
        "syscall\n\t"
        "jr $ra\n\t"
        "nop\n\t"
    ".set reorder\n\t");
