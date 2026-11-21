#!/usr/bin/env python3
"""Evidence-separated, source-only coverage of the eight PS-X executables.

This is a layout census, not a retail SHA-1 witness. "C bytes" means the
current splat YAML assigns that range to a compiled C unit. "SDK-evidenced"
means the range intersects a committed Psy-Q member/function anchor.
Everything else has UNATTRIBUTED ORIGIN, not necessarily game provenance.

Semantic recovery is NEVER inferred from the lack of inline assembly.
Only explicitly reviewed, source-linked rows in config/coverage_reviews.json
count as "reviewed semantic C"; all unreviewed rows remain unreviewed.

Usage:
    python3 tools/coverage_report.py
    python3 tools/coverage_report.py --json --rows
    python3 tools/coverage_report.py --target g3_jp --json --rows
    python3 tools/coverage_report.py --strict --json > coverage.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
TARGETS = (
    "g3_eu", "g3_jp", "g3org_eu", "g3org_jp",
    "mainmenu_eu", "mainmenu_jp", "sces_00269", "slps_00270",
)
ANCHOR_RE = re.compile(
    r"^(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s+\S+\s+\S+\s+\S+\s+"
    r"(?:anchored|unique|agree|window-verbatim|window-fixed)\s*$"
)
ASM_RE = re.compile(r"\b(?:__asm__|asm)\s*(?:(?:__volatile__|volatile)\s*)?\(")
INCLUDE_RE = re.compile(r"\bINCLUDE_ASM\s*\(")
REVIEW_TIERS = ("semantic_c", "hybrid", "asm_preserved")


class CoverageError(ValueError):
    pass


def sdk_anchors(root: Path) -> dict[str, list[tuple[int, int]]]:
    """Return address intervals with committed member/window evidence."""
    path = root / "config/sdk_anchors.txt"
    if not path.is_file():
        raise CoverageError(f"SDK evidence missing: {path}")
    anchors: dict[str, list[tuple[int, int]]] = defaultdict(list)
    target = None
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if line.startswith("// target:"):
            parts = line.split()
            target = parts[2] if len(parts) >= 3 else None
            continue
        if not line.strip() or line.lstrip().startswith("//"):
            continue
        match = ANCHOR_RE.fullmatch(line.strip())
        if match is None or target is None:
            raise CoverageError(f"invalid SDK anchor at {path}:{number}")
        start, length = int(match[1], 16), int(match[2], 16)
        if length <= 0:
            raise CoverageError(f"nonpositive SDK anchor length at {path}:{number}")
        anchors[target].append((start, start + length))
    return {k: sorted(v) for k, v in anchors.items()}


def overlap_union(start: int, end: int, intervals: list[tuple[int, int]]) -> int:
    """Count SDK-evidenced bytes in [start, end) once, even if anchors overlap."""
    clipped = sorted(
        (max(start, lo), min(end, hi))
        for lo, hi in intervals if lo < end and hi > start
    )
    total = 0
    cursor = start
    for lo, hi in clipped:
        if hi > cursor:
            total += hi - max(lo, cursor)
            cursor = hi
    return total


def code_rows(root: Path, target: str) -> tuple[list[dict], int]:
    """Use parsed YAML segment boundaries, not possibly stale row comments."""
    path = root / f"config/splat.{target}.yaml"
    try:
        doc = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        raise CoverageError(f"cannot parse {path}: {exc}") from exc

    segments = doc.get("segments") or []
    out: list[dict] = []
    payload_bytes = 0
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict) or segment.get("type") != "code":
            continue
        rows = segment.get("subsegments") or []
        start = segment.get("start")
        vram = segment.get("vram")
        if not isinstance(start, int) or not isinstance(vram, int) or not rows:
            raise CoverageError(f"{target}: code segment missing start/vram/rows")
        next_segment = segments[index + 1] if index + 1 < len(segments) else None
        if isinstance(next_segment, (list, tuple)) and next_segment:
            end = next_segment[0]
        elif isinstance(next_segment, dict):
            end = next_segment.get("start")
        else:
            end = segment.get("end")
        if not isinstance(end, int) or end <= start:
            raise CoverageError(f"{target}: no valid code-segment end boundary")
        payload_bytes += end - start
        cursor = start
        for row_index, row in enumerate(rows):
            if not isinstance(row, (list, tuple)) or len(row) < 3:
                raise CoverageError(f"{target}: malformed row {row_index}")
            off, kind, name = row[:3]
            next_off = rows[row_index + 1][0] if row_index + 1 < len(rows) else end
            if (not isinstance(off, int) or not isinstance(next_off, int)
                    or not isinstance(name, str) or not isinstance(kind, str)
                    or off != cursor or next_off <= off or next_off > end):
                raise CoverageError(
                    f"{target}: invalid/noncontiguous row {row_index}: {row!r}"
                )
            va = row[3] if len(row) >= 4 and isinstance(row[3], int) else vram + off - start
            out.append({
                "target": target, "name": name, "kind": kind, "offset": off,
                "vram": va, "bytes": next_off - off,
            })
            cursor = next_off
        if cursor != end:
            raise CoverageError(f"{target}: rows do not cover code-segment end")
    if not out:
        raise CoverageError(f"{target}: no code rows")
    return out, payload_bytes


def resolve_source(root: Path, target: str, name: str) -> Path | None:
    """The build uses target-local C first, then shared C; .pN rows share a unit."""
    base = re.sub(r"\.p[0-9]+$", "", name)
    for path in (root / "src" / target / f"{base}.c", root / "src" / f"{base}.c"):
        if path.is_file():
            return path
    return None


def source_style(source: Path) -> str:
    """Lexical *source-unit* flag; it does not certify semantic recovery."""
    source_text = source.read_text(errors="replace")
    without_comments = re.sub(
        r"/\*.*?\*/|//[^\n]*", "", source_text, flags=re.DOTALL
    )
    if INCLUDE_RE.search(without_comments):
        return "include_asm"
    if ASM_RE.search(without_comments):
        return "inline_asm"
    return "no_inline_asm_detected"


def load_reviews(root: Path) -> dict[tuple[str, str], dict]:
    path = root / "config/coverage_reviews.json"
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text())
    except (ValueError, OSError) as exc:
        raise CoverageError(f"invalid review registry: {exc}") from exc
    if doc.get("schema") != 1 or not isinstance(doc.get("reviews"), list):
        raise CoverageError("review registry must use schema 1 and reviews array")
    reviews = {}
    for entry in doc["reviews"]:
        if not isinstance(entry, dict):
            raise CoverageError("review entry must be an object")
        t, n, tier = entry.get("target"), entry.get("name"), entry.get("tier")
        source, evidence = entry.get("source"), entry.get("evidence")
        if (t not in TARGETS or not isinstance(n, str) or not n
                or tier not in REVIEW_TIERS or not isinstance(source, str)
                or not source.startswith("src/") or not evidence
                or not isinstance(evidence, str)):
            raise CoverageError(f"invalid review entry: {entry!r}")
        if (t, n) in reviews:
            raise CoverageError(f"duplicate review for {t}:{n}")
        reviews[(t, n)] = entry
    return reviews


def summarise_target(
    root: Path, target: str, anchor_intervals: list[tuple[int, int]],
    reviews: dict[tuple[str, str], dict], *, include_rows: bool = False,
) -> dict:
    rows, payload_bytes = code_rows(root, target)
    counters: dict[str, int] = defaultdict(int)
    details = []
    style_cache: dict[Path, str] = {}

    for row in rows:
        kind, size = row["kind"], row["bytes"]
        counters[f"{kind}_bytes"] += size
        counters[f"{kind}_rows"] += 1
        covered = overlap_union(
            row["vram"], row["vram"] + size, anchor_intervals
        )
        counters[f"{kind}_sdk_evidenced_bytes"] += covered
        counters[f"{kind}_origin_unattributed_bytes"] += size - covered
        entry = dict(row)
        entry["sdk_evidenced_bytes"] = covered

        if kind == "c":
            source = resolve_source(root, target, row["name"])
            src_path = source.relative_to(root).as_posix() if source else None
            style = "source_missing"
            if source is not None:
                if source not in style_cache:
                    style_cache[source] = source_style(source)
                style = style_cache[source]
            counters[f"c_{style}_bytes"] += size
            counters[f"c_{style}_rows"] += 1
            entry["source"] = src_path
            entry["source_style"] = style

            review = reviews.get((target, row["name"]))
            if review is not None:
                if review["source"] != src_path:
                    raise CoverageError(
                        f"review source differs from resolved C unit for "
                        f"{target}:{row['name']}: {review['source']} != {src_path}"
                    )
                if review["tier"] == "semantic_c" and style != "no_inline_asm_detected":
                    raise CoverageError(
                        f"semantic C review contradicts source flags: "
                        f"{target}:{row['name']} ({style})"
                    )
                counters[f"c_reviewed_{review['tier']}_bytes"] += size
                counters[f"c_reviewed_{review['tier']}_rows"] += 1
                entry["review"] = {
                    "tier": review["tier"], "evidence": review["evidence"]
                }
            else:
                counters["c_unreviewed_bytes"] += size
                counters["c_unreviewed_rows"] += 1
        if include_rows:
            details.append(entry)

    # A manual review may only refer to a real, resolved C row in the target.
    row_keys = {(target, r["name"]) for r in rows if r["kind"] == "c"}
    unused = sorted(set(k for k in reviews if k[0] == target) - row_keys)
    if unused:
        raise CoverageError(f"orphaned review(s) for {target}: {unused}")

    c_bytes = counters["c_bytes"]
    asm_bytes = counters["asm_bytes"]
    mapped_code = c_bytes + asm_bytes
    sdk_code = counters["c_sdk_evidenced_bytes"] + counters["asm_sdk_evidenced_bytes"]
    unassigned_code = mapped_code - sdk_code
    if mapped_code == 0:
        raise CoverageError(f"{target}: no mapped C/asm bytes")
    if sum(counters[f"{x}_bytes"] for x in ("c", "asm", "data")) > payload_bytes:
        raise CoverageError(f"{target}: classified bytes exceed payload")
    pct = lambda count, denominator: round(100 * count / denominator, 2) if denominator else None

    result = {
        "target": target,
        "payload_bytes": payload_bytes,
        "mapped_code_bytes": mapped_code,
        "mapped_data_bytes": counters["data_bytes"],
        "c_bytes": c_bytes,
        "asm_bytes": asm_bytes,
        "c_rows": counters["c_rows"],
        "asm_rows": counters["asm_rows"],
        "c_share_of_mapped_code_pct": pct(c_bytes, mapped_code),
        "sdk_evidenced_code_bytes": sdk_code,
        "sdk_evidenced_c_bytes": counters["c_sdk_evidenced_bytes"],
        "sdk_evidenced_asm_bytes": counters["asm_sdk_evidenced_bytes"],
        "sdk_c_share_pct": pct(counters["c_sdk_evidenced_bytes"], sdk_code),
        "origin_unattributed_code_bytes": unassigned_code,
        "origin_unattributed_c_bytes": counters["c_origin_unattributed_bytes"],
        "origin_unattributed_asm_bytes": counters["asm_origin_unattributed_bytes"],
        "origin_unattributed_c_share_pct": pct(
            counters["c_origin_unattributed_bytes"], unassigned_code
        ),
        "c_source_flags_bytes": {
            "no_inline_asm_detected": counters["c_no_inline_asm_detected_bytes"],
            "inline_asm": counters["c_inline_asm_bytes"],
            "include_asm": counters["c_include_asm_bytes"],
            "source_missing": counters["c_source_missing_bytes"],
        },
        "c_review_bytes": {
            "semantic_c": counters["c_reviewed_semantic_c_bytes"],
            "hybrid": counters["c_reviewed_hybrid_bytes"],
            "asm_preserved": counters["c_reviewed_asm_preserved_bytes"],
            "unreviewed": counters["c_unreviewed_bytes"],
        },
        "reviewed_rows": {
            tier: counters[f"c_reviewed_{tier}_rows"] for tier in REVIEW_TIERS
        },
        "source_missing_rows": counters["c_source_missing_rows"],
    }
    if include_rows:
        result["rows"] = details
    return result


def total_row(results: list[dict]) -> dict:
    """Sum *target instances*, never deduplicate cross-target shared C units."""
    sum_fields = (
        "payload_bytes", "mapped_code_bytes", "mapped_data_bytes", "c_bytes",
        "asm_bytes", "c_rows", "asm_rows", "sdk_evidenced_code_bytes",
        "sdk_evidenced_c_bytes", "sdk_evidenced_asm_bytes",
        "origin_unattributed_code_bytes", "origin_unattributed_c_bytes",
        "origin_unattributed_asm_bytes", "source_missing_rows",
    )
    out = {key: sum(r[key] for r in results) for key in sum_fields}
    for key in ("c_source_flags_bytes", "c_review_bytes", "reviewed_rows"):
        out[key] = {k: sum(r[key][k] for r in results) for k in results[0][key]}
    pct = lambda num, den: round(100 * num / den, 2) if den else None
    out["c_share_of_mapped_code_pct"] = pct(out["c_bytes"], out["mapped_code_bytes"])
    out["sdk_c_share_pct"] = pct(
        out["sdk_evidenced_c_bytes"], out["sdk_evidenced_code_bytes"]
    )
    out["origin_unattributed_c_share_pct"] = pct(
        out["origin_unattributed_c_bytes"], out["origin_unattributed_code_bytes"]
    )
    return out


def report(root: Path = REPO, *, target: str | None = None,
           rows: bool = False, strict: bool = False) -> dict:
    if target is not None and target not in TARGETS:
        raise CoverageError(f"unknown target {target}")
    anchors = sdk_anchors(root)
    reviews = load_reviews(root)
    targets = [target] if target else list(TARGETS)
    results = [
        summarise_target(root, t, anchors.get(t, []), reviews, include_rows=rows)
        for t in targets
    ]
    if strict:
        missing = {r["target"]: r["source_missing_rows"] for r in results
                   if r["source_missing_rows"]}
        if missing:
            raise CoverageError(f"C rows with no resolved source: {missing}")
        for t in targets:
            if t not in anchors:
                raise CoverageError(f"no committed SDK anchors for {t}")
    return {
        "schema": 1,
        "metric": "splat_yaml_mapped_c_asm_byte_spans",
        "source_only": True,
        "retail_verified": False,
        "denominator_warning": (
            "Mapped code is YAML C+ASM span bytes, not proven executable "
            "instructions or all game logic; data rows can hide code."
        ),
        "origin_warning": (
            "Only intersecting SDK anchors justify SDK-evidenced origin. "
            "Nonintersecting spans are UNATTRIBUTED, not proven game code."
        ),
        "quality_warning": (
            "No inline asm detected is a lexical source-unit flag, not "
            "semantic recovery. Semantic tiers require explicit manual review."
        ),
        "targets": results,
        "total_target_instances": total_row(results),
    }


def human_report(data: dict) -> None:
    print(
        f"{'target':<14} {'C/code':>8} {'SDK C':>8} "
        f"{'unattrib C':>11} {'C asm*':>9} {'reviewed C':>11}"
    )
    for row in [*data["targets"], dict(data["total_target_instances"], target="TOTAL")]:
        pct = lambda key: (f"{row[key]:.2f}%" if row[key] is not None else "n/a")
        asm = row["c_source_flags_bytes"]
        print(
            f"{row['target']:<14} {pct('c_share_of_mapped_code_pct'):>8} "
            f"{pct('sdk_c_share_pct'):>8} "
            f"{pct('origin_unattributed_c_share_pct'):>11} "
            f"{(asm['inline_asm'] + asm['include_asm']) / 1024:>8.1f}K "
            f"{row['c_review_bytes']['semantic_c'] / 1024:>10.1f}K"
        )
    print("* C asm: bytes assigned to C units with detected inline asm / INCLUDE_ASM.")
    print("SDK-evidenced = overlap with committed SDK anchors; remainder is")
    print("UNATTRIBUTED ORIGIN, not confirmed game-specific code.")
    print("Reviewed semantic C counts ONLY annotated rows; unreviewed != nonsemantic.")
    print("The code denominator is YAML C+ASM bytes, not all actual executable code.")
    print("This report does not run or replace the full-image retail SHA-1 oracle.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--rows", action="store_true", help="include every YAML row in JSON")
    ap.add_argument("--target", choices=TARGETS, help="one target only")
    ap.add_argument("--strict", action="store_true",
                    help="fail when C sources or SDK anchor evidence is missing")
    args = ap.parse_args()
    if args.rows and not args.json:
        ap.error("--rows requires --json")
    try:
        result = report(target=args.target, rows=args.rows, strict=args.strict)
    except CoverageError as exc:
        print(f"coverage_report: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        human_report(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
