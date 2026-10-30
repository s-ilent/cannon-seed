/* probe: which shape stops gcc 2.6.3 from CSE-ing the D_800AB0B0 counter
 * address into one la-form register? Retail wants THREE independent
 * materializations: entry store via $at, loop load as the fused same-reg
 * pair, loop store via $at - and no re-read after the ++ store. */
extern long D_800AB0B0[];
extern int printf();
extern char A[];
extern char B[];

extern int sink(long);

void q1_two_stmts(int p)
{
    D_800AB0B0[0] = 0;
    if (p) {
        do {
            if (++D_800AB0B0[0] >= 0x1389) {
                printf(A, B);
                break;
            }
        } while (p);
    }
}

void q2_barrier(int p)
{
    D_800AB0B0[0] = 0;
    __asm__ __volatile__("" ::: "memory");
    if (p) {
        do {
            if (++D_800AB0B0[0] >= 0x1389) {
                printf(A, B);
                break;
            }
        } while (p);
    }
}

void q3_loop_only(int p)
{
    if (p) {
        do {
            if (++D_800AB0B0[0] >= 0x1389) {
                printf(A, B);
                break;
            }
        } while (p);
    }
}

void q4_plusassign(int p)
{
    D_800AB0B0[0] = 0;
    if (p) {
        do {
            D_800AB0B0[0] += 1;
            if (D_800AB0B0[0] >= 0x1389) {
                printf(A, B);
                break;
            }
        } while (p);
    }
}

void q5_volatile_local_ptr(int p)
{
    D_800AB0B0[0] = 0;
    if (p) {
        do {
            if (++D_800AB0B0[0] >= 0x1389) {
                printf(A, B);
                break;
            }
            __asm__ __volatile__("" ::: "memory");
        } while (p);
    }
}

void q6_assign_expr(int p)
{
    D_800AB0B0[0] = 0;
    if (p) {
        do {
            if ((D_800AB0B0[0] = D_800AB0B0[0] + 1) >= 0x1389) {
                printf(A, B);
                break;
            }
        } while (p);
    }
}

void q7_assign_barrier(int p)
{
    D_800AB0B0[0] = 0;
    if (p) {
        do {
            __asm__ __volatile__("" ::: "memory");
            if ((D_800AB0B0[0] = D_800AB0B0[0] + 1) >= 0x1389) {
                printf(A, B);
                break;
            }
        } while (p);
    }
}

void q8_three_stmt(int p)
{
    long w;
    D_800AB0B0[0] = 0;
    if (p) {
        do {
            w = D_800AB0B0[0] + 1;
            D_800AB0B0[0] = w;
            if (w >= 0x1389) {
                printf(A, B);
                break;
            }
        } while (p);
    }
}

void q9_postinc_stmt(int p)
{
    long w;
    D_800AB0B0[0] = 0;
    if (p) {
        do {
            D_800AB0B0[0] += 1;
            w = D_800AB0B0[0];
            if (w >= 0x1389) {
                printf(A, B);
                break;
            }
        } while (p);
    }
}

extern long D_800AB0B0S;

void q10_scalar_assign(int p)
{
    long w;
    D_800AB0B0S = 0;
    if (p) {
        do {
            w = D_800AB0B0S + 1;
            D_800AB0B0S = w;
            if (w >= 0x1389) {
                printf(A, B);
                break;
            }
        } while (p);
    }
}

void q11_scalar_plusassign(int p)
{
    D_800AB0B0S = 0;
    if (p) {
        do {
            if ((D_800AB0B0S += 1) >= 0x1389) {
                printf(A, B);
                break;
            }
        } while (p);
    }
}
