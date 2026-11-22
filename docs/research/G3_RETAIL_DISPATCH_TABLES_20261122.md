# G3 retail object dispatch and script opcode tables

R1 pass 12, 2026-11-22. Main 173e1dfb; research input 10c66d7c.
Extends [mission scripting](G3_MISSION_SCRIPTING_20261122.md) and
[hit/damage/score](G3_HIT_DAMAGE_SCORE_20261122.md).

## Evidence: exact retail bytes were already available

The already-tracked private extract/jp and extract/eu DRAGOON_G3.EXE;1
files are NOT the retired woven dumps. Decoded GitHub contents in memory,
computed SHA-1 independently (SHA-1 implementation checked against the
standard abc vector), checked PS-X EXE header layout, and compared to
committed config/sha1 oracles.

| Target | Git blob | Bytes | SHA-1 (computed; matches oracle) |
| --- | --- | ---: | --- |
| g3_jp | 7b5ad2b5035634abd6873c86c90f486f6a99dffd | 575488 | 994a680cd139069404e5c6d6c51d3796a728f2ec |
| g3_eu | e9cfc4ee2bb3a4b474567d371037cfcd6c56cbb7 | 577536 | 39030a759e8462575b709f77eed1050f7bbaa572 |

Both load VA 80020000, header size 800 hex, t_size equals file size
minus header. No MODE2 sync pattern in either input. Read LE u32 at
file offset VA - 80020000 + 800. No binary, raw asset, or new copy of
the executable committed; only structural/address findings.
This is a static verified-input witness, not a rebuilt retail match,
runtime or fresh census. Historical binary-removal owner decision
remains deferred. Do not reintroduce these files after cleanup.

## 1. Object command opcode map

18 entries JP 80020C44 / EU 80020C24; all entries point to matching
decoder arms with JP-to-EU code delta -398 hex. Index = s16(opcode+17).

| Signed opcode | Hex | JP arm | JP handler | Operand bytes | Observed behaviour |
| ---: | --- | --- | --- | ---: | --- |
| -17..-11 | FFEF..FFF5 | 80034150 | 80033BB0 | 0 | Return -1 |
| -10 | FFF6 | 80034140 | 80033DA4 | 6 | Enable angle transition, word target + s16 step |
| -9 | FFF7 | 80034130 | 80033D58 | 2 | Clear 2000 flag, assign +7E |
| -8 | FFF8 | 80034120 | 80033D0C | 2 | Set 2000 flag, assign +7E |
| -7 | FFF9 | 80034110 | 80033CC0 | 2 | Clear 1000 flag, assign +7C |
| -6 | FFFA | 80034100 | 80033C74 | 2 | Set 1000 flag, assign +7C |
| -5 | FFFB | 800340F0 | 80033C44 | 0 | Clear C00 flags |
| -4 | FFFC | 800340E0 | 80033C10 | 0 | Clear 400 flag, set 800 flag |
| -3 | FFFD | 800340D0 | 80033BEC | 0 | Clear +32 state halfword |
| -2 | FFFE | 800340C0 | 80033BC0 | 0 | Set +32=1, clear +68 |
| -1,0 | FFFF,0000 | 80034150 | 80033BB0 | 0 | Return -1 |

All nine active arms return 0 after calling 80033BB8; reject/terminal
arm returns -1 even for out-of-range opcodes. On first-family object
driver, nonzero decoder return releases object (sets +0=0).
Do not distinguish intentional end marker from invalid opcode solely
by return value. No evidence yet for exact operand semantics of flags
1000 and 2000 or whether all rejected values occur in authored scripts.
Adjacent 80033E14 is not a decoder target.

### SDK provenance conflict: opcode -3

The current generated config/sdk_anchors.txt contains a unique
SsGetNck (SSGNC LIBSND) claim at JP 80033BEC size 28 hex,
EU 80033854 size 28 hex. Actual hash-verified retail code at
JP 80033BEC..80033C10 is a complete 24-byte-hex object handler:
stack frame, store zero halfword to object+32 in JAL delay slot,
call game return-zero leaf 80033BB8, sign-normalize result, return.
The following opcode -4 handler starts at 80033C10, within the
claimed anchor extent, and clears/sets object+24 flags as above.
This is a concrete provenance/extent conflict, not an automatic
renaming/categorization decision. The two handlers together
(80033BEC..80033C44) match JP/EU 22/22 after JAL relocation,
20/22 raw words. No raw instructions reproduced in this report.
Keep the existing SDK row/config unchanged pending adjudication,
including archive matching evidence and the full matching oracle.
This is a candidate false SDK attribution, not verified archive
identity or a newly landed C function.

## 2. Object dispatch: full 256-slot table

JP 8008A2F4..8008A6F4, EU 8008AB0C..8008AF0C; 0x400-byte
extent corroborated by next independently referenced table (section
pointer selector) at the exclusive end. All 256 entries are aligned
code pointers and map by exact -398 hex JP/EU displacement. Next
word is zero in both regions; not claimed as part of dispatch.
29 non-default entries, 227 shared default clear handler entries
(including 0). 30 distinct targets. Index is signed type halfword
in an unchecked indirect call: 256 entries does not guarantee safe
out-of-range type values or imply 256 implemented gameplay classes.

| Type (hex) | JP handler | Role established or next investigation |
| --- | --- | --- |
| 01 | 80030D5C | Render helper 80031C5C |
| 02 | 80030D7C | Render helper 80031CDC |
| 03 | 80030D9C | Render helper 80031C9C |
| 07 | 80030D54 | No-op |
| 12 | 80038434 | Pending |
| 13 | 8003DDC0 | Pending |
| 14 | 8003E060 | Pending |
| 18 | 8003442C | Pending |
| 19 | 8003416C | Pending |
| 1C | 800385F4 | Pending |
| 1D | 800341E8 | Pending |
| 20 | 80037280 | Pending |
| 28 | 8003822C | Pending |
| 29 | 80037FB4 | Pending |
| 30 | 80037D0C | Pending |
| 31 | 80037D58 | Secondary effect (pass 10) |
| 38 | 8003DB0C | Fragment motion/lifetime (pass 10) |
| 50 | 8003098C | Pending |
| 60 | 80033E44 | Dual-clock object scripting (pass 11) |
| 68 | 80038A9C | Second scripting family (pass 11 inner loop) |
| 70 | 80036810 | Pending |
| 71 | 80036E14 | Pending |
| 78 | 8003176C | Pending |
| 79 | 80039104 | Pending |
| 80 | 8003C414 | Pending |
| 81 | 80039CC4 | Pending |
| 88 | 8003A5D4 | Pending |
| 89 | 8003ADB8 | Pending |
| 90 | 80031628 | Pending (+5C stream reader lead) |
| All others, including 00 | 80030D4C | Clear object+0 then return |

The type 00 default handler is not a pure no-op: it writes zero to
the type. Dispatcher always calls it and advances PRNG afterwards.
This confirms the deterministic empty-slot behaviour rather than
simply hypothesizing it from the iterator. Type 07 is the actual
empty-return handler. Configuration/descriptor ID 18 in the scheduler
is distinct from runtime type 18; do not conflate IDs.

## 3. Damage class table entries (pass 9 closure)

JP 80020CF4/EU 80020CD4 and JP 80020D0C/EU 80020CEC, five
entries each. All 10 agree with code relocation -398 hex.

| Gunner +88 class | Standard JP arm | Alternate JP arm | Behaviour family |
| ---: | --- | --- | --- |
| 0 | 80034B7C | 80034C40 | Whole-stage/update fallback, zero A8 |
| 1 | 80034AEC | 80034BEC | Fractional 75/100 accumulator |
| 2 | 80034B48 | 80034C24 | Whole-stage/update with award |
| 3 | 80034AEC | 80034BEC | Fractional 75/100 accumulator |
| 4 | 80034B48 | 80034C24 | Whole-stage/update with award |
| Other | 80034B7C | 80034C40 | Same as 0 via range rejection |

Actual arm behaviour in pass 9. Standard 1/3 subtract 75 from A8
and consume a stage when threshold reached; 2/4 consume one stage
directly and award as conditioned by remaining durability. Alternate
1/3 add to hit progress +88 when accumulator crosses threshold;
2/4 increment +88 and award cfg+E4; 0/invalid increment +88 and
clear A8. Names/physical meaning of the five weapon classes are
not assumed; trace gunner+88 writers next.

## 4. Next

We can now extract the actual mission timeline, configuration pointers
and descriptor/script references from the hash-matched existing
private input using strict pointer/bounds guards and no raw asset
publication. Prefer a bounded first-section inventory next: establish
actual sentinels, count unique descriptors, cross-reference all config
types with this table, and sample-script decode with explicit alignment
and termination checks. Trace the third cursor +5C, especially type
90, before naming paths. Source-only comparisons no longer need to
stand in for the actual table values. Any C landing still requires
the normal full retail matching oracle.
