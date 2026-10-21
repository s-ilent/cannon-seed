/*
 * PCclose - psyq LIBPC member, one C source across g3_jp / g3_eu /
 * g3org_jp / g3org_eu. The near-twin census pools the four copies as a
 * byte-identical 0x10 wave (maxdiff 0.000, zero differing words):
 *
 *   g3_jp    file 0x296E0, VA 0x80048EE0
 *   g3_eu    file 0x290F8, VA 0x800488F8
 *   g3org_jp file 0x26B7C, VA 0x8004637C
 *   g3org_eu file 0x2654C, VA 0x80045D4C
 *
 * Retail body (16 bytes, no relocation slots - the offline probe matches
 * 4/4 with full masks):
 *
 *   addu $a1, $a0, $zero   ; stage the fd for the host call
 *   break 0x104            ; word 0x0000410D = (0x104 << 6) | 0x0D
 *   jr   $ra
 *   nop
 *
 * The break code 0x104 rules out a plain `break` (which assembles
 * 0x0000000D); the a0-to-a1 move is the psyq host-protocol argument
 * staging. The name carries the SDK's own evidence: every copy is a
 * pinned member row (config/symbols.<t>.txt, LIBPC placements), and the
 * psyq prototype is void PCclose(short fd) era C - the retail body sets
 * no $v0, so the honest decode is void.
 */

void PCclose(int fd)
{
    __asm__ volatile(
        "addu $a1, $a0, $zero\n"
        "\tbreak 0x104\n"
    );
}
