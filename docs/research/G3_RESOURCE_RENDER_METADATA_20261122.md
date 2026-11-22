# G3 resource metadata to primitive lighting and ordering-table depth

R1 pass 27, 2026-11-22. Input HEAD d7ee3ab6af6690ee1e122b71f4da2399a7fd0, PR #10. Continues [pass 26](G3_SHARED_RESOURCE_RESOLVERS_20261122.md). Static source and tracked original EXE investigation only; no new compiler/full-image witness. Addresses JP unless stated.

## Model attributes and depth shift

Both model constructors 8002E318..8002E4B8 and 8002E4B8..8002E638 (latter end not needed for proof) in [JP scene ASM](../../asm/g3_jp/nonmatchings/func_8002A2DC.s) call logical-ID resolver 8002F368, test -1, link model via GsLinkObject4, and write model-table +8 to stage+4 (GsDOBJ2 attribute), model-table +0C to stage+68. First stores 8002E488/48C, second 8002E60C/610. The first constructor forms key signed16(descriptor+2 halfword + 8); the second takes explicit key. Stage+64 retains TMD base. 0x6C stride. Stage+4 is pointer argument to primitive dispatcher at 8002EC2C..8002EC44; a2 is stage+68. Do not confuse model attributes with game stage type at +0.

[JP dispatcher](../../asm/g3_jp/nonmatchings/func_800526D4.s) 80052738..750 extracts bit6 to D_801474F4; 800527A4..7B4, 80052804/808 select mode2 when set, else mode0 or mode1 conditioned on bits3..5 and global GsSetLightMode_lmode. 80052834 computes mode*4; primitive-code 20/24 cases select tables D_80098180 / D_800981C0 with additional offset 12 when attribute bits9..11 nonzero. Raw original EXE table words (first three, normal non-subdivision path) resolved against target SDK anchors:

| Primitive | mode0 | mode1 | mode2 |
|---|---|---|---|
| 0x20 flat triangle | 80054DC4 GsTMDfastF3L | 80054F0C GsTMDfastF3LFG | 80054C84 GsTMDfastF3NL |
| 0x24 textured flat triangle | 80057A80 GsTMDfastTF3L | 80057BF0 GsTMDfastTF3LFG | 8005791C GsTMDfastTF3NL |

Mode0 triangle runs GTE nccs at 80054E9C; mode1 uses ncds at 80054FE4 (normal-color depth cue); mode2 does neither in full 0x140-byte F3NL body, while still projecting, clipping, sorting and writing packet color. Textured triangle L also runs nccs at 80057B80, NL lacks that normal-lighting command. This proves authored bit6 selects **no normal lighting** for these primitive variants, not merely abstract mode selection. Other primitive classes and subdivided branches require separate enumeration. See [F3L](../../asm/g3_jp/nonmatchings/func_80054DC4.s), [F3LFG](../../asm/g3_jp/nonmatchings/func_80054F0C.s), [F3NL](../../asm/g3_jp/nonmatchings/func_80054C84.s), [TF3L](../../asm/g3_jp/nonmatchings/func_80057A80.s), [TF3NL](../../asm/g3_jp/nonmatchings/func_8005791C.s). Dispatcher attribution gate remains intact.

Dispatcher saves third arg in s5 at 800526E4 and forwards as stack arg at 80052884/8C. F3L loads t7 from sp+14 at 80054DCC, runs avsz3 (80054E88), reads GTE OTZ, subtracts OT offset, logical shifts right by t7 at 80054EA4, masks low16, multiplies by4 and adds OT pointer. F3NL repeats at 80054D4C..D68. Thus model +0C is an **OT depth shift**, not an absolute priority. Formula for measured cases: slot = (((uint32_t)(OTZ - ot.offset)) >> (shift & 31)) & 0xffff. No claim that all callback variants are identical.

Census from 307 rows in original JP EXE at 800717C4: exact paired counts (attribute, shift): (64,0)=192, (64,8)=54, (64,9)=6, (64,10)=21, (64,11)=1, (0,0)=33. Thus 274/307 select no-normal-lighting mode for measured triangle cases; 225 shift0, 54 shift8, 6 shift9, 21 shift10, 1 shift11. Counts include disabled archive entries and are authored resource rows, not a count of visible models or primitives. Regional model table equality previously measured in pass25. Shift values map polygons to progressively coarser/lower OT buckets; not a Z-buffer, not proven physical depth units.

## Texture +0C = ordering-table priority

- Projected sprite staging 8002E770..8002E894 gets lookup output at sp+10 and copies to 0x7C stage+28 at 8002E84C. Renderer 8002EC7C..8002EF14 uses that same word as a2 in GsSortSprite at 8002EED0 (load 8002EECC), independently of actual camera depth used for projection/scale.
- FOBJ staging 8002E894..8002E9F4 copies 36-byte descriptor then output to 40-byte stage+24 at 8002E958 (s0=stage+6). Renderer 8002EF14..8002EF84 loads stage+24 into a2 at 8002EF48 and calls GsSortSprite at 8002EF54.
- Direct HUD 8002EF84..8002F09C uses 0x700 resource, passes same lookup output from sp+60 to TWO GsSortSprite calls at 8002F074, 8002F084 (positions y=-104/+104).
- [SDK sprite sorter](../../asm/g3_jp/nonmatchings/func_80051D14.s) saves a2 in s4, masks low16 at 80051DBC / 8005213C when passing ordering depth to packet insertion paths. Also rejects negative sprite attribute (80051D40), and zero width/height. Confirms pass25 initializer's high bit is a render suppression flag; lookup itself does not reject disabled flags.

273 authored Dragoon texture rows at 80072FD4: priority0=105, 1=16, 2=138, 12=10, 14=4. All priority fields equal across JP/EU per pass25. Do not infer identical art from equal logical IDs, or assume sorting direction without OT setup evidence. Texture +8 authored flags OR into initialized GsSPRITE attribute; distinct from model attributes layout. Provisional semantic records: ModelResource = id,index,attributes,depthShift,modelPtr (20 bytes); TextureResource = id,index,attributes,otPriority,GsSPRITE (52 bytes). Names are descriptive, not source symbol recoveries.

## Four-target corroboration (game-owned consumer windows)

Original EXEs read using private file API base64, skip 0x800 header, little-endian words. Search aligned 8002D000..80032000 for matching normalized windows; mask J/JAL destinations and LUI/ADDIU/memory immediates, then compare exact words. Seven unique best matches with all shapes equal; table shows full window counts and exact matches EU/Gourb JP/Gourb EU.

| JP start | words | EU | Gourb JP | Gourb EU | exact per sibling |
|---|---:|---|---|---|---|
| 8002E470 | 8 | 8002E240 | 8002F118 | 8002EEA0 | 8/8/8 |
| 8002E600 | 5 | 8002E3D0 | 8002F2A8 | 8002F030 | 5/5/5 |
| 8002E83C | 5 | 8002E60C | 8002F4E4 | 8002F26C | 4/4/4 |
| 8002E950 | 6 | 8002E720 | 8002F5F8 | 8002F380 | 6/6/6 |
| 8002EC2C | 7 | 8002E9FC | 8002F8D4 | 8002F65C | 6/6/6 |
| 8002EECC | 3 | 8002EC9C | 8002FB74 | 8002F8FC | 2/2/2 |
| 8002EF44 | 6 | 8002ED14 | 8002FBEC | 8002F974 | 5/5/5 |

40/40 normalized shapes, 36 exact in each sibling. An additional 8-word HUD submission window has two equal shape hits per target (repeated draw pair), excluded from unique totals. This corroborates field flow in four game targets, not fresh Gourb SDK primitive semantics or table census. Both constructors/draw loops reside in large game ASM rows from pass26. No SDK anchor applied to game constructors. Negative: visual equivalence/render output not tested.

Next: recover OT setup, draw direction, bucket capacity and placement/layering policy; cross-reference resource IDs with lighting and priority distributions by gameplay class. Distinguish runtime GPU sorting from modern depth-buffer emulation; no source landings pending guarded verification.
