/* MATCHING: verbatim retail bytes as a hand-asm unit (bare
 * file-scope asm; no C body, no compiler framing). The global
 * label sits where the bytes are so cross-object callers resolve. */
__asm__(
    ".section .r_000068E4, \"awx\", @progbits\n\t"
    ".set noreorder\n\t"
    ".globl func_800260E4\n\t"
    "func_800260E4:\n\t"
        ".set noreorder\n\t"
        "addiu $a2, $a2, 0x455c\n\t"
        "lw $v0, 0($a2)\n\t"
        "lw $v1, 4($a2)\n\t"
        "lw $a0, 8($a2)\n\t"
        "lw $a1, 0xc($a2)\n\t"
    ".set reorder\n\t");
