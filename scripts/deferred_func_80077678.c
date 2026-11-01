/* mainmenu_jp data_8008433C row TRUE HEAD #2 (listing 0x80077678, 0x40
 * frame, ra+s0..s5) - CD_newmedia: the PVD reader + root-directory
 * indexer. Its TAIL is the asm row's "head fragment"
 * (0x80077824..0x80077968): the entry-parse loop body spans the row
 * boundary (the loop head 0x800777D4 lives in the data row, the back-edge
 * bnez 0x800778E0 jumps into it, and the shared exit/epilogue sits in the
 * fragment) - the mis-typed-data spill is REAL CODE CONTINUITY, not a
 * boundary accident. Offline decode, cron-20261101-0621, oracle DOWN.
 *
 * IDENTITY (format strings): D_800235DC "CD_newmedia: Read error in
 * cd_read(PVD)\n", D_80023610 "CD_newmedia: Disc format error in
 * cd_read(PVD)\n", D_80023640 "CD_newmedia: Read error (PT:%08x)\n",
 * D_80023664 "CD_newmedia: sarching dir..\n" [sic - the typo is retail],
 * D_80023684 "\t%08x,%04x,%04x,%s\n", D_80023698 "CD_newmedia: %d dir
 * entries found\n". All gates read D_800C7CF0 (> 0 for errors, >= 2 for
 * the trace prints); printf = 0x8005C62C and strncmp = 0x8005D49C are
 * pinned/curated LIBC members.
 *
 * FLOW:
 *   s0 = &D_80149484 (the 0x800-B work buffer, bound D_80149C84)
 *   if (func_80077CD4(1, 0x10, s0) != 1)                 // SECTOR 16 = PVD
 *       { if (D_800C7CF0 > 0) printf("...Read error in cd_read(PVD)\n");
 *         return 0; }
 *   if (strncmp(&D_80149484[1], "CD001", 5) != 0)        // the ISO9660 mark
 *       { if (D_800C7CF0 > 0) printf("...Disc format error...\n");
 *         return 0; }
 *   lba = *(u32*)&D_80159510;                            // misaligned read
 *   if (func_80077CD4(1, lba, s0) != 1)                  // root directory
 *       { if (D_800C7CF0 > 0) printf("...Read error (PT:%08x)\n", lba);
 *         return 0; }
 *   if (D_800C7CF0 >= 2) printf("CD_newmedia: sarching dir..\n");
 *   count = 0; s4 = &D_80147E8C; s5 = &D_80147E90;
 *   // ---- entry loop (head 0x800777D4 in the data row, body in the
 *   //      asm-row fragment; the REPACKED stream format) ----
 *   do {
 *       len = src[0];                                    // u8 name length
 *       if (len == 0) break;
 *       rec = &D_80147E84 + count*0x2C;                  // (a3*0x2C fold)
 *       *(u32*)(&D_80147E8C + count*0x2C) = *(u32*)(src + 2);  // misaligned
 *       name = &D_80147E90 + count*0x2C;
 *       ord = count + 1;                                 // s3 = a3 + 1
 *       *(u32*)(&D_80147E84 + count*0x2C) = ord;         // 1-based ordinal
 *       *(u32*)(&D_80147E88 + count*0x2C) = src[6];      // the id byte
 *       memcpy_iso9660(name, src + 8, len);              // the interior alabel
 *       name[len] = 0;
 *       src += len + (len & 1) + 8;                      // even-padded advance
 *       if (D_800C7CF0 >= 2)
 *           printf("\t%08x,%04x,%04x,%s\n",
 *                  *(u32*)(&D_80147E8C + count*0x2C),   // %08x
 *                  *(u32*)(&D_80147E84 + count*0x2C),   // %04x
 *                  *(u32*)(&D_80147E88 + count*0x2C),   // %04x
 *                  name);                               // %s (5th arg)
 *       count = ord;
 *   } while (count < 0x80 && src < &D_80149C84);
 *   if (count < 0x80) *(u32*)(&D_80147E88 + count*0x2C) = 0;  // terminator
 *   D_800C8024 = 0;                                      // invalidate fn3's cache
 *   if (D_800C7CF0 >= 2) printf("CD_newmedia: %d dir entries found\n", count);
 *   return 1;
 *
 * STREAM FORMAT (this parser's view of the staged buffer): REPACKED
 * entries {u8 name_len@0; u32@2 misaligned; u8 id@6; char name[name_len]@8
 * even-padded} - a DIFFERENT shape from fn3's raw-ISO9660 view of the same
 * buffer; each func_80077CD4 call restages, and the two parsers never run
 * on the same staging.
 *
 * TABLE (base D_80147E84, 0x80 records x 0x2C): +0 u32 ordinal (1-based),
 * +4 u32 id (src[6]; 0-terminated by the tail store), +8 u32 (src +2),
 * +0xC char name[0x20]. fn2 (0x8007796C) walks id@+4/name@+0xC.
 *
 * ENTRY: called by the CD_newmedia path walker (TRUE HEAD #1, listing
 * 0x8007736C, 0xB0 frame: a0->s5, a1->s3 = the path string, prints
 * "%s: path level (%d) error\n" D_80023550 and "%s: dir was not found\n"
 * D_8002356C with %s = that string) guarded by D_800D8028 != D_800C7CFC;
 * the walker's other callers jal 0x8007736C from func_8003D3DC,
 * func_80025D9C, func_800264B4, func_8003D59C, func_800262FC and
 * data_8003B970 (a drifted code row). The walker's own decode stays with
 * the spill audit (step 1 of the parked plan).
 *
 * ADDRESS-SPACE NOTE (for the de-frame lane): all seven encoded call
 * targets in and around this row agree with the LISTING space (fn2/fn3/
 * 77CD4/77D40 jals, the walker's six external callers, printf/strncmp)
 * while the yaml row names sit 0xCFD0/0xD100 ABOVE the listing heads -
 * and that delta grows exactly 0x130 = 304 B (one sector's framing) over
 * the single 0x58000 sector boundary the row pair spans (runtime span
 * 0x5E8 = carve 0x4B8 + 0x130). mainmenu_eu's Witness A showed the
 * encoded space -0x9210 vs carve at its depth; the two regions do not
 * agree on the skew's sign or size - the drift is not a single linear
 * law. Reconciling the scan's address law vs the encoded-call space
 * stays de-frame-lane material.
 *
 * STAGING: step 6 of the parked plan (yaml split + C rows + judge live);
 * the split-fix scope owns the data-row carve.
 */

s32 func_80077678(void) {
    u8* src;
    u8* name;
    s32 count;
    s32 ord;
    u8 len;
    s32 lba;

    if (func_80077CD4(1, 0x10, (s32)&D_80149484) != 1) {
        if (D_800C7CF0 > 0) {
            printf(&D_800235DC);
        }
        return 0;
    }
    if (strncmp((char*)&D_80149484 + 1, "CD001", 5) != 0) {
        if (D_800C7CF0 > 0) {
            printf(&D_80023610);
        }
        return 0;
    }
    lba = *(s32*)&D_80159510;
    if (func_80077CD4(1, lba, (s32)&D_80149484) != 1) {
        if (D_800C7CF0 > 0) {
            printf(&D_80023640, lba);
        }
        return 0;
    }
    if (D_800C7CF0 >= 2) {
        printf(&D_80023664);
    }
    src = (u8*)&D_80149484;
    count = 0;
    while (1) {
        len = src[0];
        if (len == 0) {
            break;
        }
        ord = count + 1;
        *(s32*)((u8*)&D_80147E8C + count * 0x2C) = *(s32*)(src + 2);
        name = (char*)&D_80147E90 + count * 0x2C;
        *(s32*)((u8*)&D_80147E84 + count * 0x2C) = ord;
        *(s32*)((u8*)&D_80147E88 + count * 0x2C) = src[6];
        memcpy_iso9660(name, src + 8, len);
        name[len] = 0;
        src += len + (len & 1) + 8;
        if (D_800C7CF0 >= 2) {
            printf(&D_80023684,
                   *(s32*)((u8*)&D_80147E8C + count * 0x2C),
                   *(s32*)((u8*)&D_80147E84 + count * 0x2C),
                   *(s32*)((u8*)&D_80147E88 + count * 0x2C),
                   name);
        }
        count = ord;
        if (count >= 0x80) {
            break;
        }
        if (src >= (u8*)&D_80149C84) {
            break;
        }
    }
    if (count < 0x80) {
        *(s32*)((u8*)&D_80147E88 + count * 0x2C) = 0;
    }
    D_800C8024 = 0;
    if (D_800C7CF0 >= 2) {
        printf(&D_80023698, count);
    }
    return 1;
}
