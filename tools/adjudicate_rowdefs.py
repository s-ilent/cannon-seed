#!/usr/bin/env python3
"""adjudicate_rowdefs.py - apply the FLIP-ROWDEF census adjudication spellings.

The with-row class of the woven-name/true-position clash census (both the
dlabel class and the cross-file glabel-dupe class resolve the same way):
rename the row to <name>.rowdef in the splat yaml and retire the name's
generated-symbols line with the FLIP-ROWDEF comment.  The plain name then
belongs to the retail-encoded definition (the auto-context dlabel or the
nested nonmatching glabel at the true position).

Spellings are the landed precedent (sces_00269 pilot through a5db3893
g3_eu, window cron-20261019-1051):
  yaml:    - [0xOFF, asm, func_X]   ->   - [0xOFF, asm, func_X.rowdef]
  symbols: func_X = 0xVMA; // type:func
        -> // FLIP-ROWDEF (woven row name retired, the row is func_X.rowdef
           and the retail-encoded definition owns the plain name): func_X =
           0xVMA; // type:func

No-row census names (identity branch-target entries) are NOT handled here -
they have no yaml row and use the no-row spelling variant by hand.

Validated cron-20261019-1319: g3org_jp 20/20 (commit 8147010a) and
g3org_eu 23/23 (commit 14a69b66) applied the exact landed spellings, and
both censuses re-derived 0 on the extract basis after clean_stale_asm +
re-extract. Per-name guards: exactly one yaml row and one symbols line
must match, else the name is skipped untouched.

Usage: python3 adjudicate_rowdefs.py <target> <name> [name ...]
       (names straight from tools/audit_flip_clashes.py)
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROW_T = r"^(\s*-\s*\[0x[0-9A-Fa-f]+,\s*(?:asm|data|c),\s*)({name})(\]\s*#.*)$"
LINE_T = r"^({name}) = (0x[0-9A-Fa-f]+); (// type:\w+.*)$"


def adjudicate(target: str, names: list[str]) -> int:
    yaml_path = REPO / "config" / f"splat.{target}.yaml"
    sym_path = REPO / "config" / f"symbols.{target}.txt"
    yaml_text = yaml_path.read_text()
    sym_text = sym_path.read_text()
    yaml_edits = sym_edits = 0
    for name in names:
        # yaml row rename (exactly one row must own the name)
        row_re = re.compile(ROW_T.format(name=re.escape(name)))
        hits = [m for m in (row_re.match(l) for l in yaml_text.splitlines()) if m]
        if len(hits) != 1:
            print(f"  {target}: {name}: yaml row matches = {len(hits)} "
                  f"(expected 1) - SKIPPED, no edit")
            continue
        yaml_text = "\n".join(
            (f"{m.group(1)}{name}.rowdef{m.group(3)}"
             if (m := row_re.match(l)) else l)
            for l in yaml_text.splitlines()
        ) + "\n"
        yaml_edits += 1

        # symbols line retirement
        line_re = re.compile(LINE_T.format(name=re.escape(name)))
        lhits = [m for m in (line_re.match(l) for l in sym_text.splitlines()) if m]
        if len(lhits) != 1:
            print(f"  {target}: {name}: symbols line matches = {len(lhits)} "
                  f"(expected 1) - SKIPPED, no edit")
            continue
        m = lhits[0]
        retired = (f"// FLIP-ROWDEF (woven row name retired, the row is "
                   f"{name}.rowdef and the retail-encoded definition owns the "
                   f"plain name): {name} = {m.group(2)}; {m.group(3)}")
        sym_text = "\n".join(
            retired if line_re.match(l) else l
            for l in sym_text.splitlines()
        ) + "\n"
        sym_edits += 1
    yaml_path.write_text(yaml_text)
    sym_path.write_text(sym_text)
    print(f"{target}: {yaml_edits} yaml rows renamed, "
          f"{sym_edits} symbols lines retired (of {len(names)} names)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    sys.exit(adjudicate(sys.argv[1], sys.argv[2:]))
