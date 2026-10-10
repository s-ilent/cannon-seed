#!/usr/bin/env bash
# build.sh - assemble the splat split of the primary target and lay it out
# into a PS-X EXE image. This is the round-trip half of the oracle loop:
# split (splat) -> maspsx -> GNU as (mipsel, MIPS1) -> ld (splat script)
# -> objcopy -> full image; tools/verify.sh compares the result with the
# retail SHA-1.
#
# Toolchain (no root in this sandbox): mipsel binutils 2.31.1 extracted
# from the Debian buster .deb into tools-local/ (git-ignored, rebuild via
# tools/get_binutils.sh). maspsx from tools-src/maspsx (pinned clone).
# Python bits from the persistent venv /home/z/my-project/.venv (survives
# re-provisions; tools/rehydrate.sh rebuilds it offline from the wheelhouse).
set -u

cd "$(dirname "$0")/.."
REPO="$PWD"

# Interpreter resolution: persistent venv first, legacy path as fallback.
PY="${PY:-}"
if [ -z "$PY" ]; then
    for cand in /home/z/my-project/.venv/bin/python3 /home/z/.venv/bin/python3; do
        if [ -x "$cand" ] && "$cand" -c "import splat, spimdisasm" >/dev/null 2>&1; then
            PY="$cand"
            break
        fi
    done
fi
[ -n "$PY" ] || PY=python3
MASPSX="${MASPSX:-/home/z/my-project/tools-src/maspsx/maspsx.py}"
TOOLROOT="${TOOLROOT:-/home/z/my-project/tools-local/mipsel-root}"
export LD_LIBRARY_PATH="$TOOLROOT/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
AS="$TOOLROOT/usr/bin/mipsel-linux-gnu-as"
LD="$TOOLROOT/usr/bin/mipsel-linux-gnu-ld"
OBJCOPY="$TOOLROOT/usr/bin/mipsel-linux-gnu-objcopy"

TARGET="${TARGET:-slps_00270}"
LD_SCRIPT="build/${TARGET}.gen.ld"
OUT_ELF="build/${TARGET}.elf"

ASFLAGS="-march=mips64 -mabi=32 -EL -I include -I asm/nonmatchings"

fail() { echo "build: $*" >&2; exit 2; }

[ -x "$AS" ] || fail "mipsel-as not found at $AS (see tools-local/ setup in docs/TOOLCHAIN.md)"
[ -f "config/splat.${TARGET}.yaml" ] || fail "splat config missing - run the split pipeline first"

# asm tree is PER TARGET (every address is valid for one revision only):
# build.sh follows the yaml's asm_path, so the target's own split is
# assembled - never a mix of two targets' files.
ASM_DIR=$("$PY" -c "import yaml; print(yaml.safe_load(open('config/splat.${TARGET}.yaml'))['options']['asm_path'].rstrip('/'))") \
    || fail "could not read asm_path from config/splat.${TARGET}.yaml"
[ -d "$ASM_DIR" ] || fail "asm tree missing at $ASM_DIR - run: make extract TARGET=$TARGET"
ASFLAGS="$ASFLAGS -I $ASM_DIR"

mkdir -p build
# regenerate the round-trip linker script from the committed yaml
"$PY" tools/gen_ld.py "$TARGET" || fail "gen_ld failed"
# stage the preprocessed assembly under build/, mirroring asm/nonmatchings
find build/asm -name "*.s" -delete 2>/dev/null
find build/asm -name "*.o" -delete 2>/dev/null

n_ok=0
n_fail=0
while IFS= read -r src; do
    rel="${src#asm/}"                       # e.g. nonmatchings/func_x.s
    staged="build/asm/$rel"
    obj="build/asm/${rel}.o"
    mkdir -p "$(dirname "$staged")"
    if ! "$PY" "$MASPSX" < /dev/null "$src" > "$staged" 2> "$staged.err"; then
        echo "maspsx FAILED: $src" >&2
        n_fail=$((n_fail + 1))
        continue
    fi
    # cross-file branches: spimdisasm emits address-encoded local labels
    # (.L8003BC00) for branch targets inside OTHER function files; .L is
    # file-local in GNU as, so globalize every address-encoded local label
    # (bytes are unchanged - the branch still resolves to the same vram).
    sed -i 's/^\(\.L[0-9A-Fa-f]\{8\}\):[[:space:]]*$/.globl \1\n\1:/' "$staged"
    # unique per-file input section: every .section directive in the file
    # becomes .r_<rom> with uniform flags, so text/data interleave inside
    # the file survives into one contiguous chunk the gen_ld script can
    # place at the subsegment's exact address.
    case "$staged" in
        */data_*) rom_hex=$(basename "$staged" | sed -E 's/^data_([0-9A-Fa-f]{8}).*/\1/') ;;
        *)        rom_hex=$(basename "$staged" | sed -E 's/^func_([0-9A-Fa-f]{8}).*/\1/') ;;
    esac
    rom=$(( 0x800 + (0x${rom_hex} - 0x80020000) ))
    python3 - "$staged" "$rom" <<'PYSEC'
import re, sys
path, rom = sys.argv[1], int(sys.argv[2])
MACRO_PRONE = {
    "ld", "sd", "lwu", "lld", "scd", "ldl", "ldr", "sdl", "sdr",
    "ll", "sc", "pref", "ldc1", "sdc1", "ldc2", "sdc2",
    "ulw", "usw", "ulh", "ulhu", "ush", "la", "dla", "daddi", "dsub",
}
out = []
for line in open(path):
    m = re.match(r"^(/\* [0-9A-F]{4,6} [0-9A-F]{8} ([0-9A-F]+) \*/)\s+([a-zA-Z.]+)", line)
    if m and m.group(3).lower() in MACRO_PRONE:
        raw = bytes.fromhex(m.group(2))
        val = int.from_bytes(raw, "little")
        line = f"{m.group(1)}  .word 0x{val:08X}  # was {m.group(3)} (data-as-code; gas would expand)\n"
    out.append(line)
sec = f'.r_{rom:08X}'
text = "".join(out)
text = re.sub(r'^\.section\s+\.(?:text|data|rodata|bss|sbss|sdata)\b[^\n]*$',
              f'.section {sec}, "awx", @progbits', text, flags=re.M)
open(path, 'w').write(text)
PYSEC
    if ! "$AS" $ASFLAGS -o "$obj" "$staged" 2> "$staged.aserr"; then
        echo "as FAILED: $src" >&2
        head -5 "$staged.aserr" >&2
        n_fail=$((n_fail + 1))
        continue
    fi
    n_ok=$((n_ok + 1))
done < <(find "$ASM_DIR" -name "*.s" | sort)

echo "assembled: $n_ok ok, $n_fail failed"
[ "$n_fail" -eq 0 ] || fail "assembly errors - fix the split or the pipeline"

# --- compile C sources (matched functions) ------------------------------------
# yaml subsegments of type `c` are matched C functions. They compile with
# the Psy-Q-era compiler through tools/cc.sh -S (bundled cpp -> cc1 under
# qemu-i386 -> maspsx --expand-div), then get the same staging treatment
# as asm: the .text directive is rewritten to .r_<rom> IN THE SOURCE and
# the file is assembled with $ASFLAGS. Doing the rename in the source (not
# with objcopy --rename-section) matters: gas pads the default .text to 16
# bytes on MIPS, while a fresh .section name carries no default padding —
# this is exactly why the asm path stages the same way. Orphan sections
# the C toolchain would contribute (.reginfo, .MIPS.abiflags,
# .gnu.attributes, .pdr, .comment) are discarded by gen_ld.py's /DISCARD/.
if [ -d src ]; then
    mkdir -p build/src
    c_list="build/${TARGET}.c_entries"
    "$PY" - "$TARGET" > "$c_list" <<EOF || fail "could not list C subsegments"
import sys, yaml
cfg = yaml.safe_load(open(f"config/splat.{sys.argv[1]}.yaml"))
for seg in cfg["segments"]:
    if isinstance(seg, dict) and seg.get("type") == "code":
        for e in seg.get("subsegments", []):
            if isinstance(e, list) and len(e) >= 3 and e[1] == "c":
                print(f"{e[2]} {e[0]:X}")
EOF
    n_c=0
    n_c_fail=0
    while read -r cname crom; do
        [ -n "${cname:-}" ] || continue
        [ -f "src/${cname}.c" ] || fail "yaml wants C at ${cname} but src/${cname}.c is missing"
        if ! "$REPO/tools/cc.sh" -S -o "build/src/${cname}.o" "src/${cname}.c"; then
            fail "C compile failed: src/${cname}.c"
        fi
        csec=$(printf '%08X' "0x${crom}")
        staged="build/src/${cname}.r.s"
        "$PY" - "build/src/${cname}.mas.s" "$staged" "$csec" <<'PYSEC' || fail "C staging failed: ${cname}"
import re, sys
src, dst, sec = sys.argv[1], sys.argv[2], sys.argv[3]
text = open(src).read()
text = re.sub(r"^\s*\.text\s*$",
              f'.section .r_{sec}, "awx", @progbits', text, flags=re.M)
# Small-data rewrite: cc1 -G8 emits bare-symbol memory operands for
# gp-relative globals (aspsx would relax them via .extern size + -G).
# maspsx only registers .comm/.sdata symbols, so extern-referenced
# globals pass through bare — GNU as would emit HI16/LO16 (absolute),
# which does NOT round-trip. Convert to the explicit form; the linker
# resolves GPREL16 against _gp (gen_ld.py emits it from yaml gp_value).
text = re.sub(
    r"(?m)^(\s*(?:lb|lbu|lh|lhu|lw|lwl|lwr|sb|sh|sw|swl|swr)\s+\$[a-z0-9]+,)"
    r"([A-Za-z_][A-Za-z0-9_]*(?:\+[0-9]+)?)\s*$",
    r"\1%gp_rel(\2)($gp)",
    text,
)
open(dst, "w").write(text)
PYSEC
        if ! "$AS" $ASFLAGS -o "build/src/${cname}.o" "$staged" 2> "build/src/${cname}.aserr"; then
            echo "as FAILED: src/${cname}.c" >&2
            head -5 "build/src/${cname}.aserr" >&2
            n_c_fail=$((n_c_fail + 1))
            continue
        fi
        n_c=$((n_c + 1))
    done < "$c_list"
    [ "$n_c_fail" -eq 0 ] || fail "C assembly errors"
    [ "$n_c" -eq 0 ] || echo "compiled: $n_c C source file(s)"
fi

# --- link (two-pass: auto-define address-encoded unresolved symbols) ---------
# spimdisasm names symbols it cannot resolve after their runtime address
# (D_8011C31C, func_8002DB14, ...). The retail bytes encode that same
# address via %hi/%lo pairs, so defining the symbol AT its name address
# reproduces the original word exactly. Symbols without an address in the
# name are a real problem and fail the build loudly.
rm -f build/undef_syms.ld
"$LD" -N -T "$LD_SCRIPT" --no-check-sections -o "$OUT_ELF" 2> build/ld.err || true
if grep -q "undefined reference" build/ld.err; then
    "$PY" - <<EOF
import re, sys
errs = open("build/ld.err", errors="replace").read()
names = sorted(set(re.findall(r"undefined reference to \`([A-Za-z_][A-Za-z0-9_]*)'", errs)))
out, bad = [], []
for n in names:
    # spimdisasm names unresolved references after their runtime value;
    # values may be real addresses (8 hex) or address-like constants
    # (e.g. the 0x7FFFFF bitmask via lui/addiu) with fewer digits.
    m = re.match(r"^[A-Za-z_]+_([0-9A-Fa-f]{1,8})$", n)
    (out.append(f"{n} = 0x{m.group(1)};") if m else bad.append(n))
if bad:
    sys.stderr.write("build: unresolved symbols without address-encoded names:\\n"
                     + "\\n".join(bad) + "\\n")
    sys.exit(2)
with open("build/undef_syms.ld", "w") as f:
    f.write("/* generated by tools/build.sh - auto-resolved spimdisasm symbols */\\n")
    f.write("\\n".join(out) + "\\n")
print(f"build: auto-defined {len(out)} unresolved symbols")
EOF
    "$LD" -T "$LD_SCRIPT" -T build/undef_syms.ld --no-check-sections -o "$OUT_ELF" \
        || fail "link failed (second pass)"
fi

"$OBJCOPY" -O binary "$OUT_ELF" "build/${TARGET}.payload.bin" || fail "objcopy failed"

"$PY" tools/mkpsxexe.py "$TARGET" || fail "mkpsxexe failed"
bytes=$(stat -c %s "build/${TARGET}.bin")
echo "linked image: build/${TARGET}.bin ($bytes bytes)"
