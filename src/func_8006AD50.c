/* cc-post: keep-epilogue
 *
 * Third/fourth real-decompiled-C game functions of the twenty-ninth window
 * (cron-202610300053). One yaml row, 0x40 bytes, TWO functions: the
 * spimdisasm file holds both glabels and the row is listed once.
 *
 * Pair of one-call wrappers feeding func_8006AC04 (the reset/init driver
 * this target's scan tagged sdk, itself called by ResetCallback-adjacent
 * code) with the constants 0 and 1. Caller edge: both jal from
 * func_80028140 (0x2174 untagged game row) - game-authored glue. Shape:
 * GCC 2.6.3 non-sibcall wrapper frame, the constant argument materialized
 * in the jal's delay slot (addu $a0,$zero,$zero for 0, ori $a0,$zero,1
 * for 1), epilogue in GCC's own frame-release-before-jump order
 * (keep-epilogue, same as func_8004E29C this window).
 */
extern void func_8006AC04(long);

void func_8006AD50(void)
{
    func_8006AC04(0);
}

void func_8006AD70(void)
{
    func_8006AC04(1);
}
