/* Matched 2026-10-13 through the round-trip oracle (sces_00269).
 *
 * LIBSND VS_MONO member .text+0x0 (extent 0x14; sig-db sig matches
 * retail: ori $v0,$zero,1 / lui+sh on the backing static / jr $ra +
 * nop). Sets the Sound System mono flag: stores 1 as a halfword into
 * the member's backing static `_svm_stereo_mono`. Name evidence: the
 * local Psy-Q 3.3 LIBSND.LIB archive carries member VS_MONO with
 * source path E:\PS-X~~00\SRC\SND\VM\VS_MONO.C, defined symbols
 * SsSetMono + SsSetStereo, and one undefined external besides the
 * pair: _svm_stereo_mono; the SVM cluster references the same symbol.
 * LIBSND.H 3.3: void SsSetMono(void) - no args, no return. The static
 * sits beyond the payload segment (EXE bss; no dlabel renders) and
 * resolves extern. Full evidence under target: mainmenu_jp in
 * symbols.curated.txt.
 */
extern short _svm_stereo_mono;

void SsSetMono(void)
{
    _svm_stereo_mono = 1;
}
