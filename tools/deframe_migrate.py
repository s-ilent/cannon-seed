#!/usr/bin/env python3
"""deframe_migrate.py - migrate splat subsegment offsets from the woven
framed baseline layout to the true (de-framed) file layout.

WHY
  `baselines/*.bin` are contiguous raw reads of MODE2/2352 sectors: the
  0x800-byte PS-X EXE header, then 2352-byte sectors whose 2048-byte data
  areas carry the true file bytes and whose 304-byte gaps (280-byte EDC/ECC
  tail + 24-byte sync/address/mode/subheader) are framing with no runtime
  address. config/splat.<t>.yaml addresses that woven file linearly, so the
  carve VA of a byte differs from its true runtime VA by the framing drift -
  the lying view the de-frame transition replaces.

THE MATH (measured per file via tools/deframe.py; nothing hardcoded)
  first  = offset of the first MODE2 sync (0x918 on all 8 retail baselines)
  start  = first + 24 = 0x930        (the first sector's data area)
  sector m data area = framed [start + m*2352, start + m*2352 + 2048)
  and holds true file bytes [0x800 + m*2048, 0x800 + (m+1)*2048).
  So for a framed offset o inside a data area:
      true_offset(o) = 0x800 + ((o - start) // 2352) * 2048 + ((o - start) % 2352)
  which equals deframe.py's own mapping: `0x800 + framed_to_runtime(o) -
  0x80020000` for the carve vram `0x80020000 + (o - 0x800)` (the tool
  cross-checks both, and re-verifies the byte identity against the
  `--payload` join over every captured data byte).

ROW SEMANTICS
  A row [o, type, name] is a byte window; migration re-expresses the SAME
  LOGICAL BYTES at their true offsets:
    new_off  = offset of the first data byte at or after o (a row starting
               in framing snaps forward; the snap is reported)
    new_size = data bytes inside the woven span [o, next_o) =
               old_size - framing bytes inside the span
  A row that is 100% framing has zero true bytes and is DROPPED in write
  mode (the true file contains no such bytes). The last row of every target
  ends at the local truncation point: the baseline's tail user data is
  disc-only, so that extent is a lower bound and the shortfall vs the
  header's t_size is reported per target.

USAGE
  python3 tools/deframe_migrate.py --target slps_00270             # dry-run
  python3 tools/deframe_migrate.py --all                           # all 8
  python3 tools/deframe_migrate.py --target slps_00270 --write     # emit yaml
  python3 tools/deframe_migrate.py --all --write --spotcheck

  Dry-run writes build/work/true/impact.<t>.txt (the full old->new table)
  and prints a one-screen summary. --write emits migrated yamls to
  build/work/true/yamls/splat.<t>.yaml (NEVER in place) with target_path
  rewritten to the true baseline. --spotcheck proves sampled rows byte for
  byte against the true baseline (needs build/work/true/<t>.bin; regenerate
  with `python3 tools/deframe.py --payload <t> build/work/true/<t>.bin`).
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"
OUT_DIR = REPO / "build" / "work" / "true"
TARGETS = ["slps_00270", "sces_00269", "mainmenu_jp", "mainmenu_eu",
           "g3_jp", "g3_eu", "g3org_jp", "g3org_eu"]

HEADER = 0x800          # PS-X EXE header: true [0, 0x800), verbatim in the woven file
HDR = 24                # sync(12) + address(3) + mode(1) + subheader(8)
DATA = 2048             # MODE2 Form 1 data area
SECTOR = 2352           # MODE2/2352
SYNC = bytes.fromhex("00ffffffffffffffffffff00")

# emitted by tools/scan_functions.py: `- [0xNNN, type, name]   # <size hex>[ marker]`
ROW_RE = re.compile(
    r"^(?P<indent>\s*- \[)0x(?P<off>[0-9A-Fa-f]+)"
    r"(?P<mid>,\s*(?P<typ>\w+),\s*(?P<name>[\w.]+)\]\s*#\s*)"
    r"0x(?P<size>[0-9a-fA-F]+)(?P<mark>\s*(?:pinned|sdk|noseed)?)\s*$")


def load_deframe():
    """Import tools/deframe.py (needs pyyaml); None when unavailable."""
    try:
        sys.path.insert(0, str(TOOLS))
        import deframe  # noqa: E402
        return deframe
    except Exception:
        return None


class Framing:
    """The measured weave of one framed baseline: first sync + sector math."""

    def __init__(self, baseline: Path, dmod):
        if dmod is not None:
            lay = dmod.layout(baseline)
            self.first, self.period = lay["first"], lay["period"]
        else:                       # fallback: same measurement, no yaml dep
            d = baseline.read_bytes()
            self.first = d.find(SYNC)
            if self.first < 0:
                raise SystemExit(f"{baseline}: no MODE2 sync pattern")
            offs, i = [], self.first
            while i >= 0:
                offs.append(i)
                i = d.find(SYNC, i + 1)
            if {offs[k + 1] - offs[k] for k in range(len(offs) - 1)} != {SECTOR}:
                raise SystemExit(f"{baseline}: irregular framing")
            self.period = SECTOR
        if self.period != SECTOR:
            raise SystemExit(f"{baseline}: unexpected sector period {self.period}")
        self.start = self.first + HDR          # first data area (0x930 measured)

    def is_data(self, o: int) -> bool:
        """True when framed offset o holds true file content (data area)."""
        if o < HEADER or o < self.start:
            return False
        return (o - self.start) % SECTOR < DATA

    def true_of(self, o: int) -> int:
        """True offset of the first data byte at framed >= o (snap forward)."""
        if o <= HEADER:
            return HEADER
        if o < self.start:
            return HEADER
        k, into = divmod(o - self.start, SECTOR)
        if into < DATA:
            return HEADER + k * DATA + into
        return HEADER + (k + 1) * DATA


def parse_rows(yaml_path: Path):
    """[(offset, type, name)] of the code segment, plus the trailing size
    marker (the last `- [0xNNN]` bare segment = the file length)."""
    cfg = yaml.safe_load(yaml_path.read_text())
    segs = cfg["segments"]
    code = [s for s in segs if isinstance(s, dict) and s.get("type") == "code"]
    if len(code) != 1:
        raise SystemExit(f"{yaml_path}: expected exactly one code segment")
    rows = []
    for e in code[0].get("subsegments", []):
        if not isinstance(e, list) or len(e) != 3:
            raise SystemExit(f"{yaml_path}: unexpected subsegment {e!r}")
        rows.append((int(e[0]), str(e[1]), str(e[2])))
    marker = None
    for s in segs:
        if isinstance(s, list) and len(s) == 1:
            marker = int(s[0])
    if marker is None:
        raise SystemExit(f"{yaml_path}: no trailing size marker")
    return rows, marker


def plan_rows(rows, marker, fw: Framing):
    """Per-row migration plan; raises on any structural violation."""
    out = []
    if rows[0][0] != HEADER:
        raise SystemExit(f"first row starts at 0x{rows[0][0]:X}, expected 0x800")
    for i, (o, typ, name) in enumerate(rows):
        e = rows[i + 1][0] if i + 1 < len(rows) else marker
        if e <= o:
            raise SystemExit(f"row {name}: non-increasing span 0x{o:X}..0x{e:X}")
        if o < HEADER:
            raise SystemExit(f"row {name}: starts inside the EXE header")
        new_off = fw.true_of(o)
        new_size = fw.true_of(e) - new_off
        old_size = e - o
        out.append({
            "name": name, "type": typ,
            "old_off": o, "old_size": old_size,
            "new_off": new_off, "new_size": new_size,
            "framing": old_size - new_size,
            "snapped": not fw.is_data(o),
            "dropped": new_size == 0,
            "idx": i,
        })
    # the kept rows must tile the true payload exactly (no gap, no overlap)
    kept = [r for r in out if not r["dropped"]]
    if kept and kept[0]["new_off"] != HEADER:
        raise SystemExit("migration broke the first row's true offset")
    for a, b in zip(kept, kept[1:]):
        if a["new_off"] + a["new_size"] != b["new_off"]:
            raise SystemExit(f"gap/overlap after row {a['name']} in the true view")
    if fw.true_of(marker) != kept[-1]["new_off"] + kept[-1]["new_size"]:
        raise SystemExit("migration does not reach the local truncation point")
    return out


def true_sizes(target: str):
    """(t_size from the baseline header, local true payload length)."""
    b = (REPO / "baselines" / f"{target}.bin").read_bytes()
    t_size = int.from_bytes(b[0x1C:0x20], "little")
    tf = OUT_DIR / f"{target}.bin"
    local = (len(tf.read_bytes()) - HEADER) if tf.is_file() else None
    return t_size, local


def cross_check(target: str, fw: Framing, dmod, rows) -> str:
    """Verify the mapping two ways; returns a one-line evidence string."""
    baseline = REPO / "baselines" / f"{target}.bin"
    framed = baseline.read_bytes()
    # (1) own true_of() vs deframe.py's framed_to_runtime at every row start
    n_map = 0
    if dmod is not None:
        for o, _t, _n in rows:
            vram = 0x80020000 + (o - HEADER)
            r = dmod.framed_to_runtime(baseline, vram)
            expect = None if r is None else HEADER + (r - 0x80020000)
            mine = fw.true_of(o)
            if r is not None:
                assert mine == expect, (o, mine, expect)
                n_map += 1
    # (2) byte identity: the woven data areas join to the deframe --payload
    tf = OUT_DIR / f"{target}.bin"
    if tf.is_file():
        payload = tf.read_bytes()[HEADER:]
        n_bytes = 0
        for k in range(len(payload) // DATA + 1):
            ko = fw.start + k * SECTOR
            kb = payload[k * DATA:(k + 1) * DATA]
            if not kb:
                break
            # the true file may extend past the woven baseline's truncation
            # point: compare only the overlap (every CAPTURED data byte).
            seg = framed[ko:ko + len(kb)]
            if not seg:
                break
            if seg != kb[:len(seg)]:
                raise SystemExit(f"{target}: mapping mismatch at sector {k}")
            n_bytes += len(seg)
        return f"mapping OK ({n_map} row starts vs deframe.py; {n_bytes} bytes re-verified)"
    return f"mapping OK ({n_map} row starts vs deframe.py; --payload output absent)"


def write_impact(target: str, plan, marker, t_size, local, fw, evidence, summary) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p = OUT_DIR / f"impact.{target}.txt"
    lines = [
        f"# deframe_migrate impact table - {target}",
        f"# framed baseline: baselines/{target}.bin (first sync 0x{fw.first:X}, "
        f"data start 0x{fw.start:X}, file 0x{marker:X} B)",
        f"# true file: build/work/true/{target}.bin "
        f"(t_size 0x{t_size:X} = {t_size} B; local payload "
        + (f"0x{local:X} B)" if local is not None else "absent)"),
        f"# {evidence}",
        f"# {summary}",
        "#",
        "# idx  type  name                  old_off   old_size  new_off   new_size"
        "  framing  note",
    ]
    for r in plan:
        note = []
        if r["dropped"]:
            note.append("PURE-FRAMING(dropped)")
        elif r["snapped"]:
            note.append("start-snapped")
        if r["framing"] and not r["dropped"]:
            note.append(f"-{r['framing']}B")
        lines.append(
            f"{r['idx']:5d}  {r['type']:4s}  {r['name']:20s}  "
            f"0x{r['old_off']:06X}  0x{r['old_size']:06X}  0x{r['new_off']:06X}  "
            f"0x{r['new_size']:06X}  {r['framing']:7d}  {' '.join(note)}")
    # tail accounting: what the true file needs beyond the local truncation
    last = plan[-1]
    shortfall = HEADER + t_size - (last["new_off"] + last["new_size"])
    lines.append("")
    lines.append(f"# last row '{last['name']}' ends at 0x{last['new_off']+last['new_size']:X}; "
                 f"true end 0x{HEADER+t_size:X}; disc-only tail shortfall {shortfall} B")
    p.write_text("\n".join(lines) + "\n")
    return p


def summarize(target: str, plan, marker, t_size, local, fw, evidence) -> str:
    kept = [r for r in plan if not r["dropped"]]
    dropped = [r for r in plan if r["dropped"]]
    framing = sum(r["framing"] for r in plan)
    moved = sum(1 for r in plan if r["new_off"] != r["old_off"])
    by_type = {}
    for r in plan:
        t = by_type.setdefault(r["type"], [0, 0, 0])
        t[0] += 1
        if r["framing"]:
            t[1] += 1
        t[2] += r["framing"]
    old_total = sum(r["old_size"] for r in plan)
    new_total = sum(r["new_size"] for r in plan)
    short = HEADER + t_size - (local + HEADER) if local is not None else None
    lines = [
        f"{target}: rows {len(plan)} -> {len(kept)} kept, {len(dropped)} dropped "
        f"(pure framing); offsets moved {moved}; framing removed {framing} B",
        f"  extents: old {old_total} B -> new {new_total} B "
        f"(delta {new_total-old_total:+d})",
        "  rows carrying framing: "
        + ", ".join(f"{t} {v[1]}/{v[0]} ({v[2]} B)" for t, v in sorted(by_type.items())),
        f"  {evidence}",
    ]
    if short:
        lines.append(f"  TRUNCATED: local true payload {local} B vs t_size {t_size} B; "
                     f"disc-only tail {short} B (last row extent is a lower bound)")
    return "\n".join(lines)


def migrate_yaml(target: str, src: Path, plan, marker, t_size, local, target_path: str,
                 summary: str) -> Path:
    """Rewrite the yaml text line by line: rows in block order, everything
    else untouched (comments, options, markers survive byte for byte).

    The trailing size marker and the last row's extent are set to the LOCAL
    true file's end: splat uses the marker as the carve boundary, so a marker
    that reaches past the truncated placeholder makes the split read past EOF.
    Re-running this tool after the disc tails are restored recomputes both.
    """
    text = src.read_text()
    out, pi = [], 0
    for ln in text.split("\n"):
        m = ROW_RE.match(ln)
        if not m:
            out.append(ln)
            continue
        if pi >= len(plan):
            raise SystemExit(f"{target}: more row lines than planned rows: {ln!r}")
        r = plan[pi]
        if (m.group("name") != r["name"] or m.group("typ") != r["type"]
                or int(m.group("off"), 16) != r["old_off"]):
            raise SystemExit(f"{target}: row line mismatch: {ln!r} vs {r}")
        pi += 1
        if r["dropped"]:
            out.append("# MIGRATE-DROPPED (pure framing, 0 true bytes): " + ln)
        else:
            out.append(f"{m.group('indent')}0x{r['new_off']:X}"
                       f"{m.group('mid')}0x{r['new_size']:x}{m.group('mark')}")
    if pi != len(plan):
        raise SystemExit(f"{target}: matched {pi} row lines, expected {len(plan)}")
    text = "\n".join(out)
    # target_path -> the true baseline
    text, n = re.subn(r"^(\s*target_path:\s*)\S+.*$", r"\g<1>" + target_path,
                      text, count=1, flags=re.M)
    if n != 1:
        raise SystemExit(f"{target}: could not rewrite target_path")
    # trailing size marker: the LOCAL true file length (0x800 + local payload)
    end = HEADER + (local if local is not None else t_size)
    note = ("" if local is None or local == t_size else
            f"  # local truncation; true end 0x{HEADER+t_size:X} "
            f"(disc-only tail {t_size - local} B; re-run after restoring it)")
    text, n = re.subn(r"^(\s*- \[)0x[0-9A-Fa-f]+(\])", rf"\g<1>0x{end:X}\g<2>{note}",
                      text, count=1, flags=re.M)
    if n != 1:
        raise SystemExit(f"{target}: could not rewrite the size marker")
    prov = [
        "  # -------------------------------------------------------------------",
        "  # MIGRATED to the true (de-framed) file layout by tools/deframe_migrate.py",
        f"  # from config/splat.{target}.yaml + baselines/{target}.bin.",
        "  # Row offsets are TRUE file offsets (header 0x800 + payload); the carve",
        "  # VA now equals the runtime VA. Row names keep their woven-era spelling.",
        "  # " + summary.split("\n")[0],
        "  # " + summary.split("\n")[1].strip(),
    ]
    if "TRUNCATED" in summary:
        prov.append("  # " + [l for l in summary.split("\n") if "TRUNCATED" in l][0].strip())
        prov.append("  # The last row and the size marker end at the LOCAL truncation;")
        prov.append("  # splat uses the marker as the carve boundary, so both must be")
        prov.append("  # extended (or this tool re-run) once the disc tails are restored.")
    prov += [
        "  # config/symbols.<t>.txt MIXES address spaces (measured 2026-10-19):",
        "  #   - the curated LIBETC INTR family (intr_*_begin/commit, intr_start_auxN,",
        "  #     intr_restart_*) is TRUE-space: every entry's jal word exists in the",
        "  #     true payload as written and its woven reading has zero hits;",
        "  #   - scanner-generated names (func_XXXXXXXX, data_XXXXXXXX) and the",
        "  #     woven-pinned SDK members (e.g. startIntr = the WOVEN VA of its row)",
        "  #     are WOVEN-space and land wrong once the carve is true.",
        "  # The transition must re-derive the woven-space names (re-scan on the true",
        "  # baseline) and re-author the woven curated entries in true space",
        "  # (true VA = tools/deframe.py --map-framed <woven VA>); gp_value likewise.",
        "  # -------------------------------------------------------------------",
        "",
    ]
    text = text.replace("\nsegments:\n", "\n" + "\n".join(prov) + "segments:\n", 1)
    dest = OUT_DIR / "yamls" / f"splat.{target}.yaml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)
    return dest


def spotcheck(target: str, fw: Framing, plan, dmod) -> None:
    """Row-level proof: new bytes == old bytes minus framing, plus capstone."""
    framed = (REPO / "baselines" / f"{target}.bin").read_bytes()
    tpath = OUT_DIR / f"{target}.bin"
    if not tpath.is_file():
        print(f"  spotcheck: {tpath} absent - run deframe.py --payload first")
        return
    true = tpath.read_bytes()
    # pick: the first row, every 50th kept row, and the row holding the
    # banked rand-routine head (slps/sces); plan order keeps them unique
    rand_va = {"slps_00270": 0x80023474, "sces_00269": 0x8002349C}.get(target)
    rand_off = None if rand_va is None else HEADER + (rand_va - 0x80020000)
    picks, checked = [], 0
    for r in plan:
        if r["dropped"]:
            continue
        if checked % 50 == 0 or r["idx"] == 0:
            picks.append(r)
        if rand_off is not None and r["new_off"] <= rand_off < r["new_off"] + r["new_size"]:
            if r not in picks:
                picks.append(r)
            rand_off = None
        checked += 1
    print(f"  spotcheck {target}:")
    for r in picks:
        o, e = r["old_off"], r["old_off"] + r["old_size"]
        new = true[r["new_off"]:r["new_off"] + r["new_size"]]
        n_cmp, n_bad = 0, 0
        for j in range(o, e):
            if fw.is_data(j):
                t = fw.true_of(j)
                if true[t] != framed[j]:
                    n_bad += 1
                n_cmp += 1
        if n_bad:
            raise SystemExit(f"{target}/{r['name']}: {n_bad} byte mismatches")
        print(f"    {r['name']:20s} 0x{o:06X}+0x{r['old_size']:X} -> "
              f"0x{r['new_off']:06X}+0x{r['new_size']:X}  "
              f"{n_cmp} bytes compared, 0 differ, sha1 {hashlib.sha1(new).hexdigest()[:12]}")
    if rand_va is not None:
        try:
            import capstone
            md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32
                             | capstone.CS_MODE_LITTLE_ENDIAN)
            off = HEADER + (rand_va - 0x80020000)
            dis = list(md.disasm(true[off:off + 16], rand_va))
            print(f"    capstone @ true 0x{rand_va:X}: "
                  + " ; ".join(f"{i.mnemonic} {i.op_str}" for i in dis[:4]))
        except ImportError:
            print("    capstone not available - decode check skipped")
    # whole-payload census for the boots: the docs bank 7 rand-call jal words
    words = {"slps_00270": 0x0C00BAAC, "sces_00269": 0x0C00B995}.get(target)
    if words is not None:
        pat = words.to_bytes(4, "little")
        n = sum(1 for i in range(0, len(true) - HEADER - 4, 4)
                if true[HEADER + i:HEADER + i + 4] == pat)
        print(f"    rand jal word 0x{words:08X}: {n} occurrences in the true payload "
              "(docs bank 7)")


def run(target: str, do_write: bool, do_spot: bool, target_path_tmpl: str) -> None:
    dmod = load_deframe()
    src = REPO / "config" / f"splat.{target}.yaml"
    baseline = REPO / "baselines" / f"{target}.bin"
    fw = Framing(baseline, dmod)
    rows, marker = parse_rows(src)
    plan = plan_rows(rows, marker, fw)
    t_size, local = true_sizes(target)
    evidence = cross_check(target, fw, dmod, rows)
    summary = summarize(target, plan, marker, t_size, local, fw, evidence)
    imp = write_impact(target, plan, marker, t_size, local, fw, evidence, summary)
    print(summary)
    print(f"  impact table: {imp.relative_to(REPO)}")
    if do_write:
        tpath = target_path_tmpl.format(target=target)
        dest = migrate_yaml(target, src, plan, marker, t_size, local, tpath, summary)
        print(f"  wrote {dest.relative_to(REPO)} (target_path -> {tpath})")
    if do_spot:
        spotcheck(target, fw, plan, dmod)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--target", action="append", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--write", action="store_true",
                    help="emit migrated yamls to build/work/true/yamls/ (default: dry-run)")
    ap.add_argument("--spotcheck", action="store_true",
                    help="prove sampled rows byte for byte against the true baseline")
    ap.add_argument("--target-path", default="build/work/true/{target}.bin",
                    help="target_path for the migrated yaml (default: %(default)s)")
    args = ap.parse_args(argv[1:])
    targets = TARGETS if args.all else (args.target or [])
    if not targets:
        ap.error("pass --target <t> (repeatable) or --all")
    for t in targets:
        if t not in TARGETS:
            ap.error(f"unknown target {t}; known: {' '.join(TARGETS)}")
        run(t, args.write, args.spotcheck, args.target_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
