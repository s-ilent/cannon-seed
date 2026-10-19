#!/usr/bin/env python3
"""flip_reauthor.py - the de-frame flip's re-authoring step.

Maps every woven-space VA in config/symbols.curated.txt and
config/symbols.<t>.txt to its true (de-framed) VA using the same framing
math as tools/deframe_migrate.py (which already migrated the yaml rows).
Flips the slps gp_value per the owner's checklist (0x8006322C ->
0x8006632C), refreshes the migrated yamls' header comments, and proves
every re-authored symbols entry lands inside the migrated yaml row set.

Inputs:  woven baselines (baselines/<t>.bin, still in place pre-swap),
         migrated yamls (build/work/true/yamls/splat.<t>.yaml)
Outputs: build/work/flip/{symbols.curated.txt, symbols.<t>.txt,
         splat.<t>.yaml, sha1/<t>.sha1}
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/cannon-seed")
sys.path.insert(0, str(REPO / "tools"))
import deframe_migrate as dm  # noqa: E402

BASE = 0x80020000
TARGETS = dm.TARGETS
TRUE_SHA1 = {
    "slps_00270": "fa9474b4e6ecf08e0bfc182fee776cf71f6d8195",
    "sces_00269": "06b4bda68dce0f3734cfb7cbb76913a6e7fa2dc9",
    "mainmenu_jp": "d637286a60e36dfeee10c0441509c98b2f952d48",
    "mainmenu_eu": "f9f29eebb419b5e957ce2389d33caeedbb93685e",
    "g3_jp": "994a680cd139069404e5c6d6c51d3796a728f2ec",
    "g3_eu": "39030a759e8462575b709f77eed1050f7bbaa572",
    "g3org_jp": "2b2a42250b9fe8849bbd791515ce341a678ddef0",
    "g3org_eu": "01b37b4e01afe69acd2a46e69359dadd4a20877b",
}
GP_FLIP = {"slps_00270": ("0x8006322C", "0x8006632C")}
# The boots' small-data class (the flip's last stall, closed this window):
# entries recorded from the retail gp-relative encodings with the CARVE gp
# substituted - the woven view's lie. Their true addresses come from the
# banked slot maps (docs/TASKS.md "the definitive slot map", content-
# correlated), NOT from the framing math: the carve-gp window's bytes are
# late woven data whose true home is ~0x3100 BELOW the retail window, which
# lives in the never-woven-captured tail. Re-point is pure gp arithmetic:
#   true = true_gp + (va - carve_gp)
# Witness: boot_flag_0's C store is retail 0x3C($gp) -> true 0x80066368
# (slot-map gp+0x3C = 1, the measured 0/1 word flag); boot_flag_1 = gp+0x68
# -> 0x80066394 (slot-map 0). GP_INFO then keeps the compiled form
# (func_80025AE0 stays 0x10, RotTransPers4 stays 0x80). sces's window has
# no symbol entries (no C references to its statics): nothing to repoint.
GP_REPOINT = {"slps_00270": (0x8006322C, 0x8006632C, 0xE0)}
# The curated-table retail-bound class (docs/TASKS.md 2026-10-19, the
# sces_00269 pilot, first flipped-era GREEN): entries RETAIL CODE
# REFERENCES (C %hi/%lo pairs, stopIntr's no-arg jals) must keep the
# retail-encoded address. Retail runtime encodings are layout-invariant -
# the flip re-places rows in the FILE, it does not change what the retail
# code encodes - so reference resolution binds to the retail encodings,
# NOT to row-position arithmetic; the framing re-point of this class broke
# 33 retail bytes across two waves (4 + 3 names) before the restoration.
# Values = the pre-flip entries (the woven pipeline resolved at retail
# encodings all along). intr_stop_commit additionally needs
# allow_duplicated:True on both sides in the symbols file: it shares
# 0x8002F458 with the re-pointed psyq pin ResetEntryInt - the row-name
# class and the retail-encoded class legitimately coincide post-flip
# (pre-flip they sat at different addresses: 0x80031928 vs 0x8002F458).
# The woven row names whose yaml rows migrated away from their name
# addresses (the glabel-dupe census class) are adjudicated at the yaml
# layer instead: the row becomes <name>.rowdef and the name belongs to
# the definition at the retail-encoded position (sces_00269 pilot, 8 rows).
RETAIL_BOUND = {
    "sces_00269": {
        "video_mode": 0x8004CF20,
        "_spu_inTransfer": 0x80065A68,
        "intr_stop_begin": 0x8002F388,
        "intr_stop_commit": 0x8002F458,
        "intr_active_flag": 0x8004CF24,
        "intr_saved_mask": 0x8004CF56,
        "intr_saved_dicr": 0x8004CF58,
    },
}
# The rehearsal's alias-adjudication layer (docs/TASKS.md 2026-10-18, banked
# policy: psyq name wins, the intr_* alias retires with a provenance note;
# C sources reference none of the collided names - grep-verified). These
# curated psyq member placements (HookEntryInt/ResetEntryInt/_96_remove,
# recorded already-true) and the scanner's intr_* labels (mapped from the
# carve) land on the same true bytes in mainmenu_eu. (target, alias, va):
# the GEN-file alias line retires; the curated psyq entry labels the bytes.
ALIAS_ADJUDICATE = {
    "mainmenu_eu": [("intr_restart_begin", "HookEntryInt", 0x8005F2A0),
                    ("intr_stop_commit", "ResetEntryInt", 0x8005F2F0),
                    ("intr_start_aux6", "_96_remove", 0x8005F370)],
}
ENTRY_RE = re.compile(r"^(\s*[A-Za-z_]\w*\s*=\s*0x)([0-9A-Fa-f]+)(\s*;.*)$")


def framing(target):
    # post-swap baselines/<t>.bin are TRUE files (no framing); the woven
    # baselines live in the backup dir for exactly this reason.
    return dm.Framing(REPO / "build" / "work" / "woven" / f"{target}.bin", None)


def map_va(va, fw):
    """woven carve VA -> true carve VA (snap-forward on framing)."""
    off = (va - BASE) + dm.HEADER
    snapped = not fw.is_data(off)
    return BASE + (fw.true_of(off) - dm.HEADER), snapped


def yaml_rows(target):
    """name -> (off, size) from the migrated yaml's generated block."""
    rows = {}
    ypath = dm.OUT_DIR / "yamls" / f"splat.{target}.yaml"
    for m in re.finditer(r"^\s*-\s*\[(0x[0-9A-Fa-f]+),\s*(\w+),\s*(\w+)\]"
                         r"\s*#\s*(0x[0-9A-Fa-f]+)", ypath.read_text(), re.M):
        rows[m.group(3)] = (int(m.group(1), 16), int(m.group(4), 16))
    return rows


def dropped_rows(target):
    """Names of MIGRATE-DROPPED rows (pure framing, 0 true bytes). Their
    labels refer to bytes that do not exist in the true view - symbol
    entries bearing such names must die with the row (the snap-identity
    rule would otherwise keep them at their carve VAs, clashing with the
    surviving neighbours' mapped starts: data_8005A014 vs func_80062B04)."""
    ypath = dm.OUT_DIR / "yamls" / f"splat.{target}.yaml"
    return set(re.findall(r"MIGRATE-DROPPED[^\n]*-\s*\[0x[0-9A-Fa-f]+, \w+, (\w+)\]",
                          ypath.read_text()))


def check_entry(target, name, new_va, rows):
    """Every re-authored entry must sit at/inside the migrated rows.
    Row offsets are FILE offsets (header 0x800 included); new_va is a
    carve/runtime VA, so convert through the 0x800 header."""
    p = (new_va - BASE) + dm.HEADER
    if name in rows:
        off, size = rows[name]
        if p != off:
            raise SystemExit(f"{target}: {name} -> 0x{new_va:X} but yaml row "
                             f"starts 0x{off:X}")
        return "row-start"
    for off, size in rows.values():
        if off <= p < off + size:
            return "contained"
    raise SystemExit(f"{target}: {name} -> 0x{new_va:X} lands in no row")


def entry_name(line):
    m = re.match(r"\s*([A-Za-z_]\w*)\s*=", line)
    return m.group(1) if m else ""


def map_symbols_text(target, text, fw, rows, max_off, dropped, adjudicate):
    out, n, snaps, classes = [], 0, [], {}
    enc = re.compile(r"^(func|D)_[0-9A-F]{8}$")
    mapped_vas = set()
    for line in text.splitlines():
        m = ENTRY_RE.match(line)
        if m:
            va = int(m.group(2), 16)
            name = entry_name(line)
            if name in rows:
                # row name: the yaml row's own (tool-mapped) start wins.
                new_va, sn = map_va(va, fw)
                cls = check_entry(target, name, new_va, rows)
                classes[cls] = classes.get(cls, 0) + 1
                if sn:
                    snaps.append((name, va, new_va))
                mapped_vas.add(new_va)
                out.append(f"{m.group(1)}{new_va:X}{m.group(3)}")
                n += 1
                continue
            if name in dropped:
                # the row this label named was pure framing and died in
                # migration - the label has no true existence; retire it.
                classes["dropped-row-label"] = \
                    classes.get("dropped-row-label", 0) + 1
                out.append(f"// FLIP-DROPPED-ROW (pure framing): {line.strip()}")
                continue
            if name in adjudicate:
                winner = adjudicate[name][0]
                if va == adjudicate[name][1]:
                    classes["alias-retired"] = \
                        classes.get("alias-retired", 0) + 1
                    out.append(f"// FLIP-ALIAS (retired: psyq member {winner} "
                               f"owns these bytes): {line.strip()}")
                    continue
            if target in GP_REPOINT:
                cg, tg, win = GP_REPOINT[target]
                if cg <= va < cg + win:
                    # gp-relative small-data static: re-point through the
                    # slot-map gp arithmetic (see GP_REPOINT note).
                    new_va = tg + (va - cg)
                    cls = check_entry(target, name, new_va, rows)
                    classes["gp-repointed"] = classes.get("gp-repointed", 0) + 1
                    if new_va in mapped_vas:
                        raise SystemExit(f"{target}: gp-repoint clash {name} "
                                         f"at 0x{new_va:X}")
                    mapped_vas.add(new_va)
                    out.append(f"{m.group(1)}{new_va:X}{m.group(3)}")
                    n += 1
                    continue
            if va == RETAIL_BOUND.get(target, {}).get(name):
                # retail-bound curated entry: the retail bytes encode this
                # exact address (see the RETAIL_BOUND note) - pass through
                # verbatim; the framing re-point would break the encoding.
                if va in mapped_vas:
                    classes["retail-bound-dupe-dropped"] = \
                        classes.get("retail-bound-dupe-dropped", 0) + 1
                    out.append(f"// FLIP-DUPE (dropped): {line.strip()}")
                    continue
                mapped_vas.add(va)
                out.append(line)
                classes["retail-bound"] = classes.get("retail-bound", 0) + 1
                n += 1
                continue
            if ((va - BASE) + dm.HEADER >= max_off
                    or (enc.match(name) and int(name[-8:], 16) == va)):
                # beyond-payload symbol (BIOS region, scratchpad), or an
                # ADDRESS-ENCODED branch-target name: the retail bytes'
                # own j/jal words encode RUNTIME = true addresses, and the
                # flip makes carve = runtime - pass through verbatim.
                if va in mapped_vas:
                    # a mapped (established) name already labels these true
                    # bytes - the duplicate would trip splat. Established
                    # name wins; spimdisasm re-emits references to it.
                    classes["ident-dupe-dropped"] = \
                        classes.get("ident-dupe-dropped", 0) + 1
                    out.append(f"// FLIP-DUPE (dropped): {line.strip()}")
                    continue
                mapped_vas.add(va)
                out.append(line)
                classes["identity-true"] = classes.get("identity-true", 0) + 1
                continue
            new_va, sn = map_va(va, fw)
            if sn and name not in rows:
                # woven position is framing: the entry is an ALREADY-TRUE
                # address (recorded from the binary's own encodings) - keep
                # it verbatim (identity). Snapping would corrupt it.
                if new_va in mapped_vas:
                    classes["ident-dupe-dropped"] = \
                        classes.get("ident-dupe-dropped", 0) + 1
                    out.append(f"// FLIP-DUPE (dropped): {line.strip()}")
                    continue
                classes["identity-true"] = classes.get("identity-true", 0) + 1
                mapped_vas.add(va)
                out.append(line)
                continue
            cls = check_entry(target, name, new_va, rows)
            classes[cls] = classes.get(cls, 0) + 1
            if sn:
                snaps.append((name, va, new_va))
            if new_va in mapped_vas:
                raise SystemExit(f"{target}: mapped clash {name} at "
                                 f"0x{new_va:X}")
            mapped_vas.add(new_va)
            out.append(f"{m.group(1)}{new_va:X}{m.group(3)}")
            n += 1
        else:
            out.append(line)
    return "\n".join(out) + "\n", n, snaps, classes


def git_read(rel: str) -> str:
    """Read a config input from git HEAD - the script must always map the
    ORIGINAL woven-space files (running it twice on its own output would
    double-map)."""
    r = subprocess.run(["git", "-C", str(REPO), "show", f"HEAD:{rel}"],
                       capture_output=True, text=True, check=True)
    return r.stdout


def main():
    outdir = REPO / "build" / "work" / "flip"
    (outdir / "sha1").mkdir(parents=True, exist_ok=True)
    total = {}
    for t in TARGETS:
        fw = framing(t)
        rows = yaml_rows(t)
        dropped = dropped_rows(t)
        ADJUDICATE = {a: (w, v) for a, w, v in ALIAS_ADJUDICATE.get(t, [])}
        max_off = (REPO / "build" / "work" / "woven" / f"{t}.bin").stat().st_size
        # per-target symbols file
        spath = f"config/symbols.{t}.txt"
        new, n, snaps, classes = map_symbols_text(t, git_read(spath), fw,
                                                  rows, max_off, dropped,
                                                  ADJUDICATE)
        (outdir / f"symbols.{t}.txt").write_text(new)
        total[t] = [n, len(snaps), classes]
        # oracle staging
        (outdir / "sha1" / f"{t}.sha1").write_text(
            f"# config/sha1/{t}.sha1 - THE ORACLE for target '{t}'\n"
            f"# TRUE (de-framed) baseline oracle: the flip commit re-baselines\n"
            f"# this file from the woven hash to the per-sector true EXE hash\n"
            f"# banked in docs/TASKS.md and witnessed 8/8 on the re-fetched\n"
            f"# discs. One deliberate --no-verify flip commit, per checklist.\n"
            f"{TRUE_SHA1[t]}  baselines/{t}.bin\n")
    # curated file: ONE pass, each entry mapped with its own scope's framing
    framings = {t: framing(t) for t in TARGETS}
    ctx = {t: (yaml_rows(t), dropped_rows(t),
               (REPO / "build" / "work" / "woven" / f"{t}.bin").stat().st_size)
           for t in TARGETS}
    cpath = "config/symbols.curated.txt"
    scope, counts = None, {t: 0 for t in TARGETS}
    out = []
    for line in git_read(cpath).splitlines():
        ms = re.match(r"\s*//\s*target:\s*(\w+)", line)
        if ms:
            scope = ms.group(1)
            out.append(line)
            continue
        m = ENTRY_RE.match(line)
        if m and scope in ctx:
            rows, dropped, max_off = ctx[scope]
            va0 = int(m.group(2), 16)
            name = entry_name(line)
            enc = re.compile(r"^(func|D)_[0-9A-F]{8}$")
            if name in dropped:
                out.append(f"// FLIP-DROPPED-ROW (pure framing): {line.strip()}")
                continue
            if ((va0 - BASE) + dm.HEADER >= max_off
                    or (name and enc.match(name)
                        and int(name[-8:], 16) == va0)):
                # beyond-payload, or address-encoded branch target
                # (runtime value) - identity.
                out.append(line)
                continue
            if scope in GP_REPOINT:
                cg, tg, win = GP_REPOINT[scope]
                if cg <= va0 < cg + win:
                    # gp-relative small-data static (see GP_REPOINT note).
                    new_va = tg + (va0 - cg)
                    check_entry(scope, name, new_va, rows)
                    print(f"  curated gp-repoint {scope}: {name} "
                          f"0x{va0:X} -> 0x{new_va:X}")
                    out.append(f"{m.group(1)}{new_va:X}{m.group(3)}")
                    counts[scope] += 1
                    continue
            new_va, sn = map_va(va0, framings[scope])
            if sn and name not in rows:
                # woven framing position: already-true address (binary's
                # own encodings) - identity, judge sweep reviews.
                out.append(line)
                continue
            check_entry(scope, name, new_va, rows)
            if sn:
                print(f"  curated snap {scope}: {m.group(1).strip()} "
                      f"-> 0x{new_va:X}")
            out.append(f"{m.group(1)}{new_va:X}{m.group(3)}")
            counts[scope] += 1
        else:
            out.append(line)
    (outdir / "symbols.curated.txt").write_text("\n".join(out) + "\n")
    # yaml polish: gp flip + header truth (the migrated yamls are staging)
    for t in TARGETS:
        ypath = dm.OUT_DIR / "yamls" / f"splat.{t}.yaml"
        ytext = ypath.read_text()
        if t in GP_FLIP:
            old, new = GP_FLIP[t]
            if f"gp_value: {old}" in ytext:
                ytext = ytext.replace(f"gp_value: {old}", f"gp_value: {new}")
            else:
                assert f"gp_value: {new}" in ytext, \
                    f"{t}: neither gp_value {old} nor {new} present"
        ytext = ytext.replace("# true file: build/work/true/",
                              "# true file: baselines/")
        ytext = re.sub(r"# SHA-1: [0-9a-f]{40} \(config/sha1/[^)]+\)",
                       f"# SHA-1: {TRUE_SHA1[t]} (config/sha1/{t}.sha1, the "
                       f"true de-framed baseline)", ytext)
        ypath.write_text(ytext)
    for t, v in total.items():
        print(f"{t}: symbols {v[0]} entries ({v[2]}), {v[1]} snaps, "
              f"curated {counts[t]} mapped")
    print("staged to build/work/flip/")


if __name__ == "__main__":
    main()

# --- post-step (idempotent): extend each migrated last row to the true
# file end. The migrate tool stops the last row at the woven capture point
# (a lower bound); with the true baselines on disc the tail is real content
# the build must reproduce (extract re-emits the last .data.s from the true
# file), so the last row spans to the segment end like the woven yaml did.
def extend_last_rows():
    import re as _re
    for t in TARGETS:
        fsize = (REPO / "build" / "work" / "true" / f"{t}.bin").stat().st_size
        yp = dm.OUT_DIR / "yamls" / f"splat.{t}.yaml"
        txt = yp.read_text()
        m = list(_re.finditer(r"^(      - \[(0x[0-9A-Fa-f]+), \w+, \w+\])   # (0x[0-9A-Fa-f]+)$", txt, _re.M))
        last = m[-1]
        off = int(last.group(2), 16); size = int(last.group(3), 16)
        new_size = fsize - off
        if size != new_size:
            txt = txt[:last.start(3)] + f"0x{new_size:X}" + txt[last.end(3):]
            yp.write_text(txt)
        print(f"{t}: last row 0x{off:X} size 0x{size:X} -> 0x{new_size:X} (end 0x{off+new_size:X})")

if "extend" in sys.argv:
    extend_last_rows()

def fix_c_references():
    """Identity/curated names dedupe-dropped against row labels: rewrite
    C references to the winning row name - but ONLY in files the dropping
    target builds (a yaml row named after the file stem). The same src
    file can be built by several targets; in a non-dropping target the
    alias survives in that target's own map, and the winner label exists
    only in the dropping target's map - a global rewrite would break the
    other targets' links with an undefined reference. The compiled
    encoding depends only on the address (identical), never the label."""
    import re as _re
    total = 0
    srcdir = REPO / "src"
    for t in TARGETS:
        staged = (REPO / "build" / "work" / "flip" / f"symbols.{t}.txt").read_text()
        rows = yaml_rows(t)  # name -> (file off, size)
        built = set(rows)    # a c row's name is its src/ file stem
        # winner names by true VA
        va_of_row = {BASE + (off - dm.HEADER): name for name, (off, _s) in rows.items()}
        drops = _re.findall(r"^// FLIP-DUPE \(dropped\): (\w+) = (0x[0-9A-Fa-f]+);", staged, _re.M)
        for name, vas in drops:
            va = int(vas, 16)
            winner = va_of_row.get(va)
            if winner is None:
                print(f"  {t}: {name} dropped at 0x{va:X} - no row label, "
                      f"NEEDS MANUAL REVIEW")
                continue
            for f in srcdir.glob("*.c"):
                if f.stem not in built:
                    continue
                txt = f.read_text()
                if _re.search(rf"\b{name}\b", txt):
                    new = _re.sub(rf"\b{name}\b", winner, txt)
                    f.write_text(new)
                    print(f"  {t}: {f.name}: {name} -> {winner}")
                    total += 1
    print(f"C reference rewrites: {total}")

if "fixc" in sys.argv:
    fix_c_references()
