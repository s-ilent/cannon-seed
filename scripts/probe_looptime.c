/* probe: which C shape makes cc1 2.6.3-PSX emit the doubled-load timeout
 * loop bottom: [lw][addiu][sw][lw][lw][slti][bnez]? */
extern int sink(int *p);

void p1_plain(void) {
    int x, i;
    x = 13; i = 0;
    while (i < 240) { x = x * 3; i++; }
    sink(&x); sink(&i);
}

void p2_volatile(void) {
    volatile int x, i;
    x = 13; i = 0;
    while (i < 240) { x = x * 3; i++; }
}

void p3_addrtaken(void) {
    int x, i;
    sink(&x); sink(&i);
    x = 13; i = 0;
    while (i < 240) { x = x * 3; i++; }
    sink(&x);
}

void p4_for_volatile(void) {
    volatile int x, i;
    for (x = 13, i = 0; i < 240; i++) { x = x * 3; }
}

void p5_postinc_cond(void) {
    volatile int x, i;
    x = 13; i = 0;
    while (i++ < 240) { x = x * 3; }
}

void p6_preinc_cond(void) {
    volatile int x, i;
    x = 13; i = 0;
    while (++i < 240) { x = x * 3; }
}

void p7_do_while(void) {
    volatile int x, i;
    x = 13; i = 0;
    if (i < 240) {
        do { x = x * 3; i++; } while (i < 240);
    }
}

void p8_addrtaken_for(void) {
    int x, i;
    sink(&x); sink(&i);
    for (x = 13, i = 0; i < 240; i++) { x = x * 3; }
    sink(&x);
}
