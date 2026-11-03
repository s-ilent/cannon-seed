/* cc-post: sdk-aspsx
 * cc-post: cc1-O1
 *
 * LIBSND VS_VH member: SsVabOpenHeadWithMode (the member's big
 * .text+0x90 piece). The VAB head opener with explicit SPU placement:
 * allocates a vab slot in the D_8017E038 state table (vabid==1 scans
 * for a free entry, any other id must be free already), bumps the
 * D_8017FB20 open counter, validates the "pBAV" head magic and the
 * version-derived program limit (0x40 programs for version < 5, 0x80
 * for version >= 5, stored to D_80178894), assigns sequential program
 * indices over the program table, walks 256 VAG size halfwords
 * accumulating the body size (size << 2 for version < 5, << 3 for
 * version >= 5), then places the bank either at the caller's SPU
 * address (mode != 0) or via SpuMalloc, rejects anything past the
 * 0x80000 SPU RAM bound, backfills the cumulative VAG offsets into the
 * program records at +0xC/+0xE (>> 3 into SPU word units) and marks
 * the slot state 2. Returns the slot id, or -1 on every failure path.
 *
 * Identity PROVEN by sdk_members.py unique placement + sig-db agree
 * (LIBSND VS_VH, g3org_jp 0x80068064, adoptable; the game row carries
 * the member's 0x3dc piece plus 0x6c of retail tail, extent 0x448).
 * The landed fake-head registrar src/g3org_jp/func_80068030.c forwards
 * here with mode 1.
 *
 * Shape notes: the (nv & 0xFF) < 0 guard after the SPU bound check is
 * never taken (andi result can't be negative) but the slti/bnez pair
 * is retail - reproduced by testing the masked value as a signed int.
 * The 256-slot scan always runs its full count; the process bound only
 * gates the body (the VAG table cursor advances every iteration via
 * the loop-back delay slot). The scan body's store-reload (*ap = size;
 * total += *ap) is retail gcc aliasing. The per-claim counter
 * increments are written once per arm; gcc cross-jumps the identical
 * addiu/sh tails into one shared block. The cumulative offset stored
 * per VAG is (spu + running total) >> 3, total accumulated BEFORE the
 * store (the entry holds the end offset of its VAG), and the even/odd
 * halves split across +0xC/+0xE of program record i/2.
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
    unsigned long arr[256];
    unsigned char *base;
    unsigned char *p;
    unsigned long *ap;
    unsigned long *ap2;
    unsigned long *end;
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
        goto err_free;
    }
    base = vh + 0x20;
    m = 0x40;
    if ((w0 & 0xFF) == 0x70 && *(unsigned long *)(vh + 4) >= 5) {
        m = 0x80;
    }
    D_80178894 = m;
    nprogs = *(unsigned short *)(vh + 0x12);
    if (D_80178894 < nprogs) {
        goto err_free;
    }
    D_80178704[slot] = (unsigned long)base;
    p = base;
    tp = (unsigned long)base + m * 0x10;
    idx = 0;
    for (k = 0; k < m; k++) {
        *(unsigned long *)(p + 8) = idx;
        if (*p) {
            idx++;
        }
        p += 0x10;
    }
    total = 0;
    ap = arr;
    D_801787B0[slot] = tp;
    nprogs = *(unsigned short *)(vh + 0x12);
    nv = *(unsigned char *)(vh + 0x16);
    tp += nprogs << 9;
    end = arr + nv;
    for (k = 0; k < 256; k++) {
        if (end >= ap) {
            ver = *(unsigned long *)(vh + 4);
            raw = *(unsigned short *)tp;
            *ap = ver < 5 ? raw << 2 : raw << 3;
            total += *ap;
        }
        ap++;
        tp += 2;
    }
    D_8017FB6C[slot] = tp;
    if (mode != 0) {
        spu = addr;
    } else {
        spu = SpuMalloc(total);
        if (spu == -1) {
            goto err_free;
        }
    }
    end_addr = spu + total;
    total = 0;
    if (0x80000 < end_addr) {
        goto err_free;
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
    return slot;
err_free:
    D_8017E038[slot] = 0;
err:
    _spu_setInTransfer(0);
    D_8017FB20 = D_8017FB20 - 1;
    return -1;
}
