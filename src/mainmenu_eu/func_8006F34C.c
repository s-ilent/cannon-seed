/* The 0x1CC recursive triangle-subdivision row - x20 byte-identical own-row
 * wave (sha1 28494af42860, 456 bytes; mainmenu_eu/g3_jp/g3_eu/g3org_jp/
 * g3org_eu x4 each; identities live in the yaml, the symbols file and the
 * landing commit - the headers name no siblings).
 *
 * Decode (26th window, cron-202610292127; both 25th-window open items closed):
 * a frustum-honoring recursive triangle-subdivision driver feeding a
 * display-list builder. The row is a SIX-chunk multi-function listing - the
 * chunks are ONE handwritten routine, chained by intra-row beqz falls:
 *   chunk 1 (0x48): depth cull - the three vertex records' +0x14 depth words
 *     (a3->0x48/4C/50 are the vertex POINTERS) vs cfc2 $26 >> 1 unsigned;
 *     all three below the line -> early-return a0 (cull, cursor unchanged).
 *   chunk 2 (0x50) + chunk 3 (0x2C): screen-X band - hi(R24) +/- (a1->4 >> 1)
 *     via sra 16 + unsigned srl 1; all three +0x10 halfwords above the upper
 *     band OR all below the lower band -> early-return a0; the addu/subu
 *     pair reuses the staged values across the two chunk heads.
 *   chunk 4 (0x40) + chunk 5 (0x2C): the same band law for screen Y (+0x12
 *     halfwords) via R25 and a1->8.
 *   chunk 6 (0x9c): the midpoint splitter - three edge midpoints of the
 *     vertex xyz triples ((t0+t1)>>1 -> a3+0x00, (t1+t2)>>1 -> a3+0x18,
 *     (t2+t0)>>1 -> a3+0x30, the `add` pair-sums tagged handwritten), then
 *     the first three GTE data-reg loads (VXY0/VZ0/VXY1 = mid01.xyz,
 *     mid12.xy) - the row ENDS MID-FLOW there by the wave's own extent bar.
 *
 * THE ROW IS THE FRONT HALF OF A RECURSIVE WHOLE: the successor "data" row
 * (data_8005A308, mis-typed) is the routine's recursive tail - lwc2 $3/$4/$5
 * complete V1/V2, cop2 RTPT transforms all three midpoints, and the depth
 * limit (a1->0) picks the exits: EMIT (leaf) stores SXY0/1/2 into the mid
 * records' +0x10 and emits the four quad-split sub-triangle packets through
 * the 0x4c packet shim (a0 += 0x14 per packet, the returned
 * cursor IS the routine's return value), RECURSE advances a3 by the 0x58
 * child-record stride, saves $ra at child->0x54, writes the sub-triangle
 * vertex pointers into child->0x48/4C/50 with the midpoints' SZ1/2/3 ->
 * +0x14 and SXY -> +0x10 write-backs, and jal's the row's OWN head four
 * times (self-recursion), restoring $ra after. Every vertex record - real
 * mesh vertex or 0x18-stride midpoint - carries screen X/Y at +0x10/+0x12
 * and depth at +0x14; the GTE control regs $24/$25/$26 carry APPLICATION
 * bounds (the reboot/init ctc2 seed path in the g3org_jp tree writes
 * R26=1000 (the depth line, consumed as >>1), R24/R25=0 (the screen band
 * centers), R27-R30 sibling scratch -
 * the only ctc2 writers to $24-$30 in the tree).
 *
 * LANDING SHAPE: verbatim retail bytes as a hand-asm unit (the memmove/
 * memclr bare file-scope asm precedent; the four tagged chunks + the
 * cfc2 reads are the hand-asm proof - gcc 2.6.3 emits no cfc2). The row
 * carries NO absolute relocations (all branches intra-row relative, no
 * lui/%hi-%lo, no jal inside the 456 bytes), so ONE template serves all
 * twenty members - the five interior chunk labels are row-local (zero
 * exterior references verified) and become .L labels here; the unit
 * declares plain `.text` (tools/stage_c.py renames it per target) with
 * `.globl` + the row's own walk name (the row-name==unit-name law; one
 * placeholder mention per file, headers name no siblings). No tail words -
 * the row ends exactly at the lwc2 $2 boundary (0x1cc = 115 insns).
 */
__asm__(
    ".text\n\t"
    ".set\tnoreorder\n\t"
    ".set noreorder\n\t"
    ".globl func_8006F34C\n\t"
    "func_8006F34C:\n\t"
        "lw $t0,0x48($a3)\n\t"
        "lw $t1,0x4C($a3)\n\t"
        "lw $t2,0x50($a3)\n\t"
        "cfc2 $t9,$26\n\t"
        "lw $t4,0x14($t0)\n\t"
        "lw $t5,0x14($t1)\n\t"
        "lw $t6,0x14($t2)\n\t"
        "sra $t8,$t9,1\n\t"
        "sltu $at,$t4,$t8\n\t"
        "beqz $at,.Lc2\n\t"
        "sltu $at,$t5,$t8\n\t"
        "beqz $at,.Lc2\n\t"
        "sltu $at,$t6,$t8\n\t"
        "beqz $at,.Lc2\n\t"
        "nop\n\t"
        "addu $v0,$a0,$zero\n\t"
        "jr $ra\n\t"
        "nop\n\t"
    ".Lc2:\n\t"
        "cfc2 $t9,$24\n\t"
        "lw $v0,0x4($a1)\n\t"
        "lw $v1,0x8($a1)\n\t"
        "sra $t9,$t9,16\n\t"
        "srl $v0,$v0,1\n\t"
        "srl $v1,$v1,1\n\t"
        "addu $t8,$t9,$v0\n\t"
        "lh $t4,0x10($t0)\n\t"
        "lh $t5,0x10($t1)\n\t"
        "lh $t6,0x10($t2)\n\t"
        "slt $at,$t8,$t4\n\t"
        "beqz $at,.Lc3\n\t"
        "slt $at,$t8,$t5\n\t"
        "beqz $at,.Lc3\n\t"
        "slt $at,$t8,$t6\n\t"
        "beqz $at,.Lc3\n\t"
        "nop\n\t"
        "addu $v0,$a0,$zero\n\t"
        "jr $ra\n\t"
        "nop\n\t"
    ".Lc3:\n\t"
        "subu $t8,$t9,$v0\n\t"
        "slt $at,$t4,$t8\n\t"
        "beqz $at,.Lc4\n\t"
        "slt $at,$t5,$t8\n\t"
        "beqz $at,.Lc4\n\t"
        "slt $at,$t6,$t8\n\t"
        "beqz $at,.Lc4\n\t"
        "nop\n\t"
        "addu $v0,$a0,$zero\n\t"
        "jr $ra\n\t"
        "nop\n\t"
    ".Lc4:\n\t"
        "cfc2 $t9,$25\n\t"
        "lh $t4,0x12($t0)\n\t"
        "lh $t5,0x12($t1)\n\t"
        "lh $t6,0x12($t2)\n\t"
        "sra $t9,$t9,16\n\t"
        "addu $t8,$t9,$v1\n\t"
        "slt $at,$t8,$t4\n\t"
        "beqz $at,.Lc5\n\t"
        "slt $at,$t8,$t5\n\t"
        "beqz $at,.Lc5\n\t"
        "slt $at,$t8,$t6\n\t"
        "beqz $at,.Lc5\n\t"
        "nop\n\t"
        "addu $v0,$a0,$zero\n\t"
        "jr $ra\n\t"
        "nop\n\t"
    ".Lc5:\n\t"
        "subu $t8,$t9,$v1\n\t"
        "slt $at,$t4,$t8\n\t"
        "beqz $at,.Lc6\n\t"
        "slt $at,$t5,$t8\n\t"
        "beqz $at,.Lc6\n\t"
        "slt $at,$t6,$t8\n\t"
        "beqz $at,.Lc6\n\t"
        "nop\n\t"
        "addu $v0,$a0,$zero\n\t"
        "jr $ra\n\t"
        "nop\n\t"
    ".Lc6:\n\t"
        "lh $t4,0x0($t0)\n\t"
        "lh $t5,0x0($t1)\n\t"
        "lh $t6,0x0($t2)\n\t"
        "add $t7,$t4,$t5\n\t"
        "add $t8,$t5,$t6\n\t"
        "add $t9,$t6,$t4\n\t"
        "sra $t7,$t7,1\n\t"
        "sra $t8,$t8,1\n\t"
        "sra $t9,$t9,1\n\t"
        "sh $t7,0x0($a3)\n\t"
        "sh $t8,0x18($a3)\n\t"
        "sh $t9,0x30($a3)\n\t"
        "lh $t4,0x2($t0)\n\t"
        "lh $t5,0x2($t1)\n\t"
        "lh $t6,0x2($t2)\n\t"
        "add $t7,$t4,$t5\n\t"
        "add $t8,$t5,$t6\n\t"
        "add $t9,$t6,$t4\n\t"
        "sra $t7,$t7,1\n\t"
        "sra $t8,$t8,1\n\t"
        "sra $t9,$t9,1\n\t"
        "sh $t7,0x2($a3)\n\t"
        "sh $t8,0x1A($a3)\n\t"
        "sh $t9,0x32($a3)\n\t"
        "lh $t4,0x4($t0)\n\t"
        "lh $t5,0x4($t1)\n\t"
        "lh $t6,0x4($t2)\n\t"
        "add $t7,$t4,$t5\n\t"
        "add $t8,$t5,$t6\n\t"
        "add $t9,$t6,$t4\n\t"
        "sra $t7,$t7,1\n\t"
        "sra $t8,$t8,1\n\t"
        "sra $t9,$t9,1\n\t"
        "sh $t7,0x4($a3)\n\t"
        "sh $t8,0x1C($a3)\n\t"
        "sh $t9,0x34($a3)\n\t"
        "lwc2 $0,0x0($a3)\n\t"
        "lwc2 $1,0x4($a3)\n\t"
        "lwc2 $2,0x18($a3)\n\t"
    ".set\treorder\n\t");
