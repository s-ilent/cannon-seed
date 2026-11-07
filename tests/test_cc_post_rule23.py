"""Rule 23 (pos-op) unit tests - the position mover.

The transform: explicit-site insert/delete/modify/move operations applied
sequentially, per-site shape-verified (mnemonic), loud exit 3 on any
contract miss, never default-on (fires only on --pos-op payloads from
`cc-post: pos-op` markers). The site addressing is the rule-22 convention
(label + is_instruction-counted index; comments/directives carry no
words). Spec layout: `<kind>:<label>;<idx>;<mnem>[;<text>]`, fields
`;`-separated, the kind colon-joined to the label; in insn texts the
FIRST `_` separates mnemonic from operands, later `_` are literal.
"""
import unittest

import cc_post

BASE = [
    "func:\n",
    "$L1:\n",
    "\taddu $2,$4,$zero\n",
    "\tnop\n",
    "\tlw $2,4($16)\n",
    "\tj $31\n",
    "\taddu $sp,$sp,80\n",
]


def apply(lines, spec):
    return cc_post._rule23_pos_op(lines, spec)


class Rule23Insert(unittest.TestCase):
    def test_ins_after_site(self):
        r = apply(BASE, "i:$L1;0;addu;addiu_$2,$2,8")
        self.assertEqual(r[3], "\taddiu $2,$2,8\n")
        self.assertEqual(r[2], "\taddu $2,$4,$zero\n")

    def test_ins_anchor_mnemonic_verified(self):
        self.assertIsNone(apply(BASE, "i:$L1;0;lw;addiu_$2,$2,8"))

    def test_ins_unknown_label_loud(self):
        self.assertIsNone(apply(BASE, "i:$L9;0;addu;addiu_$2,$2,8"))

    def test_ins_out_of_range_loud(self):
        self.assertIsNone(apply(BASE, "i:$L1;9;addu;addiu_$2,$2,8"))

    def test_ins_symbol_underscores_survive(self):
        r = apply(BASE, "i:$L1;0;addu;la_$2,D_8014788C")
        self.assertEqual(r[3], "\tla $2,D_8014788C\n")

    def test_ins_empty_text_loud(self):
        self.assertIsNone(apply(BASE, "i:$L1;0;addu;"))


class Rule23Delete(unittest.TestCase):
    def test_del_nop(self):
        r = apply(BASE, "d:$L1;1;nop")
        self.assertEqual(len(r), len(BASE) - 1)
        self.assertNotIn("\tnop\n", r)

    def test_del_mnemonic_mismatch_loud(self):
        self.assertIsNone(apply(BASE, "d:$L1;1;lw"))


class Rule23Modify(unittest.TestCase):
    def test_mod_rewrites_text(self):
        r = apply(BASE, "m:$L1;2;lw;lw_$3,8($16)")
        self.assertEqual(r[4], "\tlw $3,8($16)\n")

    def test_mod_keeps_lead_whitespace(self):
        r = apply(BASE, "m:$L1;0;addu;addiu_$2,$2,-8")
        self.assertEqual(r[2], "\taddiu $2,$2,-8\n")

    def test_mod_mnemonic_mismatch_loud(self):
        self.assertIsNone(apply(BASE, "m:$L1;2;sw;lw_$3,8($16)"))


class Rule23Move(unittest.TestCase):
    def test_mov_relocates(self):
        r = apply(BASE, "v:$L1;1;nop;$L1;1;lw")
        # nop deleted from after the addu, re-inserted after the lw (the
        # lw sits at idx1 in the post-delete stream)
        self.assertEqual(
            [ln.strip() for ln in r[2:7]],
            ["addu $2,$4,$zero", "lw $2,4($16)", "nop", "j $31",
             "addu $sp,$sp,80"])

    def test_mov_dst_indices_post_delete(self):
        # deleting idx1 (the nop) shifts the lw from idx2 to idx1; the
        # dst site addresses the POST-DELETE stream
        r = apply(BASE, "v:$L1;1;nop;$L1;1;lw")
        self.assertEqual(r[4], "\tnop\n")

    def test_mov_src_mnemonic_loud(self):
        self.assertIsNone(apply(BASE, "v:$L1;1;lw;$L1;3;lw"))


class Rule23SequentialAndSpec(unittest.TestCase):
    def test_sequential_ops_see_earlier_effects(self):
        out = apply(BASE, "i:$L1;0;addu;addiu_$2,$2,8")
        out = apply(out, "d:$L1;0;addu")   # the ORIGINAL addu is idx0
        self.assertEqual(out[2], "\taddiu $2,$2,8\n")
        self.assertNotIn("\taddu $2,$4,$zero\n", out)

    def test_prepass_loud_exit3_on_miss(self):
        cc_post.POS_OPS = ["d:$L1;1;lw"]
        try:
            with self.assertRaises(SystemExit) as cm:
                cc_post._prepass_pos_op(list(BASE))
            self.assertEqual(cm.exception.code, 3)
        finally:
            cc_post.POS_OPS = None

    def test_prepass_applies_in_order(self):
        cc_post.POS_OPS = ["d:$L1;1;nop", "i:$L1;0;addu;lw_$3,0($16)"]
        try:
            r = cc_post._prepass_pos_op(list(BASE))
            self.assertEqual(r[3], "\tlw $3,0($16)\n")
        finally:
            cc_post.POS_OPS = None


if __name__ == "__main__":
    unittest.main()
