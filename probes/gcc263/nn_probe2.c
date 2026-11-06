/* d71 round 2: force the materialization; find any slti-0 route */
long p21(long x){ long t=(x<5); if (t==0) return 7; return 9; }
long p22(long x){ long t=(x<0); if (t==0) return x+1; return t-2; }
struct S{long f;}; long p23(struct S*s){ long t=(s->f<0); if (t==0) return 7; return 9; }
long p24(long x){ long t; if (x<0) t=1; else t=0; if (t==0) return 7; return 9; }
long p25(long x){ register long t asm("$2")=(x<0); if (t==0) return 7; return 9; }
long p26(unsigned nv){ register long n asm("$3")=nv&0xff; long t=(n<0); register long i asm("$5")=0; if (t==0) return n+i; return 9; }
long p27(long x){ long t=(x<0); long u=t; if (u==0) return 7; return t+9; }
short gp; long p28(void){ long t=(gp<0); if (t==0) return 7; return 9; }
long p29(long x){ volatile long v=(x<0); if (v==0) return 7; return 9; }
long p30(long x){ long t=(x<0)?1:0; if (t!=1) return 7; return 9; }
