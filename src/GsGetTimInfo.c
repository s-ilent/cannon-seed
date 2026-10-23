/* cc-post: keep-epilogue
 *
 * GsGetTimInfo - LIBGS SCLIB member (extent 0xe4), landed as ONE source
 * across EIGHT placements (file offsets 0x13A38 sces_00269,
 * 0x44338 mainmenu_jp, 0x43C3C mainmenu_eu, 0x2FE24 g3_jp, 0x2D2C0
 * g3org_jp, 0x2CBB4 g3org_eu, then 0x2F760 g3_eu and 0x13F70
 * slps_00270 - the boots' copy the data-row copy census surfaced as a
 * whole 0xe4 data row, retiring this comment's original no-placement
 * claim). The two census finds sit as whole data rows and flipped with
 * zero new pins: their single cross-copy variant slot is the internal
 * join jump, self-resolving per placement. Decoded offline against
 * the mainmenu_jp retail words through the cc.sh probe loop to 57/57
 * slots (the single cross-copy variant is the internal join jump, an
 * R_MIPS_26 relocation masked in the compare; all fifteen cross-target
 * word comparisons run 56/57 with exactly that one differing slot).
 *
 * The walk: the packed flags word copies whole; bit 3 selects the
 * image-present leg. Both blocks walk the pointer forward between the
 * halfword reads - the pixel block starts one word into the record and
 * ends with the walker on the pixel data; the CLUT block address is the
 * second header word's round-down-to-4 (srl/sll by 2) taken as a byte
 * offset from the record's second word, its own header word skipped
 * (a one-word advance) before the four halfword reads and the final
 * data pointer. The no-image leg reads the CLUT block only: one-word
 * skip, two halfwords, one-word advance, two halfwords, data pointer.
 * The image leg's CLUT walker is a separate pointer (kept in a second
 * register across the pixel walk) while the no-image leg reuses the
 * argument walker throughout.
 */
typedef struct {
    unsigned long  mode;                /* +0x00 */
    unsigned short cx, cy, cw, ch;      /* +0x04 */
    unsigned long *clut;                /* +0x0C */
    unsigned short px, py, pw, ph;      /* +0x10 */
    unsigned long *pixel;               /* +0x18 */
} TimImage;

void GsGetTimInfo(unsigned long *tim, TimImage *info)
{
    unsigned long h;
    unsigned short *q;

    h = *tim;
    info->mode = h;
    if ((h >> 3) & 1) {
        tim++;
        q = (unsigned short *)((unsigned char *)tim + ((*tim >> 2) << 2));
        tim++;
        info->px = *(unsigned short *)tim;
        info->py = *((unsigned short *)tim + 1);
        tim++;
        info->pw = *(unsigned short *)tim;
        info->ph = *((unsigned short *)tim + 1);
        tim++;
        info->pixel = tim;
        q += 2;
        info->cx = *(unsigned short *)q;
        info->cy = *((unsigned short *)q + 1);
        q += 2;
        info->cw = *(unsigned short *)q;
        info->ch = *((unsigned short *)q + 1);
        q += 2;
        info->clut = (unsigned long *)q;
    } else {
        tim += 2;
        info->cx = *(unsigned short *)tim;
        info->cy = *((unsigned short *)tim + 1);
        tim++;
        info->cw = *(unsigned short *)tim;
        info->ch = *((unsigned short *)tim + 1);
        tim++;
        info->clut = tim;
    }
}
