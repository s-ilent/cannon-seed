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

# -G0: no implicit small-data relaxation. cc1 -G8 emits bare-symbol
# operands for extern globals; gas's default -G8 would relax those to
# %gp_rel silently, but only the boot targets (yaml gp_value) really
# use gp-relative data - the others use absolute lui/$at in retail.
# Explicit forms in the sources (%hi/%lo, %gp_rel) are unaffected.
ASFLAGS="-march=mips64 -mabi=32 -EL -G0 -I include -I asm/nonmatchings"

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
# The nested nonmatchings/nonmatchings/ tree is splat's extract-after-flip
# stub noise (untracked, gitignored) - its files are named by SYMBOL, not
# by row, so the per-file rom decode below cannot handle them; they are
# not inputs to any gate. Excluded from the build walk.
done < <(find "$ASM_DIR" -name "*.s" ! -path "*/nonmatchings/nonmatchings/*" | sort)

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
    # gp_rel rewrite applies only to targets whose retail build used
    # gp-relative small data (yaml options.gp_value, _gp in the linker
    # script). Targets without a gp base keep cc1's bare-symbol form;
    # with -G0 gas expands it to the absolute lui/$at pair retail shows.
    GP_REWRITE=$("$PY" - "$TARGET" <<'EOF'
import sys, yaml
cfg = yaml.safe_load(open(f"config/splat.{sys.argv[1]}.yaml"))
print("1" if cfg["options"].get("gp_value") is not None else "0")
EOF
)
    # Range data for the gp_rel rewrite (PYSEC below): %gp_rel is legal
    # only within +/-0x7FFF of the gp base, and retail's own libraries
    # use absolute lui+lo for anything farther (e.g. LIBETC's video-mode
    # static, ~85 KB below slps_00270's gp base). Emit the gp base and a
    # name:address table from the committed symbols file; PYSEC rewrites
    # a bare load/store only when the symbol is known and in range
    # (unknown names keep the old behavior and fail loudly at link time
    # if they are genuinely out of range).
    GP_INFO=$("$PY" - "$TARGET" <<'EOF'
import sys, yaml, re
cfg = yaml.safe_load(open(f"config/splat.{sys.argv[1]}.yaml"))
gp = cfg["options"].get("gp_value") or 0
addr = {}
# A curated entry may carry a 'gp:absolute' marker when retail provably
# loads that symbol with an absolute lui+lo pair even though it sits
# inside +/-32 KB of the gp base (first case: LIBSPU's _spu_inTransfer,
# an 8-byte S_INI flag that S_ITC loads absolutely in slps_00270, while
# same-range 4-byte flags like boot_flag_0 are gp-relative there). The
# range test alone cannot know this - it is per-symbol retail evidence -
# so the marker flags the name (a '!' suffix in the PYSEC table) and the
# rewrite skips it, keeping the absolute form the non-gp targets prove.
for ln in open(f"config/symbols.{sys.argv[1]}.txt"):
    m = re.match(r"^(\w+) = 0x([0-9A-Fa-f]+);", ln)
    if m:
        # splat's native absolute:true boolean (curated gp:absolute) marks
        # per-symbol retail evidence: load it absolutely even in range.
        # The '!' suffix tells PYSEC to skip the rewrite for this name
        # (exclusion alone would fall into the unknown-name rewrite path).
        marked = "absolute:true" in ln
        addr[m.group(1) + ("!" if marked else "")] = int(m.group(2), 16)
print(f"{gp:#x} " + " ".join(f"{n}:{a:#x}" for n, a in sorted(addr.items())))
EOF
)
    "$PY" - "$TARGET" > "$c_list" <<EOF || fail "could not list C subsegments"
import sys, yaml
cfg = yaml.safe_load(open(f"config/splat.{sys.argv[1]}.yaml"))
for seg in cfg["segments"]:
    if isinstance(seg, dict) and seg.get("type") == "code":
        for e in seg.get("subsegments", []):
            if isinstance(e, list) and len(e) >= 3 and e[1] == "c":
                print(f"{e[2]} {e[0]:X}")
EOF
    # Multi-subsegment C (docs/FABRIC.md machinery): rows named <base>.pN
    # are PIECES of src/<base>.c - one compilation unit covering several
    # disjoint address windows. Group them with their base row into units
    # ("BASE ROM1 [ROM2 ...]" in yaml order = address order), and shrink
    # c_list to the plain single-window rows the loop below handles as
    # before. Zero .pN rows -> c_list unchanged, this is a no-op.
    "$PY" - "$c_list" > "${c_list}.units" <<'PYUNITS' || fail "piece grouping failed"
import re, sys
bases, pieces, order = {}, {}, []
for ln in open(sys.argv[1]):
    parts = ln.split()
    if not parts:
        continue
    name, rom = parts
    m = re.match(r"^([A-Za-z_]\w*)\.p(\d+)$", name)
    if m:
        pieces.setdefault(m.group(1), []).append((int(m.group(2)), rom))
        if m.group(1) not in pieces:
            order.append(m.group(1))
    else:
        bases[name] = rom
        order.append(name)
out = []
for name in order:
    if name in pieces:
        ps = sorted(pieces[name])
        want = list(range(2, len(ps) + 2))
        if [n for n, _r in ps] != want:
            raise SystemExit(f"piece numbering gap under {name}")
        if name not in bases:
            raise SystemExit(f"piece rows under {name} but no base row")
        out.append(" ".join([name, bases[name]] + [r for _n, r in ps]))
    else:
        out.append(f"{name} {bases[name]}")
print("\n".join(out))
PYUNITS
    grep -vE '^[A-Za-z_][A-Za-z0-9_]*\.p[0-9]{1,} ' "$c_list" > "${c_list}.plain" || true
    mv "${c_list}.plain" "$c_list"
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
        "$PY" - "build/src/${cname}.mas.s" "$staged" "$csec" "$GP_REWRITE" "$GP_INFO" <<'PYSEC' || fail "C staging failed: ${cname}"
import re, sys
src, dst, sec, gp_rewrite, gp_info = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
text = open(src).read()
text = re.sub(r"^\s*\.text\s*$",
              f'.section .r_{sec}, "awx", @progbits', text, flags=re.M)
# Small-data rewrite, gp targets only (GP_REWRITE=1: yaml options.gp_value
# exists, _gp is in the linker script): cc1 -G8 emits bare-symbol memory
# operands for gp-relative globals (aspsx would relax them via .extern
# size + -G). maspsx only registers .comm/.sdata symbols, so
# extern-referenced globals pass through bare - GNU as would emit
# HI16/LO16 (absolute), which does NOT round-trip when retail used
# gp-relative form. Convert to the explicit form; the linker resolves
# GPREL16 against _gp. Targets WITHOUT a gp base (GP_REWRITE=0) keep the
# bare form; with -G0 gas expands it to the absolute lui/$at pair that
# those targets' retail shows.
if gp_rewrite == "1":
    gp_base_str, _, tbl = gp_info.partition(" ")
    gp_base = int(gp_base_str, 16)
    symaddr = {}
    gp_abs = set()
    for tok in tbl.split():
        n, _, a = tok.rpartition(":")
        if not n:
            continue
        if n.endswith("!"):
            # curated gp:absolute marker (splat absolute:true): retail
            # provably loads this datum absolutely; never rewrite it.
            gp_abs.add(n[:-1])
            n = n[:-1]
        symaddr[n] = int(a, 16)

    def gp_rewrite_one(m):
        name = m.group(2)
        base_name = name.split("+", 1)[0]
        if base_name in gp_abs:
            return m.group(0)
        a = symaddr.get(base_name)
        if a is None or abs(a - gp_base) <= 0x7FFF:
            return f"{m.group(1)}%gp_rel({name})($gp)"
        return m.group(0)

    text = re.sub(
        r"(?m)^(\s*(?:lb|lbu|lh|lhu|lw|lwl|lwr|sb|sh|sw|swl|swr)\s+\$[a-z0-9]+,)"
        r"([A-Za-z_][A-Za-z0-9_]*(?:\+[0-9]+)?)\s*$",
        gp_rewrite_one,
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

    # --- multi-subsegment C units (docs/FABRIC.md machinery) --------------
    # One src/<base>.c covering several yaml c rows: the base row plus its
    # <base>.pN piece rows. cc.sh -S runs ONCE; tools/cc_split.py cuts the
    # product at function boundaries (piece order = .c function order =
    # base row then p2..pN) into per-row staged files with their own
    # .r_<rom> sections; each assembles to the object name gen_ld.py links
    # for its row (build/src/<base>.o, build/src/<base>.pN.o, ...).
    n_c=0
    n_c_fail=0
    while read -ra unit; do
        [ -n "${unit:-}" ] || continue
        [ "${#unit[@]}" -ge 3 ] || continue     # 2-field lines: plain rows
        base="${unit[0]}"; shift_count=0
        roms=("${unit[@]:1}")
        [ -f "src/${base}.c" ] || fail "yaml wants C at ${base} but src/${base}.c is missing"
        if ! "$REPO/tools/cc.sh" -S -o "build/src/${base}.o" "src/${base}.c"; then
            fail "C compile failed: src/${base}.c"
        fi
        rom_args=()
        for r in "${roms[@]}"; do rom_args+=("0x$r"); done
        if ! "$PY" "$REPO/tools/cc_split.py" "build/src/${base}.mas.s" \
                "build/src/${base}" "${rom_args[@]}" --gp="$GP_REWRITE" \
                > build/src/${base}.split.log; then
            cat build/src/${base}.split.log >&2
            fail "C split failed: src/${base}.c"
        fi
        for idx in "${!roms[@]}"; do
            r="${roms[$idx]}"
            if [ "$idx" -eq 0 ]; then staged="build/src/${base}.r.s"
            else staged="build/src/${base}.p$((idx + 1)).r.s"; fi
            if [ "$idx" -eq 0 ]; then obj="build/src/${base}.o"
            else obj="build/src/${base}.p$((idx + 1)).o"; fi
            if ! "$AS" $ASFLAGS -o "$obj" "$staged" 2> "${staged%.s}.aserr"; then
                echo "as FAILED: ${base} piece $((idx + 1))" >&2
                head -5 "${staged%.s}.aserr" >&2
                n_c_fail=$((n_c_fail + 1))
                continue
            fi
        done
        n_c=$((n_c + 1))
    done < "${c_list}.units"
    [ "$n_c_fail" -eq 0 ] || fail "C piece assembly errors"
    [ "$n_c" -eq 0 ] || echo "compiled: $n_c multi-subsegment C unit(s)"
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
    "$PY" - "$TARGET" <<EOF
import re, sys
errs = open("build/ld.err", errors="replace").read()
names = sorted(set(re.findall(r"undefined reference to \`([A-Za-z_.][A-Za-z0-9_.]*)'", errs)))
# Committed per-target symbols file: the retail placement of every
# curated name. Symbols the tree already knows by real name (Psy-Q bss
# statics beyond the payload segment, like LIBGS's PSDIDX) carry no
# address in their spelling and no dlabel renders for them, so the
# address-encoded fallbacks below cannot see them. Their address in
# this file IS the retail value - the same principle as the encoded
# names, just spelled out in the table instead of the symbol.
symaddr = {}
try:
    for ln in open(f"config/symbols.{sys.argv[1]}.txt"):
        m = re.match(r"^(\\w+) = 0x([0-9A-Fa-f]+);", ln)
        if m:
            symaddr[m.group(1)] = int(m.group(2), 16)
except FileNotFoundError:
    pass
out, bad = [], []
for n in names:
    # spimdisasm names unresolved references after their runtime value;
    # values may be real addresses (8 hex) or address-like constants
    # (e.g. the 0x7FFFFF bitmask via lui/addiu) with fewer digits.
    m = re.match(r"^[A-Za-z_]+_([0-9A-Fa-f]{1,8})$", n)
    if m:
        out.append(f"{n} = 0x{m.group(1)};")
        continue
    # .L<8hex> local labels are spimdisasm's intra-body jump targets;
    # maspsx promotes them to linkable symbols, and after an asm->c flip
    # their definition is gone while the jumpers (other asm files) remain.
    # The address is in the name, so define it there - same principle as
    # the func_/D_ forms above (first exercised by func_8003B568's
    # j .L80037CB0 into the C-matched func_80037CAC).
    m = re.match(r"^\.L([0-9A-Fa-f]{8})$", n)
    if m:
        out.append(f"{n} = 0x{m.group(1)};")
        continue
    a = symaddr.get(n)
    if a is not None:
        out.append(f"{n} = 0x{a:X};")
        continue
    bad.append(n)
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
