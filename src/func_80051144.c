/* STAGED, not yet listed by any yaml row - the build never compiles this
 * file until config/splat.g3_eu.yaml flips the twin row asm -> c (the
 * yaml-row-driven c_entries selection is the whole gate; an unlisted src
 * file is build-inert). Staged by the cron-20261024-1347 oracle-down
 * window alongside src/func_8004A9F8.c (cron-20261024-1231), completing
 * g3_eu's three-copy memclr family map.
 *
 * LIBETC INTR_VB member memclr (static copy) at g3_eu vram 0x8004AB24
 * (yaml rom 0x2B324, extent 0x2c). sdk_members.txt pins the address:
 * startIntrVSync 0x8004AA24 / trapIntrVSync 0x8004AA7C / setIntrVSync
 * 0x8004AAF8 / memclr 0x8004AB24 - the member spine sits immediately
 * after the INTR_DMA member's (startIntrDMA 0x8004A77C .. memclr
 * 0x8004A9F8, itself staged as src/func_8004A9F8.c). The retail static
 * carries no symbol of its own, and this target's canonical `memclr`
 * slot is taken by the curated INTR-member unit src/func_80050C30.c -
 * the copy therefore claims its address label as its symbol. The
 * single caller is the member's own startIntrVSync (jal from
 * func_80051044), already spelled with the address label: zero
 * renames.
 *
 * Byte provenance (offline, no oracle): the committed extracted body's
 * eleven instruction words are word-for-word the family sequence
 * F8FFBD27 0600A010 FFFFA224 FFFF0324 000080AC FFFF4224 FDFF4314
 * 04008424 0800BD27 0800E003 00000000 - identical to the INTR_DMA
 * twin's committed asm and to both sces_00269 copies, all four
 * extracted by the scan-verified pipeline. The census twin votes for
 * this copy (dw=0 class) re-derive at the next census rerun; the
 * name-independence compile proof (cc.sh, cron-20261024-1231) covers
 * the flip's byte-exactness.
 *
 * LANDING RECIPE (oracle window): (1) yaml
 * `- [0x2B324, asm, func_80051144]   # 0x2c sdk` -> `c`; (2) delete
 * asm/g3_eu/nonmatchings/func_80051144.s (clean_stale_asm also sweeps
 * it post-extract); (3) zero renames; (4) make verify TARGET=g3_eu +
 * ratchet audit. Sces_00269's remaining copy stages as
 * src/func_80031124.c.
 */

void func_80051144(void *ptr, long len)
{
    long *p;
    long i;

    p = (long *)ptr;
    for (i = len - 1; i != -1; i--) {
        *p = 0;
        p++;
    }
}
