/* Matched 2026-10-12 through the round-trip oracle (mainmenu_eu).
 *
 * EU twin of func_8002C478 (the first family-C component, mainmenu_jp) -
 * the same function at VRAM -0x60, carved out of data_8002B8D8's row.
 * The JP source is the template: word-diff of the two zones shows 61/100
 * words identical and every one of the 39 diffs a relocation flavor.
 * Relocation map (JP -> EU), all read off the retail encodings:
 *   gp displacements      -4  (0x3D8/0x1048/0x1050 -> 0x3D4/0x1044/0x104C)
 *   state-map D_80089xxx  +0x814  (uniform across all 16 words touched)
 *   D_800C9B3C/44         +0x838  -> D_800CA374/D_800CA37C
 *   callees               -0xB0 (267C8/26784/26414 -> 26718/266D4/26364),
 *                         except func_80035A78 -> 0x80035A18 (-0x60)
 *   tail jump             -0x60 (.L8002ABD4 -> .L8002AB74)
 *
 * The yaml row carries the `noseed` marker for the same reason as JP:
 * this function OPENS with the gp load, so the scan's prologue-pair
 * anchor sits one word past its head (C41C) and an interior-seeded walk
 * re-decomposes the zone. First noseed row between unpinned data rows -
 * the gap-carve path owns the split and the seed-pass skips keep the
 * surrounding data rows untouched.
 *
 * Shaping notes are identical to the JP file (probes/gcc263/c478.c holds
 * the full recipe): file-scope r_v0 register variable (documented rule-6
 * exception), the hand-asm D_ store group with s0 as an opaque output,
 * the output-only cse-break asm before the last reset-table call, s1 = -1
 * placed after the func_800266D4 call for the delay-slot fills.
 *
 * Other code jumps into the middle of this function (the trampoline band
 * around func_8002DE00's row), and the equal-path tail jumps out to
 * .L8002AB74 inside func_8002AB64's row. All resolve by address through
 * build.sh's two-pass auto-definition, as already exercised by the JP
 * landing (ed3ba27).
 */

extern int D_80089B3C;
extern int D_80089B7C;
extern int D_80089C14;
extern int D_80089C54;
extern int D_80089C58;
extern int D_80089C5C;
extern int D_80089C60;
extern int D_80089F0C;
extern int D_80089F4C;
extern int D_80089F8C;
extern int D_80089FCC;
extern int D_8008A00C;
extern int D_8008A04C;
extern int D_8008A25C;
extern int D_8008A1D4;
extern int D_8008A1EC;
extern int D_800CA374;
extern int D_800CA37C;
extern void func_80026718(int, int, int);
extern void func_800266D4(int);
extern void func_80026364(int, int, int);
extern int func_80035A18(int);

register int r_v0 asm("$2");

void func_8002C418(void)
{
    int s1;
    int *s0;

    __asm__("lw %0,0x3D4($gp)" : "=r"(r_v0));
    if (r_v0 != 0) {
        func_80026718((int)&D_80089C14, (int)&D_800CA374, (int)&D_800CA37C);
        __asm__ volatile("sw $0,0x3D4($gp)");
    }
    __asm__ volatile("lw $5,0x1044($gp)");
    __asm__ volatile("lw $6,0x104C($gp)");
    func_800266D4((int)&D_80089C14);
    s1 = -1;
    /* MATCHING: retail store group, emitted verbatim; s0 leaves opaque
     * (see the JP twin's header - the tie/output-only/volatile asm
     * alternatives all fold under GCC 2.6.3's cse). */
    __asm__ volatile(
        "lui %0,%%hi(D_80089C54)\n\t"
        "addiu %0,%0,%%lo(D_80089C54)\n\t"
        "sw %1,0(%0)\n\t"
        "lui $1,%%hi(D_80089C58)\n\t"
        "sw %1,%%lo(D_80089C58)($1)\n\t"
        "lui $1,%%hi(D_80089C5C)\n\t"
        "sw %1,%%lo(D_80089C5C)($1)\n\t"
        "lui $1,%%hi(D_80089C60)\n\t"
        "sw %1,%%lo(D_80089C60)($1)"
        : "=r"(s0) : "r"(s1) : "$1");
    func_80026364((int)&D_80089B3C, 0, -1);
    func_80026364((int)&D_80089B7C, 0, -1);
    func_80026364((int)s0 - 0x40, 0, -1);
    func_80026364((int)&D_8008A25C, 0, 0);
    func_80026364((int)&D_80089F0C, 0, 0);
    func_80026364((int)&D_80089F4C, 0, 0);
    func_80026364((int)&D_80089F8C, 0, 0);
    func_80026364((int)&D_80089FCC, 0, 0);
    func_80026364((int)&D_8008A00C, 0, 0);
    func_80026364((int)&D_8008A04C, 0, 0);
    /* MATCHING: drop the shared (s0 - 0x40) cse entry so the last
     * reset-table call recomputes its argument from s0 (see header). */
    __asm__("" : "=r"(s0));
    func_80026364((int)s0 - 0x40, 2, -1);
    if (func_80035A18(0xC) == s1) {
        r_v0 = (int)&D_8008A1EC;
        D_8008A1D4 = r_v0;
        __asm__ volatile("j .L8002AB74");
    }
    D_8008A1D4 = s1;
}
