#!/usr/bin/env python3
"""worklog_digest - rebuild the shared worklog's lost window sections from the repo record.

The sandbox periodically reverts /home/z/my-project (worklog.md included) to an old
snapshot; the repo is the recovery medium: every agent window commits its log to
docs/TASKS.md under a "## <date> (window cron-YYYYMMDD-HHMM): ..." header and its
commits to git history. This tool lists, one line per window, every window whose
Task ID is absent from the local worklog - exactly the digest a RESTORE NOTE needs,
mechanically, with the anchor commit(s) cited per window.

The window IDs come from docs/TASKS.md headers (canonical log order); anchor commits
come from git-log subjects mentioning the window ID, with a -S pickaxe search over
docs/TASKS.md as the fallback for windows whose docs commit does not name the window
in its subject. Digest text is the header's own summary, trimmed.

Usage:
    python3 tools/worklog_digest.py [worklog_path] [--all]
    worklog_path defaults to /home/z/my-project/worklog.md (missing file = nothing covered)
    --all lists every window regardless of worklog coverage.
Coverage levels: a full "Task ID: cron-..." section, or a digest bullet
"- cron-... (hash): ..." from a prior RESTORE NOTE - only windows with
neither trace are listed as missing. Exit status: 0 when nothing is
missing, 1 when the digest lists missing windows.
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TASKS = REPO / "docs" / "TASKS.md"
DEFAULT_WORKLOG = Path("/home/z/my-project/worklog.md")
HDR_RE = re.compile(
    r"^## (\d{4}-\d{2}-\d{2})[^\n(]*\(window (cron-\d{8}-\d{4})(?:, same session)?\)(.*)$")


def git_log():
    """Chronological (oldest first) (hash, date, subject) tuples for main history."""
    out = subprocess.run(
        ["git", "-C", str(REPO), "log", "--reverse", "--format=%h|%ad|%s",
         "--date=iso-strict", "HEAD"],
        check=True, capture_output=True, text=True).stdout
    entries = []
    for line in out.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            entries.append(tuple(parts))
    return entries


def header_windows():
    """docs/TASKS.md order: list of (window_id, header summary text, full header line)."""
    windows = []
    seen = set()
    lines = TASKS.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines):
        m = HDR_RE.match(line)
        if not m:
            continue
        wid = m.group(2)
        if wid in seen:
            continue  # "same session" duplicate headers merge into the first
        seen.add(wid)
        # The header summary wraps across consecutive "## "-prefixed lines; join.
        text = re.sub(r"^[\s:—-]+", "", m.group(3)).strip()
        j = i + 1
        while (len(text) < 200 and j < len(lines)
               and lines[j].startswith("## ")
               and not HDR_RE.match(lines[j])):
            cont = lines[j].lstrip("#").strip()
            if not cont:
                break
            text = f"{text} {cont}"
            j += 1
        text = text.rstrip(":-— ").strip()
        if len(text) > 220:
            text = text[:217].rstrip() + "..."
        windows.append((wid, text))
    return windows


def anchor_map(entries):
    """window_id -> list of commit hashes whose subject names the window."""
    anchors = {}
    for h, _date, subj in entries:
        for m in re.finditer(r"window (cron-\d{8}-\d{4})", subj):
            anchors.setdefault(m.group(1), []).append(h)
    return anchors


def pickaxe_anchor(wid):
    """First commit that introduced the window ID into docs/TASKS.md."""
    out = subprocess.run(
        ["git", "-C", str(REPO), "log", "--reverse", "--format=%h", f"-S{wid}",
         "HEAD", "--", "docs/TASKS.md"],
        check=True, capture_output=True, text=True).stdout.split()
    return out[0] if out else "??"


def main():
    args = [a for a in sys.argv[1:] if a != "--all"]
    show_all = "--all" in sys.argv
    worklog = Path(args[0]) if args else DEFAULT_WORKLOG

    sections = set()
    digest = set()
    if worklog.exists():
        text = worklog.read_text(errors="replace")
        sections = set(re.findall(r"^Task ID: (cron-\d{8}-\d{4})", text, re.M))
        # RESTORE NOTE digest bullets: "- cron-YYYYMMDD-HHMM (hash[, hash]): ..."
        digest = set(re.findall(r"^- (cron-\d{8}-\d{4}) \((?:[0-9a-f]{8}(?:, [0-9a-f]{8})*(?:, \.\.\.)?|\?\?)\): ", text, re.M))

    entries = git_log()
    subjects = anchor_map(entries)
    windows = header_windows()

    covered = sections | digest
    missing = [(wid, t) for wid, t in windows if show_all or wid not in covered]
    print(f"worklog_digest: {len(windows)} window(s) in docs/TASKS.md, "
          f"{sum(1 for w, _ in windows if w in sections)} full section(s), "
          f"{sum(1 for w, _ in windows if w in digest - sections)} digest-level, "
          f"{len(missing)} missing  [{worklog}]")
    for wid, text in missing:
        anchors = subjects.get(wid)
        if anchors:
            short = ", ".join(anchors[:2]) + (", ..." if len(anchors) > 2 else "")
        else:
            short = pickaxe_anchor(wid)
        print(f"- {wid} ({short}): {text}")
    return 1 if missing and not show_all else 0


if __name__ == "__main__":
    sys.exit(main())
