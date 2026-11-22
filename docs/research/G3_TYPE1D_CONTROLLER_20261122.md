# G3 object type 0x1D constructor and 0x1C active controller

Static research, 2026-11-22. Base: `173e1dfb434caac71ef4cecf1bf815443ca16037`. No executable, source, symbol or oracle changes.

## Input evidence

Read the legacy tracked JP/EU `extract/<region>/DRAGOON_G3.EXE;1` at the pinned base privately. Decoded base64 and recomputed SHA-1 over the complete PS-X EXE; both match the committed `config/sha1/g3_{jp,eu}.sha1`:

| Target | Bytes | SHA-1 |
|---|---:|---|
| JP | 575488 | 994a680cd139069404e5c6d6c51d3796a728f2ec |
| EU | 577536 | 39030a759e8462575b709f77eed1050f7bbaa572 |

Little-endian words at file offset VA - 0x80020000 + 0x800. This is input verification, not a rebuilt retail witness. Prior mission inventory reported 74 type-0x1D spawns in ticks 5000–5499; the event inventory has not been independently rerun in this pass. The following dispatch and configuration facts are independently measured.

## Constructor indirection

| Evidence | JP VA | EU VA |
|---|---|---|
| object dispatch table | 8008A2F4 | 8008AB0C |
| configuration table | 80089D3C | 8008A554 |
| config ID 0x66 | 800AB970 | 800AC1B4 |
| config ID 0x7B | 80089A74 | 8008A28C |
| dispatch slot 0x1D | 800341E8 | 80033E50 |
| dispatch slot 0x1C | 800385F4 | 8003825C |

The entry at config table index 0x66 points to two halfwords {0x1D, 0x7B}. At 800342A4..800342E8 the handler loads the second halfword of the current configuration, indexes the configuration table, replaces object+0x60 (configuration pointer), and copies the new record's first two halfwords into object+0x00 and +0x30. Config 0x7B starts with {0x1C, 0x9F}. Therefore 0x1D is an initializer transition, not the active update ID; the 0x66 path becomes 0x1C and selects model/resource ID 0x9F. No visual model identification yet.

JP 0x800341E8–0x8003442C (exclusive) consists of the 37-word wrapper and 108-word helper. 145/145 instruction words match the EU sibling under relocation masking (J/JAL targets, LUI immediates and ADDIU based on at). Config 0x7B's first 192 bytes match JP/EU byte for byte. The type-0x18 dispatcher nearby at 8003442C is a *different* type, not the 0x1D successor.

The helper also converts object+0x10/12/14 angles through 80030454, computes direction terms via 80032364, scales them depending on +0x26 and +0x46, then stores direction/delta at +0x38/3C/40 and adds it to +0x04/08/0C. The wrapper writes the state fields below if +0x00 is nonzero.

| Object offset | Initial value/source |
|---|---|
| +0x24 | 0 (phase) |
| +0x28 | 1 |
| +0x2A | 0 (hit mask) |
| +0x2C | config+0x0A |
| +0x2E | config+0x14 (durability used by active handler) |
| +0x34 | object+0x44 |
| +0x46 | low halfword of config+0xB4 |
| +0x48/4C/50 | 0 |
| +0x6C | config+0xBE (signed countdown in update) |
| +0xA4 | low 32 bits of (config word +0xB4 + 110)^2; precise consumer/meaning not yet established |

## Active controller

JP 800385F4..8003869C: if object+0x2A is nonzero, call hit processor 80034C60 with object/config. Use returned index for model/resource selection; negative signed durability at +0x2E calls 80038968, which sets type 0x31 and calls 80037E0C and 80037D58. Otherwise dispatch by +0x24 values 0 or 1.

- 8003869C..80038734 (phase 0): decrement signed halfword countdown +0x6C; call 80033274; test signed high halfword +0x36 against +0x46. Once countdown is negative and the threshold is met, set phase 1 and copy config word +0xB4 to object+0x44. Call 800334AC and 800387BC.
- 80038734..800387BC (phase 1): if +0x26 is zero, copy global position-like vector 8016AC18..20 to +0x48/4C/50. Call 80033274, 800332C4, 800334AC, 800389EC, then 800387BC. The angular adjustment helper advances +0x10 and +0x12 toward +0x78 and +0x7A using config halfwords +0xB8/+0xBA.
- 800387BC..80038968: add +0x38/3C/40 to position, arithmetic right shift by 16 when +0x26 is zero; call 80034974 and conditionally clear type using the signed angular bound. Call 80034748, compare its result against a sum of squares of velocity-like components plus an environment-mode-dependent constant (0x2F44 or 0x10810), and invoke 800389A0 on the near threshold. Clear type on another distance-like bound; otherwise update angle +0x14 by config+0xBC, recompute direction terms and call 800337B8.
- 800389A0..800389EC: call 800351D0 and branch on signed return -1; the return -1 path calls the destruction transition 80038968 at 800389C8 and jumps to the epilogue; other returns clear type. Meaning of 800351D0 unresolved.

The EU 0x1C dispatcher and phase/integration family from 8003825C (221 words through the end of the integration function) have 220/221 matches using a narrow instruction-shape mask (direct jump targets, LUI immediates and selected address immediates); the remaining word is LH a0, low address AC3C versus AD64, part of a relocated global coordinate load. This is a structural check, not equivalence of computed addresses or runtime behaviour.

Config 0x7B has +0xB4 = 0x003C0000, +0xB8/+0xBA = 0x0400 each, +0xBC = signed -0xA00, +0xBE = 0x7FFF. Note that 0x7FFF is a very long countdown; although the generic active controller implements two phases, phase 1 should **not** be assumed to occur in a normal wave. No dynamic trace has been performed.

## Next bounded question

Reconstruct the exact initial descriptors/events selecting configuration 0x66, then simulate a few initial positions in the actual coordinate frame, accounting for the environment vector and +0x26 mode. Establish model/resource 0x9F mapping to TMD.DAT and determine the meaning of 800351D0 and the proximity/distance checks. Only then identify the visible atmospheric encounter or claim attack direction. Code provenance is game-specific from the type/config/state dispatch and prior hit-path evidence; archive membership and YAML row boundaries still require independent review before any C landing. No semantic C conversion, runtime test, rebuild, or CI claimed.
