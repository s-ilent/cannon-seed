/* Matched 2026-10-13 through the round-trip oracle (g3org_jp).
 *
 * LIBSND VS_MONO member .text+0x14 (extent 0x10; sig-db sig matches
 * retail: lui+sh $zero on the backing static / jr $ra + nop). Clears
 * the Sound System mono flag: stores 0 as a halfword into the member's
 * backing static `_svm_stereo_mono` (see the SsSetMono unit for the
 * full name evidence; VS_MONO.OBJ labels the adjacent pair at 0 and
 * 0x14). LIBSND.H 3.3: void SsSetStereo(void). Full evidence under
 * target: mainmenu_jp in symbols.curated.txt.
 */
extern short _svm_stereo_mono;

void SsSetStereo(void)
{
    _svm_stereo_mono = 0;
}
