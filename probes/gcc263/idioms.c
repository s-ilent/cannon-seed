/* Probe functions exercising the fingerprint rows measured on the
 * matched asm (docs/TOOLCHAIN.md). Compiled with tools/cc.sh — compare
 * the emitted .mas.s / objdump output against asm/nonmatchings/.
 * Not part of any build target; lives here purely as compiler-pin
 * evidence. */

/* Row: division guard — expect div + bnez/nop/break 7, then
 * addiu $at,-1 / bne+lui 0x80000000 / bne / break 6, then mflo. */
int div_signed(int a, int b)
{
    return a / b;
}

/* Row: unsigned division — expect divu + bnez/nop/break 7 only. */
unsigned int div_unsigned(unsigned int a, unsigned int b)
{
    return a / b;
}

/* Row: ISA — expect mult + mflo, no MIPS32 mul. */
int mul32(int a, int b)
{
    return a * b;
}

/* Row: char signedness — expect lbu for plain char. */
unsigned char load_uchar(unsigned char *p, int i)
{
    return p[i];
}

/* Row: char signedness minority — expect lb for signed char. */
signed char load_schar(signed char *p, int i)
{
    return p[i];
}
