/* Matched 2026-10-17 through the round-trip oracle (g3org_jp first;
 * cross-target byte-identical in mainmenu_jp, g3_eu, g3org_jp, g3org_eu,
 * see the matching lane's GTE families queue item).
 *
 * LIBGTE NormalClip: backface clip via the GTE NCLIP command - the three
 * vector halves go into the GTE FIFO (a0 -> VXY0 $12, a2 -> VZ1 $14,
 * a1 -> VXY1 $13; retail's scheduler orders a0, a2, a1), two latency
 * nops, NCLIP (0x4b400006 - GNU as has no GTE mnemonics, banked as its
 * exact retail .word), then MAC0 ($24) is read back as the return value.
 *
 * The mtc2 address-free forms are plain asm; the mfc2 output lands on a
 * $2 register-var (the RotTransPers4 return law) so gcc emits jr $ra
 * straight after the block with no move. Args stay `long` so gcc emits
 * no caller-side extension insns in the body.
 */
long NormalClip(long a0, long a1, long a2)
{
    register long r asm("$2");
    __asm__ volatile(
        "mtc2 %1, $12\n"
        "\tmtc2 %3, $14\n"
        "\tmtc2 %2, $13\n"
        "\tnop\n"
        "\tnop\n"
        "\t.word 0x4b400006\n"
        "\tmfc2 %0, $24"
        : "=r"(r)
        : "r"(a0), "r"(a1), "r"(a2));
    return r;
}
