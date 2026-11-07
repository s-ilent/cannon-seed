/* LIBSND VS_MONO member .text+0x0 (extent 0x14; ori $v0,$zero,1 /
 * lui+sh on the backing static / jr $ra + nop). Sets the Sound System
 * mono flag: stores 1 as a halfword into the member's backing static
 * `_svm_stereo_mono`. LIBSND.H 3.3: void SsSetMono(void) - no args,
 * no return. The static sits beyond the payload segment (EXE bss; no
 * dlabel renders) and resolves extern; the shared source resolves the
 * static per-target at link.
 *
 * Landings: sces_00269 matched 2026-10-13 through the round-trip
 * oracle (sig-db sig matches retail); slps_00270 matched 2026-10-22
 * through the sibling probe (the retail body ONE word off the sces
 * copy, dw=1 @0x8, and two off the six game modules, dw=2 @0x4+0x8 -
 * the per-target bss address is the ONLY delta: slps 0x80114FF8, the
 * same 0x8011 page as sces 0x80114578 with the lower half differing;
 * the six sit on their own pages), so the flip is first-shot by
 * construction. The same body landed for every other target.
 *
 * Name evidence: the local Psy-Q 3.3 LIBSND.LIB archive carries member
 * VS_MONO with source path E:\PS-X~~00\SRC\SND\VM\VS_MONO.C, defined
 * symbols SsSetMono + SsSetStereo, and one undefined external besides
 * the pair: _svm_stereo_mono; the SVM cluster references the same
 * symbol. Full evidence under target: mainmenu_jp in
 * symbols.curated.txt.
 *
 * sces_00269 row note: the yaml row at 0x248D0 (VA 0x800440D0)
 * originally carried the sibling's VA-derived auto-name (the 0x1224
 * asm row at VA 0x80049780); the name-uniqueness law renamed the c row
 * to the true name once the misnomer was traced, mirroring the
 * slps_00270 row's true-name landing.
 */
extern short _svm_stereo_mono;

void SsSetMono(void)
{
    _svm_stereo_mono = 1;
}
