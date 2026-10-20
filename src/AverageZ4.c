/* Matched 2026-10-20 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% byte twins across g3_jp/g3_eu, the matching
 * lane's libgte math cluster queue item).
 *
 * LIBGTE AverageZ4: the four depth values (a0/a1/a2/a3) load into
 * SZ1/SZ2/SZ3/SZ4 ($16/$17/$18/$19), the avsz4 command (0x4B68002E -
 * GNU as has no GTE mnemonics, banked as its exact retail .word)
 * averages them into OTZ ($7), and the result returns via mfc2 into
 * $2.
 *
 * psyq prototype: long AverageZ4(long sz1, long sz2, long sz3,
 * long sz4); the mfc2 targets the return register directly, so the
 * $2 register-var output needs no post-block move and the epilogue is
 * the stock frameless jr $ra with a nop delay slot.
 */
long AverageZ4(long a0, long a1, long a2, long a3)
{
    register long vv asm("$2");
    __asm__ volatile(
        "mtc2 $4, $16\n"
        "\tmtc2 $5, $17\n"
        "\tmtc2 $6, $18\n"
        "\tmtc2 $7, $19\n"
        "\tnop\n"
        "\t.word 0x4B68002E\n" /* avsz4 */
        "\tmfc2 $2, $7\n"
        : "=r"(vv));
    return vv;
}
