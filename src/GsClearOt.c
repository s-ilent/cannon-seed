/* cc-post: keep-epilogue
 *
 * GsClearOt - LIBGS SCLIB member (extent 0x58), landed as ONE source
 * across EIGHT curated placements in window cron-20261020-2113 (file
 * offsets 0x18144 slps_00270, 0x17C0C sces_00269, 0x3E590 g3_jp, 0x3EBF4
 * g3_eu, 0x3BA2C g3org_jp, 0x3C048 g3org_eu, 0x533C0 mainmenu_jp, 0x539EC
 * mainmenu_eu - all eight the 0x58 sdk rows at the pinned LIBGS SCLIB
 * member addresses). Decoded offline first shot: probes/gcc263/GsClearOt.c
 * carries the shape story (byte-granular org/tail fields keep the
 * +0x04/+0x10 pointer arithmetic unscaled; 4 << width is the table size
 * in bytes and the callee takes the entry count 1 << width; the second
 * width read is a true reload - the two stores may alias it - which puts
 * the shift amount in a1 for the sllv whose destination is the call's
 * second argument register; the epilogue is GCC's own order, not the
 * maspsx branch-delay swap). tools/lm_probe_diff.py proved 22/22 against
 * the mainmenu_jp retail words before landing, and the eight rows are
 * word-identical except the single jal slot at word offset 0x40.
 *
 * The callee (a 0x98 member whose body is byte-identical across the
 * eight targets modulo its own per-target data refs, and whose only
 * caller is this member - fan-in 1 in every baseline scan) uses a shared
 * alias name curated per target:
 *   GsClearOt_clear: slps_00270 0x80030318, sces_00269 0x8002FE14,
 *     g3_jp 0x8004BE60, g3_eu 0x8004B7D0, g3org_jp 0x800492FC,
 *     g3org_eu 0x80048C24, mainmenu_jp 0x80060374, mainmenu_eu 0x8005FCAC.
 */
extern void GsClearOt_clear(unsigned char *org, long n);

typedef struct {
    long width;              /* +0x00 */
    unsigned char *org;      /* +0x04 */
    long top;                /* +0x08 */
    long bottom;             /* +0x0c */
    unsigned char *tail;     /* +0x10 */
} GsOT_W;

void GsClearOt(unsigned short top, unsigned short bottom, GsOT_W *ot)
{
    ot->top = top;
    ot->bottom = bottom;
    ot->tail = ot->org + (4 << ot->width) - 4;
    GsClearOt_clear(ot->org, 1 << ot->width);
}
