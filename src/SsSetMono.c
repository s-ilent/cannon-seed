/* Matched 2026-10-22 through the sibling probe (slps_00270).
 *
 * LIBSND VS_MONO member .text+0x0 (extent 0x14; ori $v0,$zero,1 /
 * lui+sh on the backing static / jr $ra + nop). Sets the Sound System
 * mono flag: stores 1 as a halfword into the member's backing static
 * `_svm_stereo_mono`. The same body landed for sces_00269
 * (func_80049780.c, 2026-10-13) and every other target; the sibling
 * probe measured slps_00270's retail body ONE word off the sces copy
 * (dw=1 @0x8) and two off the six game modules (dw=2 @0x4+0x8) - the
 * per-target bss address is the ONLY delta (slps 0x80114FF8: the same
 * 0x8011 page as sces 0x80114578, lower half differs; the six sit on
 * their own pages). The shared source resolves the static per-target
 * at link, so the flip is first-shot by construction. Name evidence
 * chain under target: mainmenu_jp in symbols.curated.txt (local Psy-Q
 * 3.3 LIBSND.LIB member VS_MONO, source path E:\PS-X~~00\SRC\SND\VM\
 * VS_MONO.C, one undefined external besides the pair:
 * _svm_stereo_mono). LIBSND.H 3.3: void SsSetMono(void).
 */
extern short _svm_stereo_mono;

void SsSetMono(void)
{
    _svm_stereo_mono = 1;
}
