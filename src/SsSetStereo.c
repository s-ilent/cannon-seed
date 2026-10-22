/* Matched 2026-10-22 through the sibling probe (slps_00270).
 *
 * LIBSND VS_MONO member .text+0x14 (extent 0x10; lui+sh $zero on the
 * backing static / jr $ra + nop). Clears the Sound System mono flag:
 * stores 0 as a halfword into the member's backing static
 * `_svm_stereo_mono` (see the SsSetMono unit for the full name
 * evidence; VS_MONO.OBJ labels the adjacent pair at 0 and 0x14). The
 * same body landed for sces_00269 (the boot's SsSetStereo source,
 * 2026-10-13) and every other target; the sibling probe measured slps_00270's retail
 * body ONE word off the sces copy (dw=1 @0x4) and two off the six
 * game modules (dw=2 @0x0+0x4) - the per-target bss address is the
 * ONLY delta (slps 0x80114FF8). The shared source resolves the static
 * per-target at link, so the flip is first-shot by construction.
 * LIBSND.H 3.3: void SsSetStereo(void).
 */
extern short _svm_stereo_mono;

void SsSetStereo(void)
{
    _svm_stereo_mono = 0;
}
