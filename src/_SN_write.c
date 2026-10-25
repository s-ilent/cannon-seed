/* Matched 2026-10-26 (window cron-202610252019) - the _SN_write member
 * of the psyq LIBSN host-file family, x4 across g3_jp / g3_eu /
 * g3org_jp / g3org_eu. The identity is banked in config/sdk_anchors.txt
 * ("_SN_write ? LIBSN unique"), and this window's pair-report sweep
 * proves the region pairs byte-identical at 100.00% while both sides
 * are still asm:
 *
 *   g3_jp     file 0x297B0, VA 0x80048FB0
 *   g3_eu     file 0x291C8, VA 0x800489C8
 *   g3org_jp  file 0x26C4C, VA 0x8004644C
 *   g3org_eu  file 0x2661C, VA 0x80045E1C
 *
 * (each site was its own sdk-annotated whole asm row under a woven-era
 * scanner label before this flip; scripts/land_libsn_hosts.sh and
 * scripts/prove_libsn_hosts.py carry the per-target name mapping.)
 *
 * The body is the host-protocol call with NO argument staging (the
 * caller's a0..a2 pass through untouched - the host reads them where
 * they are): the 0x106 break traps to the host, then the standard
 * error tail - v0 = 0 means success and the real byte count rides v1,
 * nonzero v0 means the caller gets -1. The tail is the banked
 * five-word shape: beqz with the success move in its delay slot, the
 * -1 fallthrough, the shared jr.
 *
 * The block carries the retail words 0..3 1:1 (the break code 0x106
 * assembles (0x106<<6)|0x0D exactly as PCclose's 0x104 does). GCC's
 * frameless epilogue then emits jr $ra + nop - ret is already in $2
 * via the register var, so no return move fires and the whole image
 * word-counts 0x18.
 *
 * The branchy tail sits inside an explicit .set noreorder window (the
 * TAB-form directive is the spelling maspsx honors inside #APP; the
 * space form parses as an unknown directive and maspsx's reorder-mode
 * branch rule then inserts its own nop, shifting the fill one slot
 * late - the tool lesson this landing banks).
 *
 * psyq prototype: int _SN_write(int fd, const void *buf, int len) -
 * the SN-stage write the host protocol serves; the arguments are the
 * host's own and this callee never inspects them.
 */
int _SN_write(int fd, const void *buf, int len)
{
    register int ret asm("$2");
    __asm__ volatile(
        "break 0x106\n"
        "\t.set\tnoreorder\n"
        "\tbeq $2, $0, 1f\n"
        "\taddu $2, $3, $0\n"
        "\taddiu $2, $0, -1\n"
        "1:\n"
        "\t.set\treorder\n"
        : "=r"(ret));
    return ret;
}
