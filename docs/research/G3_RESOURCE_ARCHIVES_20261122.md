# G3 resource archives, TIM/TMD initialization and shared Gourb loader

R1 pass 25, 2026-11-22. Input head e0c4b353c78e6ea591eadbd81acbbc472340fee2. Inspected original private Dragoon JP/EU EXE blobs 7b5ad2b5035634abd6873c86c90f486f6a99dffd / e9cfc4ee2bb3a4b474567d371037cfcd6c56cbb7 (SHA-1 verified in prior passes), Gourb JP/EU d10cad84f9f0070d5f631d19c2cdbf7674139082 / 062afcfc25510e67575a7fb33ec66f884ad20176 (repository blob identity, not freshly SHA-1 verified). Static analysis. Container startup still returns ClientError on basic ls; actual CHD archives not inspected. No game data publication, source conversion or matching build claims.

## 1. Memory and archive lookup contract

JP 80024760 wrapper calls 800247C8 repeatedly while result == -1, with initial counter 0x0FFFFFFF; on exhaustion prints FLOAD:fault! and returns zero. 800247C8 frees previous allocation stored at gp+54 (if non-null), calls CdSearchFile(80061FCC) and gets file byte size from returned CdlFILE, rounds size up to 2048-byte sector count for ordinary positive sizes. Allocates fixed 0x66000 bytes (417792 = 204 sectors), stores pointer in gp+54, zero-fills allocation, seeks via CdControl(0x15,&CdlFILE,NULL), requires CdSync(0,...) result2, invokes CdRead(sectors,buffer,0x80). Polls CdReadSync(1,NULL) until <=0, returns buffer on that branch (negative result also satisfies branch, do not modernize presumed intended error handling). No file size vs allocation bound check visible. CdSearchFile/seek/read failure branches and NULL allocation have distinct return behavior. 80024738 frees gp+54 and zeros it. Separate loader 800249BC reads into fixed playrec buffer pointer from 80045950 instead of allocating, with similar sector rounding/read path; not part of general archive allocation.

JP 80024910:
    if (index < 0) return pointer_minus_one;
    int32 offset = ((int32*)archive_base)[index];
    return archive_base + (offset / 4) * 4;

Disassembly uses sign correction then arithmetic shift, equivalent to truncation toward zero for signed int32. Index stride 4 from archive base, no magic/count/length validation, no +header adjustment, no positive upper bound. Offset zero yields archive base, not automatic missing-entry sentinel. Negative offset not rejected by this routine. Actual archives may use conventions beyond this contract; cannot infer number of table entries from first offset until inspecting file. Any offline extractor must be stricter: reject out-of-bounds index, negative/unaligned offset, check target header and container bounds instead of trusting retail behavior. No assertion of compressed payload or per-entry lengths.

## 2. Distinct texture and model lifetimes

Startup JP 80022504..8002257C:
- loads TIM.DAT filename via pointer 8007179C, calls archive loader;
- direct texture entry indices 0x4D and 0x4E passed to 80024AD8 and 800250B0 respectively (atlas/HUD texture setup leads);
- sets texture mapping table 80072FD4 through 8002DECC, calls 8002DEDC(0,-1) to initialize records until sentinel;
- frees TIM archive at 80022540;
- later loads TMD.DAT filename via ptr 800717A4, sets model mapping 800717C4 through 8002DE2C, initializes at 8002257C via 8002DE3C. Archive stays resident across gameplay, freed at 8002271C. Model pointers refer into this allocation, not independent model copies.

Model table 20-byte rows {u32 logical_id, s32 archive_index, u32 meta2, u32 meta3, u32 initialized_ptr}, ends ID=-1. 8002DE3C iterates; negative archive index or resolved NULL -> initialized_ptr=-1. Else copies resolved pointer and calls GsMapModelingData(ptr+4), deliberately skipping leading TMD ID. SDK anchor JP 8004F5AC, size78. Body sets flag bit0 if clear, reads object count, relocates three pointer fields at +0/+8/+10 hex in each 28-byte TMD object record relative to first record base. Already mapped flag bypasses relocation, important for multiple logical IDs referencing the same archive index. No TMD ID check in caller. This is standard SDK on-disk TMD model mapping, not custom geometry compression in this measured path.

TIM upload 8002F9B0 checks first word=0x10, else returns without filling output. Calls GsGetTimInfo(ptr+4,&stack_info) (JP8004F624), copies first rectangle and uploads data via LoadImage and DrawSync(0); if flags bit3 set, uploads second rectangle/data and DrawSync. Order observed is first SDK rectangle, then optional second; don't assume palette-first order without SDK struct layout verification. Copies seven words (28 bytes) to destination. Invalid input output untouched; caller may use uninitialized values if archive corrupt. 8002F838 wraps upload into a 36-byte sprite/texture descriptor: extracts flags low2 into high byte, calls GetTPage(flags,0,x,y), width and U offset multiplied by4 for flags0, by2 for flags1, unchanged for2, other flags diagnostic/zero width; height retained; copies palette coordinates and initializes color 0x80 RGB, centered half-width/half-height, scale 0x1000 and trailing zero. SDK anchors confirm GsGetTimInfo, LoadImage, DrawSync, GetTPage. Texture descriptor creation retains GPU page/coordinate info, not original CPU texture bytes.

Texture table rows stride52 (13 words), sentinel id=-1. 8002DEDC computes table row from starting index, maximum count argument (-1 unlimited), skips negative archive indices or NULL resolution and sets high bit of initialized flags; otherwise calls 8002F838(row+16,archiveptr), ORs initialized flags with authored row+8. First four words are authored ID, archive index, flags, extra field (last field semantics pending), remaining 36 bytes initialized descriptor. 8002F36C references model table; 8002F3D8 and 8002F42C reference texture table (resolver details pending). Preserve duplicate IDs and ordering.

## 3. Resource inventory and regional distinction

Dragoon JP model rows 307 unique logical IDs, 12 negative archive index entries, 295 nonnegative mappings with 260 unique indices (0..294 range, not necessarily contiguous). Same 307x5 words EU from pass16. Metadata word2 values 0/64, word3 0/8/9/10/11; do not name their semantics yet.

| Logical model | Archive index | Context |
|---:|---:|---|
|9F|57|active type1D fighter|
|D9|89|Doldva parent resource|
|19A|226|type98 placeholder's second halfword, NOT rendered by type98|
|1C0|239|SPARKBIT parent initial resource|
|1C4|243|SPARKBIT scripted model change|
|1C5|244|SPARKBIT phase -3 effect|

Observed model table mappings, not inspected model geometry.

Texture tables JP80072FD4..80076748, EU80073814..80076F88 (exclusive rows, sentinel at end). Both 273 rows, 272 unique IDs; duplicate resource ID0x3A0 (928), consecutive JP rows179/180 identical first four words. Compared all 3549 words, 3276 equal: precisely all 12 non-index words per row; archive index changes in all 273 rows. JP 204 distinct indices range0..205, EU126 distinct range0..125. All nonnegative. Examples first logical ID101 -> JP170/EU2, ID256 -> JP133/EU3, final ID2048 -> JP189/EU79. Thus regional texture archive indexing differs materially even though logical IDs/metadata match. Do not use JP index table to resolve EU textures; logical resource ID is stable across both. Counts of referenced indices are not actual archive entry count or proof of deduplicated identical images.

## 4. Cross-scenario loader witness

Six game-owned windows compared by scanning target code 80022400..80048000, unique best normalized shape in each of Dragoon EU and both Gourb EXEs. Mask J/JAL target bits, LUI/ADDIU/memory immediates. Not a complete semantic equivalence proof; preserve meaningful immediate differences.

| Dragoon JP range (exclusive) | Words | Dragoon EU start | Gourb JP start | Gourb EU start |
|---|---:|---|---|---|
|80024738..80024910|118|80024798|800250FC|80025114|
|80024910..80024954|17|80024970|800252D4|800252EC|
|8002DE2C..8002DECC|40|8002DBFC|8002EAD4|8002E85C|
|8002DECC..8002DFD8|67|8002DC9C|8002EB74|8002E8FC|
|8002F838..8002F9B0|94|8002F4C8|800304E0|80030128|
|8002F9B0..8002FA9C|59|8002F640|80030658|800302A0|

395 words total. Dragoon EU: 395/395 shape,352 exact. Gourb JP: 393/395 shape,350 exact. Gourb EU:395/395 shape,348 exact. Only Gourb JP shape differences in loader window are ORI immediate 6000 ->5800 in allocation and zero-fill size (JP Gourb fixed 0x65800=415744, one sector smaller; other three match 0x66000). This supports shared implementation across all four retail scenario targets, with specific region/scenario tuning. Do not force common constants where observed difference. SDK calls named via existing target-scoped anchors, not claimed game functions. No code split or build witness performed.

## Next

Trace resource lookup consumers 8002F36C/8002F3D8/8002F42C and model primitive dispatch if necessary; prioritize four-target shared-function atlas and matching C conversion plan with reproducible build witnesses. Actual archive validation/extraction must await private CHD access and working execution environment; do not commit raw assets.
