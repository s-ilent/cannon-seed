/* Matched 2026-10-26 (window cron-202610252019) - the PCopen member of
 * the psyq LIBSN host-file family, x4 across g3_jp / g3_eu / g3org_jp /
 * g3org_eu. The identity is banked in config/sdk_anchors.txt ("PCopen ?
 * LIBSN unique"), and this window's pair-report sweep proves the region
 * pairs byte-identical at 100.00% while both sides are still asm:
 *
 *   g3_jp     file 0x2969C, VA 0x80048E9C
 *   g3_eu     file 0x290B4, VA 0x800488B4
 *   g3org_jp  file 0x26B38, VA 0x80046338
 *   g3org_eu  file 0x26508, VA 0x80045D08
 *
 * (each site was its own sdk-annotated whole asm row under a woven-era
 * scanner label before this flip; scripts/land_libsn_hosts.sh and
 * scripts/prove_libsn_hosts.py carry the per-target name mapping.)
 *
 * The body is the psyq host-protocol call PCclose already banks: the
 * arguments stage one register right (the host reads them from a1 up;
 * a0 holds the protocol slot the 0x103 break code encodes), the break
 * traps to the host, then the standard error tail reads the verdict -
 * v0 = 0 means the host call succeeded and the real result rides v1,
 * any nonzero v0 is the error and the caller gets -1. The tail is the
 * banked five-word shape: beqz with the success move in its delay slot,
 * the -1 fallthrough, the shared jr.
 *
 * The block carries the retail words 0..5 1:1 (addu/break/beq/addu/
 * addiu assemble natively; the break code 0x103 assembles (0x103<<6)|
 * 0x0D exactly as PCclose's 0x104 does). GCC's frameless epilogue then
 * emits jr $ra + nop - ret is already in $2 via the register var, so
 * no return move fires and the whole image word-counts 0x20.
 *
 * The branchy tail sits inside an explicit .set noreorder window (the
 * TAB-form directive is the spelling maspsx honors inside #APP; the
 * space form parses as an unknown directive and maspsx's reorder-mode
 * branch rule then inserts its own nop, shifting the fill one slot
 * late - the tool lesson this landing banks).
 *
 * psyq prototype: int PCopen(const char *name, int flags, int mode);
 */
int PCopen(char *path, int flags, int mode)
{
    register int ret asm("$2");
    __asm__ volatile(
        "addu $a2, $a1, $zero\n"
        "\taddu $a1, $a0, $zero\n"
        "\tbreak 0x103\n"
        "\t.set\tnoreorder\n"
        "\tbeq $2, $0, 1f\n"
        "\taddu $2, $3, $0\n"
        "\taddiu $2, $0, -1\n"
        "1:\n"
        "\t.set\treorder\n"
        : "=r"(ret));
    return ret;
}
