/* STAGED, not yet listed by any yaml row - the build never compiles this
 * file until config/splat.sces_00269.yaml flips the twin row asm -> c
 * (the yaml-row-driven c_entries selection is the whole gate; an
 * unlisted src file is build-inert). Staged by the cron-20261024-1347
 * oracle-down window alongside src/func_8002F03C.c (cron-20261024-1231),
 * completing sces_00269's three-copy memclr family map.
 *
 * LIBETC INTR member memclr (static copy) at sces_00269 vram 0x8002ED84
 * (yaml rom 0xF584, extent 0x2c). sdk_members.txt pins the member
 * window (trapIntr 0x8002ED44 et al) and marks this address as the
 * member's un-adopted memclr copy; the member spine runs alongside the
 * INTR_DMA member's (startIntrDMA 0x8002EDC0 .. memclr 0x8002F03C,
 * itself staged as src/func_8002F03C.c). The retail static carries no
 * symbol of its own, and this target's canonical `memclr` slot is
 * taken by the curated INTR_VB-member unit src/func_80031638.c - the
 * copy therefore claims its address label as its symbol.
 *
 * REFERENCE NOTE: the committed extracted tree shows ZERO jal/j
 * references into 0x8002ED84 - unlike its two siblings, neither this
 * member's own functions nor anything else in the extracted image
 * calls this copy (the INTR member's code reaches its clears another
 * way, or the copy is dead in this link). Zero references also means
 * zero renames; the flip changes nothing but the row's kind.
 *
 * Byte provenance (offline, no oracle): the committed extracted body's
 * eleven instruction words are word-for-word the family sequence
 * F8FFBD27 0600A010 FFFFA224 FFFF0324 000080AC FFFF4224 FDFF4314
 * 04008424 0800BD27 0800E003 00000000 - identical to the INTR_DMA
 * twin's committed asm and to both g3_eu copies, all four extracted by
 * the scan-verified pipeline. The census twin votes for this copy
 * (dw=0 class) re-derive at the next census rerun; the
 * name-independence compile proof (cc.sh, cron-20261024-1231) covers
 * the flip's byte-exactness.
 *
 * LANDING RECIPE (oracle window): (1) yaml
 * `- [0xF584, asm, func_80031124]   # 0x2c sdk` -> `c`; (2) delete
 * asm/sces_00269/nonmatchings/func_80031124.s (clean_stale_asm also
 * sweeps it post-extract); (3) zero renames; (4) make verify
 * TARGET=sces_00269 + ratchet audit. The g3_eu INTR_VB copy stages as
 * src/func_80051144.c.
 */

void func_80031124(void *ptr, long len)
{
    long *p;
    long i;

    p = (long *)ptr;
    for (i = len - 1; i != -1; i--) {
        *p = 0;
        p++;
    }
}
