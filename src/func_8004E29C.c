/* cc-post: keep-epilogue
 *
 * First real-decompiled-C game function of the twenty-ninth window
 * (cron-202610300053) - the pivot from stub/asm landings to hand-written C.
 *
 * Game glue in the g3_eu low game zone: frameless-looking non-leaf wrapper
 * that forwards its argument to the GTE screen-height setter and returns
 * nothing. Caller: func_80022B5C (the 0x4EE0 untagged game row at the base
 * of the text segment) - the call edge into this wrapper is what marks the
 * row game-authored rather than stray library code.
 *
 * Shape: GCC 2.6.3 -O2 non-sibcall wrapper - addiu $sp,-0x18, sw $ra,0x10($sp),
 * jal SetGeomScreen (0x8004E40C, the local LIBGTE copy this target curates),
 * nop, lw $ra, addiu $sp,0x18, jr $ra, nop. No argument moves: the a0
 * passthrough IS the argument marshalling.
 */
extern void SetGeomScreen(long);

void func_8004E29C(long height)
{
    SetGeomScreen(height);
}
