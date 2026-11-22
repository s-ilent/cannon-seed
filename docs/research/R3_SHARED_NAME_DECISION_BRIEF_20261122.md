# R3 decision brief: the 13 cross-target shared names

**2026-11-22.** Read-only status and options paper for the owner-gated naming
call (WORK_QUEUE R3). Method: `python3 tools/audit_c_names.py --cross
--adjudicate` rerun at HEAD, live yaml/curated/src reference checks, no
renames, no coverage change. **This brief takes no naming action; every option
below is the owner's call.**

## 1. Current census state (this tree, read-only, exit 0)

c rows 930 → VA-named 219, **match 144, MISMATCH 75**, curated 711; target-
unique mismatches 43; **cross-target names 13**; per-target fair recount
22 (20 mainmenu_jp lane-owned + the two parked-with-evidence OPEN rows).
Membership is **unchanged** from the last recorded state
(TASKS.md `cron-202611211415`): no row joined or left the shared classes
since the sweep closed.

The 13 names decompose into **two mechanically different classes**:

### Class A — travelling definition names (one landed C definition, many targets)

One `src/`-root C file, consumed by N target yamls, compiled at **each
target's own VMA**; the function's name travels with the definition, so the
name encodes only the canonical host's placement and every other host
"mismatches" **by construction**. These rows are not stale; the name==VMA law
can only hold at one host.

| Name (src file) | Canonical host (row matches) | Mismatching consumer rows | Row extent/tag |
| --- | --- | --- | --- |
| `func_800492F8` | g3_eu (`0x800492F8`) | 7 — g3_jp `0x800498E0`, g3org_eu `0x8004674C`, g3org_jp `0x80046D7C`, mainmenu_eu `0x8005D7D4`, mainmenu_jp `0x8005DDF4`, sces_00269 `0x80033ED8`, slps_00270 `0x80034410` | `0x110 sdk` (SetRotMatrix-template GTE composer, landed 2026-10-29 via the judge loop; "byte-identical in all eight executables" per the file header) |
| `func_8005E3DC` | mainmenu_jp (`0x8005E3DC`) | 4 — g3_jp `0x80049EC8`, g3org_eu `0x80046D34`, g3org_jp `0x80047364`, sces_00269 `0x800344C0` | `0x10c` graveyard pair first half (staged 2026-10-25) |
| `func_8005E4E8` | mainmenu_jp (`0x8005E4E8`) | 5 — g3_jp `0x80049FD4`, g3org_eu `0x80046E40`, g3org_jp `0x80047470`, mainmenu_eu `0x8005DEC8`, sces_00269 `0x800345CC` | `0x10c` graveyard pair second half |
| `func_800250F4` | g3org_eu | 0 — g3org_jp also MATCHES (same VMA in both twins) | twin repair's cross-target confirmation |
| `func_8005AE70` | g3_eu | 0 — mainmenu_eu also MATCHES | both hosts agree |

**15 mismatch rows** total in Class A (7+4+5). Per-host deltas are all
different (each target compiles the same source at its own layout) — no twin
fingerprint, by design.

### Class B — the mainmenu pair-family (8 woven-era stale names, twin-shared)

`func_8002E3C0` / `func_8002E3C8` / `func_8002FF04` / `func_80030978` /
`func_80030980` / `func_80030988` / `func_80030990` / `func_800309C8` —
**NO-MATCH-HOST**: 16 c rows (8 names × mainmenu_eu + mainmenu_jp) at
**identical placements in both twins** (e.g. both hosts place the family rows
at `0x8002C610`/`0x8002C618`/`0x8002DDC4`/`0x8002E708..0x8002E758`), each
name stale by a **uniform twin delta** (name − placement = `+0x1DB0`,
`+0x1DB0`, `+0x2140`, `+0x1270` ×5 — the woven-era fingerprint, the same
shift in both binaries). The src files are **empty graveyard stubs**
(`void func_8002E3C0(void) {}` …) awaiting the real decode — the same class
as the parked "graveyard C candidates" on the do-not-grab list.

**Third-holder fact (new in this pass):** `func_80030990` is **also** the name
of a sces_00269 **asm row** — `config/splat.sces_00269.yaml:197`
`[0x11190, asm, func_80030990] # 0xcc sdk`, sitting in the sces GTE/SDK
cluster (TransposeMatrix/CompMatrix/ApplyRotMatrix neighbors). The c-row
census does not count it; any family re-spell must coordinate with that asm
row or it silently diverges.

## 2. Live reference surface (verified)

- `config/symbols.curated.txt`: **zero** entries for all 13 names — the
  shared names are the landed C definitions' own function names (the yaml
  `c` row takes the src file's stem; the per-target symbols files carry them
  as auto entries). A rename is a src-file + yaml + symbols operation, not a
  curated edit.
- Non-self C references: **only the `func_8005E3DC.c ↔ func_8005E4E8.c`
  pair** (one reference each, the graveyard pair's commit-destination
  twins). Zero C callers for `func_800492F8` and the family stubs.
- Assembly references: zero `jal`/`j` to any of the names in the walked
  g3_jp/g3_eu surfaces; the one live holder is the sces asm row above.

## 3. Options (owner's call)

**Option A — status quo, documented carve-out.** Keep the travelling
definition names on every consumer target; the census's SHARED class already
routes them owner-gated. Cost: zero commits; the 15 Class-A "mismatches"
remain a permanent, documented exception to name==VMA. Pros: preserves the
one-definition reuse model; zero risk. Cons: the census never reaches 0
mismatches.

**Option B — region-local carve names on every consumer (per-target split).**
Restore name==VMA everywhere by splitting each shared root definition into
per-target `src/<target>/` copies named after each placement. Cost: 8
targets' yamls + 3 src files → 16 files + build-resolution churn across the
whole tree; breaks the reuse model the root layout exists for; zero matching
gain (same bytes either way). **Not recommended** — recorded as the
rejected alternative.

**Option C — SDK-name curation for the `0x110 sdk` class.** The
`func_800492F8` row (and the family's sces asm neighbor rows) are tagged
`sdk` and sit in the SetRotMatrix/CompMatrix GTE cluster
(`src/SetRotMatrix.c` is already landed). If the sdk-curation lane attributes
the 0x110 composer to a Psy-Q member family, its canonical name becomes that
member's name at every host simultaneously (one root-file rename). Cost: one
lane decision + one rename; **owner-gated to the sdk-curation lane**, not
this brief.

**Option D — Class-B carve repair when the lane unlocks.** The 8 family
names are genuinely stale: re-spell to the true placement names
(`func_8002C610`…, the 3ccee159/9388aca7 motion) in both twins + `git mv`
the 8 stubs, per-target verify. Gates: (1) mainmenu_jp is the reserved
naming lane — the 8 jp rows are inside its 20 tool-fair set, so the repair
needs the lane handoff; (2) the graveyard stubs are the do-not-grab
"graveyard C candidates" — a name change without the decode just moves the
placeholder; (3) the `func_80030990` sces asm holder must re-spell in the
same motion. Cost: ~16 c rows + 1 asm row + 8 stub renames, 2+1 targets to
verify.

## 4. Proposed collision policy (for the owner to ratify or amend)

1. **Landed definitions own their name at every consumer** (Class A): the
   census law applies per-definition at the canonical host; SHARED rows are
   documented exceptions, never auto-repaired.
2. **A shared name with a third holder is frozen** until every holder moves
   together (the `func_80030990` rule: c stubs ×2 + sces asm row).
3. **Truly stale twin-shared names** (Class B) repair by carve motion only,
   with the owning lane's handoff and the owner's call — never by census
   batch.
4. **No shared-name row is ever re-spelled to a non-canonical copy's own
   placement name** unless the definition splits (Option B) — that is the
   rejected alternative, kept on record.

## 5. The other R3 subjects (current state, unchanged)

- **mainmenu_jp's 20 tool-fair rows** — lane-owned, untouched; the recount
  still reports fair=20 (32 mismatch = 9 shared + 3 memclr-parked + 17
  carve + 3 open).
- **memclr/INTR parked families** — unchanged: sces ×2, slps ×3,
  mainmenu_eu ×3, g3_jp ×3, g3org_eu ×3, g3org_jp ×3 (all
  `sdk_anchors`-covered; the parked C-move notes stand).
- **The two non-lane OPEN rows** — unchanged and parked-with-evidence:
  g3_jp `func_800629A0` (0x3A7E0 → 0x80059FE0; the scan's duplicate-name
  name-holder — the live .2 asm row at 0x431A0 depends on the C row's name,
  `scan_functions.py` 1314-1316) and slps_00270 `func_80036CFC` (0x1457C →
  0x80033D7C; the cross-target adopted name — g3_eu's symbols adopt it for
  g3_eu's own copy). Both stay unless the scan lane or the owner says
  otherwise.
- **New observation for the record:** mainmenu_jp's OPEN row
  `func_800791A4` (0x4E064 → 0x8006D864, delta +0xB940) is the
  placement-neighbor of the g3org_eu twin pair landed in `a13c6f92`
  (`0x800791F8` → `0x8006D8B8`, same +0xB940 delta class) — when the
  mainmenu_jp lane opens, that row is a ready-made carve-candidate of the
  proven motion.

## 6. Recommendation

Ratify **Option A** (documented carve-out, zero churn) as the standing rule
for Class A; defer **Option C** to the sdk-curation lane; schedule **Option
D** only with the mainmenu_jp lane handoff. No action is required from this
brief itself — it is the decision paper WORK_QUEUE R3 asked for.
