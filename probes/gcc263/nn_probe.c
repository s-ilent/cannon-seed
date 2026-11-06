/* d71 micro-probe: which (x<0) spelling makes gcc 2.6.3 -O1 emit slt/slti
 * instead of the sign-extract srl 31 for the materialization? */
long p1(long x){ long t=(x<0); if (t==0) return 7; return 9; }
long p2(long x){ long t=((x<0)?1:0); if (t==0) return 7; return 9; }
long p3(long x){ long t=!(x>=0); if (t==0) return 7; return 9; }
long p4(long x){ return (x<0); }
long p5(unsigned nv){ long n=nv&0xff; long t=(n<0); if (t==0) return n+1; return 9; }
long p6(long x){ if ((x<0)==0) return 7; return 9; }
long p7(long x){ long t=(x<=-1); if (t==0) return 7; return 9; }
long p8(long x){ long t=(x<0); long r=0; if (t==0) r=x+1; r=r+t; return r; }
long p9(long x){ long t=(x<0); if (t!=0) return 7; return 9; }
long p10(long x){ int t=(x<0); if (t==0) return 7; return 9; }
