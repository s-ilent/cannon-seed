/* STAGED, not yet listed by any yaml row - the build never compiles this
 * file until config/splat.g3org_eu.yaml flips the twin row asm -> c
 * (the yaml-row-driven c_entries selection is the whole gate; an
 * unlisted src file is build-inert). Staged by the cron-20261024-1347
 * oracle-down window under the address-named-c-row convention the
 * memclr source-mapping question closed with (cron-20261024-1231).
 *
 * LIBETC INTR_VB member memclr (static copy) at g3org_eu vram 0x80047F78
 * (yaml rom 0x28778, extent 0x2c); sdk_members.txt pins the address as
 * the member's un-adopted memclr copy. This target's canonical
 * `memclr` slot is taken by the curated unit src/func_8004DD4C.c - the copy
 * therefore claims its address label as its symbol.
 * The single caller is the member's own VSync-path caller (jal from func_8004DD78), already spelled with the address label: zero
 * renames.
 *
 * Byte provenance (offline, no oracle): the committed extracted
 * body's eleven instruction words are word-for-word the family
 * sequence F8FFBD27 0600A010 FFFFA224 FFFF0324 000080AC FFFF4224 FDFF4314 04008424 0800BD27 0800E003 00000000 - identical across all fourteen carved copies in the
 * six game modules, all extracted by the scan-verified pipeline. The
 * name-independence compile proof (cc.sh, cron-20261024-1231) covers
 * the flip's byte-exactness; the census twin votes re-derive at the
 * next census rerun.
 *
 * LANDING RECIPE (oracle window): (1) yaml
 * `- [0x28778, asm, func_8004DE78]   # 0x2c sdk` -> `c`; (2) delete
 * asm/g3org_eu/nonmatchings/func_8004DE78.s (clean_stale_asm also sweeps it
 * post-extract); (3) zero renames; (4) make verify TARGET=g3org_eu +
 * ratchet audit.
 */

void func_8004DE78(void *ptr, long len)
{
    long *p;
    long i;

    p = (long *)ptr;
    for (i = len - 1; i != -1; i--) {
        *p = 0;
        p++;
    }
}
