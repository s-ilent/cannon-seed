/* memmove - LIBC member, x4 byte-identical own-row wave (0x90 row = 0x88
 * function + 2 zero tail words).
 * Identities: slps func_80030D90 (@0x8002E9F0, curated pin), mainmenu_jp
 * func_8006661C (@0x8005D40C, curated pin), g3_jp func_8004EF2C
 * (@0x80048DCC, curated pin), g3org_jp func_8004BDD8 (@0x80046268,
 * curated pin). Every member sits flanked by the same 0x10 sdk rows - the
 * SDK's own LIBC cluster.
 *
 * Decode (20th-return NEXT 3, offline window cron-202610291255): psyq's
 * memmove is a HAND-WRITTEN asm member, not a gcc compilation - the
 * evidence chain: (1) the sltu result lives in $at, a register gcc never
 * allocates for a plain comparison; (2) the three incoming args are stored
 * to their o32 home slots (8/0xC/0x10($sp) under the -0x8 frame) and never
 * reloaded - dead stores no -O level emits; (3) the frame itself is never
 * read or written; (4) the return keeps the frame release in the branch
 * delay slot (`jr $ra; addiu $sp,$sp,8`), the ASPSX hand-asm convention -
 * gcc's own frame-only epilogue puts the release before the jump (the
 * func_8003BF4C shape) and cc_post's rule-1 variants only fire on
 * $ra-reload prologues, none of which exist here; (5) the backward loop
 * recomputes both addresses from the live index every iteration (no
 * strength reduction - gcc 2.6.3 pointer-walks d[n]/s[n] forms, the
 * screen's honest first iteration proved it). The body: dst/src direction
 * test (sltu $at, dst, src; bnez = forward when dst < src), the two
 * `while (n-- > 0)` idioms (pre-test blez on the old value, decrement in
 * the pre-head delay slot, loop guard on the just-used index with the
 * sb re-entering the next iteration's delay slot), forward loop copying
 * through the bumped pointers (`sb $t9, -0x1($a3)` after the bumps), the
 * backward loop indexing from the live end (`d[n] = s[n]` with the shared
 * index $t1), both paths converging on `addu $v0, $a3, $zero` (return
 * dst) then the delay-filled return.
 *
 * LANDING SHAPE: verbatim retail bytes as a hand-asm unit (the
 * func_80031ABC precedent: bare file-scope asm, no C body, no compiler
 * framing). The unit declares plain `.text` - tools/stage_c.py renames it
 * to the target's `.r_<rom>` section, so one template serves all four
 * carriers - and carries `.globl` + label under the row's own walk name
 * (the row-name==unit-name law; the curated memmove pins carry the
 * identity, zero symbols edits).
 */
__asm__(
    ".text\n\t"
    ".set\tnoreorder\n\t"
    ".set noreorder\n\t"
    ".globl func_80030D90\n\t"
    "func_80030D90:\n\t"
        "addiu $sp,$sp,-0x8\n\t"
        "addu $a3,$a0,$zero\n\t"
        "addu $t0,$a1,$zero\n\t"
        "sltu $at,$a3,$t0\n\t"
        "sw $a0,0x8($sp)\n\t"
        "sw $a1,0xC($sp)\n\t"
        "sw $a2,0x10($sp)\n\t"
        "bnez $at,.Lfwd\n\t"
        "addu $t1,$a2,$zero\n\t"
        "addu $t2,$t1,$zero\n\t"
        "blez $t2,.Lend\n\t"
        "addiu $t1,$t1,-0x1\n\t"
    ".Lbwd:\n\t"
        "addu $t6,$t0,$t1\n\t"
        "lbu $t7,0x0($t6)\n\t"
        "addu $t8,$a3,$t1\n\t"
        "addu $t2,$t1,$zero\n\t"
        "addiu $t1,$t1,-0x1\n\t"
        "bgtz $t2,.Lbwd\n\t"
        "sb $t7,0x0($t8)\n\t"
        "b .Lret\n\t"
        "addu $v0,$a3,$zero\n\t"
    ".Lfwd:\n\t"
        "addu $t2,$t1,$zero\n\t"
        "blez $t2,.Lend\n\t"
        "addiu $t1,$t1,-0x1\n\t"
    ".Lloop:\n\t"
        "lbu $t9,0x0($t0)\n\t"
        "addu $t2,$t1,$zero\n\t"
        "addiu $t1,$t1,-0x1\n\t"
        "addiu $t0,$t0,0x1\n\t"
        "addiu $a3,$a3,0x1\n\t"
        "bgtz $t2,.Lloop\n\t"
        "sb $t9,-0x1($a3)\n\t"
    ".Lend:\n\t"
        "addu $v0,$a3,$zero\n\t"
    ".Lret:\n\t"
        "jr $ra\n\t"
        "addiu $sp,$sp,0x8\n\t"
    ".set\treorder\n\t");
