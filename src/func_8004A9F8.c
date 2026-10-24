/* STAGED, not yet listed by any yaml row - the build never compiles this
 * file until config/splat.g3_eu.yaml flips the twin row asm -> c (the
 * yaml-row-driven c_entries selection is the whole gate; an unlisted src
 * file is build-inert). Staged by the cron-20261024-1231 oracle-down
 * window so the flip is a one-line edit + verify at the next disc return.
 *
 * LIBETC INTR_DMA member memclr (static copy) at g3_eu vram 0x8004A9F8
 * (yaml rom 0x2B1F8, extent 0x2c). sdk_members.txt pins the address:
 * startIntrDMA 0x8004A77C / trapIntrDMA 0x8004A7CC / setIntrDMA
 * 0x8004A950 / memclr 0x8004A9F8 - the member spine is identical in
 * sces_00269 at 0x8002EDC0..0x8002F03C. The retail static carries no
 * symbol of its own, and this target's canonical `memclr` slot is taken
 * by the curated INTR-member unit src/func_80050C30.c - a second
 * definition of the name would be a multiple definition at link time
 * (the link-oracle catch that parked the wave). The copy therefore
 * claims its address label as its symbol: the row name equals the
 * extract's linear default, so the single caller (startIntrDMA, jal
 * from func_8004A77C) needs zero renames.
 *
 * Census provenance: the copy-census twin (dw=0, 11/11 words, votes 7,
 * rel +0x27C in the pre-rescan data_80050C6C row); the post-framing
 * re-scan carved it as the standalone sdk asm row this file stages.
 * Body proven byte-identical to the curated INTR-member unit under a
 * symbol rename: cc.sh (cc1 2.6.3 under qemu -> maspsx -> mipsel-as
 * 2.31.1) compiles both to instruction streams that differ only in the
 * name-bearing directives (.file/.globl/.ent/label/.end) - the .o text
 * is word-for-word the memclr signature (addiu $sp,-8 / beqz $a1 with
 * the len-1 init in the delay slot / -1 sentinel in $v1 / sw + countdown
 * loop over whole words / addiu $sp,8 / jr $ra + nop).
 *
 * LANDING RECIPE (oracle window): (1) yaml
 * `- [0x2B1F8, asm, func_8004A9F8]   # 0x2c sdk` -> `c`; (2) delete
 * asm/g3_eu/nonmatchings/func_8004A9F8.s (clean_stale_asm also sweeps
 * it post-extract); (3) zero renames; (4) make verify TARGET=g3_eu +
 * ratchet audit. The sces_00269 twin src/func_8002F03C.c stages the
 * same shape; the INTR_VB copies (g3_eu 0x8004AB24 asm row
 * func_80051144, sces 0x8002F168) are the next class - they wait for
 * the census rerun's own dw=0 votes, not this staging.
 */

void func_8004A9F8(void *ptr, long len)
{
    long *p;
    long i;

    p = (long *)ptr;
    for (i = len - 1; i != -1; i--) {
        *p = 0;
        p++;
    }
}
