# RECON — Galaxian³ (Project Dragoon), Phase 0-1 findings

Everything measured so far, kept current per the methodology (facts here,
counts in tools, lessons in commits). Compiled from the two retail discs
supplied by the project owner; the discs and executables themselves never
enter the repository.

## 1. The discs (provenance)

| file | size (bytes) | SHA-1 |
| --- | --- | --- |
| Galaxian3_Japan.chd | 382,607,234 | `129b9f04311752a43a73e133322509882cca0647` |
| Galaxian3_Europe.chd | 382,613,010 | `cc94a34260969427e3b690f4cef5e2c6446ad85f` |

Both are CHD v5 CD-ROM images (`cdlz` primary codec). Extracted with the
project's own reader (`tools/chd_extract.py`, a port of MAME's
`chd.cpp`/`chdcodec.cpp`/`cdrom.cpp` algorithms — LZMA main channel decoded
length-exact, FLAC subcode skipped, sync/ECC regenerated per
`cdrom_file::ecc_generate`). Volume ID on both: `GALAXIAN3`.

| | Japan | Europe |
| --- | --- | --- |
| boot serial | SLPS-00270 (`BISLPS-00270` in exe strings) | SCES-00269 (`BOOT = cdrom:\SCES_002.69;1`) |
| data track | 248,318 frames (MODE2_RAW) | 248,562 frames |
| CDDA tracks | 3 (4,083 + 1,448 + 13,651 frames) | 3 (same lengths) |

## 2. The executables — FOUR build targets per region

This is a **multi-EXE game** (old Psy-Q chained-launch scheme): a small boot
executable plus three larger payloads the boot/menu code loads from disc.
Every one of them is a byte-exact rebuild target, analogous to Parasite
Eve's overlays: one oracle file per target under `config/sha1/`.

| target | file on disc | size (B) | payload (B) | SHA-1 |
| --- | --- | --- | --- | --- |
| `slps_00270` | SLPS_002.70;1 | 290,816 | 288,768 | `f2a13b5270876e8117ddcc38fb99716124195c46` |
| `sces_00269` | SCES_002.69;1 | 290,816 | 288,768 | `1969898477965aefa053fabd07cd6c410e816986` |
| `mainmenu_jp` | MAINMENU.EXE;1 | 698,368 | 696,320 | `ec26c6964ede52114254013c2b3da81c84d9aaa2` |
| `mainmenu_eu` | MAINMENU.EXE;1 | 700,416 | 698,368 | `cbad60dc66b4d0c5b8f559c269b18ae2288ed8c5` |
| `g3_jp` | DRAGOON/G3.EXE;1 | 575,488 | 573,440 | `6ab446ff7a802d95fba7efce8dae4bdb5457ff3a` |
| `g3_eu` | DRAGOON/G3.EXE;1 | 577,536 | 575,488 | `80acb6d1ecccfcf2ee2f7e05b357b8331ef24e03` |
| `g3org_jp` | GOURB/G3ORG.EXE;1 | 628,736 | 626,688 | `5923d4eb4b239630286ab4f9b26b88186690def9` |
| `g3org_eu` | GOURB/G3ORG.EXE;1 | 630,784 | 624,768 | `c83138e295864531c0cb7234b6059b340803eb9b` |

(payload = file size − 0x800-byte PS-X EXE header. The header's own
`t_size` field reads 0 in all eight — see §3.)

Primary region: **Japan** (original). Europe is the regional port target
afterwards; EU payloads differ by 1-4 KiB from their JP counterparts.

## 3. Header facts (all eight executables)

| target | t_addr (payload) | pc0 (entry) | gp0 ($gp) |
| --- | --- | --- | --- |
| slps_00270 | `0x8002DB14` | `0x80020000` | `0x00046800` |
| sces_00269 | `0x8002D908` | `0x80020000` | `0x00046800` |
| mainmenu_jp | `0x8005C530` | `0x80020000` | `0x000AA000` |
| mainmenu_eu | `0x8005C160` | `0x80020000` | `0x000AA800` |
| g3_jp | `0x80047EF0` | `0x80020000` | `0x0008C000` |
| g3_eu | `0x80047B58` | `0x80020000` | `0x0008C800` |
| g3org_jp | `0x8004538C` | `0x80020000` | `0x00099000` |
| g3org_eu | `0x80044FAC` | `0x80020000` | `0x00099800` |

`SYSTEM.CNF` (both regions): `TCB = 4`, `EVENT = 16`, `STACK = 801fff00`.

**Open question (the first Phase-1 item):** the load scheme is nonstandard.
All four exes share entry `0x80020000` while their `t_addr` values differ
and `t_size` is 0 — consistent with a chained multi-EXE launcher where the
BIOS boots SLPS_002.70 into the 0x80020000 region and each stage loads the
next stage from disc and jumps. The exact mapping (what the BIOS does with
this header, what each stage loads where) must be measured in a debugger
(e.g. PCSX-Redux) before any `vram:` in a splat config is trusted.

## 4. Disc contents (Japan tree, abbreviated)

* `SLPS_002.70;1`, `MAINMENU.EXE;1` at the root
* `DRAGOON/` — `G3.EXE`, `TIM.DAT`, `TMD.DAT`, briefing/ending STR video,
  per-character `*.DAT` (FRANK/JOHNSON/REIKO/SHARK), demo scripts
* `GOURB/` — `G3ORG.EXE`, `G3ORG.STR` (153 MB), `TIM?ORG.DAT`, `TMD1ORG.DAT`
* root — `LOGO.STR`, `MISSION.STR`, `MIN3.DA` (XA audio), `MTIM?.DAT`,
  `SE.VB`/`SE.VH` (sound bank), `TIM.DAT`, `TMD.DAT`
* Europe adds localized variants (e.g. `BRIEFE.STR` vs `BRIEFN.STR`)

## 5. Toolchain fingerprint (Phase 1, first evidence)

Inside `SLPS_002.70`:

```
$Id: intr.c,v 1.71 1995/08/29 11:01:44 suzu Exp $
$Id: sys.c,v 1.109 1995/10/26 13:06:43 suzu Exp $
```

Sony Psy-Q kernel RCS tags date the linked SDK to **October 1995** —
Psy-Q 3.x vintage. Working hypothesis: **GCC 2.6.3** (the Psy-Q default of
that era; same as lsddecomp). This is a hypothesis, not a measurement: the
revision gets pinned only after the compiler-idiom fingerprint pass
(Phase 1 §3.2 of docs/WORKFLOW.md) and stays pinned thereafter.

Expected Psy-Q libraries (to confirm from import data): libapi, libetc,
libcd, libcard, libgpu, libgs, libgte, libspu, libsnd, libpress, libc2.

## 6. Immediate next steps

1. Debugger session (PCSX-Redux): measure what the BIOS does with this
   header, where each stage actually loads, and the RAM map of each stage.
2. Identify `SLPS_002.70`'s structure: it is mostly the loader stub plus
   Sony library objects — decide the SDK-object strategy (link Sony's
   objects, LSD-style) versus decompiling the kernel glue.
3. Compile-idiom pass to pin the compiler revision; write the facts into
   the splat configs and setup scripts.
4. First split of the primary target once the layout is proven; from
   there, the round-trip oracle (`make verify`) gates everything.
