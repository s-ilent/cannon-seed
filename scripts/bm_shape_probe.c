/* bm_shape_probe.c - THE MOVSTRSI DECODE-LAW PROBE (banked cron-202610260649)
 *
 * LAW: gcc 2.6.3 (psx, -mips1 -O2 -G0 -funsigned-char -fno-builtin) compiles
 * a 0x80-byte struct assignment `*d = *s;` into the EXACT retail block-move
 * expansion class found throughout all eight targets:
 *
 *   dispatch head:  or t, src, dst; andi t, 3; beqz t -> aligned_path
 *                   (end setup addiu t0, src, 0x80 rides the delay slot or
 *                   lands as the unaligned path's first insn - a scheduler
 *                   choice; retail's func_8002AE60 head shows the real-insn
 *                   + AF78-duplicate form, the isolated probe the delay form)
 *   unaligned 0x54: lwl/lwr x4 at 0/4/8/12(src) ; swl/swr x4 at 0/4/8/12(dst)
 *                   ; addiu src,0x10 ; bne src,end ; addiu dst,0x10 ; j tail
 *   aligned   0x2c: lw x4 + sw x4, same 16-stride cursors and bne back
 *
 * PROOF: tools/cc.sh on this file emits (objdump of the .o)
 *   00803821 move a3,a0 / 00a03021 move a2,a1 / 00c71025 or v0,a2,a3
 *   30420003 andi v0,3 / 10400016 beqz v0 / 24c80080 addiu t0,a2,128
 *   lwl v0,3(a2)=88C20003 ... swr a1,12(a3) - byte-identical to the
 *   unaligned-loop signature words (addiu renders as 24xx = retail's addiu).
 * Retail deltas are register CONTEXT (cursors pre-bound in s0/s1/a3 by the
 * owning function) and the end-setup slot placement only.
 *
 * FAMILY MAP: scripts/bm_family_map.py scans the unaligned-loop signature
 * (88 unaligned+aligned pairs across all 8 targets; 9-13 per target, every
 * pair rhythm-confirmed). The boots' slps/sces copies sit inside the giant
 * func_80027340 rows: func_8002AE60 (0xc4 body = 0x30 straight-line 0x30-byte
 * copy + (short)s2==0x13 check + head 1) chains AF24/AF78/AF7C -> AFA8 ->
 * AFC4/B018 -> B044 -> B060/B0B4 -> B0E8 -> B0FC/B154 -> B180 -> B19C/B1F4
 * -> B220 -> B23C/B290 -> B2BC -> B2DC ... successive 0x80 struct copies.
 *
 * NEXT WINDOW LANDING RECIPE (slps+sces, 2 targets): (1) split the giant
 * row at yaml 0xB660 (VA 0x8002AE60), c-row extent = the full unit through
 * the last chunk; (2) decode func_8002AE60.c (body + the struct-assignment
 * sequence the movstrsi chunks serve); (3) judge_unit with the row
 * temporarily carved + flipped (the GsMapModelingData probe pattern);
 * (4) verify x2; ratchet audit. The x88 family map turns every other
 * target's copies into the same decode once their host rows split.
 */
/* bm.c - the movstrsi decode-law probe: does gcc 2.6.3 emit the retail
 * block-move shape for a 0x80-byte struct assignment?
 * retail chunks: head (or/andi/beqz + end setup) + AF24 0x54 unaligned
 * lwl/lwr loop + AF78 0x4 + AF7C 0x2c aligned lw/sw loop + j AFA8 */
struct Big { unsigned char b[0x80]; };

void bm_copy(struct Big *d, struct Big *s)
{
    *d = *s;
}
