/* cc-post: keep-epilogue
/* Real-decompiled-C game function #9 (window 30, cron-202610300229). One
 * yaml row, 0x94 bytes, four spimdisasm pieces: the main body (0x48), the
 * ?0:1 false-arm store piece (0x8), the callback-registration piece (0x20)
 * and the shared 0x1B-command + epilogue tail (0x24). Caller: func_8002A2CC
 * (landed C game row); callees: the LIBCD host-command member func_8005FED8
 * (sdk row, word ABI), func_800602F8 / func_8005FEA8 (the CD callback
 * registration pair) and func_80063364 (the sdk-tagged 0x978 worker whose
 * address is handed to the latter).
 *
 * Shape notes banked while matching: the pair of host commands 0xE (with a
 * one-byte stack argument holding the flags) and 0x1B bracket the body -
 * the 0x1B call is the SHARED continuation, not an else-arm: the
 * `flags & 0x100` branch jumps over the flag store + registrations
 * straight into it. The flag store is the select `? 0 : 1` written as
 * if/else with the STORES IN THE ARMS - as a value-select GCC if-converts
 * it into srl/xori/andi bit math (5 words short), but memory stores are
 * not if-convertible, so the two-arm form keeps retail's branchy layout:
 * true arm sw zero, false arm sw v0 with the ori v0,1 hoisted into the
 * beqz delay slot. The byte argument is a plain char local whose address
 * escapes into the call; GCC schedules its sb into the jal delay slot.
 */
extern void func_8005FED8(long, void *, long);
extern void func_800602F8(void (*)(void));
extern void func_8005FEA8(void (*)(void));
extern void data_ready_callback(void);
extern void func_80063364(void);
extern long D_8016530C[];

void func_80062840(long flags)
{
    char buf;

    buf = flags;
    func_8005FED8(0xE, &buf, 0);
    if (flags & 0x100) {
        if (flags & 0x20)
            D_8016530C[0] = 0;
        else
            D_8016530C[0] = 1;
        func_800602F8(data_ready_callback);
        func_8005FEA8(func_80063364);
    }
    func_8005FED8(0x1B, 0, 0);
}
