/* cc-post: sdk-aspsx
 * cc-post: cc1-O1
 *
 * LIBSND VS_VH member: SsVabOpenHeadWithMode (the member's big
 * .text+0x90 piece). DRAFT 2 (judge wave 2, window cron-202611030614).
 * VAB head opener with explicit SPU placement: allocates a vab slot in
 * the D_8017E038 state table, bumps the D_8017FB20 open counter,
 * validates the "pBAV" head magic and the version-derived program
 * limit, assigns sequential program indices, walks 256 VAG size
 * halfwords, places the bank (mode != 0: caller's address, else
 * SpuMalloc), rejects past the 0x80000 SPU RAM bound, backfills the
 * cumulative VAG offsets into the program records (+0xC/+0xE, >> 3)
 * and marks the slot state 2. Returns the slot id, or -1.
 *
 * Wave 2 shape law (banked this window): the retail binary has NO
 * shared err_free block - each of the four free paths INLINES its own
 * D_8017E038[slot] = 0 (magic fail indexes through a3 = (short)slot,
 * malloc fail through the s1 sign-extended copy, the D_80178894-gate
 * and SPU-bound fails re-derive sll16/sra16 (short)slot), then jumps
 * the shared err block (setInTransfer(0) with a0 pre-zeroed on every
 * path's delay slot, counter--, return -1). A shared err_free label
 * makes gcc emit one free block with one index register - 5+ words
 * off. The four err paths that need NO free (getInTransfer==1,
 * vabid>=0x10, alloc-fail scan) jump .L80068480 (the shared
 * return--1) directly.
 *
 * Wave 1 shape laws (banked window cron-202611031258): (1) the scan
 * guard compares SIGNED (long* pointers); (2) the scan loop is
 * cursor-based (for ap = arr; ap < arr + 256; ap++), retail
 * materializes arr+256 (addiu t0, sp, 0x410); (3) the program-loop
 * body loads *p BEFORE the store (the sw rides the beqz delay slot);
 * (4) the retail prologue is FULLY INTERLEAVED - every param import
 * carries its own save (sw s3/addu s3,a0 / sw s0/addu s0,a1 / sw s2/
 * ori s2,0x10 / sw s6/addu s6,a3 / sw s5/addu s5,a2), ra saves
 * LAST, sw s4 follows, and the s1 save rides the first call's DELAY
 * SLOT (s1 = a vabid copy made in the getInTransfer-verdict branch's
 * delay - addu s1,s0,zero - reused as the else-branch slot source;
 * gcc 2.6.3 emits this neither at -O1 nor -O2: both levels emit the
 * batch [frame][ra][descending s saves][imports][jal][const delay]
 * prologue, judge DIFF stuck at 220/229 across both). The (nv & 0xFF)
 * < 0 guard is never taken but the slti/bnez pair is retail. The
 * scan body's store-reload (*ap = size; total += *ap) is retail gcc
 * aliasing.
 *
 * Remaining decode notes: slti (vabid<0x10) result is REUSED as the
 * ==1 constant in the bne v1,v0 verdict test; slot's sign-extend
 * sll16 rides the alloc-scan loop's exit delay; program-index walk
 * uses s3 = base with a3 = m bound copy and v1 = cursor.
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

long SsVabOpenHeadWithMode(unsigned char *vh, short vabid, short mode, unsigned long addr)
{
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
    long slot;
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

    slot = 0x10;
    if (_spu_getInTransfer() == 1) {
        return -1;
    }
    _spu_setInTransfer(1);
    if ((long)vabid >= 0x10) {
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
