/* cc-post: sdk-aspsx
 * cc-post: cc1-O1
 * cc-post: rule15
 * cc-post: rule16 jdelay li v0 -1
 * cc-post: rule17 $L19 jdelay addu 4 0
 *
 * DRAFT 22 (cron-202611041358): THIS FILE = draft21 + the slt signed
 * re-shape (the banked NEXT(2), the draft17 byte facts): the backfill
 * loop's address holders move from C POINTERS to SIGNED LONGS - the
 * long* pointer compare emits sltu while the original held the
 * addresses in signed longs (retail slt v0,a3,a1 / slt v0,a1,t0), and
 * end_addr goes unsigned->signed for the 0x80000 check (retail slt at
 * 0x80068300, built sltu). Deref sites re-spelled *(long*)p; the loop
 * steps ap += 4 / ap2 += 4. Judge-deferred like draft21 (oracle down):
 * the offline shape check is that slt MATERIALIZES at the loop
 * compares + the 0x80000 check while the draft18-closed store->reload
 * window survives byte-identical; the exact count resolves at the
 * judge. The rule17 anchor ($L19) may renumber with the source edit -
 * re-pin the marker if gcc's err label moves (the rule-10 precedent).
 * CORRECTION (cron-202611042128 audit, see draft26): the end_addr
 * HALF of this lever is a REGRESSION - the header mis-cited 0x80068300
 * (the loop back-edge, correctly slt) for the 0x80000 check; the real
 * check at 0x8006836C is retail SLTU. The loop-holder conversions
 * STAND; end_addr reverts to unsigned in draft26.
 *
 * DRAFT 21 (cron-202611041358): THIS FILE = draft20 + `cc-post: rule17
 * $L19 jdelay addu 4 0` - the banked NEXT(1), the rule-17
 * merge-polarity cc_post transform SHIPPED this window (tools/cc_post.py
 * _rule17_on_file + the cc.sh marker pass-through + the CLI-path
 * selftest tests/test_cc_post_rule17.py, 12 cases; suite 145/145). The
 * transform: the built `beq $2,$0,$L19` (fail branches FAR to the
 * shared err tail, body falls through) inverts to `bne $2,$0,$Lr17c`
 * (+3 by construction: delay + j + jdelay then the join - exactly
 * retail's bnez-near), the built delay (addu $4,$19,$zero) is KEPT
 * verbatim in the bne delay, and the inline 2-word err trampoline
 * `j $L19` + `addu $4,$0,$zero` (the marker jdelay) is inserted before
 * the join - the draft16 map's +2 words, retail's trampoline shape.
 * Offline pipeline proof (compile-only, cc.sh): the .mas.s delta vs
 * draft20's build is EXACTLY the merge site (beq->bne + the 3-line
 * trampoline) - nothing else moved.
 * JUDGE-DEFERRED (the oracle is DOWN this window: both 2026-11-01 disc
 * links 404, the baselines/ dir rolled back to the woven set, AND the
 * disc_*_true/ third recovery medium rolled back with the sandbox -
 * judge verdicts are live-only, nothing was scored). When the oracle
 * returns, judge this file and confirm three open items: (1) the
 * jdelay op spelling - `addu 4 0` (gcc 2.6.3's own zero-arg spelling,
 * the family-consistent guess, assembles 0x00801025) vs retail's actual
 * word (li a0,0 -> 0x24040000 is the alternative; one judge diff read
 * decides, the marker arg is the correction vehicle); (2) the SIZE
 * accounting - the trampoline is +2 words against the draft20 build
 * whose SIZE already matches the 0x448 row extent, so this draft
 * EXPECTS SIZE 1098 (row +2) until a tail lever sheds 2 words (the
 * banked tail list: the 66-word tail loop levers, the slt signed
 * re-shape, the pre-loop dst-reg/sharing form); (3) the err-tail
 * companion - if retail moved the setInTransfer(0) a0=0 setup INTO the
 * trampoline (the banked "delay a0=0" dump fact), retail's err-tail
 * jal delay may be a nop where the built still emits addu $4,$0,$zero -
 * a separate one-site follow-up this rule does not reach.
 * NEXT after the judge pass: re-read the reg-home chain (the bne delay
 * keeps the built a0=vh copy; retail's merge delay is move a2,s3 - the
 * hv-chain home), then the tail levers. The anchor $L19 is
 * gcc-deterministic for this frozen source; any source edit that moves
 * it must re-pin the marker (the rule-10 precedent).
 *
 * LIBSND VS_VH member: SsVabOpenHeadWithMode (g3org_jp 0x48864, extent
 * 0x448). DRAFT 17 (cron-202611041243): THIS FILE = draft16 + the mode
 * SPLIT-TEMP (see the DRAFT 17 RESULT) - the banked NEXT(1) from
 * cron-202611041128. The mode test reuses the `shifted` ($2/v0) pin:
 * `shifted = mode << 16; if (shifted != 0)` - the def must land in the
 * hard-reg home, so the extend materializes as sll v0,s5,16 (retail
 * 0x80068328) instead of draft16's in-place sll s5,s5,16; the bnez then
 * tests the temp. `mode << 16 != 0` == `(short)mode != 0` (the low-16
 * zero test survives both spellings). shifted's two webs (the vb extend
 * at the top, the mode test here) are disjoint, neither crosses a call.
 * DRAFT 18 (cron-202611041243): THIS FILE = draft17 + the in-loop memory
 * barrier between `*ap = size;` and `total += *ap;` (see the DRAFT 18
 * RESULT) - the backfill-loop lever from the draft17 region dump. Retail
 * keeps the source-verbatim STORE->RELOAD (sw v0,0(a1) / lw v0,0(a1) /
 * nop / addu s0,s0,v0 at 0x800682EC..0x800682F8) while gcc 2.6.3
 * store-forwards the pair into one addu (-3 words: the skew source that
 * masked draft17's byte-exact mode pair). The draft15 empty-asm memory
 * clobber law ("kills gcc 2.6.3's store-forwarding and emits nothing")
 * applies verbatim inside the loop body.
 *
 * DRAFT 19 (cron-202611041243): THIS FILE = draft18 + the spu pin
 * `register unsigned long spu asm("$7")` (a3) - the spu->a3 nudge from
 * the draft18 map. Retail homes spu in a3 (addu a3,v0,zero after
 * SpuMalloc, addu a3,s6,zero in the bnez delay, bne a3,v0, addu
 * v1,a3,s0); the built rides addr's dead $22 home (s6). The pin should
 * also EVICT tp from a3 (retail tp home a2: the FB6C store sw a2 and
 * the tp+=2 addiu a2) and re-home end to a3 - the built/retail tp+end
 * homes are exactly swapped. spu never crosses a call: its def is
 * either the bnez delay (spu=addr, taken path) or the post-jal move
 * (malloc path).
 *
 * DRAFT 19 RESULT (cron-202611041243): POSITIVE - judge DIFF 155/274
 * @ 1096 (SIZE MATCH - the built section reached retail's exact row
 * extent) from 173/273 (-18 diff words). The whole malloc window
 * CLOSED: addu a3,s6,zero (bnez delay = spu=addr), move a0,s0,
 * addu a3,v0,zero (spu=ret), li v0,-1, bne a3,v0, addu v1,a3,s0 -
 * byte-exact at address; the hoisted pre-call v1=s6+s0 form dissolved
 * (the delay now carries spu=addr exactly like retail). tp did NOT
 * re-home to a2 (still a3: 0x80068308 addiu a3 / 0x80068324 sw a3)
 * - gcc re-chose freely, the pin is the lever (draft20).
 * REMAINING MAP: 0x800680AC the verdict j word (structural middle
 * delta); 0x80068188..0x80068250 (51 words, the merge-polarity +
 * m-check + verdict-2 region); 0x80068258..0x800682C8 (29 words, the
 * pre-loop: nprogs/nv load homes, tp+= form, end/ap sharing, the t0
 * bound); 0x800682D4..D8 (ver-load hv home + raw-load tp home);
 * singles 0x80068300 (sltu vs slt signedness), 0x80068308/324 (tp
 * home a3 vs a2), 0x8006835C..60 + 0x80068370 (the err-trampoline j
 * target = the structural delta); 0x80068378..0x8006847C (66 words,
 * the tail: second backfill loop + FAE0/E038 tail extends).
 *
 * DRAFT 20 (cron-202611041243): THIS FILE = draft19 + TWO home pins
 * (the draft10 three-pin precedent): `register unsigned char *hv
 * asm("$4")` (a0 - retail's loop-read home: lhu 0x12(a0) / lbu
 * 0x16(a0) / lw 0x4(a0); the built rode t1) and `register unsigned
 * long tp asm("$6")` (a2 - retail's raw-load/increment home: lhu
 * v1,0(a2) / addiu a2,a2,0x2 / the FB6C store sw a2; the built rode
 * a3). Neither web crosses a call (hv dead before the malloc window;
 * tp has no call in its range). Expected cascade: end re-homes a3
 * (retail), the arr bound may pre-materialize in t0.
 *
 * DRAFT 20 RESULT (cron-202611041243): POSITIVE - judge DIFF 151/274
 * @ 1096 (SIZE HELD at the exact row extent) from 155/274 (-4). Both
 * pins took: the tp home closed (0x80068308 addiu a2 / 0x80068324 sw
 * a2 byte-exact; the raw load lhu v1,0(a2) exact) and the hv loop
 * reads re-homed a0 (0x800682D4..D8 closed). The -4 only: gcc's load
 * DST regs still differ in the pre-loop (lhu v1 vs retail lhu v0 at
 * the nprogs/nv pair) and end/ap still share the sp+16 temp vs
 * retail's direct addiu a1,sp,0x10 - both inside the 29-word
 * 0x80068258..0x800682C8 run. REMAINING MAP (151 words, all
 * shape-level): 0x800680AC (1, the verdict j word - structural
 * middle delta); 0x80068188..0x80068250 (51, the merge-polarity +
 * m-check + verdict-2 region - the rule-17 cc_post candidate's
 * territory); 0x80068258..0x800682C8 (29, the pre-loop: load dst
 * regs, end/ap sharing, the t0 bound, the slt/sltu signedness pair);
 * 0x80068300 (1, sltu vs slt); 0x8006835C..60 + 0x80068370 (3, the
 * err-trampoline j target - structural delta); 0x80068378..0x8006847C
 * (66, the tail: second backfill loop + FAE0/E038 tail extends).
 * NEXT (in order): (1) the rule-17 merge-polarity cc_post candidate
 * (rule-16 class: invert the branch + insert the j-trampoline pair;
 * the delay content differs per site - marker-arg pattern) for the
 * 51-word region; (2) the slt signed re-shape (the addresses in
 * signed longs) for 0x80068300 + the pre-loop compares; (3) the tail
 * loop levers; (4) the pre-loop dst-reg/sharing form. THEN land
 * SsVabOpenHeadWithMode g3org_jp judge EXACT + verify GREEN; the
 * seven region twins after.
 *
 * DRAFT 18 RESULT (cron-202611041243): POSITIVE - judge DIFF 173/273
 * @ 1092 from 193/271 @ 1084 (-20 diff words). The in-loop barrier
 * reproduced retail's store->reload verbatim (sw v0,0(a1) / lw v0,0(a1)
 * / nop / addu s0,s0,v0 at 0x800682EC..F8) AND cascaded: the whole
 * slot-extend/D_8017FB6C-store/mode-test/malloc-arg window closed
 * byte-exact except register-selection words (the diff runs collapsed
 * from 0x8006830C..0x8006833C wholesale to singles: 0x80068300 sltu
 * a1,a0 vs slt a1,t0; 0x80068308 addiu a3 vs a2 (tp home); 0x80068324
 * sw a3 vs a2 (FB6C store); 0x80068330/3C/44/48 the spu home cascade;
 * 0x8006835C..0x8006846C the 69-word tail). The mode test pair (sll
 * v0,s5,16 / bnez v0,+13) is now BYTE-EXACT AT ADDRESS. NEW LAWS: the
 * empty-asm clobber works INSIDE a loop body (emits nothing, forces
 * the reload, the loop's other loads re-derive); the reload nop is
 * gcc's unfilled load-delay slot, matching retail.
 * REMAINING MAP after draft18: the 0x80068188..0x80068250 run (51
 * words, the merge-polarity + m-check + verdict-2 region), the
 * 0x80068258..0x800682C8 run (29 words, the pre-loop/home-swap
 * region), the 0x8006835C..0x8006846C tail (69 words), the
 * 0x80068474..0x800684A4 run (13 words), plus 6 single words in the
 * malloc window (all reg-home/signedness).
 *
 * DRAFT 17 RESULT (cron-202611041243): POSITIVE-CONTENT, COUNT-MASKED.
 * judge DIFF 193/271 @ 1084 - the SAME counts as draft16, but the
 * region dump (build/judge .elf vs baselines/g3org_jp.bin) shows the
 * mode test pair now BYTE-EXACT CONTENT: built 0x80068320 = sll
 * v0,s5,16 (00151400, retail's own word) + bnez v0,+13 (1440000d,
 * retail's own word) vs draft16's in-place sll s5,s5,16/bnez s5. The
 * pair sits at VA-2 (0x80068320/24 vs retail 0x80068328/2c) behind the
 * backfill-loop skew - the words are right, the address is not, so the
 * VA-to-VA diff count cannot see it. The skew source identified in the
 * same dump: retail keeps `total += *ap` as store->reload (sw/lw/nop/
 * addu) where gcc forwards to one addu (-3 words), plus the built
 * drops retail's nprogs reload/lbu s4 separation into a fused pair
 * around the D_801787B0 store. NEW BYTE FACTS BANKED: (a) retail's two
 * backfill-loop compares are SIGNED slt on address-valued regs (slt
 * v0,a3,a1 / slt v0,a1,t0) where the built emits UNSIGNED sltu on its
 * long* pointer compares - the original source held the addresses in
 * signed longs (or index form), a lever for a later rung; (b) retail
 * materializes the loop bound t0 = arr+256 ONCE pre-loop (addiu
 * t0,sp,0x410 at 0x8006829C) where the built re-materializes per edge;
 * (c) the spu reg-home diff confirmed: built addu s6,v0,zero (spu
 * rides addr's dead $22 home) vs retail addu a3,v0,zero.
 * NEXT: the reload barrier (draft18), then the slt/sltu signed-long
 * re-shape, then the spu->a3 pin.
 *
 * DRAFT 16 (cron-202611041128): the 139-word structural middle
 * 0x80068160..0x80068388 - the banked NEXT(1) from cron-202611041013.
 * THAT FILE = draft15 + the (short)mode test (see the DRAFT 16 RESULT).
 * Source vs draft10: slot re-typed SHORT (register short slot asm("$18")
 * = 0x10 - retail re-extends at every use: per-predecessor sll v0,s2,16
 * feeding the merge sra, sll16/sra14 index folds, the s1 call-crossing
 * copy); vh UNPINNED; the vh SPLIT (hv local); the fb-SPLIT increment;
 * the version reads SIGNED; the m reload via an empty memory barrier;
 * the goto-ok alloc merge form.
 *
 * DRAFT 11 (slot-short alone): s7 spill REPRODUCED at the draft10 shape
 * (sw s7 0x434, frame -0x440) - confirming the banked negative; built
 * SIZE 1072, extends materialized but nv pushed to s7.
 * DRAFT 12 (vh unpinned + goto-ok merge): spill persists - gcc still
 * keeps vh in s3 whole-function (import move s3,a0 unpinned is IDENTICAL
 * to retail's prologue), base s4, nv s7.
 * DRAFT 13 (the vh SPLIT: hv = vh at alloc_ok, all post-merge reads
 * through hv): THE SPILL DISSOLVES - hv's web starts after the last
 * setInTransfer call so gcc homes it in a temp (t1), vh's web ENDS at
 * the split, s3 frees for base (addiu s3,t1,0x20), nv takes s4 - the
 * prologue goes byte-exact through 0x800680A8 (sw ra/sw s4/jal/sw s1
 * delay/ori v1,1/bne/move s1,s0). DIFF 217/267 @ 1068 (from 248/268 @
 * 1072). THE BANKED "middle re-shape is the only vehicle" HYPOTHESIS
 * CONFIRMED WITH ITS MECHANISM: the spill was vh's pinned corpse, not
 * slot-short pressure - single-register pins cannot fix it because the
 * extra call-saved tenant IS the pin itself.
 * DRAFT 14 (signed version + volatile m reload + increment-before-slot):
 * slti LANDED (signed compare byte-shape); the volatile read-back came
 * out lhu + manual sll16/sra16 extend (5 words) instead of retail's
 * sign-extending lh (3); the full-statement-per-path increment
 * DUPLICATED load+add+store both paths (+6 words) - retail shares
 * addiu+lui+sh at the join. DIFF 217/274 @ 1108 (overshot).
 * DRAFT 15 (fb-SPLIT increment + memory-barrier m reload): THE ALLOC
 * REGION CLOSES BYTE-EXACT 0x800680AC..0x80068184 - found-slot path
 * carries its own lui/lhu with slot=k in the j delay, direct path its
 * own lui/lhu with move s2,s1, and the inc_join block [addiu v0,v0,1 /
 * lui at / sh] is SHARED - exactly retail. The empty asm memory clobber
 * kills the store-forwarding and the reload came out sign-extending lh
 * (lui v0/lh v0/nop). DIFF 192/270 @ 1080 - below draft10's 199 with
 * +104 bytes of retail shape materialized.
 * DRAFT 16 (= this file: + (short)mode test): the extend LANDED but
 * IN-PLACE (sll s5,s5,16 vs retail's temp sll v0,s5,16) - the same
 * in-place-vs-temp extend law as the slot err-path canonicalization;
 * the split-temp law (draft10 lever 2) applies: an explicit intermediate
 * local is the next lever. DIFF 193/271 @ 1084.
 *
 * REMAINING MIDDLE DIFFS (the draft16 map, all shape-level):
 *  - merge polarity: built beqz v0,far-err (fail branches far, body
 *    falls through) vs retail bnez v0,+3 (success branches past the
 *    inline 2-word err trampoline j .L80068394/delay a0=0); +2 words.
 *    BOTH textual forms (if>=goto-err and if<goto-ok;goto-err) collapse
 *    to beqz-far - candidate: a cc_post rule-17 merge-polarity transform
 *    (rule-16 class: invert + insert the trampoline).
 *  - register homes: slotx a0 (retail a3), hv t1 (retail a2 chain:
 *    merge-delay move a2,s3 -> addiu a2,a2,0x20 in the magic-beq delay
 *    -> s3 := a2 in the m-check bnez delay), m first-home t0 then
 *    reload v0 (retail v0 then reload v1), nprogs v1 (retail v0), spu
 *    s6 (retail a3; the built also FUSES spu=addr into the bnez delay
 *    addu v1,s6,s0), the 78704/787B0 stores sw s3/sw a3 (retail sw a2).
 *  - err-path extends go in-place (sll s2,s2,16) where retail uses a
 *    temp (sll v0,s2,16).
 *  - verdict-2 bne offset +2 (built target 0x80068134 vs retail
 *    0x8006813C) is downstream of the found-slot block length - closes
 *    with the region.
 * NEXT: the split-temp law on mode (explicit intermediate), then the
 * polarity rule-17 candidate or the reg-home nudges.
 * (draft4 note kept for the ladder: DRAFT 4 (cron-202611032028): draft3
 * with vabid/mode and the two signature params widened short->long.
 * DIFF 219/228 SIZE 912.)
 *
 * DRAFT 9 (cron-202611040743): the rule 16 COPY-DELAY variant - the
 * banked NEXT(1) from cron-202611040358. Source = draft7b verbatim
 * (form B: init-less $17 pin, the vabid copy as the else head - its
 * built beq verdict carries the copy in the branch delay with the
 * right adjacency) + `cc-post: rule16 jdelay li v0 -1`. The variant
 * (cc_post rule 16 class B): the verdict delay is `addu $rD,$rS,$zero`
 * with $rD call-SAVED, so the bne delay keeps the COPY verbatim and
 * the inserted j's delay takes the fail li FROM THE MARKER ARGS (the
 * remnant-ori1 arg precedent). Expected verdict window after the
 * transform: bne $2,$3,+3 (byte-exact since draft8) + addu s1,s0
 * (NEW - 0x800680A8) + j $L48 (still the 0xB0 middle delta) + li
 * v0,-1 (NEW - 0x800680B0) - ONLY the j word left wrong in the
 * verdict window; then the 139-word structural middle.
 *
 * RESULT (cron-202611040743): POSITIVE - the verdict window closes
 * except the j word. judge DIFF 207/236 SIZE 944 (draft7b baseline
 * 211/234 @ 936; +2 words = the inserted j+li pair) - first diff
 * ADVANCES 0x800680A4 -> 0x800680AC: the bne branch word (since
 * draft8) AND the copy delay 0x800680A8 (addu s1,s0) AND the j-delay
 * li 0x800680B0 (retail FFFF0224 == addiu $2,$zero,-1; the `li v0,-1`
 * marker spelling assembles to the same word) AND the continue join
 * 0x800680B4..0x800680BB are all byte-exact - the verdict window is
 * bne+copy+j+li with ONLY the j target wrong (built 0x0801A0F9 ->
 * 0x800683E4 vs retail 0x0801A120 -> 0x80068480, the 0x9C structural
 * middle delta; the inserted pair shifted the built tail +0x14).
 * Next diff region = 0x800680C0, the skew-dominated slt/bnez body
 * wave, then the 139-word structural middle (0x80068160..0x80068388).
 * TWO build-system lessons banked the hard way (caught live, first
 * judge run silently produced the draft7b image): the --rule16
 * rewrite dropped `RULE16_VERDICT = True` from main() AND the new
 * R16_JDELAY global needed a `global` declaration - both fixed; the
 * selftest now covers the CLI arg path (scripts repo-external), not
 * just _rule16_on_file directly. Loud-fail surfaces unchanged: bare
 * rule16 marker = class A; copy delay without jdelay args = exit 3;
 * unknown jdelay op = exit 3 (all verified).
 *
 * DRAFT 10 (cron-202611041013): the body wave 0x800680C0..0x80068160 -
 * the banked NEXT(1) from cron-202611040743. Source = draft7b + THREE
 * register-home pins and the addiu-at unit flag:
 *   (1) `register long vb asm("$3")` - retail keeps the (short)vabid
 *       extend RESULT live in v1 across both verdicts and the else
 *       block (bne v1,v0 at 0x800680E0; addu at,at,v1 x2 in the else).
 *       Pinning the SHORT copies first (addu v1,s0,0) and re-extends
 *       per use; pinning the LONG makes the extend land in v1 directly
 *       and every later use reads it - no remat.
 *   (2) `register long shifted asm("$2")` (v0) + the two-step
 *       `shifted = vabid << 16; vb = shifted >> 16;` - WITHOUT the pin
 *       gcc ties the sll temp to vb's home (in-place sll v1/sra v1,v1);
 *       WITH the v0 pin the extend SPLITS exactly as retail:
 *       sll v0,s0,16 / sra v1,v0,16 (0x800680BC/C0 byte-exact).
 *   (3) `register long k asm("$5")` (a1) - retail's scan-loop cursor
 *       lives in a1 with the k=0 init riding the verdict-2 bne DELAY
 *       (addu a1,zero,zero at 0x800680E4); unpinned, gcc homed k in v1
 *       (free on the vb==-1 path) and put the init in the loop head,
 *       shifting every later word one slot.
 *   (4) tools/maspsx_flags.txt `unit:SsVabOpenHeadWithMode
 *       --addiu-at on` - the D_8017E038[k]/D_8017E038[vb] walks take
 *       the aspsx < 2.30 4-insn at-split (lui/addiu/addu/lbu 0) like
 *       func_80069740's LIBSND class; addiu-at off folds %lo into the
 *       lbu immediate and the loop loses its addiu word.
 *
 * DRAFT 10 RESULT (cron-202611041013): POSITIVE - the wave closes through
 * the scan loop. judge DIFF 199/244 SIZE 976 (draft9 207/236 @ 944).
 * Byte-exact 0x800680B4..0x8006810F except the two j words: the split
 * extend (BC/C0), slti v0,v1,0x10 (C4), the bnez + li v0,-1 delay
 * (C8/CC), the setInTransfer(0) fail path (D0-DC), verdict-2 bne v1,v0
 * with the k-init delay (E0 branch word/E4), and the whole scan loop
 * E8..0x8006810F incl. the at-split addressing. Remaining wave diffs
 * are the SLOT-EXTEND family: retail keeps `slot` a SHORT (sll16
 * extends at every alloc_check join - delays 0x80068110/0x80068154,
 * the sequential sll at 0x80068184, sra a3,v0,16 at 0x80068188) while
 * the built keeps slot a raw long (slti v0,s2,0x10 directly); the
 * else-distance bne offset (E0 +0x14 vs +0x16) is downstream of it.
 * NEGATIVE x2 this window: slot as a SHORT pin costs an s7 SPILL at
 * this source shape (frame -0x438 -> -0x440, sw s7 appears; the
 * allocator pushes the vh+0x16 nv byte read out of the temps) - the
 * slot-short form must ride the 139-word middle re-shape, not the
 * wave; and the v1 SHORT pin (copy+per-use-extend) is the wrong
 * mechanism for a live-extended value.
 *
 * Experiment: the param imports re-authored as pinned-local inits -
 * the 7736C interleave bypass (NEGATIVE on every form; the full ladder
 * and its consequence live in draft3's RESULT block below).
 *
 * DRAFT 6 (cron-202611032143): this file carries `cc-post: rule15` -
 * the first live run of cc_post rule 15 prologue-param-interleave,
 * built from the negative result above: gcc keeps the batch prologue,
 * so the retail interleave is reproduced as a post-pass reorder
 * (pairs in import order, ra last, leftover saves after, the last
 * leftover save in the first call's delay slot).
 *
 * RESULT (POSITIVE - the whole prologue closes): judge DIFF 206/228
 * SIZE 912 (draft4-no-rule15 was 219/228; one iteration caught a
 * duplicate-save bug: rest[-1] was emitted both before AND after the
 * jal - the delay fill must consume it). Byte-exact 0x80068064 through
 * 0x800680A0: frame, all five pairs (s3/s0/s2/s6/s5), sw ra LAST,
 * sw s4, jal _spu_getInTransfer, sw s1 IN THE JAL DELAY, and the ori
 * v1,1 verdict constant. FIRST REMAINING DIFF = 0x800680A4: the
 * polarity-inverted verdict (built beq-to-return + addiu -1 delay vs
 * retail bne-to-continue + addu s1,s0 COPY delay) - the known body
 * wave (banked cron-202611030614), then the 139-word structural
 * middle. Loud-fail verified: --rule15 on a non-matching run exits 3.
 *
 * Retail prologue being chased (asm/g3org_jp/nonmatchings/func_80068064.s):
 *   addiu sp,-0x438 / sw s3,0x424 / addu s3,a0 (vh->s3 $19)
 *   sw s0,0x418 / addu s0,a1 (vabid->s0 $16)
 *   sw s2,0x420 / ori s2,0x10 (slot=0x10 init ->s2 $18)
 *   sw s6,0x430 / addu s6,a3 (addr->s6 $22)
 *   sw s5,0x42C / addu s5,a2 (mode->s5 $21) / sw ra LAST (+ s1 save in
 *   the getInTransfer jal delay; s1 = the vabid copy - body wave, not
 *   attempted here).
 *
 * METRIC: prologue words go interleaved? Everything else is draft2
 * verbatim (wave-1 scan/program-loop laws + wave-2 no-shared-err-free
 * law carried; the 139-word structural middle stays open either way).
 *
 * DRAFT 7 (cron-202611040243): the verdict-polarity wave.
 * (a) the $17 pin `vabid_s1` (banked NEXT(1) form: init at decl, the
 *     copy is scheduler-free to park late because its only use is the
 *     direct path's slot assign far downstream) + `slot = vabid_s1`;
 * (b) the first verdict re-authored in the else-goto shape
 *     (`if (getInTransfer() != 1) goto trans_ok; return -1;`) so gcc
 *     emits bne-to-continue instead of beq-to-return;
 * (c) the short extend made explicit: retail computes v1=(short)vabid
 *     (sll16/sra16) right after setInTransfer(1) and uses it for the
 *     0x10 range check, the second verdict AND the D_8017E038 index
 *     (banked recon: "indexes through $v1") - so the C reads a local
 *     `short vb` set from the pin;
 * (d) NEW BYTE FACT: the second verdict compares v1 against -1, not 1
 *     (the bnez delay li v0,-1 at 0x800680CC feeds bne v1,v0 at
 *     0x800680E0; scan path .L800680E8 == vabid==-1, direct
 *     .L8006813C) - draft6's `vabid == 1` was a decode slip the body
 *     wave was always going to catch.
 *
 * DRAFT 7 RESULT (form A, init-at-decl pin + !=1-goto verdict): judge
 * NOT EXACT, first diff stayed 0x800680A4 - the prologue REGRESSED (the
 * $17 init landed in the prologue import run as a sixth pair: sw
 * s1,0x41C adjacent to addu s1,s0, pushing sw s4 into the jal delay)
 * AND gcc RE-INVERTED the else-goto into beq v0,v1 -> far return block
 * with addiu -1 in the beq delay (jump.c goto-to-branch inversion).
 * Lesson: the polarity is decided by BLOCK LAYOUT (then = return
 * inline, else = continue target), not by the goto; and an
 * init-at-decl pin copy never leaves the prologue run.
 *
 * DRAFT 7b RESULT (form B, init-less pin + else-block copy): judge
 * DIFF 211/234 SIZE 936 (draft6 baseline 206/228 @ 912). POSITIVE
 * halves: the prologue is back to the draft6 EXACT shape (five pairs,
 * sw ra last, sw s4, sw s1 in the jal delay - the init-less pin's save
 * is a rule-15 leftover again) AND the copy rides the branch delay
 * (addu s1,s0) with the right delay-adjacency (the join head filled
 * it). NEGATIVE: the polarity is STILL beq v0,v1 -> $L48 (the merged
 * return tail, addiu -1 target-filled into the beq delay) - gcc 2.6.3
 * at -O1 does NOT invert to branch-around-the-return for this shape;
 * the else-goto was re-folded by jump.c (goto-to-next deleted, the
 * else became the plain join) before the branch choice. CONSEQUENCE:
 * the polarity lever is NOT source-shape reachable by if/else/goto
 * forms - the candidates left are (i) the copy inside the then-block
 * (dead-store gamble), (ii) cc_post rule 16 verdict-polarity (a pure
 * post-pass invert+reorder in the rule-15 class: [beq -> ret][delay]
 * [join] -> [bne -> join][delay: moved copy][j ret; delay: li]),
 * (iii) cc1-O2 for this unit (untested; the wave-2 note covered the
 * prologue at -O2, not the verdict). The vb/(short) extend + the
 * vabid==-1 second verdict (NEW byte fact this window) ride into
 * whichever form lands.
 */

extern unsigned char D_8017E038[];
extern unsigned short D_8017FB20;
extern short D_80178894;
extern unsigned long D_80178704[];
extern unsigned long D_8017876C[];
extern unsigned long D_801787B0[];
extern unsigned long D_8017FAE0[];
extern unsigned long D_8017FB6C[];
extern unsigned long D_8017FB24[];
extern long _spu_getInTransfer(void);
extern void _spu_setInTransfer(long mode);
extern long SpuMalloc(long size);

long SsVabOpenHeadWithMode(unsigned char *vh_p, long vabid_p, long mode_p, unsigned long addr_p)
{
    register unsigned char *vh = vh_p;               /* UNPINNED (draft12): retail REUSES s3 (vh -> base at the m-check delay) - the $19 pin holds vh's corpse all function and pushes base to s4 + nv to s7 (the spill); unpinned, gcc may run retail's choreography (import s3, copy to a0, s3 := base) */
    register long vabid asm("$16") = vabid_p;       /* s0: the vab id */
    register short slot asm("$18") = 0x10;           /* s2: the slot cursor - retail keeps it a SHORT and re-extends at every use (the join extends + the sll16/sra14 index folds); draft10's LONG built merges the check once and indexes raw */
    register unsigned long addr asm("$22") = addr_p; /* s6: caller SPU addr */
    register long mode asm("$21") = mode_p;         /* s5: placement mode */
    register long vabid_s1 asm("$17");              /* s1: the vabid copy */
    register long vb asm("$3");                      /* v1: the extended vabid - retail keeps the extend RESULT live in v1 across both verdicts and the else block; pin the LONG so no per-use re-extend */
    long arr[256];
    unsigned char *base;
    unsigned char *p;
    register unsigned char *hv asm("$4");            /* a0: retail's loop-read home (lhu 0x12(a0) / lbu 0x16(a0) / lw 0x4(a0)) - the built rode t1; dead before the malloc window so a0 is free for the SpuMalloc arg */
    long ap;
    long ap2;
    long end;
    register unsigned long tp asm("$6");             /* a2: retail's raw-load/increment home (lhu v1,0(a2) / addiu a2,a2,0x2 / the FB6C store sw a2) - the built rode a3 */
    unsigned long w0;
    register unsigned long spu asm("$7");           /* a3: retail's spu home (addu a3,v0,zero after SpuMalloc; addu a3,s6,zero in the bnez delay) - the built rode addr's dead $22 home; the pin also evicts tp from a3 (retail tp home a2) */
    long end_addr;
    register long shifted asm("$2");                 /* v0: the sll16 temp pin - keeps the extend SPLIT (sll v0,s0,16 / sra v1,v0,16) instead of in-place into vb.s pinned v1 */
    register long k asm("$5");                      /* a1: the scan-loop cursor - retail keeps k in a1 with the k=0 init riding the verdict-2 bne delay */
    long i;
    long idx;
    long total;
    long m;
    long fb;
    long nprogs;
    long nv;
    long n;
    long ver;
    long raw;
    long val;
    long size;

    if (_spu_getInTransfer() == 1) {
        return -1;
    } else {
        vabid_s1 = vabid;
        goto trans_ok;
    }
trans_ok:
    _spu_setInTransfer(1);
    shifted = vabid << 16;
    vb = shifted >> 16;                              /* the split-temp extend: retail sll v0,s0,16 / sra v1,v0,16 - the sll temp must not tie to vb's pinned home */
    if (vb >= 0x10) {
        _spu_setInTransfer(0);
        return -1;
    }
    if (vb == -1) {
        for (k = 0; k < 0x10; k++) {
            if (D_8017E038[k] == 0) {
                D_8017E038[k] = 1;
                fb = D_8017FB20;                 /* the fb-SPLIT increment (draft15): each alloc path LOADS D_8017FB20 into a temp and the ADD+STORE live at the inc_join label - retail's exact share (per-path lui/lhu, one addiu/lui/sh at the join). A full statement per path duplicates everything (draft14 NEGATIVE); one shared statement merges the loads too (draft13 NEGATIVE). */
                slot = k;
                goto inc_join;
            }
        }
        goto alloc_check;
    } else {
        if (D_8017E038[vb] != 0) {
            goto alloc_check;
        }
        D_8017E038[vb] = 1;
        fb = D_8017FB20;
        slot = vabid_s1;
    }
inc_join:
    D_8017FB20 = fb + 1;
alloc_check:
    if (slot < 0x10) {
        goto alloc_ok;
    }
    goto err;
alloc_ok:
    hv = vh;                                         /* the vh SPLIT (draft13): vh's only body uses start here; routing them through a fresh local ends vh's live range at the merge so s3 frees for base (retail: s3 := base at the m-check delay) and nv takes s4 instead of the s7 spill */
    D_8017876C[slot] = (unsigned long)hv;
    w0 = *(unsigned long *)hv;
    if ((w0 >> 8) != 0x564142) {
        D_8017E038[slot] = 0;
        goto err;
    }
    base = hv + 0x20;
    m = 0x40;
    if ((w0 & 0xFF) == 0x70 && *(long *)(hv + 4) >= 5) {
        m = 0x80;
    }
    D_80178894 = m;
    __asm__ __volatile__ ("" ::: "memory");          /* the m RELOAD barrier: retail re-reads D_80178894 with a sign-extending lh (lui v1/lh v1/nop/slt); gcc 2.6.3 store-forwards the plain read and the volatile read-back came out lhu+manual-extend - the empty asm memory clobber kills the forwarding and emits nothing */
    nprogs = *(unsigned short *)(hv + 0x12);
    if (D_80178894 < nprogs) {
        D_8017E038[slot] = 0;
        goto err;
    }
    D_80178704[slot] = (unsigned long)base;
    p = base;
    tp = (unsigned long)base + m * 0x10;
    idx = 0;
    for (k = 0; k < m; k++) {
        val = *p;
        *(unsigned long *)(p + 8) = idx;
        if (val) {
            idx++;
        }
        p += 0x10;
    }
    total = 0;
    D_801787B0[slot] = tp;
    nprogs = *(unsigned short *)(hv + 0x12);
    nv = *(unsigned char *)(hv + 0x16);
    tp += nprogs << 9;
    end = (long)(arr + nv);
    ap = (long)arr;
    for (; ap < (long)(arr + 256); ap += 4) {
        if (end >= ap) {
            ver = *(long *)(hv + 4);
            raw = *(unsigned short *)tp;
            size = ver < 5 ? raw << 2 : raw << 3;
            *(long *)ap = size;
            __asm__ __volatile__ ("" ::: "memory");   /* the in-loop reload barrier (draft18): retail keeps total += *ap as store->reload (sw/lw/nop/addu); the draft15 empty-asm clobber kills gcc 2.6.3's store-forwarding and emits nothing */
            total += *(long *)ap;
        }
        tp += 2;
    }
    D_8017FB6C[slot] = tp;
    shifted = mode << 16;                         /* the mode SLL16 via the split-temp law (draft17): the $2 pin forces the extend into the TEMP (retail sll v0,s5,16 / bnez v0) instead of in-place on s5; a plain long test has no extend */
    if (shifted != 0) {
        spu = addr;
    } else {
        spu = SpuMalloc(total);
        if (spu == -1) {
            D_8017E038[slot] = 0;
            goto err;
        }
    }
    end_addr = spu + total;
    total = 0;
    if (0x80000 < end_addr) {
        D_8017E038[slot] = 0;
        goto err;
    }
    D_8017FB24[slot] = spu;
    n = nv & 0xFF;
    if (n >= 0) {
        ap2 = (long)arr;
        i = 0;
        do {
            total += *(long *)ap2;
            if (i & 1) {
                *(unsigned short *)(base + (i / 2) * 0x10 + 0xE) = (spu + total) >> 3;
            } else {
                *(unsigned short *)(base + (i / 2) * 0x10 + 0xC) = (spu + total) >> 3;
            }
            i++;
            ap2 += 4;
        } while (n >= i);
    }
    D_8017FAE0[slot] = total;
    D_8017E038[slot] = 2;
    return slot;
err:
    _spu_setInTransfer(0);
    D_8017FB20 = D_8017FB20 - 1;
    return -1;
}
