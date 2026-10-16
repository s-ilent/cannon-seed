/* Matched 2026-10-17 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% twins, pair-report matching lane).
 *
 * LIBGS MATRIX member .text+0x7c (extent 0x2c; sdk_members.py unique
 * placement + sig-db agree; the curated rows carry the evidence per
 * target). Provisions a GsCOORD2PARAM to the identity state: the
 * three +0x00..+0x08 longs take 0x1000 (the Gs one-point fixed
 * scale), the three +0x10..+0x14 halfwords and the three
 * +0x18..+0x20 longs take zero. The psyq 3.3 LIBGS.H is not in-tree,
 * so the parameter block is a plain byte-view struct covering the
 * fields the member touches (+0x0c..+0x0f and +0x16..+0x17 stay
 * untouched padding at this size).
 *
 * Source shape that makes GCC 2.6.3 reproduce the retail body:
 * three chained assignments (rightmost first), one per field group -
 * the zero halfword group stated FIRST (retail schedules the sh trio
 * before the sw trio), the diag group second, the tail group last.
 * Frameless leaf - no frame, no calls; the final sw rides the return
 * delay slot. The 0x1000 materialization is shared (one ori).
 */

typedef struct {
    long diag[3];   /* +0x00..+0x08: 0x1000 x3 */
    long pad0c;     /* +0x0c: untouched */
    short zeros[3]; /* +0x10..+0x14: 0 x3 */
    short pad16;    /* +0x16: untouched */
    long tail[3];   /* +0x18..+0x20: 0 x3 */
} GsCOORD2PARAM;

void GsInitCoord2param(GsCOORD2PARAM *cp)
{
    cp->zeros[0] = cp->zeros[1] = cp->zeros[2] = 0;
    cp->diag[0] = cp->diag[1] = cp->diag[2] = 0x1000;
    cp->tail[0] = cp->tail[1] = cp->tail[2] = 0;
}
