#!/bin/sh
# Apply the color-war experiment guards to the source-built GCC 2.6.3 PSX
# tree (tools/build_cc1_263.sh builds the stock tree first) and rebuild cc1.
#
# The experiment: the G probe's retail render needs a spelling whose extra
# in-loop color read survives cse2 into the .flow tally and dies in combine
# with the render byte-identical (probes/gcc263/GsTMDdivG4LFG.c STATUS
# blocks, windows cron-20261021-2213 / cron-20261022-0043).  The self-kill
# fold happens at three levels; the guards suppress it at the first two and
# keep combine's:
#
#   GUARD 1 (M2, cron-20261022-0043)  fold-const.c ~3751 - the tree-level
#          "&x - &x" X-X -> integer_zero_node fold.
#   GUARD 2 (M2, cron-20261022-0043)  cse.c ~3631 - simplify_binary_
#          _operation's direct rtx_equal_p MINUS self-kill -> CONST0_RTX.
#   GUARD 3 (M3, cron-20261022-0158)  cse.c fold_rtx entry short-circuit
#          for a same-operand integral MINUS.  Every other cse-level door
#          for the shape (the sbop X*C-X coefficient distribution and the
#          simplify_plus_minus negs[] associate path, cse.c ~4124+) sits
#          behind a fold_rtx call, so one entry guard closes them all.
#   GUARD 4 (M4, cron-20261022-0428)  loop.c: a replaceable giv whose insn
#          is a same-operand integral MINUS keeps its dest->new_reg map
#          unset.  The 0158 "cse reg substitution" reading is REFUTED by
#          the fresh pass dumps: the pair survives the first cse as a true
#          self-kill (minus 132 132), then loop.c's giv reduction creates
#          the reduced reg, reg_map rewrites the CONSUMER to read it, the
#          original minus is orphaned and the second cse's dead-deletion
#          cascade eats it.  Skipping the reg_map write keeps the consumer
#          on the original giv reg (minus live into cse2/combine), the
#          reduced reg stays unread so its init/increment insns die, and
#          biv elimination (all_reduced) is untouched - the pair, not the
#          function.
#
# All four are `if (0 && ...)` / early-return suppressions tagged
# MODIFIED-CC1; combine's fold (the level we WANT) is untouched.
# Regression gate: the unmodified G probe must still render byte-identical
# through the guarded cc1 (the probe carries no same-operand MINUS shape).
#
# Usage: sh tools/patch_cc1_263.sh      (idempotent; skips applied guards)

set -e

GCCSRC="${GCCSRC:-/home/z/my-project/tools-local/gcc-2.6.3-src/gcc-2.6.3}"
[ -f "$GCCSRC/cc1" ] || { echo "patch_cc1: no cc1 at $GCCSRC - run tools/build_cc1_263.sh first" >&2; exit 1; }

python3 - "$GCCSRC" <<'EOF'
import sys, os
root = sys.argv[1]

def edit(path, old, new, tag):
    p = os.path.join(root, path)
    src = open(p).read()
    if tag in src:
        print(f"[patch_cc1] {path}: {tag} already applied")
        return
    n = src.count(old)
    if n != 1:
        raise SystemExit(f"[patch_cc1] FATAL {path}: anchor matches {n} times (want 1)")
    open(p, 'w').write(src.replace(old, new))
    print(f"[patch_cc1] {path}: {tag} applied")

# ---- GUARD 1: fold-const.c tree-level X-X fold (M2) ----
edit('fold-const.c',
"""      if ((! FLOAT_TYPE_P (type) || flag_fast_math)
\t  && operand_equal_p (arg0, arg1, 0))
\treturn convert (type, integer_zero_node);""",
"""      /* MODIFIED-CC1 (GUARD 1, M2 cron-20261022-0043): the tree-level
         X-X fold is suppressed - the color-war experiment needs the
         self-kill pair to reach RTL so combine (the level we want) can
         own the fold.  */
      if (0 && (! FLOAT_TYPE_P (type) || flag_fast_math)
\t  && operand_equal_p (arg0, arg1, 0))
\treturn convert (type, integer_zero_node);""",
"MODIFIED-CC1 (GUARD 1")

# ---- GUARD 2: cse.c simplify_binary_operation direct self-kill (M2) ----
edit('cse.c',
"""\t  /* We can't assume x-x is 0 even with non-IEEE floating point,
\t     but since it is zero except in very strange circumstances, we
\t     will treat it as zero with -ffast-math.  */
\t  if (rtx_equal_p (op0, op1)
\t      && ! side_effects_p (op0)
\t      && (! FLOAT_MODE_P (mode) || flag_fast_math))
\t    return CONST0_RTX (mode);""",
"""\t  /* We can't assume x-x is 0 even with non-IEEE floating point,
\t     but since it is zero except in very strange circumstances, we
\t     will treat it as zero with -ffast-math.  */
\t  /* MODIFIED-CC1 (GUARD 2, M2 cron-20261022-0043): the direct MINUS
\t     self-kill fold is suppressed (see the G probe STATUS).  */
\t  if (0 && rtx_equal_p (op0, op1)
\t      && ! side_effects_p (op0)
\t      && (! FLOAT_MODE_P (mode) || flag_fast_math))
\t    return CONST0_RTX (mode);""",
"MODIFIED-CC1 (GUARD 2")

# ---- GUARD 3: fold_rtx entry short-circuit (M3) ----
edit('cse.c',
"""  if (x == 0)
    return x;

  mode = GET_MODE (x);
  code = GET_CODE (x);
  switch (code)""",
"""  if (x == 0)
    return x;

  /* MODIFIED-CC1 (GUARD 3, M3 cron-20261022-0158): fold_rtx entry
     short-circuit for a same-operand integral MINUS.  The color-war
     experiment needs the in-loop (minus cp cp) to survive cse2 so the
     extra register read reaches the .flow tally; every cse-level fold
     door for the shape (GUARD 2's site, the X*C-X coefficient
     distribution, and the simplify_plus_minus associate path) is behind
     this call, so one entry guard closes them all.  combine still folds
     the pair later via LOG_LINKS - the stock pipeline's render.  */
  if (GET_CODE (x) == MINUS
      && INTEGRAL_MODE_P (GET_MODE (x))
      && rtx_equal_p (XEXP (x, 0), XEXP (x, 1))
      && ! side_effects_p (x))
    return x;

  mode = GET_MODE (x);
  code = GET_CODE (x);
  switch (code)""",
"MODIFIED-CC1 (GUARD 3")

# ---- GUARD 4: loop.c giv reduction keeps the minus's dest map unset (M4) ----
edit('loop.c',
"""	  else if (v->replaceable)
	    {
	      reg_map[REGNO (v->dest_reg)] = v->new_reg;""",
"""	  else if (v->replaceable)
	    {
	      /* MODIFIED-CC1 (GUARD 4, M4 cron-20261022-0428): a giv whose
	      insn is a same-operand integral MINUS does not get the
	      dest->new_reg map - the color-war pair's consumer must
	      keep reading the original giv reg so the minus insn
	      survives cse2 (GUARD 3 holds it unfolded) and dies in
	      combine via LOG_LINKS (see probes/gcc263/GsTMDdivG4LFG_
	      wa.c STATUS).  The reduced reg stays unread, so its
	      init/increment insns die downstream; biv elimination is
	      untouched.  */
	      if (! (GET_CODE (PATTERN (v->insn)) == SET
	    		     && GET_CODE (SET_SRC (PATTERN (v->insn))) == MINUS
	    		     && INTEGRAL_MODE_P (GET_MODE (SET_SRC (PATTERN (v->insn))))
	    		     && rtx_equal_p (XEXP (SET_SRC (PATTERN (v->insn)), 0),
	    				     XEXP (SET_SRC (PATTERN (v->insn)), 1))))
			reg_map[REGNO (v->dest_reg)] = v->new_reg;""",
"MODIFIED-CC1 (GUARD 4")

print("[patch_cc1] all guards present")
EOF

echo "[patch_cc1] rebuilding cc1 (cse.c + fold-const.o + link)..."
cd "$GCCSRC"
make cpp cc1 xgcc CFLAGS="-std=gnu89 -static -fcommon -Dbsd4_4 -Dmips -DHAVE_STRERROR" >/dev/null 2>&1 || make cpp cc1 xgcc CFLAGS="-std=gnu89 -static -fcommon -Dbsd4_4 -Dmips -DHAVE_STRERROR"
echo "[patch_cc1] done: guarded cc1 at $GCCSRC/cc1"
