# R1 pass 21 — the D_800AC4F4 exit-flag census: four writer sites,
# two machines, and no zero-writer in the static image

Date: 2026-11-26 (window cron-20261126-1409, job 540513's seventeenth
fire — same window as pass 20). Scope: g3_jp only, JP-first
discipline. Docs only; zero source, YAML, asm or oracle change; zero
renames.

## The question this pass closes

Pass 20 posed: who sets D_800AC4F4 = 1 — the dispatcher exit /
reboot-to-launcher trigger? The census: every reference to the word
in the g3_jp image (row sweeps over all nonmatchings files, plus a
gp-relative alias check at gp+0x1288 — none exist), each writer's
value and guard decoded by hand.

**Verdict: exactly four writer sites, in two machines, every one
storing 1, and no site ever stores 0 — the flag is
write-once-per-load. The module cannot un-request its exit; only the
module swap (the crt0 bss-zero) clears it.** The dispatcher's reader
is exact: `lh D_800AC4F4` at 0x80042D24, `bne v1, 1` back to the loop
head 0x80042C90, else `jal func_8002AD24` and return (the HUD note's
section 6 item 8, now instruction-pinned).

## Machine A — the vsync-side mode machinery (row func_80022AFC.s,
## the row holding the registered vsync mid-entry 0x8002370C)

1. **func_8002366C** (0x8002366C..0x8002367C): `sh v0` to the flag,
   then `j func_800236F8`. Single branch source: func_80023584's
   `beq s0, 2` at 0x800235A8 with the delay `ori v0, 1` — so the
   stored value is 1. The guard chain: `lw *(s1)` / `andi 0x10`
   (a pad/button bit), zero-test, then the mode switch
   s0==1 -> func_800235E0, s0<2 -> func_800235B0, **s0==2 -> the
   flag store**. Reading: button bit 0x10 while mode 2 requests the
   exit — the in-flight button exit. The sibling tail
   func_80023554 fires the script executor func_80029FC0(0x36)
   (pass 15's executor; the exit jingle slot).
2. **func_80023D14** (0x80023D14..24): `sh v0` (1, from the branch
   delay at 0x8002390C) to the flag, then `j func_80023D48` (the
   vsync join). Guard: mode word D_800AC5AC == 5 AND s3 == 4 AND
   the halfword *(gp+0xA) == 0 (func_800238C4's tail,
   0x800238E4..0x80023908).
3. **func_80023D24** (0x80023D24..40): `ori v0, 1` / `sh v0` to the
   flag, **then `jal func_80029FC0` with a0 = 0x35** — the exit
   fires script command 0x35 through the pass-15 executor — then
   `j func_80023D48`. Guard: func_800239F4's mode match AND
   lh D_800AC02C >= 0 AND lh D_800AC164 == 0 (0x800239FC..0x80023A1C).

## Machine B — the dispatcher-row attract timer
## (row func_80033C44.s, the dispatcher's own row)

4. **func_80043FAC** (0x80043FAC..C4): the store trio
   **D_800AC5AC = 1** (the mode word set to 1), D_800ABE94 = 0,
   **D_800AC4F4 = 1**, falling into the shared epilogue
   func_80043FC4. Reached from func_80043F80: `beqz v0` (the
   caller's decision word) takes the store path immediately;
   otherwise the halfword countdown D_800ABE7C is decremented and
   `bgez` returns on non-negative — expiry (negative) is the only
   other path to the trio.
   The caller **func_80043EEC**: `jal func_80022DE0("STAR_MODE7")`
   first (the pass-13/14 script-selector machinery on the
   STAR_MODE7 label), then the gate reads D_800ABF9C / D_800ABFC4
   and ends in one of three `j func_80043F80` tails whose delay
   slots compute `slti v0, *(D_800AC294), <threshold>` — the
   thresholds **0xC78 (3200), 0x16F8 (5880), 0x1E76 (7798)**, keyed
   by the gate pair. So the STAR_MODE7 attract sequence's length
   word D_800AC294 either crosses its mode-keyed threshold (immediate
   exit) or lets D_800ABE7C tick down to expiry (timed exit); either
   way the store trio fires, the dispatcher sees flag == 1 on its
   next check, and main runs the teardown + LoadExec reboot pass 20
   decoded.

## The consolidated reading

- **The per-frame exit tier**: the dispatcher polls the flag once per
  iteration (after the render submit func_80022FE4). Four
  requesters, two machines — one keying on the STAR_MODE7 attract
  sequence (time/length), three on the vsync-side mode machinery
  (a button exit at mode 2, a mode-5 counter condition, a
  mode-counter expiry that also fires script command 0x35).
- **Write-once-per-load**: all four sites store 1; no in-image store
  of 0 exists; the flag's only reset is the crt0 bss-zero at the
  next module load. The static image cannot cancel an exit request.
- The exit flow end to end (all now instruction-pinned in-image):
  requester sets flag -> dispatcher's next check exits via
  func_8002AD24 -> main's teardown tail (pass 20's calls 33-46) ->
  LoadExec("cdrom:\\MAINMENU.EXE;1", 0x801FFF00, 0).

## What this closes and what it opens

Closed: pass 20's next-question (a) — the reboot trigger's full
writer census with values and guards.

Open: (a) the button-bit word *(s1) behind func_80023584's 0x10 mask
(the pad-state pointer's identity — the pad lane is lane-owned and
stays untouched); (b) the mode-5/gp+0xA and D_800AC164 guard words'
owners as named rows; (c) the D_800ABF9C / D_800ABFC4 gate pair and
D_800AC294's writer (the STAR_MODE7 length source); (d) the EU
corroboration of both passes 20 and 21 in one walk; (e) the getter
func_80025944 id map (pass 20's item, unchanged).
