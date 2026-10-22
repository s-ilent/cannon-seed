/* MATCHING: verbatim retail bytes as a hand-asm unit (bare
 * file-scope asm; no C body, no compiler framing). The global
 * label sits where the bytes are so cross-object callers resolve. */
__asm__(
    ".section .r_0000687C, \"awx\", @progbits\n\t"
    ".set noreorder\n\t"
    ".globl func_8002607C\n\t"
    "func_8002607C:\n\t"
        ".set noreorder\n\t"
        "lui $a2, 0x8007\n\t"
        "addiu $a2, $a2, 0x441c\n\t"
        "lw $v0, 0($a2)\n\t"
        "lw $v1, 4($a2)\n\t"
        "lw $a0, 8($a2)\n\t"
    ".set reorder\n\t");
