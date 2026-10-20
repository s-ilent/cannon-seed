/* GsGetTimInfo - LIBGS SCLIB member (extent 0xe4), wave probe.
 *
 * TIM info walker: copies the packed flags word, then depending on the
 * image-present bit (bit 3) fills both the pixel block and the CLUT
 * block or the CLUT block only. Both blocks are walked with the pointer
 * advanced between the halfword reads; the CLUT block address comes
 * from the second header word rounded down to a 4-byte boundary taken
 * as a byte offset from tim+4 (it packs the pixel data length plus the
 * block headers, the low mode bits the mask drops), and its own header
 * word is skipped before the four halfword reads.
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
