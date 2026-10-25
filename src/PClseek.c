/* Matched 2026-10-26 (window cron-202610252019) - the PClseek member of
 * the psyq LIBSN host-file family, x2 across g3_jp / g3_eu (the g3org
 * pair's yaml carries no PClseek row - the member is x2, not x4). The
 * identity is banked in config/sdk_anchors.txt ("PClseek ? LIBSN
 * unique"), and this window's pair-report sweep proves the g3 region
 * pair byte-identical at 100.00% while both sides are still asm:
 *
 *   g3_jp     file 0x296BC, VA 0x80048EBC
 *   g3_eu     file 0x290D4, VA 0x800488D4
 *
 * (each site was its own sdk-annotated whole asm row under a woven-era
 * scanner label before this flip; scripts/land_libsn_hosts.sh and
 * scripts/prove_libsn_hosts.py carry the per-target name mapping.)
 *
 * The body is PCopen's host-protocol shape one argument wider: the
 * three arguments stage one register right (a2->a3, a1->a2, a0->a1;
 * the host reads them from a1 up), the 0x107 break traps to the host,
 * then the standard error tail - v0 = 0 means success and the real
 * result rides v1, nonzero v0 means the caller gets -1. The tail is
 * the banked five-word shape: beqz with the success move in its delay
 * slot, the -1 fallthrough, the shared jr.
 *
 * The block carries the retail words 0..6 1:1 (the break code 0x107
 * assembles (0x107<<6)|0x0D exactly as PCclose's 0x104 does). GCC's
 * frameless epilogue then emits jr $ra + nop - ret is already in $2
 * via the register var, so no return move fires and the whole image
 * word-counts 0x24.
 *
 * The branchy tail sits inside an explicit .set noreorder window (the
 * TAB-form directive is the spelling maspsx honors inside #APP; the
 * space form parses as an unknown directive and maspsx's reorder-mode
 * branch rule then inserts its own nop, shifting the fill one slot
 * late - the tool lesson this landing banks).
 *
 * psyq prototype: long PClseek(int fd, long offset, int mode);
 */
int PClseek(int fd, int offset, int whence)
{
    register int ret asm("$2");
    __asm__ volatile(
        "addu $a3, $a2, $zero\n"
        "\taddu $a2, $a1, $zero\n"
        "\taddu $a1, $a0, $zero\n"
        "\tbreak 0x107\n"
        "\t.set\tnoreorder\n"
        "\tbeq $2, $0, 1f\n"
        "\taddu $2, $3, $0\n"
        "\taddiu $2, $0, -1\n"
        "1:\n"
        "\t.set\treorder\n"
        : "=r"(ret));
    return ret;
}
