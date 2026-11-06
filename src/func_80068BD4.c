/* cc-post: sdk-aspsx
 * cc-post: cc1-O1
 * cc-post: rule15
 * cc-post: rule17 $L19 jdelay addu 4 0
 * cc-post: lt0-scc 1
 *
 * DRAFT 66 LIVE (cron-202611060501, oracle UP): H.2 judged - **DIFF 4/274
 * SIZE-EXACT = THE NEW LIVE RECORD** (d65 17 -> d66 4; the ladder 143 ->
 * 146 -> 150 -> 17 -> 4 in two windows). SIZE-EXACT at the row (1096),
 * offline 214/274 aligned, ZERO word_diff insert/delete blocks - every
 * remaining diff is content-only. THE 4-WORD RESIDUAL = one region, the
 * second loop's head: (i) [221] the n_neg materialization emits srl
 * $2,$3,31 where retail runs slti $2,$3,0 - a d66-v2 REGRESSION (d65/d62
 * emitted slti aligned; the trigger is NOT the i=0 order - the v5 swap
 * measured no-flip - the suspect = the $3-web pressure from the new
 * mask/magic pins changing gcc's store_flag pick) and (ii) [231][232]
 * [234] the signed-div-by-2 expansion's temp home $2 vs retail's $3
 * (the v3 ihalf pin measured NEGATIVE - it restructured the whole loop,
 * 273 built / 203 aligned, the expansion sank below the arms; needs a
 * subtler spelling - e.g. a CSE-blocker between the arms - parked).
 * Gates: staging reverted, ratchets 948/538 = tree, suite OK, witness
 * 8/8. NEXT: the twins take the d66 shape; the 4-word region hunts the
 * store_flag trigger.
 *
 * DRAFT 66 (cron-202611060501, oracle UP): THIS FILE = draft65 + THE THREE
 * 17-WORD-RESIDUAL REGIONS. (a) THE MAGIC SPLIT: retail [84] lui $v1,0x56
 * and [87] ori $v1,0x4142 are ONE constant SPLIT around the a0 copy [85]
 * and the w0 load [86] (the ori fills the load delay); d65's single local
 * emitted the pair adjacent at [86]/[87] (the lui 2 late). Two pinned
 * locals on the sequential $3 web split them from C: magic_hi = 0x560000
 * right after the 7876C store (the lui $3,0x56 = [84]), magic = magic_hi
 * | 0x4142 between the load and w0hi (the ori $3,$3,0x4142 = [87], the
 * load-delay filler). (b) THE MASK TEMP: retail [97] andi $3,$5,0xff /
 * [98] ori $2,0x70 / [99] bne $3,$2 - the mask temp's home IS $3 (m's
 * dead pin) and the andi precedes the ori; d65 emitted [ori][andi $5,$5]
 * (the temp in-place on w0's home, the constant first). register long
 * mask asm("$3") = w0 & 0xFF BEFORE shifted = 0x70 fixes home + order.
 * (c) THE FAIL-TAIL HEAD: retail's shared fail entry @0x80068378 = [a0:=0]
 * [sll16][sra16][clear] - the head force FIRST; d65's tail-merged block
 * = [sll16][sra16][a0:=0][clear] (the decl's extend emitted before the
 * force). Both fail sites reorder to hv = 0 BEFORE the slot_x decl (the
 * GNU-C mixed-decl form) so the tail-merge keeps the retail order.
 * MEASURED (live): 17 -> 8 - the ONLY residual class left = the $2-vs-$3
 * TEMP-HOME residue: the err-tail FB20 RMW temp (retail lui $3/lhu $3/
 * addiu $3,-1/sh $3; the built picked $2) and the second loop's signed-
 * div-by-2 temp (retail runs the whole (i/2) expansion in v1 = the n
 * dead web inside the loop; the built picked $2). d66 v3 pins BOTH to
 * $3 (fbtmp, ihalf - the C89 decl-only + assignment form).
 *
 * DRAFT 65 LIVE (cron-202611060346, oracle UP): H.2 judged - **DIFF 17/274
 * SIZE-EXACT = THE NEW LIVE RECORD** (d62 143 -> d65 17, eight times
 * better; d61 146, the d53 parked best 150). All four delay slots
 * retail-exact: [76] the verdict-delay copy addu $a2,$s3,$zero, [83] sw
 * $a2, [90] the magic beq delay addiu $a2,$a2,0x20, [115] the m-check
 * bne delay addu $s3,$a2,$zero. SIZE-EXACT at the row (1096) via the two
 * funding kills (the magic local kills the load-delay nop; the i=0 raise
 * moves the init into the n-check bnez delay). Gates: verify g3org_jp
 * GREEN whole-image, ratchets 948/538 = tree, suite OK, staging reverted.
 * THE 17-WORD RESIDUAL = THREE REGIONS: (a) [84..86] the magic lui one
 * word late (copy,lw,lui vs retail lui,copy,lw - moving the def earlier
 * costs the load-delay filler back); (b) [97..99] the mask check needs
 * the andi dst $3 + the andi-before-ori order + the beq polarity;
 * (c) @0x8378 the n-check bnez delay = a THIRD err-entry head force
 * (a0:=0) in retail where the built parked the floated slot4 sll16 pair.
 *
 * DRAFT 65 (cron-202611060346, oracle UP): THIS FILE = draft64 + THE FULL
 * A2-CHAIN TRIPLE (the d64 header design, landed as one arc). The three
 * retail words all ride DELAY SLOTS: [76] addu $a2,$s3,$zero in the
 * vb-check bnez delay, [90] addiu $a2,$a2,0x20 in the magic beq delay,
 * [115] addu $s3,$a2,$zero in the m-check bne delay. V1 LESSON (measured:
 * 276 built / 192 aligned): a plain hv6 = hv gets copy-FORWARDED into the
 * store (sw $4 not sw $6) and the copy sinks past it into the magic beq
 * delay - gcc 2.6.3 propagates plain assignments into uses regardless of
 * the dest pin. V2 LESSON (measured: 276 built / 200 ALIGNED, +8 over the
 * d62 record; the store sw $6, the magic beq delay addiu $6,$6,32 and the
 * m-check tp = s3 + tpose all LANDED): an EMPTY asm with an "=r" output
 * is ASSUMED-WRITTEN, never moved - no addu materializes and the pin
 * holds garbage (only the arg-regs' leftover values made it accidentally
 * benign; the vb-check delay went NOP). V3 MECHANISM = THE ADDU AS THE
 * ASM TEMPLATE: __asm__("addu %0,%1,$zero" : "=r"(dst) : "r"(src)) - the
 * copy IS the statement, non-volatile (the banked dbr-skips-volatile-asms
 * law), opaque in both directions (no forward/back propagation through
 * it), emits EXACTLY addu $6,$19,$zero / addu $4,$19,$zero and schedules
 * like a normal insn (the d33 back-walk law fills the delay above it).
 * Also v3: w0 pinned $5 (retail home a1 - lw $a1,0($a0) / srl v0,a1,8 /
 * andi v1,a1,0xff all read it; k's dead pin per the disjoint-web law) and
 * base = base6 RAISED above the m-check if (the v2 build's m-check delay
 * took a DUPLICATED sll16 - the barrier blocked the move so the dbr
 * copied - the from-above position makes the copy the nearest independent
 * set and the d33 law applies).
 *
 * DRAFT 64 (cron-202611060231, oracle UP): THIS FILE = draft62 + THE BASE-HOME STEERING (the H.4 item 2 a2-chain lever, first sub-lever). MEASURED NEGATIVE (offline, knob-alive anchor d38 1092 first): built 276 words (+2) / aligned 192/274 = ZERO gain over d62 (192/274 at 274) / linked 1100. The $6 pin perturbed the check WINDOW wholesale: word_diff shows insert built[76] retail[76:84] (the 7876C store block scattered) + replace built[79:97] retail[97:98] (the 18-word blob where retail has the ONE andi word) - the pin's eviction ripple re-materialized the at-build webs. LESSON BANKED: the a2-chain is a THREE-word UNIT - retail's [76] addu $a2,$s3,$zero (the hv copy, ALSO the 7876C store's operand web) + [90] addiu $a2,$a2,0x20 (base = the copy +0x20) + [115] addu $s3,$a2,$zero (the m-check bne DELAY re-home, the 111-word tail's +1 shift source) - steering [115] alone (this draft) shifts the window without re-aligning anything; d65 must land the TRIPLE as one unit: hv6 pinned $6 = hv BEFORE the 7876C store (the store reads the a2 home, retail [83] sw $a2), base6 = hv6 + 0x20 reusing $6 (sequential webs, retail [90]), base = base6 post-m-check (retail [115]), funded by killing the built-only words (the word_diff delete entries: built[116]/[226]/[275] class - the shift re-sync word + two more) - net +2 built needs the -2 built-only kills in the SAME draft or the H.5 SIZE gate breaks.
 * DRAFT 64 DESIGN NOTES (superseded by the measurement above, kept for the arc): base6 pinned $6 (tp's dead pin - tp's web starts at the tp def AFTER the store; w0's a2 web dies at the mask compare - the disjoint-web law) carries the early web through the 78704 store, and `base = base6` sits right after the m-check if as the delay-fill candidate (both fail paths never read it - semantically delay-safe); base stays UNPINNED for the late web (gcc's natural s3 pick per the draft12 s3 reuse).
 * DRAFT 62 LIVE (cron-202611060116, oracle UP): H.2 judged - SIZE-EXACT (built = row 1096) / DIFF 143/274 = THE LIVE RECORD (d61 146, the d53 parked best 150; the offline -G0 192 overcounted DIFF by the two-sided gap -49). The polarity swap's +3 aligned carries live (143 vs 146). First diff 0x80068188, IDENTICAL map to d61 (the swap region is downstream and aligned): 0x188 the div-chain sra first-dst ($2 vs $3), 0x18C the slti base reg ($a1 vs $a3), 0x194 built lui $v1,0x0056 vs retail addu $a2,$s3,$zero = THE A2-CHAIN COPY SITE - the d64 lever (H.4 item 2: merge delay -> a2=s3, a0 copy -> post-join straight-line, vh reads -> a0), authorable from this run's build/judge dump per the no-blind law.
 * DRAFT 62 (cron-202611052343, oracle DOWN): THIS FILE = draft61 + THE I&1 BRANCH POLARITY SWAP. The d61 region read found the loop's i&1 test INVERTED vs retail: the built emits beq $2,$0,$L48 (branch-on-EVEN to the 0xC block, the 0xE fall-through with j-over) where retail runs bnez $v0,.L80068424 (branch-on-ODD to the 0xE block, the 0xC fall-through with the sh riding the j delay) - the d56 polarity class, source-reachable this time: swapping the if/else arms (even arm first) flips gcc's branch choice. Retail's layout = even-inline: source if ((i & 1) == 0) {0xC} else {0xE}. MEASURED (-G0): 274 built words / 192/274 aligned / linked 1096 = THE ROW SIZE - the swap bought +3 aligned (d61 189) with the size held; THE NEW OFFLINE RECORD at the row size (the old parked best d53 = 179 at 1096).
 * DRAFT 61 (cron-202611052343, oracle DOWN): THIS FILE = draft60 + THE N-HOME/CURSOR-HOME PINS + THE LOOP-BOUND COPY. The d60 region read (build/judge .mas.s vs retail 0x800683D4-0x8006844C) found the transposition BEHIND the middle-op: retail runs n home = v1 (andi $v1,$s4,0xff), the loop cursor i home = a1, ap2 home = a0, and copies the loop bound n -> a2 (addu $a2,$v1,$zero) because v1 is the division scratch INSIDE the loop; the built kept n home = a2 (tp's dead pin), cursor i = a0 (hv's dead pin), ap2 = a1 (k's dead pin) - the ap2/cursor TRANSPOSITION - and emitted no copy (n's home already stable). d61 pins n to $3 (v1, m's dead pin - the disjoint-web law, same class as the nine $2 webs) and i to $5 (a1, k's dead pin), and routes the loop bound through an UNPINNED n2 = n so the copy must materialize (the draft30 m2 law: a pinned home cannot coalesce with the source) while n's own web dies at the copy - freeing $3 for the loop's division scratch EXACTLY as retail reuses v1. Predicted region: andi $v1 retail-exact, the copy word materializes (+1 word = 274 = ROW SIZE), ap2/cursor un-transpose, the loop tail slt reads (a2-cursor a1) retail-exact; the middle op (srl vs retail slti) and the delay-fill pick (i-init vs the floated sll) stay measured-open.
 * DRAFT 57 (cron-202611052113, oracle DOWN): THIS FILE = draft53 MINUS THE
 * RULE16 MARKER (the cron-202611051843 next-shape resolved: the sltu-check
 * edge form was never a gcc shape at all - it was OUR cc_post rule16
 * spurious fire). Ground truth: the early verdict's built region
 * [bne $2,$3,$L2][addu $17,$16 delay][j $L53][li -1 delay] carries NO
 * $Lr16c label = rule16 never touched it - the d53 else+goto trans_ok
 * spelling already makes gcc emit the retail polarity NATIVELY (retail
 * 0x800680A4: bne $v0,$v1 / addu $s1,$s0 / j .L80068480 / addiu $v0,-1 -
 * structurally identical). The rule16 marker stayed in the header, so the
 * prepass scanned on and its FIRST beq+class-B-delay match was THE SLTU
 * CHECK: gcc's native [beq $2,$0 -> $L43 (OK edge, retail polarity)]
 * [delay total=0][fail body falls through] got inverted into
 * [bne -> $Lr16c][j $L43][li -1] = the 2-word skip pair the cron-
 * 202611051843 geometry blamed on gcc's block layout. REMOVING the marker
 * kills the spurious fire: the check region returns to gcc's native beq
 * form = retail's [beqz -> FB24][delay total=0][fail body fall-through]
 * with NO skip pair (−2 words), and the d56 source-spelling experiment
 * (the same inversion attempted in C, probes/..._draft56.c) measured the
 * identical d53 region - the inversion was cc_post's, not gcc's, both
 * times. d56's comment block carries the full experiment record.
 * THE HEAD POSITION ([sll][sra][a0=0] vs retail [a0=0][sll][sra]) is a
 * separate lever (the scheduler first-insn priority) and the gp-class
 * words (D_80180404/D_80178980 bare vs retail lui/$at) are the OTHER
 * open lever (cc1 -G8 vs retail's materialized form) - both queued.
 *
 * DRAFT 53 (cron-202611051458, oracle DOWN): THIS FILE = draft52 + THE
 * HEAD FORCE ON THE $4 PIN (the d48 lever re-derived for this landscape):
 * d48's plain-long err_arg took a NEW callee-saved (s7, the allocator law
 * - arg regs are never reused for cross-block pseudos); the d38 landscape
 * already PINS hv to $4 (the a0 read-home, dead before the sltu check),
 * so the force rides the EXISTING pin instead of a fresh pseudo: every
 * fail path assigns hv = 0 on its dead edge and the tail call reads hv.
 * The assignments are the delay-fill/block-head candidates: the three
 * plain goto entries get addu $4,$0,$zero into their jump delays (retail
 * entries' delays), the two $2-tail fail blocks get it BETWEEN the decl
 * (emits nothing, coalesced) and the clear = the MERGED BLOCK HEAD
 * (retail addu $a0,$zero,$zero @0x0314), and the jal delay empties to
 * nop (retail @0x0334). The tail-merge keeps working: both $2 tails now
 * carry the identical [hv=0][extend][clear] prefix. MEASURE: the pin
 * costs nothing if hv's live web (def @alloc_ok, last use the pre-loop
 * nv read) and the fail-edge defs never collide with the SpuMalloc arg
 * or the param copy.
 *
 * DRAFT 52 (cron-202611051458, oracle DOWN): THIS FILE = draft38 + THE
 * ERR-LABEL MID-FUNCTION RESTRUCTURE PORTED OFF THE CHAIN LANDSCAPE (the
 * cron-202611051343 next-shape: the d46 restructure rebased onto the
 * PRE-CHAIN d38 base, 266 w / 175/274 / linked 1092, where $4 is the hv
 * read-home's natural home and the fail blocks are pressure-free - the
 * d41-chain landscape's s1/s7 thefts and the episode web own exactly the
 * homes the err-region levers need, so the port DROPS the whole a2/base
 * chain: no b0, no explicit copy, no slot4a pin, no raw-slot unmerge).
 * The move is the d46 recipe verbatim: the err body leaves the function
 * END and re-sits right after the 0x80000-check fail block (before the
 * FB24 store), guarded by `if (0)`. Retail's layout: [the merged m-check/
 * sltu fail block: a0=0 head + E038 clear][the err TAIL: jal setInTransfer
 * / FB20 dec / j epilogue with li -1 in the delay][the FB24 path
 * continues] - the tail is MID-FUNCTION, the m-check fail FALLS INTO it,
 * the other entries carry a0=0 in their jump delays, and the sltu-false
 * edge branches over the whole thing (the beqz at 0x80068370). On the
 * chain landscape the port bought 170 -> 171 and exposed two residuals
 * (the 0x0314 a0=0 head, the skip-branch pair) that the register pressure
 * blocked; this landscape should hand the fail blocks to the port
 * pressure-free. MEASURE before any conclusion: if the port holds 175
 * the region is live for the head force ($4-pinned asm-def variant) and
 * the skip fusion (the d47 nesting without the duplication risk).
 *
 * DRAFT 38 (cron-202611050613, same window): THIS FILE = draft37 + THE
 * END= OPERAND-ORDER FLIP (end = ap + nv * 4 -> end = nv * 4 + ap): the
 * built's addu emitted (a1 + v0) - ap's home as rs, the scaled-nv temp
 * as rt (00a23821) - while retail's is (v0 + a1), the temp FIRST
 * (00453821 at 0x800682C4, the draft23-open-3 banked retail form `addu
 * $a3,$v0,$a1`). gcc 2.6.3 preserves the SOURCE addition order in the
 * RTL operand order for commutative PLUS, so swapping the source
 * operands swaps the encoding. MEASURED 171/274 at 252 built words, NET
 * +1, SIZE-neutral: the end= word flips retail-exact AND the whole
 * entry-test group (end= / slt v0,a3,a1 / bnez v0,+11 = 1440000b / nop)
 * now aligns INSIDE the equal blocks - the replace built[138:139]
 * hunk disappears entirely. The post-loop positional set (the cron-
 * 202611050458 next-queue item) is now CLOSED end to end: total=0 /
 * ap / sll16 / sra14 / BOUND / store / reads / tp+= / end= / slt / bne /
 * nop all retail-ordered, the only remaining store-group delta the
 * separate at-chain class lever (retail's six 4-word lui/addiu-lo/
 * addu/sw symbolic sw stores vs the built's 3-word gas embed, -1 word
 * per site, banked for the next window).
 *
 * DRAFT 37 (cron-202611050613, same window): THIS FILE = draft36 + THE
 * 787B0 SPLIT-TEMP EXTEND + THE BOUND REMAT ORDER (two coupled source
 * facts, one lever): retail's post-exit order is total=0 / ap / sll16 /
 * sra14 / BOUND / 787B0-chain / sw - the extend pair (sll v0,s2,16 /
 * sra v0,v0,14 at 0x80068294/98) is scheduled BEFORE the bound def
 * (addiu t0,sp,0x410 at 0x8006829C), which sits BETWEEN the extend and
 * the 787B0 lui. The built emitted the extend as part of the STORE's
 * address computation (list position = the store), so no source position
 * of `bound = ap + 1024;` could land the def inside the store group:
 * BEFORE the store (pos a) and AFTER the store (pos b) both hoisted the
 * independent $8 def ABOVE the extend pair (measured identical machine:
 * total/ap/BOUND/sll16/sra14/sw), and after the reads it sank to the
 * entry test (the d36 form). THE FIX follows the banked split-temp law
 * (draft17/25 class): the extend moves OUT of the store into its own
 * PINNED statement - register long slot4 asm("$2") (the NINTH disjoint
 * web on the $2 pin, all earlier webs dead at this def); slot4 = (long)
 * slot << 16 >> 14 forces sll $2,$18,16 / sra $2,$2,14 as its own list
 * position BEFORE the bound def; the store reads it back through the
 * pin (sw $6,D_801788A0($2), the same embed form). Source order ap= /
 * slot4= / bound= / store => machine list order ap / extend / BOUND /
 * store = RETAIL'S ORDER. The bound word itself is unchanged
 * (1004a827, byte-identical to retail). NOTE the remaining store-group
 * delta is the SEPARATE at-chain class lever (retail's six symbolic sw
 * stores 7876C/78704/787B0/FB6C/FB24/FAE0 all use the 4-word
 * lui/addiu-lo/addu/sw form - the built's gas embed is 3 words, -1 per
 * site), banked for the next window.
 *
 * DRAFT 36 (cron-202611050613, oracle DOWN - eighth consecutive outage
 * window): THIS FILE = draft35 + THE HEAD-LOOP DO-WHILE RE-SHAPE (the
 * draft23 pre-entry end<ap re-shape, the last named post-loop positional
 * set item): the head loop's for-form `for (; ap < bound; ap += 4)`
 * makes gcc emit a TOP GUARD (addu $8,$sp,1040 / slt $2,$5,$8 / beq
 * $2,$0,<exit> / sll $2,$18,16 dead delay - the d35 banked delay-fill
 * side effect) before the end<ap test, but RETAIL HAS NO TOP GUARD -
 * retail's entry falls straight from end= (addu a3,v0,a1 at 0x800682C4)
 * into .L800682C8 slt v0,a3,a1 / bnez v0,.L800682FC / NOP (the end<ap
 * skip test with a nop delay), and the ap<bound test rides ONLY the
 * back-edge (.L800682FC: addiu a1,4 / slt v0,a1,t0 / bnez v0 / addiu
 * a2,2 delay). Re-shaped source: `do { if (end >= ap) { body } tp += 2;
 * ap += 4; } while (ap < bound);` - semantically identical for this
 * caller (ap = sp+0x10, bound = ap+0x400, both frame-fixed: ap < bound
 * holds at entry, the top guard was dead runtime code), and retail's
 * binary IS the source-shape truth. Expected wins: the top-guard 3 words
 * (slt/beq/dead-sll) die, the entry test (slt $2,$7,$5 = v0,a3,a1 /
 * bne / nop) aligns retail-exact, and the back-edge distance (retail
 * bnez offset -16) re-derives. The bound's def (addu $8,$sp,1040,
 * byte-identical to retail's 1004a827) keeps its current late position
 * in THIS draft - the bound remat HOIST to retail's 0x8006829C slot
 * (between sra14 and the 787B0 lui) is the NEXT lever (draft37), kept
 * separate for lever isolation.
 *
 * DRAFT 35 (cron-202611050458, oracle DOWN - seventh consecutive outage
 * window): THIS FILE = draft34 + THE TOTAL=0 SINK-BARRIER (an empty
 * volatile asm with a memory clobber placed immediately after the FIRST
 * total = 0) - retail's first total=0 sits at the loop EXIT (addu
 * s0,zero,zero at 0x8006828C, before the ap word) but gcc floats the
 * independent set ~40 words down to the backfill pre-entry (its only
 * use is the second loop's accumulator); the barrier sits AFTER the def
 * so the set cannot sink past it (the banked m-reload precedent - the
 * empty asm emits nothing). MEASURED 169/274, NET +1, at 262 objdump
 * words = +1 REAL word (the post-exit total=0; retail HAS the word -
 * the second source total=0 already rode the end_addr beqz delay
 * retail-exact per draft25 open 3, so both of retail's s0-zeroings now
 * have built counterparts). LIVE prediction 276 = +2 over the row (the
 * d30 copy + this word) - the SIZE verdict stays LIVE-ONLY (H.5), the
 * a2-chain base-def fund still the identified lever; the conservative
 * SIZE-neutral form is draft34 (168/274, 261 w) if the gate refuses.
 * NOTE the delay-fill side effect: with total=0 held at the exit, the
 * pre-entry beq's delay got refilled with a DEAD sll duplicate of the
 * 787B0 store prep (retail's delay there is a nop; same slot count, no
 * SIZE delta) - the draft23 pre-entry re-shape (the end<ap bnez form)
 * refills it when it lands. Outage ladder: 156 (d28) -> 161 (d30) ->
 * 164 (d31) -> 166 (d32) -> 167 (d33) -> 168 (d34) -> 169 (d35), +13.
 * H.2 judge order 21 -> 28 -> 29 -> 30 -> 31 -> 32 -> 33 -> 34 -> 35.
 *
 * DRAFT 34 (cron-202611050458, same window): THIS FILE = draft33 + THE
 * AP REORDER (ap = (long)arr; moved from after the reads+tp+= to
 * immediately after total = 0, before the D_801788A0 store) - retail's
 * post-exit order is total=0 (0x8006828C) THEN ap (addiu a1,sp,0x10 at
 * 0x80068290) THEN the 787B0 store prep (sll16/sra14/lui/addiu/addu/sw
 * at 0x80068294..AC); the d33 form had ap after the reads+tp+= and gcc
 * kept it there. The ap word itself was ALREADY retail-exact (0x27A50010
 * via the gas addu-with-imm law, see the d33 opcode-class note) - only
 * its POSITION was wrong. MEASURED 168/274 at 261 objdump words, NET
 * +1, SIZE-neutral (261 = the d30-d33 count). The remaining post-loop
 * positional wrong after this: the bound remat (retail addiu t0,sp,0x410
 * sits BETWEEN the sra14 and the 787B0 lui at 0x8006829C; the built
 * keeps it with the end group) and the total=0 float (fixed by d35's
 * barrier).
 *
 * DRAFT 33 (cron-202611050458, same window): THIS FILE = draft32 + THE
 * PRE-BRANCH REORDER (idx = 0 moved from the first statement inside the
 * if to immediately before it) - the k=0/idx=0 delay-fill item. Retail's
 * k=0 is the straight-line insn BEFORE the blez (addu a1,zero,zero at
 * 0x80068254) and the DELAY carries idx=0 (addu s0,zero,zero at
 * 0x8006825C); the d32 form had idx=0 first INSIDE the if and the
 * delay-fill scheduler took k=0 (the immediately-preceding independent
 * set) for the slot, leaving idx=0 post-branch: the built's blez offset
 * word was 0x1860000D vs retail 0x1860000C and the slot word was a1=0
 * vs retail s0=0. The reorder is semantically identical: the delay slot
 * executes unconditionally and idx dies at loop exit. MEASURED 167/274
 * at 261 objdump words (254 on the w_diff counter), NET +1,
 * SIZE-neutral: the ENTIRE 16-word loop window retail[122..137]
 * (0x8006824C..0x80068288) is now ONE binary equal block - k=0
 * pre-branch, the blez offset word 0x1860000C retail-exact, idx=0 in
 * the delay, the copy, p=base and the full body (lbu/nop/beqz/sw/
 * idx++/k++/slt/bnez/p+=16) all byte-identical.
 *
 * THE OPCODE-CLASS ITEM CLOSES AS A FALSE ITEM (same window, zero
 * words at stake): the "built addu $16,$16,1 / addu $5,$5,1 /
 * addu $3,$3,16 vs retail addiu x3" residual was a MNEMONIC-TEXT
 * artifact, never a binary diff. gcc 2.6.3 emits the addu-with-
 * immediate TEXT form pre-maspsx (checked in .gcc.s), maspsx passes it
 * through, and gas (mipsel-linux-gnu-as 2.31.1) assembles
 * "addu reg,reg,imm" as the I-type addiu ENCODING - the built .o words
 * at all three sites are 0x26100001 / 0x24A50001 / 0x24630010,
 * byte-identical to retail's addiu words (the retail dump prints
 * "addiu" because that IS the encoding). word_diff.py (gas+objdump
 * based) had already counted all three sites equal. Same conversion
 * covers the backfill-loop "addu $5,$5,4 / addu $6,$6,2" text forms
 * (the .o shows 0x24A50004 / 0x24C60002). The flag-or-shape question
 * is moot - no flag, no shape change needed; banked so no future
 * window re-opens it.
 *
 * DRAFT 32 (cron-202611050228, same window): THIS FILE = draft31 + THE
 * OFFSET-TEMP PIN (register long tpose asm("$2"); tpose = m * 0x10; tp =
 * base + tpose) - retail's tp offset rides v0 (sll v0,v1,4 / addu
 * a2,s3,v0); the built's free temp rode tp's own home $6 (sll $6,$3,4 /
 * addu $6,$19,$6). The pin rides the $2 web freed by the m-check reads'
 * death (the eighth disjoint web on the $2 pin) and MEASURED NET +2:
 * 166/274 at 254 built words (sll dst v0 + addu src2 v0 flip retail-exact;
 * the addu src1 $19 vs retail s3 stays judge-gated a2-chain territory).
 * C89 note: the register decl must sit in the declaration block, not
 * mid-block (gcc 2.6.3 parse error). H.2 judge order 21 -> 28 -> 29 ->
 * 30 -> 31 -> 32.
 *
 * DRAFT 31 (cron-202611050228, same window): THIS FILE = draft30 + THE IDX-HOME PIN (register long idx asm("$16")) - retail idx = s0 in the first loop (addu s0,zero,zero in the blez delay, sw s0,8(v1), addiu s0,s0,1) and total re-rides s0 after (0x8006828C); the built's free idx rode $8 (bound's dead pin). The pin rides vabid's dead $16 web (the disjoint-web law, the $2 four-web precedent) and MEASURED NET +3: 164/274 at 254 built words; total's free web kept $16 (no eviction - the idx/bound precedent held). The addu-vs-addiu increment opcodes stay wrong (a separate opcode-class item). H.2 judge order 21 -> 28 -> 29 -> 30 -> 31.
 *
 * DRAFT 30 (cron-202611050228, oracle DOWN - sixth consecutive outage
 * window): THIS FILE = draft29 + THE LOOP-BOUND COPY FORM (the
 * cron-202611042243 residual, draft23-bucket territory). Retail's first
 * loop re-derives its bound through a COPY so the m reload's v1 home
 * frees for p: after the tp def and the k=0 init, the blez v1 guard
 * (delay idx=0), then addu a3,v1,zero (the m -> a3 bound COPY at
 * 0x80068260) and addu v1,s3,zero (p = base into the FREED v1 at
 * 0x80068264); the loop compare rides the COPY (slt v0,a1,a3), NOT m.
 * The d28 m pin held v1 through the loop compare and evicted p to $7
 * (the recorded d28 cost: d26's addu v1,s3,zero p-home was retail-exact
 * and d28 lost it). The form here: guard stays on m (retail blez reads
 * v1), the compare moves to a COPY (m2), and p is PINNED to the freed
 * home (register, asm("$3")) - the m/p/vb three-web partition of the
 * hard reg (the shifted/w0hi/slot_x four-web precedent on $2). MEASURED:
 * see the commit and the H.1 ledger row.
 *
 * DRAFT 29 (cron-202611042243, same window as 28): THIS FILE = draft28
 * + ONE pin - the w0>>8 temp through $2 (register unsigned long w0hi
 * asm("$2") = w0 >> 8; if (w0hi != 0x564142)). MEASURED: the aligned-
 * match metric STAYS 156/274 (the wins absorb into difflib's
 * alignment - the count-masking class, same lesson as the VA-to-VA
 * skew) but the CODE is strictly closer: FOUR magic-check words flip
 * retail-exact - srl dst $3 -> $2 (retail srl $v0,$a1,8), the
 * constant lui/ori $2 -> $3 (retail v1), the beq pair $3,$2 -> $2,$3
 * (retail beq $v0,$v1); the diff vs d28 is EXACTLY those four words,
 * nothing else moved (verified). The srl SRC and the mask andi src
 * stay $6 (w0's home) - the w0 -> $5 pin was AUTHORED, MEASURED AND
 * REJECTED the same window: aligned-match 155/274 (NET -1) - the pin
 * EVICTS the early split-temp webs from $5 (the sra/slt/sll
 * alloc-merge temps and the E038 index shuffle $5 <-> $6, five words
 * lost) against four magic-check words gained; gcc 2.6.3 treats an
 * explicit register variable as a WHOLE-FUNCTION reservation for the
 * OTHER pseudos' packing choices, so a pin on a reg with early
 * free-web traffic costs more than its own web wins - banked for the
 * twins (pin $5-class regs ONLY when the early traffic is already
 * pinned away). Judge-deferred with the ladder (H.2 order 21 -> 28
 * -> 29; a surprise at 28 re-opens 26's region, at 29 re-opens 28's).
 *
 * DRAFT 28 (cron-202611042243): THE PARKED NEXT FORM AUTHORED - the
 * full-window condition-chain re-shape through `shifted` ($2 pin) with
 * explicit gotos, exactly as parked in the draft27 header. THE RETAIL
 * MAP (banked runbook H.3 + re-derived from the row dump this window):
 * the window 0x800681E8..0x80068214 is a FIVE-web sequential chain
 * through v0 - ori v0,0x70 (the compare constant) / bne v1,v0 with the
 * ori v0,0x40 in the DELAY (the fail-path flag, dead on the
 * fall-through where the lw overwrites v0) / lw v0,4(a0) (the ver
 * read) / nop / slti v0,v0,5 / bnez v0 with the ori v0,0x40 in the
 * DELAY again / ori v0,0x80 (the success fork) / then the join store
 * sh v0,D_80178980($at). The mask is v1 (andi v1,a1,0xff). Retail's
 * gcc filled BOTH branch delays from the fail paths' single 0x40
 * materialization (the merged 1-insn target block duplicated into the
 * delays with the branches retargeted past it). THE RE-SHAPE: (a) the
 * d26 source shape `m = 0x40; if ((w0 & 0xFF) == 0x70 && *(long
 * *)(hv + 4) >= 5) m = 0x80; D_80178980 = m;` becomes the explicit
 * chain shifted = 0x70; if ((w0 & 0xFF) != shifted) goto m40;
 * shifted = *(long *)(hv + 4); if (shifted < 5) goto m40; shifted =
 * 0x80; goto m_store; m40: shifted = 0x40; m_store: D_80178980 =
 * shifted; - every def rides the $2 pin (the draft17/23/24 disjoint
 * web law, now six webs), the two fail gotos tail-merge into the
 * one-insn m40 block, and reorg's delay-fill/retarget must produce
 * the double ori v0,0x40 delays. (b) THE M RE-HOME: m's later uses
 * (tp = base + m*0x10, the k < m loop) ride the m-check RELOAD in
 * retail (lui v1/lh v1 at 0x8006821C/20 feeds slt AND sll v0,v1,4 at
 * 0x8006824C AND blez v1 at 0x80068258 - the def-side register web
 * DIES at the sh), so m = D_80178980 is loaded fresh after the
 * barrier (CSE-merged with the m-check compare's read - one load)
 * and the d26 def-side pseudo ($8, which also served the loop) is
 * GONE. The d26 built state this attacks (measured this window,
 * word_diff aligned-match 153/274 reproduced): the window residual =
 * 4 wrong words - bne delay ori $8,0x40 (src $8 vs retail $2), bnez
 * delay nop (vs ori $2,0x40), ori $8,0x80 and sh $8 (src $8 vs $2);
 * the m-check compare slt $3,$3,$2 / bne $3,$0 (the banked open
 * slt-dst item, NOT this lever); the first loop entry beq $8,$0 +
 * slt $2,$5,$8 (vs retail blez v1 + the addu a3,v1,zero copy + slt
 * v0,a1,a3 - the reload-riding form). Judge-deferred (oracle down,
 * links 404/404 re-probed this window ~14:5x UTC). MEASURED (v2, two
 * steering iterations this window): word_diff aligned-match 156/274 vs
 * d26's 153/274 - NET +3, the same 253 built words (SIZE class and the
 * 0x448 row extent unchanged; offline deltas scale-exact per H.1).
 * THE MEASURED FORM (v2 = the chain + the m re-home PINNED $3 + the
 * base def moved post-window):
 *  (1) THE 9-WORD CHAIN CORE IS RETAIL-EXACT: bne $3,$2,+7 / delay
 *      ori $2,$zero,0x40 / lw $2,4($4) / nop / slti $2,$2,5 / bne
 *      $2,$0,+2 / delay ori $2,$zero,0x40 / ori $2,$zero,0x80 / sh
 *      $2,D_80178980 - the m40 fold FIRED for BOTH branches (the
 *      merged 1-insn fail block duplicated into both delays and
 *      retargeted past), the fork falls through (no j), the
 *      standalone block is gone. d26 had 4 wrong words here (the two
 *      delay fills + ori $8,0x80 + sh $8); v2 has ZERO.
 *  (2) THE M-CHECK COMPARE IS RETAIL-EXACT: lh $3,D_80178980 / slt
 *      $2,$3,$2 / bne $2,$0 - the BANKED OPEN SLT-DST ITEM (the
 *      "slt/branch regs land $3 as gcc's first-operand habit" open
 *      judge item from cron-202611041628) CLOSES OFFLINE: the m
 *      re-home makes the compare's dst v0 and the branch src v0, both
 *      retail words. d26 had 2 wrong here; v2 has ZERO.
 *  (3) THE TP SLL SRC: sll $6,$3,4 (m from v1 = retail's reload home;
 *      d26 rode $8). The blez entry: blez $3 (retail's opcode AND
 *      src; d26 had beq $8,$0).
 *  (4) THE COUPLING (the draft27 header's warning, now measured): the
 *      chain's FIRST def (shifted = 0x70, ori $2,0x70) is floated by
 *      the scheduler INTO THE MAGIC-BEQ DELAY SLOT - the slot retail
 *      fills with the a2-chain's addiu $a2,$a2,0x20 (the judge-gated
 *      draft25-open-4 lever). The window therefore stands at 11 built
 *      words vs retail's 12 with the 0x70 upstream: the 9-word core
 *      is exact, the andi src ($6 vs retail $5 = w0's home, the
 *      upstream open class) and the magic-beq delay (contested slot)
 *      stay wrong - the FULL 12/12 window closure is COUPLED to the
 *      a2-chain landing, exactly as parked. The d26 magic-beq delay
 *      word was ALSO wrong (the base def) - the slot count is
 *      NEUTRAL, the chain core is the win.
 *  (5) THE V1->V2 STEERING FACTS (banked for the twins): v1 (base
 *      pre-window, m unpinned) - the base def stole the bne's delay
 *      slot from the m40 fold (the fold lost to the candidate fill),
 *      the fork needed an explicit j over the standalone fail block,
 *      the reload landed $8 (gcc reused the bound pin's reg). v2 =
 *      base def moved POST-WINDOW (its first use is the 78704 store;
 *      out of the delay-candidate pool) + m PINNED $3 (register long
 *      m asm("$3") - $3 is free post-vb, the window mask still takes
 *      $3 where m is dead, the draft17/23/24 disjoint-web law) -> both
 *      folds fire, the reload lands $3, the compare closes.
 *  (6) THE COST (recorded, not hidden): the loop's p := base lost its
 *      v1 home (d26 addu $3,$19,$zero = retail-exact; v2 addu
 *      $7,$19,$zero) - m's pin holds $3 through the loop compare, so
 *      p cannot take v1 without the retail loop-bound COPY form (the
 *      a2-chain-class choreography); idx moved $7 -> $8 (wrong ->
 *      wrong). The loop region is the draft23-bucket territory with
 *      its own lever set - NET still +3.
 * Judge-deferred with the ladder (oracle down; the H.2 sequence now
 * runs 21 -> 22 -> 23 -> 24 -> 25 -> 26 -> 28, 28 = the new best
 * parked form; a judge surprise at 26 re-opens 25's region first, a
 * surprise at 28 re-opens 26's).
 *
 * DRAFT 26 (cron-202611042128): THIS FILE = draft25 with end_addr
 * REVERTED to UNSIGNED - the cron-202611042128 offline audit of the
 * committed retail row dump (asm/g3org_jp/nonmatchings/func_80068064.s,
 * no oracle needed) found draft22's end_addr conversion is a
 * REGRESSION: the draft22 header cited "retail slt at 0x80068300" for
 * the 0x80000 check, but 0x80068300 is the LOOP BACK-EDGE compare
 * (slt $v0,$a1,$t0 = ap < bound - correctly slt, the re-shape's real
 * win). The ACTUAL 0x80000 SPU-bound check is at 0x8006836C and retail
 * is SLTU there: lui $v0,0x0008 / sltu $v0,$v0,$v1 / beqz
 * $v0,.L800683BC / delay addu $s0,$zero,$zero (0x80068368..74). The
 * loop address holders (ap/ap2/end) STAY signed long (retail slt at
 * 0x800682C8 pre-check/guard and 0x80068300 back-edge stand); only
 * end_addr reverts. Offline delta vs draft25: EXACTLY the one-word
 * slt->sltu flip at the check (verified below, nothing else moved).
 *
 * THE AUDIT'S OTHER RESOLUTIONS (all from the row dump, retail-side
 * facts - the live judge reads remain for the BUILT-form confirms):
 *  (a) draft21 open 1 RESOLVED: retail's rule17 trampoline jdelay =
 *      addu $a0,$zero,$zero (0x8006819C) - the marker's `addu 4 0`
 *      form, NOT li; no re-spell needed.
 *  (b) draft23 open 1 RESOLVED: retail nv home = s4 (lbu $s4,0x16($a0)
 *      at 0x800682B4); the built's $20 IS s4 - already retail-exact.
 *  (c) draft23 open 3 RESOLVED retail-side: retail end home = a3
 *      (addu $a3,$v0,$a1 at 0x800682C4, end = (nv<<2) + ap); the built
 *      draft23 lands $7 = a3 (the offline build confirms).
 *  (d) draft24 open 1 CONFIRMED: retail m-check pair = lhu $v0,
 *      0x12($a0) / lh $v1,D_80178980 / nop / slt $v0,$v1,$v0
 *      (0x80068218..28) - exactly the draft24 expected pair
 *      (lhu $2 / lh $3 / slt $2,$3,$2).
 *  (e) draft25 open 3 RESOLVED: retail's end_addr-check beqz delay =
 *      addu $s0,$zero,$zero (0x80068374); the built already emits
 *      addu $16,$0,$zero = the same word.
 *  (f) draft25 open 1 SHARPENED: retail's m-check bnez (0x8006822C)
 *      targets .L80068378 whose FIRST word is addu $a0,$zero,$zero
 *      (the a0=0 pre-zero) BEFORE the tail's sll $v0,$s2,16/sra
 *      $v0,$v0,16 (the tail entry is 3 words: a0, sll, sra); the
 *      built's merged tail starts at the sll (its a0=0 rides the
 *      jdelays) - when the a2-chain lever lands, the built target
 *      returns to tail+0 = the sll.
 *  (g) THE A2/BASE CHAIN FULLY RETAIL-CONFIRMED (draft25 open 4's
 *      map): (1) addu $a2,$s3,$zero @ 0x80068194 = the ALLOC-merge
 *      bnez delay (the rule17 site), (2) addiu $a2,$a2,0x20 @
 *      0x800681CC = the magic-beq delay, (3) addu $s3,$a2,$zero @
 *      0x80068230 = the m-check bnez delay, (4) sw $a2 through the
 *      at-split at 0x80068248 (D_801787F4) / 0x800682AC (D_801788A0) /
 *      0x80068324 (D_80180450). AND THE A0 RE-MATERIALIZATION SLOT IS
 *      FOUND: retail addu $a0,$s3,$zero @ 0x800681B8 - POST-JOIN
 *      STRAIGHT-LINE (after the D_8017885C store, before the magic lw
 *      $a1,0($a0)), NOT a delay slot. The built's a0 copy rides the
 *      merge delay (addu $4,$19,$zero) and its vh reads go through
 *      $19/s3 (lw $6,0($19)) where retail reads through a0 - the
 *      chain lever's steering target is now concrete: merge delay ->
 *      a2=s3, a0 copy -> post-join, vh reads -> a0.
 *
 * DRAFT 25 (cron-202611042013): THIS FILE = draft24 + the LAST
 * in-place err-path extend flipped to the TEMP form - the SHARED fail
 * tail (the m-check fail and the end_addr overflow fail merge into one
 * D_8017E120[slot]=0;goto err tail; built tail at 0x2ec = retail
 * 0x8006834C).
 * MEASURED FORM LADDER (all three built offline this window):
 *  (1) plain intermediate `long slot_x = slot;` -> ZERO delta: gcc
 *      coalesces the copy back to the in-place sll s2,s2/sra s2,s2.
 *  (2) single-site $2 pin (end_addr only) -> the tails DIVERGE (the
 *      $2-form vs the in-place form), gcc's tail-merge splits: the
 *      m-check branch INVERTED to beq (polarity regression vs the
 *      banked retail bnez) + the tail DUPLICATED (+5 words) - REJECTED.
 *  (3) BOTH sites pinned $2 (THIS FILE) -> the tails re-merge; the
 *      built tail machine stream becomes
 *        sll $2,$18,16 / sra $2,$2,16 / lui at / addu at,at,$2 / sb
 *      = sll v0,s2,16 / sra v0,v0,16 / lui at / addu at,at,v0 / sb
 *      EXACTLY the draft16 map class fact ("err-path extends go
 *      in-place (sll s2,s2,16) where retail uses a temp (sll v0,s2,16)").
 *      The gcc label $L53 sits between the tail's sll and sra (labels
 *      are free - no word impact): the end_addr path FALLS THROUGH the
 *      tail's own sll; the m-check bne targets $L53 (the sra) and gets
 *      $2 = slot<<16 from ITS DELAY SLOT - the pre-existing hoisted
 *      OK-path index-extend sll $2,$18,16 (the sll16 half of the
 *      sll16/sra14 D_801787F4-index fold), which executes on the taken
 *      path too. BOTH paths semantically correct; .text 0x410 = 1040
 *      UNCHANGED; word positions unchanged.
 *      REGION DIFF MATH vs the banked retail form: draft24 wrong =
 *      [delay: OK-sll vs the a2-chain move s3,a2][bne src $3 vs $2]
 *      [tail sll s2-dst][tail sra s2-dst][tail addu $18-src] = 5
 *      words; draft25 wrong = [delay: same][bne word: src $3 + the
 *      target offset +1 (built lands at the sra, retail at the sll)]
 *      = 2 words. NET -3 DIFF, the err-path extend class CLOSED (the
 *      only remaining sll s2,s2 in the built is GONE - grep-verified).
 * Judge-deferred (oracle down; links re-probed 404/404 at ~12:2x UTC
 * this window; the 0859Z set is 3.5 days old). ALSO RESOLVED OFFLINE
 * (draft24 open item 1): the m reload landed $3/v1 UNPINNED (the
 * draft24 build emits lh $3, D_80178980) - no pin needed, matching the
 * banked retail v1 home.
 * OPEN JUDGE ITEMS: (1) the bne target offset +1 - built lands at the
 * sra (tail+1) using the delay-sll; retail's banked delay = the
 * a2-chain move s3,a2 (NOT an sll) so retail's target should be the
 * sll (tail+0) - when the a2-chain lever lands the m-check site's pin
 * must be re-read (the delay-sll disappears, the target returns to
 * tail+0, and the tail keeps the full 5-word temp form). (2) the bne
 * src $3 vs retail $2 - the draft24 slt-dst open item, unchanged here.
 * (3) the retail end_addr-check delay (built move s0,zero) is
 * unbanked - one judge diff read. (4) the a2/base chain (the draft16
 * map's move a2,s3 / addiu a2,a2,0x20 / move s3,a2 choreography) stays
 * JUDGE-GATED: the a0 re-materialization question (retail must copy
 * vh back to a0 after the setInTransfer calls clobber it, but no
 * banked slot holds that copy) blocks a semantically-safe offline
 * authoring - analysis banked here so the judge window reads the map
 * directly.
 *
 * DRAFT 24 (cron-202611041628): THIS FILE = draft23 + the m-check
 * nprogs FIRST-READ home flip - the banked cron-202611041128
 * register-homes fact "nprogs v1 (retail v0)" for the OTHER read (the
 * draft23 lever (a) covered only the pre-loop read). The first read
 * rides the $2 pin too: `shifted = *(unsigned short *)(hv + 0x12); if
 * (D_80178980 < shifted)` - the plain nprogs local is GONE (both reads
 * now banked v0 retail-side). Expected pair against the built
 * lhu $3,18($4) / lh $2,D_80178980 / nop / slt $2,$2,$3:
 *   lhu $2,18($4) / lh $3,D_80178980 / nop / slt $2,$3,$2
 * - the m RELOAD home should fall to $3/v1 (the banked retail home,
 * "retail v0 then reload v1") and the slt operand order swaps to
 * retail's word. FOUR disjoint webs now share the $2 pin (the vb
 * extend, this read, the pre-loop read, the mode test) - all dead-at
 * each next def, the draft17/23 reuse precedent. Judge-deferred (the
 * oracle is down; links re-probed 404/404 at ~10:07 UTC this window).
 * OPEN JUDGE ITEMS: (1) whether the m reload lands $3 unpinned or
 * needs the pin (one judge diff read); (2) the 0x70/ver window
 * upstream of this read is NOT fully banked (built li $8/li t0 forms
 * vs retail's m first-home v0 claim) - if the judge shows the ver/
 * slti window moving, the cascade is the next lever, NOT a regression
 * of this one; (3) the rule17 anchor $L19 sits upstream of this edit
 * (the alloc merge) - cc_post loud-fails if the label numbering moved.
 *
 * DRAFT 23 (cron-202611041628): THIS FILE = draft22 + the pre-loop
 * dst-reg/sharing form (the banked NEXT(4) from cron-202611041243, the
 * 29-word 0x80068258..0x800682C8 bucket) - THREE sub-levers, all in the
 * pre-backfill window, nothing else touched:
 *   (a) the nprogs LOAD DST: retail reads the pre-loop nprogs with dst
 *       v0 (banked draft20 fact: "lhu v1 vs retail lhu v0 at the
 *       nprogs/nv pair"); the built rode $3. The read now rides the
 *       $2 pin's third disjoint web (the draft17 mode-test reuse
 *       precedent): `shifted = *(unsigned short *)(hv + 0x12);`
 *       feeding `tp += shifted << 9;` - the plain nprogs local keeps
 *       only the FIRST read (the m-check, upstream, untouched).
 *   (b) the end/ap DE-SHARE: the built computes BOTH through one sp+16
 *       temp (addu $2,$sp,16 / addu $8,$2,$3 / addu $5,$2,$zero);
 *       retail materializes ap DIRECTLY (addiu a1,sp,0x10). Reorder ap
 *       first and derive end from it: `ap = (long)arr; end = ap +
 *       nv * 4;` - with a single consumer the shared temp dies and the
 *       ap materialization should collapse to one direct addiu.
 *   (c) the t0 BOUND: retail materializes the loop bound ONCE pre-loop
 *       (addiu t0,sp,0x410 at 0x8006829C - draft17 byte fact (b)); the
 *       built rematerializes per edge (entry test in $2 + loop-carried
 *       $7/a3) with the homes EXACTLY SWAPPED vs retail (built end t0 /
 *       bound a3; retail end a3 / bound t0). An explicit `bound` local
 *       pinned `asm("$8")` forces the single t0 home; end (unpinned)
 *       should fall to a3 (a1 = ap, a2 = tp, t0 = bound taken).
 * EXPECTED built pre-loop after the three levers (word forms):
 *   lhu $2,18($4) / lbu $20,22($4) / sll $2,$2,9 / addu $6,$6,$2 /
 *   addu $5,$sp,16 / sll $2,$20,2 / addu $7,$5,$2 / addu $8,$sp,1040 /
 *   slt $2,$5,$8 / beq $2,$0,<exit> / addu $16,$0,$zero (delay) ...
 *   slt $2,$7,$5 / bne $2,$0,<skip> / nop ... slt $2,$5,$8 /
 *   bne $2,$0,<head> / addu $6,$6,2 (delay).
 * JUDGE-DEFERRED (oracle down). OPEN JUDGE ITEMS: (1) the nv load dst -
 * the built lbu $20 home s4 is UNBANKED retail-side (the banked v0 fact
 * covers the lhu only; if retail's nv home differs, one more pin); (2)
 * the bound remat COUNT - the pin forces the HOME, not the count: a
 * second addiu $8,$sp,1040 at the entry test = +1 word (SIZE 1101 vs
 * the 1098 draft21 expectation, the accounting shifts again); (3) end's
 * a3 home is gcc's free choice - if it lands in a temp the compare regs
 * stay wrong (one judge diff read decides the next pin). The rule17
 * anchor ($L19) and the rule16 verdict are UPSTREAM of every edit -
 * cc_post loud-fails if either moved.
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
 * slot-extend/D_80180450-store/mode-test/malloc-arg window closed
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
 * around the D_801788A0 store. NEW BYTE FACTS BANKED: (a) retail's two
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
 * right adjacency) + the rule16 marker (jdelay payload li v0 -1). The variant
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
 *       --addiu-at on` - the D_8017E120[k]/D_8017E120[vb] walks take
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
 *     0x10 range check, the second verdict AND the D_8017E120 index
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
 * DRAFT 60 (cron-202611052228; the committing message mislabels it 2213): THIS FILE = draft57 + THE N-CHECK COMPARISON
 * MATERIALIZATION (the -2 deficit's third retail-only word, the source-spelling
 * lever). n = nv & 0xFF; if (n >= 0) folded to [andi $a2][bltz $a2] (2 words);
 * retail = [andi $v1][slti $v0,$v1,0][bnez $v0] (3 words, the comparison as a
 * VALUE). Spelling: n_neg = (n < 0); if (n_neg == 0) {...}. MEASURED (the -G0
 * instrument, rebaseline_h1 law): 273 built words / 181/274 / linked 1092 =
 * row - 1 WORD (d57 272/181/1088) at ZERO alignment cost, frame intact
 * (addiu sp,sp,-1080). The materialization lever is VALIDATED. The built's
 * materialization idiom = gcc's bit-extract form [srl $v0,$a2,0x1f][bnez $v0]
 * vs retail's [slti $v0,$v1,0x0][bnez $v0] - same 3-word shape, same polarity,
 * the middle op differs; the srl->slti refinement is the follow-up
 * micro-lever (the a2-chain pair of the -2 stays judge-gated per H.4).
 */

extern unsigned char D_8017E120[];
extern unsigned short D_80180404;
extern short D_80178980;
extern unsigned long D_801787F4[];
extern unsigned long D_8017885C[];
extern unsigned long D_801788A0[];
extern unsigned long D_801803C4[];
extern unsigned long D_80180450[];
extern unsigned long D_80180408[];
extern long _spu_getInTransfer(void);
extern void _spu_setInTransfer(long mode);
extern long SpuMalloc(long size);

long func_80068BD4(unsigned char *vh_p, long vabid_p, long mode_p, unsigned long addr_p)
{
    register unsigned char *vh = vh_p;               /* UNPINNED (draft12): retail REUSES s3 (vh -> base at the m-check delay) - the $19 pin holds vh's corpse all function and pushes base to s4 + nv to s7 (the spill); unpinned, gcc may run retail's choreography (import s3, copy to a0, s3 := base) */
    register long vabid asm("$16") = vabid_p;       /* s0: the vab id */
    register short slot asm("$18") = 0x10;           /* s2: the slot cursor - retail keeps it a SHORT and re-extends at every use (the join extends + the sll16/sra14 index folds); draft10's LONG built merges the check once and indexes raw */
    register unsigned long addr asm("$22") = addr_p; /* s6: caller SPU addr */
    register long mode asm("$21") = mode_p;         /* s5: placement mode */
    register long vabid_s1 asm("$17");              /* s1: the vabid copy */
    register long vb asm("$3");                      /* v1: the extended vabid - retail keeps the extend RESULT live in v1 across both verdicts and the else block; pin the LONG so no per-use re-extend */
    long arr[256];
    unsigned char *base;                             /* the base LATE web (draft64): re-def'd from base6 AFTER the m-check (the s3 := a2 delay copy) - unpinned, gcc's natural s3 pick = retail's late home (the draft12 s3 reuse, now at retail's position) */
    register unsigned char *base6 asm("$6");         /* the base EARLY-WEB PIN (draft64): retail base home = a2 from the def to the 78704 store - $6 = tp's dead pin (tp's web starts at the tp def after the store; w0's a2 web dies at the mask compare) per the disjoint-web law */
    unsigned char *p;                                /* the LOOP-BOUND COPY FORM (draft30): retail p home = v1 (addu v1,s3,zero at 0x80064) - v1 frees when the m web dies at the guard+copy. UNPINNED (measured): a p pin (register asm("$3")) deletes p's stack home and SHRINKS the frame 1080 -> 1072, flipping the subu word and all eight save-slot offsets (-8 each) - the prologue is retail-exact at 0x438 and must not move; the disjoint-web free-packing precedent (idx rides $8 past bound's dead web, ext-slot rides $5 before k's web) lets a free p take the vacated v1 */
    register unsigned char *hv asm("$4");            /* a0: retail's loop-read home (lhu 0x12(a0) / lbu 0x16(a0) / lw 0x4(a0)) - the built rode t1; dead before the malloc window so a0 is free for the SpuMalloc arg */
    register unsigned char *hv6 asm("$6");           /* the A2-CHAIN COPY PIN (draft65): retail [76] addu $a2,$s3,$zero rides the alloc-verdict bnez DELAY and [83] sw reads it - $6 = tp's dead pin (tp's web starts at the tp def after the 78704 store); the copy's web dies at base6's def (the chain), freeing $6 for tp exactly as retail does */
    long ap;
    long ap2;
    long end;
    register long bound asm("$8");                   /* t0: retail's loop-bound home - ONE addiu t0,sp,0x410 pre-loop (0x8006829C); the built rematerialized per edge with the end/bound homes swapped (draft23 lever c). No call in the web so the caller-saved temp is safe */
    register unsigned long tp asm("$6");             /* a2: retail's raw-load/increment home (lhu v1,0(a2) / addiu a2,a2,0x2 / the FB6C store sw a2) - the built rode a3 */
    register unsigned long w0 asm("$5");             /* the W0 HOME PIN (draft65 v3): retail w0 home = a1 (lw $a1,0($a0) / srl v0,a1,8 / andi v1,a1,0xff) - $5 = k's dead pin (k's web ended at the first loop; i's web starts at the second loop), the same reg i rides, per the disjoint-web law */
    register unsigned long w0hi asm("$2");           /* the >>8 temp PIN (draft29): retail srl $v0,$a1,8 - dst v0; $2 free between the vb web and the chain web, the seventh disjoint web on the pin */
    register unsigned long spu asm("$7");           /* a3: retail's spu home (addu a3,v0,zero after SpuMalloc; addu a3,s6,zero in the bnez delay) - the built rode addr's dead $22 home; the pin also evicts tp from a3 (retail tp home a2) */
    unsigned long end_addr;   /* retail 0x80000 check is SLTU (0x8006836C) - draft22's signed conversion was a mis-cite regression, reverted cron-202611042128 */
    register long shifted asm("$2");                 /* v0: the sll16 temp pin - keeps the extend SPLIT (sll v0,s0,16 / sra v1,v0,16) instead of in-place into vb.s pinned v1 */
    register long k asm("$5");                      /* a1: the scan-loop cursor - retail keeps k in a1 with the k=0 init riding the verdict-2 bne delay */
    register long i asm("$5");                       /* the i-HOME PIN (draft61): retail's second-loop cursor home = a1 (andi $v0,$a1,1 / addiu $a1,$a1,1) - the built transposed i to a0 (hv's dead pin) and gave k's $5 to ap2; i rides k's dead web per the disjoint-web law (k's web ended at the first loop) */
    register long idx asm("$16");                    /* the idx-home PIN (draft31): retail idx home = s0 (addu s0,zero,zero at 0x8006825C in the blez delay; the built rode $8 = bound's dead pin) - $16 = vabid's dead pin, the disjoint-web law (measured: total's free web KEEPS $16 past idx's death - the idx/bound precedent held, no eviction); MEASURED 164/274 = NET +3 over d30 (sw $16,8($3) and the idx=0/idx++ dsts flip retail-exact; the addu-vs-addiu increment opcodes stay wrong) */
    long total;
    register long tpose asm("$2");                   /* the offset-temp PIN (draft32): retail sll v0,v1,4 / addu a2,s3,v0 - the tp offset temp rides the $2 pin (the m-check reads' web is dead at this def, the eighth disjoint web); unpinned, the temp rode tp's own home $6 */
    register long slot4 asm("$2");                   /* the 787B0 SPLIT-TEMP EXTEND (draft37): the store's index scale (sll $2,$18,16 / sra $2,$2,14) as its OWN statement so the bound def (source-next) schedules between it and the store = retail's order; the NINTH disjoint web on the $2 pin */
    register long m asm("$3");                      /* v1: the m RE-HOME PIN (draft28) - m rides the m-check RELOAD in retail (lui v1/lh v1 feeds slt AND sll v0,v1,4 AND blez v1); $3 is free here (vb's web died at the else-block D_8017E120[vb] use) and the window MASK (w0 & 0xFF) still takes $3 where m is dead - the draft17/23/24 disjoint-web law */
    register long mask asm("$3");
    register long fbtmp asm("$3");                   /* the err-tail FB20 RMW TEMP (draft66 v3): retail = lui $3,0x8018 / lhu $3,%lo / addiu $3,-1 / sh $3 - the address AND the data ride $3; the built's free temp picked $2. n's dead web by then (n died at the n2 copy) */
    long ihalf;                                      /* D69: the ihalf pin DROPPED (redundant per d67e - the quotient lands $3 unpinned). (draft66 v3, MEASURED NEGATIVE: the pin restructured the whole loop - 273 built / 203 aligned, the div expansion sank below the arms and the sign-fix sequence changed shape; the d61 region read needs the fresh dump first - PARKED, revert to the d65 free-temp form) */
    long magic;                                      /* D69: the magic pin DROPPED (redundant per d67c - judged identical 4/274 unpinned): retail's magic home = v1 ($3) through the magic check - the ori writes it in-place; m's web starts at the m-check reload, n's at the andi after FB24 - disjoint webs on the pin */
    long magic_hi;                                   /* D69: the magic_hi pin DROPPED (redundant per d67b): retail [84] lui $v1,0x56 rides between the store and the a0 copy - magic_hi's web dies at the ori (sequential webs on $3) */
    long fb;
    long nv;
    register long n asm("$3");                       /* the n-HOME PIN (draft61): retail n home = v1 (andi $v1,$s4,0xff / slti $v0,$v1,0 reads it) - the built kept n in a2 (tp's dead pin) which killed the retail loop-bound copy; $3 = m's dead pin, the disjoint-web law (m's web ended at the m-check) */
    register long sgn asm("$3");                     /* D70B: the HOISTED SIGN-TERM WEB pinned $3 (the d70b lever, see draft70b) */
    long n2;                                         /* the LOOP-BOUND COPY (draft61): retail copies n -> a2 (addu $a2,$v1,$zero) because v1 is the division scratch inside the loop - the unpinned n2 rides the copy while the pinned n web dies at it, freeing $3 for the division scratch exactly as retail reuses v1 */
    long n_neg;                                      /* the n-check COMPARISON MATERIALIZATION (draft60): retail = [andi $v1][slti $v0,$v1,0][bnez $v0] (3 words, the comparison as a VALUE) where the d57 spelling if (n >= 0) folded to [andi][bltz] (2 words) - the folded form is the -2 deficit's third retail-only word's partner; a materialized temp forces gcc's slti+branch form (the middle-end emits the slt def, the branch reads it) */
    register long m2 asm("$7");                      /* the loop-bound COPY PIN (draft30): retail addu a3,v1,zero at 0x80068260 (m -> a3) and the compare rides the COPY (slt v0,a1,a3) - an unpinned m2 was COALESCED back into m (the copy died, the compare re-read v1, p stayed evicted); a register variable on a DIFFERENT hard reg cannot coalesce, so the copy must materialize. $7 = spu's pin (web dead here - the disjoint-web law; end's free web rides $7 past m2's death like idx rides bound's) */
    long ver;
    long raw;
    long val;
    long size;
    long frame_pad;                                  /* the frame-pad (draft30): the do-while rewrite eliminated reload's 8-byte reservation (vars 1032 -> 1024, frame 1080 -> 1072) and the shrink flips the subu word + all eight save offsets retail-wrong; the dead address-take re-reserves the slot at parse time with no emitted code (measured: the only build delta is the .file line + label renumbering) */

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
            if (D_8017E120[k] == 0) {
                D_8017E120[k] = 1;
                fb = D_80180404;                 /* the fb-SPLIT increment (draft15): each alloc path LOADS D_80180404 into a temp and the ADD+STORE live at the inc_join label - retail's exact share (per-path lui/lhu, one addiu/lui/sh at the join). A full statement per path duplicates everything (draft14 NEGATIVE); one shared statement merges the loads too (draft13 NEGATIVE). */
                slot = k;
                goto inc_join;
            }
        }
        goto alloc_check;
    } else {
        if (D_8017E120[vb] != 0) {
            goto alloc_check;
        }
        D_8017E120[vb] = 1;
        fb = D_80180404;
        slot = vabid_s1;
    }
inc_join:
    D_80180404 = fb + 1;
alloc_check:
    hv6 = vh;                                        /* the A2-CHAIN COPY (draft65 v5): retail [76] addu $a2,$s3,$zero rides the ALLOC-VERDICT bnez DELAY - PLAIN form because gcc's dbr refuses asm insns as delay fills (the v4 NOP lesson) while plain copies fill (the v1 magic-beq evidence, the d33 k=0 law); propagation risk known from v1 (the store read the source's home) - measured here to see if the single-copy (no hv-chain) form escapes it the way the draft30 m2 pin did */
    if (slot < 0x10) {
        goto alloc_ok;
    }
    goto err;                                        /* NO HEAD FORCE HERE (draft53): the alloc verdict is rule17's anchor (the cc-post trampoline inserts the entry's a0=0) - a source assignment between the verdict and the goto dissolves the beq-far pattern and rule17 exits 3 */
alloc_ok:
    D_8017885C[slot] = (unsigned long)hv6;           /* the store reads the A2 home (draft65): retail [83] sw $a2,0($at) - was hv ($4), the d64 scatter's root cause; hv6 is opaque so the operand must be $6 */
    __asm__ ("lui %0,0x56" : "=r"(magic_hi));           /* the LUI HALF, OPAQUE (draft66 v2): retail [84] lui $v1,0x56 - the plain assignment magic_hi = 0x560000 got CONSTANT-FOLDED with the ori half back into one 0x564142 materialization (gcc sees both halves at compile time); the asm template is opaque so the fold is impossible and the lui sits at its statement position between the store block and the a0 copy */
    __asm__ ("addu %0,%1,$zero" : "=r"(hv) : "r"(vh));   /* the A0 COPY (draft65 v3): retail [85] addu $a0,$s3,$zero straight-line between the store and the w0 load; the template form forces the $4 materialization and every hv use reads $4 (retail [86] lw $a1,0($a0)) */
    w0 = *(unsigned long *)hv;
    magic = magic_hi | 0x4142;                       /* the ORI HALF (draft66): retail [87] ori $v1,0x4142 = the w0 load's DELAY FILLER (independent of the load) - the pair splits around the a0 copy [85] and the load [86] exactly as retail */
    w0hi = w0 >> 8;                                  /* the magic-check temp rides $2 (draft29) - retail srl v0,a1,8 */
    base6 = hv6 + 0x20;                              /* the base CHAIN def, RAISED (draft65 v2): reads the COPY ($6 = a2), retail [90] addiu $a2,$a2,0x20 rides the MAGIC BEQ delay - placed above the check so the dbr's back-walk finds it past the needed srl/ori (the v1 m_store position landed straight-line) */
    if (w0hi != magic) {                             /* the compare reads the LOCAL (draft65 v6) - the d28 constant-through-a-variable law */
        D_8017E120[slot] = 0;
        hv = 0;                                      /* THE HEAD FORCE (draft53): rides the goto's delay (retail magic-fail entry) */
        goto err;
    }
    mask = w0 & 0xFF;                                /* the MASK TEMP ASSIGNMENT (draft66): retail [97] andi $3,$5,0xff - the def PRECEDES shifted = 0x70 so the andi precedes the ori (retail's order; d65 emitted ori-then-andi with the temp in-place on w0's home $5) */
    shifted = 0x70;                                  /* the chain form (draft28): the compare constant rides the $2 pin - retail ori v0,0x70 */
    if (mask != shifted) {
        goto m40;
    }
    shifted = *(long *)(hv + 4);                     /* the ver read rides $2 - retail lw v0,4(a0) */
    if (shifted < 5) {
        goto m40;
    }
    shifted = 0x80;                                  /* the success fork - retail ori v0,0x80 */
    goto m_store;
m40:
    shifted = 0x40;                                  /* the merged fail def (1 insn) - reorg duplicates it into BOTH branch delays and retargets (retail's double ori v0,0x40) */
m_store:
    D_80178980 = shifted;                            /* retail sh v0,D_80178980($at) - the def-side m web is GONE */
    __asm__ __volatile__ ("" ::: "memory");          /* the m RELOAD barrier: retail re-reads D_80178980 with a sign-extending lh (lui v1/lh v1/nop/slt); gcc 2.6.3 store-forwards the plain read and the volatile read-back came out lhu+manual-extend - the empty asm memory clobber kills the forwarding and emits nothing */
    shifted = *(unsigned short *)(hv + 0x12);        /* the m-check nprogs read rides the $2 pin's second web (draft24): retail's load dst IS v0 here too (the 1128 banked "nprogs v1 (retail v0)"); the plain local is gone */
    m = D_80178980;                                  /* the m RE-HOME (draft28): m's later uses ride the m-check RELOAD in retail (v1 feeds slt AND sll v0,v1,4 AND blez v1) - CSE-merged with the compare's read, ONE load */
    base = base6;                                    /* the s3 := a2 DELAY COPY, RAISED (draft65 v3): retail rides the m-check bne's delay slot (00C09821 @0x80068230) - above the if so the dbr's back-walk (the d33 law) fills the delay with it; the v2 below-the-if position lost the slot to a DUPLICATED sll16 (the barrier blocked the move, the dbr copied); semantically safe - pure reg copy, both fail paths never read base */
    if (m < shifted) {
        register long slot_x asm("$2");              /* the split-temp PINNED (draft25), C89 DECL-ONLY (gcc 2.6.3 rejects mixed decls - the d66 first try parse-error'd): emits nothing, the extend moves to the assignment BELOW the head force */
        hv = 0;                                      /* THE HEAD FORCE FIRST (draft66): retail's shared fail entry @0x80068378 = [a0:=0][sll16][sra16][clear] - the force is the ENTRY HEAD, before the extend; the d65 order (init-decl first) emitted the extend pair ahead of it */
        slot_x = slot;                               /* the SHORT EXTEND at the assignment (draft66): sll $2,$18,16 / sra $2,$2,16 = retail [198]/[199] - both fail tails stay IDENTICAL $2-temp-form sequences for the tail-merge (the d25 law) */
        D_8017E120[slot_x] = 0;
        goto err;
    }
    __asm__ __volatile__ ("" ::: "memory");          /* the SLL16 FLOAT BLOCKER (draft65 v2, kept): the slot4 extend's sll half floated up and stole the m-check delay in d62/d64; the barrier pins it below the branch - emits nothing */
    D_801787F4[slot] = (unsigned long)base6;
    tpose = m * 0x10;                                /* the offset rides the $2 pin (draft32) - retail sll v0,v1,4 */
    tp = (unsigned long)base + tpose;                /* retail addu a2,s3,v0 (the s3 home = the a2-chain, judge-gated) */
    k = 0;
    idx = 0;                                         /* the PRE-BRANCH REORDER (draft33): retail's k=0 is the straight-line insn BEFORE the blez (addu a1,zero,zero at 0x80068254) and the DELAY carries idx=0 (addu s0,zero,zero at 0x8006825C) - the delay slot executes unconditionally, so pre-branch idx=0 is semantically identical (idx dies at loop exit; the m<=0 path never reads it); the d32 form had idx=0 first INSIDE the if and the delay-fill scheduler took k=0 (the immediately-preceding independent set) for the slot - the fix is to make idx=0 that set */
    if (m > 0) {                                     /* the guard stays on m (retail blez v1 reads the reload, NOT the copy) */
        m2 = m;                                      /* the LOOP-BOUND COPY (draft30): retail addu a3,v1,zero at 0x80068260 - AFTER the guard, freeing v1 */
        p = base;                                    /* retail addu v1,s3,zero at 0x80068264 - p rides the freed home via the pin */
        do {
            val = *p;
            *(unsigned long *)(p + 8) = idx;
            if (val) {
                idx++;
            }
            k++;
            p += 0x10;
        } while (k < m2);                            /* the compare rides the COPY (retail slt v0,a1,a3); p += 0x10 rides the back-edge delay (retail addiu v1,v1,0x10) */
    }
    total = 0;
    __asm__ __volatile__ ("" ::: "memory");          /* the TOTAL=0 SINK-BARRIER (draft35): retail's first total=0 sits at the loop EXIT (addu s0,zero,zero at 0x8006828C, immediately post-exit, before the ap word) but gcc floats the independent set ~40 words down to the backfill pre-entry (its only use is the second loop's accumulator) - the empty-asm barrier (the banked m-reload precedent, emits nothing) sits AFTER the def so the set cannot sink past it; the d34 form already fixed ap's position (168/274), this holds the remaining word */
    ap = (long)arr;                                  /* the AP REORDER (draft34): retail's post-exit order is total=0 (0x8006828C) THEN ap (addiu a1,sp,0x10 at 0x80068290) THEN the 787B0 store prep (sll16/sra14/lui/addiu/addu/sw at 0x80068294..AC) - the d33 form had ap after the reads+tp+= (line ~927) and gcc floated total=0 late into the backfill pre-entry; the word itself is already retail-exact (0x27A50010 via the gas addu- imm law), only its POSITION is wrong */
    slot4 = (long)slot << 16 >> 14;                  /* the 787B0 SPLIT-TEMP EXTEND (draft37): the store's index scale as its own pinned statement - retail schedules it BEFORE the bound def (sll v0,s2,16 / sra v0,v0,14 at 0x80068294/98) */
    bound = ap + 1024;                               /* the t0 bound (draft23 lever c) + the BOUND REMAT ORDER (draft37): retail materializes the loop bound ONCE at 0x8006829C - BETWEEN the extend pair and the 787B0 lui; with the extend split out (source-prev) this def's list position lands it exactly there */
    *(unsigned long *)((char *)D_801788A0 + slot4) = tp;   /* the 787B0 store reads the split temp back through the pin (sw $6,D_801788A0($2)) */
    shifted = *(unsigned short *)(hv + 0x12);        /* the pre-loop nprogs read rides the $2 pin's third disjoint web (draft23 lever a): retail's load dst IS v0 (lhu v0,0x12(a0)); the built rode $3 through the plain local */
    nv = *(unsigned char *)(hv + 0x16);
    tp += shifted << 9;
    end = nv * 4 + ap;                               /* the END= OPERAND-ORDER FLIP (draft38): retail addu a3,v0,a1 (00453821 at 0x800682C4) = the scaled-nv temp FIRST - gcc 2.6.3 preserves the source addition order in the commutative-plus encoding; the ap-first form emitted 00a23821 (wrong) */
    do {                                             /* the DO-WHILE RE-SHAPE (draft36): retail has NO top guard - the entry falls straight into the end<ap skip test (.L800682C8) and ap<bound rides ONLY the back-edge (.L800682FC); ap<bound always holds at entry (ap=sp+0x10, bound=ap+0x400, frame-fixed) so the for-form's rotated top guard was dead runtime code */
        if (end >= ap) {
            ver = *(long *)(hv + 4);
            raw = *(unsigned short *)tp;
            size = ver < 5 ? raw << 2 : raw << 3;
            *(long *)ap = size;
            __asm__ __volatile__ ("" ::: "memory");   /* the in-loop reload barrier (draft18): retail keeps total += *ap as store->reload (sw/lw/nop/addu); the draft15 empty-asm clobber kills gcc 2.6.3's store-forwarding and emits nothing */
            total += *(long *)ap;
        }
        tp += 2;
        ap += 4;
    } while (ap < bound);
    D_80180450[slot] = tp;
    shifted = mode << 16;                         /* the mode SLL16 via the split-temp law (draft17): the $2 pin forces the extend into the TEMP (retail sll v0,s5,16 / bnez v0) instead of in-place on s5; a plain long test has no extend */
    if (shifted != 0) {
        spu = addr;
    } else {
        spu = SpuMalloc(total);
        if (spu == -1) {
            D_8017E120[slot] = 0;
            hv = 0;                                      /* THE HEAD FORCE (draft53): the malloc-fail entry's a0=0 (retail entries' delays) */
            goto err;
        }
    }
    end_addr = spu + total;
    total = 0;
    if (0x80000 < end_addr) {
        register long slot_x asm("$2");              /* the split-temp PINNED (draft25), C89 DECL-ONLY (the d66 mixed-decl parse error) - the extend rides the assignment below */
        hv = 0;                                      /* THE HEAD FORCE FIRST (draft66): same reorder as the m-check site - the merged tail's entry = a0:=0 before the extend */
        slot_x = slot;                               /* the extend at the assignment (draft66) = retail's order */
        D_8017E120[slot_x] = 0;
        goto err;
    }
    if (0) {
    err:
        _spu_setInTransfer((long)hv);                /* THE HEAD FORCE (draft53): the tail reads the $4 pin - the a0=0 lives at the entries/heads, the jal delay is nop (retail @0x0334) */
        fbtmp = D_80180404;                          /* the RMW temp on $3 (draft66 v3): retail [206..209] lui $3/lhu $3/addiu $3,-1/sh $3 */
        D_80180404 = fbtmp - 1;
        return -1;
    }
    D_80180408[slot] = spu;
    n = nv & 0xFF;
    n_neg = (n < 0);
    i = 0;                                           /* the I=0 PRE-BRANCH RAISE (draft65 v6): retail's i=0 = addu $a1,$zero,$zero rides the n-check bnez DELAY - above the branch it is the nearest preceding independent set and the dbr's from-above fill moves it into the delay (the d33 law). NOTE (d66 v5 negative): moving it ABOVE n_neg did NOT flip the (n<0) materialization back to slti - still srl $2,$3,31; the d66-v2 trigger for the srl form is elsewhere (the $3-web pressure from the mask/magic pins is the suspect) */
    if (n_neg == 0) {
        n2 = n;
        ap2 = (long)arr;
        do {
            total += *(long *)ap2;
            sgn = (unsigned)i >> 31;
            if ((i & 1) == 0) {
                *(unsigned short *)(base + ((i + sgn) >> 1) * 0x10 + 0xC) = (spu + total) >> 3;
            } else {
                *(unsigned short *)(base + ((i + sgn) >> 1) * 0x10 + 0xE) = (spu + total) >> 3;
            }
            i++;
            ap2 += 4;
        } while (n2 >= i);
    }
    D_801803C4[slot] = total;
    D_8017E120[slot] = 2;
    return slot;
    if (0) {
        (void)&frame_pad;                            /* dead: marks the decl address-taken at parse time only */
    }
}
