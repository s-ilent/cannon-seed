/* cc-post: sdk-aspsx
 * cc-post: cc1-O1
 *
 * LIBSND VS_VH member: SsVabOpenHeadWithMode (g3org_jp 0x48864, extent
 * 0x448). DRAFT 4 (cron-202611032028): draft3 with vabid/mode and the two
 * signature params widened short->long - full-word pins. DIFF 219/228
 * SIZE 912: the best WithMode judge number so far; see draft3's RESULT
 * block for the ladder and the consequence.
 *
 * Experiment: the param imports re-authored as pinned-local inits -
 * the 7736C interleave bypass (NEGATIVE on every form; the full ladder
 * and its consequence live in draft3's RESULT block below).
 *
 * Retail prologue being chased (asm/g3org_jp/nonmatchings/func_80068064.s):
 *   addiu sp,-0x438 / sw s3,0x424 / addu s3,a0 (vh->s3 $19)
 *   sw s0,0x418 / addu s0,a1 (vabid->s0 $16)
 *   sw s2,0x420 / ori s2,0x10 (slot=0x10 init ->s2 $18)
 *   sw s6,0x430 / addu s6,a3 (addr->s6 $22)
 *   sw s5,0x42C / addu s5,a2 (mode->s5 $21) / sw ra LAST (+ s1 save in
 *   the getInTransfer jal delay; s1 = the vabid copy - body wave, not
 *   attempted here).
 *
 * METRIC: prologue words go interleaved? Everything else is draft2
 * verbatim (wave-1 scan/program-loop laws + wave-2 no-shared-err-free
 * law carried; the 139-word structural middle stays open either way).
 */

extern unsigned char D_8017E038[];
extern unsigned short D_8017FB20;
extern short D_80178894;
extern unsigned long D_80178704[];
extern unsigned long D_8017876C[];
extern unsigned long D_801787B0[];
extern unsigned long D_8017FAE0[];
extern unsigned long D_8017FB6C[];
extern unsigned long D_8017FB24[];
extern long _spu_getInTransfer(void);
extern void _spu_setInTransfer(long mode);
extern long SpuMalloc(long size);

long SsVabOpenHeadWithMode(unsigned char *vh_p, long vabid_p, long mode_p, unsigned long addr_p)
{
    register unsigned char *vh asm("$19") = vh_p;    /* s3: the pBAV head */
    register long vabid asm("$16") = vabid_p;       /* s0: the vab id */
    register long slot asm("$18") = 0x10;            /* s2: the slot cursor */
    register unsigned long addr asm("$22") = addr_p; /* s6: caller SPU addr */
    register long mode asm("$21") = mode_p;         /* s5: placement mode */
    long arr[256];
    unsigned char *base;
    unsigned char *p;
    long *ap;
    long *ap2;
    long *end;
    unsigned long tp;
    unsigned long w0;
    unsigned long spu;
    unsigned long end_addr;
    long k;
    long i;
    long idx;
    long total;
    long m;
    long nprogs;
    long nv;
    long n;
    long ver;
    long raw;
    long val;
    long size;

    if (_spu_getInTransfer() == 1) {
        return -1;
    }
    _spu_setInTransfer(1);
    if (vabid >= 0x10) {
        _spu_setInTransfer(0);
        return -1;
    }
    if (vabid == 1) {
        for (k = 0; k < 0x10; k++) {
            if (D_8017E038[k] == 0) {
                D_8017E038[k] = 1;
                slot = k;
                D_8017FB20 = D_8017FB20 + 1;
                goto alloc_check;
            }
        }
        goto alloc_check;
    } else {
        if (D_8017E038[vabid] != 0) {
            goto alloc_check;
        }
        D_8017E038[vabid] = 1;
        slot = vabid;
        D_8017FB20 = D_8017FB20 + 1;
    }
alloc_check:
    if ((long)slot >= 0x10) {
        goto err;
    }
    D_8017876C[slot] = (unsigned long)vh;
    w0 = *(unsigned long *)vh;
    if ((w0 >> 8) != 0x564142) {
        D_8017E038[slot] = 0;
        goto err;
    }
    base = vh + 0x20;
    m = 0x40;
    if ((w0 & 0xFF) == 0x70 && *(unsigned long *)(vh + 4) >= 5) {
        m = 0x80;
    }
    D_80178894 = m;
    nprogs = *(unsigned short *)(vh + 0x12);
    if (D_80178894 < nprogs) {
        D_8017E038[slot] = 0;
        goto err;
    }
    D_80178704[slot] = (unsigned long)base;
    p = base;
    tp = (unsigned long)base + m * 0x10;
    idx = 0;
    for (k = 0; k < m; k++) {
        val = *p;
        *(unsigned long *)(p + 8) = idx;
        if (val) {
            idx++;
        }
        p += 0x10;
    }
    total = 0;
    D_801787B0[slot] = tp;
    nprogs = *(unsigned short *)(vh + 0x12);
    nv = *(unsigned char *)(vh + 0x16);
    tp += nprogs << 9;
    end = arr + nv;
    ap = arr;
    for (; ap < arr + 256; ap++) {
        if (end >= ap) {
            ver = *(unsigned long *)(vh + 4);
            raw = *(unsigned short *)tp;
            size = ver < 5 ? raw << 2 : raw << 3;
            *ap = size;
            total += *ap;
        }
        tp += 2;
    }
    D_8017FB6C[slot] = tp;
    if (mode != 0) {
        spu = addr;
    } else {
        spu = SpuMalloc(total);
        if (spu == -1) {
            D_8017E038[slot] = 0;
            goto err;
        }
    }
    end_addr = spu + total;
    total = 0;
    if (0x80000 < end_addr) {
        D_8017E038[slot] = 0;
        goto err;
    }
    D_8017FB24[slot] = spu;
    n = nv & 0xFF;
    if (n >= 0) {
        ap2 = arr;
        i = 0;
        do {
            total += *ap2;
            if (i & 1) {
                *(unsigned short *)(base + (i / 2) * 0x10 + 0xE) = (spu + total) >> 3;
            } else {
                *(unsigned short *)(base + (i / 2) * 0x10 + 0xC) = (spu + total) >> 3;
            }
            i++;
            ap2++;
        } while (n >= i);
    }
    D_8017FAE0[slot] = total;
    D_8017E038[slot] = 2;
    return (short)slot;
err:
    _spu_setInTransfer(0);
    D_8017FB20 = D_8017FB20 - 1;
    return -1;
}
