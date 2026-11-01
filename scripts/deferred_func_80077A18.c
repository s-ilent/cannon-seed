/* mainmenu_jp func_80084924 row UNIT 3 - CD_cachefile: the raw-ISO9660
 * directory-record parser into the 0x40-entry cache (listing
 * 0x80077A18..0x80077CD0, 0x40 frame, ra+s0..s6); offline decode,
 * cron-20261101-0621 window, oracle DOWN (both links 404 at ~42.7h).
 *
 * IDENTITY (this window's format-string reads, data_80020000.data.s):
 *   D_800236BC "CD_cachefile: dir not found\n"    - staged-load failure
 *   D_800236DC "CD_cachefile: searching...\n"     - entry
 *   D_80023700 "\t(%02x:%02x:%02x) %8d %s\n"      - per-record dump
 *   D_8002371C "CD_cachefile: %d files found\n"   - exit
 * and the arm constants D_800236F8/FC/FE are the C strings "." and "..":
 * slots 0/1 of the cache are the ISO9660 self/parent entries - they are
 * SYNTHESIZED from the constants, never copied from the stream.
 *
 * STREAM FORMAT (the staged buffer D_80149484..D_80149C84, 0x800 B) =
 * RAW ISO9660 directory records:
 *   +0x00  u8  record length (0 = terminator; the cursor advances by it)
 *   +0x02  u32 extent LBA (misaligned, lwl 5/lwr 2)  -> func_7502C arg
 *   +0x0A  u32 data size (misaligned, lwl 0xD/lwr 0xA) -> rec +4
 *   +0x20  u8  name length
 *   +0x21  char name[name_len] -> memcpy_iso9660 into rec +8, NUL at +8+len
 * (extent@+2 and size@+0xA are the ISO9660 record's own fields; the
 * "%8d" in the dump prints the SIZE.)
 *
 * CACHE TABLE (D_80147884, 0x40 records x 0x18 stride):
 *   +0..+2  three bytes (the dump's %02x x3; written by func_8007502C)
 *   +4      u32 size (from stream +0xA)
 *   +8      name area - "." at slot 0, ".." at slot 1, copies from slot 2
 * (the dump's %s arg = rec + 8; s3/s4/s1 in the asm are three forms of
 * the same index: rec+8 cursor, rec cursor, i*0x18 byte index.)
 *
 * FLOW: id guard on D_800C8024 (== a0 -> return 1); staged load via
 * func_80077CD4(1, *(u32*)(&D_80147E60 + a0*0x2C), &D_80149484); != 1 ->
 * "dir not found" (gate D_800C7CF0 > 0) and return -1; "searching..."
 * (gate >= 2); the parse loop lowers from the "ori 1; beqz never-taken"
 * idiom (gcc's do-while materialization): break on len == 0, break on
 * i >= 0x40, continue only while src < &D_80149C84; arms dispatch on the
 * RECORD INDEX i (i == 0 -> ".", i == 1 -> "..", else the name copy) and
 * gcc folds the i==0/i==1 arms' store addresses to s5+8 / s5+0x20 (the
 * induction-variable materialization); per-record dump gate >= 2 with
 * args (rec[0], rec[1], rec[2], size, rec+8); tail: D_800C8024 = a0;
 * if (i < 0x40) *(u8*)(&D_8014788C + i*0x18) = 0 (the next slot's first
 * name byte zeroed); "%d files found" (gate >= 2); return 1.
 *
 * NOTE: the func_8007502C call sits BEFORE the arms, so slots 0/1 also
 * receive the extent LBA - the synthesized entries are otherwise
 * constants-only.
 *
 * STAGING: step 6 of the parked plan (yaml split + C rows + judge live);
 * the memcpy_iso9660 interior rename composes here (7059420f).
 */

s32 func_80077A18(s32 id) {
    u8* src;
    u8* rec;   /* walks D_80147884 + i*0x18 */
    u8* rec8;  /* walks D_8014788C + i*0x18 (== rec + 8) */
    s32 i;
    u8 len;

    if (id == D_800C8024) {
        return 1;
    }
    if (func_80077CD4(1, *(s32*)((u8*)&D_80147E60 + id * 0x2C), (s32)&D_80149484) != 1) {
        if (D_800C7CF0 > 0) {
            printf(&D_800236BC);
        }
        return -1;
    }
    if (D_800C7CF0 >= 2) {
        printf(&D_800236DC);
    }
    src = (u8*)&D_80149484;
    rec = (u8*)&D_80147884;
    rec8 = (u8*)&D_8014788C;
    i = 0;
    while (1) {
        len = src[0];
        if (len == 0) {
            break;
        }
        func_8007502C(*(s32*)(src + 2), rec);     /* misaligned u32 at +2 */
        *(s32*)(rec + 4) = *(s32*)(src + 0xA);    /* misaligned u32 at +0xA */
        if (i == 0) {
            *(u16*)(rec + 8) = *(u16*)&D_800236F8;  /* "." */
        } else if (i == 1) {
            *(u16*)(rec + 8) = *(u16*)&D_800236FC;  /* ".." */
            rec[0xA] = *(u8*)&D_800236FE;
        } else {
            memcpy_iso9660(rec8, src + 0x21, src[0x20]);
            rec8[src[0x20]] = 0;
        }
        if (D_800C7CF0 >= 2) {
            printf(&D_80023700, rec[0], rec[1], rec[2], *(s32*)(rec + 4), rec8);
        }
        rec += 0x18;
        rec8 += 0x18;
        src += len;
        i++;
        if (i >= 0x40) {
            break;
        }
        if (src >= (u8*)&D_80149C84) {
            break;
        }
    }
    D_800C8024 = id;
    if (i < 0x40) {
        *(u8*)((u8*)&D_8014788C + i * 0x18) = 0;
    }
    if (D_800C7CF0 >= 2) {
        printf(&D_8002371C, i);
    }
    return 1;
}
